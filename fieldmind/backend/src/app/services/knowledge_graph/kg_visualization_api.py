"""
知识图谱可视化 API
Knowledge Graph Visualization API

功能：
1. 生成网络图数据（nodes + edges）
2. 生成时间线数据
3. 生成关系矩阵
4. 生成树形图数据
5. 生成热力图数据
6. 导出为标准格式（Cytoscape.js, D3.js, ECharts）
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
import logging
from typing import List, Dict, Any, Optional
import json
from collections import defaultdict

from app.services.knowledge_graph.kg_query_service import KnowledgeGraphQueryService
from app.services.knowledge_graph.unified_query_interface import UnifiedQueryInterface

logger = logging.getLogger(__name__)


class KnowledgeGraphVisualizationAPI:
    """知识图谱可视化 API"""

    def __init__(self, db: Session):
        self.db = db
        self.kg_query = KnowledgeGraphQueryService(db)
        self.unified_query = UnifiedQueryInterface(db)

    # ============================================================
    # 网络图数据
    # ============================================================

    def get_network_graph_data(
        self,
        node_ids: Optional[List[str]] = None,
        node_types: Optional[List[str]] = None,
        edge_types: Optional[List[str]] = None,
        center_node_id: Optional[str] = None,
        depth: int = 2,
        limit: int = 100,
        format: str = 'cytoscape'
    ) -> Dict[str, Any]:
        """
        生成网络图数据

        Args:
            node_ids: 指定节点 ID 列表
            node_types: 节点类型过滤
            edge_types: 边类型过滤
            center_node_id: 中心节点 ID（如果提供，返回其邻居网络）
            depth: 邻居深度
            limit: 节点数量限制
            format: 输出格式（cytoscape/d3/echarts）

        Returns:
            网络图数据
        """
        # 获取节点和边
        if center_node_id:
            # 以某个节点为中心的邻居网络
            neighbors_data = self.kg_query.get_neighbors(
                center_node_id,
                depth=depth,
                edge_types=edge_types
            )

            # 添加中心节点
            center_node = self.kg_query.get_node_by_id(center_node_id)
            nodes = [center_node] + neighbors_data['neighbors'] if center_node else neighbors_data['neighbors']
            edges = neighbors_data['edges']

        elif node_ids:
            # 指定节点的子图
            subgraph = self.kg_query.get_subgraph(node_ids, include_edges=True)
            nodes = subgraph['nodes']
            edges = subgraph['edges']

        else:
            # 获取所有节点（带限制）
            nodes = []
            if node_types:
                for node_type in node_types:
                    type_nodes = self.kg_query.get_nodes_by_type(node_type, limit=limit)
                    nodes.extend(type_nodes)
            else:
                # 获取重要节点
                nodes = self.kg_query.get_top_nodes(by='importance', limit=limit)

            # 获取节点间的边
            node_id_set = {n['node_id'] for n in nodes}
            edges = []
            for node in nodes:
                node_edges = self.kg_query.get_node_edges(node['node_id'], direction='out')
                for edge in node_edges['out_edges']:
                    if edge['target_node_id'] in node_id_set:
                        edges.append(edge)

        # 按格式转换
        if format == 'cytoscape':
            return self._to_cytoscape_format(nodes, edges)
        elif format == 'd3':
            return self._to_d3_format(nodes, edges)
        elif format == 'echarts':
            return self._to_echarts_format(nodes, edges)
        else:
            return {
                'nodes': nodes,
                'edges': edges,
                'statistics': {
                    'node_count': len(nodes),
                    'edge_count': len(edges)
                }
            }

    # ============================================================
    # 时间线数据
    # ============================================================

    def get_timeline_data(
        self,
        project_id: Optional[int] = None,
        document_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成时间线数据

        Args:
            project_id: 项目 ID
            document_id: 文档 ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            时间线数据
        """
        from app.models.unified_models import EventUnified

        # 构建查询
        query = self.db.query(EventUnified).filter(
            EventUnified.normalized_time_start.isnot(None)
        )

        if document_id:
            query = query.filter(EventUnified.document_id == document_id)
        elif project_id:
            from app.models.project import ProjectDocument
            doc_ids = self.db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == project_id
            ).all()
            doc_ids = [d[0] for d in doc_ids]
            query = query.filter(EventUnified.document_id.in_(doc_ids))

        if start_time:
            query = query.filter(EventUnified.normalized_time_start >= start_time)
        if end_time:
            query = query.filter(EventUnified.normalized_time_start <= end_time)

        # 按时间排序
        events = query.order_by(EventUnified.normalized_time_start).all()

        # 转换为时间线格式
        timeline_items = []
        for event in events:
            participants = json.loads(event.participants) if event.participants else []

            timeline_items.append({
                'id': event.event_id,
                'time': event.normalized_time_start,
                'title': event.event_name,
                'type': event.event_type,
                'description': event.description,
                'location': event.normalized_location,
                'participants': participants,
                'confidence': event.confidence
            })

        return {
            'timeline': timeline_items,
            'total_events': len(timeline_items),
            'time_range': {
                'start': timeline_items[0]['time'] if timeline_items else None,
                'end': timeline_items[-1]['time'] if timeline_items else None
            }
        }

    # ============================================================
    # 关系矩阵
    # ============================================================

    def get_relationship_matrix(
        self,
        entity_ids: Optional[List[str]] = None,
        document_id: Optional[int] = None,
        top_n: int = 20
    ) -> Dict[str, Any]:
        """
        生成关系矩阵（显示实体间的关系强度）

        Args:
            entity_ids: 实体 ID 列表
            document_id: 文档 ID
            top_n: Top N 个实体

        Returns:
            关系矩阵数据
        """
        from app.models.unified_models import EntityUnified, RelationshipUnified

        # 获取实体列表
        if entity_ids:
            entities = self.db.query(EntityUnified).filter(
                EntityUnified.entity_id.in_(entity_ids)
            ).all()
        elif document_id:
            entities = self.db.query(EntityUnified).filter(
                EntityUnified.document_id == document_id
            ).order_by(EntityUnified.mention_count.desc()).limit(top_n).all()
        else:
            entities = self.db.query(EntityUnified).order_by(
                EntityUnified.mention_count.desc()
            ).limit(top_n).all()

        entity_list = [{'id': e.entity_id, 'name': e.entity_name} for e in entities]
        entity_id_set = {e['id'] for e in entity_list}

        # 构建关系矩阵
        matrix = [[0 for _ in range(len(entity_list))] for _ in range(len(entity_list))]

        # 查询关系
        relationships = self.db.query(RelationshipUnified).filter(
            RelationshipUnified.subject_id.in_(entity_id_set),
            RelationshipUnified.object_id.in_(entity_id_set)
        ).all()

        # 填充矩阵
        entity_index = {e['id']: i for i, e in enumerate(entity_list)}

        for rel in relationships:
            i = entity_index.get(rel.subject_id)
            j = entity_index.get(rel.object_id)
            if i is not None and j is not None:
                matrix[i][j] += 1
                if not rel.is_directed:
                    matrix[j][i] += 1

        return {
            'entities': entity_list,
            'matrix': matrix,
            'total_relationships': len(relationships)
        }

    # ============================================================
    # 树形图数据
    # ============================================================

    def get_tree_data(
        self,
        root_node_id: Optional[str] = None,
        hierarchy_type: str = 'ontology'
    ) -> Dict[str, Any]:
        """
        生成树形图数据

        Args:
            root_node_id: 根节点 ID
            hierarchy_type: 层次类型（ontology/document_structure）

        Returns:
            树形图数据
        """
        if hierarchy_type == 'ontology':
            return self._get_ontology_tree(root_node_id)
        elif hierarchy_type == 'document_structure':
            return self._get_document_structure_tree(root_node_id)
        else:
            return {'error': f'Unknown hierarchy type: {hierarchy_type}'}

    def _get_ontology_tree(self, root_concept_id: Optional[str] = None) -> Dict:
        """获取本体树"""
        from app.models.unified_models import OntologyConcept

        # 获取所有概念
        concepts = self.db.query(OntologyConcept).all()

        if not concepts:
            return {'tree': None, 'total_concepts': 0}

        # 构建树
        concept_dict = {}
        for concept in concepts:
            concept_dict[concept.concept_id] = {
                'id': concept.concept_id,
                'name': concept.concept_name,
                'type': concept.concept_type,
                'level': concept.hierarchy_level,
                'instance_count': concept.instance_count,
                'children': []
            }

        # 建立父子关系
        root_nodes = []
        for concept in concepts:
            node = concept_dict[concept.concept_id]

            if concept.parent_concept_id and concept.parent_concept_id in concept_dict:
                parent = concept_dict[concept.parent_concept_id]
                parent['children'].append(node)
            else:
                root_nodes.append(node)

        return {
            'tree': root_nodes,
            'total_concepts': len(concepts)
        }

    def _get_document_structure_tree(self, document_id: int) -> Dict:
        """获取文档结构树"""
        from app.models.unified_models import DocumentStructure

        nodes = self.db.query(DocumentStructure).filter(
            DocumentStructure.document_id == document_id
        ).order_by(DocumentStructure.sequence_order).all()

        if not nodes:
            return {'tree': None, 'total_nodes': 0}

        # 构建树
        node_dict = {}
        for node in nodes:
            node_dict[node.id] = {
                'id': node.id,
                'type': node.node_type,
                'level': node.node_level,
                'title': node.title,
                'children': []
            }

        # 建立父子关系
        root_nodes = []
        for node in nodes:
            node_data = node_dict[node.id]

            if node.parent_id and node.parent_id in node_dict:
                parent = node_dict[node.parent_id]
                parent['children'].append(node_data)
            else:
                root_nodes.append(node_data)

        return {
            'tree': root_nodes,
            'total_nodes': len(nodes)
        }

    # ============================================================
    # 热力图数据
    # ============================================================

    def get_heatmap_data(
        self,
        metric: str = 'co_occurrence',
        project_id: Optional[int] = None,
        top_n: int = 20
    ) -> Dict[str, Any]:
        """
        生成热力图数据

        Args:
            metric: 度量类型（co_occurrence/correlation）
            project_id: 项目 ID
            top_n: Top N 个实体

        Returns:
            热力图数据
        """
        if metric == 'co_occurrence':
            return self._get_co_occurrence_heatmap(project_id, top_n)
        else:
            return {'error': f'Unknown metric: {metric}'}

    def _get_co_occurrence_heatmap(self, project_id: Optional[int], top_n: int) -> Dict:
        """实体共现热力图"""
        from app.models.unified_models import EntityUnified

        # 获取 Top 实体
        query = self.db.query(EntityUnified)
        if project_id:
            from app.models.project import ProjectDocument
            doc_ids = self.db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == project_id
            ).all()
            doc_ids = [d[0] for d in doc_ids]
            query = query.filter(EntityUnified.document_id.in_(doc_ids))

        entities = query.order_by(EntityUnified.mention_count.desc()).limit(top_n).all()

        entity_list = [{'id': e.entity_id, 'name': e.entity_name} for e in entities]

        # 计算共现矩阵
        matrix = [[0 for _ in range(len(entity_list))] for _ in range(len(entity_list))]

        for i, entity_i in enumerate(entities):
            chunks_i = set(json.loads(entity_i.chunk_ids) if entity_i.chunk_ids else [])

            for j, entity_j in enumerate(entities):
                if i == j:
                    matrix[i][j] = entity_i.mention_count
                else:
                    chunks_j = set(json.loads(entity_j.chunk_ids) if entity_j.chunk_ids else [])
                    co_occurrence = len(chunks_i & chunks_j)
                    matrix[i][j] = co_occurrence

        return {
            'entities': entity_list,
            'matrix': matrix,
            'metric': 'co_occurrence'
        }

    # ============================================================
    # 格式转换
    # ============================================================

    def _to_cytoscape_format(self, nodes: List[Dict], edges: List[Dict]) -> Dict:
        """转换为 Cytoscape.js 格式"""
        elements = []

        # 添加节点
        for node in nodes:
            elements.append({
                'data': {
                    'id': node['node_id'],
                    'label': node['label'],
                    'type': node['node_type'],
                    'degree': node['degree'],
                    'importance': node['importance_score']
                }
            })

        # 添加边
        for edge in edges:
            elements.append({
                'data': {
                    'id': edge['edge_id'],
                    'source': edge['source_node_id'],
                    'target': edge['target_node_id'],
                    'label': edge['edge_label'],
                    'type': edge['edge_type'],
                    'weight': edge['weight']
                }
            })

        return {
            'elements': elements,
            'format': 'cytoscape'
        }

    def _to_d3_format(self, nodes: List[Dict], edges: List[Dict]) -> Dict:
        """转换为 D3.js 格式"""
        # D3 使用 nodes 和 links
        d3_nodes = []
        for node in nodes:
            d3_nodes.append({
                'id': node['node_id'],
                'name': node['label'],
                'type': node['node_type'],
                'value': node['degree'],
                'importance': node['importance_score']
            })

        d3_links = []
        for edge in edges:
            d3_links.append({
                'source': edge['source_node_id'],
                'target': edge['target_node_id'],
                'value': edge['weight'],
                'label': edge['edge_label']
            })

        return {
            'nodes': d3_nodes,
            'links': d3_links,
            'format': 'd3'
        }

    def _to_echarts_format(self, nodes: List[Dict], edges: List[Dict]) -> Dict:
        """转换为 ECharts 格式"""
        echarts_nodes = []
        for node in nodes:
            echarts_nodes.append({
                'id': node['node_id'],
                'name': node['label'],
                'symbolSize': node['degree'] * 2,
                'category': node['node_type'],
                'value': node['importance_score']
            })

        echarts_links = []
        for edge in edges:
            echarts_links.append({
                'source': edge['source_node_id'],
                'target': edge['target_node_id'],
                'value': edge['weight'],
                'label': {
                    'show': True,
                    'formatter': edge['edge_label']
                }
            })

        return {
            'nodes': echarts_nodes,
            'links': echarts_links,
            'format': 'echarts',
            'categories': list(set(n['category'] for n in echarts_nodes))
        }


# ============================================================
# 便捷函数
# ============================================================

def kg_visualization(db: Session) -> KnowledgeGraphVisualizationAPI:
    """
    获取可视化 API 实例

    Args:
        db: 数据库会话

    Returns:
        可视化 API 实例
    """
    return KnowledgeGraphVisualizationAPI(db)
