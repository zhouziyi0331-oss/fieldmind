"""
缩影查询服务
Summary Query Service

功能：
1. 查询文档缩影
2. 查询项目缩影列表
3. 搜索缩影
4. 获取缩影关联数据（知识图谱、Wiki、本体）
5. 缩影统计分析
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_
import logging
from typing import List, Dict, Any, Optional
import json

from app.models.project import FileSummary, ProjectDocument
from app.models.unified_models import KnowledgeGraphNode, WikiPage
from app.services.knowledge_graph.kg_query_service import KnowledgeGraphQueryService

logger = logging.getLogger(__name__)


class SummaryQueryService:
    """缩影查询服务"""

    def __init__(self, db: Session):
        self.db = db
        self.kg_query = KnowledgeGraphQueryService(db)

    # ============================================================
    # 基本查询
    # ============================================================

    def get_summary_by_document(self, document_id: int) -> Optional[Dict]:
        """
        根据文档 ID 获取缩影

        Args:
            document_id: 文档 ID

        Returns:
            缩影信息
        """
        summary = self.db.query(FileSummary).filter(
            FileSummary.document_id == document_id
        ).first()

        if not summary:
            return None

        return self._summary_to_dict(summary)

    def get_summaries_by_project(
        self,
        project_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取项目的所有缩影

        Args:
            project_id: 项目 ID
            limit: 返回数量
            offset: 偏移量

        Returns:
            缩影列表
        """
        query = self.db.query(FileSummary).filter(
            FileSummary.project_id == project_id
        ).order_by(FileSummary.created_at.desc())

        total = query.count()
        summaries = query.limit(limit).offset(offset).all()

        return {
            'total': total,
            'limit': limit,
            'offset': offset,
            'summaries': [self._summary_to_dict(s) for s in summaries]
        }

    def search_summaries(
        self,
        query: str,
        project_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        搜索缩影

        Args:
            query: 搜索关键词
            project_id: 项目 ID（可选）
            limit: 返回数量

        Returns:
            缩影列表
        """
        q = self.db.query(FileSummary).filter(
            or_(
                FileSummary.one_sentence_summary.like(f'%{query}%'),
                FileSummary.full_summary.like(f'%{query}%')
            )
        )

        if project_id:
            q = q.filter(FileSummary.project_id == project_id)

        summaries = q.order_by(FileSummary.created_at.desc()).limit(limit).all()

        return [self._summary_to_dict(s) for s in summaries]

    # ============================================================
    # 关联数据查询
    # ============================================================

    def get_summary_with_associations(self, document_id: int) -> Dict[str, Any]:
        """
        获取缩影及其所有关联数据

        Args:
            document_id: 文档 ID

        Returns:
            缩影及关联数据
        """
        summary = self.get_summary_by_document(document_id)

        if not summary:
            return {'error': 'Summary not found'}

        # 获取文档信息
        document = self.db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        # 获取知识图谱节点
        kg_node = None
        kg_neighbors = None
        if summary.get('knowledge_graph_node_id'):
            kg_node = self.kg_query.get_node_by_id(summary['knowledge_graph_node_id'])
            if kg_node:
                kg_neighbors = self.kg_query.get_direct_neighbors(kg_node['node_id'])

        # 获取 Wiki 页面
        wiki_page = None
        if summary.get('wiki_page_id'):
            wiki_page = self.db.query(WikiPage).filter(
                WikiPage.page_id == summary['wiki_page_id']
            ).first()

        # 获取知识单元
        knowledge_units = json.loads(summary.get('knowledge_units', '[]'))

        # 获取本体标签
        ontology_tags = json.loads(summary.get('ontology_tags', '[]'))

        return {
            'summary': summary,
            'document': {
                'id': document.id,
                'filename': document.original_filename,
                'status': document.status
            } if document else None,
            'knowledge_graph': {
                'node': kg_node,
                'neighbors': kg_neighbors
            },
            'wiki_page': {
                'page_id': wiki_page.page_id,
                'title': wiki_page.page_title,
                'type': wiki_page.page_type
            } if wiki_page else None,
            'knowledge_units': knowledge_units,
            'ontology_tags': ontology_tags,
            'statistics': {
                'inference_count': summary.get('inference_count', 0),
                'relationships_count': summary.get('relationships_count', 0)
            }
        }

    # ============================================================
    # 统计分析
    # ============================================================

    def get_project_summary_statistics(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目缩影统计

        Args:
            project_id: 项目 ID

        Returns:
            统计信息
        """
        # 总数
        total_summaries = self.db.query(func.count(FileSummary.id)).filter(
            FileSummary.project_id == project_id
        ).scalar()

        # 有知识图谱关联的数量
        with_kg = self.db.query(func.count(FileSummary.id)).filter(
            FileSummary.project_id == project_id,
            FileSummary.knowledge_graph_node_id.isnot(None)
        ).scalar()

        # 有 Wiki 关联的数量
        with_wiki = self.db.query(func.count(FileSummary.id)).filter(
            FileSummary.project_id == project_id,
            FileSummary.wiki_page_id.isnot(None)
        ).scalar()

        # 平均推理数量
        avg_inferences = self.db.query(func.avg(FileSummary.inference_count)).filter(
            FileSummary.project_id == project_id
        ).scalar()

        # 平均关系数量
        avg_relationships = self.db.query(func.avg(FileSummary.relationships_count)).filter(
            FileSummary.project_id == project_id
        ).scalar()

        # 本体标签统计
        summaries = self.db.query(FileSummary).filter(
            FileSummary.project_id == project_id,
            FileSummary.ontology_tags.isnot(None)
        ).all()

        tag_counts = {}
        for summary in summaries:
            tags = json.loads(summary.ontology_tags) if summary.ontology_tags else []
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        return {
            'total_summaries': total_summaries,
            'with_knowledge_graph': with_kg,
            'with_wiki': with_wiki,
            'knowledge_graph_coverage': round(with_kg / total_summaries * 100, 2) if total_summaries > 0 else 0,
            'wiki_coverage': round(with_wiki / total_summaries * 100, 2) if total_summaries > 0 else 0,
            'avg_inferences': round(float(avg_inferences or 0), 2),
            'avg_relationships': round(float(avg_relationships or 0), 2),
            'ontology_tag_distribution': tag_counts
        }

    def get_top_summaries(
        self,
        project_id: int,
        by: str = 'inferences',
        limit: int = 10
    ) -> List[Dict]:
        """
        获取 Top 缩影

        Args:
            project_id: 项目 ID
            by: 排序依据（inferences/relationships）
            limit: 返回数量

        Returns:
            Top 缩影列表
        """
        query = self.db.query(FileSummary).filter(
            FileSummary.project_id == project_id
        )

        if by == 'inferences':
            query = query.order_by(FileSummary.inference_count.desc())
        elif by == 'relationships':
            query = query.order_by(FileSummary.relationships_count.desc())
        else:
            query = query.order_by(FileSummary.created_at.desc())

        summaries = query.limit(limit).all()

        return [self._summary_to_dict(s) for s in summaries]

    # ============================================================
    # 对比分析
    # ============================================================

    def compare_summaries(self, document_ids: List[int]) -> Dict[str, Any]:
        """
        对比多个文档的缩影

        Args:
            document_ids: 文档 ID 列表

        Returns:
            对比结果
        """
        summaries = self.db.query(FileSummary).filter(
            FileSummary.document_id.in_(document_ids)
        ).all()

        if not summaries:
            return {'error': 'No summaries found'}

        comparison = []
        for summary in summaries:
            comparison.append({
                'document_id': summary.document_id,
                'one_sentence': summary.one_sentence_summary,
                'inference_count': summary.inference_count or 0,
                'relationships_count': summary.relationships_count or 0,
                'has_kg': summary.knowledge_graph_node_id is not None,
                'has_wiki': summary.wiki_page_id is not None,
                'ontology_tags': json.loads(summary.ontology_tags) if summary.ontology_tags else []
            })

        # 计算共同标签
        all_tags = []
        for item in comparison:
            all_tags.extend(item['ontology_tags'])

        from collections import Counter
        tag_counts = Counter(all_tags)
        common_tags = [tag for tag, count in tag_counts.items() if count >= len(summaries) / 2]

        return {
            'comparison': comparison,
            'common_ontology_tags': common_tags,
            'total_compared': len(summaries)
        }

    # ============================================================
    # 辅助方法
    # ============================================================

    def _summary_to_dict(self, summary: FileSummary) -> Dict:
        """将缩影对象转换为字典"""
        return {
            'id': summary.id,
            'project_id': summary.project_id,
            'document_id': summary.document_id,
            'one_sentence_summary': summary.one_sentence_summary,
            'full_summary': summary.full_summary,
            'knowledge_graph_node_id': summary.knowledge_graph_node_id,
            'knowledge_units': summary.knowledge_units,
            'wiki_page_id': summary.wiki_page_id,
            'ontology_tags': summary.ontology_tags,
            'inference_count': summary.inference_count,
            'relationships_count': summary.relationships_count,
            'created_at': summary.created_at.isoformat() if summary.created_at else None,
            'updated_at': summary.updated_at.isoformat() if summary.updated_at else None
        }


# ============================================================
# 便捷函数
# ============================================================

def query_summary(db: Session) -> SummaryQueryService:
    """
    获取缩影查询服务实例

    Args:
        db: 数据库会话

    Returns:
        查询服务实例
    """
    return SummaryQueryService(db)
