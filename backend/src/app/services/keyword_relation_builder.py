"""
关键词关系构建服务
计算关键词之间的共现关系、关系强度
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import defaultdict, Counter
import json

from app.models.keyword import Keyword, DocumentKeyword, KeywordRelation
from app.models.document import Document

logger = logging.getLogger(__name__)


class KeywordRelationBuilder:
    """关键词关系构建器"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

        # 共现窗口配置（字符数）
        self.WINDOW_SENTENCE = 100  # 句子级（强关系）
        self.WINDOW_PARAGRAPH = 500  # 段落级（中等关系）

        # 权重配置
        self.WEIGHT_SENTENCE = 1.0
        self.WEIGHT_PARAGRAPH = 0.6
        self.WEIGHT_DOCUMENT = 0.3

    def build_cooccurrence_relations(
        self,
        project_id: int,
        min_cooccurrence: int = 2,
        recalculate: bool = False
    ) -> Dict[str, Any]:
        """
        构建关键词共现关系

        Args:
            project_id: 项目ID
            min_cooccurrence: 最小共现次数（过滤噪音）
            recalculate: 是否重新计算（删除旧关系）

        Returns:
            统计信息
        """
        logger.info(f"开始构建关键词共现关系: project_id={project_id}")

        # 如果需要重新计算，删除旧关系
        if recalculate:
            deleted = self.db.query(KeywordRelation).filter(
                KeywordRelation.project_id == project_id
            ).delete()
            self.db.commit()
            logger.info(f"已删除旧关系: {deleted} 条")

        # 获取项目中有关键词的文档ID列表
        doc_ids_with_keywords = self.db.query(DocumentKeyword.document_id)\
            .distinct()\
            .join(Keyword, DocumentKeyword.keyword_id == Keyword.id)\
            .filter(Keyword.project_id == project_id)\
            .all()

        doc_ids = [row[0] for row in doc_ids_with_keywords]

        if not doc_ids:
            logger.warning(f"项目 {project_id} 没有包含关键词的文档")
            return {"relations_created": 0, "documents_processed": 0}

        logger.info(f"找到 {len(doc_ids)} 个包含关键词的文档")

        # 初始化关系缓存
        self._relation_cache = {}

        # 统计信息
        stats = {
            "documents_processed": 0,
            "keyword_pairs_found": 0,
            "relations_created": 0,
            "relations_updated": 0
        }

        # 按文档处理
        for doc_id in doc_ids:
            doc_stats = self._process_document_cooccurrence(doc_id, project_id)
            stats["documents_processed"] += 1
            stats["keyword_pairs_found"] += doc_stats["pairs_found"]

            if stats["documents_processed"] % 10 == 0:
                logger.info(f"已处理 {stats['documents_processed']}/{len(doc_ids)} 个文档")

        # 批量写入关系到数据库
        logger.info(f"批量写入 {len(self._relation_cache)} 条关系到数据库...")
        self._flush_relation_cache()

        # 计算关系强度并过滤
        stats["relations_created"] = self._finalize_relations(project_id, min_cooccurrence)

        logger.info(f"共现关系构建完成: {stats}")
        return stats

    def _process_document_cooccurrence(
        self,
        document_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        处理单个文档的关键词共现

        策略：
        1. 文档级共现：同一文档中出现的所有关键词对
        2. 窗口级共现：基于位置信息计算接近度
        """
        # 获取文档的所有关键词及其位置
        doc_keywords = self.db.query(DocumentKeyword).filter(
            DocumentKeyword.document_id == document_id
        ).all()

        if len(doc_keywords) < 2:
            return {"pairs_found": 0}

        pairs_found = 0

        # 遍历所有关键词对
        for i in range(len(doc_keywords)):
            for j in range(i + 1, len(doc_keywords)):
                kw1 = doc_keywords[i]
                kw2 = doc_keywords[j]

                # 计算接近度权重
                proximity_weight = self._calculate_proximity_weight(kw1, kw2)

                # 记录共现
                self._record_cooccurrence(
                    keyword1_id=kw1.keyword_id,
                    keyword2_id=kw2.keyword_id,
                    project_id=project_id,
                    proximity_weight=proximity_weight,
                    document_id=document_id
                )

                pairs_found += 1

        return {"pairs_found": pairs_found}

    def _calculate_proximity_weight(
        self,
        kw1: DocumentKeyword,
        kw2: DocumentKeyword
    ) -> float:
        """
        计算两个关键词的接近度权重

        基于位置信息计算：
        - 如果在句子级窗口内：1.0
        - 如果在段落级窗口内：0.6
        - 否则（仅文档级）：0.3
        """
        # 解析位置信息
        positions1 = kw1.positions if kw1.positions else []
        positions2 = kw2.positions if kw2.positions else []

        if not positions1 or not positions2:
            # 没有位置信息，使用文档级权重
            return self.WEIGHT_DOCUMENT

        # 计算最小距离
        min_distance = float('inf')
        for pos1 in positions1:
            for pos2 in positions2:
                distance = abs(pos1 - pos2)
                min_distance = min(min_distance, distance)

        # 根据距离返回权重
        if min_distance <= self.WINDOW_SENTENCE:
            return self.WEIGHT_SENTENCE
        elif min_distance <= self.WINDOW_PARAGRAPH:
            return self.WEIGHT_PARAGRAPH
        else:
            return self.WEIGHT_DOCUMENT

    def _record_cooccurrence(
        self,
        keyword1_id: int,
        keyword2_id: int,
        project_id: int,
        proximity_weight: float,
        document_id: int
    ):
        """
        记录关键词共现

        使用内存缓存，避免频繁查询和提交
        """
        # 确保 keyword1_id < keyword2_id（避免重复）
        if keyword1_id > keyword2_id:
            keyword1_id, keyword2_id = keyword2_id, keyword1_id

        # 使用缓存字典（在 build_cooccurrence_relations 中初始化）
        cache_key = (keyword1_id, keyword2_id, project_id)

        if not hasattr(self, '_relation_cache'):
            self._relation_cache = {}

        if cache_key in self._relation_cache:
            # 更新缓存中的关系
            self._relation_cache[cache_key]['co_occurrence'] += 1
            self._relation_cache[cache_key]['correlation'] += proximity_weight
            if document_id not in self._relation_cache[cache_key]['contexts']:
                self._relation_cache[cache_key]['contexts'].append(document_id)
        else:
            # 添加到缓存
            self._relation_cache[cache_key] = {
                'keyword1_id': keyword1_id,
                'keyword2_id': keyword2_id,
                'project_id': project_id,
                'co_occurrence': 1,
                'correlation': proximity_weight,
                'contexts': [document_id]
            }

    def _flush_relation_cache(self):
        """
        将缓存的关系批量写入数据库
        """
        if not hasattr(self, '_relation_cache') or not self._relation_cache:
            return

        logger.info(f"准备写入 {len(self._relation_cache)} 条关系...")

        # 批量创建关系对象
        batch_size = 100
        relations_to_add = []

        for cache_key, data in self._relation_cache.items():
            relation = KeywordRelation(
                keyword1_id=data['keyword1_id'],
                keyword2_id=data['keyword2_id'],
                project_id=data['project_id'],
                relation_type="co_occurrence",
                co_occurrence=data['co_occurrence'],
                correlation=data['correlation'],
                contexts=data['contexts']
            )
            relations_to_add.append(relation)

            # 分批提交
            if len(relations_to_add) >= batch_size:
                self.db.bulk_save_objects(relations_to_add)
                self.db.commit()
                logger.info(f"已提交 {len(relations_to_add)} 条关系")
                relations_to_add = []

        # 提交剩余的
        if relations_to_add:
            self.db.bulk_save_objects(relations_to_add)
            self.db.commit()
            logger.info(f"已提交最后 {len(relations_to_add)} 条关系")

        # 清空缓存
        self._relation_cache = {}

    def _finalize_relations(
        self,
        project_id: int,
        min_cooccurrence: int
    ) -> int:
        """
        最终化关系：计算关系强度，过滤低频关系

        Returns:
            保留的关系数量
        """
        logger.info(f"开始计算关系强度并过滤...")

        # 先提交之前的所有关系记录
        self.db.commit()

        # 获取所有关系
        relations = self.db.query(KeywordRelation).filter(
            KeywordRelation.project_id == project_id
        ).all()

        logger.info(f"共 {len(relations)} 条原始关系")

        kept_count = 0
        deleted_count = 0

        for relation in relations:
            # 过滤低频关系
            if relation.co_occurrence < min_cooccurrence:
                self.db.delete(relation)
                deleted_count += 1
                continue

            # 计算关系强度
            strength = self._calculate_relation_strength(relation)
            relation.strength = strength

            # 归一化 correlation（平均接近度）
            if relation.correlation and relation.co_occurrence > 0:
                relation.correlation = relation.correlation / relation.co_occurrence

            kept_count += 1

        self.db.commit()

        logger.info(f"保留 {kept_count} 条关系，删除 {deleted_count} 条低频关系")
        return kept_count

    def _calculate_relation_strength(self, relation: KeywordRelation) -> float:
        """
        计算关系强度

        公式: strength = (co_occurrence / geometric_mean_frequency) * avg_proximity_weight

        范围: 0.0 - 1.0
        """
        # 获取两个关键词的频率
        kw1 = self.db.query(Keyword).filter(Keyword.id == relation.keyword1_id).first()
        kw2 = self.db.query(Keyword).filter(Keyword.id == relation.keyword2_id).first()

        if not kw1 or not kw2:
            return 0.0

        # 使用几何平均数（避免高频词主导）
        freq1 = kw1.frequency or 1
        freq2 = kw2.frequency or 1
        geometric_mean = (freq1 * freq2) ** 0.5

        # 共现强度
        cooccurrence_strength = relation.co_occurrence / geometric_mean

        # 接近度权重
        proximity_weight = relation.correlation or self.WEIGHT_DOCUMENT

        # 综合强度
        strength = cooccurrence_strength * proximity_weight

        # 归一化到 0-1（使用 tanh 压缩）
        import math
        normalized_strength = math.tanh(strength / 2)

        return round(normalized_strength, 4)

    def build_hierarchy_relations(
        self,
        project_id: int
    ) -> int:
        """
        构建层级关系（可选）

        基于分类和实体类型识别上下位关系
        例如: "村委会" -> "基层组织"

        TODO: 需要 LLM 或知识库支持
        """
        logger.info("层级关系构建暂未实现")
        return 0

    def get_relation_statistics(self, project_id: int) -> Dict[str, Any]:
        """获取关系统计信息"""

        total_relations = self.db.query(KeywordRelation).filter(
            KeywordRelation.project_id == project_id
        ).count()

        avg_strength = self.db.query(func.avg(KeywordRelation.strength)).filter(
            KeywordRelation.project_id == project_id
        ).scalar() or 0.0

        max_cooccurrence = self.db.query(func.max(KeywordRelation.co_occurrence)).filter(
            KeywordRelation.project_id == project_id
        ).scalar() or 0

        # 获取连接最多的关键词
        from sqlalchemy import union_all

        kw1_counts = self.db.query(
            KeywordRelation.keyword1_id.label('keyword_id'),
            func.count(KeywordRelation.id).label('connection_count')
        ).filter(
            KeywordRelation.project_id == project_id
        ).group_by(KeywordRelation.keyword1_id)

        kw2_counts = self.db.query(
            KeywordRelation.keyword2_id.label('keyword_id'),
            func.count(KeywordRelation.id).label('connection_count')
        ).filter(
            KeywordRelation.project_id == project_id
        ).group_by(KeywordRelation.keyword2_id)

        # 合并统计
        combined = union_all(kw1_counts, kw2_counts).subquery()

        top_connected = self.db.query(
            combined.c.keyword_id,
            func.sum(combined.c.connection_count).label('total_connections')
        ).group_by(combined.c.keyword_id)\
         .order_by(func.sum(combined.c.connection_count).desc())\
         .limit(10).all()

        # 获取关键词名称
        top_keywords = []
        for kw_id, conn_count in top_connected:
            kw = self.db.query(Keyword).filter(Keyword.id == kw_id).first()
            if kw:
                top_keywords.append({
                    "keyword": kw.text,
                    "connections": conn_count
                })

        return {
            "total_relations": total_relations,
            "average_strength": round(avg_strength, 4),
            "max_cooccurrence": max_cooccurrence,
            "top_connected_keywords": top_keywords
        }
