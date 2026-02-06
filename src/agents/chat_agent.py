"""
Chat Agent - 对话处理Agent
负责智能对话、FAQ匹配、用户画像更新
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.graph.state import AgentState
from src.database.crud import ConversationCRUD, UserCRUD, FAQCRUD
from src.database.session import db_manager
from src.cache.redis_client import cache_manager


class ChatAgent(BaseAgent):
    """聊天Agent - 负责对话处理"""

    def __init__(self):
        super().__init__("chat_agent")

    async def invoke(self, state: AgentState) -> AgentState:
        """
        执行聊天Agent逻辑

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        self.log_invocation(state)

        user_id = state.get("user_id")
        message = state.get("message", "")
        intent = state.get("intent", "other")
        entities = state.get("entities", {})

        # 1. 获取对话历史
        chat_history = await self._get_chat_history(user_id)

        # 2. 尝试FAQ匹配
        faq_response = await self._match_faq(message, intent)
        if faq_response:
            state = self.update_state(
                state,
                chat_response=faq_response,
                faq_matches=[{"question": message, "answer": faq_response}],
                response_message=faq_response
            )
            print(f"[{self.name}] FAQ matched")
        else:
            # 3. 使用Claude生成回复
            claude_response = await self._generate_claude_response(
                message, intent, chat_history, entities
            )

            state = self.update_state(
                state,
                chat_response=claude_response,
                response_message=claude_response
            )
            print(f"[{self.name}] Claude response generated")

        # 4. 保存对话历史
        await self._save_conversation(user_id, message, state["chat_response"])

        # 5. 更新用户画像
        await self._update_user_profile(user_id, intent, state)

        state["agent_chain"] = state.get("agent_chain", []) + [self.name]

        return state

    async def _get_chat_history(self, user_id: str) -> List[Dict[str, str]]:
        """
        获取对话历史（优先从Redis缓存）

        Args:
            user_id: 用户ID

        Returns:
            对话历史列表
        """
        # 先从Redis缓存获取
        cached_history = cache_manager.get_conversation_history(int(user_id))
        if cached_history:
            return cached_history

        # 缓存未命中，从数据库获取
        with db_manager.get_session() as db:
            recent_messages = ConversationCRUD.get_recent_messages(
                db, int(user_id), hours=24, limit=10
            )
            return [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(recent_messages)
            ]

    async def _match_faq(self, message: str, intent: str) -> str:
        """
        匹配FAQ知识库

        Args:
            message: 用户消息
            intent: 意图

        Returns:
            FAQ答案（如果匹配）或None
        """
        # 只有query类型的意图才匹配FAQ
        if intent not in ["query", "other"]:
            return None

        with db_manager.get_session() as db:
            faqs = FAQCRUD.search_faq(db, message, limit=3)

            if faqs:
                # 更新命中次数
                FAQCRUD.update_faq_hit(db, faqs[0].id)
                return faqs[0].answer

        return None

    async def _generate_claude_response(self, message: str, intent: str,
                                         chat_history: List[Dict[str, str]],
                                         entities: Dict[str, Any]) -> str:
        """
        使用Claude生成智能回复

        Args:
            message: 用户消息
            intent: 意图
            chat_history: 对话历史
            entities: 实体

        Returns:
            Claude生成的回复
        """
        # 系统提示
        system_prompt = """你是一个专业的客服助手，代表品牌与用户沟通。

回复要求：
1. 语气友好自然，像真人对话
2. 直接回答用户问题
3. 适当使用emoji增加亲和力（但不要过度）
4. 如果无法解决，引导转人工客服
5. 回复长度控制在200字以内
6. 根据用户意图调整回复策略：
   - greeting: 热情问候，主动介绍功能
   - query: 专业解答，提供详细信息
   - complaint: 表示理解，道歉并给出解决方案
   - praise: 表达感谢，引导互动
   - purchase: 提供购买指引
   - other: 尝试理解，提供帮助"""

        # 构建对话上下文
        messages = []

        # 添加历史对话（最近5轮）
        for msg in chat_history[-5:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # 添加当前消息
        messages.append({
            "role": "user",
            "content": message
        })

        # 添加意图上下文
        if intent != "other":
            context_msg = f"\n[系统提示：用户意图是 {intent}]"
            messages[-1]["content"] += context_msg

        try:
            response = self.call_claude_with_history(
                messages=messages,
                max_tokens=500,
                system_prompt=system_prompt
            )
            return response

        except Exception as e:
            print(f"[{self.name}] Claude生成回复失败: {e}")
            # 降级回复
            return "抱歉，我暂时无法理解您的消息。您可以换个说法，或联系人工客服。"

    async def _save_conversation(self, user_id: str, user_message: str,
                                  bot_response: str):
        """
        保存对话到数据库和缓存

        Args:
            user_id: 用户ID
            user_message: 用户消息
            bot_response: 机器人回复
        """
        with db_manager.get_session() as db:
            # 获取或创建会话
            conversation = ConversationCRUD.get_active_conversation(db, int(user_id))
            if not conversation:
                conversation = ConversationCRUD.create_conversation(
                    db, int(user_id), agent_route="chat_agent"
                )

            # 保存消息
            ConversationCRUD.add_message(
                db, conversation.id, int(user_id),
                role="user", content=user_message
            )
            ConversationCRUD.add_message(
                db, conversation.id, int(user_id),
                role="assistant", content=bot_response, agent_used="chat_agent"
            )

        # 更新Redis缓存
        cache_manager.add_conversation_message(int(user_id), "user", user_message)
        cache_manager.add_conversation_message(int(user_id), "assistant", bot_response)

    async def _update_user_profile(self, user_id: str, intent: str, state: AgentState):
        """
        更新用户画像

        Args:
            user_id: 用户ID
            intent: 意图
            state: 当前状态
        """
        with db_manager.get_session() as db:
            user = UserCRUD.get_user_by_openid(db, user_id)
            if not user:
                return

            # 更新最后互动时间
            user.last_interaction_time = datetime.utcnow()
            user.total_interactions += 1

            # 根据意图更新标签
            new_tags = []
            if intent == "purchase":
                new_tags.append("购买意向")
            elif intent == "complaint":
                new_tags.append("有过投诉")
            elif intent == "praise":
                new_tags.append("积极用户")

            # 合并标签
            if new_tags:
                existing_tags = user.tags or []
                updated_tags = list(set(existing_tags + new_tags))
                user.tags = updated_tags

            # 更新缓存
            profile = {
                "total_interactions": user.total_interactions,
                "tags": user.tags,
                "lifecycle_stage": user.lifecycle_stage.value if user.lifecycle_stage else "new"
            }
            cache_manager.set_user_profile(int(user_id), profile)
