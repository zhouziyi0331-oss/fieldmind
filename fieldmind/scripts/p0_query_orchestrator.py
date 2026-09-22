#!/usr/bin/env python3
"""
P0 Day 4: 查询编排器（四库协同查询）

目标：
1. 实现统一查询接口
2. 四库协同查询
3. 智能缓存策略
4. 查询结果合并
5. 性能优化
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """查询结果"""
    data: Any
    source: str  # postgresql, neo4j, chromadb, redis
    latency_ms: float
    cached: bool = False


class QueryOrchestrator:
    """查询编排器 - 协调四库查询"""

    def __init__(self, pg_conn, neo4j_driver, chroma_client, redis_client):
        self.pg = pg_conn
        self.neo4j = neo4j_driver
        self.chroma = chroma_client
        self.redis = redis_client

        # 缓存配置
        self.cache_ttl = {
            'entity': 300,  # 5分钟
            'chunk': 600,   # 10分钟
            'search': 300,  # 5分钟
            'graph': 180,   # 3分钟
        }

    # ============================================
    # 基础查询方法
    # ============================================

    async def get_entity(self, entity_id: str, include_relations: bool = False) -> Dict:
        """
        获取实体详情（四库协同）

        查询流程：
        1. Redis 检查缓存
        2. PostgreSQL 获取主数据
        3. Neo4j 获取关系（如果需要）
        4. 合并结果
        5. 写入 Redis 缓存
        """
        start_time = datetime.now()

        # 1. 检查缓存
        cache_key = f"entity:{entity_id}"
        cached = await self._get_from_cache(cache_key)
        if cached:
            logger.info(f"✅ 缓存命中: {entity_id}")
            return {
                'entity': cached,
                'source': 'redis',
                'cached': True,
                'latency_ms': (datetime.now() - start_time).total_seconds() * 1000
            }

        # 2. 从 PostgreSQL 获取主数据
        entity = await self._get_entity_from_pg(entity_id)
        if not entity:
            return {'error': 'Entity not found', 'entity_id': entity_id}

        # 3. 如果需要，从 Neo4j 获取关系
        if include_relations:
            relations = await self._get_entity_relations_from_neo4j(entity_id)
            entity['relations'] = relations

        # 4. 写入缓存
        await self._set_cache(cache_key, entity, self.cache_ttl['entity'])

        latency = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"✅ 查询实体 {entity_id} 完成 ({latency:.2f}ms)")

        return {
            'entity': entity,
            'source': 'postgresql+neo4j' if include_relations else 'postgresql',
            'cached': False,
            'latency_ms': latency
        }

    async def search_chunks(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None
    ) -> Dict:
        """
        语义搜索 chunks（四库协同）

        查询流程：
        1. Redis 检查缓存
        2. ChromaDB 向量检索
        3. PostgreSQL 获取完整信息
        4. Neo4j 获取关联实体
        5. 合并结果
        6. 写入 Redis 缓存
        """
        start_time = datetime.now()

        # 1. 检查缓存
        cache_key = self._generate_search_cache_key(query, limit, filters)
        cached = await self._get_from_cache(cache_key)
        if cached:
            logger.info(f"✅ 搜索缓存命中: {query[:30]}...")
            return {
                'results': cached,
                'source': 'redis',
                'cached': True,
                'latency_ms': (datetime.now() - start_time).total_seconds() * 1000
            }

        # 2. ChromaDB 向量检索
        chunk_ids = await self._search_chunks_from_chroma(query, limit * 2, filters)

        # 3. PostgreSQL 获取完整信息
        chunks = await self._get_chunks_from_pg(chunk_ids)

        # 4. Neo4j 获取每个 chunk 关联的实体
        for chunk in chunks:
            entities = await self._get_chunk_entities_from_neo4j(chunk['id'])
            chunk['entities'] = entities

        # 5. 排序和截取
        chunks = chunks[:limit]

        # 6. 写入缓存
        await self._set_cache(cache_key, chunks, self.cache_ttl['search'])

        latency = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"✅ 搜索完成: {query[:30]}... ({latency:.2f}ms, {len(chunks)} 结果)")

        return {
            'results': chunks,
            'source': 'chromadb+postgresql+neo4j',
            'cached': False,
            'latency_ms': latency,
            'total_results': len(chunks)
        }

    async def get_knowledge_graph(
        self,
        project_id: str,
        center_entity_id: Optional[str] = None,
        depth: int = 2
    ) -> Dict:
        """
        获取知识图谱（四库协同）

        查询流程：
        1. Redis 检查缓存
        2. Neo4j 获取图结构
        3. PostgreSQL 获取节点详细信息
        4. 合并结果
        5. 写入 Redis 缓存
        """
        start_time = datetime.now()

        # 1. 检查缓存
        cache_key = f"graph:{project_id}:{center_entity_id}:{depth}"
        cached = await self._get_from_cache(cache_key)
        if cached:
            logger.info(f"✅ 图谱缓存命中: {project_id}")
            return {
                'graph': cached,
                'source': 'redis',
                'cached': True,
                'latency_ms': (datetime.now() - start_time).total_seconds() * 1000
            }

        # 2. Neo4j 获取图结构
        graph_data = await self._get_graph_from_neo4j(project_id, center_entity_id, depth)

        # 3. PostgreSQL 补充节点详细信息
        entity_ids = [node['id'] for node in graph_data['nodes']]
        entity_details = await self._get_entities_batch_from_pg(entity_ids)

        # 合并详细信息到节点
        entity_map = {e['id']: e for e in entity_details}
        for node in graph_data['nodes']:
            if node['id'] in entity_map:
                node.update(entity_map[node['id']])

        # 4. 写入缓存
        await self._set_cache(cache_key, graph_data, self.cache_ttl['graph'])

        latency = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"✅ 图谱查询完成: {project_id} ({latency:.2f}ms)")

        return {
            'graph': graph_data,
            'source': 'neo4j+postgresql',
            'cached': False,
            'latency_ms': latency
        }

    async def get_entity_timeline(self, entity_id: str) -> Dict:
        """
        获取实体时间线（四库协同）

        查询流程：
        1. Redis 检查缓存
        2. PostgreSQL 获取实体和 timeline 字段
        3. PostgreSQL 查询提及该实体的所有 chunks（按时间排序）
        4. 合并构建完整时间线
        5. 写入 Redis 缓存
        """
        start_time = datetime.now()

        # 1. 检查缓存
        cache_key = f"timeline:{entity_id}"
        cached = await self._get_from_cache(cache_key)
        if cached:
            return {
                'timeline': cached,
                'source': 'redis',
                'cached': True,
                'latency_ms': (datetime.now() - start_time).total_seconds() * 1000
            }

        # 2. 获取实体基础信息和已有 timeline
        entity = await self._get_entity_from_pg(entity_id)
        if not entity:
            return {'error': 'Entity not found'}

        timeline_events = json.loads(entity.get('timeline', '[]'))

        # 3. 查询提及该实体的所有 chunks
        chunks = await self._get_chunks_mentioning_entity(entity_id)

        # 4. 构建时间线（按时间排序）
        for chunk in chunks:
            if chunk.get('timestamp_start'):
                timeline_events.append({
                    'timestamp': chunk['timestamp_start'],
                    'type': 'mention',
                    'context': chunk['text'][:100],
                    'sentiment': chunk.get('sentiment_polarity'),
                    'chunk_id': chunk['id'],
                })

        # 排序
        timeline_events.sort(key=lambda x: x.get('timestamp', 0))

        timeline = {
            'entity_id': entity_id,
            'entity_name': entity.get('name'),
            'events': timeline_events,
            'total_events': len(timeline_events),
        }

        # 5. 写入缓存
        await self._set_cache(cache_key, timeline, self.cache_ttl['entity'])

        latency = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"✅ 时间线查询完成: {entity_id} ({latency:.2f}ms)")

        return {
            'timeline': timeline,
            'source': 'postgresql',
            'cached': False,
            'latency_ms': latency
        }

    # ============================================
    # 底层数据库查询方法
    # ============================================

    async def _get_entity_from_pg(self, entity_id: str) -> Optional[Dict]:
        """从 PostgreSQL 获取实体"""
        cursor = self.pg.cursor()
        cursor.execute("""
            SELECT id, name, type, description, mention_count, sentiment_avg,
                   importance_score, first_appearance, last_appearance,
                   related_entities, related_events, timeline, metadata
            FROM entities
            WHERE id = %s
        """, (entity_id,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'description': row[3],
            'mention_count': row[4],
            'sentiment_avg': row[5],
            'importance_score': row[6],
            'first_appearance': row[7].isoformat() if row[7] else None,
            'last_appearance': row[8].isoformat() if row[8] else None,
            'related_entities': json.loads(row[9]) if row[9] else [],
            'related_events': json.loads(row[10]) if row[10] else [],
            'timeline': row[11],
            'metadata': json.loads(row[12]) if row[12] else {},
        }

    async def _get_entity_relations_from_neo4j(self, entity_id: str) -> List[Dict]:
        """从 Neo4j 获取实体关系"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (e:Entity {id: $id})-[r:RELATES_TO]-(other:Entity)
                RETURN other.id AS entity_id, other.name AS name,
                       r.relation_type AS relation_type, r.confidence AS confidence
            """, id=entity_id)

            return [
                {
                    'entity_id': record['entity_id'],
                    'name': record['name'],
                    'relation_type': record['relation_type'],
                    'confidence': record['confidence'],
                }
                for record in result
            ]

    async def _search_chunks_from_chroma(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict]
    ) -> List[str]:
        """从 ChromaDB 搜索 chunks"""
        try:
            collection = self.chroma.get_collection("chunks")

            # 构建查询参数
            query_params = {
                'query_texts': [query],
                'n_results': limit,
            }

            # 添加过滤条件
            if filters:
                where_filter = {}
                if filters.get('dimension_category'):
                    where_filter['dimension_category'] = filters['dimension_category']
                if filters.get('project_id'):
                    where_filter['project_id'] = filters['project_id']

                if where_filter:
                    query_params['where'] = where_filter

            results = collection.query(**query_params)

            return results['ids'][0] if results['ids'] else []

        except Exception as e:
            logger.error(f"ChromaDB 搜索失败: {e}")
            return []

    async def _get_chunks_from_pg(self, chunk_ids: List[str]) -> List[Dict]:
        """从 PostgreSQL 批量获取 chunks"""
        if not chunk_ids:
            return []

        cursor = self.pg.cursor()
        placeholders = ','.join(['%s'] * len(chunk_ids))
        cursor.execute(f"""
            SELECT id, text, speaker, sentiment_polarity, sentiment_subjectivity,
                   dimension_category, dimension_sub_category, quality_score,
                   entities, keywords, metadata
            FROM chunks
            WHERE id IN ({placeholders})
        """, chunk_ids)

        chunks = []
        for row in cursor.fetchall():
            chunks.append({
                'id': row[0],
                'text': row[1],
                'speaker': row[2],
                'sentiment_polarity': row[3],
                'sentiment_subjectivity': row[4],
                'dimension_category': row[5],
                'dimension_sub_category': row[6],
                'quality_score': row[7],
                'entities': json.loads(row[8]) if row[8] else [],
                'keywords': json.loads(row[9]) if row[9] else [],
                'metadata': json.loads(row[10]) if row[10] else {},
            })

        return chunks

    async def _get_chunk_entities_from_neo4j(self, chunk_id: str) -> List[Dict]:
        """从 Neo4j 获取 chunk 关联的实体"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (c:Chunk {id: $chunk_id})-[:MENTIONS]->(e:Entity)
                RETURN e.id AS id, e.name AS name, e.type AS type
            """, chunk_id=chunk_id)

            return [
                {'id': r['id'], 'name': r['name'], 'type': r['type']}
                for r in result
            ]

    async def _get_graph_from_neo4j(
        self,
        project_id: str,
        center_entity_id: Optional[str],
        depth: int
    ) -> Dict:
        """从 Neo4j 获取图结构"""
        with self.neo4j.session() as session:
            if center_entity_id:
                # 以某个实体为中心
                query = """
                    MATCH path = (center:Entity {id: $center_id})-[*1..%d]-(other:Entity)
                    WHERE center.project_id = $project_id
                    WITH nodes(path) AS nodes, relationships(path) AS rels
                    UNWIND nodes AS n
                    WITH collect(DISTINCT {id: n.id, name: n.name, type: n.type}) AS all_nodes
                    MATCH (e1:Entity)-[r:RELATES_TO]->(e2:Entity)
                    WHERE e1.project_id = $project_id
                    RETURN all_nodes AS nodes,
                           collect({source: e1.id, target: e2.id, type: r.relation_type}) AS edges
                """ % depth

                result = session.run(query, center_id=center_entity_id, project_id=project_id)
            else:
                # 整个项目的图
                query = """
                    MATCH (e:Entity {project_id: $project_id})
                    WITH collect({id: e.id, name: e.name, type: e.type}) AS nodes
                    MATCH (e1:Entity {project_id: $project_id})-[r:RELATES_TO]->(e2:Entity)
                    RETURN nodes,
                           collect({source: e1.id, target: e2.id, type: r.relation_type}) AS edges
                """
                result = session.run(query, project_id=project_id)

            record = result.single()
            if record:
                return {
                    'nodes': record['nodes'],
                    'edges': record['edges'],
                }

            return {'nodes': [], 'edges': []}

    async def _get_entities_batch_from_pg(self, entity_ids: List[str]) -> List[Dict]:
        """从 PostgreSQL 批量获取实体"""
        if not entity_ids:
            return []

        cursor = self.pg.cursor()
        placeholders = ','.join(['%s'] * len(entity_ids))
        cursor.execute(f"""
            SELECT id, name, type, description, mention_count, sentiment_avg, importance_score
            FROM entities
            WHERE id IN ({placeholders})
        """, entity_ids)

        return [
            {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'description': row[3],
                'mention_count': row[4],
                'sentiment_avg': row[5],
                'importance_score': row[6],
            }
            for row in cursor.fetchall()
        ]

    async def _get_chunks_mentioning_entity(self, entity_id: str) -> List[Dict]:
        """获取提及某实体的所有 chunks"""
        cursor = self.pg.cursor()
        cursor.execute("""
            SELECT id, text, timestamp_start, sentiment_polarity
            FROM chunks
            WHERE entities::text LIKE %s
            ORDER BY timestamp_start
        """, (f'%{entity_id}%',))

        return [
            {
                'id': row[0],
                'text': row[1],
                'timestamp_start': row[2],
                'sentiment_polarity': row[3],
            }
            for row in cursor.fetchall()
        ]

    # ============================================
    # 缓存方法
    # ============================================

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """从 Redis 获取缓存"""
        try:
            cached = self.redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Redis 读取失败: {e}")

        return None

    async def _set_cache(self, key: str, value: Any, ttl: int):
        """写入 Redis 缓存"""
        try:
            self.redis.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis 写入失败: {e}")

    def _generate_search_cache_key(self, query: str, limit: int, filters: Optional[Dict]) -> str:
        """生成搜索缓存键"""
        key_parts = [query, str(limit)]
        if filters:
            key_parts.append(json.dumps(filters, sort_keys=True))

        key_str = '|'.join(key_parts)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return f"search:{key_hash}"

    async def invalidate_cache(self, pattern: str):
        """失效缓存"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"✓ 失效缓存: {pattern} ({len(keys)} keys)")
        except Exception as e:
            logger.error(f"Redis 失效缓存失败: {e}")


