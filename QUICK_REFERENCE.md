# FieldMind 工作舱 - 快速参考指南

## 🚀 快速启动

### 1. 启动服务器
```bash
cd /Users/alwan/FieldMind/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问 API 文档
```
http://localhost:8000/docs
```

### 3. 测试工作舱服务
```bash
curl http://localhost:8000/api/v1/workbench/health
```

---

## 📦 已完成的服务

### ✅ 1. 统一服务层
**入口**: `app/core/workbench_services.py`

```python
from app.core.workbench_services import get_workbench_services

services = get_workbench_services(db)

# 健康检查
health = services.health_check()
```

### ✅ 2. 中文 NLP (HanLP)
```python
# 分词
tokens = services.nlp.tokenize("自然语言处理")

# 关键词提取
keywords = services.nlp.extract_keywords(text, top_k=10)

# 实体识别
entities = services.nlp.extract_entities(text)
```

### ✅ 3. 长期记忆 (Mem0)
```python
# 存储记忆
memory_id = services.memory.store_memory(user_id, content, context)

# 搜索记忆
results = services.memory.search_memory(user_id, query, limit=10)
```

### ✅ 4. 爬虫系统
```python
# 爬取单页
result = services.crawler.crawl_url("https://example.com")

# 爬取网站
pages = services.crawler.crawl_website(url, max_depth=2, max_pages=50)
```

### ✅ 5. 知识图谱
```python
# 自动构建
result = services.knowledge_graph.build_graph_from_documents(
    document_ids=[1, 2, 3],
    project_id=1
)

# 查询图谱
results = services.knowledge_graph.query_graph(query, project_id)
```

---

## 🧪 测试脚本

```bash
# 测试工作舱服务
python test_workbench_services.py

# 测试 HanLP
python test_hanlp_service.py

# 测试 Mem0
python test_mem0_service.py

# 测试爬虫
python test_crawler_service.py
```

---

## 📊 当前状态

- **整体完成度**: 78%
- **可用服务**: 6/7 (85.7%)
- **代码行数**: 5,900+
- **文档页数**: 79+

---

## 🎯 API 端点

### 工作舱核心
- `GET /api/v1/workbench/health` - 健康检查
- `GET /api/v1/workbench/services` - 服务列表
- `GET /api/v1/workbench/overview` - 概览

### NLP 服务
- `POST /api/v1/workbench/nlp/tokenize` - 分词
- `POST /api/v1/workbench/nlp/keywords` - 关键词提取
- `POST /api/v1/workbench/nlp/entities` - 实体识别

### 记忆服务
- `POST /api/v1/workbench/memory/store` - 存储记忆
- `GET /api/v1/workbench/memory/search` - 搜索记忆

### 爬虫服务
- `POST /api/v1/workbench/crawler/crawl` - 爬取网站

### 知识图谱
- `POST /api/v1/workbench/kg/build` - 构建图谱
- `POST /api/v1/workbench/kg/query` - 查询图谱

---

## 📚 文档位置

- 总体评估: `WORKBENCH_STATUS_ASSESSMENT.md`
- 进度跟踪: `WORKBENCH_IMPLEMENTATION_PROGRESS.md`
- Day 1 总结: `WORKBENCH_DAY1_FINAL_REPORT.md`
- HanLP 集成: `HANLP_INTEGRATION_COMPLETE.md`
- 爬虫集成: `CRAWLER_INTEGRATION_COMPLETE.md`

---

**状态**: ✅ Day 1 完成  
**下一步**: 第二阶段 - 工作流能力
