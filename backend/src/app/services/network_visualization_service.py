"""
网络可视化服务
专门用于报告关系网络、关键词网络的可视化数据生成
支持多种前端可视化库的数据格式
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.report import Report
from app.models.report_relation import ReportRelation, ReportNetworkNode, ReportNetworkEdge
from app.models.keyword import Keyword, KeywordRelation

logger = logging.getLogger(__name__)


class NetworkVisualizationService:
    """网络可视化服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ==================== 报告关系网络可视化 ====================

    def get_report_network_visualization(
        self,
        project_id: int,
        format_type: str = "d3",
        min_strength: float = 0.1,
        include_isolated: bool = False
    ) -> Dict[str, Any]:
        """
        获取报告关系网络可视化数据

        格式类型：
        - d3: D3.js force-directed graph
        - echarts: ECharts graph
        - cytoscape: Cytoscape.js
        - vis: Vis.js network

        Returns:
            标准化的网络数据格式
        """
        logger.info(f"生成报告网络可视化: project_id={project_id}, format={format_type}")

        # 获取节点
        nodes_query = self.db.query(ReportNetworkNode).filter(
            ReportNetworkNode.project_id == project_id
        )

        if not include_isolated:
            nodes_query = nodes_query.filter(
                ReportNetworkNode.degree_centrality > 0
            )

        nodes = nodes_query.all()

        # 获取边
        edges = self.db.query(ReportNetworkEdge).filter(
            and_(
                ReportNetworkEdge.project_id == project_id,
                ReportNetworkEdge.strength >= min_strength
            )
        ).all()

        # 根据格式转换
        if format_type == "d3":
            return self._format_report_network_d3(nodes, edges, project_id)
        elif format_type == "echarts":
            return self._format_report_network_echarts(nodes, edges, project_id)
        elif format_type == "cytoscape":
            return self._format_report_network_cytoscape(nodes, edges, project_id)
        elif format_type == "vis":
            return self._format_report_network_vis(nodes, edges, project_id)
        else:
            raise ValueError(f"不支持的格式: {format_type}")

    def _format_report_network_d3(
        self,
        nodes: List[ReportNetworkNode],
        edges: List[ReportNetworkEdge],
        project_id: int
    ) -> Dict[str, Any]:
        """D3.js 格式"""
        # 获取报告信息
        report_ids = [node.report_id for node in nodes]
        reports = self.db.query(Report).filter(Report.id.in_(report_ids)).all()
        report_dict = {r.id: r for r in reports}

        d3_nodes = []
        for node in nodes:
            report = report_dict.get(node.report_id)
            d3_nodes.append({
                "id": node.report_id,
                "name": report.title if report else node.report_id,
                "group": report.report_type if report else "unknown",
                "value": node.pagerank * 100,  # 节点大小
                "degree": node.degree_centrality,
                "betweenness": node.betweenness_centrality,
                "pagerank": node.pagerank
            })

        d3_links = []
        for edge in edges:
            d3_links.append({
                "source": edge.source_report_id,
                "target": edge.target_report_id,
                "value": edge.strength,  # 边粗细
                "type": edge.relation_type
            })

        return {
            "format": "d3",
            "nodes": d3_nodes,
            "links": d3_links,
            "metadata": {
                "project_id": project_id,
                "node_count": len(d3_nodes),
                "edge_count": len(d3_links)
            }
        }

    def _format_report_network_echarts(
        self,
        nodes: List[ReportNetworkNode],
        edges: List[ReportNetworkEdge],
        project_id: int
    ) -> Dict[str, Any]:
        """ECharts 格式"""
        report_ids = [node.report_id for node in nodes]
        reports = self.db.query(Report).filter(Report.id.in_(report_ids)).all()
        report_dict = {r.id: r for r in reports}

        echarts_nodes = []
        for node in nodes:
            report = report_dict.get(node.report_id)
            echarts_nodes.append({
                "id": node.report_id,
                "name": report.title if report else node.report_id,
                "category": report.report_type if report else "unknown",
                "symbolSize": node.pagerank * 100,
                "value": node.pagerank,
                "label": {
                    "show": node.pagerank > 0.01  # 只显示重要节点标签
                }
            })

        echarts_links = []
        for edge in edges:
            echarts_links.append({
                "source": edge.source_report_id,
                "target": edge.target_report_id,
                "value": edge.strength,
                "lineStyle": {
                    "width": edge.strength * 5
                }
            })

        # 分类
        categories = list(set(node["category"] for node in echarts_nodes))

        return {
            "format": "echarts",
            "data": echarts_nodes,
            "links": echarts_links,
            "categories": [{"name": cat} for cat in categories],
            "metadata": {
                "project_id": project_id,
                "node_count": len(echarts_nodes),
                "edge_count": len(echarts_links)
            }
        }

    def _format_report_network_cytoscape(
        self,
        nodes: List[ReportNetworkNode],
        edges: List[ReportNetworkEdge],
        project_id: int
    ) -> Dict[str, Any]:
        """Cytoscape.js 格式"""
        report_ids = [node.report_id for node in nodes]
        reports = self.db.query(Report).filter(Report.id.in_(report_ids)).all()
        report_dict = {r.id: r for r in reports}

        elements = []

        # 节点
        for node in nodes:
            report = report_dict.get(node.report_id)
            elements.append({
                "data": {
                    "id": node.report_id,
                    "label": report.title if report else node.report_id,
                    "type": report.report_type if report else "unknown",
                    "pagerank": node.pagerank,
                    "degree": node.degree_centrality
                },
                "classes": f"report-{report.report_type if report else 'unknown'}"
            })

        # 边
        for edge in edges:
            elements.append({
                "data": {
                    "id": f"{edge.source_report_id}-{edge.target_report_id}",
                    "source": edge.source_report_id,
                    "target": edge.target_report_id,
                    "strength": edge.strength,
                    "type": edge.relation_type
                }
            })

        return {
            "format": "cytoscape",
            "elements": elements,
            "metadata": {
                "project_id": project_id,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }

    def _format_report_network_vis(
        self,
        nodes: List[ReportNetworkNode],
        edges: List[ReportNetworkEdge],
        project_id: int
    ) -> Dict[str, Any]:
        """Vis.js 格式"""
        report_ids = [node.report_id for node in nodes]
        reports = self.db.query(Report).filter(Report.id.in_(report_ids)).all()
        report_dict = {r.id: r for r in reports}

        vis_nodes = []
        for node in nodes:
            report = report_dict.get(node.report_id)
            vis_nodes.append({
                "id": node.report_id,
                "label": report.title if report else node.report_id,
                "title": f"PageRank: {node.pagerank:.4f}",  # 悬浮提示
                "value": node.pagerank * 100,
                "group": report.report_type if report else "unknown"
            })

        vis_edges = []
        for edge in edges:
            vis_edges.append({
                "from": edge.source_report_id,
                "to": edge.target_report_id,
                "value": edge.strength,
                "title": f"强度: {edge.strength:.2f}"
            })

        return {
            "format": "vis",
            "nodes": vis_nodes,
            "edges": vis_edges,
            "metadata": {
                "project_id": project_id,
                "node_count": len(vis_nodes),
                "edge_count": len(vis_edges)
            }
        }

    # ==================== 关键词网络可视化 ====================

    def get_keyword_network_visualization(
        self,
        project_id: int,
        format_type: str = "d3",
        min_strength: float = 0.1,
        top_n: Optional[int] = None,
        category_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取关键词网络可视化数据

        Args:
            project_id: 项目ID
            format_type: 格式类型 (d3, echarts, cytoscape, vis)
            min_strength: 最小关系强度
            top_n: 只显示前N个关键词（按频率）
            category_filter: 分类过滤
        """
        logger.info(f"生成关键词网络可视化: project_id={project_id}, format={format_type}")

        # 获取关键词
        keywords_query = self.db.query(Keyword).filter(
            Keyword.project_id == project_id
        )

        if category_filter:
            keywords_query = keywords_query.filter(Keyword.category == category_filter)

        if top_n:
            keywords_query = keywords_query.order_by(Keyword.frequency.desc()).limit(top_n)

        keywords = keywords_query.all()
        keyword_ids = [kw.id for kw in keywords]

        if not keyword_ids:
            return {
                "format": format_type,
                "nodes": [],
                "links": [],
                "metadata": {"project_id": project_id, "node_count": 0, "edge_count": 0}
            }

        # 获取关系
        relations = self.db.query(KeywordRelation).filter(
            and_(
                KeywordRelation.project_id == project_id,
                KeywordRelation.strength >= min_strength,
                KeywordRelation.keyword1_id.in_(keyword_ids),
                KeywordRelation.keyword2_id.in_(keyword_ids)
            )
        ).all()

        # 根据格式转换
        if format_type == "d3":
            return self._format_keyword_network_d3(keywords, relations, project_id)
        elif format_type == "echarts":
            return self._format_keyword_network_echarts(keywords, relations, project_id)
        elif format_type == "cytoscape":
            return self._format_keyword_network_cytoscape(keywords, relations, project_id)
        elif format_type == "vis":
            return self._format_keyword_network_vis(keywords, relations, project_id)
        else:
            raise ValueError(f"不支持的格式: {format_type}")

    def _format_keyword_network_d3(
        self,
        keywords: List[Keyword],
        relations: List[KeywordRelation],
        project_id: int
    ) -> Dict[str, Any]:
        """D3.js 格式 - 关键词网络"""
        d3_nodes = []
        for kw in keywords:
            d3_nodes.append({
                "id": kw.id,
                "name": kw.text,
                "group": kw.category or "未分类",
                "value": kw.frequency,  # 节点大小
                "importance": kw.importance
            })

        d3_links = []
        for rel in relations:
            d3_links.append({
                "source": rel.keyword1_id,
                "target": rel.keyword2_id,
                "value": rel.strength,
                "co_occurrence": rel.co_occurrence
            })

        return {
            "format": "d3",
            "nodes": d3_nodes,
            "links": d3_links,
            "metadata": {
                "project_id": project_id,
                "node_count": len(d3_nodes),
                "edge_count": len(d3_links)
            }
        }

    def _format_keyword_network_echarts(
        self,
        keywords: List[Keyword],
        relations: List[KeywordRelation],
        project_id: int
    ) -> Dict[str, Any]:
        """ECharts 格式 - 关键词网络"""
        echarts_nodes = []
        for kw in keywords:
            echarts_nodes.append({
                "id": kw.id,
                "name": kw.text,
                "category": kw.category or "未分类",
                "symbolSize": min(10 + kw.frequency * 2, 80),  # 限制最大尺寸
                "value": kw.frequency,
                "label": {
                    "show": kw.frequency > 5  # 只显示高频关键词标签
                }
            })

        echarts_links = []
        for rel in relations:
            echarts_links.append({
                "source": rel.keyword1_id,
                "target": rel.keyword2_id,
                "value": rel.strength,
                "lineStyle": {
                    "width": rel.strength * 3,
                    "curveness": 0.1
                }
            })

        # 分类
        categories = list(set(kw.category or "未分类" for kw in keywords))

        return {
            "format": "echarts",
            "data": echarts_nodes,
            "links": echarts_links,
            "categories": [{"name": cat} for cat in categories],
            "metadata": {
                "project_id": project_id,
                "node_count": len(echarts_nodes),
                "edge_count": len(echarts_links)
            }
        }

    def _format_keyword_network_cytoscape(
        self,
        keywords: List[Keyword],
        relations: List[KeywordRelation],
        project_id: int
    ) -> Dict[str, Any]:
        """Cytoscape.js 格式 - 关键词网络"""
        elements = []

        # 节点
        for kw in keywords:
            elements.append({
                "data": {
                    "id": str(kw.id),
                    "label": kw.text,
                    "category": kw.category or "未分类",
                    "frequency": kw.frequency,
                    "importance": kw.importance
                },
                "classes": f"keyword-{kw.category or 'uncategorized'}"
            })

        # 边
        for rel in relations:
            elements.append({
                "data": {
                    "id": f"{rel.keyword1_id}-{rel.keyword2_id}",
                    "source": str(rel.keyword1_id),
                    "target": str(rel.keyword2_id),
                    "strength": rel.strength,
                    "co_occurrence": rel.co_occurrence
                }
            })

        return {
            "format": "cytoscape",
            "elements": elements,
            "metadata": {
                "project_id": project_id,
                "node_count": len(keywords),
                "edge_count": len(relations)
            }
        }

    def _format_keyword_network_vis(
        self,
        keywords: List[Keyword],
        relations: List[KeywordRelation],
        project_id: int
    ) -> Dict[str, Any]:
        """Vis.js 格式 - 关键词网络"""
        vis_nodes = []
        for kw in keywords:
            vis_nodes.append({
                "id": kw.id,
                "label": kw.text,
                "title": f"频率: {kw.frequency}",
                "value": kw.frequency,
                "group": kw.category or "未分类"
            })

        vis_edges = []
        for rel in relations:
            vis_edges.append({
                "from": rel.keyword1_id,
                "to": rel.keyword2_id,
                "value": rel.strength,
                "title": f"共现: {rel.co_occurrence}次"
            })

        return {
            "format": "vis",
            "nodes": vis_nodes,
            "edges": vis_edges,
            "metadata": {
                "project_id": project_id,
                "node_count": len(vis_nodes),
                "edge_count": len(vis_edges)
            }
        }

    # ==================== 社区可视化 ====================

    def get_keyword_community_visualization(
        self,
        project_id: int,
        communities: List[Dict[str, Any]],
        format_type: str = "echarts"
    ) -> Dict[str, Any]:
        """
        关键词社区可视化

        Args:
            project_id: 项目ID
            communities: 社区数据（来自 KeywordNetworkBuilder）
            format_type: 格式类型

        Returns:
            社区可视化数据
        """
        if format_type == "echarts":
            # ECharts Graph 支持社区高亮
            community_data = []

            for comm in communities:
                keyword_ids = comm['keywords']
                keywords = self.db.query(Keyword).filter(
                    Keyword.id.in_(keyword_ids)
                ).all()

                for kw in keywords:
                    community_data.append({
                        "name": kw.text,
                        "value": kw.frequency,
                        "category": f"社区 {comm['id']}: {comm['label']}",
                        "symbolSize": min(10 + kw.frequency * 2, 60)
                    })

            return {
                "format": "echarts",
                "type": "community",
                "data": community_data,
                "communities": communities,
                "metadata": {
                    "project_id": project_id,
                    "community_count": len(communities)
                }
            }

        return {"error": "不支持的格式"}

    # ==================== 统计图表 ====================

    def get_network_statistics_charts(
        self,
        project_id: int,
        network_type: str = "report"
    ) -> Dict[str, Any]:
        """
        获取网络统计图表数据

        Args:
            network_type: report | keyword
        """
        if network_type == "report":
            return self._get_report_network_stats(project_id)
        elif network_type == "keyword":
            return self._get_keyword_network_stats(project_id)
        else:
            raise ValueError(f"未知网络类型: {network_type}")

    def _get_report_network_stats(self, project_id: int) -> Dict[str, Any]:
        """报告网络统计"""
        nodes = self.db.query(ReportNetworkNode).filter(
            ReportNetworkNode.project_id == project_id
        ).all()

        if not nodes:
            return {"charts": []}

        # 度分布
        degree_distribution = {}
        for node in nodes:
            degree = int(node.degree_centrality * 100)
            degree_distribution[degree] = degree_distribution.get(degree, 0) + 1

        # PageRank 分布
        pagerank_ranges = {"0-0.01": 0, "0.01-0.05": 0, "0.05-0.1": 0, ">0.1": 0}
        for node in nodes:
            pr = node.pagerank
            if pr < 0.01:
                pagerank_ranges["0-0.01"] += 1
            elif pr < 0.05:
                pagerank_ranges["0.01-0.05"] += 1
            elif pr < 0.1:
                pagerank_ranges["0.05-0.1"] += 1
            else:
                pagerank_ranges[">0.1"] += 1

        return {
            "charts": [
                {
                    "type": "bar",
                    "title": "度分布",
                    "data": {
                        "x": list(degree_distribution.keys()),
                        "y": list(degree_distribution.values())
                    }
                },
                {
                    "type": "pie",
                    "title": "PageRank分布",
                    "data": [
                        {"name": k, "value": v}
                        for k, v in pagerank_ranges.items()
                    ]
                }
            ]
        }

    def _get_keyword_network_stats(self, project_id: int) -> Dict[str, Any]:
        """关键词网络统计"""
        keywords = self.db.query(Keyword).filter(
            Keyword.project_id == project_id
        ).all()

        if not keywords:
            return {"charts": []}

        # 分类分布
        category_distribution = {}
        for kw in keywords:
            cat = kw.category or "未分类"
            category_distribution[cat] = category_distribution.get(cat, 0) + 1

        # 频率分布
        frequency_ranges = {"1-5": 0, "6-10": 0, "11-20": 0, ">20": 0}
        for kw in keywords:
            freq = kw.frequency
            if freq <= 5:
                frequency_ranges["1-5"] += 1
            elif freq <= 10:
                frequency_ranges["6-10"] += 1
            elif freq <= 20:
                frequency_ranges["11-20"] += 1
            else:
                frequency_ranges[">20"] += 1

        return {
            "charts": [
                {
                    "type": "pie",
                    "title": "关键词分类分布",
                    "data": [
                        {"name": k, "value": v}
                        for k, v in category_distribution.items()
                    ]
                },
                {
                    "type": "bar",
                    "title": "关键词频率分布",
                    "data": {
                        "x": list(frequency_ranges.keys()),
                        "y": list(frequency_ranges.values())
                    }
                }
            ]
        }
