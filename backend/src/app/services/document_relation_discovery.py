"""
文档关系发现服务 - 识别文档间的引用、补充、矛盾等关系
"""
import logging
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DocumentRelationDiscovery:
    """文档关系发现器"""

    # 关系类型定义
    RELATION_TYPES = {
        'REFERENCES': '引用',          # A引用B
        'SUPPLEMENTS': '补充',         # A补充B
        'CONTRADICTS': '矛盾',         # A与B矛盾
        'SIMILAR_TOPIC': '相似主题',   # 主题相似
        'TEMPORAL_SEQUENCE': '时间顺序', # 时间顺序
        'SAME_ENTITY': '相同实体'      # 提到相同实体
    }

    def __init__(self, use_workflow_engine: bool = True):



        self.use_workflow_engine = use_workflow_engine



        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)
        logger.info("✅ 文档关系发现器初始化完成")

    def discover_relations(self, project_id: int, db: Session) -> List[Dict[str, Any]]:
        """
        发现项目中所有文档间的关系

        Args:
            project_id: 项目ID
            db: 数据库会话

        Returns:
            List of {
                'source_document_id': int,
                'target_document_id': int,
                'relation_type': str,
                'confidence': float,
                'evidence': Dict
            }
        """
        from app.models.project import ProjectDocument

        try:
            # 获取所有已完成的文档
            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status == "completed"
            ).all()

            if len(documents) < 2:
                logger.info("文档数量不足，跳过关系发现")
                return []

            logger.info(f"开始分析{len(documents)}个文档间的关系")

            all_relations = []

            # 两两比对文档
            for i, doc_a in enumerate(documents):
                for j, doc_b in enumerate(documents):
                    if i >= j:  # 避免重复比对
                        continue

                    # 发现各种关系
                    relations = self._discover_relations_between(doc_a, doc_b)
                    all_relations.extend(relations)

            logger.info(f"✅ 发现{len(all_relations)}个文档关系")
            return all_relations

        except Exception as e:
            logger.error(f"❌ 文档关系发现失败: {e}", exc_info=True)
            return []

    def _discover_relations_between(self, doc_a, doc_b) -> List[Dict[str, Any]]:
        """发现两个文档之间的所有关系"""
        relations = []

        # 1. 检查实体共享关系
        entity_relation = self._check_entity_sharing(doc_a, doc_b)
        if entity_relation:
            relations.append(entity_relation)

        # 2. 检查主题相似性
        topic_relation = self._check_topic_similarity(doc_a, doc_b)
        if topic_relation:
            relations.append(topic_relation)

        # 3. 检查时间顺序
        temporal_relation = self._check_temporal_sequence(doc_a, doc_b)
        if temporal_relation:
            relations.append(temporal_relation)

        # 4. 检查文本引用（文件名提及）
        reference_relation = self._check_text_reference(doc_a, doc_b)
        if reference_relation:
            relations.append(reference_relation)

        return relations

    def _check_entity_sharing(self, doc_a, doc_b) -> Dict[str, Any]:
        """检查两个文档是否共享实体"""
        entities_a = set()
        entities_b = set()

        if doc_a.extracted_entities:
            entities_a = set(e['name'] for e in doc_a.extracted_entities if 'name' in e)

        if doc_b.extracted_entities:
            entities_b = set(e['name'] for e in doc_b.extracted_entities if 'name' in e)

        shared_entities = entities_a & entities_b

        if len(shared_entities) >= 2:  # 至少2个共同实体
            confidence = min(1.0, len(shared_entities) / 10)  # 共享越多越可信

            return {
                'source_document_id': doc_a.id,
                'target_document_id': doc_b.id,
                'relation_type': 'SAME_ENTITY',
                'confidence': confidence,
                'evidence': {
                    'shared_entities': list(shared_entities)[:10],
                    'count': len(shared_entities)
                }
            }

        return None

    def _check_topic_similarity(self, doc_a, doc_b) -> Dict[str, Any]:
        """检查主题相似性"""
        # 使用关键词和自动聚类判断
        keywords_a = set()
        keywords_b = set()

        if doc_a.extra_data and 'keywords' in doc_a.extra_data:
            keywords_a = set(kw[:10] for kw in doc_a.extra_data['keywords'] if isinstance(kw, str))

        if doc_b.extra_data and 'keywords' in doc_b.extra_data:
            keywords_b = set(kw[:10] for kw in doc_b.extra_data['keywords'] if isinstance(kw, str))

        if keywords_a and keywords_b:
            shared_keywords = keywords_a & keywords_b
            similarity = len(shared_keywords) / max(len(keywords_a), len(keywords_b))

            if similarity > 0.3:  # 30%以上关键词重叠
                return {
                    'source_document_id': doc_a.id,
                    'target_document_id': doc_b.id,
                    'relation_type': 'SIMILAR_TOPIC',
                    'confidence': similarity,
                    'evidence': {
                        'shared_keywords': list(shared_keywords)[:10],
                        'similarity_score': round(similarity, 3)
                    }
                }

        # 检查聚类标签
        clusters_a = self._cluster_labels(doc_a.auto_clusters or [])
        clusters_b = self._cluster_labels(doc_b.auto_clusters or [])

        shared_clusters = set(clusters_a) & set(clusters_b)
        if shared_clusters:
            return {
                'source_document_id': doc_a.id,
                'target_document_id': doc_b.id,
                'relation_type': 'SIMILAR_TOPIC',
                'confidence': 0.8,
                'evidence': {
                    'shared_topics': list(shared_clusters)
                }
            }

        return None

    def _cluster_labels(self, clusters: Any) -> List[str]:
        """把历史上不同形态的聚类结果归一成可比较的标签列表。"""
        labels: List[str] = []

        def add(value: Any):
            if value is None:
                return
            if isinstance(value, str):
                text = value.strip()
                if text:
                    labels.append(text)
                return
            if isinstance(value, (int, float, bool)):
                labels.append(str(value))
                return
            if isinstance(value, dict):
                for key in ("label", "name", "topic", "title", "cluster_label", "cluster_id"):
                    if key in value:
                        add(value.get(key))
                        return
                keywords = value.get("keywords")
                if isinstance(keywords, list):
                    add(" / ".join(str(item) for item in keywords[:3] if item))
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    add(item)

        add(clusters)
        return list(dict.fromkeys(labels))

    def _check_temporal_sequence(self, doc_a, doc_b) -> Dict[str, Any]:
        """检查时间顺序关系"""
        # 从文件名或元数据中提取时间
        time_a = self._extract_time(doc_a)
        time_b = self._extract_time(doc_b)

        if time_a and time_b:
            if time_a < time_b:
                return {
                    'source_document_id': doc_a.id,
                    'target_document_id': doc_b.id,
                    'relation_type': 'TEMPORAL_SEQUENCE',
                    'confidence': 0.9,
                    'evidence': {
                        'time_a': time_a.isoformat(),
                        'time_b': time_b.isoformat(),
                        'order': 'A在B之前'
                    }
                }

        return None

    def _extract_time(self, doc) -> datetime:
        """从文档中提取时间信息"""
        # 1. 从文件名提取日期
        patterns = [
            r'(\d{4})-?(\d{2})-?(\d{2})',  # 2024-03-15 或 20240315
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2024年3月15日
        ]

        for pattern in patterns:
            match = re.search(pattern, doc.file_name)
            if match:
                try:
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                    return datetime(year, month, day)
                except (ValueError, OverflowError) as e:
                    # 文件名中的数字不一定是真实日期；此处会回退到上传时间，
                    # 不应在批量跨文档分析中重复刷屏为用户错误。
                    logger.debug("文件名日期无效，回退到上传时间: %s (%s)", doc.file_name, e)
                    pass

        # 2. 使用上传时间
        if doc.created_at:
            return doc.created_at

        return None

    def _check_text_reference(self, doc_a, doc_b) -> Dict[str, Any]:
        """检查文本中是否互相引用"""
        # 检查doc_a的文本中是否提到doc_b的文件名
        if doc_a.text_content and doc_b.file_name:
            # 去掉扩展名
            name_b = doc_b.file_name.rsplit('.', 1)[0]

            if name_b in doc_a.text_content:
                return {
                    'source_document_id': doc_a.id,
                    'target_document_id': doc_b.id,
                    'relation_type': 'REFERENCES',
                    'confidence': 0.95,
                    'evidence': {
                        'reference_text': f"文档A中提到了'{name_b}'"
                    }
                }

        return None


# 全局实例
document_relation_discovery = DocumentRelationDiscovery()
