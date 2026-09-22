"""
关键词分析服务
提取关键词、计算词频、识别核心概念
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import Counter
import json
import re
from .base_analysis import BaseAnalysisService


class KeywordAnalysisService(BaseAnalysisService):
    """关键词分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='keyword')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行关键词分析"""
        # 从entities表获取实体作为关键词
        entity_query = text("""
            SELECT entity_name, entity_type, properties
            FROM entities
            WHERE project_id = :project_id
        """)
        entity_result = db_session.execute(entity_query, {'project_id': project_id})
        entities = [dict(row._mapping) for row in entity_result.fetchall()]

        # 统计实体名称频率（作为关键词）
        entity_names = [e['entity_name'] for e in entities]
        keyword_frequency = Counter(entity_names)

        # 按实体类型分组关键词
        keywords_by_type = {}
        for entity in entities:
            etype = entity.get('entity_type', 'unknown')
            name = entity.get('entity_name')
            if etype not in keywords_by_type:
                keywords_by_type[etype] = []
            if name not in keywords_by_type[etype]:
                keywords_by_type[etype].append(name)

        # 从knowledge_nodes获取核心概念
        knowledge_query = text("""
            SELECT node_type, content, properties
            FROM knowledge_nodes
            WHERE project_id = :project_id
        """)
        knowledge_result = db_session.execute(knowledge_query, {'project_id': project_id})
        knowledge_nodes = [dict(row._mapping) for row in knowledge_result.fetchall()]

        # 提取知识节点中的核心概念
        core_concepts = []
        for node in knowledge_nodes:
            content = node.get('content', '')
            properties = node.get('properties', {})
            if isinstance(properties, str):
                try:
                    properties = json.loads(properties)
                except:
                    properties = {}

            # 从properties中提取关键词
            if 'keywords' in properties and isinstance(properties['keywords'], list):
                core_concepts.extend(properties['keywords'])

            # 从content中提取短语（简单方法：提取2-4个词的组合）
            if content:
                # 提取可能的核心概念（标题化的词组）
                phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b', content)
                core_concepts.extend(phrases)

        core_concept_frequency = Counter(core_concepts)

        # 获取文档标题和描述中的关键词
        doc_query = text("""
            SELECT metadata
            FROM documents
            WHERE project_id = :project_id
        """)
        doc_result = db_session.execute(doc_query, {'project_id': project_id})
        documents = [dict(row._mapping) for row in doc_result.fetchall()]

        doc_keywords = []
        for doc in documents:
            metadata = doc.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}

            if 'keywords' in metadata and isinstance(metadata['keywords'], list):
                doc_keywords.extend(metadata['keywords'])
            if 'tags' in metadata and isinstance(metadata['tags'], list):
                doc_keywords.extend(metadata['tags'])

        doc_keyword_frequency = Counter(doc_keywords)

        # 合并所有关键词源，计算综合权重
        all_keywords = {}

        # 实体关键词（权重1.0）
        for keyword, count in keyword_frequency.most_common(50):
            all_keywords[keyword] = all_keywords.get(keyword, 0) + count * 1.0

        # 核心概念（权重1.5，更重要）
        for concept, count in core_concept_frequency.most_common(30):
            all_keywords[concept] = all_keywords.get(concept, 0) + count * 1.5

        # 文档关键词（权重1.2）
        for keyword, count in doc_keyword_frequency.most_common(30):
            all_keywords[keyword] = all_keywords.get(keyword, 0) + count * 1.2

        # 排序并取前30个
        top_keywords = sorted(
            [{'keyword': k, 'score': round(v, 2)} for k, v in all_keywords.items()],
            key=lambda x: x['score'],
            reverse=True
        )[:30]

        return {
            'total_unique_keywords': len(all_keywords),
            'top_keywords': top_keywords,
            'keywords_by_entity_type': {
                k: v[:10] for k, v in keywords_by_type.items()
            },
            'entity_based_keywords': len(entity_names),
            'concept_based_keywords': len(core_concepts),
            'document_based_keywords': len(doc_keywords),
            'keyword_sources': {
                'entities': len(set(entity_names)),
                'concepts': len(set(core_concepts)),
                'documents': len(set(doc_keywords))
            },
            'confidence_score': 0.87
        }
