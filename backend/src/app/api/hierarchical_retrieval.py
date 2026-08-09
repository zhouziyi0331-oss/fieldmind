"""
分层检索API - 链路17：报告优先级

新增接口：
1. POST /hierarchical-search - 分层检索（优先高层级报告）
2. POST /mixed-search - 混合检索（加权排序）
3. GET /search-stats - 各层级统计
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.core.database import get_db
from app.services.hierarchical_retriever import get_hierarchical_retriever
from app.schemas.document_metadata import SourceLevel

router = APIRouter(tags=["hierarchical-retrieval"])
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class HierarchicalSearchRequest(BaseModel):
    """分层检索请求"""
    query: str
    project_id: Optional[int] = None
    n_results: int = 5
    prefer_reports: bool = True  # 是否优先报告
    min_level: int = SourceLevel.RAW_MATERIAL  # 最低接受层级
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SearchResult(BaseModel):
    """检索结果"""
    text: str
    citation: str
    source_level: int
    level_name: str
    relevance: float
    weighted_score: Optional[float] = None
    metadata: dict


class HierarchicalSearchResponse(BaseModel):
    """分层检索响应"""
    query: str
    results: List[SearchResult]
    total_count: int
    strategy: str  # "fallback" | "mixed"
    level_distribution: dict  # 各层级结果数量


# ==================== API Endpoints ====================

@router.post("/search", response_model=HierarchicalSearchResponse)
async def hierarchical_search(
    request: HierarchicalSearchRequest,
    db: Session = Depends(get_db)
):
    """
    分层检索（链路17核心接口）

    **检索策略：**
    - prefer_reports=True: 优先高层级报告，不足时降级
      - 先查三度报告，不够再查二度报告，依次降级
      - 适合日常对话：优先展示已消化的知识

    - prefer_reports=False: 混合检索所有层级
      - 按加权分数（层级权重 * 相似度）排序
      - 适合全面搜索：需要查看所有层级的相关内容

    **示例：**
    ```json
    {
      "query": "费孝通的差序格局理论",
      "project_id": 1,
      "n_results": 5,
      "prefer_reports": true,
      "min_level": 0
    }
    ```

    **返回格式：**
    ```json
    {
      "results": [
        {
          "text": "费孝通指出，差序格局是中国社会的基本特征...",
          "citation": "[来源：深度分析报告.pdf P12]",
          "source_level": 3,
          "level_name": "三度报告",
          "relevance": 0.95
        }
      ],
      "level_distribution": {
        "三度报告": 2,
        "二度报告": 1,
        "原始材料": 2
      }
    }
    ```
    """
    try:
        retriever = get_hierarchical_retriever()

        # 构建日期范围
        date_range = None
        if request.date_from or request.date_to:
            date_range = (request.date_from, request.date_to)

        # 执行检索
        results = retriever.retrieve_with_hierarchy(
            query_text=request.query,
            n_results=request.n_results,
            project_id=request.project_id,
            prefer_reports=request.prefer_reports,
            min_level=request.min_level,
            date_range=date_range
        )

        # 统计各层级分布
        level_distribution = {}
        for result in results:
            level_name = result.get("level_name", "未知")
            level_distribution[level_name] = level_distribution.get(level_name, 0) + 1

        return {
            "query": request.query,
            "results": results,
            "total_count": len(results),
            "strategy": "fallback" if request.prefer_reports else "mixed",
            "level_distribution": level_distribution
        }

    except Exception as e:
        logger.error(f"分层检索失败: {e}", exc_info=True)
        return {
            "query": request.query,
            "results": [],
            "total_count": 0,
            "strategy": "error",
            "level_distribution": {}
        }


@router.get("/stats")
async def get_hierarchy_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的层级统计

    返回各层级的文档数量和chunk数量

    示例返回：
    ```json
    {
      "project_id": 1,
      "total_chunks": 1250,
      "level_stats": {
        "三度报告": {"chunks": 120, "percentage": 9.6},
        "二度报告": {"chunks": 280, "percentage": 22.4},
        "一度报告": {"chunks": 350, "percentage": 28.0},
        "原始材料": {"chunks": 500, "percentage": 40.0}
      },
      "recommendation": "建议增加二度和三度报告的生成，提升知识消化层次"
    }
    ```
    """
    try:
        retriever = get_hierarchical_retriever()
        vectorizer = retriever.vectorizer

        # 获取项目所有chunks
        all_chunks = vectorizer.collection.get(
            where={"project_id": str(project_id)},
            include=["metadatas"]
        )

        if not all_chunks or not all_chunks.get("metadatas"):
            return {
                "project_id": project_id,
                "total_chunks": 0,
                "level_stats": {},
                "recommendation": "项目无数据"
            }

        # 统计各层级
        level_counts = {
            "三度报告": 0,
            "二度报告": 0,
            "一度报告": 0,
            "原始材料": 0
        }

        for metadata in all_chunks["metadatas"]:
            source_level = metadata.get("source_level", 0)
            level_name = retriever._get_level_name(source_level)
            level_counts[level_name] = level_counts.get(level_name, 0) + 1

        total_chunks = sum(level_counts.values())

        # 计算百分比
        level_stats = {}
        for level_name, count in level_counts.items():
            percentage = (count / total_chunks * 100) if total_chunks > 0 else 0
            level_stats[level_name] = {
                "chunks": count,
                "percentage": round(percentage, 1)
            }

        # 生成建议
        report_percentage = (
            level_stats["三度报告"]["percentage"] +
            level_stats["二度报告"]["percentage"]
        )

        if report_percentage < 20:
            recommendation = "建议增加二度和三度报告的生成，当前报告占比过低"
        elif report_percentage < 40:
            recommendation = "报告占比适中，可继续提升三度报告的深度"
        else:
            recommendation = "知识消化层次良好，继续保持"

        return {
            "project_id": project_id,
            "total_chunks": total_chunks,
            "level_stats": level_stats,
            "recommendation": recommendation
        }

    except Exception as e:
        logger.error(f"获取层级统计失败: {e}", exc_info=True)
        return {
            "project_id": project_id,
            "total_chunks": 0,
            "level_stats": {},
            "recommendation": "统计失败"
        }


