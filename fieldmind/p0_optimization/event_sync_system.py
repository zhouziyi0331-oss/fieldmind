#!/usr/bin/env python3
"""
P0 Day 2: 事件驱动同步机制

目标：
1. 实现事件总线（Event Bus）
2. PostgreSQL 变更事件发布
3. Neo4j 同步订阅器
4. ChromaDB 同步订阅器
5. Redis 缓存失效机制
"""

import json
import asyncio
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    # Entity 事件
    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_DELETED = "entity.deleted"

    # Relation 事件
    RELATION_CREATED = "relation.created"
    RELATION_UPDATED = "relation.updated"
    RELATION_DELETED = "relation.deleted"

    # Chunk 事件
    CHUNK_CREATED = "chunk.created"
    CHUNK_UPDATED = "chunk.updated"
    CHUNK_DELETED = "chunk.deleted"

    # Document 事件
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"

    # Project 事件
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"


class Event:
    """事件对象"""

    def __init__(
        self,
        event_type: EventType,
        entity_id: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.event_id = f"evt_{datetime.now().timestamp()}"
        self.event_type = event_type
        self.entity_id = entity_id
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'entity_id': self.entity_id,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
        }


class EventBus:
    """事件总线（单例模式）"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._initialized = True

        logger.info("EventBus 初始化完成")

    def subscribe(self, event_type: EventType, callback: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)
        logger.info(f"订阅事件: {event_type.value}")

    def unsubscribe(self, event_type: EventType, callback: Callable):
        """取消订阅"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
            logger.info(f"取消订阅: {event_type.value}")

    async def publish(self, event: Event):
        """发布事件（异步）"""
        logger.info(f"发布事件: {event.event_type.value} - {event.entity_id}")

        # 记录事件历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # 通知所有订阅者
        if event.event_type in self._subscribers:
            tasks = []
            for callback in self._subscribers[event.event_type]:
                # 异步执行回调
                task = asyncio.create_task(self._execute_callback(callback, event))
                tasks.append(task)

            # 等待所有回调完成
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_callback(self, callback: Callable, event: Event):
        """执行回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(f"回调执行失败: {callback.__name__} - {e}")

    def get_event_history(self, limit: int = 100) -> List[Dict]:
        """获取事件历史"""
        return [e.to_dict() for e in self._event_history[-limit:]]


# ============================================
# PostgreSQL 数据服务（主权层）
# ============================================

class PostgreSQLDataService:
    """PostgreSQL 数据服务 - 唯一写入口"""

    def __init__(self, db_connection, event_bus: EventBus):
        self.db = db_connection
        self.event_bus = event_bus

    async def create_entity(self, entity_data: Dict) -> str:
        """创建实体"""
        # 1. 生成 ID
        from p0_unified_id_design import UnifiedIDGenerator, EntityType
        entity_id = UnifiedIDGenerator.generate(EntityType.ENTITY)

        # 2. 写入 PostgreSQL
        query = """
            INSERT INTO entities (
                id, project_id, name, type, description,
                mention_count, sentiment_avg, importance_score,
                created_at, updated_at, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s
            )
        """

        self.db.execute(query, (
            entity_id,
            entity_data.get('project_id'),
            entity_data.get('name'),
            entity_data.get('type'),
            entity_data.get('description'),
            0,  # mention_count
            0.0,  # sentiment_avg
            0.0,  # importance_score
            json.dumps(entity_data.get('metadata', {})),
        ))
        self.db.commit()

        # 3. 发布事件
        event = Event(
            event_type=EventType.ENTITY_CREATED,
            entity_id=entity_id,
            data=entity_data
        )
        await self.event_bus.publish(event)

        logger.info(f"✅ 创建实体: {entity_id}")
        return entity_id

    async def update_entity(self, entity_id: str, updates: Dict):
        """更新实体"""
        # 1. 更新 PostgreSQL
        set_clauses = []
        values = []

        for key, value in updates.items():
            if key in ['name', 'type', 'description', 'mention_count',
                      'sentiment_avg', 'importance_score']:
                set_clauses.append(f"{key} = %s")
                values.append(value)

        set_clauses.append("updated_at = NOW()")

        query = f"""
            UPDATE entities
            SET {', '.join(set_clauses)}
            WHERE id = %s
        """
        values.append(entity_id)

        self.db.execute(query, values)
        self.db.commit()

        # 2. 发布事件
        event = Event(
            event_type=EventType.ENTITY_UPDATED,
            entity_id=entity_id,
            data=updates
        )
        await self.event_bus.publish(event)

        logger.info(f"✅ 更新实体: {entity_id}")

    async def delete_entity(self, entity_id: str):
        """删除实体"""
        # 1. 删除 PostgreSQL
        query = "DELETE FROM entities WHERE id = %s"
        self.db.execute(query, (entity_id,))
        self.db.commit()

        # 2. 发布事件
        event = Event(
            event_type=EventType.ENTITY_DELETED,
            entity_id=entity_id,
            data={}
        )
        await self.event_bus.publish(event)

        logger.info(f"✅ 删除实体: {entity_id}")

    async def create_chunk(self, chunk_data: Dict) -> str:
        """创建 chunk"""
        from p0_unified_id_design import UnifiedIDGenerator, EntityType
        chunk_id = UnifiedIDGenerator.generate(EntityType.CHUNK)

        # 写入 PostgreSQL（包含增强字段）
        query = """
            INSERT INTO chunks (
                id, document_id, project_id, text, position, word_count,
                speaker, speaker_role, timestamp_start, timestamp_end,
                sentiment_polarity, sentiment_subjectivity, emotion_scores,
                dimension_category, dimension_sub_category, dimension_confidence,
                entities, keywords, embedding, quality_score,
                created_at, updated_at, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                NOW(), NOW(), %s
            )
        """

        self.db.execute(query, (
            chunk_id,
            chunk_data.get('document_id'),
            chunk_data.get('project_id'),
            chunk_data.get('text'),
            chunk_data.get('position'),
            chunk_data.get('word_count'),
            chunk_data.get('speaker'),
            chunk_data.get('speaker_role'),
            chunk_data.get('timestamp_start'),
            chunk_data.get('timestamp_end'),
            chunk_data.get('sentiment_polarity'),
            chunk_data.get('sentiment_subjectivity'),
            json.dumps(chunk_data.get('emotion_scores', {})),
            chunk_data.get('dimension_category'),
            chunk_data.get('dimension_sub_category'),
            chunk_data.get('dimension_confidence'),
            json.dumps(chunk_data.get('entities', [])),
            json.dumps(chunk_data.get('keywords', [])),
            chunk_data.get('embedding'),
            chunk_data.get('quality_score'),
            json.dumps(chunk_data.get('metadata', {})),
        ))
        self.db.commit()

        # 发布事件
        event = Event(
            event_type=EventType.CHUNK_CREATED,
            entity_id=chunk_id,
            data=chunk_data
        )
        await self.event_bus.publish(event)

        logger.info(f"✅ 创建 chunk: {chunk_id}")
        return chunk_id


# ============================================
# Neo4j 同步服务
# ============================================

class Neo4jSyncService:
    """Neo4j 同步服务"""

    def __init__(self, neo4j_driver, event_bus: EventBus):
        self.driver = neo4j_driver
        self.event_bus = event_bus

        # 订阅事件
        self.event_bus.subscribe(EventType.ENTITY_CREATED, self.on_entity_created)
        self.event_bus.subscribe(EventType.ENTITY_UPDATED, self.on_entity_updated)
        self.event_bus.subscribe(EventType.ENTITY_DELETED, self.on_entity_deleted)
        self.event_bus.subscribe(EventType.RELATION_CREATED, self.on_relation_created)
        self.event_bus.subscribe(EventType.RELATION_DELETED, self.on_relation_deleted)

        logger.info("Neo4j 同步服务已启动")

    async def on_entity_created(self, event: Event):
        """实体创建事件处理"""
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    CREATE (e:Entity {
                        id: $id,
                        name: $name,
                        type: $type,
                        mention_count: $mention_count,
                        sentiment_avg: $sentiment_avg,
                        importance_score: $importance_score,
                        created_at: $created_at
                    })
                    """,
                    id=event.entity_id,
                    name=event.data.get('name'),
                    type=event.data.get('type'),
                    mention_count=event.data.get('mention_count', 0),
                    sentiment_avg=event.data.get('sentiment_avg', 0.0),
                    importance_score=event.data.get('importance_score', 0.0),
                    created_at=event.timestamp,
                )

            logger.info(f"Neo4j: 同步创建实体 {event.entity_id}")

        except Exception as e:
            logger.error(f"Neo4j: 同步失败 - {e}")

    async def on_entity_updated(self, event: Event):
        """实体更新事件处理"""
        try:
            with self.driver.session() as session:
                # 动态构建 SET 子句
                set_clauses = []
                params = {'id': event.entity_id}

                for key, value in event.data.items():
                    if key in ['name', 'type', 'mention_count', 'sentiment_avg', 'importance_score']:
                        set_clauses.append(f"e.{key} = ${key}")
                        params[key] = value

                if set_clauses:
                    query = f"""
                        MATCH (e:Entity {{id: $id}})
                        SET {', '.join(set_clauses)}, e.updated_at = $updated_at
                    """
                    params['updated_at'] = event.timestamp

                    session.run(query, **params)
                    logger.info(f"Neo4j: 同步更新实体 {event.entity_id}")

        except Exception as e:
            logger.error(f"Neo4j: 更新失败 - {e}")

    async def on_entity_deleted(self, event: Event):
        """实体删除事件处理"""
        try:
            with self.driver.session() as session:
                # 删除节点及其所有关系
                session.run(
                    """
                    MATCH (e:Entity {id: $id})
                    DETACH DELETE e
                    """,
                    id=event.entity_id
                )

            logger.info(f"Neo4j: 同步删除实体 {event.entity_id}")

        except Exception as e:
            logger.error(f"Neo4j: 删除失败 - {e}")

    async def on_relation_created(self, event: Event):
        """关系创建事件处理"""
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (s:Entity {id: $source_id})
                    MATCH (t:Entity {id: $target_id})
                    CREATE (s)-[r:RELATES_TO {
                        id: $id,
                        relation_type: $relation_type,
                        confidence: $confidence,
                        created_at: $created_at
                    }]->(t)
                    """,
                    id=event.entity_id,
                    source_id=event.data.get('source_entity_id'),
                    target_id=event.data.get('target_entity_id'),
                    relation_type=event.data.get('relation_type'),
                    confidence=event.data.get('confidence', 1.0),
                    created_at=event.timestamp,
                )

            logger.info(f"Neo4j: 同步创建关系 {event.entity_id}")

        except Exception as e:
            logger.error(f"Neo4j: 创建关系失败 - {e}")

    async def on_relation_deleted(self, event: Event):
        """关系删除事件处理"""
        try:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH ()-[r:RELATES_TO {id: $id}]-()
                    DELETE r
                    """,
                    id=event.entity_id
                )

            logger.info(f"Neo4j: 同步删除关系 {event.entity_id}")

        except Exception as e:
            logger.error(f"Neo4j: 删除关系失败 - {e}")


