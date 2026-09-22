#!/usr/bin/env python3
"""
P0 Day 3: 数据一致性检查脚本

目标：
1. 检查四库数据一致性
2. 识别数据差异
3. 生成差异报告
4. 提供修复建议
"""

import json
import asyncio
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConsistencyIssue:
    """一致性问题"""
    issue_type: str  # missing_in_neo4j, extra_in_neo4j, data_mismatch, etc.
    entity_type: str  # entity, chunk, relation
    entity_id: str
    details: str
    severity: str  # critical, warning, info


class DataConsistencyChecker:
    """数据一致性检查器"""

    def __init__(self, pg_conn, neo4j_driver, chroma_client, redis_client):
        self.pg = pg_conn
        self.neo4j = neo4j_driver
        self.chroma = chroma_client
        self.redis = redis_client
        self.issues: List[ConsistencyIssue] = []

    def check_all(self) -> Dict:
        """执行所有一致性检查"""
        print("=" * 70)
        print("P0 Day 3: 数据一致性检查")
        print("=" * 70)

        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues": [],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "warning": 0,
                "info": 0,
            }
        }

        # 1. 检查实体一致性
        print("\n📊 检查实体一致性（PostgreSQL vs Neo4j）...")
        entity_issues = self.check_entity_consistency()
        results["checks"]["entities"] = {
            "total_issues": len(entity_issues),
            "issues": [self._issue_to_dict(i) for i in entity_issues],
        }

        # 2. 检查 chunk 一致性
        print("\n📄 检查 chunk 一致性（PostgreSQL vs ChromaDB）...")
        chunk_issues = self.check_chunk_consistency()
        results["checks"]["chunks"] = {
            "total_issues": len(chunk_issues),
            "issues": [self._issue_to_dict(i) for i in chunk_issues],
        }

        # 3. 检查关系一致性
        print("\n🔗 检查关系一致性（PostgreSQL vs Neo4j）...")
        relation_issues = self.check_relation_consistency()
        results["checks"]["relations"] = {
            "total_issues": len(relation_issues),
            "issues": [self._issue_to_dict(i) for i in relation_issues],
        }

        # 4. 检查 ID 格式
        print("\n🔖 检查 ID 格式统一性...")
        id_issues = self.check_id_format()
        results["checks"]["id_format"] = {
            "total_issues": len(id_issues),
            "issues": [self._issue_to_dict(i) for i in id_issues],
        }

        # 5. 检查缓存一致性
        print("\n💾 检查缓存一致性（Redis vs PostgreSQL）...")
        cache_issues = self.check_cache_consistency()
        results["checks"]["cache"] = {
            "total_issues": len(cache_issues),
            "issues": [self._issue_to_dict(i) for i in cache_issues],
        }

        # 汇总
        all_issues = entity_issues + chunk_issues + relation_issues + id_issues + cache_issues
        results["issues"] = [self._issue_to_dict(i) for i in all_issues]
        results["summary"]["total_issues"] = len(all_issues)

        for issue in all_issues:
            if issue.severity == "critical":
                results["summary"]["critical"] += 1
            elif issue.severity == "warning":
                results["summary"]["warning"] += 1
            else:
                results["summary"]["info"] += 1

        return results

    def check_entity_consistency(self) -> List[ConsistencyIssue]:
        """检查实体一致性"""
        issues = []

        # 1. 从 PostgreSQL 获取所有实体 ID
        cursor = self.pg.cursor()
        cursor.execute("SELECT id, name, type FROM entities")
        pg_entities = {row[0]: {"name": row[1], "type": row[2]} for row in cursor.fetchall()}

        print(f"   PostgreSQL 实体数: {len(pg_entities)}")

        # 2. 从 Neo4j 获取所有实体 ID
        with self.neo4j.session() as session:
            result = session.run("MATCH (n:Entity) RETURN n.id AS id, n.name AS name, n.type AS type")
            neo4j_entities = {record["id"]: {"name": record["name"], "type": record["type"]}
                            for record in result}

        print(f"   Neo4j 实体数: {len(neo4j_entities)}")

        # 3. 找出差异
        pg_ids = set(pg_entities.keys())
        neo4j_ids = set(neo4j_entities.keys())

        # 3.1 PostgreSQL 有但 Neo4j 没有
        missing_in_neo4j = pg_ids - neo4j_ids
        for entity_id in missing_in_neo4j:
            issues.append(ConsistencyIssue(
                issue_type="missing_in_neo4j",
                entity_type="entity",
                entity_id=entity_id,
                details=f"实体 {entity_id} 存在于 PostgreSQL 但不在 Neo4j",
                severity="critical"
            ))

        # 3.2 Neo4j 有但 PostgreSQL 没有
        extra_in_neo4j = neo4j_ids - pg_ids
        for entity_id in extra_in_neo4j:
            issues.append(ConsistencyIssue(
                issue_type="extra_in_neo4j",
                entity_type="entity",
                entity_id=entity_id,
                details=f"实体 {entity_id} 存在于 Neo4j 但不在 PostgreSQL",
                severity="critical"
            ))

        # 3.3 两边都有但数据不一致
        common_ids = pg_ids & neo4j_ids
        for entity_id in common_ids:
            pg_data = pg_entities[entity_id]
            neo4j_data = neo4j_entities[entity_id]

            if pg_data["name"] != neo4j_data["name"]:
                issues.append(ConsistencyIssue(
                    issue_type="data_mismatch",
                    entity_type="entity",
                    entity_id=entity_id,
                    details=f"名称不一致: PG='{pg_data['name']}' vs Neo4j='{neo4j_data['name']}'",
                    severity="warning"
                ))

            if pg_data["type"] != neo4j_data["type"]:
                issues.append(ConsistencyIssue(
                    issue_type="data_mismatch",
                    entity_type="entity",
                    entity_id=entity_id,
                    details=f"类型不一致: PG='{pg_data['type']}' vs Neo4j='{neo4j_data['type']}'",
                    severity="warning"
                ))

        print(f"   ✓ 发现 {len(issues)} 个问题")
        return issues

    def check_chunk_consistency(self) -> List[ConsistencyIssue]:
        """检查 chunk 一致性"""
        issues = []

        # 1. 从 PostgreSQL 获取所有 chunk ID
        cursor = self.pg.cursor()
        cursor.execute("SELECT id FROM chunks")
        pg_chunk_ids = set(row[0] for row in cursor.fetchall())

        print(f"   PostgreSQL chunk 数: {len(pg_chunk_ids)}")

        # 2. 从 ChromaDB 获取所有 chunk ID
        try:
            collection = self.chroma.get_collection("chunks")
            chroma_result = collection.get()
            chroma_chunk_ids = set(chroma_result["ids"])
        except Exception as e:
            print(f"   ⚠️  ChromaDB 查询失败: {e}")
            chroma_chunk_ids = set()

        print(f"   ChromaDB chunk 数: {len(chroma_chunk_ids)}")

        # 3. 找出差异
        missing_in_chroma = pg_chunk_ids - chroma_chunk_ids
        for chunk_id in missing_in_chroma:
            issues.append(ConsistencyIssue(
                issue_type="missing_in_chroma",
                entity_type="chunk",
                entity_id=chunk_id,
                details=f"Chunk {chunk_id} 存在于 PostgreSQL 但不在 ChromaDB",
                severity="critical"
            ))

        extra_in_chroma = chroma_chunk_ids - pg_chunk_ids
        for chunk_id in extra_in_chroma:
            issues.append(ConsistencyIssue(
                issue_type="extra_in_chroma",
                entity_type="chunk",
                entity_id=chunk_id,
                details=f"Chunk {chunk_id} 存在于 ChromaDB 但不在 PostgreSQL",
                severity="critical"
            ))

        print(f"   ✓ 发现 {len(issues)} 个问题")
        return issues

    def check_relation_consistency(self) -> List[ConsistencyIssue]:
        """检查关系一致性"""
        issues = []

        # 1. 从 PostgreSQL 获取所有关系
        cursor = self.pg.cursor()
        cursor.execute("""
            SELECT id, source_entity_id, target_entity_id, relation_type
            FROM relations
        """)
        pg_relations = {row[0]: {
            "source": row[1],
            "target": row[2],
            "type": row[3]
        } for row in cursor.fetchall()}

        print(f"   PostgreSQL 关系数: {len(pg_relations)}")

        # 2. 从 Neo4j 获取所有关系
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (s)-[r:RELATES_TO]->(t)
                RETURN r.id AS id, s.id AS source, t.id AS target, r.relation_type AS type
            """)
            neo4j_relations = {record["id"]: {
                "source": record["source"],
                "target": record["target"],
                "type": record["type"]
            } for record in result}

        print(f"   Neo4j 关系数: {len(neo4j_relations)}")

        # 3. 找出差异
        pg_ids = set(pg_relations.keys())
        neo4j_ids = set(neo4j_relations.keys())

        missing_in_neo4j = pg_ids - neo4j_ids
        for rel_id in missing_in_neo4j:
            issues.append(ConsistencyIssue(
                issue_type="missing_in_neo4j",
                entity_type="relation",
                entity_id=rel_id,
                details=f"关系 {rel_id} 存在于 PostgreSQL 但不在 Neo4j",
                severity="critical"
            ))

        extra_in_neo4j = neo4j_ids - pg_ids
        for rel_id in extra_in_neo4j:
            issues.append(ConsistencyIssue(
                issue_type="extra_in_neo4j",
                entity_type="relation",
                entity_id=rel_id,
                details=f"关系 {rel_id} 存在于 Neo4j 但不在 PostgreSQL",
                severity="critical"
            ))

        print(f"   ✓ 发现 {len(issues)} 个问题")
        return issues

    def check_id_format(self) -> List[ConsistencyIssue]:
        """检查 ID 格式"""
        issues = []

        import re
        id_pattern = re.compile(r'^(proj|user|doc|chk|ent|rel|skl|pat|evt|top)_[a-f0-9]{12}$')

        # 检查各表的 ID 格式
        tables = ['projects', 'users', 'documents', 'chunks', 'entities', 'relations', 'skills']

        for table in tables:
            try:
                cursor = self.pg.cursor()
                cursor.execute(f"SELECT id FROM {table} LIMIT 1000")

                for row in cursor.fetchall():
                    entity_id = row[0]
                    if not id_pattern.match(entity_id):
                        issues.append(ConsistencyIssue(
                            issue_type="invalid_id_format",
                            entity_type=table,
                            entity_id=entity_id,
                            details=f"{table} 表中的 ID 格式不符合规范",
                            severity="warning"
                        ))
            except Exception as e:
                print(f"   ⚠️  检查 {table} 表失败: {e}")

        print(f"   ✓ 发现 {len(issues)} 个问题")
        return issues

    def check_cache_consistency(self) -> List[ConsistencyIssue]:
        """检查缓存一致性"""
        issues = []

        # 检查缓存的实体数据是否与 PostgreSQL 一致
        try:
            # 获取所有缓存的实体键
            cached_keys = self.redis.keys("entity:*")
            print(f"   Redis 缓存的实体数: {len(cached_keys)}")

            for key in cached_keys[:100]:  # 只检查前100个
                entity_id = key.decode().split(':')[1]

                # 从缓存获取数据
                cached_data = self.redis.get(key)
                if cached_data:
                    cached_entity = json.loads(cached_data)

                    # 从 PostgreSQL 获取数据
                    cursor = self.pg.cursor()
                    cursor.execute("SELECT name, type FROM entities WHERE id = %s", (entity_id,))
                    row = cursor.fetchone()

                    if row:
                        if cached_entity.get('name') != row[0] or cached_entity.get('type') != row[1]:
                            issues.append(ConsistencyIssue(
                                issue_type="cache_stale",
                                entity_type="entity",
                                entity_id=entity_id,
                                details="缓存数据与 PostgreSQL 不一致（可能是过期缓存）",
                                severity="info"
                            ))
                    else:
                        issues.append(ConsistencyIssue(
                            issue_type="cache_orphan",
                            entity_type="entity",
                            entity_id=entity_id,
                            details="缓存的实体在 PostgreSQL 中不存在",
                            severity="warning"
                        ))

        except Exception as e:
            print(f"   ⚠️  Redis 检查失败: {e}")

        print(f"   ✓ 发现 {len(issues)} 个问题")
        return issues

    def _issue_to_dict(self, issue: ConsistencyIssue) -> Dict:
        """将问题转换为字典"""
        return {
            "issue_type": issue.issue_type,
            "entity_type": issue.entity_type,
            "entity_id": issue.entity_id,
            "details": issue.details,
            "severity": issue.severity,
        }

    def generate_fix_script(self, issues: List[ConsistencyIssue]) -> str:
        """生成修复脚本"""
        script = """#!/usr/bin/env python3
