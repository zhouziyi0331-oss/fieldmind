# FieldMind 实施计划 - 深度集成

## 实施顺序

### 阶段1：核心数据模型扩展 ✅
创建支持深度分析的数据模型

**文件清单：**
1. `app/models/document.py` - 文档模型（元数据、向量ID、实体引用）
2. `app/models/entity.py` - 实体模型（人物、地点、事件、概念）
3. `app/models/context.py` - 脉络模型（历史、文化、经济三大脉络）
4. `app/models/chat.py` - 对话模型（多轮对话历史）
5. `app/models/analysis_report.py` - 三层分析报告模型

### 阶段2：文档处理增强 ✅
完整的文档处理流程

**文件清单：**
1. `app/services/video_processor.py` - 视频处理（提取音频→转录）
2. `app/services/document_parser.py` - 文档解析（PDF/Word/Excel/PPT）
3. `app/services/vectorization_service.py` - 向量化服务（封装）
4. `app/services/entity_extractor.py` - 实体提取服务（HanLP/SpaCy）
5. `app/tasks/document_tasks.py` - 增强：完整处理链

### 阶段3：语义匹配与RAG系统 ✅
核心的语义理解能力

**文件清单：**
1. `app/core/semantic_matcher.py` - 语义匹配引擎
2. `app/core/rag_engine.py` - 增强：深度RAG
3. `app/services/chat_service.py` - 对话服务（多轮、上下文）
4. `app/api/v1/chat.py` - 对话API端点

### 阶段4：知识脉络系统 ✅
三大脉络的梳理与可视化

**文件清单：**
1. `app/services/context_analyzer.py` - 脉络分析器
2. `app/services/timeline_generator.py` - 时间线生成器
3. `app/services/graph_builder.py` - 知识图谱构建器
4. `app/api/v1/knowledge.py` - 知识脉络API

### 阶段5：三层报告生成 ✅
核心的分析报告系统

**文件清单：**
1. `app/services/skill_loader.py` - Skill动态加载器
2. `app/services/report_generator.py` - 报告生成器
3. `app/services/tier1_analyzer.py` - 一度分析
4. `app/services/tier2_analyzer.py` - 二度分析（应用skill）
5. `app/services/tier3_analyzer.py` - 三度分析（商业分析）
6. `app/templates/report_template.html` - HTML报告模板
7. `app/tasks/report_tasks.py` - 增强：三层报告任务

### 阶段6：技能约束系统增强 ✅
确保上传的skill真正可用

**文件清单：**
1. `app/services/skill_validator.py` - 增强验证器
2. `app/services/skill_executor.py` - 安全执行器
3. `app/api/v1/skills.py` - 增强API

### 阶段7：API整合与测试 ✅
所有功能的API端点

**新增/增强端点：**
- 文档处理：支持视频、批量、向量查询
- 知识脉络：三大脉络API
- 报告生成：三层报告API
- 智能对话：RAG对话API
- 技能管理：增强验证和应用

## 数据库Schema更新

### 新表
```sql
-- 文档表
documents (
    id, filename, file_type, file_path, file_size,
    text_content, vector_id, entities (JSON),
    metadata (JSON), status, uploaded_at, processed_at
)

-- 实体表
entities (
    id, entity_type, name, properties (JSON),
    document_ids (JSON), confidence, created_at
)

-- 脉络表
contexts (
    id, context_type (历史/文化/经济), title, description,
    entities (JSON), timeline (JSON), graph_data (JSON),
    documents (JSON), created_at, updated_at
)

-- 对话表
chat_sessions (
    id, user_id, title, context (JSON), created_at
)

chat_messages (
    id, session_id, role (user/assistant), content,
    sources (JSON), created_at
)

-- 分析报告表
analysis_reports (
    id, tier (1/2/3), title, content (JSON),
    word_count, skill_ids (JSON), status,
    file_path, created_at, completed_at
)
```

## 实施步骤

