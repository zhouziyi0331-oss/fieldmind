# Alembic 数据库迁移使用指南

## 📋 概述

本项目已完全集成 Alembic 数据库迁移系统，用于管理数据库 schema 的版本控制和变更。

**当前状态**: ✅ 已配置并就绪  
**当前版本**: 001 (Initial migration)  
**数据库支持**: SQLite (开发) / PostgreSQL (生产)

---

## 🚀 快速开始

### 查看当前迁移状态

```bash
# 查看当前数据库版本
alembic current

# 查看迁移历史
alembic history --verbose

# 查看待应用的迁移
alembic show head
```

### 应用迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到特定版本
alembic upgrade <revision_id>

# 升级一个版本
alembic upgrade +1
```

### 回滚迁移

```bash
# 回滚到上一个版本
alembic downgrade -1

# 回滚到特定版本
alembic downgrade <revision_id>

# 回滚所有迁移
alembic downgrade base
```

---

## 📝 创建新迁移

### 方法 1: 自动生成迁移（推荐）

Alembic 可以通过对比模型和数据库自动生成迁移脚本：

```bash
# 自动检测模型变更并生成迁移
alembic revision --autogenerate -m "add user profile fields"
```

**注意**: 使用 `--autogenerate` 前请确保：
1. 所有模型已正确导入到 `alembic/env.py`
2. 数据库已同步到当前 head 版本
3. 仔细检查生成的迁移脚本

### 方法 2: 手动创建迁移

```bash
# 创建空白迁移脚本
alembic revision -m "add custom index"
```

然后手动编辑生成的文件：

```python
def upgrade() -> None:
    """Upgrade schema."""
    # SQLite 使用 batch_alter_table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bio', sa.Text(), nullable=True))
        batch_op.create_index('ix_users_bio', ['bio'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_bio')
        batch_op.drop_column('bio')
```

---

## 🔧 常见操作示例

### 添加新字段

```python
def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('phone', sa.String(20), nullable=True)
        )

def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('phone')
```

### 修改字段类型

```python
def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'bio',
            existing_type=sa.String(500),
            type_=sa.Text(),
            existing_nullable=True
        )

def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column(
            'bio',
            existing_type=sa.Text(),
            type_=sa.String(500),
            existing_nullable=True
        )
