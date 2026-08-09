"""
Celery 应用配置
"""
from celery import Celery
from kombu import Exchange, Queue
import os

# Redis 配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
BACKEND_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB + 1}"

# 创建 Celery 应用
celery_app = Celery(
    "fieldmind",
    broker=BROKER_URL,
    backend=BACKEND_URL,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.audio_tasks",
        "app.tasks.crawler_tasks",
        "app.tasks.rag_tasks",
        "app.tasks.graph_tasks",
        "app.tasks.report_tasks",
    ]
)

# Celery 配置
celery_app.conf.update(
    # 任务结果过期时间（24小时）
    result_expires=86400,

    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # 任务路由
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "documents"},
        "app.tasks.audio_tasks.*": {"queue": "audio"},
        "app.tasks.crawler_tasks.*": {"queue": "crawler"},
        "app.tasks.rag_tasks.*": {"queue": "rag"},
        "app.tasks.graph_tasks.*": {"queue": "graph"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },

    # 任务队列定义
    task_queues=(
        Queue("documents", Exchange("documents"), routing_key="documents"),
        Queue("audio", Exchange("audio"), routing_key="audio"),
        Queue("crawler", Exchange("crawler"), routing_key="crawler"),
        Queue("rag", Exchange("rag"), routing_key="rag"),
        Queue("graph", Exchange("graph"), routing_key="graph"),
        Queue("reports", Exchange("reports"), routing_key="reports"),
        Queue("default", Exchange("default"), routing_key="default"),
    ),

    # 并发配置
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # 任务限流
    task_annotations={
        "app.tasks.crawler_tasks.*": {"rate_limit": "10/m"},  # 爬虫限速
        "app.tasks.audio_tasks.transcribe_audio": {"rate_limit": "5/m"},  # 转录限速
    },

    # 重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# 定期任务（可选）
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "app.tasks.maintenance.cleanup_old_tasks",
        "schedule": 3600.0,  # 每小时执行一次
    },
}
