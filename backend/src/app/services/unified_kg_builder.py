"""
统一管道知识图谱构建器
将9步骤管道的输出转换为可视化知识图谱
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import hashlib
import math
import random
from sqlalchemy.orm import Session

from app.models.unified_pipeline import (
    DirtyChannelDocument,
    CleanChannelEvent,
    CleanChannelEntity,
    CleanChannelRelation,
    NineStepPipelineStatus
)


class UnifiedKnowledgeGraphBuilder:
    """统一管道知识图谱构建器 - 9步骤管道到可视化图谱的转换"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    async def build_graph_from_pipeline(
        self,
        dirty_doc_id: int,
        include_steps: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        从9步骤统一管道构建知识图谱

        Args:
            dirty_doc_id: 脏数据文档ID
            include_steps: 包含哪些步骤 (1-9)，None表示全部

        Returns:
            图谱数据: {nodes, edges, statistics, metadata}
        """
        # 1. 获取脏数据文档
        dirty_doc = self.db.query(DirtyChannelDocument).filter(
            DirtyChannelDocument.id == dirty_doc_id
        ).first()

        if not dirty_doc:
            raise ValueError(f"脏数据文档 {dirty_doc_id} 不存在")

        # 2. 获取干净数据（步骤1-3的输出）
        clean_events = self.db.query(CleanChannelEvent).filter(
            CleanChannelEvent.dirty_doc_id == dirty_doc_id
        ).all()

        clean_entities = self.db.query(CleanChannelEntity).filter(
            CleanChannelEntity.dirty_doc_id == dirty_doc_id
        ).all()

        clean_relations = self.db.query(CleanChannelRelation).filter(
            CleanChannelRelation.dirty_doc_id == dirty_doc_id
        ).all()

        # 3. 获取9步骤管道状态
        pipeline_status = self.db.query(NineStepPipelineStatus).filter(
            NineStepPipelineStatus.dirty_doc_id == dirty_doc_id
        ).first()

        # 4. 构建节点和边
        nodes = []
        edges = []

        # 步骤3-4: 实体构建 → 图谱节点
        if not include_steps or 3 in include_steps or 4 in include_steps:
            for entity in clean_entities:
                node = self._entity_to_node(entity, dirty_doc_id, pipeline_step=4)
                nodes.append(node)

        # 步骤4: 事件提取 → 事件节点
        if not include_steps or 4 in include_steps:
            for event in clean_events:
                event_node = self._event_to_node(event, dirty_doc_id, pipeline_step=4)
                nodes.append(event_node)

        # 步骤5: 关系发现 → 图谱边
        if not include_steps or 5 in include_steps:
            for relation in clean_relations:
                edge = self._relation_to_edge(relation, dirty_doc_id, pipeline_step=5)
                edges.append(edge)

        # 步骤6-9: 高级推理输出 → 图谱增强
        if pipeline_status:
            # 步骤6: 本体构建 → 层级关系
            if (not include_steps or 6 in include_steps) and pipeline_status.step6_ontology_result:
                ontology_data = pipeline_status.step6_ontology_result
                if isinstance(ontology_data, str):
                    ontology_data = json.loads(ontology_data)
                ontology_edges = self._ontology_to_edges(ontology_data, dirty_doc_id, pipeline_step=6)
                edges.extend(ontology_edges)

            # 步骤7: 逻辑推理 → 推断关系
            if (not include_steps or 7 in include_steps) and pipeline_status.step7_inference_result:
                inference_data = pipeline_status.step7_inference_result
                if isinstance(inference_data, str):
                    inference_data = json.loads(inference_data)
                inference_edges = self._inference_to_edges(inference_data, dirty_doc_id, pipeline_step=7)
                edges.extend(inference_edges)

            # 步骤8: 知识单元化 → 核心节点标记
            if (not include_steps or 8 in include_steps) and pipeline_status.step8_units_result:
                units_data = pipeline_status.step8_units_result
                if isinstance(units_data, str):
                    units_data = json.loads(units_data)
                self._mark_core_nodes(nodes, units_data)

        # 5. 计算节点布局（力导向布局）
        nodes = self._calculate_layout(nodes, edges)

        # 6. 统计信息
        statistics = self._calculate_statistics(nodes, edges, dirty_doc_id)

        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": statistics,
            "metadata": {
                "dirty_doc_id": dirty_doc_id,
                "source_type": dirty_doc.source_type,
                "complete_text_length": len(dirty_doc.complete_text or ""),
                "completeness_score": dirty_doc.completeness_score,
                "total_events": len(clean_events),
                "total_entities": len(clean_entities),
                "total_relations": len(clean_relations),
                "pipeline_current_step": pipeline_status.current_step if pipeline_status else 0,
                "built_at": datetime.now().isoformat()
            }
        }

    def _entity_to_node(self, entity: CleanChannelEntity, dirty_doc_id: int, pipeline_step: int) -> Dict:
        """将实体转换为图谱节点"""
        node_id = f"entity_{entity.id}"

        # 解析属性（SQLAlchemy的JSON字段已自动解析）
        properties = entity.properties if entity.properties else {}

        return {
            "id": node_id,
            "node_id": node_id,
            "name": entity.entity_name,
            "type": entity.entity_type,
            "description": properties.get("description", ""),
            "importance_score": entity.importance_score,
            "is_core": False,  # 步骤8会标记核心节点
            "actions": properties.get("actions", []),
            "context_summary": properties.get("context", ""),
            "dirty_doc_id": dirty_doc_id,
            "clean_event_ids": [entity.event_id] if entity.event_id else [],
            "pipeline_step": pipeline_step,
            "category": properties.get("category", ""),
            "confidence": 1.0,
            "layer": 2,  # 默认次要层级
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _event_to_node(self, event: CleanChannelEvent, dirty_doc_id: int, pipeline_step: int) -> Dict:
        """将事件转换为图谱节点"""
        node_id = f"event_{event.id}"

        # 解析5W1H（SQLAlchemy的JSON字段已自动解析）
        info_nodes = event.information_nodes if event.information_nodes else {}

        return {
            "id": node_id,
            "node_id": node_id,
            "name": event.event_title,
            "type": "EVENT",
            "description": event.event_summary,
            "importance_score": event.importance_score,
            "is_core": True,  # 事件通常是核心节点
            "actions": [event.event_title],
            "context_summary": event.event_summary,
            "timeline": [{
                "who": info_nodes.get("who"),
                "what": info_nodes.get("what"),
                "when": info_nodes.get("when"),
                "where": info_nodes.get("where"),
                "why": info_nodes.get("why"),
                "how": info_nodes.get("how")
            }],
            "dirty_doc_id": dirty_doc_id,
            "clean_event_ids": [event.id],
            "pipeline_step": pipeline_step,
            "confidence": 1.0,
            "layer": 1,  # 事件是核心层级
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _relation_to_edge(self, relation: CleanChannelRelation, dirty_doc_id: int, pipeline_step: int) -> Dict:
        """将关系转换为图谱边"""
        edge_id = f"relation_{relation.id}"

        # 构建源和目标节点ID
        source_node_id = f"entity_{relation.source_entity_id}" if relation.source_entity_id else ""
        target_node_id = f"entity_{relation.target_entity_id}" if relation.target_entity_id else ""

        return {
            "id": edge_id,
            "edge_id": edge_id,
            "source": source_node_id,
            "target": target_node_id,
            "relation_type": relation.relation_type,
            "label": relation.relation_type,
            "description": relation.relation_description,
            "weight": relation.strength_score,
            "confidence": relation.strength_score,
            "dirty_doc_id": dirty_doc_id,
            "clean_relation_id": relation.id,
            "pipeline_step": pipeline_step,
            "evidence": [relation.relation_description] if relation.relation_description else [],
            "verified": False,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _ontology_to_edges(self, ontology_data: Dict, dirty_doc_id: int, pipeline_step: int) -> List[Dict]:
        """将本体结构转换为层级关系边"""
        edges = []

        # 本体数据可能是字符串或字典
        if isinstance(ontology_data, str):
            ontology_data = json.loads(ontology_data)

        # 本体通常包含 is-a, part-of 等层级关系
        hierarchies = ontology_data.get("hierarchies", [])

        for hierarchy in hierarchies:
            parent = hierarchy.get("parent")
            child = hierarchy.get("child")
            relation_type = hierarchy.get("type", "IS_A")

            if parent and child:
                edge_id = f"ontology_{hashlib.md5(f'{parent}_{child}_{relation_type}'.encode()).hexdigest()[:12]}"

                edges.append({
                    "id": edge_id,
                    "edge_id": edge_id,
                    "source": child,
                    "target": parent,
                    "relation_type": relation_type,
                    "label": relation_type,
                    "description": f"{child} {relation_type} {parent}",
                    "weight": 1.0,
                    "confidence": 0.9,
                    "dirty_doc_id": dirty_doc_id,
                    "pipeline_step": pipeline_step,
                    "evidence": ["从本体构建步骤推断"],
                    "verified": False,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })

        return edges

    def _inference_to_edges(self, inference_data: Dict, dirty_doc_id: int, pipeline_step: int) -> List[Dict]:
        """将逻辑推理结果转换为推断关系边"""
        edges = []

        # 推理数据可能是字符串或字典
        if isinstance(inference_data, str):
            inference_data = json.loads(inference_data)

        # 推理结果包含推断出的隐含关系
        inferred_relations = inference_data.get("inferred_relations", [])

        for relation in inferred_relations:
            source = relation.get("source")
            target = relation.get("target")
            relation_type = relation.get("type", "INFERRED")
            confidence = relation.get("confidence", 0.8)
            reasoning = relation.get("reasoning", "")

            if source and target:
                edge_id = f"inferred_{hashlib.md5(f'{source}_{target}_{relation_type}'.encode()).hexdigest()[:12]}"

                edges.append({
                    "id": edge_id,
                    "edge_id": edge_id,
                    "source": source,
                    "target": target,
                    "relation_type": relation_type,
                    "label": relation_type,
                    "description": reasoning,
                    "weight": confidence,
                    "confidence": confidence,
                    "dirty_doc_id": dirty_doc_id,
                    "pipeline_step": pipeline_step,
                    "evidence": [reasoning],
                    "verified": False,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })

        return edges

    def _mark_core_nodes(self, nodes: List[Dict], units_data: Dict):
        """标记核心节点（基于步骤8的知识单元化结果）"""
        core_unit_ids = set(units_data.get("core_units", []))

        for node in nodes:
            # 如果节点在核心单元列表中，标记为核心
            if node["id"] in core_unit_ids or node.get("is_core"):
                node["is_core"] = True
                node["layer"] = 1  # 核心层级
                node["importance_score"] = max(node.get("importance_score", 0), 0.8)

    def _calculate_layout(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        """
        计算节点布局（简化版力导向布局）
        实际应用中可以使用 networkx, d3-force 等库
        """
        n = len(nodes)
        if n == 0:
            return nodes

        radius = 300  # 基础半径

        for i, node in enumerate(nodes):
            layer = node.get("layer", 2)

            # 根据层级调整半径
            layer_radius = radius * (2 - layer * 0.3)  # 核心层更靠近中心

            # 圆形分布
            angle = 2 * math.pi * i / n
            node["x"] = layer_radius * math.cos(angle) + random.uniform(-20, 20)
            node["y"] = layer_radius * math.sin(angle) + random.uniform(-20, 20)

        return nodes

    def _calculate_statistics(self, nodes: List[Dict], edges: List[Dict], dirty_doc_id: int) -> Dict:
        """计算图谱统计信息"""
        # 节点类型统计
        node_type_stats = {}
        for node in nodes:
            node_type = node.get("type", "UNKNOWN")
            node_type_stats[node_type] = node_type_stats.get(node_type, 0) + 1

        # 边类型统计
        edge_type_stats = {}
        for edge in edges:
            edge_type = edge.get("relation_type", "UNKNOWN")
            edge_type_stats[edge_type] = edge_type_stats.get(edge_type, 0) + 1

        # 核心节点数量
        core_nodes = [n for n in nodes if n.get("is_core")]

        # 平均度数（每个节点的平均连接数）
        degree_map = {}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            degree_map[source] = degree_map.get(source, 0) + 1
            degree_map[target] = degree_map.get(target, 0) + 1

        avg_degree = sum(degree_map.values()) / len(degree_map) if degree_map else 0

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "core_nodes": len(core_nodes),
            "node_type_stats": node_type_stats,
            "edge_type_stats": edge_type_stats,
            "average_degree": round(avg_degree, 2),
            "density": round(len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0, 4),
            "layers": {
                "layer_1_core": len([n for n in nodes if n.get("layer") == 1]),
                "layer_2_secondary": len([n for n in nodes if n.get("layer") == 2]),
                "layer_3_detail": len([n for n in nodes if n.get("layer") == 3])
            }
        }

    async def create_snapshot(
        self,
        dirty_doc_id: int,
        name: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建知识图谱快照（用于版本管理和可视化）

        Args:
            dirty_doc_id: 脏数据文档ID
            name: 快照名称
            description: 快照描述

        Returns:
            快照数据
        """
        # 构建完整图谱
        graph_data = await self.build_graph_from_pipeline(dirty_doc_id)

        # 生成快照ID
        snapshot_id = f"snapshot_{dirty_doc_id}_{int(datetime.now().timestamp())}"

        # 保存快照数据
        snapshot = {
            "id": snapshot_id,
            "snapshot_id": snapshot_id,
            "name": name,
            "description": description or f"文档 {dirty_doc_id} 的知识图谱快照",
            "dirty_doc_ids": [dirty_doc_id],
            "total_nodes": graph_data["statistics"]["total_nodes"],
            "total_edges": graph_data["statistics"]["total_edges"],
            "core_nodes": graph_data["statistics"]["core_nodes"],
            "node_type_stats": graph_data["statistics"]["node_type_stats"],
            "edge_type_stats": graph_data["statistics"]["edge_type_stats"],
            "layout_algorithm": "force_directed",
            "layout_data": {
                "nodes": graph_data["nodes"],
                "edges": graph_data["edges"]
            },
            "created_at": datetime.now().isoformat()
        }

        return snapshot

    async def compare_graphs(
        self,
        dirty_doc_id1: int,
        dirty_doc_id2: int
    ) -> Dict[str, Any]:
        """
        比较两个文档的知识图谱

        Returns:
            比较结果：共同节点、独有节点、共同边等
        """
        graph1 = await self.build_graph_from_pipeline(dirty_doc_id1)
        graph2 = await self.build_graph_from_pipeline(dirty_doc_id2)

        # 提取节点名称集合
        nodes1 = set(n["name"] for n in graph1["nodes"])
        nodes2 = set(n["name"] for n in graph2["nodes"])

        # 提取边集合
        edges1 = set(f"{e['source']}-{e['relation_type']}-{e['target']}"
                     for e in graph1["edges"])
        edges2 = set(f"{e['source']}-{e['relation_type']}-{e['target']}"
                     for e in graph2["edges"])

        return {
            "document1": {
                "id": dirty_doc_id1,
                "total_nodes": len(nodes1),
                "total_edges": len(edges1)
            },
            "document2": {
                "id": dirty_doc_id2,
                "total_nodes": len(nodes2),
                "total_edges": len(edges2)
            },
            "comparison": {
                "common_nodes": list(nodes1 & nodes2),
                "unique_to_doc1": list(nodes1 - nodes2),
                "unique_to_doc2": list(nodes2 - nodes1),
                "common_edges": list(edges1 & edges2),
                "unique_edges_doc1": list(edges1 - edges2),
                "unique_edges_doc2": list(edges2 - edges1),
                "similarity_score": round(len(nodes1 & nodes2) / len(nodes1 | nodes2) if (nodes1 | nodes2) else 0, 4)
            }
        }
