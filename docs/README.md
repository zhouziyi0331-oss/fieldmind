# FieldMind - 知识脉络分析系统

基于AI的民族文化智能分析平台

## 系统概述

本系统是一个面向民族文化研究的智能知识分析平台，通过语义向量匹配技术实现对多媒体文档的深度理解和分析。系统支持视频、音频、文本等多种格式的文档处理，能够自动提取知识点、构建知识图谱、生成多层次分析报告，并提供智能对话交互功能。

### 核心特性

1. **用户认证与权限管理** 🔐
   - JWT token身份验证
   - 基于角色的访问控制（RBAC）：admin、researcher、viewer
   - 项目级权限隔离
   - Argon2密码哈希

2. **语义向量匹配**
   - 使用 sentence-transformers 多语言模型进行文本向量化
   - 通过余弦相似度实现语义理解（如"山歌"="民歌"="18洞歌"）
   - ChromaDB 向量数据库支持高效语义检索

2. **多媒体文档处理**
   - 视频文档：自动提取音频 → 语音识别 → 文本向量化
   - 音频文档：Whisper 大模型语音识别 → 文本向量化
   - 文本文档：直接进行语义分析和向量化
   - 所有文档统一索引，支持跨模态语义检索

3. **知识脉络构建**
   - 三条主线并行分析：历史脉络、文化脉络、经济农业脉络
   - HanLP 中文 NLP 工具进行实体识别（人物、地点、组织、事件）
   - Neo4j 图数据库构建知识图谱和实体关系网络

4. **三层次分析报告**
   - **第一层：信息整理报告**（5000-10000字）
     * 基础统计数据、时间线梳理、实体列表
     * 快速了解文档概况和关键信息点
   
   - **第二层：学术深度分析**（8000-15000字）
     * 费孝通理论视角：差序格局、礼治秩序、熟人社会
     * 民族志方法论、田野调查技巧
     * 深入的文化人类学和社会学分析
   
   - **第三层：商业价值分析**（10000-20000字）
     * 市场规模估算、商业模式设计、ROI 分析
     * 实施路线图、合作伙伴策略、财务预测
     * 5年详细财务投影（营收、利润、估值）

5. **智能对话系统**
   - RAG（检索增强生成）架构
   - 多轮对话上下文管理
   - 基于语义检索的精准答案生成
   - 会话历史持久化

6. **技能管理增强**
   - 支持用户上传自定义 Python 分析脚本
   - 三层验证机制：语法检查 → 安全扫描 → 沙盒测试
   - 技能激活/停用管理
   - 动态集成到分析流程

## 技术架构

### 后端技术栈

- **Web 框架**: FastAPI（高性能异步 API）
- **数据库**: 
  - PostgreSQL/SQLite（关系型数据，SQLAlchemy ORM）
  - ChromaDB（向量数据库，语义检索）
  - Neo4j（图数据库，知识图谱）
  - Redis（缓存和任务队列）
- **NLP & ML**:
  - sentence-transformers（多语言语义向量模型）
  - HanLP（中文 NLP 工具包）
  - OpenAI Whisper（语音识别大模型）
  - Transformers（深度学习模型库）
- **任务队列**: Celery（异步任务处理）
- **模板引擎**: Jinja2（HTML 报告生成）

### 前端技术栈

- HTML5 + CSS3 + JavaScript
- Bootstrap（响应式 UI）
- Axios（HTTP 客户端）
- Markdown 渲染支持

## 项目结构

```
knowledge_system/
├── app/
│   ├── main.py                 # FastAPI 应用入口
│   ├── database.py             # 数据库配置
│   ├── models/                 # SQLAlchemy 数据模型
│   │   ├── __init__.py
│   │   ├── document.py         # 文档模型
│   │   ├── entity.py           # 实体模型
│   │   ├── context.py          # 知识脉络模型
│   │   ├── dialogue.py         # 对话模型
│   │   └── skill.py            # 技能模型
│   ├── services/               # 业务逻辑层
│   │   ├── tier1_analyzer.py   # 第一层分析服务
│   │   ├── tier2_analyzer.py   # 第二层分析服务
│   │   ├── tier3_analyzer.py   # 第三层分析服务
│   │   ├── report_generator.py # 报告生成服务
│   │   ├── context_analyzer.py # 知识脉络分析
│   │   └── dialogue_system.py  # 对话系统（待实现）
│   └── api/                    # API 路由
│       └── v1/
│           ├── __init__.py
│           ├── reports.py      # 报告生成 API
│           ├── chat.py         # 对话系统 API
│           └── contexts.py     # 知识脉络 API
├── requirements.txt            # Python 依赖
├── .env.example               # 环境变量模板
└── README.md                  # 项目文档
```

## 快速开始

### 方式1：Docker部署（推荐）⭐

最简单的启动方式，一键部署所有服务：

```bash
# 1. 配置环境变量
cp .env.example .env
nano .env  # 填入 ANTHROPIC_API_KEY 等配置

# 2. 启动服务
chmod +x start.sh
./start.sh
```