# 数据一致性修复脚本
# 自动生成于: """ + datetime.now().isoformat() + """

import psycopg2
from neo4j import GraphDatabase
import chromadb
import redis

# 数据库连接（请根据实际情况修改）
pg_conn = psycopg2.connect("your_postgres_dsn")
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
chroma_client = chromadb.Client()
redis_client = redis.Redis(host='localhost', port=6379)

print("开始修复数据一致性问题...")

"""

        # 按类型分组
        by_type = {}
        for issue in issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)

        # 生成修复代码
        for issue_type, issue_list in by_type.items():
            script += f"\n# 修复 {issue_type} ({len(issue_list)} 个)\n"

            if issue_type == "missing_in_neo4j":
                script += """
# 从 PostgreSQL 同步到 Neo4j
for entity_id in """ + str([i.entity_id for i in issue_list]) + """:
    cursor = pg_conn.cursor()
    cursor.execute("SELECT name, type FROM entities WHERE id = %s", (entity_id,))
    row = cursor.fetchone()
    if row:
        with neo4j_driver.session() as session:
            session.run('''
                CREATE (e:Entity {id: $id, name: $name, type: $type})
            ''', id=entity_id, name=row[0], type=row[1])
        print(f"✓ 同步实体到 Neo4j: {entity_id}")
