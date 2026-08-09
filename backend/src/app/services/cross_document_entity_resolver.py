"""
跨文档实体消歧服务 - 识别并合并不同文档中的同一实体
"""
import logging
from typing import Dict, List, Any, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import difflib

logger = logging.getLogger(__name__)


class CrossDocumentEntityResolver:
    """跨文档实体消歧器"""

    def __init__(self):
        self.similarity_threshold = 0.85  # 名称相似度阈值
        logger.info("✅ 跨文档实体消歧器初始化完成")

    def resolve_entities(self, project_id: int, db: Session) -> Dict[str, Any]:
        """
        解析项目中的所有实体，识别重复实体

        Args:
            project_id: 项目ID
            db: 数据库会话

        Returns:
            {
                'canonical_entities': List[Dict],  # 标准实体列表
                'alignments': List[Dict],          # 对齐关系
                'statistics': Dict                 # 统计信息
            }
        """
        from app.models.entity import Entity
        from app.models.project import ProjectDocument

        try:
            # 1. 获取项目中所有已完成文档的实体
            documents = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status == "completed"
            ).all()

            if len(documents) < 2:
                logger.info("文档数量不足，跳过跨文档实体消歧")
                return {
                    'canonical_entities': [],
                    'alignments': [],
                    'statistics': {'reason': 'insufficient_documents'}
                }

            # 2. 收集所有实体
            all_entities = []
            for doc in documents:
                if doc.extracted_entities:
                    for entity in doc.extracted_entities:
                        all_entities.append({
                            'name': entity.get('name', ''),
                            'type': entity.get('type', 'UNKNOWN'),
                            'document_id': doc.id,
                            'document_name': doc.file_name,
                            'context': entity.get('context', ''),
                            'confidence': entity.get('confidence', 0.5)
                        })

            logger.info(f"收集到{len(all_entities)}个实体，来自{len(documents)}个文档")

            # 3. 按类型分组
            entities_by_type = {}
            for entity in all_entities:
                entity_type = entity['type']
                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []
                entities_by_type[entity_type].append(entity)

            # 4. 对每个类型进行实体消歧
            canonical_entities = []
            alignments = []

            for entity_type, entities in entities_by_type.items():
                canonical, align = self._resolve_entities_of_type(entities, entity_type)
                canonical_entities.extend(canonical)
                alignments.extend(align)

            # 5. 统计
            statistics = {
                'total_entities': len(all_entities),
                'canonical_entities': len(canonical_entities),
                'merged_count': len(all_entities) - len(canonical_entities),
                'documents_processed': len(documents),
                'entity_types': len(entities_by_type)
            }

            logger.info(f"✅ 实体消歧完成: {len(all_entities)}个实体 → {len(canonical_entities)}个标准实体")

            return {
                'canonical_entities': canonical_entities,
                'alignments': alignments,
                'statistics': statistics
            }

        except Exception as e:
            logger.error(f"❌ 跨文档实体消歧失败: {e}", exc_info=True)
            return {
                'canonical_entities': [],
                'alignments': [],
                'statistics': {'error': str(e)}
            }

    def _resolve_entities_of_type(self, entities: List[Dict], entity_type: str) -> Tuple[List[Dict], List[Dict]]:
        """
        对同一类型的实体进行消歧

        Returns:
            (canonical_entities, alignments)
        """
        if not entities:
            return [], []

        # 使用并查集来合并相似实体
        clusters = []  # 每个cluster是一组相似实体的列表

        for entity in entities:
            # 查找是否应该加入现有cluster
            merged = False
            for cluster in clusters:
                if self._should_merge(entity, cluster):
                    cluster.append(entity)
                    merged = True
                    break

            # 如果没有找到匹配的cluster，创建新cluster
            if not merged:
                clusters.append([entity])

        # 从每个cluster生成canonical entity
        canonical_entities = []
        alignments = []

        for cluster_idx, cluster in enumerate(clusters):
            canonical_id = f"{entity_type}_{cluster_idx}"

            # 选择最有代表性的名称（出现次数最多的）
            name_counts = {}
            for e in cluster:
                name = e['name']
                name_counts[name] = name_counts.get(name, 0) + 1

            canonical_name = max(name_counts.items(), key=lambda x: x[1])[0]

            # 合并所有出现的文档
            document_ids = list(set(e['document_id'] for e in cluster))
            document_names = list(set(e['document_name'] for e in cluster))

            # 合并上下文
            contexts = [e['context'] for e in cluster if e['context']][:5]  # 最多保留5个上下文

            # 计算平均置信度
            avg_confidence = sum(e['confidence'] for e in cluster) / len(cluster)

            canonical_entities.append({
                'canonical_id': canonical_id,
                'name': canonical_name,
                'type': entity_type,
                'document_ids': document_ids,
                'document_names': document_names,
                'mention_count': len(cluster),
                'contexts': contexts,
                'confidence': avg_confidence,
                'variant_names': list(name_counts.keys())
            })

            # 记录对齐关系
            alignments.append({
                'canonical_id': canonical_id,
                'canonical_name': canonical_name,
                'mentions': [
                    {
                        'name': e['name'],
                        'document_id': e['document_id'],
                        'document_name': e['document_name']
                    }
                    for e in cluster
                ],
                'merge_reason': self._explain_merge(cluster)
            })

        return canonical_entities, alignments

    def _should_merge(self, entity: Dict, cluster: List[Dict]) -> bool:
        """
        判断实体是否应该加入cluster
        """
        entity_name = entity['name'].lower().strip()

        # 与cluster中任意一个实体相似即可合并
        for cluster_entity in cluster:
            cluster_name = cluster_entity['name'].lower().strip()

            # 1. 完全相同
            if entity_name == cluster_name:
                return True

            # 2. 名称相似度高
            similarity = difflib.SequenceMatcher(None, entity_name, cluster_name).ratio()
            if similarity >= self.similarity_threshold:
                return True

            # 3. 一个是另一个的子串（处理全名/简称）
            if entity_name in cluster_name or cluster_name in entity_name:
                # 长度差异不能太大（避免误合并）
                len_ratio = min(len(entity_name), len(cluster_name)) / max(len(entity_name), len(cluster_name))
                if len_ratio > 0.5:
                    return True

            # 4. 特殊规则：中文人名（姓相同，名字相似）
            if entity['type'] == 'PERSON' and self._is_chinese_name(entity_name):
                if self._is_similar_chinese_name(entity_name, cluster_name):
                    return True

        return False

    def _is_chinese_name(self, name: str) -> bool:
        """判断是否为中文姓名"""
        return 2 <= len(name) <= 4 and all('一' <= c <= '鿿' for c in name)

    def _is_similar_chinese_name(self, name1: str, name2: str) -> bool:
        """判断两个中文姓名是否相似"""
        if not (self._is_chinese_name(name1) and self._is_chinese_name(name2)):
            return False

        # 姓相同
        if name1[0] == name2[0]:
            # 名字部分相似
            if len(name1) == len(name2):
                return difflib.SequenceMatcher(None, name1[1:], name2[1:]).ratio() > 0.6
            # 全名和简称（例如：张三 vs 张三丰）
            if name1 in name2 or name2 in name1:
                return True

        return False

    def _explain_merge(self, cluster: List[Dict]) -> str:
        """解释为什么这些实体被合并"""
        if len(cluster) == 1:
            return "单一实体"

        names = [e['name'] for e in cluster]
        unique_names = list(set(names))

        if len(unique_names) == 1:
            return f"完全相同的名称，出现在{len(cluster)}个文档中"
        else:
            return f"相似的名称变体: {', '.join(unique_names[:3])}"


# 全局实例
cross_document_resolver = CrossDocumentEntityResolver()