访问系统：
- **前端**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Neo4j浏览器**: http://localhost:7474

详细Docker部署文档：[DOCKER.md](DOCKER.md)

---

### 方式2：本地开发环境

### 1. 环境准备

**系统要求**:
- Python 3.9+
- PostgreSQL 13+ 或 SQLite
- Neo4j 4.4+
- Redis 6.0+
- 8GB+ RAM（推荐 16GB）
- GPU（可选，用于加速模型推理）

### 2. 安装依赖

```bash
# 克隆项目
cd /Users/alwan

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 下载 NLP 模型（首次运行）
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
python -c "import hanlp; hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)"
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置数据库连接等信息
nano .env
```

关键配置项：
```env
# 数据库
DATABASE_URL=sqlite:///./knowledge_system.db  # 或 PostgreSQL URL

# Neo4j 图数据库
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# ChromaDB 向量数据库
CHROMADB_PATH=./data/chromadb

# Redis
REDIS_URL=redis://localhost:6379/0

# 文件存储
UPLOAD_DIR=./data/uploads
PROCESSED_DIR=./data/processed
AUDIO_EXTRACT_DIR=./data/audio_extracts
```

### 4. 初始化数据库

```bash
# 创建数据目录
mkdir -p data/uploads data/processed data/audio_extracts data/chromadb

# 初始化关系型数据库
python -c "from app.database import init_db; init_db()"

# 启动 Neo4j（需单独安装）
# 访问 http://localhost:7474 配置初始密码

# 启动 Redis
redis-server
```

### 5. 启动服务

```bash
# 启动 Celery 任务队列（新终端）
celery -A app.tasks worker --loglevel=info

# 启动 FastAPI 应用
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问系统：
- API 文档: http://localhost:8000/docs
- 系统首页: http://localhost:8000/

## API 使用示例

### 0. 用户认证

**注册新用户**:
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "researcher",
    "password": "secure_password"
  }'
```

**用户登录**:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "researcher",
    "password": "secure_password"
  }'
```

响应示例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**获取当前用户信息**:
```bash
curl -X GET "http://localhost:8000/api/auth/me" \
  -H "Authorization: Bearer <access_token>"
```

**后续API请求都需要带上token**:
```bash
# 在请求头中添加
-H "Authorization: Bearer <your_access_token>"
```

### 1. 生成三层次分析报告

```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2, 3],
    "context_ids": [1],
    "entity_ids": [10, 20, 30],
    "skill_ids": [5],
    "tiers": [1, 2, 3],
    "export_format": "html"
  }'
```

响应示例：
```json
{
  "report": {
    "metadata": {
      "report_id": "rpt_abc123",
      "generated_at": "2026-07-30T10:30:00Z",
      "word_counts": {"tier1": 7500, "tier2": 12000, "tier3": 15000}
    },
    "tier1": {...},
    "tier2": {...},
    "tier3": {...}
  },
  "export_path": "/data/reports/rpt_abc123.html"
}
```

### 2. 智能对话查询

```bash
curl -X POST "http://localhost:8000/api/v1/chat/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "十八洞村的苗族山歌有什么特点？",
    "session_id": "sess_xyz789",
    "document_ids": [1, 2, 3],
    "top_k": 5
  }'
```

响应示例：
```json
{
  "session_id": "sess_xyz789",
  "answer": "根据文档分析，十八洞村的苗族山歌具有以下特点：\n1. 传承古老：保留了苗族传统的五声音阶...\n2. 内容丰富：涵盖劳动、爱情、历史传说...\n3. 即兴创作：歌手能够根据场景即兴编词...",
  "sources": [
    {"document_id": 1, "title": "十八洞村田野调查", "similarity": 0.89},
    {"document_id": 3, "title": "苗族音乐研究", "similarity": 0.85}
  ],
  "context_used": ["苗族山歌是一种口头传承的民间艺术形式...", "..."]
}
```

### 3. 生成知识脉络

```bash
curl -X POST "http://localhost:8000/api/v1/contexts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "context_type": "cultural",
    "document_ids": [1, 2, 3, 4, 5],
    "entity_ids": [10, 20, 30]
  }'
```

## 核心功能详解

### 语义向量匹配原理

系统使用 384 维多语言语义向量模型，通过余弦相似度计算实现语义匹配：

1. **文本向量化**: 输入文本 → 编码器 → 384维向量
2. **语义检索**: 查询向量 × 文档向量库 → 相似度排序 → Top-K 结果
3. **跨语义匹配**: "山歌" ≈ "民歌" ≈ "18洞歌" （相似度 > 0.8）

**示例**:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 向量化
v1 = model.encode("十八洞村的苗族山歌")
v2 = model.encode("湘西民歌艺术")

# 计算相似度
from numpy import dot
from numpy.linalg import norm
similarity = dot(v1, v2) / (norm(v1) * norm(v2))
print(f"相似度: {similarity:.3f}")  # 输出: 0.847
```

### 三层次报告生成逻辑

