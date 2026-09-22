# FieldMind 索引诊断和优化报告

## 执行时间
生成时间：2024-09-14

---

## 第一部分：现有索引情况

### 1. Documents 表索引

✅ **已建立的索引：**
- `project_id` - 单列索引 (index=True)
- `type` - 单列索引 (index=True)
- `status` - 单列索引 (index=True)
- `hash` - 唯一索引 (unique=True, index=True)
- `created_at` - 单列索引 (index=True)
- `idx_project_type` - 复合索引 (project_id, type)
- `idx_project_status` - 复合索引 (project_id, status)

⚠️ **缺失的索引：**
- `uploaded_at` - **没有索引**（关键字段！）

### 2. DocumentChunks 表索引

✅ **已建立的索引：**
- `chunk_id` - 唯一索引 (unique=True, index=True)
- `document_id` - 单列索引 (index=True)
- `project_id` - 单列索引 (index=True)
- `idx_chunk_document` - 复合索引 (document_id, chunk_index)
- `idx_chunk_project` - 复合索引 (project_id, created_at)
- `idx_chunk_page` - 复合索引 (document_id, page_number)
- `idx_chunk_timestamp` - 复合索引 (document_id, timestamp_start)

✅ **索引覆盖良好**

### 3. KnowledgeEntity 表索引

✅ **已建立的索引：**
- `document_id` - 单列索引 (index=True)
- `project_id` - 单列索引 (index=True)
- `name` - 单列索引 (index=True)
- `type` - 单列索引 (index=True)

✅ **索引覆盖良好**

---

## 第二部分：索引失效问题

### 🔴 问题 1：DATE() 函数导致索引失效

**位置：** `backend/src/app/services/analysis/trend_analysis.py`

**问题代码（多处）：**
```python
# 行 32, 37, 56, 61, 80, 85, 104, 109, 128, 133
sql = f"""
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as count
    FROM documents
    WHERE project_id = :project_id
    GROUP BY DATE(created_at)
"""
```

**为什么索引失效：**
- `DATE(created_at)` 在索引字段 `created_at` 上套了函数
- 导致 PostgreSQL/SQLite 无法使用 `created_at` 的索引
- 变成全表扫描

**修复方案：**
```python
# ✅ 正确写法
sql = f"""
    SELECT 
        DATE(created_at) as date,
        COUNT(*) as count
    FROM documents
    WHERE project_id = :project_id
      AND created_at >= :start_date
      AND created_at < :end_date
    GROUP BY DATE(created_at)
"""
```

**或者使用日期范围查询：**
```python
from datetime import datetime, timedelta

# 按天聚合
start_date = datetime(2024, 9, 1)
end_date = datetime(2024, 9, 15)

# 生成日期范围
dates = []
current = start_date
while current < end_date:
    next_day = current + timedelta(days=1)
    
    # 这样查询可以走索引
    count = session.query(Document).filter(
        Document.project_id == project_id,
        Document.created_at >= current,
        Document.created_at < next_day
    ).count()
    
    dates.append({'date': current.date(), 'count': count})
    current = next_day
```

---

## 第三部分：缺失索引

### 🔴 缺失索引 1：uploaded_at 字段

**影响：** 按上传时间查询文档时全表扫描

**SQL 修复：**
```sql
CREATE INDEX idx_documents_uploaded_at ON documents(uploaded_at);
```

**SQLAlchemy 修复：**
```python
# 在 backend/src/app/models/document.py 中修改
uploaded_at = Column(DateTime, index=True, comment="上传时间")  # 添加 index=True
```

### 🟡 建议索引 1：按项目 + 上传时间排序

**场景：** 查询某项目的最新文档

**当前查询（可能很慢）：**
```python
documents = session.query(Document).filter(
    Document.project_id == project_id
).order_by(Document.uploaded_at.desc()).limit(20)
```

**SQL 修复：**
```sql
CREATE INDEX idx_documents_project_uploaded ON documents(project_id, uploaded_at DESC);
```

**SQLAlchemy 修复：**
```python
# 在 Document 模型中添加
__table_args__ = (
    Index('idx_project_type', 'project_id', 'type'),
    Index('idx_project_status', 'project_id', 'status'),
    Index('idx_project_uploaded', 'project_id', 'uploaded_at'),  # 新增
)
```

### 🟡 建议索引 2：文件名搜索

**场景：** 按文件名搜索（如果有这个功能）

**如果有类似查询：**
```python
documents = session.query(Document).filter(
    Document.name.ilike(f"%{keyword}%")
)
```

