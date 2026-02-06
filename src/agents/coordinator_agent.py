"""
Coordinator Agent - 主控Agent
负责意图识别和Agent路由
"""
import json
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.graph.state import AgentState


class CoordinatorAgent(BaseAgent):
    """主控Agent - 负责路由和协调"""

    def __init__(self):
        super().__init__("coordinator")

        # Agent注册表
        self.agent_registry = {
            "greeting": "chat_agent",  # 问候 -> 聊天Agent
            "query": "chat_agent",  # 咨询 -> 聊天Agent
            "complaint": "chat_agent",  # 投诉 -> 聊天Agent
            "praise": "chat_agent",  # 表扬 -> 聊天Agent
            "purchase": "chat_agent",  # 购买 -> 聊天Agent
            "content_creation": "content_agent",  # 内容创作 -> 内容Agent
            "analytics": "analytics_agent",  # 数据分析 -> 分析Agent
            "schedule": "scheduler_agent",  # 调度 -> 调度Agent
        }

        # 意图分类提示
        self.intent_system_prompt = """你是一个意图分类专家。你的任务是分析用户的消息，将其归类到以下意图之一：

意图类别：
- greeting: 问候（你好、在吗、早上好等）
- query: 咨询问题（产品咨询、价格询问、使用问题等）
- complaint: 投诉（不满、问题反馈、服务质量问题等）
- praise: 表扬（感谢、赞美、好评等）
- purchase: 购买意向（怎么买、下单、购买链接等）
- content_creation: 内容创作请求（写文章、生成内容、帮我写等）
- analytics: 数据分析请求（看数据、分析报告、统计等）
- schedule: 调度相关（定时发布、内容计划、时间安排等）
- other: 其他

请返回JSON格式：
{
  "intent": "意图类别",
  "confidence": 0.95,
  "entities": {"关键实体": "值"},
  "reasoning": "判断理由"
}

注意：
1. confidence必须是0到1之间的浮点数
2. entities提取关键实体（如产品名、时间、数量等）
3. reasoning简要说明判断依据
"""

    async def invoke(self, state: AgentState) -> AgentState:
        """
        执行主控Agent逻辑

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        self.log_invocation(state)

        # 1. 意图识别
        intent_result = await self._classify_intent(state)

        # 2. 更新状态
        state = self.update_state(
            state,
            intent=intent_result["intent"],
            confidence=intent_result["confidence"],
            entities=intent_result.get("entities", {}),
            current_agent=self.name
        )

        # 3. Agent路由决策
        next_agent = self._route_to_agent(state, intent_result)
        state["next_agent"] = next_agent
        state["agent_chain"] = state.get("agent_chain", []) + [self.name]

        # 4. 特殊事件处理
        if state.get("message_type") == "event":
            state = await self._handle_event(state)

        print(f"[{self.name}] Intent: {intent_result['intent']}")
        print(f"[{self.name}] Next Agent: {next_agent}")
        print(f"[{self.name}] Confidence: {intent_result['confidence']}")

        return state

    async def _classify_intent(self, state: AgentState) -> Dict[str, Any]:
        """
        使用Claude进行意图分类

        Args:
            state: 当前状态

        Returns:
            意图分类结果
        """
        message = state.get("message", "")
        chat_history = state.get("chat_history", [])

        # 构建提示
        prompt = f"""用户消息：{message}

对话历史：
{json.dumps(chat_history[-5:], ensure_ascii=False) if chat_history else "无"}

请分析用户意图并返回JSON结果。"""

        try:
            response = self.call_claude(
                prompt=prompt,
                max_tokens=500,
                system_prompt=self.intent_system_prompt
            )

            # 解析JSON响应
            result = json.loads(response)
            return result

        except json.JSONDecodeError as e:
            print(f"[{self.name}] JSON解析失败: {e}")
            print(f"[{self.name}] 原始响应: {response}")

            # 降级处理：返回默认意图
            return {
                "intent": "other",
                "confidence": 0.5,
                "entities": {},
                "reasoning": "JSON解析失败，使用默认意图"
            }

        except Exception as e:
            print(f"[{self.name}] 意图分类失败: {e}")
            return {
                "intent": "other",
                "confidence": 0.0,
                "entities": {},
                "reasoning": f"分类失败: {str(e)}"
            }

    def _route_to_agent(self, state: AgentState, intent_result: Dict[str, Any]) -> str:
        """
        根据意图路由到相应的Agent

        Args:
            state: 当前状态
            intent_result: 意图识别结果

        Returns:
            下一个Agent的名称
        """
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]

        # 置信度过低，路由到Chat Agent进行澄清
        if confidence < 0.6:
            return "chat_agent"

        # 根据意图路由
        agent = self.agent_registry.get(intent, "chat_agent")

        # 特殊处理：如果是消息类型事件，也路由到Chat Agent
        if state.get("message_type") == "event":
            if state.get("event_type") == "subscribe":
                return "chat_agent"  # 欢迎消息
            elif state.get("event_type") == "unsubscribe":
                return "analytics_agent"  # 记录流失数据

        return agent

    async def _handle_event(self, state: AgentState) -> AgentState:
        """
        处理特殊事件

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        event_type = state.get("event_type")

        if event_type == "subscribe":
            # 用户关注事件
            state["response_message"] = "欢迎关注我们的公众号！😊"
            state["metadata"] = {
                "event": "subscribe",
                "welcome": True
            }

        elif event_type == "unsubscribe":
            # 用户取消关注事件
            state["response_message"] = None  # 不需要回复
            state["metadata"] = {
                "event": "unsubscribe",
                "record_churn": True
            }

        elif event_type == "click":
            # 菜单点击事件
            entity_key = state.get("entities", {}).get("key", "")
            state["metadata"] = {
                "event": "menu_click",
                "menu_key": entity_key
            }

        return state

    def get_agent_description(self, agent_name: str) -> str:
        """
        获取Agent的描述信息

        Args:
            agent_name: Agent名称

        Returns:
            Agent描述
        """
        descriptions = {
            "coordinator": "主控Agent，负责任务分发和协调",
            "chat_agent": "聊天Agent，负责用户对话和FAQ匹配",
            "content_agent": "内容Agent，负责AI内容生成",
            "analytics_agent": "分析Agent，负责数据采集和分析",
            "scheduler_agent": "调度Agent，负责定时任务和内容发布"
        }
        return descriptions.get(agent_name, "未知Agent")