```

### 创建新表

```python
def upgrade() -> None:
    op.create_table(
        'user_notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_notifications_user_id', 'user_notifications', ['user_id'])
    op.create_foreign_key(
        'fk_notifications_user',
        'user_notifications', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    op.drop_table('user_notifications')
```

### 添加索引

```python
def upgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.create_index('ix_projects_status', ['status'])

def downgrade() -> None:
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_index('ix_projects_status')
```

### 数据迁移

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # 1. 添加新字段
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(20), nullable=True))
    
    # 2. 迁移数据
    users_table = table('users',
        column('id', sa.String),
        column('is_active', sa.Boolean),
        column('status', sa.String)
    )
    
    op.execute(
        users_table.update().where(
            users_table.c.is_active == True
        ).values(status='active')
    )
    
    op.execute(
        users_table.update().where(
            users_table.c.is_active == False
        ).values(status='inactive')
    )
    
    # 3. 设置字段为 NOT NULL
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False)

def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('status')
```

---

## 🗄️ 多数据库支持

### 开发环境 (SQLite)

默认配置使用 SQLite：

```bash
# .env 或环境变量
DATABASE_URL=sqlite:///./data/fieldmind.db

# 运行迁移
alembic upgrade head
```

**重要**: SQLite 需要使用 `batch_alter_table` 来修改表结构：

```python
# ✅ 正确 - SQLite 兼容
with op.batch_alter_table('users', schema=None) as batch_op:
    batch_op.add_column(...)

# ❌ 错误 - SQLite 不支持
op.add_column('users', ...)
```

### 生产环境 (PostgreSQL)

```bash
# 设置 PostgreSQL 连接
export DATABASE_URL="postgresql://user:password@localhost:5432/fieldmind"

# 运行迁移
alembic upgrade head
```

PostgreSQL 支持直接的 ALTER TABLE 操作，但为了兼容性，建议继续使用 `batch_alter_table`。

---

## 🔄 工作流程

### 开发新功能的标准流程

1. **修改模型**
   ```python
   # app/models/user.py
   class User(Base):
       # ... 现有字段
       bio = Column(Text, nullable=True)  # 新字段
   ```

2. **生成迁移**
   ```bash
   alembic revision --autogenerate -m "add user bio field"
   ```

3. **检查生成的迁移**
   ```bash
   cat alembic/versions/xxx_add_user_bio_field.py
   ```

4. **测试迁移**
   ```bash
   # 升级
   alembic upgrade head
   
   # 验证
   alembic current
   
   # 测试回滚
   alembic downgrade -1
   
   # 重新升级
   alembic upgrade head
   ```

5. **运行测试**
   ```bash
   python3 -m pytest tests/
   ```

6. **提交代码**
   ```bash
   git add alembic/versions/xxx_add_user_bio_field.py
   git add app/models/user.py
   git commit -m "feat: add user bio field"
   ```

---

## 🐛 故障排除

### 问题 1: 表已存在错误

```
sqlalchemy.exc.OperationalError: table users already exists
```

**解决方案**: 标记数据库为已迁移状态

```bash
alembic stamp head
```

### 问题 2: 迁移版本不一致

```
ERROR: Can't locate revision identified by 'xxx'
```

**解决方案**: 查看迁移历史并手动同步

```bash
# 查看数据库版本
alembic current

# 查看文件系统中的迁移
alembic history

# 手动设置版本
alembic stamp <revision_id>
```

### 问题 3: PostgreSQL 连接失败

```
connection to server at "localhost" failed
```

**解决方案**: 确保使用正确的数据库 URL

```bash
# 开发环境使用 SQLite
export DATABASE_URL="sqlite:///./data/fieldmind.db"

# 或修改 .env 文件
DATABASE_URL=sqlite:///./data/fieldmind.db
```

### 问题 4: SQLite 列已存在

```
sqlite3.OperationalError: duplicate column name: role
```

**解决方案**: 在迁移中添加条件检查

```python
from alembic import op
from sqlalchemy import inspect

def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'role' not in columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('role', sa.String(50)))
```

---

## 📚 最佳实践

### 1. 迁移命名规范

使用清晰描述性的名称：

```bash
# ✅ 好的命名
alembic revision -m "add_user_email_verification"
alembic revision -m "create_notifications_table"
alembic revision -m "add_index_on_projects_status"

# ❌ 不好的命名
alembic revision -m "update"
alembic revision -m "fix"
alembic revision -m "changes"
```

### 2. 始终提供 downgrade

每个迁移都应该有可逆的 `downgrade()` 函数：

```python
def upgrade() -> None:
    """添加字段"""
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('verified', sa.Boolean(), default=False))

def downgrade() -> None:
    """回滚: 删除字段"""
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('verified')
```

### 3. 测试迁移的双向操作

```bash
# 测试升级
alembic upgrade head

# 测试降级
alembic downgrade -1

# 再次升级验证
alembic upgrade head
```

### 4. 使用事务

大型数据迁移使用事务确保原子性：

```python
def upgrade() -> None:
    connection = op.get_bind()
    
    # Alembic 自动在事务中运行，但可以显式控制
    with connection.begin():
        # 多个操作
        op.execute("UPDATE users SET status = 'active' WHERE is_active = true")
        op.execute("UPDATE users SET status = 'inactive' WHERE is_active = false")
```

### 5. 分解大型迁移

将复杂变更分解为多个小迁移：

```bash
# 第一步：添加新字段（可选）
alembic revision -m "add_user_status_field"

# 第二步：迁移数据
alembic revision -m "migrate_user_status_data"

# 第三步：删除旧字段
alembic revision -m "remove_user_is_active_field"
```

### 6. 文档化复杂迁移

在迁移文件顶部添加详细说明：

```python
"""Add user email verification system

This migration adds the email verification functionality:
1. Adds 'email_verified' boolean field (default False)
2. Adds 'verification_token' string field
3. Adds 'verification_sent_at' datetime field
4. Creates index on verification_token for faster lookup

Related: Issue #123, PR #456

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2026-07-31 12:00:00.000000
"""
```

---

## 🔐 生产环境部署

### 部署前检查清单

- [ ] 已在开发环境测试迁移
- [ ] 已测试 upgrade 和 downgrade
- [ ] 已备份生产数据库
- [ ] 已在预发布环境验证
- [ ] 已准备回滚计划
- [ ] 已通知相关团队

### 部署步骤

```bash
# 1. 备份数据库
pg_dump -h localhost -U fieldmind fieldmind > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 查看将要应用的迁移
alembic history
alembic current

# 3. 应用迁移
alembic upgrade head

# 4. 验证
alembic current
python3 -m pytest tests/

# 5. 如需回滚
alembic downgrade -1
```

### Docker 部署

在 `docker-compose.yml` 中添加迁移步骤：

```yaml
services:
  backend:
    build: .
    command: >
      sh -c "alembic upgrade head && 
             uvicorn app.main:app --host 0.0.0.0 --port 8000"
    depends_on:
      - db
```

或使用初始化容器：

```yaml
services:
  migrate:
    build: .
    command: alembic upgrade head
    depends_on:
      - db
    restart: "no"
  
  backend:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    depends_on:
      - migrate
```

---

## 🧪 测试环境配置

测试使用独立的临时数据库，不受 Alembic 管理：

```python
# tests/conftest.py
import tempfile
import os

# 使用临时数据库
test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{test_db_file.name}"

# 测试使用 Base.metadata.create_all() 快速创建表
# 不需要运行 Alembic 迁移
```

这样测试运行更快，且不依赖迁移历史。

---

## 📊 项目当前状态

### 迁移历史

```
<base> -> 001 (head)
```

### 版本 001: Initial migration

**创建时间**: 2026-07-31 21:30:00  
**状态**: ✅ 已应用

**包含的表**:
- users (用户表)
- projects (项目表)
- project_documents (项目文档关联表)
- project_contexts (项目上下文关联表)
- project_chat_sessions (项目会话关联表)
- project_chat_messages (项目消息关联表)
- project_memories (项目记忆表)
- documents (文档表)
- entities (实体表)
- contexts (上下文表)
- chat_sessions (会话表)
- chat_messages (消息表)
- skills (技能表)
- skill_validations (技能验证表)
- timeline_events (时间线事件表)
- analysis_reports (分析报告表)
- reports (报告表)
- industry_categories (行业分类表)

### 配置文件

- **Alembic 配置**: `alembic.ini`
- **环境脚本**: `alembic/env.py`
- **迁移目录**: `alembic/versions/`
- **模板文件**: `alembic/script.py.mako`

---

## 🔗 相关资源

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [项目数据库文档](app/models/)
- [API 文档](http://localhost:8000/docs)

---

## 📞 支持

如有问题，请参考：
1. 本文档的"故障排除"部分
2. Alembic 官方文档
3. 项目 Issue 追踪

---

**最后更新**: 2026-08-01  
**维护者**: FieldMind Team
