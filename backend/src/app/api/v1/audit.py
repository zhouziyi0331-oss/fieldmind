"""审计日志API端点"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.audit_log import AuditLog, ActorType, ActionType, AuditResult
from app.services.audit_service import AuditService
from app.core.logging import logger


router = APIRouter(prefix="/audit", tags=["audit"])


# ==================== Schemas ====================


class AuditLogResponse(BaseModel):
    """审计日志响应"""

    id: str
    timestamp: datetime
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    resource_name: Optional[str]
    project_id: Optional[str]
    changes: Optional[dict]
    ai_model: Optional[str]
    ai_prompt: Optional[str]
    result: str
    error_message: Optional[str]
    duration_ms: Optional[int]
    extra_metadata: Optional[dict]

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""

    logs: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditStatisticsResponse(BaseModel):
    """审计统计响应"""

    total_logs: int
    by_actor_type: dict
    by_action_type: dict
    by_result: dict


# ==================== API端点 ====================


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="项目ID"),
    actor_type: Optional[str] = Query(None, description="操作者类型"),
    actor_id: Optional[str] = Query(None, description="操作者ID"),
    action: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    resource_id: Optional[str] = Query(None, description="资源ID"),
    result: Optional[str] = Query(None, description="操作结果"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """查询审计日志

    支持多种过滤条件，返回分页结果
    """
    try:
        # 转换枚举类型
        actor_type_enum = ActorType(actor_type) if actor_type else None
        action_enum = ActionType(action) if action else None
        result_enum = AuditResult(result) if result else None

        logs, total = await AuditService.query_logs(
            db=db,
            project_id=project_id,
            actor_type=actor_type_enum,
            actor_id=actor_id,
            action=action_enum,
            resource_type=resource_type,
            resource_id=resource_id,
            result=result_enum,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )

        return AuditLogListResponse(
            logs=[AuditLogResponse.from_orm(log) for log in logs],
            total=total,
            limit=limit,
            offset=offset,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to query audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to query audit logs")


@router.get("/resource/{resource_type}/{resource_id}", response_model=List[AuditLogResponse])
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
):
    """获取资源的操作历史

    返回指定资源的所有操作记录
    """
    try:
        logs = await AuditService.get_resource_history(
            db=db,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )

        return [AuditLogResponse.from_orm(log) for log in logs]

    except Exception as e:
        logger.error(f"Failed to get resource history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get resource history")


@router.get("/user/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: str,
    db: Session = Depends(get_db),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
):
    """获取用户活动记录

    返回指定用户的所有操作记录
    """
    try:
        logs = await AuditService.get_user_activity(
            db=db,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return [AuditLogResponse.from_orm(log) for log in logs]

    except Exception as e:
        logger.error(f"Failed to get user activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user activity")


@router.get("/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="项目ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
):
    """获取审计统计信息

    返回审计日志的统计数据
    """
    try:
        stats = await AuditService.get_statistics(
            db=db,
            project_id=project_id,
            start_time=start_time,
            end_time=end_time,
        )

        return AuditStatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get audit statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get audit statistics")


@router.delete("/cleanup")
async def cleanup_old_logs(
    db: Session = Depends(get_db),
    retention_days: int = Query(15, ge=1, le=365, description="保留天数"),
):
    """清理过期审计日志

    删除超过指定天数的审计日志记录
    需要管理员权限
    """
    try:
        deleted_count = await AuditService.cleanup_old_logs(
            db=db,
            retention_days=retention_days,
        )

        return {
            "message": f"Successfully cleaned up {deleted_count} audit logs",
            "deleted_count": deleted_count,
            "retention_days": retention_days,
        }

    except Exception as e:
        logger.error(f"Failed to cleanup audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to cleanup audit logs")
