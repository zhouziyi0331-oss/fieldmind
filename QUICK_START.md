# FieldMind 快速启动指南

## 前置要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL
- Neo4j
- Redis

## 启动步骤

### 1. 安装前端依赖

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-web
npm install
```

### 2. 启动前端开发服务器

```bash
npm run dev
```

访问: http://localhost:3000

### 3. 配置后端环境变量

```bash
cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

### 4. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 5. 启动后端API服务器

```bash
python -m uvicorn app.main:app --reload --port 8000
```

访问API文档: http://localhost:8000/docs

### 6. 启动RAGFlow服务 (可选)

```bash
docker-compose -f docker-compose.ragflow.yml up -d
```

访问RAGFlow: http://localhost:9380

## 功能验证

### 测试MarkItDown文档转换

```bash
cd fieldmind-backend
python3 -c "
from app.services.document_converter import document_converter
print('MarkItDown可用:', document_converter.is_available())
print('支持格式:', document_converter.supported_formats())
"
```

### 测试RAGFlow连接

```bash
python3 -c "
from app.services.ragflow_service import ragflow_service
print('RAGFlow可用:', ragflow_service.is_available())
"
```

## 集成工具

- ✅ MarkItDown - 文档转换 (14+格式)
- ✅ RAGFlow - RAG引擎
- ✅ simple-mind-map - 思维导图可视化

## 服务端口

- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs
- RAGFlow: http://localhost:9380
- PostgreSQL: 5432
- Neo4j: 7687
- Redis: 6379
