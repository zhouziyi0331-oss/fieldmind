"""
Entity Extraction Service - 实体抽取服务
🔥 WorkflowEngine集成 - 阶段1

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
    """
    实体抽取服务
    🔥 支持WorkflowEngine DAG执行
    """

    def __init__(self, db_path: Optional[str] = None, use_workflow_engine: bool = True):
        """
        初始化服务

        Args:
            db_path: 数据库路径
            use_workflow_engine: 是否使用WorkflowEngine
        """
        self.db_path = db_path or get_sqlite_database_path()
        self.use_workflow_engine = use_workflow_engine  # 🔥 新增

        # 🔥 初始化WorkflowEngine
        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

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

    def process_text(
        self,
        text: str,
        chunk_id: int = None,
        document_id: str = None,
        save_to_db: bool = True,
        use_workflow_engine: bool = None
    ) -> Dict[str, Any]:
        """
        处理文本并提取实体
        🔥 支持WorkflowEngine DAG执行

        Args:
            text: 输入文本
            chunk_id: chunk ID
            document_id: 文档 ID
            save_to_db: 是否保存到数据库
            use_workflow_engine: 是否使用WorkflowEngine（默认使用初始化配置）

        Returns:
            {
                'entities': List[Dict],
                'count': int,
                'by_type': Dict[str, int]
            }
        """
        if use_workflow_engine is None:
            use_workflow_engine = self.use_workflow_engine

        if use_workflow_engine:
            return self._process_with_workflow_engine(
                text=text,
                chunk_id=chunk_id,
                document_id=document_id,
                save_to_db=save_to_db
            )
        else:
            return self._process_traditional(
                text=text,
                chunk_id=chunk_id,
                document_id=document_id,
                save_to_db=save_to_db
            )

    def _process_with_workflow_engine(
        self,
        text: str,
        chunk_id: int,
        document_id: str,
        save_to_db: bool
    ) -> Dict[str, Any]:
        """
        🔥 使用WorkflowEngine处理文本（DAG模式）
        """
        logger.info(f"🔥 [WorkflowEngine] 开始提取实体")

        # 创建工作流
        workflow = self.workflow_engine.create_workflow(
            name=f"entity_extraction_{chunk_id or 'text'}",
            description=f"实体提取流水线"
        )

        # 🔥 Task 1: 提取人物
        self.workflow_engine.add_task(
            workflow,
            name="extract_persons",
            func=self._task_extract_persons,
            kwargs={'text': text},
            dependencies=[]
        )

        # 🔥 Task 2: 提取地点（可与人物并行）
        self.workflow_engine.add_task(
            workflow,
            name="extract_locations",
            func=self._task_extract_locations,
            kwargs={'text': text},
            dependencies=[]
        )

        # 🔥 Task 3: 提取文化资产（可并行）
        self.workflow_engine.add_task(
            workflow,
            name="extract_cultural_assets",
            func=self._task_extract_cultural_assets,
            kwargs={'text': text},
            dependencies=[]
        )

        # 🔥 Task 4: 提取事件（可并行）
        self.workflow_engine.add_task(
            workflow,
            name="extract_events",
            func=self._task_extract_events,
            kwargs={'text': text},
            dependencies=[]
        )

        # 🔥 Task 5: 提取政策（可并行）
        self.workflow_engine.add_task(
            workflow,
            name="extract_policies",
            func=self._task_extract_policies,
            kwargs={'text': text},
            dependencies=[]
        )

        # 🔥 Task 6: 提取组织（可并行）
        self.workflow_engine.add_task(
            workflow,
            name="extract_organizations",
            func=self._task_extract_organizations,
            kwargs={'text': text},
            dependencies=[]
        )

        # 🔥 Task 7: 合并去重
        self.workflow_engine.add_task(
            workflow,
            name="merge",
            func=self._task_merge_entities,
            kwargs={
                'persons': '$extract_persons.entities',
                'locations': '$extract_locations.entities',
                'cultural_assets': '$extract_cultural_assets.entities',
                'events': '$extract_events.entities',
                'policies': '$extract_policies.entities',
                'organizations': '$extract_organizations.entities'
            },
            dependencies=[
                "extract_persons",
                "extract_locations",
                "extract_cultural_assets",
                "extract_events",
                "extract_policies",
                "extract_organizations"
            ]
        )

        # 🔥 Task 8: 保存到数据库（条件执行）
        if save_to_db and chunk_id:
            self.workflow_engine.add_task(
                workflow,
                name="save_db",
                func=self._task_save_to_db,
                kwargs={
                    'entities': '$merge.entities',
                    'chunk_id': chunk_id,
                    'document_id': document_id
                },
                dependencies=["merge"]
            )

        # 执行工作流
        results = self.workflow_engine.execute(workflow)

        logger.info(f"✅ [WorkflowEngine] 实体提取完成")
        return results['merge']

    def _process_traditional(
        self,
        text: str,
        chunk_id: int,
        document_id: str,
        save_to_db: bool
    ) -> Dict[str, Any]:
        """
        传统顺序处理模式（向后兼容）
        """
        logger.info(f"📝 [传统模式] 开始提取实体")

        # 提取实体
        entities = self.extract_from_chunk(chunk_id or 0, text, document_id)

        # 保存到数据库
        if save_to_db and chunk_id and entities:
            self.save_entities_to_db(entities, chunk_id, document_id)

        # 统计
        by_type = {}
        for entity in entities:
            entity_type = entity['entity_type']
            by_type[entity_type] = by_type.get(entity_type, 0) + 1

        return {
            'entities': entities,
            'count': len(entities),
            'by_type': by_type
        }

    # ========================================
    # 🔥 WorkflowEngine Task Functions
    # ========================================

    def _task_extract_persons(self, text: str, _context: dict) -> dict:
        """🔥 Task 1: 提取人物"""
        logger.info(f"  [Task] extract_persons")
        entities = []
        for pattern in self.person_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1) if match.lastindex >= 1 else match.group(0)
                entities.append({
                    'entity_type': 'Person',
                    'name': name,
                    'confidence': 0.85,
                    'source': 'rule',
                    'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
                })
        logger.info(f"  ✅ extract_persons: {len(entities)} 个")
        return {'entities': entities}

    def _task_extract_locations(self, text: str, _context: dict) -> dict:
        """🔥 Task 2: 提取地点"""
        logger.info(f"  [Task] extract_locations")
        entities = []
        for pattern in self.location_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'entity_type': 'Location',
                    'name': match.group(0),
                    'confidence': 0.90,
                    'source': 'rule',
                    'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
                })
        logger.info(f"  ✅ extract_locations: {len(entities)} 个")
        return {'entities': entities}

    def _task_extract_cultural_assets(self, text: str, _context: dict) -> dict:
        """🔥 Task 3: 提取文化资产"""
        logger.info(f"  [Task] extract_cultural_assets")
        entities = []
        for pattern in self.cultural_asset_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'entity_type': 'CulturalAsset',
                    'name': match.group(0),
                    'confidence': 0.80,
                    'source': 'rule',
                    'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
                })
        logger.info(f"  ✅ extract_cultural_assets: {len(entities)} 个")
        return {'entities': entities}

    def _task_extract_events(self, text: str, _context: dict) -> dict:
        """🔥 Task 4: 提取事件"""
        logger.info(f"  [Task] extract_events")
        entities = []
        for pattern in self.event_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'entity_type': 'Event',
                    'name': match.group(0),
                    'confidence': 0.75,
                    'source': 'rule',
                    'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
                })
        logger.info(f"  ✅ extract_events: {len(entities)} 个")
        return {'entities': entities}

    def _task_extract_policies(self, text: str, _context: dict) -> dict:
        """🔥 Task 5: 提取政策"""
        logger.info(f"  [Task] extract_policies")
        entities = []
        for pattern in self.policy_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'entity_type': 'Policy',
                    'name': match.group(0),
                    'confidence': 0.85,
                    'source': 'rule',
                    'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
                })
        logger.info(f"  ✅ extract_policies: {len(entities)} 个")
        return {'entities': entities}

    def _task_extract_organizations(self, text: str, _context: dict) -> dict:
        """🔥 Task 6: 提取组织"""
        logger.info(f"  [Task] extract_organizations")
        entities = []
        for pattern in self.organization_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    'entity_type': 'Organization',
                    'name': match.group(0),
                    'confidence': 0.80,
                    'source': 'rule',
                    'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
                })
        logger.info(f"  ✅ extract_organizations: {len(entities)} 个")
        return {'entities': entities}

    def _task_merge_entities(self, persons: list, locations: list, cultural_assets: list,
                            events: list, policies: list, organizations: list,
                            _context: dict) -> dict:
        """🔥 Task 7: 合并去重"""
        logger.info(f"  [Task] merge: 合并所有实体")

        all_entities = persons + locations + cultural_assets + events + policies + organizations

        # 去重
        unique_entities = {}
        for entity in all_entities:
            key = (entity['entity_type'], entity['name'])
            if key not in unique_entities or unique_entities[key]['confidence'] < entity['confidence']:
                unique_entities[key] = entity

        entities = list(unique_entities.values())

        # 统计
        by_type = {}
        for entity in entities:
            entity_type = entity['entity_type']
            by_type[entity_type] = by_type.get(entity_type, 0) + 1

        logger.info(f"  ✅ merge: {len(entities)} 个唯一实体")
        return {
            'entities': entities,
            'count': len(entities),
            'by_type': by_type
        }

    def _task_save_to_db(self, entities: list, chunk_id: int, document_id: str, _context: dict) -> dict:
        """🔥 Task 8: 保存到数据库"""
        logger.info(f"  [Task] save_db: 保存 {len(entities)} 个实体")

        self.save_entities_to_db(entities, chunk_id, document_id)

        logger.info(f"  ✅ save_db: 保存完成")
        return {'saved': True, 'count': len(entities)}



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
