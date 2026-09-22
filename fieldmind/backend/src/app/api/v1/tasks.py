"""
任务管理 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.response import success_response, ApiResponse
from app.core.task_manager import (
    TaskManager,
    TaskMonitor,
    submit_document_processing,
    get_task_progress,
    cancel_document_processing
)


router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/documents/{document_id}/process", response_model=ApiResponse)
async def trigger_document_processing(
    document_id: str,
    request: Request
):
    """
    触发文档处理任务

    提交文档到异步处理队列

    Args:
        document_id: 文档ID

    Returns:
        任务ID和状态
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        task_id = submit_document_processing(document_id)

        return success_response(
            data={
                "document_id": document_id,
                "task_id": task_id,
                "status": "submitted"
            },
            request_id=request_id,
            message="Document processing task submitted"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/status", response_model=ApiResponse)
async def get_task_status(
    task_id: str,
    request: Request
):
    """
    获取任务状态

    查询任务的当前状态和结果

    可能的状态：
    - PENDING: 等待执行
    - STARTED: 正在执行
    - SUCCESS: 执行成功
    - FAILURE: 执行失败
    - RETRY: 正在重试
    - REVOKED: 已取消
    """
    request_id = getattr(request.state, "request_id", None)

    status = TaskManager.get_task_status(task_id)

    return success_response(
        data=status,
        request_id=request_id
    )


@router.post("/{task_id}/cancel", response_model=ApiResponse)
async def cancel_task(
    task_id: str,
    request: Request,
    terminate: bool = False
):
    """
    取消任务

    取消正在执行或等待中的任务

    Args:
        task_id: 任务ID
        terminate: 是否强制终止（谨慎使用）
    """
    request_id = getattr(request.state, "request_id", None)

    success = TaskManager.cancel_task(task_id, terminate=terminate)

    if success:
        return success_response(
            data={
                "task_id": task_id,
                "status": "cancelled"
            },
            request_id=request_id,
            message="Task cancelled successfully"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/active", response_model=ApiResponse)
async def list_active_tasks(request: Request):
    """
    获取活跃任务列表

    返回当前正在执行的所有任务
    """
    request_id = getattr(request.state, "request_id", None)

    tasks = TaskManager.get_active_tasks()

    return success_response(
        data={
            "tasks": tasks,
            "count": len(tasks)
        },
        request_id=request_id
    )


@router.get("/scheduled", response_model=ApiResponse)
async def list_scheduled_tasks(request: Request):
    """
    获取计划任务列表

    返回计划在未来执行的任务
    """
    request_id = getattr(request.state, "request_id", None)

    tasks = TaskManager.get_scheduled_tasks()

    return success_response(
        data={
            "tasks": tasks,
            "count": len(tasks)
        },
        request_id=request_id
    )


@router.get("/workers", response_model=ApiResponse)
async def get_worker_stats(request: Request):
    """
    获取 Worker 统计信息

    返回所有 Worker 的状态和统计数据
    """
    request_id = getattr(request.state, "request_id", None)

    stats = TaskManager.get_worker_stats()

    return success_response(
        data=stats,
        request_id=request_id
    )


@router.get("/metrics", response_model=ApiResponse)
async def get_task_metrics(
    request: Request,
    hours: int = 24
):
    """
    获取任务指标

    返回指定时间范围内的任务统计

    Args:
        hours: 统计时间范围（小时），默认24小时
    """
    request_id = getattr(request.state, "request_id", None)

    metrics = TaskMonitor.get_task_metrics(hours=hours)

    return success_response(
        data=metrics,
        request_id=request_id
    )


@router.get("/queues/{queue_name}/length", response_model=ApiResponse)
async def get_queue_length(
    queue_name: str,
    request: Request
):
    """
    获取队列长度

    返回指定队列中等待的任务数量

    可用队列：
    - default: 默认队列
    - documents: 文档处理队列
    - processing: 内容处理队列
    - low_priority: 低优先级队列
    """
    request_id = getattr(request.state, "request_id", None)

    length = TaskMonitor.get_queue_length(queue_name)

    return success_response(
        data={
            "queue_name": queue_name,
            "length": length
        },
        request_id=request_id
    )


@router.delete("/queues/{queue_name}", response_model=ApiResponse)
async def purge_queue(
    queue_name: str,
    request: Request
):
    """
    清空队列

    删除指定队列中的所有任务（谨慎使用）

    Args:
        queue_name: 队列名称
    """
    request_id = getattr(request.state, "request_id", None)

    count = TaskManager.purge_queue(queue_name)

    return success_response(
        data={
            "queue_name": queue_name,
            "purged_count": count
        },
        request_id=request_id,
        message=f"Purged {count} tasks from queue"
    )
