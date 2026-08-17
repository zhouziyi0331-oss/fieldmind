# Alembic 数据库迁移指南

## 📋 概述

本项目已集成 Alembic 数据库迁移系统，用于管理 PostgreSQL 数据库的表结构变更。Alembic 提供了版本控制、自动生成迁移脚本、回滚等功能。

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install alembic==1.15.2
```

### 2. 配置数据库连接

Alembic 自动从 `app/core/config.py` 读取数据库配置，无需手动配置 `alembic.ini`。

确保 `.env` 文件包含正确的数据库配置：

```env
POSTGRES_USER=fieldmind
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=fieldmind
```

### 3. 查看当前迁移状态

```bash
alembic current
```

### 4. 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade 001

# 升级一个版本
alembic upgrade +1
```

### 5. 回滚迁移

```bash
# 回滚到上一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade 001

# 回滚所有迁移
alembic downgrade base
```

## 📝 创建新迁移

### 自动生成迁移（推荐）

当你修改了模型文件后，Alembic 可以自动检测变更并生成迁移脚本：

```bash
alembic revision --autogenerate -m "描述你的变更"
```

例如：

```bash
alembic revision --autogenerate -m "Add is_verified field to users table"
```

### 手动创建迁移

如果需要手动编写迁移逻辑：

```bash
alembic revision -m "描述你的变更"
```

然后编辑生成的文件，填写 `upgrade()` 和 `downgrade()` 函数。

## 🔍 查看迁移历史

```bash
# 查看所有迁移
alembic history

# 查看详细历史
alembic history --verbose

# 查看当前版本
alembic current
```

## 📂 项目结构

```
fieldmind-backend/
├── alembic/
│   ├── versions/           # 迁移脚本目录
│   │   └── 001_initial_migration.py
│   ├── env.py             # Alembic 环境配置
│   ├── script.py.mako     # 迁移脚本模板
│   └── README
├── alembic.ini            # Alembic 配置文件
└── app/
    ├── models/            # SQLAlchemy 模型
    └── core/
        ├── config.py      # 应用配置
        └── database.py    # 数据库连接
```

## 🎯 迁移最佳实践

### 1. 始终先备份数据库

```bash
pg_dump -U fieldmind fieldmind > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 在开发环境测试迁移

```bash
# 应用迁移
alembic upgrade head

# 如有问题，立即回滚
alembic downgrade -1
```

### 3. 审查自动生成的迁移

自动生成的迁移可能不完美，始终检查生成的代码：

```bash
# 生成迁移后
cat alembic/versions/最新文件名.py
```

重点检查：
- 是否正确检测到所有变更
- 是否有意外的删除操作
- 索引和约束是否正确
- downgrade() 函数是否正确

### 4. 使用有意义的迁移消息

```bash
# ❌ 不好
alembic revision --autogenerate -m "update"

# ✅ 好
alembic revision --autogenerate -m "Add email verification fields to users"
```

### 5. 一次迁移做一件事

不要在一个迁移中混合多个不相关的变更：

```bash
# ❌ 不好
alembic revision -m "Add user fields and fix documents and update contexts"

# ✅ 好
alembic revision -m "Add email and phone to users table"
alembic revision -m "Add status index to documents table"
alembic revision -m "Add parent_id to contexts table"
```

## 🛠️ 常用操作示例

### 添加新字段

1. 修改模型文件：

```python
# app/models/user.py
class User(Base):
    # ...
    phone = Column(String(20), nullable=True)  # 新增字段
```

2. 生成迁移：

```bash
alembic revision --autogenerate -m "Add phone field to users"
```

3. 应用迁移：

```bash
alembic upgrade head
```

### 创建新表

1. 创建新模型：

```python
# app/models/notification.py
from app.core.database import Base
from sqlalchemy import Column, String, DateTime, Boolean

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
```

2. 在 `alembic/env.py` 中导入新模型：

```python
from app.models.notification import Notification
```

3. 生成迁移：

```bash
alembic revision --autogenerate -m "Create notifications table"
```

### 修改字段类型

**注意**：修改字段类型可能需要数据转换，建议手动编写迁移。

```python
def upgrade():
    # 使用 ALTER COLUMN
    op.alter_column('users', 'age',
                    existing_type=sa.String(10),
                    type_=sa.Integer(),
                    postgresql_using='age::integer')