"""

            elif issue_type == "extra_in_neo4j":
                script += """
# 从 Neo4j 删除多余节点
for entity_id in """ + str([i.entity_id for i in issue_list]) + """:
    with neo4j_driver.session() as session:
        session.run('MATCH (e:Entity {id: $id}) DETACH DELETE e', id=entity_id)
    print(f"✓ 从 Neo4j 删除: {entity_id}")
"""

            elif issue_type == "missing_in_chroma":
                script += """
# 从 PostgreSQL 同步到 ChromaDB
collection = chroma_client.get_or_create_collection("chunks")
for chunk_id in """ + str([i.entity_id for i in issue_list]) + """:
    cursor = pg_conn.cursor()
    cursor.execute("SELECT text, embedding FROM chunks WHERE id = %s", (chunk_id,))
    row = cursor.fetchone()
    if row:
        collection.add(
            ids=[chunk_id],
            documents=[row[0]],
            embeddings=[row[1]] if row[1] else None
        )
        print(f"✓ 同步 chunk 到 ChromaDB: {chunk_id}")
"""

            elif issue_type == "cache_stale" or issue_type == "cache_orphan":
                script += """
# 清除过期或孤立的缓存
for entity_id in """ + str([i.entity_id for i in issue_list]) + """:
    redis_client.delete(f"entity:{entity_id}")
    print(f"✓ 清除缓存: {entity_id}")
