"""
任务管理工具
查询和管理 Celery 任务
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from celery.result import AsyncResult
from app.core.celery_app import celery_app
from app.core.logging import logger


class TaskManager:
    """任务管理器"""

    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            Dict: 任务状态信息
        """
        result = AsyncResult(task_id, app=celery_app)

        return {
            "task_id": task_id,
            "state": result.state,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback,
            "info": result.info,
        }

    @staticmethod
    def cancel_task(task_id: str, terminate: bool = False) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID
            terminate: 是否强制终止（谨慎使用）

        Returns:
            bool: 是否成功
        """
        result = AsyncResult(task_id, app=celery_app)

        try:
            if terminate:
                result.revoke(terminate=True, signal='SIGKILL')
            else:
                result.revoke()

            logger.info(f"任务已取消: {task_id}", terminate=terminate)
            return True

        except Exception as e:
            logger.error(f"取消任务失败: {e}", task_id=task_id)
            return False

    @staticmethod
    def retry_task(task_id: str) -> Optional[str]:
        """
        重试失败的任务

        Args:
            task_id: 任务ID

        Returns:
            Optional[str]: 新任务ID
        """
        result = AsyncResult(task_id, app=celery_app)

        if result.state == 'FAILURE':
            # 获取原始任务参数
            # 注意：这需要任务结果包含足够的信息
            try:
                # 重新提交任务
                # 这里需要根据实际任务类型来调度
                logger.info(f"重试任务: {task_id}")
                # 实际实现需要更多上下文信息
                return None

            except Exception as e:
                logger.error(f"重试任务失败: {e}", task_id=task_id)
                return None

        return None

    @staticmethod
    def get_active_tasks() -> List[Dict[str, Any]]:
        """
        获取活跃的任务

        Returns:
            List[Dict]: 活跃任务列表
        """
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()

        if not active_tasks:
            return []

        tasks = []
        for worker, task_list in active_tasks.items():
            for task in task_list:
                tasks.append({
                    "worker": worker,
                    "task_id": task.get("id"),
                    "name": task.get("name"),
                    "args": task.get("args"),
                    "kwargs": task.get("kwargs"),
                    "time_start": task.get("time_start"),
                })

        return tasks

    @staticmethod
    def get_scheduled_tasks() -> List[Dict[str, Any]]:
        """
        获取计划中的任务

        Returns:
            List[Dict]: 计划任务列表
        """
        inspect = celery_app.control.inspect()
        scheduled = inspect.scheduled()

        if not scheduled:
            return []

        tasks = []
        for worker, task_list in scheduled.items():
            for task in task_list:
                tasks.append({
                    "worker": worker,
                    "task_id": task.get("request", {}).get("id"),
                    "name": task.get("request", {}).get("name"),
                    "eta": task.get("eta"),
                })

        return tasks

    @staticmethod
    def get_worker_stats() -> Dict[str, Any]:
        """
        获取 Worker 统计信息

        Returns:
            Dict: Worker 统计
        """
        inspect = celery_app.control.inspect()

        stats = inspect.stats()
        active = inspect.active()
        registered = inspect.registered()

        worker_info = {}

        if stats:
            for worker, stat in stats.items():
                worker_info[worker] = {
                    "stats": stat,
                    "active_tasks": len(active.get(worker, [])) if active else 0,
                    "registered_tasks": len(registered.get(worker, [])) if registered else 0,
                }

        return worker_info

    @staticmethod
    def purge_queue(queue_name: str) -> int:
        """
        清空队列

        Args:
            queue_name: 队列名称

        Returns:
            int: 清除的任务数量
        """
        try:
            count = celery_app.control.purge()
            logger.info(f"清空队列: {queue_name}, 清除 {count} 个任务")
            return count

        except Exception as e:
            logger.error(f"清空队列失败: {e}", queue_name=queue_name)
            return 0


class TaskMonitor:
    """任务监控器"""

    @staticmethod
    def get_task_metrics(hours: int = 24) -> Dict[str, Any]:
        """
        获取任务指标

        Args:
            hours: 统计时间范围（小时）

        Returns:
            Dict: 任务指标
        """
        # 这里需要从 Redis 或数据库查询任务执行历史
        # 暂时返回示例数据

        return {
            "time_range": f"last_{hours}_hours",
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "pending_tasks": 0,
            "average_duration": 0.0,
        }

    @staticmethod
    def get_queue_length(queue_name: str) -> int:
        """
        获取队列长度

        Args:
            queue_name: 队列名称

        Returns:
            int: 队列中的任务数量
        """
        try:
            # 从 Redis 获取队列长度
            from app.core.celery_app import celery_app

            with celery_app.connection_or_acquire() as conn:
                return conn.default_channel.queue_declare(
                    queue=queue_name,
                    passive=True
                ).message_count

        except Exception as e:
            logger.error(f"获取队列长度失败: {e}", queue_name=queue_name)
            return 0

    @staticmethod
    def get_task_history(
        document_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取文档的任务历史

        Args:
            document_id: 文档ID
            limit: 返回数量限制

        Returns:
            List[Dict]: 任务历史
        """
        # 这里需要从数据库查询任务执行记录
        # 暂时返回空列表

        return []


# 便捷函数
def submit_document_processing(document_id: str) -> str:
    """
    提交文档处理任务

    Args:
        document_id: 文档ID

    Returns:
        str: 任务ID
    """
    from app.tasks.document_tasks import process_document_task

    result = process_document_task.apply_async(
        args=[document_id],
        queue='documents'
    )

    logger.info(f"提交文档处理任务: {document_id}, task_id: {result.id}")

    return result.id


def get_task_progress(task_id: str) -> Dict[str, Any]:
    """
    获取任务进度

    Args:
        task_id: 任务ID

    Returns:
        Dict: 进度信息
    """
    return TaskManager.get_task_status(task_id)


def cancel_document_processing(task_id: str) -> bool:
    """
    取消文档处理任务

    Args:
        task_id: 任务ID

    Returns:
        bool: 是否成功
    """
    return TaskManager.cancel_task(task_id)
