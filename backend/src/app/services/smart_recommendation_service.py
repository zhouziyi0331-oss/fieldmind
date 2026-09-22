"""
智能推荐搜索服务
整合多种推荐策略：基于内容、协同过滤、网络分析
支持报告推荐、关键词推荐、文档推荐
"""

import logging
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from collections import defaultdict, Counter
from datetime import datetime, timedelta

from app.models.document import Document
from app.models.report import Report
from app.models.keyword import Keyword, KeywordRelation
from app.models.report_relation import ReportRelation, ReportEntity
from app.services.correlation_recommender import CorrelationRecommender

logger = logging.getLogger(__name__)


class SmartRecommendationService:
    """智能推荐服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.correlation_recommender = CorrelationRecommender(db)

    # ==================== 报告推荐 ====================

    def recommend_reports(
        self,
        report_id: str,
        project_id: int,
        strategy: str = "hybrid",
        top_n: int = 5,
        exclude_ids: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        推荐相关报告

        策略：
        - relation_based: 基于报告关系网络
        - entity_based: 基于共享实体
        - keyword_based: 基于关键词相似度
        - hybrid: 混合策略（推荐）

        Returns:
            [
                {
                    "report_id": "...",
                    "title": "...",
                    "score": 0.85,
                    "reason": "共享 5 个实体",
                    "strategy": "entity_based"
                }
            ]
        """
        if exclude_ids is None:
            exclude_ids = set()
        exclude_ids.add(report_id)

        logger.info(f"推荐报告: report_id={report_id}, strategy={strategy}")

        if strategy == "relation_based":
            candidates = self._recommend_by_relations(report_id, project_id, top_n * 2)
        elif strategy == "entity_based":
            candidates = self._recommend_by_entities(report_id, project_id, top_n * 2)
        elif strategy == "keyword_based":
            candidates = self._recommend_by_keywords(report_id, project_id, top_n * 2)
        elif strategy == "hybrid":
            # 混合策略：综合多种方法
            candidates = self._hybrid_report_recommendation(report_id, project_id, top_n * 3)
        else:
            raise ValueError(f"未知策略: {strategy}")

        # 过滤已排除的报告
        candidates = [c for c in candidates if c['report_id'] not in exclude_ids]

        # 按分数排序并返回 top N
        candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
        return candidates[:top_n]

    def _recommend_by_relations(
        self,
        report_id: str,
        project_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """基于报告关系网络推荐"""
        # 获取直接关联的报告
        relations = self.db.query(ReportRelation).filter(
            or_(
                ReportRelation.source_report_id == report_id,
                ReportRelation.target_report_id == report_id
            )
        ).all()

        candidates = []
        for rel in relations:
            related_id = rel.target_report_id if rel.source_report_id == report_id else rel.source_report_id

            # 获取报告信息
            report = self.db.query(Report).filter(Report.id == related_id).first()
            if not report:
                continue

            candidates.append({
                "report_id": related_id,
                "title": report.title,
                "score": rel.strength,
                "reason": f"关系类型: {rel.relation_type.value}",
                "strategy": "relation_based",
                "relation_type": rel.relation_type.value
            })

        return candidates

    def _recommend_by_entities(
        self,
        report_id: str,
        project_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """基于共享实体推荐"""
        # 获取当前报告的实体
        current_entities = self.db.query(ReportEntity).filter(
            ReportEntity.report_id == report_id
        ).all()

        if not current_entities:
            return []

        entity_names = [e.name for e in current_entities]

        # 查找包含相同实体的其他报告
        other_reports_entities = self.db.query(
            ReportEntity.report_id,
            func.count(ReportEntity.id).label('shared_count')
        ).filter(
            and_(
                ReportEntity.report_id != report_id,
                ReportEntity.name.in_(entity_names)
            )
        ).group_by(ReportEntity.report_id)\
         .order_by(desc('shared_count'))\
         .limit(limit).all()

        candidates = []
        for related_id, shared_count in other_reports_entities:
            report = self.db.query(Report).filter(Report.id == related_id).first()
            if not report:
                continue

            # 计算 Jaccard 相似度
            related_entities = self.db.query(ReportEntity).filter(
                ReportEntity.report_id == related_id
            ).all()
            related_entity_names = set(e.name for e in related_entities)
            current_entity_names = set(entity_names)

            intersection = len(current_entity_names & related_entity_names)
            union = len(current_entity_names | related_entity_names)
            jaccard_score = intersection / union if union > 0 else 0

            candidates.append({
                "report_id": related_id,
                "title": report.title,
                "score": jaccard_score,
                "reason": f"共享 {shared_count} 个实体",
                "strategy": "entity_based",
                "shared_entities_count": shared_count
            })

        return candidates

    def _recommend_by_keywords(
        self,
        report_id: str,
        project_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """基于关键词相似度推荐"""
        # 获取当前报告的关键词（通过文档）
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if not report or not report.document_ids:
            return []

        from app.models.keyword import DocumentKeyword

        # 获取报告所有文档的关键词
        current_keywords = self.db.query(DocumentKeyword.keyword_id)\
            .filter(DocumentKeyword.document_id.in_(report.document_ids))\
            .distinct().all()

        if not current_keywords:
            return []

        current_keyword_ids = [kw[0] for kw in current_keywords]

        # 查找有相似关键词的其他报告
        other_reports = self.db.query(Report).filter(
            and_(
                Report.id != report_id,
                Report.project_id == project_id,
                Report.document_ids.isnot(None)
            )
        ).limit(50).all()  # 限制候选数量

        candidates = []
        for other_report in other_reports:
            if not other_report.document_ids:
                continue

            # 获取其他报告的关键词
            other_keywords = self.db.query(DocumentKeyword.keyword_id)\
                .filter(DocumentKeyword.document_id.in_(other_report.document_ids))\
                .distinct().all()

            other_keyword_ids = set(kw[0] for kw in other_keywords)
            current_keyword_set = set(current_keyword_ids)

            # 计算关键词重叠度
            intersection = len(current_keyword_set & other_keyword_ids)
            union = len(current_keyword_set | other_keyword_ids)

            if union == 0:
                continue

            jaccard_score = intersection / union

            if jaccard_score > 0:
                candidates.append({
                    "report_id": other_report.id,
                    "title": other_report.title,
                    "score": jaccard_score,
                    "reason": f"关键词相似度: {jaccard_score:.2%}",
                    "strategy": "keyword_based",
                    "shared_keywords_count": intersection
                })

        return candidates

    def _hybrid_report_recommendation(
        self,
        report_id: str,
        project_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """混合推荐策略"""
        # 获取各策略的候选
        relation_candidates = self._recommend_by_relations(report_id, project_id, limit)
        entity_candidates = self._recommend_by_entities(report_id, project_id, limit)
        keyword_candidates = self._recommend_by_keywords(report_id, project_id, limit)

        # 合并并加权
        all_candidates = {}

        # 关系推荐权重 0.4
        for candidate in relation_candidates:
            rid = candidate['report_id']
            if rid not in all_candidates:
                all_candidates[rid] = candidate.copy()
                all_candidates[rid]['score'] = candidate['score'] * 0.4
                all_candidates[rid]['strategies'] = ['relation_based']
            else:
                all_candidates[rid]['score'] += candidate['score'] * 0.4
                all_candidates[rid]['strategies'].append('relation_based')

        # 实体推荐权重 0.35
        for candidate in entity_candidates:
            rid = candidate['report_id']
            if rid not in all_candidates:
                all_candidates[rid] = candidate.copy()
                all_candidates[rid]['score'] = candidate['score'] * 0.35
                all_candidates[rid]['strategies'] = ['entity_based']
            else:
                all_candidates[rid]['score'] += candidate['score'] * 0.35
                all_candidates[rid]['strategies'].append('entity_based')

        # 关键词推荐权重 0.25
        for candidate in keyword_candidates:
            rid = candidate['report_id']
            if rid not in all_candidates:
                all_candidates[rid] = candidate.copy()
                all_candidates[rid]['score'] = candidate['score'] * 0.25
                all_candidates[rid]['strategies'] = ['keyword_based']
            else:
                all_candidates[rid]['score'] += candidate['score'] * 0.25
                all_candidates[rid]['strategies'].append('keyword_based')

        # 转换为列表并标记策略
        result = []
        for rid, candidate in all_candidates.items():
            candidate['strategy'] = 'hybrid'
            candidate['reason'] = f"混合推荐 ({', '.join(candidate['strategies'])})"
            result.append(candidate)

        return result

    # ==================== 关键词推荐 ====================

    def recommend_keywords(
        self,
        keyword_id: int,
        project_id: int,
        strategy: str = "network",
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        推荐相关关键词

        策略：
        - network: 基于关键词网络（共现关系）
        - context: 基于上下文相似度
        - semantic: 基于语义相似度（需要词向量）
        """
        logger.info(f"推荐关键词: keyword_id={keyword_id}, strategy={strategy}")

        if strategy == "network":
            return self._recommend_keywords_by_network(keyword_id, project_id, top_n)
        elif strategy == "context":
            return self._recommend_keywords_by_context(keyword_id, project_id, top_n)
        else:
            raise ValueError(f"未知策略: {strategy}")

    def _recommend_keywords_by_network(
        self,
        keyword_id: int,
        project_id: int,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """基于关键词网络推荐"""
        # 获取直接关联的关键词
        relations = self.db.query(KeywordRelation).filter(
            and_(
                KeywordRelation.project_id == project_id,
                or_(
                    KeywordRelation.keyword1_id == keyword_id,
                    KeywordRelation.keyword2_id == keyword_id
                )
            )
        ).order_by(desc(KeywordRelation.strength)).limit(top_n * 2).all()

        candidates = []
        for rel in relations:
            related_id = rel.keyword2_id if rel.keyword1_id == keyword_id else rel.keyword1_id

            # 获取关键词信息
            keyword = self.db.query(Keyword).filter(Keyword.id == related_id).first()
            if not keyword:
                continue

            candidates.append({
                "keyword_id": related_id,
                "text": keyword.text,
                "category": keyword.category,
                "score": rel.strength,
                "reason": f"共现 {rel.co_occurrence} 次",
                "co_occurrence": rel.co_occurrence,
                "relation_strength": rel.strength
            })

        # 按分数排序
        candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
        return candidates[:top_n]

    def _recommend_keywords_by_context(
        self,
        keyword_id: int,
        project_id: int,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """基于上下文推荐（同一分类的高频关键词）"""
        # 获取当前关键词
        current_kw = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not current_kw:
            return []

        # 获取相同分类的其他高频关键词
        similar_keywords = self.db.query(Keyword).filter(
            and_(
                Keyword.project_id == project_id,
                Keyword.category == current_kw.category,
                Keyword.id != keyword_id
            )
        ).order_by(desc(Keyword.frequency)).limit(top_n).all()

        candidates = []
        for kw in similar_keywords:
            # 简单的频率归一化分数
            score = min(kw.frequency / (current_kw.frequency + 1), 1.0)

            candidates.append({
                "keyword_id": kw.id,
                "text": kw.text,
                "category": kw.category,
                "score": score,
                "reason": f"相同分类，频率 {kw.frequency}",
                "frequency": kw.frequency
            })

        return candidates

    # ==================== 文档推荐 ====================

    def recommend_documents(
        self,
        document_id: int,
        project_id: int,
        strategy: str = "keyword",
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        推荐相关文档

        策略：
        - keyword: 基于关键词相似度
        - entity: 基于实体共现
        - temporal: 基于时间相近性
        """
        logger.info(f"推荐文档: document_id={document_id}, strategy={strategy}")

        if strategy == "keyword":
            return self._recommend_documents_by_keywords(document_id, project_id, top_n)
        elif strategy == "temporal":
            return self._recommend_documents_by_time(document_id, project_id, top_n)
        else:
            raise ValueError(f"未知策略: {strategy}")

    def _recommend_documents_by_keywords(
        self,
        document_id: int,
        project_id: int,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """基于关键词相似度推荐文档"""
        from app.models.keyword import DocumentKeyword

        # 获取当前文档的关键词
        current_keywords = self.db.query(DocumentKeyword.keyword_id).filter(
            DocumentKeyword.document_id == document_id
        ).all()

        if not current_keywords:
            return []

        current_keyword_ids = set(kw[0] for kw in current_keywords)

        # 查找有相似关键词的其他文档
        other_docs_keywords = self.db.query(
            DocumentKeyword.document_id,
            func.count(DocumentKeyword.keyword_id).label('shared_count')
        ).filter(
            and_(
                DocumentKeyword.document_id != document_id,
                DocumentKeyword.keyword_id.in_(current_keyword_ids)
            )
        ).group_by(DocumentKeyword.document_id)\
         .order_by(desc('shared_count'))\
         .limit(top_n * 2).all()

        candidates = []
        for doc_id, shared_count in other_docs_keywords:
            doc = self.db.query(Document).filter(Document.id == doc_id).first()
            if not doc or doc.project_id != project_id:
                continue

            # 计算相似度
            other_keywords = self.db.query(DocumentKeyword.keyword_id).filter(
                DocumentKeyword.document_id == doc_id
            ).all()
            other_keyword_ids = set(kw[0] for kw in other_keywords)

            intersection = len(current_keyword_ids & other_keyword_ids)
            union = len(current_keyword_ids | other_keyword_ids)
            similarity = intersection / union if union > 0 else 0

            candidates.append({
                "document_id": doc_id,
                "title": doc.title or doc.file_name,
                "score": similarity,
                "reason": f"共享 {shared_count} 个关键词",
                "shared_keywords": shared_count
            })

        return sorted(candidates, key=lambda x: x['score'], reverse=True)[:top_n]

    def _recommend_documents_by_time(
        self,
        document_id: int,
        project_id: int,
        top_n: int
    ) -> List[Dict[str, Any]]:
        """基于时间相近性推荐文档"""
        # 获取当前文档
        current_doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not current_doc or not current_doc.created_at:
            return []

        # 查找时间相近的文档（前后各 7 天）
        time_window = timedelta(days=7)
        start_time = current_doc.created_at - time_window
        end_time = current_doc.created_at + time_window

        nearby_docs = self.db.query(Document).filter(
            and_(
                Document.project_id == project_id,
                Document.id != document_id,
                Document.created_at.between(start_time, end_time)
            )
        ).order_by(
            func.abs(
                func.extract('epoch', Document.created_at) -
                func.extract('epoch', current_doc.created_at)
            )
        ).limit(top_n).all()

        candidates = []
        for doc in nearby_docs:
            time_diff = abs((doc.created_at - current_doc.created_at).total_seconds())
            # 时间差越小，分数越高
            score = max(0, 1 - (time_diff / (7 * 24 * 3600)))

            candidates.append({
                "document_id": doc.id,
                "title": doc.title or doc.file_name,
                "score": score,
                "reason": f"时间相近 ({time_diff / 3600:.1f} 小时)",
                "time_difference_hours": time_diff / 3600
            })

        return candidates

    # ==================== 智能搜索建议 ====================

    def search_suggestions(
        self,
        query: str,
        project_id: int,
        suggestion_type: str = "all",
        limit: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜索建议（自动补全）

        类型：
        - keywords: 关键词建议
        - entities: 实体建议
        - documents: 文档建议
        - all: 全部
        """
        results = {}

        if suggestion_type in ["keywords", "all"]:
            results['keywords'] = self._suggest_keywords(query, project_id, limit)

        if suggestion_type in ["entities", "all"]:
            results['entities'] = self._suggest_entities(query, project_id, limit)

        if suggestion_type in ["documents", "all"]:
            results['documents'] = self._suggest_documents(query, project_id, limit)

        return results

    def _suggest_keywords(
        self,
        query: str,
        project_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """关键词建议"""
        keywords = self.db.query(Keyword).filter(
            and_(
                Keyword.project_id == project_id,
                Keyword.text.ilike(f"%{query}%")
            )
        ).order_by(desc(Keyword.frequency)).limit(limit).all()

        return [
            {
                "id": kw.id,
                "text": kw.text,
                "category": kw.category,
                "frequency": kw.frequency,
                "type": "keyword"
            }
            for kw in keywords
        ]

    def _suggest_entities(
        self,
        query: str,
        project_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """实体建议"""
        entities = self.db.query(ReportEntity).filter(
            ReportEntity.name.ilike(f"%{query}%")
        ).order_by(desc(ReportEntity.frequency)).limit(limit).all()

        return [
            {
                "id": entity.id,
                "name": entity.name,
                "type": entity.entity_type.value,
                "frequency": entity.frequency
            }
            for entity in entities
        ]

    def _suggest_documents(
        self,
        query: str,
        project_id: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """文档建议"""
        documents = self.db.query(Document).filter(
            and_(
                Document.project_id == project_id,
                or_(
                    Document.title.ilike(f"%{query}%"),
                    Document.file_name.ilike(f"%{query}%")
                )
            )
        ).limit(limit).all()

        return [
            {
                "id": doc.id,
                "title": doc.title or doc.file_name,
                "file_name": doc.file_name,
                "type": "document"
            }
            for doc in documents
        ]
