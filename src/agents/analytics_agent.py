"""
Analytics Agent - 数据分析Agent
负责数据采集、指标计算、洞察生成
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from src.agents.base_agent import BaseAgent
from src.graph.state import AgentState
from src.database.crud import AnalyticsCRUD, ContentCRUD
from src.database.session import db_manager
from src.wechat.api_client import wechat_api_client


class AnalyticsAgent(BaseAgent):
    """分析Agent - 负责数据分析"""

    def __init__(self):
        super().__init__("analytics_agent")

    async def invoke(self, state: AgentState) -> AgentState:
        """
        执行分析Agent逻辑

        Args:
            state: 当前状态

        Returns:
            更新后的状态
        """
        self.log_invocation(state)

        user_id = state.get("user_id")
        message = state.get("message", "")

        # 1. 解析分析请求
        analysis_type = await self._parse_analysis_request(message)

        # 2. 采集数据
        data = await self._collect_data(analysis_type)

        # 3. 计算指标
        metrics = await self._calculate_metrics(data)

        # 4. 生成洞察
        insights = await self._generate_insights(metrics)

        # 5. 生成报告
        report = await self._generate_report(metrics, insights)

        # 6. 保存快照
        await self._save_snapshot(metrics)

        # 7. 构建响应
        response = f"""数据分析报告 📊

{report}

关键洞察：
{chr(10).join([f'• {insight}' for insight in insights[:5]])}

详细数据已保存。"""

        state = self.update_state(
            state,
            analytics_data=metrics,
            insights=insights,
            response_message=response,
            metadata={
                "analysis_type": analysis_type,
                "data_points": len(data),
                "timestamp": datetime.now().isoformat()
            }
        )

        state["agent_chain"] = state.get("agent_chain", []) + [self.name]

        print(f"[{self.name}] Analytics completed: {analysis_type}")
        return state

    async def _parse_analysis_request(self, message: str) -> str:
        """
        解析分析请求类型

        Args:
            message: 用户消息

        Returns:
            分析类型
        """
        message_lower = message.lower()

        if any(word in message_lower for word in ["用户", "粉丝", "增长"]):
            return "user_growth"
        elif any(word in message_lower for word in ["文章", "内容", "阅读"]):
            return "content_performance"
        elif any(word in message_lower for word in ["互动", "评论", "点赞"]):
            return "engagement"
        elif any(word in message_lower for word in ["全", "全部", "整体"]):
            return "overview"
        else:
            return "overview"

    async def _collect_data(self, analysis_type: str) -> List[Dict[str, Any]]:
        """
        采集数据

        Args:
            analysis_type: 分析类型

        Returns:
            数据列表
        """
        # 计算日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        with db_manager.get_session() as db:
            if analysis_type == "content_performance":
                # 获取内容数据
                contents = ContentCRUD.get_top_content(db, days=7, limit=50)
                return [
                    {
                        "id": c.id,
                        "title": c.title,
                        "views": c.views,
                        "likes": c.likes,
                        "shares": c.shares,
                        "publish_time": c.publish_time.isoformat() if c.publish_time else None
                    }
                    for c in contents
                ]

            elif analysis_type == "user_growth":
                # 获取用户快照
                snapshots = db.query(AnalyticsSnapshot).filter(
                    AnalyticsSnapshot.snapshot_type == "daily"
                ).order_by(AnalyticsSnapshot.snapshot_date.desc()).limit(7).all()

                return [
                    {
                        "date": s.snapshot_date.isoformat(),
                        "total_followers": s.total_followers,
                        "new_followers": s.new_followers,
                        "lost_followers": s.lost_followers
                    }
                    for s in snapshots
                ]

            else:
                # 概览数据
                snapshot = AnalyticsCRUD.get_latest_snapshot(db, "daily")
                if snapshot:
                    return [{
                        "total_followers": snapshot.total_followers,
                        "total_articles": snapshot.total_articles,
                        "total_views": snapshot.total_views,
                        "total_interactions": snapshot.total_interactions
                    }]
                return []

    async def _calculate_metrics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算指标

        Args:
            data: 原始数据

        Returns:
            指标字典
        """
        if not data:
            return {}

        metrics = {
            "data_count": len(data),
            "timestamp": datetime.now().isoformat()
        }

        # 根据数据类型计算不同指标
        if "views" in data[0]:  # 内容数据
            total_views = sum(item.get("views", 0) for item in data)
            total_likes = sum(item.get("likes", 0) for item in data)
            total_shares = sum(item.get("shares", 0) for item in data)

            metrics.update({
                "total_views": total_views,
                "avg_views": total_views / len(data),
                "total_likes": total_likes,
                "total_shares": total_shares,
                "engagement_rate": (total_likes + total_shares) / total_views if total_views > 0 else 0
            })

        elif "new_followers" in data[0]:  # 用户数据
            total_new = sum(item.get("new_followers", 0) for item in data)
            total_lost = sum(item.get("lost_followers", 0) for item in data)

            metrics.update({
                "total_new_followers": total_new,
                "total_lost_followers": total_lost,
                "net_growth": total_new - total_lost,
                "avg_daily_growth": total_new / len(data)
            })

        return metrics

    async def _generate_insights(self, metrics: Dict[str, Any]) -> List[str]:
        """
        生成洞察

        Args:
            metrics: 指标数据

        Returns:
            洞察列表
        """
        prompt = f"""你是数据分析专家。请分析以下数据，生成5-8条关键洞察。

数据：
{metrics}

请返回JSON格式：
{{"insights": ["洞察1", "洞察2", ...]}}

要求：
1. 洞察要深刻，直击要点
2. 基于数据，有理有据
3. 提供可执行的建议"""

        try:
            response = self.call_claude(prompt, max_tokens=1000)
            result = eval(response)  # 简化处理，实际应该用json.loads
            return result.get("insights", [])

        except Exception as e:
            print(f"[{self.name}] 生成洞察失败: {e}")

            # 降级：生成简单洞察
            insights = []
            if "total_views" in metrics:
                insights.append(f"总阅读量达到 {metrics['total_views']} 次")
            if "net_growth" in metrics:
                insights.append(f"粉丝净增长 {metrics['net_growth']} 人")

            return insights

    async def _generate_report(self, metrics: Dict[str, Any], insights: List[str]) -> str:
        """
        生成报告

        Args:
            metrics: 指标
            insights: 洞察

        Returns:
            报告文本
        """
        report_lines = ["核心指标："]

        for key, value in metrics.items():
            if key not in ["data_count", "timestamp"]:
                # 格式化key
                formatted_key = key.replace("_", " ").title()
                report_lines.append(f"- {formatted_key}: {value}")

        return "\n".join(report_lines)

    async def _save_snapshot(self, metrics: Dict[str, Any]):
        """
        保存数据快照

        Args:
            metrics: 指标数据
        """
        with db_manager.get_session() as db:
            AnalyticsCRUD.create_snapshot(
                db,
                snapshot_date=datetime.now(),
                snapshot_type="daily",
                **metrics
            )
