"""
批量文档处理API端点

提供批量处理文档的接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.deps import get_db
from app.services.enhanced_batch_service import EnhancedBatchService

router = APIRouter()


# ==================== Pydantic 模型 ====================

class BatchProcessRequest(BaseModel):
    """批量处理请求"""
    document_ids: List[int] = Field(..., description="文档ID列表")
    operation_type: str = Field(..., description="操作类型: extract|analyze|distill|index")
    operation_config: Optional[dict] = Field(None, description="操作配置")


class BatchStatusResponse(BaseModel):
    """批处理状态响应"""
    batch_id: str
    project_id: int
    operation_type: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    created_at: str
    error_message: Optional[str] = None
    result_summary: Optional[dict] = None


class BatchOperationSummary(BaseModel):
    """批处理操作摘要"""
    batch_id: str
    project_id: int
    operation_type: str
    status: str
    total_items: int
    completed_items: int
    failed_items: int
    created_at: str


# ==================== 依赖项 ====================

def get_batch_service(db: Session = Depends(get_db)) -> EnhancedBatchService:
    """获取批量处理服务"""
    return EnhancedBatchService(db, max_workers=3)


# ==================== 批量处理 ====================

@router.post("/projects/{project_id}/batch-process", summary="批量处理文档")
async def batch_process_documents(
    project_id: int = Path(..., description="项目ID"),
    request: BatchProcessRequest = Body(...),
    service: EnhancedBatchService = Depends(get_batch_service)
):
    """
    批量处理文档

    支持的操作类型：
    - extract: 提取文档内容
    - analyze: 分析文档
    - distill: 蒸馏知识
    - index: 建立索引

    返回批处理ID，可通过WebSocket或轮询获取进度
    """
    result = await service.batch_process_documents(
        project_id=project_id,
        document_ids=request.document_ids,
        operation_type=request.operation_type,
        operation_config=request.operation_config
    )

    return result


@router.get("/batch/{batch_id}", response_model=BatchStatusResponse, summary="获取批处理状态")
async def get_batch_status(
    batch_id: str = Path(..., description="批处理ID"),
    service: EnhancedBatchService = Depends(get_batch_service)
):
    """
    获取批处理状态

    返回批处理的详细状态信息
    """
    status = service.get_batch_status(batch_id)

    if not status:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="批处理不存在")

    return BatchStatusResponse(**status)


@router.get("/batch/{batch_id}/progress", summary="获取批处理进度")
async def get_batch_progress(
    batch_id: str = Path(..., description="批处理ID"),
    service: EnhancedBatchService = Depends(get_batch_service)
):
    """
    获取批处理实时进度

    返回：
    - total: 总数
    - completed: 已完成
    - failed: 失败数
    - progress_percent: 进度百分比
    """
    progress = service.get_batch_progress(batch_id)

    if not progress:
        return {
            "batch_id": batch_id,
            "progress": None,
            "message": "批处理不存在或未开始"
        }

    return {
        "batch_id": batch_id,
        "progress": progress
    }


@router.get("/batch-operations", response_model=List[BatchOperationSummary], summary="列出批处理操作")
async def list_batch_operations(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    status: Optional[str] = Query(None, description="筛选状态"),
    limit: int = Query(50, description="返回数量", ge=1, le=200),
    service: EnhancedBatchService = Depends(get_batch_service)
):
    """
    列出批处理操作

    支持按项目和状态筛选
    """
    operations = service.list_batch_operations(
        project_id=project_id,
        status=status,
        limit=limit
    )

    return [BatchOperationSummary(**op) for op in operations]


@router.post("/batch/{batch_id}/retry", summary="重试失败项目")
async def retry_failed_items(
    batch_id: str = Path(..., description="批处理ID"),
    service: EnhancedBatchService = Depends(get_batch_service)
):
    """
    重试批处理中失败的项目

    创建新的批处理任务，只处理原批次中失败的项目
    """
    result = await service.retry_failed_items(batch_id)
    return result


@router.get("/health", summary="健康检查")
async def health_check():
    """批量处理服务健康检查"""
    return {
        "status": "healthy",
        "service": "batch_processing"
    }
