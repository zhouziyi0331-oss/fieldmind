"""
Entity Extraction Service - 实体抽取服务

从文本中抽取实体：
1. 人物（Person）
2. 地点（Location）
3. 文化资产（CulturalAsset）
4. 事件（Event）
5. 政策（Policy）
6. 组织（Organization）

使用混合方法：规则 + NLP
"""

import re
import logging
import sqlite3
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import jieba

from app.core.database import get_sqlite_database_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityExtractionService:
    """实体抽取服务"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化服务

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or get_sqlite_database_path()

        # 人物模式
        self.person_patterns = [
            r'([王李张刘陈杨黄吴赵周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤]+)(大爷|奶奶|师傅|老师|村长|主任|书记|先生|女士|同志)',
            r'([王李张刘陈杨黄吴赵周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤]+[一-龥]{1,2})(说|讲|认为|表示|告诉)',
        ]

        # 地点模式
        self.location_patterns = [
            r'([一-龥]{2,8})(村|寨|镇|乡|县|市|省)',
            r'(贵州|云南|四川|广西|湖南|重庆)',
        ]

        # 文化资产模式
        self.cultural_asset_patterns = [
            r'([一-龥]{2,8})(山歌|民歌|舞蹈|刺绣|蜡染|织布|建筑|节日|节庆|技艺|工艺|手艺)',
            r'(非遗|非物质文化遗产|传统技艺|传统文化)',
        ]

        # 事件模式
        self.event_patterns = [
            r'([一-龥]{2,8})(节|庆|会|活动)',
            r'(六月六|三月三|春节|端午|中秋)',
        ]

        # 政策模式
        self.policy_patterns = [
            r'([一-龥]{4,20})(政策|文件|规定|办法|条例|通知)',
            r'(乡村振兴|精准扶贫|文化保护|非遗保护)',
        ]

        # 组织模式
        self.organization_patterns = [
            r'([一-龥]{2,10})(委员会|协会|合作社|公司|中心|办公室)',
            r'(村委会|乡政府|县政府)',
        ]

    def extract_from_chunk(self, chunk_id: int, chunk_text: str, document_id: str = None) -> List[Dict[str, Any]]:
        """
        从 chunk 中抽取实体

        Args:
            chunk_id: chunk ID
            chunk_text: chunk 文本
            document_id: 文档 ID

        Returns:
            实体列表
        """
        entities = []

        # 1. 抽取人物
        for pattern in self.person_patterns:
            matches = re.finditer(pattern, chunk_text)
            for match in matches:
                name = match.group(1) if match.lastindex >= 1 else match.group(0)
                entities.append({
                    'entity_type': 'Person',
                    'name': name,
                    'confidence': 0.85,
                    'source': 'rule',
                    'context': chunk_text[max(0, match.start()-20):min(len(chunk_text), match.end()+20)]
                })

        # 2. 抽取地点
        for pattern in self.location_patterns:
            matches = re.finditer(pattern, chunk_text)
            for match in matches:
                name = match.group(0)
                entities.append({
                    'entity_type': 'Location',
                    'name': name,
                    'confidence': 0.90,
                    'source': 'rule',
                    'context': chunk_text[max(0, match.start()-20):min(len(chunk_text), match.end()+20)]
                })

        # 3. 抽取文化资产
        for pattern in self.cultural_asset_patterns:
            matches = re.finditer(pattern, chunk_text)
            for match in matches:
                name = match.group(0)
                entities.append({
                    'entity_type': 'CulturalAsset',
                    'name': name,
                    'confidence': 0.80,
                    'source': 'rule',
                    'context': chunk_text[max(0, match.start()-20):min(len(chunk_text), match.end()+20)]
                })

        # 4. 抽取事件
        for pattern in self.event_patterns:
            matches = re.finditer(pattern, chunk_text)
            for match in matches:
                name = match.group(0)
                entities.append({
                    'entity_type': 'Event',
                    'name': name,
                    'confidence': 0.75,
                    'source': 'rule',
                    'context': chunk_text[max(0, match.start()-20):min(len(chunk_text), match.end()+20)]
                })

        # 5. 抽取政策
        for pattern in self.policy_patterns:
            matches = re.finditer(pattern, chunk_text)
            for match in matches:
                name = match.group(0)
                entities.append({
                    'entity_type': 'Policy',
                    'name': name,
                    'confidence': 0.85,
                    'source': 'rule',
                    'context': chunk_text[max(0, match.start()-20):min(len(chunk_text), match.end()+20)]
                })

        # 6. 抽取组织
        for pattern in self.organization_patterns:
            matches = re.finditer(pattern, chunk_text)
            for match in matches:
                name = match.group(0)
                entities.append({
                    'entity_type': 'Organization',
                    'name': name,
                    'confidence': 0.80,
                    'source': 'rule',
                    'context': chunk_text[max(0, match.start()-20):min(len(chunk_text), match.end()+20)]
                })

        # 去重（相同名称的实体）
        unique_entities = {}
        for entity in entities:
            key = (entity['entity_type'], entity['name'])
            if key not in unique_entities or unique_entities[key]['confidence'] < entity['confidence']:
                unique_entities[key] = entity

        return list(unique_entities.values())

    def save_entities_to_db(self, entities: List[Dict[str, Any]], chunk_id: int, document_id: str = None):
        """
        保存实体到数据库

        Args:
            entities: 实体列表
            chunk_id: chunk ID
            document_id: 文档 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            for entity in entities:
                # 检查实体是否已存在
                cursor.execute("""
                    SELECT id FROM entities WHERE name = ? AND entity_type = ?
                """, (entity['name'], entity['entity_type']))

                existing = cursor.fetchone()

                if existing:
                    entity_id = existing[0]

                    # 更新 mention_count
                    cursor.execute("""
                        UPDATE entities
                        SET mention_count = mention_count + 1,
                            updated_at = ?
                        WHERE id = ?
                    """, (datetime.now().isoformat(), entity_id))
                else:
                    # 创建新实体
                    entity_id = str(uuid.uuid4())

                    properties = {
                        'source': entity['source'],
                        'context': entity['context']
                    }

                    cursor.execute("""
                        INSERT INTO entities (
                            id, entity_type, name, properties,
                            confidence, mention_count, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entity_id,
                        entity['entity_type'],
                        entity['name'],
                        str(properties),
                        entity['confidence'],
                        1,
                        datetime.now().isoformat()
                    ))

                # 创建 chunk_entities 关联（如果表存在）
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO chunk_entities
                        (chunk_id, entity_id, confidence, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (chunk_id, entity_id, entity['confidence'] * 100, datetime.now().isoformat()))
                except Exception as e:
                    logger.debug(f"chunk_entities插入跳过: {e}")
                    pass

            conn.commit()
            logger.info(f"✅ 保存了 {len(entities)} 个实体")

        except Exception as e:
            logger.error(f"❌ 保存实体失败: {e}")
            conn.rollback()

        finally:
            conn.close()

    def extract_from_all_chunks(self, project_id: int = None):
        """
        从所有 chunks 中批量抽取实体

        Args:
            project_id: 项目 ID（可选）
        """
        logger.info(f"\n{'='*60}")
        logger.info("批量实体抽取")
        logger.info(f"{'='*60}\n")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取所有 chunks
        if project_id:
            cursor.execute("""
                SELECT id, chunk_text, document_id FROM document_chunks
                WHERE project_id = ?
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT id, chunk_text, document_id FROM document_chunks
            """)

        chunks = cursor.fetchall()
        conn.close()

        logger.info(f"共 {len(chunks)} 个 chunks 待处理")

        total_entities = 0

        for i, (chunk_id, chunk_text, document_id) in enumerate(chunks):
            entities = self.extract_from_chunk(chunk_id, chunk_text, document_id)

            if entities:
                self.save_entities_to_db(entities, chunk_id, document_id)
                total_entities += len(entities)

            if (i + 1) % 10 == 0:
                logger.info(f"进度: {i + 1}/{len(chunks)}")

        logger.info(f"\n{'='*60}")
        logger.info(f"✅ 批量抽取完成")
        logger.info(f"  处理 chunks: {len(chunks)}")
        logger.info(f"  抽取实体: {total_entities}")
        logger.info(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='实体抽取服务')
    parser.add_argument('--db', default='data/fieldmind.db', help='数据库路径')
    parser.add_argument('--project', type=int, help='项目 ID（可选）')

    args = parser.parse_args()

    service = EntityExtractionService(args.db)
    service.extract_from_all_chunks(args.project)


if __name__ == "__main__":
    main()