def downgrade():
    op.alter_column('users', 'age',
                    existing_type=sa.Integer(),
                    type_=sa.String(10),
                    postgresql_using='age::varchar')
```

### 删除字段

1. 从模型中移除字段
2. 生成迁移：

```bash
alembic revision --autogenerate -m "Remove deprecated_field from users"
```

3. **重要**：在生产环境删除字段前，确保应用代码已不再使用该字段

## ⚠️ 生产环境注意事项

### 1. 零停机迁移策略

对于大型表的结构变更，考虑分步骤进行：

**步骤 1**：添加新字段（nullable=True）
```bash
alembic revision --autogenerate -m "Add new_field to users (nullable)"
alembic upgrade head
```

**步骤 2**：更新应用代码，开始使用新字段

**步骤 3**：数据迁移（如果需要）
```sql
UPDATE users SET new_field = old_field;
```

**步骤 4**：设置字段为 NOT NULL
```bash
alembic revision -m "Make new_field required"
# 手动编辑迁移文件
alembic upgrade head
```

**步骤 5**：删除旧字段
```bash
alembic revision --autogenerate -m "Remove old_field from users"
alembic upgrade head
```

### 2. 索引管理

创建大表的索引可能很慢，考虑使用 CONCURRENTLY：

```python
def upgrade():
    # PostgreSQL 的并发索引创建
    op.execute('CREATE INDEX CONCURRENTLY idx_users_email ON users(email)')

def downgrade():
    op.execute('DROP INDEX CONCURRENTLY idx_users_email')
```

### 3. 监控迁移执行

```bash
# 使用 time 命令监控执行时间
time alembic upgrade head

# 查看 PostgreSQL 进程
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

## 🐛 故障排查

### 问题 1：迁移冲突

```
FAILED: Multiple head revisions are present
```

**解决方案**：合并分支

```bash
alembic merge -m "Merge heads" head1 head2
alembic upgrade head
```

### 问题 2：迁移卡住

**解决方案**：检查数据库锁

```sql
-- 查看锁定的表
SELECT * FROM pg_locks WHERE granted = false;

-- 终止阻塞的进程
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'active' AND query LIKE '%your_table%';
```

### 问题 3：迁移失败需要手动修复

```bash
# 1. 回滚迁移
alembic downgrade -1

# 2. 手动修复数据库
psql -U fieldmind fieldmind
# 执行必要的 SQL

# 3. 修改迁移脚本
vim alembic/versions/xxx.py

# 4. 重新应用
alembic upgrade head
```

### 问题 4：版本表损坏

```bash
# 删除并重建版本表
alembic stamp head --purge
alembic stamp head
```

## 📊 当前数据库架构

本项目包含以下 18 个数据表：

### 核心表
- `users` - 用户表
- `projects` - 项目表
- `documents` - 文档表
- `entities` - 实体表
- `contexts` - 脉络表

### 关系表
- `project_documents` - 项目-文档关联
- `project_contexts` - 项目-脉络关联
- `project_chat_sessions` - 项目-对话关联
- `project_chat_messages` - 项目-消息关联
- `project_memories` - 项目记忆

### 对话表
- `chat_sessions` - 对话会话
- `chat_messages` - 对话消息

### 功能表
- `skills` - 技能模板
- `skill_validations` - 技能验证
- `timeline_events` - 时间线事件
- `analysis_reports` - 分析报告
- `reports` - 报告
- `industry_categories` - 业态分类

## 🔗 相关资源

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)

## 📞 支持

遇到问题？查看：
- 项目 README.md
- SESSION_SUMMARY.md - 最近的变更历史
- MIGRATION_SUMMARY.md - 框架迁移总结
