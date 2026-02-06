"""
内容相关Celery任务
"""
from celery import shared_task
from datetime import datetime, timedelta
from src.database.crud import ContentCRUD, ContentSchedule
from src.database.session import db_manager
from src.wechat.api_client import wechat_api_client
import logging

logger = logging.getLogger(__name__)


@shared_task(name="src.tasks.content_tasks.publish_scheduled_content")
def publish_scheduled_content():
    """
    发布到期的定时内容

    每10分钟执行一次，检查并发布到期内容
    """
    logger.info("检查待发布内容...")

    with db_manager.get_session() as db:
        # 获取待发布的调度任务
        schedules = ContentCRUD.get_pending_schedules(
            db,
            before_time=datetime.now()
        )

        logger.info(f"找到 {len(schedules)} 个待发布任务")

        for schedule in schedules:
            try:
                content = schedule.content

                # 上传到微信
                media_id = upload_to_wechat(content)

                if media_id:
                    # 更新内容状态
                    ContentCRUD.update_content(
                        db,
                        content.id,
                        status="published",
                        publish_time=datetime.now(),
                        wechat_media_id=media_id
                    )

                    # 更新调度状态
                    schedule.status = "success"
                    schedule.executed_at = datetime.now()

                    logger.info(f"内容 {content.id} 发布成功")
                else:
                    # 发布失败
                    schedule.status = "failed"
                    schedule.error_message = "上传微信失败"
                    schedule.retry_count += 1

                    # 如果重试次数未超限，重新调度
                    if schedule.retry_count < schedule.max_retries:
                        schedule.status = "pending"

            except Exception as e:
                logger.error(f"发布内容 {schedule.content_id} 失败: {e}")
                schedule.status = "failed"
                schedule.error_message = str(e)
                schedule.retry_count += 1

    return {"published": len(schedules)}


def upload_to_wechat(content):
    """
    上传内容到微信

    Args:
        content: Content对象

    Returns:
        media_id or None
    """
    try:
        # 构建图文消息
        articles = [{
            "title": content.title,
            "author": "AI Assistant",
            "digest": content.summary,
            "content": content.content,
            "content_source_url": "",
            "thumb_media_id": ""  # 缩略图media_id
        }]

        # 上传草稿
        result = wechat_api_client.add_draft(articles)

        if result.get("media_id"):
            return result["media_id"]

        return None

    except Exception as e:
        logger.error(f"上传微信失败: {e}")
        return None


@shared_task(name="src.tasks.content_tasks.monitor_trending_topics")
def monitor_trending_topics():
    """
    监控热点话题

    每30分钟执行一次
    """
    logger.info("监控热点话题...")

    # 这里可以实现热点监控逻辑
    # 例如：爬取微博热搜、百度指数等

    topics = []

    # 缓存热点话题
    from src.cache.redis_client import cache_manager
    cache_manager.set_trending_topics(topics, ttl=1800)

    logger.info(f"发现 {len(topics)} 个热点话题")
    return {"topics": len(topics)}


@shared_task(name="src.tasks.content_tasks.generate_content_from_topic")
def generate_content_from_topic(topic: str, content_type: str = "article"):
    """
    根据选题自动生成内容

    Args:
        topic: 选题
        content_type: 内容类型
    """
    logger.info(f"生成内容: {topic}")

    # 这里可以调用Content Agent生成内容
    # 简化实现

    return {"topic": topic, "status": "generated"}
