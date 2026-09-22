"""
Step 3: 实体构建服务
Entity Extraction Service

功能：
1. 从文本中提取实体（人物、地点、组织、概念等）
2. 使用 NER + 规则 + 模式匹配
3. 保存到 entities_unified 表
4. 创建知识图谱节点
5. 发布事件
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
import re
import logging
from typing import List, Dict, Any, Set
import uuid
import json

from app.models.project import DocumentChunk
from app.models.unified_models import EntityUnified, KnowledgeGraphNode
from app.services.event_bus import publish_event, EventTypes

logger = logging.getLogger(__name__)


class EntityExtractionService:
    """实体构建服务（Step 3）"""

    def __init__(self, db: Session):
        self.db = db

    def extract_entities(self, document_id: int) -> Dict[str, Any]:
        """
        提取文档中的所有实体

        Args:
            document_id: 文档 ID

        Returns:
            提取结果
        """
        logger.info(f"👤 Step 3: 开始实体构建 - 文档 {document_id}")

        try:
            # 获取所有 chunks
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).all()

            if not chunks:
                logger.warning(f"文档 {document_id} 没有 chunks")
                return {'success': False, 'message': '文档没有 chunks'}

            # 提取实体
            entities = self._extract_from_chunks(document_id, chunks)

            # 合并和消歧
            merged_entities = self._merge_entities(entities)

            # 保存到数据库
            saved_count = self._save_entities(document_id, merged_entities)

            # 创建知识图谱节点
            kg_nodes_count = self._create_kg_nodes(merged_entities)

            result = {
                'success': True,
                'document_id': document_id,
                'entities_extracted': len(entities),
                'entities_merged': saved_count,
                'kg_nodes_created': kg_nodes_count,
                'entity_types': self._count_by_type(merged_entities)
            }

            logger.info(
                f"✅ Step 3 完成: 提取了 {len(entities)} 个实体, "
                f"合并后 {saved_count} 个, "
                f"创建 {kg_nodes_count} 个知识图谱节点"
            )

            # 发布事件
            publish_event(
                event_type=EventTypes.ENTITIES_EXTRACTED,
                payload={
                    'step': 3,
                    'step_name': 'entity_extraction',
                    'document_id': document_id,
                    'result': result
                },
                publisher='EntityExtractionService'
            )

            return result

        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Step 3 失败: {e}", exc_info=True)
            raise

    def _extract_from_chunks(
        self,
        document_id: int,
        chunks: List[DocumentChunk]
    ) -> List[Dict[str, Any]]:
        """
        从所有 chunks 提取实体

        Returns:
            实体列表（未合并）
        """
        all_entities = []

        for chunk in chunks:
            text = chunk.cleaned_text or chunk.text
            if not text:
                continue

            # 方法1: 使用 NER（如果可用）
            entities_ner = self._extract_by_ner(text)

            # 方法2: 使用规则和模式
            entities_rule = self._extract_by_rules(text)

            # 合并结果
            chunk_entities = entities_ner + entities_rule

            # 添加来源信息
            for entity in chunk_entities:
                entity['chunk_id'] = chunk.id
                entity['document_id'] = document_id

            all_entities.extend(chunk_entities)

        return all_entities

    def _extract_by_ner(self, text: str) -> List[Dict]:
        """
        使用 NER 提取实体

        注意：需要安装 NLP 库（如 spaCy）
        这里先用简化版本
        """
        entities = []

        # TODO: 集成 spaCy 或其他 NER 工具
        # 示例：
        # import spacy
        # nlp = spacy.load("zh_core_web_sm")
        # doc = nlp(text)
        # for ent in doc.ents:
        #     entities.append({
        #         'name': ent.text,
        #         'type': ent.label_,
        #         'method': 'NER'
        #     })

        return entities

    def _extract_by_rules(self, text: str) -> List[Dict]:
        """
        使用规则提取实体

        规则：
        1. 人名：中文姓名格式
        2. 地点：包含"省/市/县/村"等
        3. 组织：包含"公司/组织/协会"等
        4. 概念：专有名词
        """
        entities = []

        # 规则1: 中文人名（姓 + 名，2-4 字）
        person_pattern = r'[一-龥]{2,4}(?:先生|女士|教授|老师|医生|师傅|大爷|大娘)?'
        person_matches = re.finditer(person_pattern, text)
        for match in person_matches:
            name = match.group(0)
            # 过滤常见词
            if len(name) >= 2 and not self._is_common_word(name):
                entities.append({
                    'name': name,
                    'type': 'person',
                    'method': 'rule',
                    'confidence': 0.7
                })

        # 规则2: 地点
        location_pattern = r'[一-龥]{2,10}(?:省|市|县|区|镇|乡|村|路|街|巷|河|山|湖|寺|庙)'
        location_matches = re.finditer(location_pattern, text)
        for match in location_matches:
            entities.append({
                'name': match.group(0),
                'type': 'location',
                'method': 'rule',
                'confidence': 0.8
            })

        # 规则3: 组织
        org_pattern = r'[一-龥]{2,20}(?:公司|企业|组织|协会|学会|研究所|大学|学院|医院|银行|政府|部门)'
        org_matches = re.finditer(org_pattern, text)
        for match in org_matches:
            entities.append({
                'name': match.group(0),
                'type': 'organization',
                'method': 'rule',
                'confidence': 0.8
            })

        # 规则4: 概念（书名号中的内容）
        concept_pattern = r'《([^》]+)》'
        concept_matches = re.finditer(concept_pattern, text)
        for match in concept_matches:
            entities.append({
                'name': match.group(1),
                'type': 'concept',
                'method': 'rule',
                'confidence': 0.9
            })

        return entities

    def _is_common_word(self, word: str) -> bool:
        """判断是否是常见词（非实体）"""
        common_words = {
            '我们', '他们', '她们', '这个', '那个', '什么', '怎么',
            '可以', '应该', '需要', '进行', '开始', '结束', '完成',
            '发现', '认为', '表示', '指出', '提出', '建议',
            '研究', '分析', '调查', '访谈', '观察', '记录'
        }
        return word in common_words

    def _merge_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        合并重复实体

        策略：
        1. 相同名称 + 相同类型 -> 合并
        2. 记录所有出现位置
        3. 累加置信度
        """
        # 按 (name, type) 分组
        entity_map = {}

        for entity in entities:
            key = (entity['name'], entity['type'])

            if key not in entity_map:
                entity_map[key] = {
                    'name': entity['name'],
                    'type': entity['type'],
                    'chunk_ids': [entity['chunk_id']],
                    'first_mention_chunk_id': entity['chunk_id'],
                    'mention_count': 1,
                    'confidence': entity.get('confidence', 1.0),
                    'extraction_method': entity.get('method', 'unknown')
                }
            else:
                existing = entity_map[key]
                existing['chunk_ids'].append(entity['chunk_id'])
                existing['mention_count'] += 1
                existing['confidence'] = min(1.0, existing['confidence'] + 0.1)

        return list(entity_map.values())

    def _save_entities(self, document_id: int, entities: List[Dict]) -> int:
        """
        保存实体到数据库

        Returns:
            保存的实体数量
        """
        # 先删除旧的实体
        self.db.query(EntityUnified).filter(
            EntityUnified.document_id == document_id
        ).delete()

        saved_count = 0

        for entity in entities:
            entity_id = f"entity_{uuid.uuid4().hex[:16]}"

            db_entity = EntityUnified(
                entity_id=entity_id,
                document_id=document_id,
                entity_name=entity['name'],
                entity_type=entity['type'],
                chunk_ids=json.dumps(entity['chunk_ids']),
                first_mention_chunk_id=entity['first_mention_chunk_id'],
                mention_count=entity['mention_count'],
                confidence=entity['confidence'],
                extraction_method=entity['extraction_method']
            )

            self.db.add(db_entity)
            saved_count += 1

        self.db.commit()

        return saved_count

    def _create_kg_nodes(self, entities: List[Dict]) -> int:
        """
        为实体创建知识图谱节点

        Returns:
            创建的节点数量
        """
        created_count = 0

        for entity in entities:
            # 检查节点是否已存在
            existing = self.db.query(KnowledgeGraphNode).filter(
                KnowledgeGraphNode.source_table == 'entities_unified',
                KnowledgeGraphNode.label == entity['name']
            ).first()

            if existing:
                # 更新统计信息
                existing.degree += 1
                continue

            # 创建新节点
            node_id = f"node_{uuid.uuid4().hex[:16]}"

            kg_node = KnowledgeGraphNode(
                node_id=node_id,
                node_type='entity',
                source_table='entities_unified',
                source_id=entity['name'],  # 暂时用名称
                label=entity['name'],
                display_name=entity['name'],
                properties=json.dumps({
                    'type': entity['type'],
                    'confidence': entity['confidence']
                }),
                importance_score=0.5
            )

            self.db.add(kg_node)
            created_count += 1

        self.db.commit()

        return created_count

    def _count_by_type(self, entities: List[Dict]) -> Dict[str, int]:
        """统计各类型实体数量"""
        type_counts = {}
        for entity in entities:
            entity_type = entity['type']
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        return type_counts


# ============================================================
# 便捷函数
# ============================================================

def extract_document_entities(db: Session, document_id: int) -> Dict[str, Any]:
    """
    提取文档实体的便捷函数

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        提取结果
    """
    service = EntityExtractionService(db)
    return service.extract_entities(document_id)
