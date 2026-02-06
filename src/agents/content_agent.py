"""
Content Agent - 内容生成Agent
负责AI内容生成、素材搜索、内容优化
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from src.agents.base_agent import BaseAgent
from src.graph.state import AgentState
from src.database.crud import ContentCRUD, UserCRUD
from src.database.session import db_manager
import yaml
from pathlib import Path


class ContentAgent(BaseAgent):
    """内容Agent - 负责内容生成"""

    def __init__(self):
        super().__init__("content_agent")

        # 加载提示词模板
        prompt_file = Path(__file__).parent.parent.parent / "config" / "prompts.yaml"
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompts = yaml.safe_load(f)

    async def invoke(self, state: AgentState) -> AgentState:
        """
        执行内容Agent逻辑

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        self.log_invocation(state)

        user_id = state.get("user_id")
        message = state.get("message", "")
        entities = state.get("entities", {})

        # 1. 解析内容创作请求
        content_request = await self._parse_content_request(message, entities)

        # 2. 生成内容大纲
        outline = await self._generate_outline(content_request)
        state["content_outline"] = outline

        # 3. 生成正文内容
        content = await self._generate_content(outline, content_request)
        state["content_draft"] = content

        # 4. 生成标题选项（A/B测试）
        titles = await self._generate_titles(content_request, outline)
        state["content_variants"] = titles

        # 5. 保存草稿
        content_id = await self._save_draft(content_request, outline, content, titles)

        # 6. 生成响应消息
        response = f"""内容已生成！📝

主题：{content_request['topic']}

标题选项：
{chr(10).join([f'{i+1}. {title}' for i, title in enumerate(titles)])}

摘要：{outline.get('summary', content[:200])}

内容已保存为草稿（ID: {content_id}）。您可以预览、编辑或调度发布。"""

        state = self.update_state(
            state,
            response_message=response,
            metadata={
                "content_id": content_id,
                "content_type": content_request.get("content_type", "article"),
                "word_count": len(content)
            }
        )

        state["agent_chain"] = state.get("agent_chain", []) + [self.name]

        print(f"[{self.name}] Content generated: {content_id}")
        return state

    async def _parse_content_request(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析内容创作请求

        Args:
            message: 用户消息
            entities: 提取的实体

        Returns:
            内容创作请求字典
        """
        # 使用Claude解析请求
        prompt = f"""用户消息：{message}

请提取以下信息并返回JSON：
{{
  "topic": "选题",
  "content_type": "内容类型 (tutorial/analysis/case/hot/casual)",
  "target_audience": "目标受众",
  "word_count": 字数 (默认1500),
  "keywords": ["关键词1", "关键词2"]
}}

如果某个字段无法确定，使用默认值。"""

        try:
            response = self.call_claude(prompt, max_tokens=500)
            request_data = json.loads(response)

            # 设置默认值
            request_data.setdefault("word_count", 1500)
            request_data.setdefault("content_type", "article")
            request_data.setdefault("target_audience", "一般读者")
            request_data.setdefault("keywords", [])

            return request_data

        except Exception as e:
            print(f"[{self.name}] 解析请求失败: {e}")
            # 降级处理
            return {
                "topic": message,
                "content_type": "article",
                "target_audience": "一般读者",
                "word_count": 1500,
                "keywords": []
            }

    async def _generate_outline(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成内容大纲

        Args:
            request: 内容创作请求

        Returns:
            大纲字典
        """
        prompt_template = self.prompts["content_generation"]["outline"]
        prompt = prompt_template.format(
            topic=request["topic"],
            audience=request["target_audience"],
            content_type=request["content_type"]
        )

        try:
            response = self.call_claude(prompt, max_tokens=1000)

            # 解析大纲
            # 假设Claude返回结构化的大纲
            outline = {
                "raw": response,
                "summary": "AI生成的文章大纲",
                "structure": ["开头", "主体", "结尾"]
            }

            return outline

        except Exception as e:
            print(f"[{self.name}] 生成大纲失败: {e}")
            return {
                "raw": f"关于 {request['topic']} 的文章",
                "summary": request["topic"],
                "structure": ["开头", "主体", "结尾"]
            }

    async def _generate_content(self, outline: Dict[str, Any], request: Dict[str, Any]) -> str:
        """
        生成正文内容

        Args:
            outline: 大纲
            request: 创作请求

        Returns:
            正文内容
        """
        prompt_template = self.prompts["content_generation"]["article"]
        prompt = prompt_template.format(
            outline=outline["raw"],
            word_count=request["word_count"]
        )

        try:
            response = self.call_claude(prompt, max_tokens=4096)
            return response

        except Exception as e:
            print(f"[{self.name}] 生成内容失败: {e}")
            return f"关于{request['topic']}的文章内容。"

    async def _generate_titles(self, request: Dict[str, Any], outline: Dict[str, Any]) -> List[str]:
        """
        生成标题选项

        Args:
            request: 创作请求
            outline: 大纲

        Returns:
            标题列表
        """
        prompt = f"""为以下文章生成5个吸引人的标题：

选题：{request['topic']}
大纲摘要：{outline['summary']}

要求：
1. 使用不同策略（数字型、痛点型、悬念型、福利型等）
2. 标题吸引但不标题党
3. 每个标题不超过30字

请返回JSON格式：
{{"titles": ["标题1", "标题2", "标题3", "标题4", "标题5"]}}"""

        try:
            response = self.call_claude(prompt, max_tokens=500)
            result = json.loads(response)
            return result.get("titles", [request["topic"]])

        except Exception as e:
            print(f"[{self.name}] 生成标题失败: {e}")
            return [request["topic"]]

    async def _save_draft(self, request: Dict[str, Any], outline: Dict[str, Any],
                          content: str, titles: List[str]) -> int:
        """
        保存内容草稿

        Args:
            request: 创作请求
            outline: 大纲
            content: 正文
            titles: 标题列表

        Returns:
            内容ID
        """
        with db_manager.get_session() as db:
            content_record = ContentCRUD.create_content(
                db,
                title=titles[0] if titles else request["topic"],
                content=content,
                summary=outline.get("summary", ""),
                content_type=request.get("content_type", "article"),
                topic=request["topic"],
                keywords=request.get("keywords", []),
                ai_generated=True,
                ai_model="claude-3.5-sonnet",
                outline=outline,
                title_variants=titles,
                status="draft"
            )
            return content_record.id