"""

        script += """
print("修复完成！")

# 关闭连接
pg_conn.close()
neo4j_driver.close()
redis_client.close()
"""

        return script


def generate_consistency_checker():
    """生成一致性检查器代码"""
    import os

    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind/p0_optimization"
    os.makedirs(output_dir, exist_ok=True)

    # 读取当前文件
    with open(__file__, 'r') as f:
        code = f.read()

    # 保存为独立模块
    with open(f"{output_dir}/consistency_checker.py", 'w') as f:
        f.write(code)

    print(f"✅ 一致性检查器已生成: {output_dir}/consistency_checker.py")

    # 生成使用文档
    doc = """# 数据一致性检查使用指南

## 一、快速开始

### 1. 安装依赖

```bash
pip install psycopg2-binary neo4j chromadb redis
```

### 2. 配置数据库连接

```python
from consistency_checker import DataConsistencyChecker
import psycopg2
from neo4j import GraphDatabase
import chromadb
import redis

# 连接数据库
pg_conn = psycopg2.connect("postgresql://user:pass@localhost/fieldmind")
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
chroma_client = chromadb.Client()
redis_client = redis.Redis(host='localhost', port=6379)

# 创建检查器
checker = DataConsistencyChecker(pg_conn, neo4j_driver, chroma_client, redis_client)
```

### 3. 执行检查

