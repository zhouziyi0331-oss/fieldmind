# FieldMind 数据库初始化指南

## 阶段0 - Week 1 - Day 1-2：数据库设计与初始化

### 📋 完成的工作

1. ✅ 设计了完整的数据库Schema（12个核心表）
2. ✅ 创建了SQL迁移脚本
3. ✅ 创建了所有SQLAlchemy ORM模型
4. ✅ 创建了数据库迁移工具
5. ✅ 创建了数据库配置文件
6. ✅ 创建了完整的测试脚本

---

## 🗄️ 数据库表结构

### 核心表（12个）

1. **documents** - 文档主表
2. **document_metadata** - 文档元数据表
3. **entities** - 实体表
4. **document_entities** - 文档-实体关系表
5. **entity_relations** - 实体关系表
6. **tags** - 标签表
7. **document_tags** - 文档-标签关系表
8. **document_chunks** - 文本分块表（RAG）
9. **embeddings** - 向量嵌入表
10. **timeline_events** - 时间线事件表
11. **processing_tasks** - 处理任务表
12. **quality_reports** - 数据质量报告表

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env

# 编辑 .env 文件，填入数据库配置
# DB_HOST=localhost
# DB_PORT=3306
# DB_USER=root
# DB_PASSWORD=your_password
# DB_NAME=fieldmind
```

### 2. 创建数据库

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE fieldmind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 退出
exit
```

### 3. 执行迁移

```bash
# 方法1: 使用迁移工具（推荐）
cd backend
python src/app/core/migrate.py migrate

# 方法2: 直接执行SQL文件
mysql -u root -p fieldmind < src/app/migrations/001_initial_schema.sql

# 方法3: 使用SQLAlchemy创建表（仅开发环境）
python src/app/core/database.py init
```

### 4. 验证安装

```bash
# 运行测试脚本
python test_database_init.py
```

**预期输出**:
```
✅ 通过: 10/10
❌ 失败: 0/10

🎉 所有测试通过！数据库初始化成功！
```

---

## 📁 项目结构

```
backend/
├── src/
│   └── app/
│       ├── core/
│       │   ├── database.py          # 数据库配置
│       │   └── migrate.py           # 迁移工具
│       ├── models/
│       │   ├── __init__.py          # 模型统一导入
│       │   ├── document.py          # 文档模型
│       │   ├── document_metadata.py # 元数据模型
│       │   ├── entity.py            # 实体模型
│       │   ├── tag.py               # 标签模型
│       │   ├── document_chunk.py    # 分块模型
│       │   └── support_models.py    # 其他支持模型
│       └── migrations/
│           └── 001_initial_schema.sql # 初始Schema
├── .env.example                     # 环境配置模板
├── requirements.txt                 # Python依赖
└── test_database_init.py           # 测试脚本
```

---

## 🔧 迁移工具使用

### 查看迁移状态

```bash
python src/app/core/migrate.py status
```

### 执行迁移

```bash
python src/app/core/migrate.py migrate
```

### 回滚迁移（暂未实现）

```bash
python src/app/core/migrate.py rollback
```

---

## 📝 ORM模型使用示例

### 创建文档

```python
from app.core.database import get_db_context
from app.models import Document, DocumentType, DocumentStatus

with get_db_context() as db:
    document = Document(
        id="doc_001",
        project_id=1,
        name="example.pdf",
        type=DocumentType.DOCUMENT,
        mime_type="application/pdf",
        file_size=1024000,
        file_path="/storage/doc_001.pdf",
        hash="abc123",
        status=DocumentStatus.UPLOADED
    )
    db.add(document)
    db.commit()
```

### 查询文档

```python
with get_db_context() as db:
    # 查询单个文档
    doc = db.query(Document).filter_by(id="doc_001").first()
    
    # 查询项目的所有文档
    docs = db.query(Document).filter_by(project_id=1).all()
    
    # 查询特定类型的文档
    images = db.query(Document).filter_by(type=DocumentType.IMAGE).all()
```

### 添加元数据

```python
from app.models import DocumentMetadata

with get_db_context() as db:
    metadata = DocumentMetadata(
        document_id="doc_001",
        metadata_type="exif",
        metadata={"camera": "iPhone 14", "location": "Beijing"},
        confidence=0.95
    )
    db.add(metadata)
    db.commit()
```

### 关系查询

```python
with get_db_context() as db:
    doc = db.query(Document).filter_by(id="doc_001").first()
    
    # 查询文档的所有元数据
    for meta in doc.metadata_entries:
        print(meta.metadata_type, meta.metadata)
    
    # 查询文档的所有实体
    for doc_entity in doc.entities:
        entity = doc_entity.entity
        print(entity.text, entity.type)
    
    # 查询文档的所有标签
    for doc_tag in doc.tags:
        tag = doc_tag.tag
        print(tag.name, tag.color)
```

---

## 🧪 测试

### 运行完整测试

```bash
python test_database_init.py
```

### 测试覆盖

测试脚本包含10个测试用例：

1. ✅ 数据库连接测试
2. ✅ 表创建测试
3. ✅ 文档插入测试
4. ✅ 文档查询测试
5. ✅ 元数据插入测试
6. ✅ 实体插入测试
7. ✅ 标签插入测试
8. ✅ 分块插入测试
9. ✅ 关系查询测试
10. ✅ 数据清理测试

---

## 🔍 常见问题

### Q1: 连接数据库失败

**A**: 检查以下配置：
- MySQL服务是否运行
- .env文件中的数据库配置是否正确
- 数据库用户是否有权限

### Q2: 表已存在错误

**A**: 如果需要重新创建表：
```bash
# 删除所有表（危险操作）
python src/app/core/database.py drop

# 重新创建
python src/app/core/migrate.py migrate
```

### Q3: 字符编码问题

**A**: 确保数据库使用utf8mb4编码：
```sql
ALTER DATABASE fieldmind CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 📊 数据库索引说明

所有表都配置了合适的索引以优化查询性能：

- **主键索引**: 所有表的id字段
- **外键索引**: 所有关系字段
- **复合索引**: 常用查询组合（如project_id + type）
- **唯一索引**: 防止重复数据（如hash, text+type）

---

## 🎯 下一步

Day 1-2任务已完成！接下来：

**Day 3-4**: 对象存储配置
- 部署MinIO或配置S3
- 实现文件上传/下载工具类
- 测试对象存储功能

**Day 5**: 向量数据库配置
- 配置pgvector扩展
- 实现向量操作工具类
- 测试向量检索性能

---

## 📚 参考资源

- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [FastAPI数据库指南](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [MySQL 8.0文档](https://dev.mysql.com/doc/refman/8.0/en/)

---

**状态**: ✅ Day 1-2 完成  
**日期**: 2024-01-20  
**质量**: 所有测试通过，代码审查通过
