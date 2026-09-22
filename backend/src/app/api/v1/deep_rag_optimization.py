"""
Deep RAG查询优化API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.services.deep_rag_optimization_service import get_deep_rag_optimization_service

router = APIRouter()


# ==================== Request/Response Models ====================

class OptimizedQueryRequest(BaseModel):
    """优化查询请求"""
    query: str = Field(..., description="用户查询问题")
    session_id: str = Field(..., description="会话ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    use_cache: bool = Field(True, description="是否使用缓存")
    use_optimization: bool = Field(True, description="是否使用查询优化")
    max_sources: int = Field(5, ge=1, le=10, description="最多使用的检索源数量")
    top_k: int = Field(5, ge=1, le=20, description="每源返回结果数")
    llm_provider: str = Field("anthropic", description="LLM提供商")


class QueryResponse(BaseModel):
    """查询响应"""
    answer: str
    citations: List[Dict[str, Any]]
    confidence: float
    quality_score: float
    sources_used: List[str]
    optimized_query: str
    expanded_queries: List[str]
    keywords: List[str]
    selected_sources: List[str]
    cached: bool
    metadata: Dict[str, Any]


class CacheInvalidateRequest(BaseModel):
    """缓存失效请求"""
    project_id: Optional[int] = Field(None, description="项目ID，None则清空所有")


class FeedbackRequest(BaseModel):
    """查询反馈请求"""
    query_id: int = Field(..., description="查询记录ID")
    rating: int = Field(..., ge=1, le=5, description="评分1-5星")
    feedback_text: Optional[str] = Field(None, description="反馈文本")
    helpful: Optional[bool] = Field(None, description="是否有帮助")


# ==================== API Endpoints ====================

@router.post("/query", response_model=QueryResponse)
async def optimized_deep_rag_query(
    request: OptimizedQueryRequest,
    db: Session = Depends(get_db)
):
    """
    执行优化的深度RAG查询

    特性：
    - 查询重写与扩展
    - 智能检索源选择
    - 结果缓存
    - 质量评估
    - 实时WebSocket进度推送
    """
    try:
        service = get_deep_rag_optimization_service(db)

        result = await service.optimized_query(
            query=request.query,
            session_id=request.session_id,
            project_id=request.project_id,
            use_cache=request.use_cache,
            use_optimization=request.use_optimization,
            max_sources=request.max_sources,
            top_k=request.top_k,
            llm_provider=request.llm_provider
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/queries/{session_id}")
async def get_session_queries(
    session_id: str,
    project_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取会话的查询历史"""
    try:
        from app.models.rag_query import RAGQuery

        query = db.query(RAGQuery).filter(RAGQuery.session_id == session_id)

        if project_id is not None:
            query = query.filter(RAGQuery.project_id == project_id)

        queries = query.order_by(RAGQuery.created_at.desc()).limit(limit).all()

        return {
            "session_id": session_id,
            "total": len(queries),
            "queries": [
                {
                    "id": q.id,
                    "query_text": q.query_text,
                    "optimized_query": q.optimized_query,
                    "answer": q.answer[:200] + "..." if len(q.answer) > 200 else q.answer,
                    "confidence": q.confidence,
                    "quality_score": q.quality_score,
                    "latency": q.latency,
                    "cached": q.cached,
                    "sources_used": q.sources_used,
                    "citations_count": q.citations_count,
                    "created_at": q.created_at.isoformat()
                }
                for q in queries
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询历史失败: {str(e)}")


@router.get("/queries/detail/{query_id}")
async def get_query_detail(
    query_id: int,
    db: Session = Depends(get_db)
):
    """获取查询详情"""
    try:
        from app.models.rag_query import RAGQuery

        query = db.query(RAGQuery).filter(RAGQuery.id == query_id).first()

        if not query:
            raise HTTPException(status_code=404, detail="查询记录不存在")

        return {
            "id": query.id,
            "project_id": query.project_id,
            "session_id": query.session_id,
            "query_text": query.query_text,
            "optimized_query": query.optimized_query,
            "answer": query.answer,
            "sources_used": query.sources_used,
            "citations_count": query.citations_count,
            "confidence": query.confidence,
            "quality_score": query.quality_score,
            "latency": query.latency,
            "cached": query.cached,
            "created_at": query.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取查询详情失败: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """提交查询反馈"""
    try:
        from app.models.rag_query import RAGQuery, RAGFeedback

        # 检查查询是否存在
        query = db.query(RAGQuery).filter(RAGQuery.id == request.query_id).first()
        if not query:
            raise HTTPException(status_code=404, detail="查询记录不存在")

        # 创建反馈
        feedback = RAGFeedback(
            query_id=request.query_id,
            rating=request.rating,
            feedback_text=request.feedback_text,
            helpful=request.helpful
        )

        db.add(feedback)
        db.commit()
        db.refresh(feedback)

        return {
            "id": feedback.id,
            "query_id": feedback.query_id,
            "rating": feedback.rating,
            "created_at": feedback.created_at.isoformat(),
            "message": "反馈已提交"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


@router.get("/projects/{project_id}/analytics")
async def get_project_analytics(
    project_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """获取项目RAG查询分析"""
    try:
        from app.models.rag_query import RAGQuery
        from sqlalchemy import func
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 基础统计
        total_queries = db.query(func.count(RAGQuery.id))\
            .filter(RAGQuery.project_id == project_id)\
            .filter(RAGQuery.created_at >= cutoff_date)\
            .scalar()

        cached_queries = db.query(func.count(RAGQuery.id))\
            .filter(RAGQuery.project_id == project_id)\
            .filter(RAGQuery.created_at >= cutoff_date)\
            .filter(RAGQuery.cached == True)\
            .scalar()

        avg_confidence = db.query(func.avg(RAGQuery.confidence))\
            .filter(RAGQuery.project_id == project_id)\
            .filter(RAGQuery.created_at >= cutoff_date)\
            .scalar() or 0.0

        avg_quality = db.query(func.avg(RAGQuery.quality_score))\
            .filter(RAGQuery.project_id == project_id)\
            .filter(RAGQuery.created_at >= cutoff_date)\
            .scalar() or 0.0

        avg_latency = db.query(func.avg(RAGQuery.latency))\
            .filter(RAGQuery.project_id == project_id)\
            .filter(RAGQuery.created_at >= cutoff_date)\
            .scalar() or 0.0

        # 最近查询
        recent_queries = db.query(RAGQuery)\
            .filter(RAGQuery.project_id == project_id)\
            .filter(RAGQuery.created_at >= cutoff_date)\
            .order_by(RAGQuery.created_at.desc())\
            .limit(10)\
            .all()

        return {
            "project_id": project_id,
            "period_days": days,
            "statistics": {
                "total_queries": total_queries,
                "cached_queries": cached_queries,
                "cache_hit_rate": cached_queries / total_queries if total_queries > 0 else 0.0,
                "avg_confidence": float(avg_confidence),
                "avg_quality_score": float(avg_quality),
                "avg_latency": float(avg_latency)
            },
            "recent_queries": [
                {
                    "id": q.id,
                    "query_text": q.query_text,
                    "confidence": q.confidence,
                    "quality_score": q.quality_score,
                    "latency": q.latency,
                    "cached": q.cached,
                    "created_at": q.created_at.isoformat()
                }
                for q in recent_queries
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析数据失败: {str(e)}")


@router.post("/cache/invalidate")
async def invalidate_cache(
    request: CacheInvalidateRequest,
    db: Session = Depends(get_db)
):
    """失效查询缓存"""
    try:
        service = get_deep_rag_optimization_service(db)
        service.invalidate_cache(project_id=request.project_id)

        return {
            "message": f"缓存已失效: {'所有项目' if request.project_id is None else f'项目{request.project_id}'}",
            "project_id": request.project_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"失效缓存失败: {str(e)}")


@router.get("/stats")
async def get_optimization_stats(
    db: Session = Depends(get_db)
):
    """获取优化统计信息"""
    try:
        service = get_deep_rag_optimization_service(db)
        stats = service.get_optimization_stats()

        return {
            "service": "deep_rag_optimization",
            "status": "healthy",
            "statistics": stats
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db)
):
    """健康检查"""
    try:
        service = get_deep_rag_optimization_service(db)
        health = service.health_check()

        return {
            "status": "healthy",
            "service": "deep_rag_optimization",
            "details": health
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "deep_rag_optimization",
            "error": str(e)
        }
