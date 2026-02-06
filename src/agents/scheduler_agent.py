"""
Scheduler Agent - 任务调度Agent
负责定时任务、内容发布计划、最佳时间预测
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.agents.base_agent import BaseAgent
from src.graph.state import AgentState
from src.database.crud import ContentCRUD
from src.database.session import db_manager


class SchedulerAgent(BaseAgent):
    """调度Agent - 负责任务调度"""

    def __init__(self):
        super().__init__("scheduler_agent")

        # 默认发布时间
        self.default_publish_times = ["08:00", "12:00", "18:00", "21:00"]

    async def invoke(self, state: AgentState) -> AgentState:
        """
        执行调度Agent逻辑

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        self.log_invocation(state)

        user_id = state.get("user_id")
        message = state.get("message", "")
        entities = state.get("entities", {})

        # 1. 解析调度请求
        schedule_request = await self._parse_schedule_request(message, entities)

        # 2. 如果是调度内容发布
        if schedule_request["type"] == "publish_content":
            response = await self._schedule_content_publish(schedule_request)

        # 3. 如果是生成内容日历
        elif schedule_request["type"] == "generate_calendar":
            response = await self._generate_content_calendar(schedule_request)

        # 4. 如果是查询待调度任务
        elif schedule_request["type"] == "list_pending":
            response = await self._list_pending_tasks()

        else:
            response = "我不确定您想做什么调度。您可以：\n1. 调度内容发布\n2. 生成内容日历\n3. 查看待调度任务"

        state = self.update_state(
            state,
            response_message=response,
            metadata={
                "schedule_type": schedule_request["type"],
                "timestamp": datetime.now().isoformat()
            }
        )

        state["agent_chain"] = state.get("agent_chain", []) + [self.name]

        print(f"[{self.name}] Schedule completed: {schedule_request['type']}")
        return state

    async def _parse_schedule_request(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析调度请求

        Args:
            message: 用户消息
            entities: 实体

        Returns:
            调度请求字典
        """
        message_lower = message.lower()

        if any(word in message_lower for word in ["发布", "推送", "定时"]):
            return {
                "type": "publish_content",
                "content_id": entities.get("content_id") or entities.get("id"),
                "publish_time": entities.get("time"),
                "date": entities.get("date")
            }
        elif any(word in message_lower for word in ["日历", "计划", "安排"]):
            return {
                "type": "generate_calendar",
                "days": entities.get("days", 7)
            }
        elif any(word in message_lower for word in ["列表", "待发", "任务"]):
            return {
                "type": "list_pending"
            }
        else:
            return {
                "type": "unknown"
            }

    async def _schedule_content_publish(self, request: Dict[str, Any]) -> str:
        """
        调度内容发布

        Args:
            request: 调度请求

        Returns:
            响应消息
        """
        content_id = request.get("content_id")
        publish_time = request.get("publish_time")

        # 如果没有指定时间，使用最佳时间预测
        if not publish_time:
            publish_time = await self._predict_best_time()

        # 解析发布时间
        if isinstance(publish_time, str):
            # 组合日期和时间
            if request.get("date"):
                datetime_str = f"{request['date']} {publish_time}"
            else:
                # 默认今天
                today = datetime.now().strftime("%Y-%m-%d")
                datetime_str = f"{today} {publish_time}"

            try:
                publish_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return "时间格式错误，请使用格式：YYYY-MM-DD HH:MM"
        else:
            publish_datetime = publish_time

        # 检查时间是否在未来
        if publish_datetime <= datetime.now():
            return "发布时间必须是未来时间"

        # 创建调度
        with db_manager.get_session() as db:
            schedule = ContentCRUD.schedule_content(
                db,
                content_id=int(content_id) if content_id else 1,
                scheduled_time=publish_datetime
            )

            return f"""内容发布已调度！✅

内容ID: {content_id}
发布时间: {publish_datetime.strftime('%Y-%m-%d %H:%M')}

系统将在指定时间自动发布。您可以随时取消或修改。"""

    async def _generate_content_calendar(self, request: Dict[str, Any]) -> str:
        """
        生成内容日历

        Args:
            request: 请求

        Returns:
            日历文本
        """
        days = request.get("days", 7)

        # 简单实现：生成未来N天的内容计划
        calendar_lines = [f"未来 {days} 天内容日历 📅\n"]

        for i in range(days):
            date = datetime.now() + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d (%a)")

            # 根据日期推荐内容类型
            content_type = self._recommend_content_type(date.weekday())

            calendar_lines.append(f"{date_str}: {content_type}")

        return "\n".join(calendar_lines)

    def _recommend_content_type(self, weekday: int) -> str:
        """
        根据星期推荐内容类型

        Args:
            weekday: 星期几 (0=周一, 6=周日)

        Returns:
            内容类型推荐
        """
        recommendations = {
            0: "规划日（上周复盘 + 本周规划）",
            1: "干货日（深度教程）",
            2: "数据日（行业分析）",
            3: "案例日（成功/失败案例）",
            4: "互动日（轻松话题/问答）",
            5: "休息/热点响应",
            6: "准备日（下周选题）"
        }
        return recommendations.get(weekday, "常规内容")

    async def _predict_best_time(self) -> str:
        """
        预测最佳发布时间

        Returns:
            时间字符串
        """
        # 简化实现：返回固定的最佳时间
        # 实际应该基于历史数据分析
        return "21:00"

    async def _list_pending_tasks(self) -> str:
        """
        列出待调度任务

        Returns:
            任务列表文本
        """
        with db_manager.get_session() as db:
            schedules = ContentCRUD.get_pending_schedules(
                db,
                before_time=datetime.now() + timedelta(days=7)
            )

            if not schedules:
                return "未来7天没有待发布的内容"

            lines = ["待发布内容列表：\n"]

            for schedule in schedules:
                content = schedule.content
                time_str = schedule.scheduled_time.strftime("%Y-%m-%d %H:%M")
                lines.append(f"- {content.title} ({time_str})")

            return "\n".join(lines)
