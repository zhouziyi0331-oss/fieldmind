# FieldMind Backend - Python FastAPI

田野调查知识管理系统 - AI后端服务

## 技术栈

- **框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL (关系数据) + Neo4j (知识图谱) + ChromaDB (向量)
- **AI**: LangChain + Whisper + HanLP
- **任务队列**: Celery + Redis
- **搜索**: Whoosh + Elasticsearch

## 目录结构

```
fieldmind-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── dependencies.py      # 依赖注入
│   │
│   ├── api/                 # API路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── audio.py     # 音频上传/转录
│   │   │   ├── documents.py # 文档管理
│   │   │   ├── search.py    # 统一搜索
│   │   │   ├── rag.py       # RAG问答
│   │   │   ├── knowledge_graph.py  # 知识图谱
│   │   │   ├── workflows.py # 工作流
│   │   │   └── auth.py      # 认证授权
│   │   └── websockets.py    # WebSocket端点
│   │
│   ├── core/                # 核心服务
│   │   ├── __init__.py
│   │   ├── transcription.py # 语音转录服务
│   │   ├── rag_engine.py    # RAG引擎
│   │   ├── knowledge_graph.py  # 知识图谱服务
│   │   ├── search_engine.py # 搜索引擎
│   │   ├── topic_modeling.py   # 主题建模
│   │   ├── vector_store.py  # 向量存储
│   │   └── encryption.py    # 加密服务
│   │
│   ├── agents/              # Agent系统
│   │   ├── __init__.py
│   │   ├── workflow_engine.py  # 工作流引擎
│   │   ├── research_agent.py   # 研究Agent
│   │   └── analysis_agent.py   # 分析Agent
│   │
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── audio.py
│   │   └── knowledge_graph.py
│   │
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── document.py
│   │   └── search.py
│   │
│   ├── db/                  # 数据库
│   │   ├── __init__.py
│   │   ├── session.py       # 数据库会话
│   │   ├── postgres.py      # PostgreSQL
│   │   ├── neo4j_client.py  # Neo4j客户端
│   │   └── vector_db.py     # ChromaDB客户端
│   │
│   ├── tasks/               # Celery任务
│   │   ├── __init__.py
│   │   ├── transcription.py
│   │   └── indexing.py
│   │
│   └── utils/               # 工具函数
│       ├── __init__.py
│       ├── file_handler.py
│       └── logger.py
│
├── tests/                   # 测试
├── alembic/                 # 数据库迁移
├── requirements.txt         # 依赖
├── Dockerfile              # Docker镜像
├── docker-compose.yml      # Docker编排
└── README.md
```

## 快速开始

### 1. 安装依赖
```bash
cd fieldmind-backend
source ../venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件
```

### 3. 启动服务
```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 4. 访问API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 音频处理
- `POST /api/v1/audio/upload` - 上传音频
- `POST /api/v1/audio/transcribe` - 语音转录
- `GET /api/v1/audio/{id}` - 获取音频信息

### 文档管理
- `POST /api/v1/documents` - 创建文档
- `GET /api/v1/documents` - 列出文档
- `GET /api/v1/documents/{id}` - 获取文档
- `PUT /api/v1/documents/{id}` - 更新文档
- `DELETE /api/v1/documents/{id}` - 删除文档

### 搜索
- `POST /api/v1/search` - 统一搜索
- `POST /api/v1/search/semantic` - 语义搜索
- `POST /api/v1/search/fulltext` - 全文搜索

### RAG
- `POST /api/v1/rag/query` - RAG问答
- `POST /api/v1/rag/index` - 索引文档

### 知识图谱
- `GET /api/v1/kg/entities` - 实体列表
- `POST /api/v1/kg/query` - 图查询
- `GET /api/v1/kg/visualize` - 可视化数据

## 数据库

### PostgreSQL Schema
```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP
);

-- 文档表
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    title TEXT,
    content TEXT,
    doc_type VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 音频表
CREATE TABLE audio_files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    file_path TEXT,
    duration INTEGER,
    transcription_id UUID,
    created_at TIMESTAMP
);
```

### Neo4j Schema
```cypher
// 人物节点
CREATE (p:Person {
    id: 'uuid',
    name: 'string',
    role: 'string'
})

// 地点节点
CREATE (l:Location {
    id: 'uuid',
    name: 'string',
    latitude: float,
    longitude: float
})

// 事件节点
CREATE (e:Event {
    id: 'uuid',
    title: 'string',
    date: datetime
})

// 关系
CREATE (p1)-[:KNOWS]->(p2)
CREATE (e)-[:HAPPENED_AT]->(l)
```

## 部署

### Docker Compose
```bash
docker-compose up -d
```

### 环境变量
```env
# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/fieldmind
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Models
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Vector DB
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
```

## 开发

### 运行测试
```bash
pytest tests/
```

### 代码格式化
```bash
black app/
ruff check app/
```

### 数据库迁移

#### Alembic 迁移系统

本项目使用 Alembic 管理数据库迁移。详细文档请查看 [ALEMBIC_GUIDE.md](ALEMBIC_GUIDE.md)。

**快速开始：**

```bash
# 使用交互式工具
./alembic_quickstart.sh

# 或直接使用命令
alembic current              # 查看当前版本
alembic upgrade head         # 应用所有迁移
alembic downgrade -1         # 回滚上一个迁移
```

**创建新迁移：**

```bash
# 自动检测模型变更
alembic revision --autogenerate -m "描述变更内容"

# 应用迁移
alembic upgrade head
```

**常用操作：**

```bash
alembic history              # 查看迁移历史
alembic upgrade 001          # 升级到特定版本
alembic downgrade base       # 回滚到初始状态
```

**⚠️ 重要提示**：
- 生产环境迁移前务必备份数据库
- 审查自动生成的迁移脚本
- 在开发环境测试后再应用到生产环境

---

**开发者**: FieldMind Team  
**最后更新**: 2026-07-29