**问题：** `LIKE '%keyword%'` 前置通配符无法走索引

**修复方案：**
1. 使用全文搜索索引（PostgreSQL）
```sql
CREATE INDEX idx_documents_name_gin ON documents USING gin(to_tsvector('simple', name));
```

2. 或者改用前缀匹配
```python
# ✅ 可以走索引
documents = session.query(Document).filter(
    Document.name.like(f"{keyword}%")  # 去掉前置 %
)
```

---

## 第四部分：复合索引顺序检查

### ✅ 现有复合索引（顺序正确）

1. **idx_project_type (project_id, type)**
   - 适用于：按项目查询特定类型文档
   - 查询示例：`WHERE project_id = 1 AND type = 'document'`

2. **idx_project_status (project_id, status)**
   - 适用于：按项目查询特定状态文档
   - 查询示例：`WHERE project_id = 1 AND status = 'completed'`

3. **idx_chunk_document (document_id, chunk_index)**
   - 适用于：查询文档的所有 chunk（按顺序）
   - 查询示例：`WHERE document_id = 123 ORDER BY chunk_index`

4. **idx_chunk_project (project_id, created_at)**
   - 适用于：按项目查询最新 chunks
   - 查询示例：`WHERE project_id = 1 ORDER BY created_at DESC`

---

## 第五部分：执行计划验证

### 验证方法

**1. SQLite 验证：**
```bash
# 检查查询是否走索引
sqlite3 fieldmind.db "EXPLAIN QUERY PLAN SELECT * FROM documents WHERE project_id = 1 ORDER BY uploaded_at DESC;"

# 期望输出（走索引）：
# SEARCH TABLE documents USING INDEX idx_project_uploaded (project_id=? AND uploaded_at>?)

# 不好的输出（全表扫描）：
# SCAN TABLE documents
```

**2. PostgreSQL 验证：**
```sql
-- 检查索引使用情况
EXPLAIN ANALYZE 
SELECT * FROM documents 
WHERE project_id = 1 
ORDER BY uploaded_at DESC 
LIMIT 20;

-- 期望看到：
-- Index Scan using idx_project_uploaded on documents
-- Planning Time: 0.1 ms
-- Execution Time: 0.5 ms

-- 不好的情况：
-- Seq Scan on documents (全表扫描)
```

---

## 第六部分：修复清单

### 立即修复（高优先级）

#### 1. 修复 DATE() 函数问题

**文件：** `backend/src/app/services/analysis/trend_analysis.py`

**修改前（10+ 处）：**
```python
sql = f"""
    SELECT DATE(created_at) as date, COUNT(*) as count
    FROM documents
    WHERE project_id = :project_id
    GROUP BY DATE(created_at)
"""
```

**修改后：**
```python
# 方案 A：使用日期范围查询
from datetime import datetime, timedelta

def get_trend_data(project_id: int, days: int = 30):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 这样可以走索引
    sql = f"""
        SELECT 
            date_trunc('day', created_at) as date,
            COUNT(*) as count
        FROM documents
        WHERE project_id = :project_id
          AND created_at >= :start_date
          AND created_at < :end_date
        GROUP BY date_trunc('day', created_at)
        ORDER BY date
    """
    
    result = session.execute(
        text(sql),
        {"project_id": project_id, "start_date": start_date, "end_date": end_date}
    )
    return result.fetchall()
```

#### 2. 添加 uploaded_at 索引

**文件：** `backend/src/app/models/document.py`

**第 59 行修改：**
```python
# 修改前
uploaded_at = Column(DateTime, comment="上传时间")

# 修改后
uploaded_at = Column(DateTime, index=True, comment="上传时间")
```

#### 3. 添加复合索引

**文件：** `backend/src/app/models/document.py`

**第 113-116 行修改：**
```python
# 修改前
__table_args__ = (
    Index('idx_project_type', 'project_id', 'type'),
    Index('idx_project_status', 'project_id', 'status'),
)

# 修改后
__table_args__ = (
    Index('idx_project_type', 'project_id', 'type'),
    Index('idx_project_status', 'project_id', 'status'),
    Index('idx_project_uploaded', 'project_id', 'uploaded_at'),  # 新增
    Index('idx_project_created', 'project_id', 'created_at'),     # 新增（如果经常按创建时间排序）
)
```

### 数据库迁移 SQL

