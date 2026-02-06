"""
Celery应用定义
"""
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Celery配置
celery_app = Celery(
    "wechat_auto",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=["src.tasks.content_tasks", "src.tasks.analytics_tasks"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时
    task_soft_time_limit=3000,  # 50分钟
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# 定时任务配置
celery_app.conf.beat_schedule = {
    # 每小时采集数据
    "hourly-data-collection": {
        "task": "src.tasks.analytics_tasks.collect_analytics_data",
        "schedule": 3600,  # 每小时
    },

    # 每日生成报告（每天8点）
    "daily-report-generation": {
        "task": "src.tasks.analytics_tasks.generate_daily_report",
        "schedule": crontab(hour=8, minute=0),
    },

    # 检查待发布内容（每10分钟）
    "check-scheduled-content": {
        "task": "src.tasks.content_tasks.publish_scheduled_content",
        "schedule": 600,  # 每10分钟
    },

    # 热点监控（每30分钟）
    "trending-monitor": {
        "task": "src.tasks.content_tasks.monitor_trending_topics",
        "schedule": 1800,  # 每30分钟
    },
}
