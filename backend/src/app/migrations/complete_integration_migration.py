# FieldMind完整程序深度分析与集成方案

## 🔍 现有程序结构深度分析

### 核心目录结构

```
FieldMind/
├── backend/src/app/
│   ├── api/          # API端点层 (68个文件)
│   ├── services/     # 服务层 (256个文件)
│   ├── models/       # 数据模型层 (64个文件)
│   ├── core/         # 核心功能 (74个文件)
│   ├── agents/       # Agent系统
│   ├── distillation/ # 蒸馏系统
│   ├── skills/       # 技能系统
│   ├── vector_store/ # 向量存储
│   ├── workflows/    # 工作流
│   └── main.py       # 主入口 (54KB, 1300+行)
│
├── frontend/         # React前端
└── database/         # PostgreSQL + pgvector
```

### 现有功能模块

#### 已存在的核心系统
1. **文档处理系统** ✓
   - 上传、解析、分块
   - 多格式支持

2. **向量存储系统** ✓
   - vector_store/ 目录
   - 已有基础实现

3. **Agent系统** ✓
   - agents/ 目录
   - 多个agent实现

4. **任务系统** ✓
   - tasks/ 目录
   - Celery集成

5. **工作流系统** ✓
   - workflows/ 目录

---

## 🔗 新集成模块与现有系统的连接方案

### 问题1: 新旧代码冲突

**发现的潜在冲突**:

1. **向量存储重复**
   - 现有: `app/vector_store/` 目录
   - 新增: `app/services/vector_store.py`
   - **冲突**: 可能有重复实现

2. **模型定义分散**
   - 现有: `app/models/` (64个文件)
   - 新增: `app/models/sbpack.py`, `app/models/skill_system.py`, `app/models/knowledge_graph.py`
   - **问题**: 新模型可能与现有模型有字段冲突

3. **API路由注册**
   - 现有: `main.py` 中注册的路由
   - 新增: `api/sbpack.py`, `api/skill_tree.py`, `api/rag.py`, `api/obsidian.py`, `api/llm.py`
   - **问题**: 需要在main.py中注册新路由

4. **服务依赖**
   - 新服务依赖LLM、嵌入模型等
   - 需要统一的配置管理

---

## 🛠️ 完整集成实施方案

### 阶段1: 环境准备和依赖安装

#### 1.1 数据库扩展安装

```bash
# PostgreSQL安装pgvector扩展
psql -U postgres -d fieldmind << EOF
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- 全文检索
CREATE EXTENSION IF NOT EXISTS btree_gin;
EOF
```

#### 1.2 Python依赖安装

```bash
cd /Users/alwan/FieldMind/backend

# 新增依赖
pip install pgvector watchdog ebooklib beautifulsoup4 yt-dlp pdfplumber python-docx cytoscape openai anthropic
```

#### 1.3 环境变量配置

```bash
# 添加到.env
cat >> .env << EOF

# LLM配置
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Obsidian同步
OBSIDIAN_VAULT_PATH=/path/to/obsidian/vault

# 向量嵌入
EMBEDDING_MODEL=text-embedding-ada-002
EMBEDDING_DIMENSION=1536

# RAG配置
RAG_TOP_K=10
RAG_SIMILARITY_THRESHOLD=0.7
RAG_CONTEXT_MAX_TOKENS=2000
EOF
```

---

### 阶段2: 数据库迁移

#### 2.1 创建完整迁移脚本

