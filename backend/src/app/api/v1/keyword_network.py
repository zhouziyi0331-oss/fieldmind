"""
关键词网络 API
提供关键词网络构建、主关键词识别、社区检测、邻域查询
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.keyword_network_builder import KeywordNetworkBuilder
from app.services.keyword_relation_builder import KeywordRelationBuilder

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Request Models ============

class BuildNetworkRequest(BaseModel):
    """构建网络请求"""
    min_strength: float = Field(0.1, ge=0.0, le=1.0, description="最小关系强度阈值")
    include_communities: bool = Field(True, description="是否进行社区检测")


class BuildRelationsRequest(BaseModel):
    """构建关系请求"""
    min_cooccurrence: int = Field(2, ge=1, description="最小共现次数")
    recalculate: bool = Field(False, description="是否重新计算（删除旧关系）")


class GetMainKeywordsRequest(BaseModel):
    """获取主关键词请求"""
    top_n: int = Field(20, ge=1, le=100, description="返回数量")
    method: str = Field("comprehensive", description="排序方法: comprehensive|pagerank|frequency|degree")


# ============ API Endpoints ============

@router.post("/projects/{project_id}/keyword-relations/build")
async def build_keyword_relations(
    project_id: int,
    request: BuildRelationsRequest,
    db: Session = Depends(get_db)
):
    """
    构建关键词共现关系

    这是构建关键词网络的第一步，需要先执行此操作
    """
    try:
        builder = KeywordRelationBuilder(db)

        stats = builder.build_cooccurrence_relations(
            project_id=project_id,
            min_cooccurrence=request.min_cooccurrence,
            recalculate=request.recalculate
        )

        return {
            "success": True,
            "message": "关键词关系构建完成",
            "data": stats
        }

    except Exception as e:
        logger.error(f"构建关键词关系失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/keyword-network/build")
async def build_keyword_network(
    project_id: int,
    request: BuildNetworkRequest,
    db: Session = Depends(get_db)
):
    """
    构建完整的关键词网络

    包括：
    - 节点数据（关键词 + 中心性指标）
    - 边数据（关系）
    - 主关键词识别
    - 社区检测（可选）
    - 网络统计信息
    """
    try:
        builder = KeywordNetworkBuilder(db)

        network = builder.build_keyword_network(
            project_id=project_id,
            min_strength=request.min_strength,
            include_communities=request.include_communities
        )

        return {
            "success": True,
            "message": "关键词网络构建完成",
            "data": network
        }

    except Exception as e:
        logger.error(f"构建关键词网络失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/keyword-network")
async def get_keyword_network(
    project_id: int,
    min_strength: float = Query(0.1, ge=0.0, le=1.0, description="最小关系强度"),
    include_communities: bool = Query(True, description="是否包含社区信息"),
    db: Session = Depends(get_db)
):
    """
    获取已构建的关键词网络

    与 build 的区别：
    - build 会重新计算所有指标
    - get 直接读取并返回网络数据
    """
    try:
        builder = KeywordNetworkBuilder(db)

        network = builder.build_keyword_network(
            project_id=project_id,
            min_strength=min_strength,
            include_communities=include_communities
        )

        return {
            "success": True,
            "data": network
        }

    except Exception as e:
        logger.error(f"获取关键词网络失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/main-keywords")
async def get_main_keywords(
    project_id: int,
    top_n: int = Query(20, ge=1, le=100, description="返回数量"),
    method: str = Query("comprehensive", description="排序方法"),
    db: Session = Depends(get_db)
):
    """
    获取主关键词列表

    排序方法：
    - comprehensive: 综合评分（PageRank + 度中心性 + 频率）
    - pagerank: 仅 PageRank（推荐，识别重要节点）
    - frequency: 仅频率
    - degree: 仅度中心性
    """
    try:
        builder = KeywordNetworkBuilder(db)

        main_keywords = builder.get_main_keywords(
            project_id=project_id,
            top_n=top_n,
            method=method
        )

        return {
            "success": True,
            "data": {
                "main_keywords": main_keywords,
                "method": method,
                "total": len(main_keywords)
            }
        }

    except Exception as e:
        logger.error(f"获取主关键词失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords/{keyword_id}/neighborhood")
async def get_keyword_neighborhood(
    keyword_id: int,
    project_id: int = Query(..., description="项目ID"),
    depth: int = Query(1, ge=1, le=3, description="邻域深度"),
    min_strength: float = Query(0.1, ge=0.0, le=1.0, description="最小关系强度"),
    db: Session = Depends(get_db)
):
    """
    获取关键词的邻域网络

    用于局部网络探索：
    - depth=1: 直接邻居
    - depth=2: 二度邻居
    - depth=3: 三度邻居
    """
    try:
        builder = KeywordNetworkBuilder(db)

        neighborhood = builder.get_keyword_neighborhood(
            keyword_id=keyword_id,
            project_id=project_id,
            depth=depth,
            min_strength=min_strength
        )

        return {
            "success": True,
            "data": neighborhood
        }

    except Exception as e:
        logger.error(f"获取关键词邻域失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/keyword-relations/statistics")
async def get_keyword_relation_statistics(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取关键词关系统计信息

    包括：
    - 总关系数
    - 平均关系强度
    - 最大共现次数
    - 连接最多的关键词（Top 10）
    """
    try:
        builder = KeywordRelationBuilder(db)

        stats = builder.get_relation_statistics(project_id)

        return {
            "success": True,
            "data": stats
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/keyword-network/full-analysis")
async def full_keyword_network_analysis(
    project_id: int,
    min_cooccurrence: int = Query(2, ge=1, description="最小共现次数"),
    min_strength: float = Query(0.1, ge=0.0, le=1.0, description="最小关系强度"),
    recalculate_relations: bool = Query(False, description="是否重新计算关系"),
    include_communities: bool = Query(True, description="是否进行社区检测"),
    db: Session = Depends(get_db)
):
    """
    完整的关键词网络分析

    一键执行：
    1. 构建关键词共现关系
    2. 构建关键词网络
    3. 识别主关键词
    4. 社区检测
    5. 计算统计信息

    适合首次分析或需要全面更新的场景
    """
    try:
        relation_builder = KeywordRelationBuilder(db)
        network_builder = KeywordNetworkBuilder(db)

        result = {}

        # 步骤 1: 构建关系
        logger.info("步骤 1/3: 构建关键词关系...")
        relation_stats = relation_builder.build_cooccurrence_relations(
            project_id=project_id,
            min_cooccurrence=min_cooccurrence,
            recalculate=recalculate_relations
        )
        result['relation_stats'] = relation_stats

        # 步骤 2: 构建网络
        logger.info("步骤 2/3: 构建关键词网络...")
        network = network_builder.build_keyword_network(
            project_id=project_id,
            min_strength=min_strength,
            include_communities=include_communities
        )
        result['network'] = network

        # 步骤 3: 获取主关键词
        logger.info("步骤 3/3: 识别主关键词...")
        main_keywords = network_builder.get_main_keywords(
            project_id=project_id,
            top_n=20,
            method="comprehensive"
        )
        result['main_keywords'] = main_keywords

        return {
            "success": True,
            "message": "关键词网络完整分析完成",
            "data": result
        }

    except Exception as e:
        logger.error(f"完整分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
