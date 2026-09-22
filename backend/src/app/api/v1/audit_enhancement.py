"""审计日志增强API端点"""
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.audit_service import AuditService
from app.services.audit_enhancement_service import (
    AuditEnhancementService,
    AnomalyDetector,
    ComplianceReporter,
    AuditExporter,
)
from app.core.logging import logger


router = APIRouter()


# ==================== Schemas ====================


class AnomalyCheckRequest(BaseModel):
    """异常检测请求"""
    actor_id: str = Field(..., description="操作者ID")


class AnomalyCheckResponse(BaseModel):
    """异常检测响应"""
    actor_id: str
    anomalies: List[dict]
    total_anomalies: int


class ComplianceReportRequest(BaseModel):
    """合规报告请求"""
    report_type: str = Field(..., description="报告类型: user_activity, project_audit, security_audit")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    target_id: Optional[str] = Field(None, description="目标ID（用户ID或项目ID）")


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field(..., description="导出格式: json, csv")
    project_id: Optional[str] = Field(None, description="项目ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(1000, ge=1, le=10000, description="最大导出数量")


class LogWithEventRequest(BaseModel):
    """带事件推送的日志创建请求"""
    session_id: str = Field(..., description="会话ID")
    actor_type: str = Field(..., description="操作者类型")
    actor_id: str = Field(..., description="操作者ID")
    action: str = Field(..., description="操作类型")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源ID")
    resource_name: Optional[str] = Field(None, description="资源名称")
    project_id: Optional[str] = Field(None, description="项目ID")
    changes: Optional[dict] = Field(None, description="变更内容")
    ai_model: Optional[str] = Field(None, description="AI模型")
    ai_prompt: Optional[str] = Field(None, description="AI提示词")
    result: str = Field("success", description="操作结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    duration_ms: Optional[int] = Field(None, description="执行时长（毫秒）")
    extra_metadata: Optional[dict] = Field(None, description="额外元数据")


# ==================== API端点 ====================


@router.post("/logs/with-events", response_model=dict)
async def create_log_with_events(
    request: LogWithEventRequest,
    db: Session = Depends(get_db),
):
    """创建审计日志并发送WebSocket事件

    创建审计日志记录，同时通过WebSocket实时推送事件
    """
    try:
        from app.models.audit_log import ActorType, ActionType, AuditResult

        service = AuditEnhancementService()

        # 转换枚举类型
        actor_type = ActorType(request.actor_type)
        action = ActionType(request.action)
        result = AuditResult(request.result)

        audit_log = await service.log_with_events(
            db=db,
            session_id=request.session_id,
            actor_type=actor_type,
            actor_id=request.actor_id,
            action=action,
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            resource_name=request.resource_name,
            project_id=request.project_id,
            changes=request.changes,
            ai_model=request.ai_model,
            ai_prompt=request.ai_prompt,
            result=result,
            error_message=request.error_message,
            duration_ms=request.duration_ms,
            extra_metadata=request.extra_metadata,
        )

        return {
            "log_id": audit_log.id,
            "timestamp": audit_log.timestamp.isoformat(),
            "result": audit_log.result.value,
            "message": "Audit log created and event emitted",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid enum value: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create audit log with events: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create audit log")


@router.post("/anomaly/detect", response_model=AnomalyCheckResponse)
async def detect_anomalies(
    request: AnomalyCheckRequest,
    db: Session = Depends(get_db),
):
    """检测异常行为

    运行所有异常检测规则，识别可疑操作模式
    """
    try:
        detector = AnomalyDetector()

        anomalies = await detector.run_all_checks(
            db=db,
            actor_id=request.actor_id,
        )

        return AnomalyCheckResponse(
            actor_id=request.actor_id,
            anomalies=anomalies,
            total_anomalies=len(anomalies),
        )

    except Exception as e:
        logger.error(f"Failed to detect anomalies: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to detect anomalies")


@router.get("/anomaly/rapid-operations/{actor_id}", response_model=dict)
async def check_rapid_operations(
    actor_id: str,
    time_window_minutes: int = Query(1, ge=1, le=60, description="时间窗口（分钟）"),
    db: Session = Depends(get_db),
):
    """检测快速连续操作

    检查指定时间窗口内的操作频率
    """
    try:
        detector = AnomalyDetector()

        result = await detector.detect_rapid_operations(
            db=db,
            actor_id=actor_id,
            time_window_minutes=time_window_minutes,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to check rapid operations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check rapid operations")


@router.get("/anomaly/failed-operations/{actor_id}", response_model=dict)
async def check_failed_operations(
    actor_id: str,
    limit: int = Query(10, ge=1, le=50, description="检查最近的操作数"),
    db: Session = Depends(get_db),
):
    """检测连续失败操作

    检查最近操作中的连续失败模式
    """
    try:
        detector = AnomalyDetector()

        result = await detector.detect_failed_operations(
            db=db,
            actor_id=actor_id,
            limit=limit,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to check failed operations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check failed operations")


@router.get("/anomaly/unusual-time", response_model=dict)
async def check_unusual_time_activity(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db),
):
    """检测异常时间段活动

    检查非工作时间的操作记录
    """
    try:
        detector = AnomalyDetector()

        result = await detector.detect_unusual_time_activity(
            db=db,
            start_time=start_time,
            end_time=end_time,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to check unusual time activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check unusual time activity")


@router.get("/anomaly/bulk-deletes/{actor_id}", response_model=dict)
async def check_bulk_deletes(
    actor_id: str,
    time_window_minutes: int = Query(5, ge=1, le=60, description="时间窗口（分钟）"),
    db: Session = Depends(get_db),
):
    """检测批量删除操作

    检查指定时间窗口内的删除操作数量
    """
    try:
        detector = AnomalyDetector()

        result = await detector.detect_bulk_deletes(
            db=db,
            actor_id=actor_id,
            time_window_minutes=time_window_minutes,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to check bulk deletes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check bulk deletes")


@router.post("/reports/compliance", response_model=dict)
async def generate_compliance_report(
    request: ComplianceReportRequest,
    db: Session = Depends(get_db),
):
    """生成合规性报告

    支持三种报告类型：
    - user_activity: 用户活动报告
    - project_audit: 项目审计报告
    - security_audit: 安全审计报告
    """
    try:
        reporter = ComplianceReporter()

        if request.report_type == "user_activity":
            if not request.target_id:
                raise HTTPException(status_code=400, detail="user_id is required for user_activity report")

            report = await reporter.generate_user_activity_report(
                db=db,
                user_id=request.target_id,
                start_time=request.start_time,
                end_time=request.end_time,
            )

        elif request.report_type == "project_audit":
            if not request.target_id:
                raise HTTPException(status_code=400, detail="project_id is required for project_audit report")

            report = await reporter.generate_project_audit_report(
                db=db,
                project_id=request.target_id,
                start_time=request.start_time,
                end_time=request.end_time,
            )

        elif request.report_type == "security_audit":
            report = await reporter.generate_security_audit_report(
                db=db,
                start_time=request.start_time,
                end_time=request.end_time,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report_type: {request.report_type}. Must be one of: user_activity, project_audit, security_audit"
            )

        return {
            "report_type": request.report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "data": report,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance report")


@router.post("/export")
async def export_audit_logs(
    request: ExportRequest,
    db: Session = Depends(get_db),
):
    """导出审计日志

    支持JSON和CSV格式导出
    """
    try:
        # 查询审计日志
        logs, _ = await AuditService.query_logs(
            db=db,
            project_id=request.project_id,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit,
        )

        if not logs:
            raise HTTPException(status_code=404, detail="No audit logs found")

        exporter = AuditExporter()

        if request.format == "json":
            content = await exporter.export_to_json(logs)
            media_type = "application/json"
            filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        elif request.format == "csv":
            content = await exporter.export_to_csv(logs)
            media_type = "text/csv"
            filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format: {request.format}. Must be 'json' or 'csv'"
            )

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export audit logs")


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """审计增强系统健康检查

    检查服务状态和统计信息
    """
    try:
        # 获取最近24小时的统计
        start_time = datetime.utcnow() - timedelta(hours=24)
        stats = await AuditService.get_statistics(
            db=db,
            start_time=start_time,
        )

        return {
            "status": "healthy",
            "service": "audit_enhancement",
            "timestamp": datetime.utcnow().isoformat(),
            "features": {
                "realtime_events": True,
                "anomaly_detection": True,
                "compliance_reports": True,
                "data_export": True,
            },
            "last_24h_stats": stats,
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "audit_enhancement",
            "error": str(e),
        }


@router.get("/statistics/timeline")
async def get_timeline_statistics(
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="项目ID"),
    days: int = Query(7, ge=1, le=90, description="天数"),
):
    """获取时间线统计

    返回指定天数内每天的操作统计
    """
    try:
        from collections import defaultdict
        from app.models.audit_log import AuditLog

        start_time = datetime.utcnow() - timedelta(days=days)
        end_time = datetime.utcnow()

        query = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time,
        )

        if project_id:
            query = query.filter(AuditLog.project_id == project_id)

        logs = query.all()

        # 按日期分组统计
        daily_stats = defaultdict(lambda: {
            "date": None,
            "total": 0,
            "successful": 0,
            "failed": 0,
            "by_action": defaultdict(int),
            "by_actor_type": defaultdict(int),
        })

        for log in logs:
            date_key = log.timestamp.date().isoformat()

            daily_stats[date_key]["date"] = date_key
            daily_stats[date_key]["total"] += 1

            if log.result.value == "success":
                daily_stats[date_key]["successful"] += 1
            else:
                daily_stats[date_key]["failed"] += 1

            daily_stats[date_key]["by_action"][log.action.value] += 1
            daily_stats[date_key]["by_actor_type"][log.actor_type.value] += 1

        # 转换为列表并排序
        timeline = sorted(
            [
                {
                    **stats,
                    "by_action": dict(stats["by_action"]),
                    "by_actor_type": dict(stats["by_actor_type"]),
                }
                for stats in daily_stats.values()
            ],
            key=lambda x: x["date"]
        )

        return {
            "period": {
                "start": start_time.date().isoformat(),
                "end": end_time.date().isoformat(),
                "days": days,
            },
            "project_id": project_id,
            "timeline": timeline,
            "summary": {
                "total_operations": sum(day["total"] for day in timeline),
                "total_successful": sum(day["successful"] for day in timeline),
                "total_failed": sum(day["failed"] for day in timeline),
            },
        }

    except Exception as e:
        logger.error(f"Failed to get timeline statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get timeline statistics")


@router.get("/statistics/top-actors")
async def get_top_actors(
    db: Session = Depends(get_db),
    project_id: Optional[str] = Query(None, description="项目ID"),
    days: int = Query(7, ge=1, le=90, description="天数"),
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
):
    """获取最活跃操作者

    返回指定时间段内操作最多的用户或AI
    """
    try:
        from collections import defaultdict
        from app.models.audit_log import AuditLog

        start_time = datetime.utcnow() - timedelta(days=days)

        query = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_time,
        )

        if project_id:
            query = query.filter(AuditLog.project_id == project_id)

        logs = query.all()

        # 统计每个操作者
        actor_stats = defaultdict(lambda: {
            "actor_id": None,
            "actor_type": None,
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "by_action": defaultdict(int),
        })

        for log in logs:
            key = f"{log.actor_type.value}:{log.actor_id}"

            actor_stats[key]["actor_id"] = log.actor_id
            actor_stats[key]["actor_type"] = log.actor_type.value
            actor_stats[key]["total_operations"] += 1

            if log.result.value == "success":
                actor_stats[key]["successful_operations"] += 1
            else:
                actor_stats[key]["failed_operations"] += 1

            actor_stats[key]["by_action"][log.action.value] += 1

        # 转换并排序
        top_actors = sorted(
            [
                {
                    **stats,
                    "by_action": dict(stats["by_action"]),
                }
                for stats in actor_stats.values()
            ],
            key=lambda x: x["total_operations"],
            reverse=True
        )[:limit]

        return {
            "period": {
                "start": start_time.date().isoformat(),
                "end": datetime.utcnow().date().isoformat(),
                "days": days,
            },
            "project_id": project_id,
            "top_actors": top_actors,
            "total_actors": len(actor_stats),
        }

    except Exception as e:
        logger.error(f"Failed to get top actors: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get top actors")