### Step 1: 数据模型
```bash
# 创建模型文件
touch app/models/document.py
touch app/models/entity.py
touch app/models/context.py
touch app/models/chat.py
touch app/models/analysis_report.py
```

### Step 2: 服务层
```bash
# 创建服务文件
mkdir -p app/services
touch app/services/video_processor.py
touch app/services/document_parser.py
touch app/services/vectorization_service.py
touch app/services/entity_extractor.py
touch app/services/chat_service.py
touch app/services/context_analyzer.py
touch app/services/timeline_generator.py
touch app/services/graph_builder.py
touch app/services/skill_loader.py
touch app/services/report_generator.py
touch app/services/tier1_analyzer.py
touch app/services/tier2_analyzer.py
touch app/services/tier3_analyzer.py
```

### Step 3: 核心引擎
```bash
touch app/core/semantic_matcher.py
# 增强 app/core/rag_engine.py
```

### Step 4: API端点
```bash
touch app/api/v1/chat.py
touch app/api/v1/knowledge.py
# 增强 app/api/v1/documents.py
# 增强 app/api/v1/reports.py
# 增强 app/api/v1/skills.py
```

### Step 5: 任务队列
```bash
# 增强 app/tasks/document_tasks.py
# 增强 app/tasks/report_tasks.py
```

### Step 6: 模板
```bash
mkdir -p app/templates
touch app/templates/report_template.html
touch app/templates/tier1_template.html
touch app/templates/tier2_template.html
touch app/templates/tier3_template.html
```

### Step 7: 数据库迁移
```bash
# 初始化数据库
python3 init_db.py

# 或使用alembic迁移
alembic revision --autogenerate -m "Add deep integration models"
alembic upgrade head
```

## 依赖安装

```bash
# 已安装
pip install fastapi uvicorn sqlalchemy psycopg2-binary
pip install celery redis
pip install openai-whisper torch
pip install langchain langchain-openai langchain-anthropic
pip install chromadb sentence-transformers
pip install neo4j
pip install python-jose passlib bcrypt python-multipart

# 新增依赖
pip install pdfplumber PyPDF2         # PDF解析
pip install python-docx python-pptx   # Word/PPT解析
pip install openpyxl                   # Excel解析
pip install hanlp                      # 中文NER
pip install spacy                      # 英文NER
pip install jinja2                     # HTML模板
pip install matplotlib plotly          # 图表生成
pip install ffmpeg-python              # 视频处理
```

## 配置文件更新

`.env` 新增配置：
```env
# LLM配置
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# 模型配置
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cpu

# 文件存储
UPLOAD_DIR=./data/uploads
SKILLS_DIR=./skills
REPORTS_DIR=./reports

# 向量数据库
CHROMADB_HOST=localhost
CHROMADB_PORT=8001

# 图数据库
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_pass

# 任务队列
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# 报告配置
REPORT_MIN_WORDS=2000
REPORT_DEFAULT_FORMAT=html
```

## 测试计划

### 单元测试
- 视频处理测试
- 实体提取测试
- 向量匹配测试
- Skill加载测试
- 报告生成测试

### 集成测试
- 完整文档处理流程
- 三层报告生成流程
- RAG对话流程
- 知识图谱构建流程

### 性能测试
- 大文件处理性能
- 向量检索性能
- 并发处理能力
- 报告生成速度

## 前端对接文档

创建前端对接指南：
- API端点列表
- 请求/响应示例
- WebSocket事件
- 错误处理
- 认证流程

## 部署清单

### 服务依赖
- PostgreSQL (已有)
- Redis (已有)
- ChromaDB (需启动)
- Neo4j (需启动)
- Celery Worker (需启动)

### 启动顺序
1. PostgreSQL
2. Redis
3. ChromaDB: `chroma run --host localhost --port 8001`
4. Neo4j: `neo4j start`
5. Celery: `celery -A app.celery_app worker --loglevel=info`
6. FastAPI: `python3 -m app.main`

## 监控指标

- 文档处理成功率
- 向量检索准确率
- 报告生成完成率
- API响应时间
- 任务队列长度
- 数据库连接数
