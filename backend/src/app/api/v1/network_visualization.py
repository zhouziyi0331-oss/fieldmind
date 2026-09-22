"""
网络可视化 API
提供报告关系网络、关键词网络的可视化数据
支持多种前端可视化库格式
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.network_visualization_service import NetworkVisualizationService
from app.services.keyword_network_builder import KeywordNetworkBuilder

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ Request Models ============

class NetworkVisualizationRequest(BaseModel):
    """网络可视化请求"""
    format_type: str = Field("d3", description="格式类型: d3|echarts|cytoscape|vis")
    min_strength: float = Field(0.1, ge=0.0, le=1.0, description="最小关系强度")
    include_isolated: bool = Field(False, description="是否包含孤立节点")


class KeywordNetworkVisualizationRequest(BaseModel):
    """关键词网络可视化请求"""
    format_type: str = Field("d3", description="格式类型: d3|echarts|cytoscape|vis")
    min_strength: float = Field(0.1, ge=0.0, le=1.0, description="最小关系强度")
    top_n: Optional[int] = Field(None, ge=1, le=500, description="只显示前N个关键词")
    category_filter: Optional[str] = Field(None, description="分类过滤")


# ============ API Endpoints ============

@router.get("/projects/{project_id}/report-network/visualization")
async def get_report_network_visualization(
    project_id: int,
    format_type: str = Query("d3", description="格式类型"),
    min_strength: float = Query(0.1, ge=0.0, le=1.0, description="最小关系强度"),
    include_isolated: bool = Query(False, description="是否包含孤立节点"),
    db: Session = Depends(get_db)
):
    """
    获取报告关系网络可视化数据

    支持的格式：
    - d3: D3.js force-directed graph（力导向图）
    - echarts: ECharts graph（关系图）
    - cytoscape: Cytoscape.js（网络图）
    - vis: Vis.js network（网络可视化）

    每种格式返回该库所需的标准数据结构
    前端可直接使用，无需额外转换
    """
    try:
        service = NetworkVisualizationService(db)

        visualization_data = service.get_report_network_visualization(
            project_id=project_id,
            format_type=format_type,
            min_strength=min_strength,
            include_isolated=include_isolated
        )

        return {
            "success": True,
            "data": visualization_data
        }

    except Exception as e:
        logger.error(f"获取报告网络可视化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/keyword-network/visualization")
async def get_keyword_network_visualization(
    project_id: int,
    format_type: str = Query("d3", description="格式类型"),
    min_strength: float = Query(0.1, ge=0.0, le=1.0, description="最小关系强度"),
    top_n: Optional[int] = Query(None, ge=1, le=500, description="只显示前N个关键词"),
    category_filter: Optional[str] = Query(None, description="分类过滤"),
    db: Session = Depends(get_db)
):
    """
    获取关键词网络可视化数据

    支持的格式：
    - d3: D3.js force-directed graph
    - echarts: ECharts graph
    - cytoscape: Cytoscape.js
    - vis: Vis.js network

    参数：
    - top_n: 限制显示关键词数量（按频率排序），避免网络过大
    - category_filter: 只显示特定分类的关键词
    """
    try:
        service = NetworkVisualizationService(db)

        visualization_data = service.get_keyword_network_visualization(
            project_id=project_id,
            format_type=format_type,
            min_strength=min_strength,
            top_n=top_n,
            category_filter=category_filter
        )

        return {
            "success": True,
            "data": visualization_data
        }

    except Exception as e:
        logger.error(f"获取关键词网络可视化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/keyword-communities/visualization")
async def get_keyword_community_visualization(
    project_id: int,
    format_type: str = Query("echarts", description="格式类型"),
    min_strength: float = Query(0.1, description="最小关系强度"),
    db: Session = Depends(get_db)
):
    """
    获取关键词社区可视化数据

    先进行社区检测，然后返回社区可视化数据
    节点按社区着色，便于识别关键词聚类
    """
    try:
        # 先构建网络并检测社区
        network_builder = KeywordNetworkBuilder(db)
        network_data = network_builder.build_keyword_network(
            project_id=project_id,
            min_strength=min_strength,
            include_communities=True
        )

        communities = network_data.get('communities', [])

        if not communities:
            return {
                "success": True,
                "data": {
                    "format": format_type,
                    "message": "未检测到社区，可能是关键词网络太小或未安装 python-louvain"
                }
            }

        # 生成社区可视化
        service = NetworkVisualizationService(db)
        visualization_data = service.get_keyword_community_visualization(
            project_id=project_id,
            communities=communities,
            format_type=format_type
        )

        return {
            "success": True,
            "data": visualization_data
        }

    except Exception as e:
        logger.error(f"获取关键词社区可视化失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/network-statistics/charts")
async def get_network_statistics_charts(
    project_id: int,
    network_type: str = Query("report", description="网络类型: report|keyword"),
    db: Session = Depends(get_db)
):
    """
    获取网络统计图表数据

    返回网络的统计分析图表：
    - 报告网络: 度分布、PageRank分布
    - 关键词网络: 分类分布、频率分布

    数据格式适用于 ECharts、Chart.js 等图表库
    """
    try:
        service = NetworkVisualizationService(db)

        charts_data = service.get_network_statistics_charts(
            project_id=project_id,
            network_type=network_type
        )

        return {
            "success": True,
            "data": charts_data
        }

    except Exception as e:
        logger.error(f"获取网络统计图表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/report-network/subgraph")
async def get_report_subgraph(
    project_id: int,
    report_id: str = Query(..., description="中心报告ID"),
    depth: int = Query(1, ge=1, le=3, description="邻域深度"),
    format_type: str = Query("d3", description="格式类型"),
    db: Session = Depends(get_db)
):
    """
    获取报告的局部网络（子图）

    从指定报告出发，提取其邻域网络
    用于聚焦查看某个报告的关联关系

    参数：
    - depth: 邻域深度（1=直接邻居，2=二度邻居）
    """
    try:
        from app.models.report_relation import ReportRelation, ReportNetworkNode, ReportNetworkEdge
        from sqlalchemy import or_

        # 递归获取邻居
        visited_reports = set([report_id])
        to_visit = [report_id]

        for d in range(depth):
            current_level = to_visit.copy()
            to_visit = []

            for rid in current_level:
                # 获取邻居
                relations = db.query(ReportRelation).filter(
                    or_(
                        ReportRelation.source_report_id == rid,
                        ReportRelation.target_report_id == rid
                    )
                ).all()

                for rel in relations:
                    neighbor = rel.target_report_id if rel.source_report_id == rid else rel.source_report_id
                    if neighbor not in visited_reports:
                        visited_reports.add(neighbor)
                        to_visit.append(neighbor)

        # 获取子图的节点和边
        nodes = db.query(ReportNetworkNode).filter(
            and_(
                ReportNetworkNode.project_id == project_id,
                ReportNetworkNode.report_id.in_(visited_reports)
            )
        ).all()

        edges = db.query(ReportNetworkEdge).filter(
            and_(
                ReportNetworkEdge.project_id == project_id,
                ReportNetworkEdge.source_report_id.in_(visited_reports),
                ReportNetworkEdge.target_report_id.in_(visited_reports)
            )
        ).all()

        # 格式化
        service = NetworkVisualizationService(db)

        if format_type == "d3":
            visualization_data = service._format_report_network_d3(nodes, edges, project_id)
        elif format_type == "echarts":
            visualization_data = service._format_report_network_echarts(nodes, edges, project_id)
        elif format_type == "cytoscape":
            visualization_data = service._format_report_network_cytoscape(nodes, edges, project_id)
        elif format_type == "vis":
            visualization_data = service._format_report_network_vis(nodes, edges, project_id)
        else:
            raise ValueError(f"不支持的格式: {format_type}")

        # 标记中心节点
        visualization_data['center_report_id'] = report_id
        visualization_data['depth'] = depth

        return {
            "success": True,
            "data": visualization_data
        }

    except Exception as e:
        logger.error(f"获取报告子图失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/keyword-network/subgraph")
async def get_keyword_subgraph(
    project_id: int,
    keyword_id: int = Query(..., description="中心关键词ID"),
    depth: int = Query(1, ge=1, le=3, description="邻域深度"),
    format_type: str = Query("d3", description="格式类型"),
    db: Session = Depends(get_db)
):
    """
    获取关键词的局部网络（子图）

    从指定关键词出发，提取其邻域网络
    用于聚焦查看某个关键词的关联关系
    """
    try:
        # 使用 KeywordNetworkBuilder 的邻域查询
        network_builder = KeywordNetworkBuilder(db)

        neighborhood_data = network_builder.get_keyword_neighborhood(
            keyword_id=keyword_id,
            project_id=project_id,
            depth=depth,
            min_strength=0.1
        )

        # 转换为指定格式
        from app.models.keyword import Keyword, KeywordRelation

        keyword_ids = [node['id'] for node in neighborhood_data['nodes']]
        keywords = db.query(Keyword).filter(Keyword.id.in_(keyword_ids)).all()

        # 构建关系对象（用于格式化）
        relations = []
        for edge in neighborhood_data['edges']:
            # 创建伪关系对象
            class FakeRelation:
                def __init__(self, source, target, strength, co_occ):
                    self.keyword1_id = source
                    self.keyword2_id = target
                    self.strength = strength
                    self.co_occurrence = co_occ

            relations.append(FakeRelation(
                edge['source'],
                edge['target'],
                edge['strength'],
                edge.get('co_occurrence', 0)
            ))

        # 格式化
        service = NetworkVisualizationService(db)

        if format_type == "d3":
            visualization_data = service._format_keyword_network_d3(keywords, relations, project_id)
        elif format_type == "echarts":
            visualization_data = service._format_keyword_network_echarts(keywords, relations, project_id)
        elif format_type == "cytoscape":
            visualization_data = service._format_keyword_network_cytoscape(keywords, relations, project_id)
        elif format_type == "vis":
            visualization_data = service._format_keyword_network_vis(keywords, relations, project_id)
        else:
            raise ValueError(f"不支持的格式: {format_type}")

        visualization_data['center_keyword_id'] = keyword_id
        visualization_data['center_keyword'] = neighborhood_data['center_keyword']
        visualization_data['depth'] = depth

        return {
            "success": True,
            "data": visualization_data
        }

    except Exception as e:
        logger.error(f"获取关键词子图失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/visualization/formats")
async def get_supported_formats():
    """
    获取支持的可视化格式列表

    返回所有支持的格式及其特点
    """
    return {
        "success": True,
        "data": {
            "formats": [
                {
                    "type": "d3",
                    "name": "D3.js",
                    "description": "强大的数据驱动文档库，适合自定义可视化",
                    "recommended_for": ["高度定制", "复杂交互", "大规模网络"],
                    "library_url": "https://d3js.org/"
                },
                {
                    "type": "echarts",
                    "name": "Apache ECharts",
                    "description": "百度开源的可视化库，配置简单，效果优美",
                    "recommended_for": ["快速开发", "中文文档", "丰富图表"],
                    "library_url": "https://echarts.apache.org/"
                },
                {
                    "type": "cytoscape",
                    "name": "Cytoscape.js",
                    "description": "专业的网络图可视化库，适合复杂网络分析",
                    "recommended_for": ["网络分析", "生物信息", "复杂拓扑"],
                    "library_url": "https://js.cytoscape.org/"
                },
                {
                    "type": "vis",
                    "name": "Vis.js Network",
                    "description": "易用的网络可视化库，开箱即用",
                    "recommended_for": ["简单快速", "默认样式美观", "交互流畅"],
                    "library_url": "https://visjs.org/"
                }
            ]
        }
    }
