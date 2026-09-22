"""
Quality Control API - 质量控制接口
提供质量检查、报告查询和统计功能
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.schemas.response import success_response, error_response
from app.agents.quality_control_agent import (
    get_quality_control_agent,
    QualityLevel,
    IssueType
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class DocumentValidationRequest(BaseModel):
    """文档验证请求"""
    id: str = Field(..., description="文档ID")
    content: str = Field(..., description="文档内容")
    format: str = Field(default="markdown", description="文档格式")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class OCRValidationRequest(BaseModel):
    """OCR验证请求"""
    task_id: str = Field(..., description="任务ID")
    text: str = Field(..., description="识别的文本")
    confidence: float = Field(..., ge=0, le=1, description="平均置信度")
    text_blocks: List[Dict[str, Any]] = Field(default_factory=list, description="文本块列表")


class EntityValidationRequest(BaseModel):
    """实体验证请求"""
    document_id: str = Field(..., description="文档ID")
    entities: List[Dict[str, Any]] = Field(..., description="实体列表")


class EmbeddingValidationRequest(BaseModel):
    """向量验证请求"""
    document_id: str = Field(..., description="文档ID")
    embedding: List[float] = Field(..., description="向量数据")


class GraphValidationRequest(BaseModel):
    """图谱验证请求"""
    document_id: str = Field(..., description="文档ID")
    nodes: List[Dict[str, Any]] = Field(..., description="节点列表")
    relationships: List[Dict[str, Any]] = Field(..., description="关系列表")


class QualityReportResponse(BaseModel):
    """质量报告响应"""
    task_id: str
    task_type: str
    overall_score: float
    quality_level: str
    passed: bool
    issues: List[Dict[str, Any]]
    issues_count: Dict[str, int]
    metrics: Dict[str, Any]
    auto_fixed: List[str]
    manual_review_required: bool
    created_at: str


class StatisticsResponse(BaseModel):
    """统计响应"""
    total_checks: int
    passed: int
    failed: int
    pass_rate: float
    auto_fixed: int
    auto_fix_rate: float


class BatchValidationRequest(BaseModel):
    """批量验证请求"""
    tasks: List[Dict[str, Any]] = Field(..., description="任务列表，每个任务包含type和data字段")


class BatchValidationResponse(BaseModel):
    """批量验证响应"""
    total: int
    passed: int
    failed: int
    reports: List[QualityReportResponse]


# ==================== API Endpoints ====================

@router.post("/validate/document", response_model=QualityReportResponse)
async def validate_document(request: DocumentValidationRequest):
    """
    验证文档转换质量

    检查项：
    - 内容是否为空
    - 编码是否正确
    - 元数据是否完整
    - 格式是否正确
    """
    try:
        agent = get_quality_control_agent()

        document_data = {
            "id": request.id,
            "content": request.content,
            "format": request.format,
            "metadata": request.metadata
        }

        report = agent.validate_document(document_data)

        return QualityReportResponse(**report.to_dict())

    except Exception as e:
        logger.error(f"Document validation error: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.post("/validate/ocr", response_model=QualityReportResponse)
async def validate_ocr(request: OCRValidationRequest):
    """
    验证OCR识别质量

    检查项：
    - 置信度是否达标
    - 是否包含乱码
    - 文本块数量
    - 内容是否为空
    """
    try:
        agent = get_quality_control_agent()

        ocr_data = {
            "task_id": request.task_id,
            "text": request.text,
            "confidence": request.confidence,
            "text_blocks": request.text_blocks
        }

        report = agent.validate_ocr_result(ocr_data)

        return QualityReportResponse(**report.to_dict())

    except Exception as e:
        logger.error(f"OCR validation error: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.post("/validate/entities", response_model=QualityReportResponse)
async def validate_entities(request: EntityValidationRequest):
    """
    验证实体识别质量

    检查项：
    - 实体数量
    - 实体类型是否有效
    - 是否有重复实体
    """
    try:
        agent = get_quality_control_agent()

        entity_data = {
            "document_id": request.document_id,
            "entities": request.entities
        }

        report = agent.validate_entities(entity_data)

        return QualityReportResponse(**report.to_dict())

    except Exception as e:
        logger.error(f"Entity validation error: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.post("/validate/embedding", response_model=QualityReportResponse)
async def validate_embedding(request: EmbeddingValidationRequest):
    """
    验证向量化质量

    检查项：
    - 向量维度
    - 向量多样性
    - 零值比例
    """
    try:
        agent = get_quality_control_agent()

        embedding_data = {
            "document_id": request.document_id,
            "embedding": request.embedding
        }

        report = agent.validate_embedding(embedding_data)

        return QualityReportResponse(**report.to_dict())

    except Exception as e:
        logger.error(f"Embedding validation error: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.post("/validate/graph", response_model=QualityReportResponse)
async def validate_graph(request: GraphValidationRequest):
    """
    验证知识图谱质量

    检查项：
    - 节点数量
    - 孤立节点比例
    - 三元组有效性
    """
    try:
        agent = get_quality_control_agent()

        graph_data = {
            "document_id": request.document_id,
            "nodes": request.nodes,
            "relationships": request.relationships
        }

        report = agent.validate_knowledge_graph(graph_data)

        return QualityReportResponse(**report.to_dict())

    except Exception as e:
        logger.error(f"Graph validation error: {e}")
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.post("/validate/batch", response_model=BatchValidationResponse)
async def validate_batch(request: BatchValidationRequest):
    """
    批量验证

    支持同时验证多个任务
    """
    try:
        agent = get_quality_control_agent()
        reports = []
        passed_count = 0

        for task in request.tasks:
            task_type = task.get("type")
            task_data = task.get("data", {})

            # 根据类型调用相应的验证方法
            if task_type == "document":
                report = agent.validate_document(task_data)
            elif task_type == "ocr":
                report = agent.validate_ocr_result(task_data)
            elif task_type == "entity":
                report = agent.validate_entities(task_data)
            elif task_type == "embedding":
                report = agent.validate_embedding(task_data)
            elif task_type == "graph":
                report = agent.validate_knowledge_graph(task_data)
            else:
                logger.warning(f"Unknown task type: {task_type}")
                continue

            reports.append(QualityReportResponse(**report.to_dict()))
            if report.passed:
                passed_count += 1

        return BatchValidationResponse(
            total=len(reports),
            passed=passed_count,
            failed=len(reports) - passed_count,
            reports=reports
        )

    except Exception as e:
        logger.error(f"Batch validation error: {e}")
        raise HTTPException(status_code=500, detail=f"批量验证失败: {str(e)}")


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    获取质量控制统计信息
    """
    try:
        agent = get_quality_control_agent()
        stats = agent.get_statistics()

        return StatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/statistics/reset")