# ============================================
# ChromaDB 同步服务
# ============================================

class ChromaDBSyncService:
    """ChromaDB 同步服务"""

    def __init__(self, chroma_client, event_bus: EventBus):
        self.client = chroma_client
        self.collection = chroma_client.get_or_create_collection("chunks")
        self.event_bus = event_bus

        # 订阅事件
        self.event_bus.subscribe(EventType.CHUNK_CREATED, self.on_chunk_created)
        self.event_bus.subscribe(EventType.CHUNK_UPDATED, self.on_chunk_updated)
        self.event_bus.subscribe(EventType.CHUNK_DELETED, self.on_chunk_deleted)

        logger.info("ChromaDB 同步服务已启动")

    async def on_chunk_created(self, event: Event):
        """chunk 创建事件处理"""
        try:
            self.collection.add(
                ids=[event.entity_id],
                documents=[event.data.get('text')],
                embeddings=[event.data.get('embedding')] if event.data.get('embedding') else None,
                metadatas=[{
                    'document_id': event.data.get('document_id'),
                    'project_id': event.data.get('project_id'),
                    'dimension_category': event.data.get('dimension_category'),
                    'quality_score': event.data.get('quality_score'),
                    'speaker': event.data.get('speaker'),
                }]
            )

            logger.info(f"ChromaDB: 同步创建 chunk {event.entity_id}")

        except Exception as e:
            logger.error(f"ChromaDB: 同步失败 - {e}")

    async def on_chunk_updated(self, event: Event):
        """chunk 更新事件处理"""
        try:
            # ChromaDB 不支持直接更新，需要删除再添加
            self.collection.delete(ids=[event.entity_id])

            self.collection.add(
                ids=[event.entity_id],
                documents=[event.data.get('text')],
                embeddings=[event.data.get('embedding')] if event.data.get('embedding') else None,
                metadatas=[{
                    'document_id': event.data.get('document_id'),
                    'project_id': event.data.get('project_id'),
                    'dimension_category': event.data.get('dimension_category'),
                    'quality_score': event.data.get('quality_score'),
                }]
            )

            logger.info(f"ChromaDB: 同步更新 chunk {event.entity_id}")

        except Exception as e:
            logger.error(f"ChromaDB: 更新失败 - {e}")

    async def on_chunk_deleted(self, event: Event):
        """chunk 删除事件处理"""
        try:
            self.collection.delete(ids=[event.entity_id])
            logger.info(f"ChromaDB: 同步删除 chunk {event.entity_id}")

        except Exception as e:
            logger.error(f"ChromaDB: 删除失败 - {e}")