**第一层：信息整理**
- 输入：原始文档集合
- 处理：统计分析、时间线提取、实体识别
- 输出：5000-10000字结构化信息报告

**第二层：学术分析**
- 输入：第一层报告 + 知识脉络 + 实体关系图
- 处理：费孝通理论应用、社会学分析、文化人类学视角
- 输出：8000-15000字学术深度报告

**第三层：商业分析**
- 输入：第一层 + 第二层 + 市场数据
- 处理：商业模式设计、财务建模、风险评估
- 输出：10000-20000字商业价值报告

### 知识图谱构建流程

1. **实体识别**: HanLP NER → 人物、地点、组织、事件
2. **关系抽取**: 依存句法分析 → 实体间关系
3. **图谱存储**: Neo4j 节点和边 → 知识网络
4. **图谱查询**: Cypher 查询语言 → 关系推理

**示例查询**:
```cypher
// 查找与"十八洞村"相关的所有人物和事件
MATCH (place:Location {name: "十八洞村"})-[r]-(entity)
WHERE entity:Person OR entity:Event
RETURN place, r, entity
LIMIT 50
```

## 开发指南

### 添加自定义分析技能

1. 创建 Python 脚本 `my_skill.py`:
```python
def analyze(documents, entities, contexts):
    """
    自定义分析函数
    
    参数:
        documents: List[Document] - 文档列表
        entities: List[Entity] - 实体列表
        contexts: List[Context] - 知识脉络列表
    
    返回:
        Dict[str, Any] - 分析结果
    """
    result = {
        "skill_name": "我的自定义分析",
        "findings": [],
        "recommendations": []
    }
    
    # 实现您的分析逻辑
    for doc in documents:
        # 分析文档...
        result["findings"].append({
            "document_id": doc.id,
            "insight": "发现的洞察..."
        })
    
    return result
```

2. 通过 API 上传技能:
```bash
curl -X POST "http://localhost:8000/api/v1/skills/upload" \
  -F "file=@my_skill.py" \
  -F "name=我的自定义分析" \
  -F "description=专门针对...的分析技能"
```

3. 激活技能后，系统会在报告生成时自动调用

### 扩展 API 端点

在 `app/api/v1/` 下创建新的路由文件：

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(db: Session = Depends(get_db)):
    # 实现您的端点逻辑
    return {"message": "Hello from my endpoint"}
```

在 `app/api/v1/__init__.py` 中注册路由：
```python
from app.api.v1 import my_module
api_router.include_router(my_module.router, prefix="/my-module", tags=["my-module"])
```

## 性能优化建议

1. **向量检索优化**
   - 使用 HNSW 索引加速相似度搜索
   - 批量向量化（batch_size=32）
   - GPU 加速推理（CUDA 支持）

2. **数据库查询优化**
   - 添加适当的索引
   - 使用连接池（pool_size=20）
   - 分页查询大数据集

3. **异步任务处理**
   - 文档处理使用 Celery 异步队列
   - 设置合理的任务超时时间
   - 实现任务结果缓存

4. **缓存策略**
   - Redis 缓存频繁查询结果
   - 向量缓存（TTL=1小时）
   - 报告缓存（TTL=24小时）

## 部署指南

### Docker 部署（推荐）

```dockerfile
# Dockerfile（待创建）
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml（待创建）
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - neo4j
      - redis
  
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: knowledge_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
  
  neo4j:
    image: neo4j:4.4
    ports:
      - "7474:7474"
      - "7687:7687"
  
  redis:
    image: redis:6
    ports:
      - "6379:6379"
```

启动：
```bash
docker-compose up -d
```

### 生产环境部署

1. **使用 Gunicorn + Uvicorn Workers**:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. **Nginx 反向代理**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **系统服务配置** (`/etc/systemd/system/knowledge-system.service`):
```ini
[Unit]
Description=Knowledge System API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/knowledge_system
Environment="PATH=/opt/knowledge_system/venv/bin"
ExecStart=/opt/knowledge_system/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

## 故障排查

### 常见问题

**Q: 模型下载失败**
```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com
pip install -r requirements.txt
```

**Q: ChromaDB 初始化错误**
```bash
# 确保目录存在且有写权限
mkdir -p data/chromadb
chmod 755 data/chromadb
```

**Q: Neo4j 连接失败**
```bash
# 检查 Neo4j 服务状态
neo4j status
# 重置密码
neo4j-admin set-initial-password your_password
```

**Q: Celery 任务不执行**
```bash
# 检查 Redis 连接
redis-cli ping
# 清空任务队列
celery -A app.tasks purge
```

## 测试

```bash
# 运行单元测试（待实现）
pytest tests/

# 运行集成测试
pytest tests/integration/

# 生成测试覆盖率报告
pytest --cov=app tests/
```

## 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

## 许可证

[待定]

## 联系方式

- 项目维护者：[待补充]
- Email：[待补充]
- 问题反馈：[待补充]

---

**最后更新**: 2026-07-30
**版本**: 1.0.0
