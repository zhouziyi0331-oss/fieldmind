"""
Celery 配置
异步任务队列
"""

import os
from celery import Celery
from kombu import Exchange, Queue

# Redis 连接配置
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# 构建 Redis URL
if REDIS_PASSWORD:
    BROKER_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

RESULT_BACKEND = BROKER_URL

# 创建 Celery 应用
celery_app = Celery(
    "fieldmind",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "app.tasks.document_tasks",
        "app.tasks.processing_tasks",
    ]
)

# Celery 配置
celery_app.conf.update(
    # 任务结果配置
    result_expires=3600,  # 结果保留1小时
    result_backend_transport_options={
        'master_name': 'mymaster'
    },

    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # 任务路由
    task_routes={
        'app.tasks.document_tasks.*': {'queue': 'documents'},
        'app.tasks.processing_tasks.*': {'queue': 'processing'},
    },

    # 任务优先级
    task_default_priority=5,
    task_queue_max_priority=10,

    # 并发配置
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,

    # 任务时间限制
    task_time_limit=3600,  # 硬限制：1小时
    task_soft_time_limit=3000,  # 软限制：50分钟

    # 任务重试
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # 监控
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# 定义队列
celery_app.conf.task_queues = (
    # 默认队列
    Queue('default', Exchange('default'), routing_key='default'),

    # 文档处理队列
    Queue('documents', Exchange('documents'), routing_key='documents.*'),

    # 内容处理队列（优先级高）
    Queue('processing', Exchange('processing'), routing_key='processing.*', priority=8),

    # 低优先级队列
    Queue('low_priority', Exchange('low_priority'), routing_key='low.*', priority=2),
)

# 定义默认队列
celery_app.conf.task_default_queue = 'default'
celery_app.conf.task_default_exchange = 'default'
celery_app.conf.task_default_routing_key = 'default'


# 任务装饰器配置
def make_task(**options):
    """
    创建任务装饰器的辅助函数

    Args:
        **options: Celery 任务选项
    """
    default_options = {
        'bind': True,
        'max_retries': 3,
        'default_retry_delay': 60,
    }
    default_options.update(options)

    return celery_app.task(**default_options)


# Celery 信号处理
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_success
)

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """任务开始前"""
    from app.core.logging import logger
    logger.info(f"任务开始: {task.name}", task_id=task_id)


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):
    """任务完成后"""
    from app.core.logging import logger
    logger.info(f"任务完成: {task.name}", task_id=task_id)


@task_success.connect
def task_success_handler(sender=None, result=None, **extra):
    """任务成功"""
    from app.core.logging import logger
    logger.info(f"任务成功: {sender.name}", result=str(result)[:100])


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
    """任务失败"""
    from app.core.logging import logger
    logger.error(
        f"任务失败: {sender.name}",
        task_id=task_id,
        exception=str(exception),
        traceback=str(traceback)[:500]
    )