**创建新索引（如果表已存在）：**
```sql
-- PostgreSQL / SQLite 通用
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_documents_project_uploaded ON documents(project_id, uploaded_at);
CREATE INDEX IF NOT EXISTS idx_documents_project_created ON documents(project_id, created_at);
```

---

## 第七部分：验证修复效果

### 验证脚本

创建文件：`backend/scripts/verify_indexes.py`

```python
"""
索引验证脚本
"""
import time
from sqlalchemy import create_engine, text
from app.core.config import settings

def verify_indexes():
    engine = create_engine(settings.database_url)
    
    print("=" * 80)
    print("索引验证开始")
    print("=" * 80)
    
    with engine.connect() as conn:
        # 1. 检查索引是否存在
        print("\n1. 检查索引是否存在...")
        
        if 'postgresql' in settings.database_url:
            result = conn.execute(text("""
                SELECT indexname, tablename, indexdef
                FROM pg_indexes
                WHERE tablename IN ('documents', 'document_chunks')
                ORDER BY tablename, indexname;
            """))
        else:  # SQLite
            result = conn.execute(text("""
                SELECT name, tbl_name, sql
                FROM sqlite_master
                WHERE type = 'index'
                  AND tbl_name IN ('documents', 'document_chunks')
                ORDER BY tbl_name, name;
            """))
        
        for row in result:
            print(f"  ✓ {row[0]} on {row[1]}")
        
        # 2. 测试查询性能
        print("\n2. 测试查询性能...")
        
        # 测试 1：按项目 + 上传时间排序
        start = time.time()
        conn.execute(text("""
            SELECT id, name, uploaded_at
            FROM documents
            WHERE project_id = 1
            ORDER BY uploaded_at DESC
            LIMIT 20;
        """))
        elapsed = time.time() - start
        print(f"  查询 1（按上传时间排序）: {elapsed*1000:.2f} ms")
        
        # 测试 2：按项目 + 状态过滤
        start = time.time()
        conn.execute(text("""
            SELECT COUNT(*)
            FROM documents
            WHERE project_id = 1 AND status = 'completed';
        """))
        elapsed = time.time() - start
        print(f"  查询 2（按状态过滤）: {elapsed*1000:.2f} ms")
        
        # 测试 3：查询文档的所有 chunks
        start = time.time()
        conn.execute(text("""
            SELECT id, chunk_index, text
            FROM document_chunks
            WHERE document_id = 1
            ORDER BY chunk_index;
        """))
        elapsed = time.time() - start
        print(f"  查询 3（查询 chunks）: {elapsed*1000:.2f} ms")
        
        print("\n" + "=" * 80)
        print("✅ 验证完成")
        print("=" * 80)

if __name__ == "__main__":
    verify_indexes()
```

---

## 第八部分：性能对比

### 预期性能提升

| 查询场景 | 修复前 | 修复后 | 提升 |
|---------|--------|--------|------|
| 按项目查询最新文档（1000 文档） | ~50ms | ~5ms | 10x |
| 按日期统计文档数（30天） | ~200ms | ~20ms | 10x |
| 查询文档的所有 chunks（100 chunks） | ~10ms | ~2ms | 5x |
| 按状态过滤文档 | ~30ms | ~3ms | 10x |

---

## 第九部分：执行步骤

### 1. 备份数据库
```bash
# PostgreSQL
pg_dump fieldmind > backup_$(date +%Y%m%d).sql

# SQLite
cp fieldmind.db fieldmind.db.backup_$(date +%Y%m%d)
```

### 2. 修改代码
按照"第六部分：修复清单"修改代码

### 3. 创建数据库迁移
```bash
cd backend
alembic revision --autogenerate -m "add_uploaded_at_indexes"
alembic upgrade head
```

### 4. 手动创建索引（如果迁移未自动创建）
```bash
# 连接数据库执行
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_documents_project_uploaded ON documents(project_id, uploaded_at);
```

### 5. 验证
```bash
python backend/scripts/verify_indexes.py
```

---

## 总结

### 🔴 严重问题（必须修复）
1. ✅ `uploaded_at` 缺少索引 → 影响按时间查询
2. ✅ `DATE(created_at)` 导致索引失效 → 影响趋势分析

### 🟡 优化建议（可选）
1. 添加 `(project_id, uploaded_at)` 复合索引 → 优化最新文档查询
2. 如果有文件名搜索，考虑全文搜索索引

### ✅ 良好实践
1. 大部分核心表已有合理索引
2. 复合索引顺序正确
3. 外键都有索引

---

生成完毕。
