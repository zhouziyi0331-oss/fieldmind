#!/usr/bin/env python3
"""
增强关系抽取服务

改进点：
1. 跨chunk的实体关联
2. 更丰富的关系类型
3. 时间和因果关系识别
4. 关系置信度评分
5. 关系去重和合并
"""

import sqlite3
import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedRelationExtractor:
    """增强关系抽取器"""

    def __init__(self, db_path: str = "data/fieldmind.db"):
        """
        初始化关系抽取器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path

        # 定义关系类型和规则
        self.relation_rules = {
            # 地理关系
            'located_in': {
                'patterns': [
                    r'(.+)位于(.+)',
                    r'(.+)在(.+)境内',
                    r'(.+)坐落在(.+)',
                ],
                'entity_types': [('CulturalAsset', 'Location'), ('Event', 'Location')]
            },

            # 继承关系
            'inherits': {
                'patterns': [
                    r'(.+)传承自(.+)',
                    r'(.+)学自(.+)',
                    r'(.+)师从(.+)',
                ],
                'entity_types': [('Person', 'Person'), ('Person', 'CulturalAsset')]
            },

            # 拥有关系
            'owns': {
                'patterns': [
                    r'(.+)拥有(.+)',
                    r'(.+)的(.+)',
                ],
                'entity_types': [('Person', 'CulturalAsset'), ('Organization', 'CulturalAsset')]
            },

            # 参与关系
            'participates_in': {
                'patterns': [
                    r'(.+)参加(.+)',
                    r'(.+)参与(.+)',
                    r'(.+)出席(.+)',
                ],
                'entity_types': [('Person', 'Event')]
            },

            # 创建关系
            'creates': {
                'patterns': [
                    r'(.+)制作(.+)',
                    r'(.+)创作(.+)',
                    r'(.+)建造(.+)',
                ],
                'entity_types': [('Person', 'CulturalAsset')]
            },

            # 保护关系
            'protects': {
                'patterns': [
                    r'(.+)保护(.+)',
                    r'(.+)维护(.+)',
                ],
                'entity_types': [('Organization', 'CulturalAsset'), ('Policy', 'CulturalAsset')]
            },

            # 组织关系
            'member_of': {
                'patterns': [
                    r'(.+)是(.+)成员',
                    r'(.+)属于(.+)',
                ],
                'entity_types': [('Person', 'Organization')]
            },

            # 时间关系
            'occurs_at': {
                'patterns': [
                    r'(.+)发生在(.+)',
                    r'(.+)举行于(.+)',
                ],
                'entity_types': [('Event', 'Location')]
            },
        }

    def extract_all_relations(self) -> int:
        """
        提取所有关系

        Returns:
            提取的关系数量
        """
        logger.info("="*60)
        logger.info("增强关系抽取")
        logger.info("="*60)

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # 1. 提取同chunk内的关系
        same_chunk_relations = self._extract_same_chunk_relations(conn)
        logger.info(f"✅ 同chunk关系: {len(same_chunk_relations)}")

        # 2. 提取跨chunk的关系
        cross_chunk_relations = self._extract_cross_chunk_relations(conn)
        logger.info(f"✅ 跨chunk关系: {len(cross_chunk_relations)}")

        # 3. 基于模式的关系
        pattern_relations = self._extract_pattern_based_relations(conn)
        logger.info(f"✅ 模式匹配关系: {len(pattern_relations)}")

        # 4. 合并和去重
        all_relations = same_chunk_relations + cross_chunk_relations + pattern_relations
        unique_relations = self._deduplicate_relations(all_relations)
        logger.info(f"✅ 去重后关系: {len(unique_relations)}")

        # 5. 保存到数据库
        saved_count = self._save_relations(conn, unique_relations)
        logger.info(f"✅ 保存关系: {saved_count}")

        conn.close()

        return saved_count

    def _extract_same_chunk_relations(self, conn: sqlite3.Connection) -> List[Dict]:
        """提取同一个chunk中的实体关系"""
        cursor = conn.cursor()

        # 获取每个chunk中的所有实体
        cursor.execute("""
            SELECT
                ce.chunk_id,
                e.id as entity_id,
                e.name,
                e.entity_type
            FROM chunk_entities ce
            JOIN entities e ON ce.entity_id = e.id
            ORDER BY ce.chunk_id
        """)

        # 按chunk分组
        chunks_entities = defaultdict(list)
        for row in cursor.fetchall():
            chunks_entities[row['chunk_id']].append({
                'id': row['entity_id'],
                'name': row['name'],
                'type': row['entity_type']
            })

        # 为每个chunk中的实体对创建关系
        relations = []
        for chunk_id, entities in chunks_entities.items():
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    relation_type = self._infer_relation_type(
                        entity1['type'],
                        entity2['type']
                    )

                    if relation_type:
                        relations.append({
                            'source_entity_id': entity1['id'],
                            'target_entity_id': entity2['id'],
                            'relation_type': relation_type,
                            'confidence': 70,
                            'chunk_id': chunk_id,
                            'source': 'same_chunk'
                        })

        return relations

    def _extract_cross_chunk_relations(self, conn: sqlite3.Connection) -> List[Dict]:
        """提取跨chunk的实体关系"""
        cursor = conn.cursor()

        # 查找在同一文档的不同chunks中出现的实体
        cursor.execute("""
            SELECT
                e1.id as entity1_id,
                e1.name as entity1_name,
                e1.entity_type as entity1_type,
                e2.id as entity2_id,
                e2.name as entity2_name,
                e2.entity_type as entity2_type,
                COUNT(DISTINCT dc1.id) as co_occurrence_count
            FROM chunk_entities ce1
            JOIN entities e1 ON ce1.entity_id = e1.id
            JOIN document_chunks dc1 ON ce1.chunk_id = dc1.id
            JOIN document_chunks dc2 ON dc1.document_id = dc2.document_id AND dc1.id != dc2.id
            JOIN chunk_entities ce2 ON dc2.id = ce2.chunk_id
            JOIN entities e2 ON ce2.entity_id = e2.id
            WHERE e1.id < e2.id
            GROUP BY e1.id, e2.id
            HAVING co_occurrence_count >= 2
        """)

        relations = []
        for row in cursor.fetchall():
            relation_type = self._infer_relation_type(
                row['entity1_type'],
                row['entity2_type']
            )

            if relation_type:
                # 置信度基于共现次数
                confidence = min(50 + row['co_occurrence_count'] * 10, 90)

                relations.append({
                    'source_entity_id': row['entity1_id'],
                    'target_entity_id': row['entity2_id'],
                    'relation_type': relation_type,
                    'confidence': confidence,
                    'chunk_id': None,
                    'source': 'cross_chunk'
                })

        return relations

    def _extract_pattern_based_relations(self, conn: sqlite3.Connection) -> List[Dict]:
        """基于文本模式提取关系"""
        cursor = conn.cursor()

        # 获取所有chunks的文本
        cursor.execute("""
            SELECT id, text FROM document_chunks
            WHERE text IS NOT NULL
        """)

        relations = []

        for row in cursor.fetchall():
            chunk_id = row['id']
            text = row['text']

            # 获取这个chunk中的所有实体
            cursor.execute("""
                SELECT e.id, e.name, e.entity_type
                FROM chunk_entities ce
                JOIN entities e ON ce.entity_id = e.id
                WHERE ce.chunk_id = ?
            """, (chunk_id,))

            entities = {row['name']: (row['id'], row['entity_type'])
                       for row in cursor.fetchall()}

            # 对每个关系规则进行匹配
            for relation_type, rule in self.relation_rules.items():
                for pattern in rule['patterns']:
                    matches = re.finditer(pattern, text)

                    for match in matches:
                        # 提取两个实体
                        entity1_name = match.group(1).strip()
                        entity2_name = match.group(2).strip()

                        # 检查是否是已知实体
                        if entity1_name in entities and entity2_name in entities:
                            entity1_id, entity1_type = entities[entity1_name]
                            entity2_id, entity2_type = entities[entity2_name]

                            # 检查实体类型是否匹配
                            types_match = any(
                                (entity1_type == t1 and entity2_type == t2) or
                                (entity1_type == t2 and entity2_type == t1)
                                for t1, t2 in rule['entity_types']
                            )

                            if types_match:
                                relations.append({
                                    'source_entity_id': entity1_id,
                                    'target_entity_id': entity2_id,
                                    'relation_type': relation_type,
                                    'confidence': 85,
                                    'chunk_id': chunk_id,
                                    'source': 'pattern_match'
                                })

        return relations

    def _infer_relation_type(self, type1: str, type2: str) -> Optional[str]:
        """根据实体类型推断关系类型"""
        types = tuple(sorted([type1, type2]))

        relation_map = {
            ('CulturalAsset', 'Location'): 'located_in',
            ('Event', 'Location'): 'occurs_at',
            ('Location', 'Person'): 'lives_in',
            ('CulturalAsset', 'Person'): 'inherits',
            ('Event', 'Person'): 'participates_in',
            ('Organization', 'Person'): 'member_of',
            ('CulturalAsset', 'Policy'): 'protected_by',
            ('Organization', 'CulturalAsset'): 'manages',
        }

        return relation_map.get(types, 'related_to')

    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """去重和合并关系"""
        # 使用 (source, target, type) 作为键
        unique_map = {}

        for rel in relations:
            key = (rel['source_entity_id'], rel['target_entity_id'], rel['relation_type'])

            if key not in unique_map:
                unique_map[key] = rel
            else:
                # 保留置信度更高的
                if rel['confidence'] > unique_map[key]['confidence']:
                    unique_map[key] = rel

        return list(unique_map.values())

    def _save_relations(self, conn: sqlite3.Connection, relations: List[Dict]) -> int:
        """保存关系到数据库"""
        cursor = conn.cursor()

        saved_count = 0

        for rel in relations:
            try:
                # chunk_id字段可能不存在，跳过它
                cursor.execute("""
                    INSERT OR IGNORE INTO entity_relations
                    (source_entity_id, target_entity_id, relation_type,
                     confidence, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    rel['source_entity_id'],
                    rel['target_entity_id'],
                    rel['relation_type'],
                    rel['confidence'],
                    datetime.utcnow()
                ))

                if cursor.rowcount > 0:
                    saved_count += 1

            except Exception as e:
                logger.warning(f"保存关系失败: {e}")

        conn.commit()
        return saved_count


def main():
    """主流程"""
    logger.info("="*60)
    logger.info("增强关系抽取")
    logger.info("="*60)

    extractor = EnhancedRelationExtractor()

    # 清空现有关系（可选）
    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM entity_relations")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        logger.info(f"\n当前数据库中有 {existing_count} 条关系")
        user_input = input("是否清空并重新抽取？(y/n): ")
        if user_input.lower() == 'y':
            cursor.execute("DELETE FROM entity_relations")
            conn.commit()
            logger.info("✅ 已清空现有关系")

    conn.close()

    # 提取关系
    total_relations = extractor.extract_all_relations()

    logger.info("\n" + "="*60)
    logger.info(f"✅ 关系抽取完成，共 {total_relations} 条关系")
    logger.info("="*60)


if __name__ == "__main__":
    main()
