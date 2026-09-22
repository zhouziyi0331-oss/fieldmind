"""
Relation Extraction Service - 关系抽取服务 (独立版本)

从文本中抽取实体间的关系
"""

import re
import logging
import sqlite3
import json
from typing import List, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RelationExtractionService:
    """关系抽取服务"""

    def __init__(self, db_path: str = "data/fieldmind.db"):
        self.db_path = db_path

        # 关系模式定义
        self.relation_patterns = {
            'belongs_to': [
                (r'(\S+?)(是|来自)(\S+?)(村|寨|镇|乡)', 'Person', 'Location', 0.90),
            ],
            'lives_in': [
                (r'(\S+?)(住在|居住在)(\S+?)(村|寨|镇)', 'Person', 'Location', 0.90),
            ],
            'inherits': [
                (r'(\S+?)(传承|继承|会唱|擅长)(\S+?)(山歌|技艺|手艺)', 'Person', 'CulturalAsset', 0.85),
            ],
            'participates_in': [
                (r'(\S+?)(参加|参与)(\S+?)(节|庆|活动)', 'Person', 'Event', 0.85),
            ],
            'occurs_at': [
                (r'(\S+?)(节|庆|活动)(在)(\S+?)(举行|举办)', 'Event', 'Location', 0.90),
            ],
        }

    def create_relation_table(self):
        """创建关系表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entity_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_entity_id VARCHAR(36) NOT NULL,
                    target_entity_id VARCHAR(36) NOT NULL,
                    relation_type VARCHAR(50) NOT NULL,
                    properties JSON,
                    confidence FLOAT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_relations_source
                ON entity_relations(source_entity_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_relations_target
                ON entity_relations(target_entity_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_relations_type
                ON entity_relations(relation_type)
            """)

            conn.commit()
            logger.info("✅ entity_relations 表已创建")

        except Exception as e:
            logger.error(f"❌ 创建表失败: {e}")
            conn.rollback()

        finally:
            conn.close()

    def extract_from_chunk(self, chunk_id: int, chunk_text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从 chunk 中抽取关系"""
        relations = []

        # 为所有实体创建 mentioned_in 关系
        for entity in entities:
            relations.append({
                'source_entity_id': entity['id'],
                'target_entity_id': str(chunk_id),
                'relation_type': 'mentioned_in',
                'confidence': 1.0,
                'context': ''
            })

        return relations

    def save_relations_to_db(self, relations: List[Dict[str, Any]]):
        """保存关系到数据库"""
        if not relations:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            saved_count = 0
            for relation in relations:
                # 检查关系是否已存在
                cursor.execute("""
                    SELECT id FROM entity_relations
                    WHERE source_entity_id = ?
                      AND target_entity_id = ?
                      AND relation_type = ?
                """, (
                    relation['source_entity_id'],
                    relation['target_entity_id'],
                    relation['relation_type']
                ))

                if cursor.fetchone():
                    continue

                # 插入新关系
                properties = {
                    'context': relation.get('context', '')
                }

                cursor.execute("""
                    INSERT INTO entity_relations (
                        source_entity_id, target_entity_id, relation_type,
                        properties, confidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    relation['source_entity_id'],
                    relation['target_entity_id'],
                    relation['relation_type'],
                    json.dumps(properties, ensure_ascii=False),
                    relation['confidence'],
                    datetime.now().isoformat()
                ))
                saved_count += 1

            conn.commit()
            if saved_count > 0:
                logger.info(f"✅ 保存了 {saved_count} 个关系")

        except Exception as e:
            logger.error(f"❌ 保存关系失败: {e}")
            conn.rollback()

        finally:
            conn.close()

    def extract_from_all_chunks(self, project_id: int = None):
        """从所有 chunks 中批量抽取关系"""
        logger.info(f"\n{'='*60}")
        logger.info("批量关系抽取")
        logger.info(f"{'='*60}\n")

        # 确保表存在
        self.create_relation_table()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取所有 chunks
        if project_id:
            cursor.execute("""
                SELECT id, chunk_text FROM document_chunks
                WHERE project_id = ?
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT id, chunk_text FROM document_chunks
            """)

        chunks = cursor.fetchall()
        logger.info(f"共 {len(chunks)} 个 chunks 待处理")

        total_relations = 0

        for i, (chunk_id, chunk_text) in enumerate(chunks):
            # 获取该 chunk 的实体
            cursor.execute("""
                SELECT e.id, e.name, e.entity_type
                FROM entities e
                JOIN chunk_entities ce ON e.id = ce.entity_id
                WHERE ce.chunk_id = ?
            """, (chunk_id,))

            entities = []
            for entity_id, name, entity_type in cursor.fetchall():
                entities.append({
                    'id': entity_id,
                    'name': name,
                    'entity_type': entity_type
                })

            if not entities:
                continue

            # 抽取关系
            relations = self.extract_from_chunk(chunk_id, chunk_text, entities)

            if relations:
                self.save_relations_to_db(relations)
                total_relations += len(relations)

            if (i + 1) % 10 == 0:
                logger.info(f"进度: {i + 1}/{len(chunks)}")

        conn.close()

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ 批量抽取完成")
        logger.info(f"  处理 chunks: {len(chunks)}")
        logger.info(f"  抽取关系: {total_relations}")
        logger.info(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='关系抽取服务')
    parser.add_argument('--db', default='data/fieldmind.db', help='数据库路径')
    parser.add_argument('--project', type=int, help='项目 ID（可选）')

    args = parser.parse_args()

    service = RelationExtractionService(args.db)
    service.extract_from_all_chunks(args.project)


if __name__ == "__main__":
    main()
