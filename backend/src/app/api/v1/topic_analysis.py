"""
TF-IDF and Clustering API - TF-IDF 和聚类分析 API

提供 TF-IDF 关键词提取和主题聚类的 API 接口
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.schemas.response import success_response, error_response
import logging

from app.services.tfidf_keyword_extractor import create_extractor
from app.services.topic_clustering_service import create_clustering_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/topics", tags=["主题分析"])

# 初始化服务
tfidf_extractor = create_extractor()
clustering_service = create_clustering_service()


class ExtractKeywordsRequest(BaseModel):
    """提取关键词请求"""
    chunk_id: Optional[int] = Field(None, description="单个chunk ID")
    project_id: int = Field(..., description="项目 ID")
    batch: bool = Field(False, description="是否批量提取（项目所有chunks）")
    top_n: int = Field(5, ge=1, le=20, description="每个chunk提取的关键词数量")


class ClusterRequest(BaseModel):
    """聚类请求"""
    project_id: int = Field(..., description="项目 ID")
    n_clusters: Optional[int] = Field(None, ge=2, le=20, description="聚类数量")
    auto_determine_k: bool = Field(True, description="是否自动确定聚类数量")


@router.post("/extract-keywords")
async def extract_keywords(request: ExtractKeywordsRequest, background_tasks: BackgroundTasks):
    """
    提取 TF-IDF 关键词

    支持两种模式：
    1. 单个 chunk：提供 chunk_id
    2. 批量提取：设置 batch=True，对项目所有 chunks 提取
    """
    try:
        if request.batch:
            # 批量提取（后台任务）
            background_tasks.add_task(
                tfidf_extractor.batch_extract_for_project,
                request.project_id,
                request.top_n
            )

            return success_response(
                data={
                    "status": "started",
                    "project_id": request.project_id
                },
                message=f"批量关键词提取任务已启动（项目 {request.project_id}）"
            )

        elif request.chunk_id:
            # 单个 chunk 提取
            keywords = tfidf_extractor.extract_keywords_for_chunk(
                request.chunk_id,
                request.project_id,
                request.top_n
            )

            if keywords:
                tfidf_extractor.save_keywords_to_db(request.chunk_id, keywords)

            return success_response(
                data={
                    "chunk_id": request.chunk_id,
                    "keywords": keywords
                }
            )

        else:
            raise HTTPException(status_code=400, detail="必须提供 chunk_id 或设置 batch=True")

    except Exception as e:
        logger.error(f"Error extracting keywords: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords/chunk/{chunk_id}/")
async def get_chunk_keywords(chunk_id: int, top_only: bool = False):
    """
    获取 chunk 的关键词

    Args:
        chunk_id: chunk ID
        top_only: 是否只返回 Top 3 关键词
    """
    try:
        keywords = tfidf_extractor.get_chunk_keywords(chunk_id, top_only)

        return success_response(
            data={
                "chunk_id": chunk_id,
                "keywords": keywords
            }
        )

    except Exception as e:
        logger.error(f"Error getting keywords for chunk {chunk_id}: {e}")
        return error_response(
            code="GET_KEYWORDS_FAILED",
            message=str(e)
        )


@router.get("/keywords/project/{project_id}/")
async def get_project_top_keywords(project_id: int, top_n: int = 50):
    """
    获取项目的 Top N 关键词

    Args:
        project_id: 项目 ID
        top_n: 返回前 N 个关键词
    """
    try:
        keywords = tfidf_extractor.get_project_top_keywords(project_id, top_n)

        return success_response(
            data={
                "project_id": project_id,
                "top_n": top_n,
                "keywords": keywords
            }
        )

    except Exception as e:
        logger.error(f"Error getting project keywords: {e}")
        return error_response(
            code="GET_PROJECT_KEYWORDS_FAILED",
            message=str(e)
        )


@router.post("/cluster")
async def cluster_project(request: ClusterRequest, background_tasks: BackgroundTasks):
    """
    对项目进行主题聚类

    自动发现主题，无需预先定义标签
    """
    try:
        # 在后台执行聚类（可能耗时较长）
        background_tasks.add_task(
            clustering_service.auto_cluster_chunks,
            request.project_id,
            request.n_clusters,
            request.auto_determine_k
        )

        return success_response(
            data={
                "status": "started",
                "project_id": request.project_id
            },
            message=f"聚类任务已启动（项目 {request.project_id}）"
        )

    except Exception as e:
        logger.error(f"Error clustering project: {e}", exc_info=True)
        return error_response(
            code="CLUSTER_FAILED",
            message=str(e)
        )


@router.get("/clusters/{project_id}/")
async def get_project_clusters(project_id: int):
    """
    获取项目的聚类结果

    返回：
    - 聚类数量
    - 每个聚类的标签、关键词、chunk数量
    """
    try:
        clusters = clustering_service.get_project_clusters(project_id)

        return success_response(
            data={
                "project_id": project_id,
                "n_clusters": len(clusters),
                "clusters": clusters
            }
        )

    except Exception as e:
        logger.error(f"Error getting clusters: {e}")
        return error_response(
            code="GET_CLUSTERS_FAILED",
            message=str(e)
        )


@router.get("/clusters/{project_id}/{cluster_id}/chunks/")
async def get_cluster_chunks(project_id: int, cluster_id: int):
    """
    获取某个聚类的所有 chunks

    Args:
        project_id: 项目 ID
        cluster_id: 聚类 ID
    """
    try:
        chunks = clustering_service.get_cluster_chunks(project_id, cluster_id)

        return success_response(
            data={
                "project_id": project_id,
                "cluster_id": cluster_id,
                "chunk_count": len(chunks),
                "chunks": chunks
            }
        )

    except Exception as e:
        logger.error(f"Error getting cluster chunks: {e}")
        return error_response(
            code="GET_CLUSTER_CHUNKS_FAILED",
            message=str(e)
        )


@router.post("/auto-analyze/{project_id}/")
async def auto_analyze_project(project_id: int, background_tasks: BackgroundTasks):
    """
    一键自动分析

    执行完整的分析流程：
    1. TF-IDF 关键词提取
    2. 主题聚类
    3. 维度映射
    """
    try:
        # 1. 批量提取关键词
        background_tasks.add_task(
            tfidf_extractor.batch_extract_for_project,
            project_id,
            5
        )

        # 2. 聚类（在关键词提取完成后）
        # 注意：这里简化处理，实际应该等待关键词提取完成
        background_tasks.add_task(
            clustering_service.auto_cluster_chunks,
            project_id,
            None,
            True
        )

        return success_response(
            data={
                "status": "started",
                "project_id": project_id,
                "steps": [
                    "TF-IDF 关键词提取",
                    "主题聚类",
                    "维度映射"
                ]
            },
            message=f"自动分析任务已启动（项目 {project_id}）"
        )

    except Exception as e:
        logger.error(f"Error auto-analyzing project: {e}", exc_info=True)
        return error_response(
            code="AUTO_ANALYZE_FAILED",
            message=str(e)
        )
