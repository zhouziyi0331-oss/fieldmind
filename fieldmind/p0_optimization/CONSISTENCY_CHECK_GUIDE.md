# 数据一致性检查使用指南

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