async def reset_statistics():
    """
    重置统计信息
    """
    try:
        agent = get_quality_control_agent()
        agent.reset_statistics()

        return success_response(
            message="统计信息已重置",
            data={"timestamp": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        logger.error(f"Reset statistics error: {e}")
        raise HTTPException(status_code=500, detail=f"重置统计失败: {str(e)}")


@router.get("/issue-types")
async def get_issue_types():
    """
    获取所有问题类型
    """
    return success_response(
        data={
            "issue_types": [
                {
                    "type": issue_type.value,
                    "name": issue_type.name,
                    "category": _get_issue_category(issue_type)
                }
                for issue_type in IssueType
            ]
        }
    )


@router.get("/quality-levels")
async def get_quality_levels():
    """
    获取质量等级定义
    """
    return success_response(
        data={
            "quality_levels": [
                {"level": QualityLevel.EXCELLENT.value, "min_score": 95, "description": "优秀"},
                {"level": QualityLevel.GOOD.value, "min_score": 80, "description": "良好"},
                {"level": QualityLevel.ACCEPTABLE.value, "min_score": 60, "description": "可接受"},
                {"level": QualityLevel.POOR.value, "min_score": 40, "description": "差"},
                {"level": QualityLevel.FAILED.value, "min_score": 0, "description": "失败"}
            ]
        }
    )


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        agent = get_quality_control_agent()
        stats = agent.get_statistics()

        return success_response(
            data={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "checks_performed": stats["total_checks"],
                "auto_fix_enabled": agent.auto_fix_enabled
            }
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        return error_response(
            message="Quality control service unhealthy",
            error=str(e),
            status_code=503
        )


# ==================== Helper Functions ====================

def _get_issue_category(issue_type: IssueType) -> str:
    """获取问题类型的分类"""
    categories = {
        IssueType.EMPTY_CONTENT: "document",
        IssueType.ENCODING_ERROR: "document",
        IssueType.FORMAT_BROKEN: "document",
        IssueType.MISSING_METADATA: "document",
        IssueType.LOW_CONFIDENCE: "ocr",
        IssueType.GARBLED_TEXT: "ocr",
        IssueType.LAYOUT_BROKEN: "ocr",
        IssueType.NO_ENTITIES: "entity",
        IssueType.DUPLICATE_ENTITIES: "entity",
        IssueType.INVALID_ENTITY_TYPE: "entity",
        IssueType.EMPTY_EMBEDDING: "embedding",
        IssueType.DIMENSION_MISMATCH: "embedding",
        IssueType.LOW_DIVERSITY: "embedding",
        IssueType.ISOLATED_NODE: "graph",
        IssueType.MISSING_RELATIONSHIP: "graph",
        IssueType.INVALID_TRIPLE: "graph",
        IssueType.INDEX_FAILED: "search",
        IssueType.EMPTY_INDEX: "search",
        IssueType.PROCESSING_TIMEOUT: "general",
        IssueType.RESOURCE_ERROR: "general"
    }
    return categories.get(issue_type, "unknown")
