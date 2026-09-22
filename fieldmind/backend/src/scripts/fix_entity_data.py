#!/usr/bin/env python3
"""
修复和填充实体关联数据

问题：
1. chunk_entities 表为空
2. entity_relations 表为空

解决方案：
1. 从 entities 表中提取 document_ids，建立 chunk-entity 关联
2. 重新运行关系抽取，填充 entity_relations
"""

import sqlite3
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_chunk_entities(db_path: str = "data/fieldmind.db"):
    """
    填充 chunk_entities 表

    从 entities 表的 document_ids 字段提取信息，
    建立 chunk 和 entity 的关联
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info("\n" + "="*60)
    logger.info("修复 chunk_entities 表")
    logger.info("="*60)

    # 1. 获取所有实体
    cursor.execute("SELECT id, name, entity_type, document_ids FROM entities")
    entities = cursor.fetchall()

    logger.info(f"📊 共 {len(entities)} 个实体")

    # 2. 为每个实体找到对应的chunks
    inserted_count = 0

    for entity in entities:
        entity_id = entity['id']
        name = entity['name']
        entity_type = entity['entity_type']
        document_ids = entity['document_ids']

        # 解析 document_ids (JSON数组)
        try:
            doc_ids = json.loads(document_ids) if document_ids else []
        except:
            doc_ids = []

        if not doc_ids:
            continue

        # 查找这些文档的chunks
        placeholders = ','.join(['?' for _ in doc_ids])
        query = f"""
        SELECT id, document_id
        FROM document_chunks
        WHERE document_id IN ({placeholders})
        """

        cursor.execute(query, doc_ids)
        chunks = cursor.fetchall()

        # 插入 chunk_entities 关联
        for chunk in chunks:
            chunk_id = chunk['id']

            try:
                cursor.execute("""
                INSERT OR IGNORE INTO chunk_entities
                (chunk_id, entity_id, confidence, created_at)
                VALUES (?, ?, ?, ?)
                """, (chunk_id, entity_id, 90, datetime.utcnow()))

                if cursor.rowcount > 0:
                    inserted_count += 1
            except Exception as e:
                logger.warning(f"插入失败: {e}")

    conn.commit()

    # 3. 验证结果
    cursor.execute("SELECT COUNT(*) FROM chunk_entities")
    final_count = cursor.fetchone()[0]

    logger.info(f"✅ 插入了 {inserted_count} 条 chunk-entity 关联")
    logger.info(f"📊 chunk_entities 表总数: {final_count}")

    conn.close()
    return inserted_count


def extract_relations_from_chunks(db_path: str = "data/fieldmind.db"):
    """
    从chunks中提取实体关系

    策略：
    1. 在同一个chunk中出现的实体，建立"mentioned_in"关系
    2. Person-Location: 如果同时出现，建立"located_at"关系
    3. Person-CulturalAsset: 建立"related_to"关系
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info("\n" + "="*60)
    logger.info("提取实体关系")
    logger.info("="*60)

    # 1. 获取所有chunk及其关联的实体
    cursor.execute("""
    SELECT
        ce.chunk_id,
        e.id as entity_id,
        e.name as entity_name,
        e.entity_type
    FROM chunk_entities ce
    JOIN entities e ON ce.entity_id = e.id
    ORDER BY ce.chunk_id
    """)

    chunk_entities = cursor.fetchall()

    # 2. 按chunk分组
    chunks_dict = {}
    for row in chunk_entities:
        chunk_id = row['chunk_id']
        if chunk_id not in chunks_dict:
            chunks_dict[chunk_id] = []

        chunks_dict[chunk_id].append({
            'entity_id': row['entity_id'],
            'name': row['entity_name'],
            'type': row['entity_type']
        })

    logger.info(f"📊 共 {len(chunks_dict)} 个chunks包含实体")

    # 3. 为每个chunk中的实体对创建关系
    inserted_count = 0

    for chunk_id, entities in chunks_dict.items():
        # 每个实体对创建一个关系
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # 确定关系类型
                relation_type = determine_relation_type(
                    entity1['type'],
                    entity2['type']
                )

                if not relation_type:
                    relation_type = "co_occurs_with"

                # 插入关系（双向）
                try:
                    cursor.execute("""
                    INSERT OR IGNORE INTO entity_relations
                    (source_entity_id, target_entity_id, relation_type,
                     confidence, chunk_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        entity1['entity_id'],
                        entity2['entity_id'],
                        relation_type,
                        80,
                        chunk_id,
                        datetime.utcnow()
                    ))

                    if cursor.rowcount > 0:
                        inserted_count += 1

                except Exception as e:
                    logger.warning(f"插入关系失败: {e}")

    conn.commit()

    # 4. 验证结果
    cursor.execute("SELECT COUNT(*) FROM entity_relations")
    final_count = cursor.fetchone()[0]

    logger.info(f"✅ 插入了 {inserted_count} 条关系")
    logger.info(f"📊 entity_relations 表总数: {final_count}")

    # 5. 统计关系类型
    cursor.execute("""
    SELECT relation_type, COUNT(*) as count
    FROM entity_relations
    GROUP BY relation_type
    ORDER BY count DESC
    """)

    logger.info("\n关系类型统计:")
    for row in cursor.fetchall():
        logger.info(f"  {row[0]}: {row[1]}")

    conn.close()
    return inserted_count


def determine_relation_type(type1: str, type2: str) -> str:
    """根据实体类型确定关系类型"""

    # 排序以保证顺序一致
    types = tuple(sorted([type1, type2]))

    relation_map = {
        ('CulturalAsset', 'Location'): 'located_in',
        ('Event', 'Location'): 'occurs_at',
        ('Location', 'Person'): 'lives_in',
        ('CulturalAsset', 'Person'): 'inherits',
        ('Event', 'Person'): 'participates_in',
        ('Organization', 'Person'): 'member_of',
        ('CulturalAsset', 'Policy'): 'protected_by',
    }

    return relation_map.get(types, None)


def verify_data(db_path: str = "data/fieldmind.db"):
    """验证数据完整性"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    logger.info("\n" + "="*60)
    logger.info("数据验证")
    logger.info("="*60)

    # 统计各表数据量
    tables = [
        'entities',
        'document_chunks',
        'chunk_entities',
        'entity_relations'
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        logger.info(f"  {table}: {count}")

    # 检查数据一致性
    cursor.execute("""
    SELECT COUNT(DISTINCT ce.entity_id)
    FROM chunk_entities ce
    """)
    entities_with_chunks = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entities")
    total_entities = cursor.fetchone()[0]

    logger.info(f"\n实体覆盖率: {entities_with_chunks}/{total_entities} " +
                f"({entities_with_chunks*100//total_entities if total_entities > 0 else 0}%)")

    conn.close()


def main():
    """主流程"""
    logger.info("="*60)
    logger.info("数据修复和填充")
    logger.info("="*60)

    db_path = "data/fieldmind.db"

    # 1. 修复 chunk_entities
    fix_chunk_entities(db_path)

    # 2. 提取实体关系
    extract_relations_from_chunks(db_path)

    # 3. 验证数据
    verify_data(db_path)

    logger.info("\n" + "="*60)
    logger.info("✅ 数据修复完成")
    logger.info("="*60)


if __name__ == "__main__":
    main()