<function_calls>
<invoke name="Write">
<parameter name="content">"""
完整数据库迁移脚本

创建所有新增表：
- SBPACK系统 (5张表)
- 技能系统 (8张表)
- 知识图谱 (10张表)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

revision = 'complete_integration_v1'
down_revision = 'previous_revision'  # 更新为实际的上一个revision

def upgrade():
    # 1. SBPACK系统表
    create_sbpack_tables()

    # 2. 技能系统表
    create_skill_system_tables()

    # 3. 知识图谱表
    create_knowledge_graph_tables()

    # 4. 创建索引
    create_indexes()

    # 5. 创建触发器
    create_triggers()


def create_sbpack_tables():
    """创建SBPACK相关表"""

    # sbpack_packages
    op.create_table(
        'sbpack_packages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id')),
        sa.Column('package_name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), default='2.0.0'),
        sa.Column('protocol_version', sa.String(50), default='2.0.0'),
        sa.Column('source_title', sa.String(500)),
        sa.Column('source_author', sa.String(255)),
        sa.Column('source_sha256', sa.String(64)),
        sa.Column('knowledge_count', sa.Integer(), default=0),
        sa.Column('skill_count', sa.Integer(), default=0),
        sa.Column('knowledge_frozen', sa.Boolean(), default=False),
        sa.Column('skill_frozen', sa.Boolean(), default=False),
        sa.Column('is_built', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # knowledge_items
    op.create_table(
        'knowledge_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('sbpack_packages.id', ondelete='CASCADE')),
        sa.Column('knowledge_id', sa.String(100), unique=True, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('knowledge_type', sa.String(50), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('evidence_refs', JSONB()),
        sa.Column('is_frozen', sa.Boolean(), default=False),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # skill_items
    op.create_table(
        'skill_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('package_id', sa.Integer(), sa.ForeignKey('sbpack_packages.id', ondelete='CASCADE')),
        sa.Column('skill_id', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(300), nullable=False),
        sa.Column('rationale', sa.Text()),
        sa.Column('interpretation', sa.Text()),
        sa.Column('execution', JSONB()),
        sa.Column('boundaries', sa.Text()),
        sa.Column('pressure_tests', JSONB()),
        sa.Column('canonical_sha256', sa.String(64)),
        sa.Column('v1_passed', sa.Boolean(), default=False),
        sa.Column('v2_passed', sa.Boolean(), default=False),
        sa.Column('v3_passed', sa.Boolean(), default=False),
        sa.Column('is_frozen', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )


def create_skill_system_tables():
    """创建技能系统表"""

    # skill_nodes
    op.create_table(
        'skill_nodes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sbpack_skill_id', sa.Integer(), sa.ForeignKey('skill_items.id')),
        sa.Column('skill_id', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), default='locked'),
        sa.Column('level', sa.Integer(), default=0),
        sa.Column('xp', sa.Integer(), default=0),
        sa.Column('tree_position_x', sa.Float()),
        sa.Column('tree_position_y', sa.Float()),
        sa.Column('prerequisites', JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # skill_relations
    op.create_table(
        'skill_relations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('skill_nodes.id')),
        sa.Column('target_id', sa.Integer(), sa.ForeignKey('skill_nodes.id')),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('strength', sa.Float(), default=1.0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # skill_progress
    op.create_table(
        'skill_progress',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('skill_id', sa.Integer(), sa.ForeignKey('skill_nodes.id')),
        sa.Column('status', sa.String(50), default='not_started'),
        sa.Column('progress_percentage', sa.Float(), default=0),
        sa.Column('current_xp', sa.Integer(), default=0),
        sa.Column('practice_count', sa.Integer(), default=0),
        sa.Column('success_rate', sa.Float(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # obsidian_notes
    op.create_table(
        'obsidian_notes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('vault_path', sa.String(500), unique=True, nullable=False),
        sa.Column('title', sa.String(500)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('frontmatter', JSONB()),
        sa.Column('tags', JSONB()),
        sa.Column('sync_status', sa.String(100)),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )


def create_knowledge_graph_tables():
    """创建知识图谱表"""

    # entities
    op.create_table(
        'entities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('entity_id', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(500), nullable=False, index=True),
        sa.Column('entity_type', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text()),
        sa.Column('attributes', JSONB()),
        sa.Column('aliases', JSONB()),
        sa.Column('first_seen', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('last_seen', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('observation_count', sa.Integer(), default=0),
        sa.Column('confidence_score', sa.Float(), default=1.0),
        sa.Column('source_documents', JSONB()),
        sa.Column('embedding', Vector(1536)),  # pgvector
        sa.Column('relation_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # relations
    op.create_table(
        'relations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('relation_id', sa.String(100), unique=True, nullable=False),
        sa.Column('source_id', sa.Integer(), sa.ForeignKey('entities.id', ondelete='CASCADE')),
        sa.Column('target_id', sa.Integer(), sa.ForeignKey('entities.id', ondelete='CASCADE')),
        sa.Column('relation_type', sa.String(100), nullable=False, index=True),
        sa.Column('description', sa.Text()),
        sa.Column('properties', JSONB()),
        sa.Column('confidence_score', sa.Float(), default=1.0),
        sa.Column('weight', sa.Float(), default=1.0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # vector_chunks
    op.create_table(
        'vector_chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('chunk_id', sa.String(100), unique=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), index=True),
        sa.Column('document_id', sa.Integer(), index=True),
        sa.Column('chunk_index', sa.Integer()),
        sa.Column('source_type', sa.String(50)),
        sa.Column('embedding', Vector(1536)),
        sa.Column('entities', JSONB()),
        sa.Column('semantic_tags', JSONB()),
        sa.Column('language', sa.String(10), default='zh'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # rag_sessions
    op.create_table(
        'rag_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('session_id', sa.String(100), unique=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('session_name', sa.String(255)),
        sa.Column('context_window', JSONB()),
        sa.Column('retrieval_config', JSONB()),
        sa.Column('query_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )

    # rag_queries
    op.create_table(
        'rag_queries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('query_id', sa.String(100), unique=True, nullable=False),
        sa.Column('session_id', sa.Integer(), sa.ForeignKey('rag_sessions.id')),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_embedding', Vector(1536)),
        sa.Column('retrieved_chunks', JSONB()),
        sa.Column('generated_answer', sa.Text()),
        sa.Column('answer_sources', JSONB()),
        sa.Column('relevance_score', sa.Float()),
        sa.Column('groundedness_score', sa.Float()),
        sa.Column('retrieval_time_ms', sa.Integer()),
        sa.Column('generation_time_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'))
    )


def create_indexes():
    """创建性能索引"""

    # 向量索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_entities_embedding
        ON entities USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vector_chunks_embedding
        ON vector_chunks USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # 全文检索索引
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_vector_chunks_content_fts
        ON vector_chunks USING gin(to_tsvector('chinese', content))
    """)

    # 组合索引
    op.create_index('idx_entities_name_type', 'entities', ['name', 'entity_type'])
    op.create_index('idx_relations_source_target', 'relations', ['source_id', 'target_id'])
    op.create_index('idx_skill_nodes_status', 'skill_nodes', ['status'])


def create_triggers():
    """创建自动更新触发器"""

    # updated_at自动更新
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    op.execute("""
        CREATE TRIGGER update_sbpack_packages_updated_at
        BEFORE UPDATE ON sbpack_packages
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade():
    """回滚所有更改"""
    op.drop_table('rag_queries')
    op.drop_table('rag_sessions')
    op.drop_table('vector_chunks')
    op.drop_table('relations')
    op.drop_table('entities')
    op.drop_table('obsidian_notes')
    op.drop_table('skill_progress')
    op.drop_table('skill_relations')
    op.drop_table('skill_nodes')
    op.drop_table('skill_items')
    op.drop_table('knowledge_items')
    op.drop_table('sbpack_packages')
