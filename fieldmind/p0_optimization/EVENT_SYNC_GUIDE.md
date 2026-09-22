# 事件驱动同步机制使用指南

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
