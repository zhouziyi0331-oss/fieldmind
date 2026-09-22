"""
智能推荐搜索 API
提供报告推荐、关键词推荐、文档推荐、搜索建议
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.smart_recommendation_service import SmartRecommendationService
from app.services.unified_search import UnifiedSearchService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Request Models ============

class RecommendReportsRequest(BaseModel):
    """推荐报告请求"""
    strategy: str = Field("hybrid", description="推荐策略: relation_based|entity_based|keyword_based|hybrid")
    top_n: int = Field(5, ge=1, le=20, description="推荐数量")
    exclude_ids: List[str] = Field(default_factory=list, description="排除的报告ID")


class RecommendKeywordsRequest(BaseModel):
    """推荐关键词请求"""
    strategy: str = Field("network", description="推荐策略: network|context")
    top_n: int = Field(10, ge=1, le=50, description="推荐数量")


class RecommendDocumentsRequest(BaseModel):
    """推荐文档请求"""
    strategy: str = Field("keyword", description="推荐策略: keyword|temporal")
    top_n: int = Field(5, ge=1, le=20, description="推荐数量")


class UnifiedSearchRequest(BaseModel):
    """统一搜索请求"""
    query: str = Field(..., min_length=1, description="搜索查询")
    search_type: str = Field("hybrid", description="搜索类型: keyword|semantic|hybrid|entity")
    top_k: int = Field(10, ge=1, le=50, description="返回结果数")


# ============ API Endpoints ============

@router.get("/reports/{report_id}/recommendations")
async def get_report_recommendations(
    report_id: str,
    project_id: int = Query(..., description="项目ID"),
    strategy: str = Query("hybrid", description="推荐策略"),
    top_n: int = Query(5, ge=1, le=20, description="推荐数量"),
    exclude_ids: Optional[str] = Query(None, description="排除的报告ID，逗号分隔"),
    db: Session = Depends(get_db)
):
    """
    获取报告推荐

    推荐策略：
    - relation_based: 基于报告关系网络
    - entity_based: 基于共享实体
    - keyword_based: 基于关键词相似度
    - hybrid: 混合策略（推荐）

    返回相关报告列表，按推荐分数排序
    """
    try:
        service = SmartRecommendationService(db)

        # 解析排除ID
        exclude_set = set(exclude_ids.split(',')) if exclude_ids else set()

        recommendations = service.recommend_reports(
            report_id=report_id,
            project_id=project_id,
            strategy=strategy,
            top_n=top_n,
            exclude_ids=exclude_set
        )

        return {
            "success": True,
            "data": {
                "report_id": report_id,
                "recommendations": recommendations,
                "strategy": strategy,
                "count": len(recommendations)
            }
        }

    except Exception as e:
        logger.error(f"获取报告推荐失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords/{keyword_id}/recommendations")
async def get_keyword_recommendations(
    keyword_id: int,
    project_id: int = Query(..., description="项目ID"),
    strategy: str = Query("network", description="推荐策略"),
    top_n: int = Query(10, ge=1, le=50, description="推荐数量"),
    db: Session = Depends(get_db)
):
    """
    获取关键词推荐

    推荐策略：
    - network: 基于关键词网络（共现关系）
    - context: 基于上下文相似度（同分类高频词）

    返回相关关键词列表
    """
    try:
        service = SmartRecommendationService(db)

        recommendations = service.recommend_keywords(
            keyword_id=keyword_id,
            project_id=project_id,
            strategy=strategy,
            top_n=top_n
        )

        return {
            "success": True,
            "data": {
                "keyword_id": keyword_id,
                "recommendations": recommendations,
                "strategy": strategy,
                "count": len(recommendations)
            }
        }

    except Exception as e:
        logger.error(f"获取关键词推荐失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/recommendations")
async def get_document_recommendations(
    document_id: int,
    project_id: int = Query(..., description="项目ID"),
    strategy: str = Query("keyword", description="推荐策略"),
    top_n: int = Query(5, ge=1, le=20, description="推荐数量"),
    db: Session = Depends(get_db)
):
    """
    获取文档推荐

    推荐策略：
    - keyword: 基于关键词相似度
    - temporal: 基于时间相近性

    返回相关文档列表
    """
    try:
        service = SmartRecommendationService(db)

        recommendations = service.recommend_documents(
            document_id=document_id,
            project_id=project_id,
            strategy=strategy,
            top_n=top_n
        )

        return {
            "success": True,
            "data": {
                "document_id": document_id,
                "recommendations": recommendations,
                "strategy": strategy,
                "count": len(recommendations)
            }
        }

    except Exception as e:
        logger.error(f"获取文档推荐失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/search-suggestions")
async def get_search_suggestions(
    project_id: int,
    query: str = Query(..., min_length=1, description="搜索查询"),
    suggestion_type: str = Query("all", description="建议类型: keywords|entities|documents|all"),
    limit: int = Query(5, ge=1, le=20, description="每种类型的建议数量"),
    db: Session = Depends(get_db)
):
    """
    搜索建议（自动补全）

    类型：
    - keywords: 关键词建议
    - entities: 实体建议
    - documents: 文档建议
    - all: 全部类型

    用于实现搜索框的自动补全功能
    """
    try:
        service = SmartRecommendationService(db)

        suggestions = service.search_suggestions(
            query=query,
            project_id=project_id,
            suggestion_type=suggestion_type,
            limit=limit
        )

        return {
            "success": True,
            "data": {
                "query": query,
                "suggestions": suggestions
            }
        }

    except Exception as e:
        logger.error(f"获取搜索建议失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/unified-search")
async def unified_search(
    project_id: int,
    request: UnifiedSearchRequest,
    db: Session = Depends(get_db)
):
    """
    统一搜索接口

    整合多种搜索方式：
    - keyword: 关键词搜索（全文匹配）
    - semantic: 语义检索（向量相似度）
    - hybrid: 混合检索（推荐，综合关键词和语义）
    - entity: 实体查询（知识图谱）

    返回统一格式的搜索结果
    """
    try:
        search_service = UnifiedSearchService()

        results = search_service.search(
            query=request.query,
            project_id=project_id,
            search_type=request.search_type,
            top_k=request.top_k
        )

        return {
            "success": True,
            "data": results
        }

    except Exception as e:
        logger.error(f"统一搜索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/recommendation-stats")
async def get_recommendation_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取推荐系统统计信息

    包括：
    - 报告关系网络统计
    - 关键词网络统计
    - 可推荐内容数量
    """
    try:
        from app.models.report import Report
        from app.models.keyword import Keyword, KeywordRelation
        from app.models.report_relation import ReportRelation
        from app.models.document import Document

        # 统计报告
        total_reports = db.query(Report).filter(Report.project_id == project_id).count()
        report_relations = db.query(ReportRelation).join(
            Report, ReportRelation.source_report_id == Report.id
        ).filter(Report.project_id == project_id).count()

        # 统计关键词
        total_keywords = db.query(Keyword).filter(Keyword.project_id == project_id).count()
        keyword_relations = db.query(KeywordRelation).filter(
            KeywordRelation.project_id == project_id
        ).count()

        # 统计文档
        total_documents = db.query(Document).filter(Document.project_id == project_id).count()

        return {
            "success": True,
            "data": {
                "reports": {
                    "total": total_reports,
                    "relations": report_relations,
                    "avg_relations_per_report": round(report_relations / total_reports, 2) if total_reports > 0 else 0
                },
                "keywords": {
                    "total": total_keywords,
                    "relations": keyword_relations,
                    "avg_relations_per_keyword": round(keyword_relations / total_keywords, 2) if total_keywords > 0 else 0
                },
                "documents": {
                    "total": total_documents
                },
                "recommendation_coverage": {
                    "reports_with_relations": report_relations > 0,
                    "keywords_with_relations": keyword_relations > 0,
                    "overall_ready": total_reports > 0 and total_keywords > 0 and total_documents > 0
                }
            }
        }

    except Exception as e:
        logger.error(f"获取推荐统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/batch-recommendations")
async def batch_recommendations(
    project_id: int,
    report_ids: List[str] = Query(..., description="报告ID列表"),
    strategy: str = Query("hybrid", description="推荐策略"),
    top_n: int = Query(3, ge=1, le=10, description="每个报告推荐数量"),
    db: Session = Depends(get_db)
):
    """
    批量获取报告推荐

    用于一次性获取多个报告的推荐，提高效率
    适合列表页、看板等场景
    """
    try:
        service = SmartRecommendationService(db)

        batch_results = {}
        for report_id in report_ids[:20]:  # 限制最多 20 个
            try:
                recommendations = service.recommend_reports(
                    report_id=report_id,
                    project_id=project_id,
                    strategy=strategy,
                    top_n=top_n,
                    exclude_ids=set(report_ids)  # 排除批量列表中的其他报告
                )
                batch_results[report_id] = recommendations
            except Exception as e:
                logger.warning(f"报告 {report_id} 推荐失败: {e}")
                batch_results[report_id] = []

        return {
            "success": True,
            "data": {
                "batch_results": batch_results,
                "strategy": strategy,
                "processed_count": len(batch_results)
            }
        }

    except Exception as e:
        logger.error(f"批量推荐失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
