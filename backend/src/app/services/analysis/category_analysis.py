"""
分类分析服务
分析文档和数据的分类分布、识别主要类别、构建分类层次
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from collections import Counter
import json
from .base_analysis import BaseAnalysisService


class CategoryAnalysisService(BaseAnalysisService):
    """分类分析服务"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        super().__init__(analysis_type='category')

    async def analyze(
        self,
        project_id: str,
        db_session: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """执行分类分析"""
        # 从documents表获取文档类型和元数据
        doc_query = text("""
            SELECT id, doc_type, metadata
            FROM documents
            WHERE project_id = :project_id
        """)
        doc_result = db_session.execute(doc_query, {'project_id': project_id})
        documents = [dict(row._mapping) for row in doc_result.fetchall()]

        # 从chunks表获取chunk的分类信息
        chunk_query = text("""
            SELECT chunk_type, metadata
            FROM chunks
            WHERE project_id = :project_id
        """)
        chunk_result = db_session.execute(chunk_query, {'project_id': project_id})
        chunks = [dict(row._mapping) for row in chunk_result.fetchall()]

        # 统计文档类型分布
        doc_types = Counter(doc.get('doc_type', 'unknown') for doc in documents)

        # 统计chunk类型分布
        chunk_types = Counter(chunk.get('chunk_type', 'text') for chunk in chunks)

        # 从metadata中提取分类标签
        categories = []
        for doc in documents:
            metadata = doc.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            if 'category' in metadata:
                categories.append(metadata['category'])
            if 'tags' in metadata and isinstance(metadata['tags'], list):
                categories.extend(metadata['tags'])

        category_distribution = Counter(categories)

        # 识别主要分类（出现次数最多的前5个）
        main_categories = [
            {'category': cat, 'count': count}
            for cat, count in category_distribution.most_common(5)
        ]

        # 计算分类覆盖率
        total_docs = len(documents)
        categorized_docs = sum(1 for doc in documents if self._has_category(doc))
        coverage_rate = categorized_docs / total_docs if total_docs > 0 else 0

        return {
            'total_documents': total_docs,
            'total_chunks': len(chunks),
            'doc_type_distribution': dict(doc_types),
            'chunk_type_distribution': dict(chunk_types),
            'category_distribution': dict(category_distribution),
            'main_categories': main_categories,
            'coverage_rate': coverage_rate,
            'total_unique_categories': len(category_distribution),
            'confidence_score': 0.88
        }

    def _has_category(self, doc: Dict[str, Any]) -> bool:
        """检查文档是否有分类信息"""
        metadata = doc.get('metadata', {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                return False
        return 'category' in metadata or 'tags' in metadata
