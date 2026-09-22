"""
报告关系构建服务
自动分析和构建报告之间的关系网络
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
from collections import defaultdict, Counter
import json

from app.models.report import Report
from app.models.report_relation import (
    ReportRelation, ReportEntity, ReportEntityRelation,
    ReportRelationType, ReportEntityType,
    ReportNetworkNode, ReportNetworkEdge
)

logger = logging.getLogger(__name__)


class ReportRelationBuilder:
    """报告关系构建器"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ============================================
    # 1. 报告实体提取
    # ============================================

    def extract_report_entities(
        self,
        report_id: str,
        use_llm: bool = False
    ) -> List[ReportEntity]:
        """
        从报告中提取实体

        Args:
            report_id: 报告ID
            use_llm: 是否使用LLM增强提取

        Returns:
            提取的实体列表
        """
        logger.info(f"开始提取报告 {report_id} 的实体")

        # 获取报告
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report:
            logger.warning(f"报告 {report_id} 不存在")
            return []

        # 获取报告内容
        content = report.content or {}
        text_content = self._extract_text_from_content(content)

        if not text_content:
            logger.warning(f"报告 {report_id} 没有文本内容")
            return []

        # 方法1: 从关键词中提取实体
        entities_from_keywords = self._extract_entities_from_keywords(report_id, text_content)

        # 方法2: 从文档关联中提取实体
        entities_from_documents = self._extract_entities_from_documents(report_id)

        # 方法3: 使用LLM提取（可选）
        if use_llm:
            entities_from_llm = self._extract_entities_with_llm(report_id, text_content)
            all_entities = entities_from_keywords + entities_from_documents + entities_from_llm
        else:
            all_entities = entities_from_keywords + entities_from_documents

        # 去重和合并
        merged_entities = self._merge_entities(all_entities)

        # 保存到数据库
        saved_entities = self._save_entities(report_id, merged_entities)

        logger.info(f"✅ 报告 {report_id} 提取了 {len(saved_entities)} 个实体")
        return saved_entities

    def _extract_text_from_content(self, content: Dict) -> str:
        """从报告content JSON中提取文本"""
        text_parts = []

        # 提取摘要
        if "summary" in content and content["summary"]:
            text_parts.append(content["summary"])

        # 提取章节内容
        if "sections" in content:
            for section in content["sections"]:
                if isinstance(section, dict) and "content" in section:
                    text_parts.append(section["content"])

        return "\n\n".join(text_parts)

    def _extract_entities_from_keywords(
        self,
        report_id: str,
        text_content: str
    ) -> List[Dict]:
        """从关键词中提取实体"""
        entities = []

        try:
            # 获取报告的数据源（关联的文档）
            report = self.db.query(Report).filter(Report.id == report_id).first()
            if not report or not report.data_sources:
                return entities

            document_ids = report.data_sources.get('document_ids', [])
            if not document_ids:
                return entities

            # 从文档关键词中提取
            from app.models.keyword import Keyword, DocumentKeyword

            # 获取这些文档的关键词
            keywords = self.db.query(Keyword, DocumentKeyword)\
                .join(DocumentKeyword, Keyword.id == DocumentKeyword.keyword_id)\
                .filter(DocumentKeyword.document_id.in_(document_ids))\
                .all()

            # 按类别分组
            for keyword, doc_keyword in keywords:
                entity_type_map = {
                    "人物": ReportEntityType.PERSON,
                    "地点": ReportEntityType.LOCATION,
                    "事件": ReportEntityType.EVENT,
                    "组织": ReportEntityType.ORGANIZATION,
                    "主题": ReportEntityType.THEME,
                }

                entity_type = entity_type_map.get(keyword.category)
                if entity_type:
                    entities.append({
                        "name": keyword.text,
                        "entity_type": entity_type,
                        "frequency": doc_keyword.frequency or 1,
                        "importance": keyword.weight or 0.5,
                        "source": "keyword"
                    })

        except Exception as e:
            logger.warning(f"从关键词提取实体失败: {e}")

        return entities

    def _extract_entities_from_documents(self, report_id: str) -> List[Dict]:
        """从关联的文档实体中提取"""
        entities = []

        try:
            report = self.db.query(Report).filter(Report.id == report_id).first()
            if not report or not report.data_sources:
                return entities

            document_ids = report.data_sources.get('document_ids', [])
            if not document_ids:
                return entities

            # 从知识图谱实体中提取
            from app.models.knowledge_graph import Entity

            kg_entities = self.db.query(Entity)\
                .filter(Entity.document_id.in_(document_ids))\
                .all()

            for entity in kg_entities:
                entities.append({
                    "name": entity.name,
                    "entity_type": self._map_kg_entity_type(entity.entity_type),
                    "frequency": entity.frequency or 1,
                    "importance": entity.confidence or 0.5,
                    "source": "knowledge_graph",
                    "source_entity_id": entity.id
                })

        except Exception as e:
            logger.warning(f"从文档实体提取失败: {e}")

        return entities

    def _extract_entities_with_llm(self, report_id: str, text_content: str) -> List[Dict]:
        """使用LLM提取实体（可选）"""
        # TODO: 实现LLM实体提取
        logger.info("LLM实体提取待实现")
        return []

    def _map_kg_entity_type(self, kg_type: str) -> ReportEntityType:
        """映射知识图谱实体类型到报告实体类型"""
        mapping = {
            "PERSON": ReportEntityType.PERSON,
            "LOCATION": ReportEntityType.LOCATION,
            "EVENT": ReportEntityType.EVENT,
            "ORGANIZATION": ReportEntityType.ORGANIZATION,
            "GPE": ReportEntityType.LOCATION,
            "DATE": ReportEntityType.EVENT,
        }
        return mapping.get(kg_type, ReportEntityType.THEME)

    def _merge_entities(self, entities: List[Dict]) -> List[Dict]:
        """合并重复的实体"""
        entity_map = {}

        for entity in entities:
            key = (entity["name"], entity["entity_type"])

            if key in entity_map:
                # 合并频率和重要性
                entity_map[key]["frequency"] += entity.get("frequency", 1)
                entity_map[key]["importance"] = max(
                    entity_map[key]["importance"],
                    entity.get("importance", 0.5)
                )
            else:
                entity_map[key] = entity

        return list(entity_map.values())

    def _save_entities(self, report_id: str, entities: List[Dict]) -> List[ReportEntity]:
        """保存实体到数据库"""
        saved_entities = []

        for entity_data in entities:
            # 检查是否已存在
            existing = self.db.query(ReportEntity).filter(
                and_(
                    ReportEntity.report_id == report_id,
                    ReportEntity.name == entity_data["name"],
                    ReportEntity.entity_type == entity_data["entity_type"]
                )
            ).first()

            if existing:
                # 更新频率和重要性
                existing.frequency = entity_data.get("frequency", existing.frequency)
                existing.importance = entity_data.get("importance", existing.importance)
                saved_entities.append(existing)
            else:
                # 创建新实体
                new_entity = ReportEntity(
                    report_id=report_id,
                    name=entity_data["name"],
                    entity_type=entity_data["entity_type"],
                    frequency=entity_data.get("frequency", 1),
                    importance=entity_data.get("importance", 0.5),
                    source_entity_id=entity_data.get("source_entity_id")
                )
                self.db.add(new_entity)
                saved_entities.append(new_entity)

        self.db.commit()
        return saved_entities

    # ============================================
    # 2. 报告关系分析
    # ============================================

    def build_report_relations(
        self,
        project_id: int,
        min_shared_entities: int = 2
    ) -> Dict[str, Any]:
        """
        构建报告之间的关系

        Args:
            project_id: 项目ID
            min_shared_entities: 最小共享实体数（过滤弱关系）

        Returns:
            统计信息
        """
        logger.info(f"开始构建项目 {project_id} 的报告关系")

        # 获取项目中的所有报告
        reports = self.db.query(Report).filter(
            Report.config.contains({"project_id": project_id})
        ).all()

        if len(reports) < 2:
            logger.warning(f"项目 {project_id} 报告数量不足（{len(reports)}）")
            return {"reports_count": len(reports), "relations_created": 0}

        logger.info(f"找到 {len(reports)} 个报告")

        stats = {
            "reports_count": len(reports),
            "relations_created": 0,
            "entity_relations_created": 0
        }

        # 两两比较报告
        for i in range(len(reports)):
            for j in range(i + 1, len(reports)):
                report_a = reports[i]
                report_b = reports[j]

                # 分析两个报告之间的关系
                relation = self._analyze_report_pair(
                    report_a, report_b, min_shared_entities
                )

                if relation:
                    stats["relations_created"] += 1

        logger.info(f"✅ 报告关系构建完成: {stats}")
        return stats

    def _analyze_report_pair(
        self,
        report_a: Report,
        report_b: Report,
        min_shared_entities: int
    ) -> Optional[ReportRelation]:
        """分析两个报告之间的关系"""

        # 获取两个报告的实体
        entities_a = self.db.query(ReportEntity).filter(
            ReportEntity.report_id == report_a.id
        ).all()

        entities_b = self.db.query(ReportEntity).filter(
            ReportEntity.report_id == report_b.id
        ).all()

        if not entities_a or not entities_b:
            return None

        # 查找共享实体
        entities_a_set = {(e.name, e.entity_type) for e in entities_a}
        entities_b_set = {(e.name, e.entity_type) for e in entities_b}

        shared = entities_a_set & entities_b_set

        if len(shared) < min_shared_entities:
            return None

        # 计算关系强度
        strength = len(shared) / max(len(entities_a_set), len(entities_b_set))

        # 推断关系类型
        relation_type = self._infer_relation_type(report_a, report_b, shared)

        # 检查是否已存在
        existing = self.db.query(ReportRelation).filter(
            or_(
                and_(
                    ReportRelation.source_report_id == report_a.id,
                    ReportRelation.target_report_id == report_b.id
                ),
                and_(
                    ReportRelation.source_report_id == report_b.id,
                    ReportRelation.target_report_id == report_a.id
                )
            )
        ).first()

        if existing:
            # 更新现有关系
            existing.strength = strength
            existing.shared_entities = [f"{name}:{etype.value}" for name, etype in shared]
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing
        else:
            # 创建新关系
            relation = ReportRelation(
                source_report_id=report_a.id,
                target_report_id=report_b.id,
                relation_type=relation_type,
                strength=strength,
                shared_entities=[f"{name}:{etype.value}" for name, etype in shared],
                confidence=int(strength * 100)
            )
            self.db.add(relation)
            self.db.commit()
            return relation

    def _infer_relation_type(
        self,
        report_a: Report,
        report_b: Report,
        shared_entities: set
    ) -> ReportRelationType:
        """推断报告关系类型"""

        # 简单规则：基于时间和报告类型
        if report_a.created_at < report_b.created_at:
            # B 可能基于 A
            return ReportRelationType.BUILDS_ON
        elif report_a.report_type == report_b.report_type:
            # 同类型报告可能是对比关系
            return ReportRelationType.COMPARES
        else:
            # 默认为引用关系
            return ReportRelationType.REFERENCES

    # ============================================
    # 3. 网络构建
    # ============================================

    def build_report_network(
        self,
        project_id: int,
        include_entities: bool = True
    ) -> Dict[str, Any]:
        """
        构建报告网络（用于可视化）

        Args:
            project_id: 项目ID
            include_entities: 是否包含实体节点

        Returns:
            网络数据 {nodes: [], edges: []}
        """
        logger.info(f"开始构建项目 {project_id} 的报告网络")

        # 清空旧的网络数据
        self.db.query(ReportNetworkNode).filter(
            ReportNetworkNode.project_id == project_id
        ).delete()
        self.db.query(ReportNetworkEdge).filter(
            ReportNetworkEdge.project_id == project_id
        ).delete()
        self.db.commit()

        nodes = []
        edges = []

        # 1. 添加报告节点
        reports = self.db.query(Report).filter(
            Report.config.contains({"project_id": project_id})
        ).all()

        for report in reports:
            node = ReportNetworkNode(
                project_id=project_id,
                node_id=f"report_{report.id}",
                node_type="report",
                label=report.title,
                properties={
                    "type": report.report_type.value if report.report_type else "unknown",
                    "size": 20,
                    "color": self._get_report_color(report.report_type)
                }
            )
            self.db.add(node)
            nodes.append(node)

        # 2. 添加报告关系边
        relations = self.db.query(ReportRelation).join(
            Report, Report.id == ReportRelation.source_report_id
        ).filter(
            Report.config.contains({"project_id": project_id})
        ).all()

        for relation in relations:
            edge = ReportNetworkEdge(
                project_id=project_id,
                source_node_id=f"report_{relation.source_report_id}",
                target_node_id=f"report_{relation.target_report_id}",
                edge_type=relation.relation_type.value,
                weight=relation.strength or 0.5,
                properties={
                    "color": "#999",
                    "width": max(1, relation.strength * 5)
                }
            )
            self.db.add(edge)
            edges.append(edge)

        # 3. 添加实体节点（可选）
        if include_entities:
            # TODO: 添加高频实体作为节点
            pass

        self.db.commit()

        # 4. 计算中心性指标
        self._calculate_centrality(project_id, nodes, edges)

        logger.info(f"✅ 网络构建完成: {len(nodes)} 个节点, {len(edges)} 条边")

        return {
            "nodes": [n.to_dict() for n in nodes],
            "edges": [e.to_dict() for e in edges],
            "stats": {
                "nodes_count": len(nodes),
                "edges_count": len(edges)
            }
        }

    def _get_report_color(self, report_type) -> str:
        """根据报告类型返回颜色"""
        color_map = {
            "research": "#1f77b4",
            "summary": "#ff7f0e",
            "analysis": "#2ca02c"
        }
        return color_map.get(report_type.value if report_type else "unknown", "#7f7f7f")

    def _calculate_centrality(
        self,
        project_id: int,
        nodes: List[ReportNetworkNode],
        edges: List[ReportNetworkEdge]
    ):
        """计算中心性指标"""
        try:
            import networkx as nx

            # 构建NetworkX图
            G = nx.Graph()

            for node in nodes:
                G.add_node(node.node_id)

            for edge in edges:
                G.add_edge(edge.source_node_id, edge.target_node_id, weight=edge.weight)

            if len(G.nodes()) == 0:
                return

            # 计算度中心性
            degree_centrality = nx.degree_centrality(G)

            # 计算中介中心性
            try:
                betweenness_centrality = nx.betweenness_centrality(G)
            except:
                betweenness_centrality = {}

            # 计算接近中心性
            try:
                closeness_centrality = nx.closeness_centrality(G)
            except:
                closeness_centrality = {}

            # 更新节点
            for node in nodes:
                node.centrality_degree = degree_centrality.get(node.node_id, 0.0)
                node.centrality_betweenness = betweenness_centrality.get(node.node_id, 0.0)
                node.centrality_closeness = closeness_centrality.get(node.node_id, 0.0)

            self.db.commit()

        except Exception as e:
            logger.warning(f"中心性计算失败: {e}")

    # ============================================
    # 4. 查询和统计
    # ============================================

    def get_report_relations(
        self,
        report_id: str,
        direction: str = "both"
    ) -> List[Dict]:
        """
        获取报告的关系

        Args:
            report_id: 报告ID
            direction: "incoming" | "outgoing" | "both"
        """
        relations = []

        if direction in ["outgoing", "both"]:
            outgoing = self.db.query(ReportRelation).filter(
                ReportRelation.source_report_id == report_id
            ).all()
            relations.extend(outgoing)

        if direction in ["incoming", "both"]:
            incoming = self.db.query(ReportRelation).filter(
                ReportRelation.target_report_id == report_id
            ).all()
            relations.extend(incoming)

        return [r.to_dict() for r in relations]

    def get_report_entities(self, report_id: str) -> List[Dict]:
        """获取报告的所有实体"""
        entities = self.db.query(ReportEntity).filter(
            ReportEntity.report_id == report_id
        ).order_by(ReportEntity.importance.desc()).all()

        return [e.to_dict() for e in entities]

    def get_network_statistics(self, project_id: int) -> Dict[str, Any]:
        """获取网络统计信息"""

        nodes_count = self.db.query(ReportNetworkNode).filter(
            ReportNetworkNode.project_id == project_id
        ).count()

        edges_count = self.db.query(ReportNetworkEdge).filter(
            ReportNetworkEdge.project_id == project_id
        ).count()

        # 最重要的节点（按度中心性）
        top_nodes = self.db.query(ReportNetworkNode).filter(
            ReportNetworkNode.project_id == project_id
        ).order_by(ReportNetworkNode.centrality_degree.desc()).limit(10).all()

        return {
            "nodes_count": nodes_count,
            "edges_count": edges_count,
            "density": edges_count / (nodes_count * (nodes_count - 1) / 2) if nodes_count > 1 else 0,
            "top_nodes": [
                {
                    "label": n.label,
                    "type": n.node_type,
                    "centrality": n.centrality_degree
                }
                for n in top_nodes
            ]
        }


# ============================================
# 全局实例
# ============================================

def get_report_relation_builder(db: Session) -> ReportRelationBuilder:
    """获取报告关系构建器实例"""
    return ReportRelationBuilder(db)
