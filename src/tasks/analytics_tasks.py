"""
分析相关Celery任务
"""
from celery import shared_task
from datetime import datetime, timedelta
from src.database.crud import AnalyticsCRUD
from src.database.session import db_manager
from src.wechat.api_client import wechat_api_client
import logging

logger = logging.getLogger(__name__)


@shared_task(name="src.tasks.analytics_tasks.collect_analytics_data")
def collect_analytics_data():
    """
    采集微信数据

    每小时执行一次
    """
    logger.info("开始采集微信数据...")

    try:
        # 获取昨天的日期
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        # 采集用户数据
        user_summary = wechat_api_client.get_user_summary(yesterday, today)

        # 采集图文数据
        article_total = wechat_api_client.get_article_total(yesterday, today)

        # 采集阅读数据
        user_read = wechat_api_client.get_user_read(yesterday, today)

        # 保存到数据库
        with db_manager.get_session() as db:
            snapshot = AnalyticsCRUD.create_snapshot(
                db,
                snapshot_date=datetime.now(),
                snapshot_type="hourly",
                total_followers=user_summary.get("total", 0),
                new_followers=user_summary.get("new", 0),
                lost_followers=user_summary.get("cancel", 0),
                total_articles=article_total.get("total", 0),
                total_views=user_read.get("total", 0) if user_read else 0
            )

            logger.info(f"数据采集完成: {snapshot.id}")

        return {
            "success": True,
            "followers": user_summary.get("total", 0),
            "views": user_read.get("total", 0) if user_read else 0
        }

    except Exception as e:
        logger.error(f"数据采集失败: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="src.tasks.analytics_tasks.generate_daily_report")
def generate_daily_report():
    """
    生成每日报告

    每天8点执行
    """
    logger.info("生成每日报告...")

    try:
        # 获取昨天的数据
        yesterday = datetime.now() - timedelta(days=1)
        start_of_day = yesterday.replace(hour=0, minute=0, second=0)
        end_of_day = yesterday.replace(hour=23, minute=59, second=59)

        with db_manager.get_session() as db:
            # 查询昨天的快照
            from src.database.models import AnalyticsSnapshot

            snapshots = db.query(AnalyticsSnapshot).filter(
                AnalyticsSnapshot.snapshot_date >= start_of_day,
                AnalyticsSnapshot.snapshot_date <= end_of_day,
                AnalyticsSnapshot.snapshot_type == "hourly"
            ).all()

            if not snapshots:
                logger.warning("没有找到昨天的数据")
                return {"success": False, "error": "No data"}

            # 汇总数据
            total_new_followers = sum(s.new_followers for s in snapshots)
            total_views = sum(s.total_views for s in snapshots)

            # 生成报告
            report = f"""📊 每日运营报告 - {yesterday.strftime('%Y-%m-%d')}

核心指标：
• 新增粉丝: {total_new_followers}
• 总阅读量: {total_views}
• 发布文章: {sum(s.total_articles for s in snapshots)}

详细数据已保存到数据库。"""

            # 保存报告
            report_path = f"output/reports/daily_{yesterday.strftime('%Y%m%d')}.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"报告生成完成: {report_path}")

            return {
                "success": True,
                "report_path": report_path,
                "new_followers": total_new_followers,
                "total_views": total_views
            }

    except Exception as e:
        logger.error(f"报告生成失败: {e}")
        return {"success": False, "error": str(e)}


@shared_task(name="src.tasks.analytics_tasks.update_user_profiles")
def update_user_profiles():
    """
    更新用户画像

    每天执行一次
    """
    logger.info("更新用户画像...")

    with db_manager.get_session() as db:
        from src.database.models import User
        # 获取活跃用户
        active_users = db.query(User).filter(
            User.is_subscribed == True,
            User.last_interaction_time >= datetime.now() - timedelta(days=7)
        ).all()

        logger.info(f"更新 {len(active_users)} 个活跃用户画像")

        # 这里可以添加RFM分析、用户分层等逻辑

        return {"updated": len(active_users)}
