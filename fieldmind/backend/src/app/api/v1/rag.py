"""
RAG 检索 API 端点

将 RAG 检索服务集成到 FastAPI，提供完整的检索接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from app.schemas.response import success_response, error_response
import logging

from app.core.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.project import ProjectDocument
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["RAG检索"])


class FilterConditionRequest(BaseModel):
    """过滤条件请求"""
    field: str = Field(..., description="字段名")
    operator: str = Field(..., description="操作符: =, in, >, <, between")
    value: Any = Field(..., description="值")
    is_required: bool = Field(True, description="是否必需")


class RAGRetrievalRequest(BaseModel):
    """RAG 检索请求"""
    query: str = Field(..., description="查询文本", min_length=1)
    top_k: int = Field(5, description="返回结果数量", ge=1, le=20)
    project_id: Optional[int] = Field(None, description="项目ID（可选）")
    filters: Optional[List[FilterConditionRequest]] = Field(None, description="过滤条件")
    enable_rerank: bool = Field(True, description="是否启用重排")
    auto_extract_filters: bool = Field(True, description="是否自动提取过滤条件")


class RAGRetrievalResponse(BaseModel):
    """RAG 检索响应"""
    success: bool
    results: List[Dict[str, Any]]
    stats: Dict[str, Any]
    message: Optional[str] = None


@router.post("/retrieve", response_model=RAGRetrievalResponse)
async def rag_retrieve(request: RAGRetrievalRequest):
    """
    RAG 检索接口

    执行三阶段检索流水线：
    1. 前置过滤（Pre-filtering）
    2. 多路召回（Recall）
    3. 精排重排（Reranking）
    """
    try:
        logger.info(f"🔍 RAG 检索请求")
        logger.info(f"   查询: {request.query[:50]}...")
        logger.info(f"   top_k: {request.top_k}")

        # 获取 RAG 服务
        from app.services.rag_retrieval_service import get_rag_service
        from app.services.reranker_service import get_reranker_service
        from app.core.rag_engine import rag_engine

        # 初始化重排器
        reranker = None
        if request.enable_rerank:
            try:
                reranker = get_reranker_service()
            except Exception as e:
                logger.warning(f"重排器初始化失败: {e}")

        # 获取 RAG 服务
        rag_service = get_rag_service(
            vector_store=rag_engine,
            reranker=reranker
        )

        # 构建过滤条件
        filters = None
        if request.filters:
            from app.services.rag_retrieval_service import FilterCondition
            filters = [
                FilterCondition(
                    field=f.field,
                    operator=f.operator,
                    value=f.value,
                    is_required=f.is_required
                )
                for f in request.filters
            ]

        # 自动提取过滤条件
        if request.auto_extract_filters:
            auto_filters = rag_service.extract_filters_from_query(request.query)
            if auto_filters:
                logger.info(f"   自动提取过滤条件: {len(auto_filters)} 个")
                filters = (filters or []) + auto_filters

        # 执行检索
        results, stats = rag_service.retrieve(
            query=request.query,
            top_k=request.top_k,
            filters=filters,
            collection_name=f"project_{request.project_id}" if request.project_id else "documents",
            enable_rerank=request.enable_rerank
        )

        # 构建响应
        response_results = [
            {
                "chunk_id": r.chunk_id,
                "text": r.text,
                "score": r.score,
                "rerank_score": r.rerank_score,
                "metadata": r.metadata
            }
            for r in results
        ]

        return RAGRetrievalResponse(
            success=True,
            results=response_results,
            stats=stats,
            message=f"检索完成，返回 {len(results)} 个结果"
        )

    except Exception as e:
        logger.error(f"❌ RAG 检索失败: {e}")
        import traceback
        logger.error(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=f"RAG 检索失败: {str(e)}"
        )


@router.get("/stats")
async def rag_stats(db: Session = Depends(get_db)):
    """获取 RAG 系统统计信息"""
    try:
        from app.core.rag_engine import rag_engine

        total_documents = db.query(func.count(ProjectDocument.id)).scalar() or 0
        total_chunks = db.query(func.count(DocumentChunk.id)).scalar() or 0
        vector_count = 0
        try:
            if getattr(rag_engine, "collection", None) is not None:
                vector_count = int(rag_engine.collection.count())
        except Exception:
            vector_count = 0

        stats = {
            "total_documents": total_documents,
            "total_chunks": total_chunks,
            "vector_count": vector_count,
            "vector_dim": getattr(rag_engine, "embedding_dim", 768)
        }

        return success_response(
            data={
                "stats": stats
            }
        )

    except Exception as e:
        return error_response(
            code="GET_STATS_FAILED",
            message=str(e)
        )


@router.post("/test")
async def test_rag():
    """测试 RAG 系统"""
    try:
        from app.services.rag_retrieval_service import get_rag_service
        from app.core.rag_engine import rag_engine

        rag_service = get_rag_service(
            vector_store=rag_engine,
            reranker=None
        )

        # 测试查询
        results, stats = rag_service.retrieve(
            query="测试查询",
            top_k=3
        )

        return success_response(
            data={
                "results_count": len(results),
                "stats": stats
            },
            message="RAG 系统正常"
        )

    except Exception as e:
        return error_response(
            code="TEST_FAILED",
            message=str(e)
        )
