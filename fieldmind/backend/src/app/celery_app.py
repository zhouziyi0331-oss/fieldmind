"""
Celery 应用配置 - 使用内存broker（不需要Redis）
"""
from celery import Celery
from kombu import Exchange, Queue
import os

# 使用内存broker而不是Redis
BROKER_URL = "memory://"
BACKEND_URL = "cache+memory://"

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

    # 任务优先级
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # 队列配置
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",

    # 定义队列
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("documents", Exchange("documents"), routing_key="documents"),
        Queue("audio", Exchange("audio"), routing_key="audio"),
        Queue("rag", Exchange("rag"), routing_key="rag"),
        Queue("graph", Exchange("graph"), routing_key="graph"),
        Queue("crawler", Exchange("crawler"), routing_key="crawler"),
        Queue("reports", Exchange("reports"), routing_key="reports"),
    ),

    # 任务路由
    task_routes={
        "app.tasks.document_tasks.*": {"queue": "documents"},
        "app.tasks.audio_tasks.*": {"queue": "audio"},
        "app.tasks.rag_tasks.*": {"queue": "rag"},
        "app.tasks.graph_tasks.*": {"queue": "graph"},
        "app.tasks.crawler_tasks.*": {"queue": "crawler"},
        "app.tasks.report_tasks.*": {"queue": "reports"},
    },

    # 超时设置
    task_soft_time_limit=3600,  # 1小时软限制
    task_time_limit=7200,  # 2小时硬限制

    # 日志
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)