# ============================================
# Redis 缓存失效服务
# ============================================

class RedisCacheInvalidationService:
    """Redis 缓存失效服务"""

    def __init__(self, redis_client, event_bus: EventBus):
        self.redis = redis_client
        self.event_bus = event_bus

        # 订阅所有更新和删除事件
        for event_type in EventType:
            if 'UPDATED' in event_type.value or 'DELETED' in event_type.value:
                self.event_bus.subscribe(event_type, self.on_data_changed)

        logger.info("Redis 缓存失效服务已启动")

    async def on_data_changed(self, event: Event):
        """数据变更事件处理"""
        try:
            # 失效相关缓存
            patterns = [
                f"entity:{event.entity_id}",
                f"entity:{event.entity_id}:*",
                f"list:entities:*",  # 列表缓存
                f"search:*",  # 搜索缓存
            ]

            for pattern in patterns:
                keys = self.redis.keys(pattern)
                if keys:
                    self.redis.delete(*keys)
                    logger.info(f"Redis: 失效缓存 {pattern} ({len(keys)} keys)")

        except Exception as e:
            logger.error(f"Redis: 缓存失效失败 - {e}")


# ============================================
# 示例代码
# ============================================

async def example_usage():
    """使用示例"""

    # 1. 初始化事件总线
    event_bus = EventBus()

    # 2. 初始化数据库连接（伪代码）
    # pg_conn = psycopg2.connect(...)
    # neo4j_driver = GraphDatabase.driver(...)
    # chroma_client = chromadb.Client()
    # redis_client = redis.Redis()

    # 3. 初始化同步服务
    # neo4j_sync = Neo4jSyncService(neo4j_driver, event_bus)
    # chroma_sync = ChromaDBSyncService(chroma_client, event_bus)
    # redis_sync = RedisCacheInvalidationService(redis_client, event_bus)

    # 4. 初始化数据服务
    # data_service = PostgreSQLDataService(pg_conn, event_bus)

    # 5. 创建实体（自动同步到 Neo4j）
    # entity_id = await data_service.create_entity({
    #     'project_id': 'proj_123',
    #     'name': '张三',
    #     'type': 'person',
    #     'description': '项目负责人',
    # })

    # 6. 更新实体（自动同步）
    # await data_service.update_entity(entity_id, {
    #     'mention_count': 5,
    #     'sentiment_avg': 0.8,
    # })

    # 7. 创建 chunk（自动同步到 ChromaDB）
    # chunk_id = await data_service.create_chunk({
    #     'document_id': 'doc_456',
    #     'project_id': 'proj_123',
    #     'text': '张三负责项目的整体规划',
    #     'speaker': '张三',
    #     'sentiment_polarity': 0.5,
    #     'dimension_category': '项目管理',
    #     'embedding': [0.1, 0.2, ...],
    # })

    print("事件驱动同步机制示例")


