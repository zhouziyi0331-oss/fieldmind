"""定时任务API路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.schemas.response import success_response, error_response
from app.schemas.scheduler import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
    ScheduledTaskListResponse,
    ScheduledTaskExecutionResponse,
    ExecutionListResponse,
    TaskRunRequest,
    TaskRunResponse
)
from app.services.scheduler import scheduler_service
from app.services.scheduler_executor import executor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scheduler", tags=["定时任务"])


@router.post("/tasks", response_model=ScheduledTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_scheduled_task(
    task_data: ScheduledTaskCreate,
    db: Session = Depends(get_db)
):
    """
    创建定时任务

    支持的任务类型：
    - crawler: 定时爬取网页
    - report: 定时生成报告
    - quality_check: 定时质量检查
    - export: 定时导出数据
    - cleanup: 定时清理数据
    """
    try:
        # 如果任务类型需要项目ID，验证项目是否存在
        if task_data.task_type in ["report", "quality_check", "export"] and not task_data.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务类型 {task_data.task_type} 需要指定项目ID"
            )

        task = scheduler_service.create_task(
            db=db,
            project_id=task_data.project_id,
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            cron_expression=task_data.cron_expression,
            config=task_data.config,
            is_active=task_data.is_active
        )

        # 如果任务是激活状态，添加到调度器
        if task.is_active:
            scheduler_service.add_job_to_scheduler(task, get_db)

        return task

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建定时任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建定时任务失败: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """获取定时任务详情"""
    task = scheduler_service.get_task(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )
    return task


@router.get("/tasks", response_model=ScheduledTaskListResponse)
async def list_scheduled_tasks(
    project_id: Optional[int] = None,
    task_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    列出定时任务

    查询参数：
    - project_id: 按项目筛选
    - task_type: 按任务类型筛选
    - is_active: 按激活状态筛选
    - limit: 返回数量限制（默认50，最大100）
    - offset: 分页偏移量
    """
    if limit > 100:
        limit = 100

    tasks = scheduler_service.list_tasks(
        db=db,
        project_id=project_id,
        task_type=task_type,
        is_active=is_active,
        limit=limit,
        offset=offset
    )

    total = scheduler_service.count_tasks(
        db=db,
        project_id=project_id,
        task_type=task_type,
        is_active=is_active
    )

    return {
        "tasks": tasks,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.put("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: str,
    task_data: ScheduledTaskUpdate,
    db: Session = Depends(get_db)
):
    """更新定时任务"""
    try:
        task = scheduler_service.update_task(
            db=db,
            task_id=task_id,
            name=task_data.name,
            description=task_data.description,
            cron_expression=task_data.cron_expression,
            is_active=task_data.is_active,
            config=task_data.config,
            db_factory=get_db
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {task_id}"
            )

        return task

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"更新定时任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新定时任务失败: {str(e)}"
        )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """删除定时任务"""
    success = scheduler_service.delete_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务不存在: {task_id}"
        )


@router.post("/tasks/{task_id}/run", response_model=TaskRunResponse)
async def run_task_manually(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    手动立即执行任务

    不影响任务的定时调度，只是额外执行一次
    """
    try:
        result = await executor.execute_task_manually(db, task_id)

        return TaskRunResponse(
            execution_id=result["execution_id"],
            task_id=task_id,
            message="任务已开始执行",
            started_at=result.get("started_at")
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"手动执行任务失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行任务失败: {str(e)}"
        )


@router.get("/executions", response_model=ExecutionListResponse)
async def list_task_executions(
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    查询任务执行记录

    查询参数：
    - task_id: 按任务ID筛选
    - status: 按状态筛选 (running, success, failed)
    - limit: 返回数量限制（默认50，最大100）
    - offset: 分页偏移量
    """
    if limit > 100:
        limit = 100

    executions = scheduler_service.get_executions(
        db=db,
        task_id=task_id,
        status=status,
        limit=limit,
        offset=offset
    )

    total = scheduler_service.count_executions(
        db=db,
        task_id=task_id,
        status=status
    )

    return {
        "executions": executions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/executions/{execution_id}", response_model=ScheduledTaskExecutionResponse)
async def get_task_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """获取任务执行记录详情"""
    from app.models.scheduled_task import ScheduledTaskExecution

    execution = db.query(ScheduledTaskExecution).filter(
        ScheduledTaskExecution.id == execution_id
    ).first()

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行记录不存在: {execution_id}"
        )

    return execution
