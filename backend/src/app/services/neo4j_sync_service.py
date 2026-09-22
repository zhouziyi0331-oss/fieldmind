"""
Week 3 - Day 1: 实现 Neo4j 同步服务
订阅 PostgreSQL 事件，自动同步到 Neo4j
"""

import sqlite3
from typing import Dict, Optional
import logging

# 由于可能没有安装 neo4j，我们先创建一个模拟版本用于测试
# 实际部署时需要: pip install neo4j

logger = logging.getLogger(__name__)


class Neo4jSyncService:
    """
    Neo4j 同步服务

    功能：
    1. 订阅 entity.created/updated/deleted 事件
    2. 订阅 relation.created 事件
    3. 同步数据到 Neo4j
    4. 支持全量重建
    """
    def __init__(self, db_path: str,
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "password",
                 use_mock: bool = False, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化同步服务

        Args:
            db_path: SQLite 数据库路径
            neo4j_uri: Neo4j 连接地址
            neo4j_user: Neo4j 用户名
            neo4j_password: Neo4j 密码
            use_mock: 是否使用模拟模式（用于测试）
        """
        self.db_path = db_path
        self.use_mock = use_mock
        self.sync_stats = {
            "entities_synced": 0,
            "relations_synced": 0,
            "errors": 0
        }

        if not use_mock:
            try:
                from neo4j import GraphDatabase
                self.driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password)
                )
                logger.info(f"已连接到 Neo4j: {neo4j_uri}")
            except ImportError:
                logger.warning("neo4j 包未安装，使用模拟模式")
                self.use_mock = True
                self.driver = None
        else:
            self.driver = None
            logger.info("使用 Neo4j 模拟模式")

    def register_event_handlers(self, event_bus):
        """注册事件处理器"""
        from app.core.event_bus import Event

        @event_bus.on("entity.created")
        def on_entity_created(event: Event):
            self.sync_entity_create(event.data)

        @event_bus.on("entity.updated")
        def on_entity_updated(event: Event):
            self.sync_entity_update(event.data)

        @event_bus.on("entity.deleted")
        def on_entity_deleted(event: Event):
            self.sync_entity_delete(event.data)

        @event_bus.on("relation.created")
        def on_relation_created(event: Event):
            self.sync_relation_create(event.data)

        logger.info("已注册 Neo4j 同步事件处理器")

    def sync_entity_create(self, data: Dict) -> bool:
        """同步实体创建事件"""
        try:
            entity_id = data.get("entity_id")
            name = data.get("name")
            entity_type = data.get("type")

            logger.info(f"同步实体创建到 Neo4j: {entity_id} - {name}")

            if self.use_mock:
                # 模拟模式：只记录日志
                logger.debug(f"[MOCK] 创建节点: ({entity_type} {{id: '{entity_id}', name: '{name}'}})")
            else:
                # 实际执行
                with self.driver.session() as session:
                    session.run("""
                        CREATE (e:Entity {
                            id: $id,
                            name: $name,
                            type: $type,
                            mention_count: $mention_count,
                            sentiment_avg: $sentiment_avg,
                            importance_score: $importance_score,
                            created_at: datetime()
                        })
                    """,
                        id=entity_id,
                        name=name,
                        type=entity_type,
                        mention_count=data.get("mention_count", 0),
                        sentiment_avg=data.get("sentiment_avg", 0.0),
                        importance_score=data.get("importance_score", 0.0)
                    )

            # 更新 SQLite 同步状态
            self._update_sync_status(entity_id)

            self.sync_stats["entities_synced"] += 1
            return True

        except Exception as e:
            logger.error(f"同步实体创建失败: {e}")
            self.sync_stats["errors"] += 1
            return False

    def sync_entity_update(self, data: Dict) -> bool:
        """同步实体更新事件"""
        try:
            entity_id = data.get("entity_id")
            logger.info(f"同步实体更新到 Neo4j: {entity_id}")

            if self.use_mock:
                logger.debug(f"[MOCK] 更新节点: {entity_id}")
            else:
                with self.driver.session() as session:
                    # 构建动态更新语句
                    set_clauses = []
                    params = {"id": entity_id}

                    for key in ["name", "mention_count", "sentiment_avg", "importance_score"]:
                        if key in data:
                            set_clauses.append(f"e.{key} = ${key}")
                            params[key] = data[key]

                    if set_clauses:
                        query = f"""
                            MATCH (e:Entity {{id: $id}})
                            SET {', '.join(set_clauses)},
                                e.updated_at = datetime()
                        """
                        session.run(query, **params)

            return True

        except Exception as e:
            logger.error(f"同步实体更新失败: {e}")
            self.sync_stats["errors"] += 1
            return False

    def sync_entity_delete(self, data: Dict) -> bool:
        """同步实体删除事件"""
        try:
            entity_id = data.get("entity_id")
            logger.info(f"同步实体删除到 Neo4j: {entity_id}")

            if self.use_mock:
                logger.debug(f"[MOCK] 删除节点: {entity_id}")
            else:
                with self.driver.session() as session:
                    session.run("""
                        MATCH (e:Entity {id: $id})
                        DETACH DELETE e
                    """, id=entity_id)

            return True

        except Exception as e:
            logger.error(f"同步实体删除失败: {e}")
            self.sync_stats["errors"] += 1
            return False

    def sync_relation_create(self, data: Dict) -> bool:
        """同步关系创建事件"""
        try:
            relation_id = data.get("relation_id")
            source_id = data.get("source_entity_id")
            target_id = data.get("target_entity_id")
            relation_type = data.get("type", "RELATED_TO")

            logger.info(f"同步关系创建到 Neo4j: {source_id} -> {target_id}")

            if self.use_mock:
                logger.debug(f"[MOCK] 创建关系: ({source_id})-[:{relation_type}]->({target_id})")
            else:
                with self.driver.session() as session:
                    session.run("""
                        MATCH (e1:Entity {id: $source_id})
                        MATCH (e2:Entity {id: $target_id})
                        CREATE (e1)-[r:RELATION {
                            id: $relation_id,
                            type: $type,
                            weight: $weight,
                            created_at: datetime()
                        }]->(e2)
                    """,
                        source_id=source_id,
                        target_id=target_id,
                        relation_id=relation_id,
                        type=relation_type,
                        weight=data.get("weight", 1.0)
                    )

            self.sync_stats["relations_synced"] += 1
            return True

        except Exception as e:
            logger.error(f"同步关系创建失败: {e}")
            self.sync_stats["errors"] += 1
            return False

    def _update_sync_status(self, entity_id: str):
        """更新 SQLite 中的同步状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE entities
                SET synced_to_neo4j = TRUE,
                    neo4j_synced_at = CURRENT_TIMESTAMP
                WHERE entity_id = ?
            """, (entity_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"更新同步状态失败: {e}")

    def rebuild_from_postgres(self) -> Dict:
        """
        从 PostgreSQL/SQLite 完全重建 Neo4j

        Returns:
            重建统计信息
        """
        logger.info("开始从 SQLite 重建 Neo4j...")

        stats = {
            "entities_rebuilt": 0,
            "relations_rebuilt": 0,
            "errors": []
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. 清空 Neo4j
            logger.info("步骤 1: 清空 Neo4j")
            if not self.use_mock:
                with self.driver.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
            else:
                logger.debug("[MOCK] 清空所有节点")

            # 2. 同步所有实体
            logger.info("步骤 2: 同步所有实体")
            cursor.execute("""
                SELECT entity_id, name, type, mention_count,
                       sentiment_avg, importance_score
                FROM entities
                WHERE entity_id IS NOT NULL
            """)

            entities = cursor.fetchall()
            logger.info(f"找到 {len(entities)} 个实体")

            for entity in entities:
                entity_id, name, e_type, mention_count, sentiment_avg, importance_score = entity

                success = self.sync_entity_create({
                    "entity_id": entity_id,
                    "name": name,
                    "type": e_type,
                    "mention_count": mention_count or 0,
                    "sentiment_avg": sentiment_avg or 0.0,
                    "importance_score": importance_score or 0.0
                })

                if success:
                    stats["entities_rebuilt"] += 1

            # 3. 同步所有关系
            logger.info("步骤 3: 同步所有关系")
            cursor.execute("""
                SELECT id, source_entity_id, target_entity_id,
                       relation_type, weight
                FROM entity_relations
                WHERE source_entity_id IS NOT NULL
                  AND target_entity_id IS NOT NULL
            """)

            relations = cursor.fetchall()
            logger.info(f"找到 {len(relations)} 个关系")

            for relation in relations:
                rel_id, source_id, target_id, rel_type, weight = relation

                success = self.sync_relation_create({
                    "relation_id": str(rel_id),
                    "source_entity_id": source_id,
                    "target_entity_id": target_id,
                    "type": rel_type or "RELATED_TO",
                    "weight": weight or 1.0
                })

                if success:
                    stats["relations_rebuilt"] += 1

            conn.close()

            logger.info(f"✅ Neo4j 重建完成: {stats['entities_rebuilt']} 个实体, {stats['relations_rebuilt']} 个关系")

        except Exception as e:
            logger.error(f"重建失败: {e}")
            stats["errors"].append(str(e))

        return stats

    def get_stats(self) -> Dict:
        """获取同步统计信息"""
        return self.sync_stats.copy()

    def close(self):
        """关闭连接"""
        if self.driver and not self.use_mock:
            self.driver.close()
            logger.info("已关闭 Neo4j 连接")


# ===== 测试代码 =====

def test_neo4j_sync():
    """测试 Neo4j 同步服务"""
    import sys
    from pathlib import Path

    # 添加路径
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from app.core.event_bus import get_event_bus

    print("=" * 60)
    print("测试 Neo4j 同步服务")
    print("=" * 60)

    # 创建事件总线
    event_bus = get_event_bus()

    # 创建同步服务（模拟模式）
    db_path = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
    sync_service = Neo4jSyncService(db_path, use_mock=True)

    # 注册事件处理器
    sync_service.register_event_handlers(event_bus)

    # 测试实体创建
    print("\n测试 1: 实体创建事件")
    event_bus.publish("entity.created", {
        "entity_id": "ent_test123456",
        "name": "测试实体",
        "type": "person",
        "mention_count": 5,
        "sentiment_avg": 0.8,
        "importance_score": 0.9
    }, source="test")

    # 测试实体更新
    print("\n测试 2: 实体更新事件")
    event_bus.publish("entity.updated", {
        "entity_id": "ent_test123456",
        "mention_count": 10,
        "sentiment_avg": 0.85
    }, source="test")

    # 测试关系创建
    print("\n测试 3: 关系创建事件")
    event_bus.publish("relation.created", {
        "relation_id": "rel_test123456",
        "source_entity_id": "ent_test123456",
        "target_entity_id": "ent_another123",
        "type": "KNOWS",
        "weight": 0.9
    }, source="test")

    # 等待异步处理
    import time
    time.sleep(0.5)

    # 显示统计
    print("\n同步统计:")
    stats = sync_service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ Neo4j 同步服务测试完成")


def test_rebuild():
    """测试完全重建"""
    print("\n" + "=" * 60)
    print("测试 Neo4j 完全重建")
    print("=" * 60)

    db_path = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
    sync_service = Neo4jSyncService(db_path, use_mock=True)

    # 执行重建
    stats = sync_service.rebuild_from_postgres()

    print("\n重建统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ 重建测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_neo4j_sync()
    test_rebuild()