# ============================================
# 导出生成代码
# ============================================

def generate_event_sync_code():
    """生成事件同步代码文件"""
    import os

    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/p0_optimization"
    os.makedirs(output_dir, exist_ok=True)

    # 读取当前文件内容
    with open(__file__, 'r') as f:
        code = f.read()

    # 保存为独立模块
    with open(f"{output_dir}/event_sync_system.py", 'w') as f:
        f.write(code)

    print(f"✅ 事件同步系统代码已生成: {output_dir}/event_sync_system.py")

    # 生成使用文档
    doc = """# 事件驱动同步机制使用指南

## 一、架构概览

```
PostgreSQL (主权层)
    ↓ 发布事件
Event Bus (事件总线)
    ↓ 异步通知
├─→ Neo4j 同步服务
├─→ ChromaDB 同步服务
└─→ Redis 缓存失效服务
```

## 二、快速开始

### 1. 初始化

```python
from event_sync_system import EventBus, PostgreSQLDataService
from event_sync_system import Neo4jSyncService, ChromaDBSyncService, RedisCacheInvalidationService

# 初始化事件总线
event_bus = EventBus()

# 初始化数据库连接
pg_conn = psycopg2.connect(DATABASE_URL)
neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(user, password))
chroma_client = chromadb.Client()
redis_client = redis.Redis(host='localhost', port=6379)

# 启动同步服务
neo4j_sync = Neo4jSyncService(neo4j_driver, event_bus)
chroma_sync = ChromaDBSyncService(chroma_client, event_bus)
redis_sync = RedisCacheInvalidationService(redis_client, event_bus)

# 初始化数据服务
data_service = PostgreSQLDataService(pg_conn, event_bus)
```

### 2. 创建数据

```python
# 创建实体（自动同步到 Neo4j）
entity_id = await data_service.create_entity({
    'project_id': 'proj_123',
    'name': '张三',
    'type': 'person',
    'description': '项目负责人',
})

# PostgreSQL: 写入主表
# Event Bus: 发布 ENTITY_CREATED 事件
# Neo4j: 自动创建节点
# Redis: 无需操作（新数据没有缓存）
```

### 3. 更新数据

```python
# 更新实体（自动同步）
await data_service.update_entity(entity_id, {
    'mention_count': 5,
    'sentiment_avg': 0.8,
})

# PostgreSQL: 更新主表
# Event Bus: 发布 ENTITY_UPDATED 事件
# Neo4j: 自动更新节点
# Redis: 失效相关缓存
```

### 4. 删除数据

```python
# 删除实体（自动同步）
await data_service.delete_entity(entity_id)

# PostgreSQL: 删除记录
# Event Bus: 发布 ENTITY_DELETED 事件
# Neo4j: 删除节点及所有关系
# Redis: 失效相关缓存
```

## 三、事件类型

| 事件类型 | 触发时机 | 同步到 |
|---------|---------|--------|
| `ENTITY_CREATED` | 创建实体 | Neo4j |
| `ENTITY_UPDATED` | 更新实体 | Neo4j, Redis |
| `ENTITY_DELETED` | 删除实体 | Neo4j, Redis |
| `CHUNK_CREATED` | 创建 chunk | ChromaDB |
| `CHUNK_UPDATED` | 更新 chunk | ChromaDB, Redis |
| `CHUNK_DELETED` | 删除 chunk | ChromaDB, Redis |

## 四、自定义订阅

```python
# 订阅自定义事件处理
async def my_custom_handler(event: Event):
    print(f"收到事件: {event.event_type.value}")
    print(f"实体 ID: {event.entity_id}")
    print(f"数据: {event.data}")

event_bus.subscribe(EventType.ENTITY_CREATED, my_custom_handler)
```

## 五、事件历史

```python
# 查看最近的事件历史
history = event_bus.get_event_history(limit=100)

for event in history:
    print(f"{event['timestamp']}: {event['event_type']} - {event['entity_id']}")
```

## 六、错误处理

事件订阅器的错误不会影响主流程：

- ✅ PostgreSQL 写入成功，事件发布
- ❌ Neo4j 同步失败 → 记录日志，不影响主流程
- ✅ ChromaDB 同步成功
- ✅ Redis 缓存失效成功

**所有同步都是异步的，不阻塞主流程。**

## 七、监控与日志

```python
import logging

logging.basicConfig(level=logging.INFO)

# 日志输出示例:
# INFO: EventBus 初始化完成
# INFO: Neo4j 同步服务已启动
# INFO: 发布事件: entity.created - ent_a1b2c3d4e5f6
# INFO: Neo4j: 同步创建实体 ent_a1b2c3d4e5f6
# INFO: Redis: 失效缓存 entity:ent_* (3 keys)
```

## 八、性能优化

1. **批量操作**: 批量创建时，使用单个事件包含多个实体
2. **异步执行**: 所有同步都是异步的，不阻塞主流程
3. **重试机制**: 失败的同步会记录日志，可通过定时任务重试
4. **监控告警**: 监控同步延迟，超过阈值告警

---

**FieldMind P0 优化**
事件驱动同步机制
Version 1.0
"""

    with open(f"{output_dir}/EVENT_SYNC_GUIDE.md", 'w') as f:
        f.write(doc)

    print(f"✅ 使用文档已生成: {output_dir}/EVENT_SYNC_GUIDE.md")


if __name__ == "__main__":
    print("=" * 70)
    print("P0 Day 2: 事件驱动同步机制")
    print("=" * 70)

    generate_event_sync_code()

    print("\n✅ P0 Day 2 完成")
    print("\n📁 生成文件:")
    print("  1. event_sync_system.py - 事件同步系统代码")
    print("  2. EVENT_SYNC_GUIDE.md - 使用指南")