@router.post("/compare-strategies")
async def compare_strategies(
    query: str,
    project_id: Optional[int] = None,
    n_results: int = 5
):
    """
    对比两种检索策略的结果

    返回：
    - fallback策略（优先报告）的结果
    - mixed策略（混合加权）的结果
    - 对比分析

    用于调试和优化检索策略
    """
    try:
        retriever = get_hierarchical_retriever()

        # 策略1：降级检索
        fallback_results = retriever.retrieve_with_hierarchy(
            query_text=query,
            n_results=n_results,
            project_id=project_id,
            prefer_reports=True
        )

        # 策略2：混合检索
        mixed_results = retriever.retrieve_with_hierarchy(
            query_text=query,
            n_results=n_results,
            project_id=project_id,
            prefer_reports=False
        )

        # 统计差异
        fallback_levels = [r.get("level_name") for r in fallback_results]
        mixed_levels = [r.get("level_name") for r in mixed_results]

        return {
            "query": query,
            "fallback_strategy": {
                "description": "优先高层级报告，不足时降级",
                "results": fallback_results,
                "level_distribution": {level: fallback_levels.count(level) for level in set(fallback_levels)}
            },
            "mixed_strategy": {
                "description": "所有层级混合，按加权分数排序",
                "results": mixed_results,
                "level_distribution": {level: mixed_levels.count(level) for level in set(mixed_levels)}
            },
            "comparison": {
                "fallback_avg_level": sum(r.get("source_level", 0) for r in fallback_results) / len(fallback_results) if fallback_results else 0,
                "mixed_avg_level": sum(r.get("source_level", 0) for r in mixed_results) / len(mixed_results) if mixed_results else 0,
                "recommendation": "Fallback策略适合日常对话，Mixed策略适合全面搜索"
            }
        }

    except Exception as e:
        logger.error(f"对比策略失败: {e}", exc_info=True)
        return {
            "query": query,
            "fallback_strategy": {"results": [], "level_distribution": {}},
            "mixed_strategy": {"results": [], "level_distribution": {}},
            "comparison": {"recommendation": "对比失败"}
        }