# ============================================
# 使用示例
# ============================================

async def example_usage():
    """使用示例"""

    # 初始化（伪代码）
    # orchestrator = QueryOrchestrator(pg_conn, neo4j_driver, chroma_client, redis_client)

    # 1. 查询实体（含关系）
    # result = await orchestrator.get_entity('ent_abc123', include_relations=True)
    # print(result)

    # 2. 语义搜索
    # result = await orchestrator.search_chunks(
    #     query='山歌传承',
    #     limit=10,
    #     filters={'dimension_category': '非遗'}
    # )
    # print(result)

    # 3. 获取知识图谱
    # result = await orchestrator.get_knowledge_graph(
    #     project_id='proj_123',
    #     center_entity_id='ent_abc',
    #     depth=2
    # )
    # print(result)

    # 4. 获取实体时间线
    # result = await orchestrator.get_entity_timeline('ent_abc123')
    # print(result)

    print("查询编排器示例")


def generate_query_orchestrator():
    """生成查询编排器代码"""
    import os

    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/p0_optimization"
    os.makedirs(output_dir, exist_ok=True)

    # 读取当前文件
    with open(__file__, 'r') as f:
        code = f.read()

    # 保存为独立模块
    with open(f"{output_dir}/query_orchestrator.py", 'w') as f:
        f.write(code)

    print(f"✅ 查询编排器已生成: {output_dir}/query_orchestrator.py")

    # 生成使用文档
    doc = """# 查询编排器使用指南

## 一、概述

查询编排器是四库协同查询的核心组件，负责：

1. 🔍 智能路由查询到不同数据库
2. 💾 Redis 缓存管理
3. 🔗 跨库数据合并
4. ⚡ 性能优化

## 二、快速开始

### 初始化

```python
from query_orchestrator import QueryOrchestrator
import psycopg2
from neo4j import GraphDatabase
import chromadb
import redis

# 连接数据库
pg_conn = psycopg2.connect(DATABASE_URL)
neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(user, password))
chroma_client = chromadb.Client()
redis_client = redis.Redis()

# 创建编排器
orchestrator = QueryOrchestrator(pg_conn, neo4j_driver, chroma_client, redis_client)
```

## 三、核心功能

### 1. 查询实体

```python
# 基础查询（仅 PostgreSQL）
result = await orchestrator.get_entity('ent_abc123')

# 包含关系（PostgreSQL + Neo4j）
result = await orchestrator.get_entity('ent_abc123', include_relations=True)

# 返回结果
{
  'entity': {
    'id': 'ent_abc123',
    'name': '张三',
    'type': 'person',
    'mention_count': 15,
    'sentiment_avg': 0.65,
    'relations': [  # 如果 include_relations=True
      {
        'entity_id': 'ent_def456',
        'name': '李四',
        'relation_type': '合作',
        'confidence': 0.9
      }
    ]
  },
  'source': 'postgresql+neo4j',
  'cached': False,
  'latency_ms': 45.2
}
```

### 2. 语义搜索

```python
# 搜索 chunks
result = await orchestrator.search_chunks(
    query='山歌传承',
    limit=10,
    filters={
        'dimension_category': '非遗',
        'project_id': 'proj_123'
    }
)

# 返回结果
{
  'results': [
    {
      'id': 'chk_abc123',
      'text': '山歌是布依族的根...',
      'speaker': '王大爷',
      'sentiment_polarity': -0.42,
      'dimension_category': '非遗',
      'entities': [  # 从 Neo4j 获取
        {'id': 'ent_001', 'name': '山歌', 'type': 'concept'}
      ],
      'keywords': ['山歌', '布依族', '传承']
    }
  ],
  'source': 'chromadb+postgresql+neo4j',
  'cached': False,
  'latency_ms': 156.8,
  'total_results': 10
}
```

**查询流程**:
```
1. Redis 检查缓存 (5ms)
   ↓ 未命中
2. ChromaDB 向量检索 (80ms)
   → 返回 chunk_ids
3. PostgreSQL 批量获取 chunk 详情 (50ms)
4. Neo4j 批量获取关联实体 (20ms)
5. 合并结果 (1ms)
6. 写入 Redis 缓存 (5ms)
   ↓
总耗时: 156ms
```

### 3. 获取知识图谱

```python
# 整个项目的图
result = await orchestrator.get_knowledge_graph(project_id='proj_123')

# 以某个实体为中心，2层深度
result = await orchestrator.get_knowledge_graph(
    project_id='proj_123',
    center_entity_id='ent_abc123',
    depth=2
)

# 返回结果
{
  'graph': {
    'nodes': [
      {
        'id': 'ent_abc123',
        'name': '张三',
        'type': 'person',
        'mention_count': 15,  # 从 PostgreSQL 补充
        'sentiment_avg': 0.65
      }
    ],
    'edges': [
      {
        'source': 'ent_abc123',
        'target': 'ent_def456',
        'type': '合作'
      }
    ]
  },
  'source': 'neo4j+postgresql',
  'cached': False,
  'latency_ms': 89.3
}
```

**查询流程**:
```
1. Redis 检查缓存
   ↓ 未命中
2. Neo4j 获取图结构（节点+边）
3. PostgreSQL 批量获取节点详细信息
4. 合并数据
5. 写入 Redis 缓存
```

### 4. 获取实体时间线

```python
result = await orchestrator.get_entity_timeline('ent_abc123')

# 返回结果
{
  'timeline': {
    'entity_id': 'ent_abc123',
    'entity_name': '张三',
    'events': [
      {
        'timestamp': 32.5,
        'type': 'mention',
        'context': '张三说，山歌是布依族的根...',
        'sentiment': -0.42,
        'chunk_id': 'chk_001'
      },
      {
        'timestamp': 128.7,
        'type': 'mention',
        'context': '张三提到年轻人不学山歌...',
        'sentiment': -0.68,
        'chunk_id': 'chk_005'
      }
    ],
    'total_events': 23
  },
  'source': 'postgresql',
  'cached': False,
  'latency_ms': 67.2
}
```

## 四、缓存策略

### 默认 TTL

| 数据类型 | TTL | 说明 |
|---------|-----|------|
| entity | 5分钟 | 实体数据相对稳定 |
| chunk | 10分钟 | chunk 很少变化 |
| search | 5分钟 | 搜索结果可能过期 |
| graph | 3分钟 | 图结构可能频繁变化 |

### 缓存失效

```python
# 失效某个实体的缓存
await orchestrator.invalidate_cache('entity:ent_abc123')

# 失效所有实体缓存
await orchestrator.invalidate_cache('entity:*')

# 失效所有搜索缓存
await orchestrator.invalidate_cache('search:*')
```

### 缓存命中率

```python
# 监控缓存命中率
from collections import defaultdict

stats = defaultdict(int)

async def track_cache_hit(result):
    if result.get('cached'):
        stats['hit'] += 1
    else:
        stats['miss'] += 1

    hit_rate = stats['hit'] / (stats['hit'] + stats['miss']) * 100
    print(f"缓存命中率: {hit_rate:.1f}%")
```

## 五、性能优化

### 1. 批量查询

```python
# ❌ 不好: 循环查询
for entity_id in entity_ids:
    entity = await orchestrator.get_entity(entity_id)

# ✅ 好: 批量查询
entities = await orchestrator._get_entities_batch_from_pg(entity_ids)
```

### 2. 按需加载

```python
# ❌ 不好: 总是加载关系
result = await orchestrator.get_entity(entity_id, include_relations=True)

# ✅ 好: 只在需要时加载
result = await orchestrator.get_entity(entity_id, include_relations=False)
```

### 3. 缓存预热

```python
# 预热热门实体的缓存
popular_entity_ids = ['ent_001', 'ent_002', 'ent_003']

for entity_id in popular_entity_ids:
    await orchestrator.get_entity(entity_id)

print("缓存预热完成")
```

## 六、错误处理

```python
try:
    result = await orchestrator.get_entity('ent_abc123')

    if 'error' in result:
        print(f"查询失败: {result['error']}")
    else:
        entity = result['entity']
        print(f"查询成功: {entity['name']}")

except Exception as e:
    print(f"系统错误: {e}")
```

## 七、监控指标

建议监控：

1. **查询延迟**: 95分位、99分位
2. **缓存命中率**: 目标 > 70%
3. **数据库负载**: 每秒查询数
4. **错误率**: 目标 < 0.1%

```python
# 记录查询延迟
import time

start = time.time()
result = await orchestrator.get_entity(entity_id)
latency = (time.time() - start) * 1000

print(f"延迟: {latency:.2f}ms")

# 设置告警
if latency > 500:
    alert(f"查询延迟过高: {latency}ms")
```

---

**FieldMind P0 优化**
查询编排器
Version 1.0
"""

    with open(f"{output_dir}/QUERY_ORCHESTRATOR_GUIDE.md", 'w') as f:
        f.write(doc)

    print(f"✅ 使用文档已生成: {output_dir}/QUERY_ORCHESTRATOR_GUIDE.md")


if __name__ == "__main__":
    print("=" * 70)
    print("P0 Day 4: 查询编排器（四库协同查询）")
    print("=" * 70)

    generate_query_orchestrator()

    print("\n✅ P0 Day 4 完成")
    print("\n📁 生成文件:")
    print("  1. query_orchestrator.py - 查询编排器")
    print("  2. QUERY_ORCHESTRATOR_GUIDE.md - 使用指南")