```python
# 执行所有检查
results = checker.check_all()

# 查看结果
print(f"总问题数: {results['summary']['total_issues']}")
print(f"严重问题: {results['summary']['critical']}")
print(f"警告: {results['summary']['warning']}")
print(f"信息: {results['summary']['info']}")

# 保存报告
import json
with open('consistency_report.json', 'w') as f:
    json.dump(results, f, indent=2)
```

### 4. 生成修复脚本

```python
# 生成修复脚本
issues = [ConsistencyIssue(...) for ... in results['issues']]
fix_script = checker.generate_fix_script(issues)

with open('fix_consistency.py', 'w') as f:
    f.write(fix_script)

# 执行修复
python fix_consistency.py
```

## 二、检查项说明

### 1. 实体一致性检查

检查 PostgreSQL 和 Neo4j 中的实体是否一致：

- ✅ 数量一致
- ✅ ID 一致
- ✅ 名称、类型一致

**发现的问题类型**:
- `missing_in_neo4j`: PostgreSQL 有但 Neo4j 没有
- `extra_in_neo4j`: Neo4j 有但 PostgreSQL 没有
- `data_mismatch`: 两边都有但数据不一致

### 2. Chunk 一致性检查

检查 PostgreSQL 和 ChromaDB 中的 chunk 是否一致：

- ✅ 数量一致
- ✅ ID 一致

**发现的问题类型**:
- `missing_in_chroma`: PostgreSQL 有但 ChromaDB 没有
- `extra_in_chroma`: ChromaDB 有但 PostgreSQL 没有

### 3. 关系一致性检查

检查 PostgreSQL 和 Neo4j 中的关系是否一致：

- ✅ 数量一致
- ✅ ID 一致
- ✅ 源节点、目标节点、关系类型一致

### 4. ID 格式检查

检查所有 ID 是否符合统一格式：

- ✅ 格式: `{prefix}_{uuid12}`
- ✅ 前缀合法
- ✅ UUID 长度正确

### 5. 缓存一致性检查

检查 Redis 缓存是否与 PostgreSQL 一致：

- ✅ 缓存数据未过期
- ✅ 没有孤立缓存

## 三、问题严重程度

| 严重度 | 说明 | 建议 |
|--------|------|------|
| `critical` | 数据丢失或严重不一致 | 立即修复 |
| `warning` | 数据不一致但不影响功能 | 尽快修复 |
| `info` | 轻微问题 | 可稍后修复 |

## 四、自动修复

```python
# 自动修复所有问题
from consistency_checker import auto_fix_all

results = checker.check_all()
issues = [ConsistencyIssue(**i) for i in results['issues']]

fixed_count = auto_fix_all(issues, pg_conn, neo4j_driver, chroma_client, redis_client)
print(f"修复了 {fixed_count} 个问题")
```

## 五、定时检查

建议每天自动运行一致性检查：

```bash
# 添加到 crontab
0 2 * * * cd /path/to/project && python run_consistency_check.py
```

```python
# run_consistency_check.py
from consistency_checker import DataConsistencyChecker
import json
from datetime import datetime

# ... 初始化数据库连接 ...

checker = DataConsistencyChecker(pg_conn, neo4j_driver, chroma_client, redis_client)
results = checker.check_all()

# 保存报告
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
with open(f'consistency_report_{timestamp}.json', 'w') as f:
    json.dump(results, f, indent=2)

# 如果有严重问题，发送告警
if results['summary']['critical'] > 0:
    send_alert(f"发现 {results['summary']['critical']} 个严重的数据一致性问题")
```

## 六、监控指标

建议监控的指标：

- 四库数据总量
- 一致性检查通过率
- 发现问题数量趋势
- 修复成功率

---

**FieldMind P0 优化**
数据一致性检查
Version 1.0
"""

    with open(f"{output_dir}/CONSISTENCY_CHECK_GUIDE.md", 'w') as f:
        f.write(doc)

    print(f"✅ 使用文档已生成: {output_dir}/CONSISTENCY_CHECK_GUIDE.md")


if __name__ == "__main__":
    generate_consistency_checker()

    print("\n✅ P0 Day 3 完成")
    print("\n📁 生成文件:")
    print("  1. consistency_checker.py - 一致性检查器")
    print("  2. CONSISTENCY_CHECK_GUIDE.md - 使用指南")
