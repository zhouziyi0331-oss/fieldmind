"""
对比分析服务
比较不同维度的数据、识别差异和相似性、生成对比洞察
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
from .base_analysis import BaseAnalysisService


class ComparisonAnalysisService(BaseAnalysisService):
    """对比分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='comparison')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行对比分析"""
        comparisons = []

        # 对比1: 文档类型分布对比
        doc_type_query = text("""
            SELECT
                doc_type,
                COUNT(*) as count,
                AVG(CAST(json_extract(metadata, '$.word_count') AS INTEGER)) as avg_words
            FROM documents
            WHERE project_id = :project_id
            GROUP BY doc_type
        """)
        doc_types = db_session.execute(doc_type_query, {'project_id': project_id}).fetchall()

        if len(doc_types) > 1:
            doc_type_comparison = []
            for doc_type in doc_types:
                doc_type_comparison.append({
                    'type': doc_type['doc_type'],
                    'count': doc_type['count'],
                    'avg_words': round(doc_type['avg_words'], 0) if doc_type['avg_words'] else 0
                })

            comparisons.append({
                'dimension': 'document_types',
                'items': doc_type_comparison,
                'insight': self._generate_doc_type_insight(doc_type_comparison),
                'variance': self._calculate_variance([item['count'] for item in doc_type_comparison])
            })

        # 对比2: 实体类型规模对比
        entity_type_query = text("""
            SELECT
                entity_type,
                COUNT(*) as count,
                COUNT(DISTINCT source_chunk_id) as source_chunks
            FROM entities
            WHERE project_id = :project_id
            GROUP BY entity_type
            ORDER BY count DESC
        """)
        entity_types = db_session.execute(entity_type_query, {'project_id': project_id}).fetchall()

        if len(entity_types) > 1:
            entity_type_comparison = []
            for entity_type in entity_types[:10]:  # 取前10种类型
                entity_type_comparison.append({
                    'type': entity_type['entity_type'],
                    'count': entity_type['count'],
                    'source_diversity': entity_type['source_chunks']
                })

            comparisons.append({
                'dimension': 'entity_types',
                'items': entity_type_comparison,
                'insight': self._generate_entity_type_insight(entity_type_comparison),
                'variance': self._calculate_variance([item['count'] for item in entity_type_comparison])
            })

        # 对比3: 关系类型分布对比
        relation_type_query = text("""
            SELECT
                relation_type,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM relations
            WHERE project_id = :project_id
            GROUP BY relation_type
            ORDER BY count DESC
        """)
        relation_types = db_session.execute(relation_type_query, {'project_id': project_id}).fetchall()

        if len(relation_types) > 1:
            relation_type_comparison = []
            for relation_type in relation_types[:10]:
                relation_type_comparison.append({
                    'type': relation_type['relation_type'],
                    'count': relation_type['count'],
                    'avg_confidence': round(relation_type['avg_confidence'], 2) if relation_type['avg_confidence'] else 0
                })

            comparisons.append({
                'dimension': 'relation_types',
                'items': relation_type_comparison,
                'insight': self._generate_relation_type_insight(relation_type_comparison),
                'variance': self._calculate_variance([item['count'] for item in relation_type_comparison])
            })

        # 对比4: 知识节点类型对比
        knowledge_type_query = text("""
            SELECT
                node_type,
                COUNT(*) as count,
                AVG(confidence_score) as avg_confidence
            FROM knowledge_nodes
            WHERE project_id = :project_id
            GROUP BY node_type
        """)
        knowledge_types = db_session.execute(knowledge_type_query, {'project_id': project_id}).fetchall()

        if len(knowledge_types) > 1:
            knowledge_type_comparison = []
            for knowledge_type in knowledge_types:
                knowledge_type_comparison.append({
                    'type': knowledge_type['node_type'],
                    'count': knowledge_type['count'],
                    'avg_confidence': round(knowledge_type['avg_confidence'], 2) if knowledge_type['avg_confidence'] else 0
                })

            comparisons.append({
                'dimension': 'knowledge_node_types',
                'items': knowledge_type_comparison,
                'insight': self._generate_knowledge_type_insight(knowledge_type_comparison),
                'variance': self._calculate_variance([item['count'] for item in knowledge_type_comparison])
            })

        # 对比5: Chunk类型质量对比
        chunk_type_query = text("""
            SELECT
                chunk_type,
                COUNT(*) as count,
                AVG(LENGTH(content)) as avg_length,
                COUNT(DISTINCT document_id) as doc_spread
            FROM chunks
            WHERE project_id = :project_id
            GROUP BY chunk_type
        """)
        chunk_types = db_session.execute(chunk_type_query, {'project_id': project_id}).fetchall()

        if len(chunk_types) > 1:
            chunk_type_comparison = []
            for chunk_type in chunk_types:
                chunk_type_comparison.append({
                    'type': chunk_type['chunk_type'],
                    'count': chunk_type['count'],
                    'avg_length': round(chunk_type['avg_length'], 0) if chunk_type['avg_length'] else 0,
                    'document_spread': chunk_type['doc_spread']
                })

            comparisons.append({
                'dimension': 'chunk_types',
                'items': chunk_type_comparison,
                'insight': self._generate_chunk_type_insight(chunk_type_comparison),
                'variance': self._calculate_variance([item['count'] for item in chunk_type_comparison])
            })

        # 对比6: 数据层次深度对比（文档->chunks->实体->关系->知识）
        layer_stats_query = text("""
            SELECT
                (SELECT COUNT(*) FROM documents WHERE project_id = :project_id) as documents,
                (SELECT COUNT(*) FROM chunks WHERE project_id = :project_id) as chunks,
                (SELECT COUNT(*) FROM entities WHERE project_id = :project_id) as entities,
                (SELECT COUNT(*) FROM relations WHERE project_id = :project_id) as relations,
                (SELECT COUNT(*) FROM knowledge_nodes WHERE project_id = :project_id) as knowledge_nodes
        """)
        layer_stats = db_session.execute(layer_stats_query, {'project_id': project_id}).fetchone()

        layer_comparison = [
            {'layer': 'documents', 'count': layer_stats['documents'], 'level': 1},
            {'layer': 'chunks', 'count': layer_stats['chunks'], 'level': 2},
            {'layer': 'entities', 'count': layer_stats['entities'], 'level': 3},
            {'layer': 'relations', 'count': layer_stats['relations'], 'level': 4},
            {'layer': 'knowledge_nodes', 'count': layer_stats['knowledge_nodes'], 'level': 5}
        ]

        comparisons.append({
            'dimension': 'data_layers',
            'items': layer_comparison,
            'insight': self._generate_layer_insight(layer_comparison),
            'processing_depth': self._calculate_processing_depth(layer_comparison)
        })

        # 计算整体对比指标
        total_dimensions = len(comparisons)
        avg_variance = sum(c.get('variance', 0) for c in comparisons) / total_dimensions if total_dimensions > 0 else 0

        return {
            'total_comparisons': total_dimensions,
            'comparisons': comparisons,
            'average_variance': round(avg_variance, 2),
            'has_diverse_data': avg_variance > 0.3,
            'confidence_score': 0.86
        }

    def _calculate_variance(self, values: List[int]) -> float:
        """计算方差（归一化）"""
        if not values or len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        if mean == 0:
            return 0.0

        variance = sum((x - mean) ** 2 for x in values) / len(values)
        # 归一化：变异系数（标准差/均值）
        cv = (variance ** 0.5) / mean if mean > 0 else 0
        return round(cv, 2)

    def _generate_doc_type_insight(self, items: List[Dict]) -> str:
        """生成文档类型对比洞察"""
        if not items:
            return "无文档类型数据"

        max_item = max(items, key=lambda x: x['count'])
        total = sum(item['count'] for item in items)
        dominance = (max_item['count'] / total * 100) if total > 0 else 0

        return f"{max_item['type']}类型文档占主导({dominance:.1f}%)，共{len(items)}种文档类型"

    def _generate_entity_type_insight(self, items: List[Dict]) -> str:
        """生成实体类型对比洞察"""
        if not items:
            return "无实体类型数据"

        max_item = max(items, key=lambda x: x['count'])
        total = sum(item['count'] for item in items)
        dominance = (max_item['count'] / total * 100) if total > 0 else 0

        return f"{max_item['type']}是最主要实体类型({dominance:.1f}%)，共识别{len(items)}种类型"

    def _generate_relation_type_insight(self, items: List[Dict]) -> str:
        """生成关系类型对比洞察"""
        if not items:
            return "无关系类型数据"

        max_item = max(items, key=lambda x: x['count'])
        avg_confidence = sum(item['avg_confidence'] for item in items) / len(items)

        return f"{max_item['type']}关系最常见，平均置信度{avg_confidence:.2f}"

    def _generate_knowledge_type_insight(self, items: List[Dict]) -> str:
        """生成知识节点类型对比洞察"""
        if not items:
            return "无知识节点数据"

        max_item = max(items, key=lambda x: x['count'])
        high_confidence_types = sum(1 for item in items if item['avg_confidence'] > 0.8)

        return f"{max_item['type']}类知识节点最多，{high_confidence_types}种类型高置信度(>0.8)"

    def _generate_chunk_type_insight(self, items: List[Dict]) -> str:
        """生成chunk类型对比洞察"""
        if not items:
            return "无chunk类型数据"

        max_item = max(items, key=lambda x: x['count'])
        avg_length = sum(item['avg_length'] for item in items) / len(items)

        return f"{max_item['type']}类型chunks最多，平均长度{avg_length:.0f}字符"

    def _generate_layer_insight(self, items: List[Dict]) -> str:
        """生成数据层次对比洞察"""
        if not items:
            return "无数据层次信息"

        docs = next((item['count'] for item in items if item['layer'] == 'documents'), 0)
        knowledge = next((item['count'] for item in items if item['layer'] == 'knowledge_nodes'), 0)

        if docs > 0:
            knowledge_ratio = knowledge / docs
            return f"从{docs}个文档提取出{knowledge}个知识节点，提炼比{knowledge_ratio:.2f}"
        else:
            return "数据层次未完整建立"

    def _calculate_processing_depth(self, items: List[Dict]) -> int:
        """计算数据处理深度（有数据的最深层级）"""
        max_depth = 0
        for item in items:
            if item['count'] > 0:
                max_depth = max(max_depth, item['level'])
        return max_depth
