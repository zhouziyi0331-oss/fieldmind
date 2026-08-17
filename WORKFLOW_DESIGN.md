# FieldMind 工具互联设计与工作流自动化

## 一、核心设计理念

**"点一下，下一个自动配套"** - 每个操作自动触发相关的后续处理流程，无需人工干预。

## 二、自动触发链路图

```
用户操作 → API接收 → Celery任务调度 → 并行/串行执行 → 结果存储 → 通知用户
```

## 三、完整工作流设计

### 3.1 文档处理流（Document Pipeline）

```
上传文档
    ↓
[API] /api/v1/documents/upload
    ↓
[Task] process_document_chain
    ├─→ [Task] convert_to_markdown (markitdown)
    │       ↓
    ├─→ [Parallel Group]
    │   ├─→ [Task] vectorize_and_store (sentence-transformers + ChromaDB)
    │   ├─→ [Task] extract_entities (HanLP + Neo4j)
    │   ├─→ [Task] fulltext_index (Whoosh)
    │   └─→ [Task] save_to_db (PostgreSQL)
    │       ↓
    └─→ [Result] 返回task_id，用户可查询状态
```

**触发方式**：
```python
# 用户上传后自动执行
task = process_document_chain.delay(file_path)
return {"task_id": task.id}
```

**涉及的工具**：
- markitdown（文档转换）
- sentence-transformers（向量化）
- ChromaDB（向量存储）
- HanLP（实体识别）
- Neo4j（知识图谱）
- Whoosh（全文索引）
- PostgreSQL（结构化存储）

### 3.2 音频处理流（Audio Pipeline）

```
上传音频
    ↓
[API] /api/v1/audio/upload
    ↓
[Task] process_audio_chain
    ├─→ [Task] extract_audio_metadata (ffmpeg)
    ├─→ [Task] transcribe_audio (Whisper本地版 或 OpenAI API)
    │       ↓
    │   (生成markdown格式文本)
    │       ↓
    └─→ [Task] process_document_chain (复用文档流)
            ├─→ vectorize_and_store
            ├─→ extract_entities
            ├─→ fulltext_index
            └─→ save_to_db
```

**触发方式**：
```python
# 转录完成后自动进入文档处理流
transcription_result = transcribe_audio(file_path)
doc_data = {"markdown": transcription_result["transcription"], ...}
process_document_chain.delay(doc_data)
```

**涉及的工具**：
- ffmpeg（音频元数据提取）
- Whisper（语音识别）
- 全部文档流工具

### 3.3 爬虫处理流（Crawler Pipeline）

```
提交URL
    ↓
[API] /api/v1/crawler/crawl 或 /news 或 /government
    ↓
[Task] crawl_and_process
    ├─→ [Task] intelligent_crawl
    │   ├─→ 智能路由选择：
    │   │   ├─ 政府网站 → gecco
    │   │   ├─ 新闻网站 → crawl4ai + newspaper3k/gne
    │   │   ├─ 需要登录 → browser-use
    │   │   ├─ 复杂交互 → drissionpage
    │   │   └─ 一般网页 → firecrawl
    │   │       ↓
    │   └─→ 返回markdown内容
    │       ↓
    └─→ [Task] process_document_chain (自动进入文档流)
            ├─→ vectorize_and_store
            ├─→ extract_entities
            ├─→ fulltext_index
            └─→ save_to_db
```

**触发方式**：
```python
# 爬取完成后自动进入文档处理流
crawl_result = intelligent_crawl(url)
if crawl_result["success"]:
    process_document_chain.delay(crawl_result)
```

**涉及的工具**：
- crawl4ai（通用爬取）
- gecco（政府网站）
- browser-use（复杂交互）
- firecrawl（API爬取）
- newspaper3k + gne（新闻提取）
- drissionpage（动态网页）

### 3.4 RAG查询流（RAG Query Pipeline）

```
用户提问
    ↓
[API] /api/v1/rag/query
    ↓
[Task] triple_retrieval_query
    ├─→ [Task] extract_query_entities (HanLP)
    │       ↓
    ├─→ [Parallel Group] 四路并行检索
    │   ├─→ [Task] vector_search (ChromaDB)
    │   ├─→ [Task] fulltext_search (Whoosh)
    │   ├─→ [Task] graph_search (Neo4j)
    │   └─→ [Task] keyword_search (PostgreSQL)
    │       ↓
    ├─→ [Task] reciprocal_rank_fusion (RRF融合算法)
    │       ↓
    ├─→ [Task] generate_answer (Ollama qwen2.5 或 OpenAI)
    │       ↓
    └─→ [Result] 返回答案 + 来源引用
```

**触发方式**：
```python
# 用户提问后自动执行多路检索
task = triple_retrieval_query.delay(query)
return {"task_id": task.id}
```

**涉及的工具**：
- HanLP（查询实体识别）
- ChromaDB（向量检索）
- Whoosh（全文检索）
- Neo4j（图谱检索）
- PostgreSQL（关键词检索）
- Ollama（本地LLM生成）

### 3.5 知识图谱构建流（Knowledge Graph Pipeline）

```
文档/音频/爬虫内容
    ↓
[Task] extract_entities_and_relations
    ├─→ [Task] hanlp_ner (命名实体识别)
    ├─→ [Task] hanlp_srl (语义角色标注)
    ├─→ [Task] dependency_parsing (依存句法分析)
    │       ↓
    ├─→ [Task] extract_triples (三元组提取)
    │   格式：(实体1, 关系, 实体2)
    │       ↓
    └─→ [Task] build_knowledge_graph
        ├─→ 创建节点 (Neo4j CREATE)
        ├─→ 创建关系 (Neo4j MERGE)
        └─→ 更新属性 (添加来源、时间戳)
```

**触发方式**：
```python
# 文档处理流中自动调用
parallel_tasks = group([
    vectorize_and_store.s(markdown_result),
    extract_entities.s(markdown_result),  # ← 这里自动构建图谱
    fulltext_index.s(markdown_result),
    save_to_db.s(markdown_result),
])
```

**涉及的工具**：
- HanLP（全套NLP功能）
- Neo4j（图数据库）

### 3.6 报告生成流（Report Generation Pipeline）

```
用户请求报告
    ↓
[API] /api/v1/reports/generate
    ↓
[Task] generate_report_chain
    ├─→ [Task] query_data_sources
    │   ├─→ PostgreSQL (结构化数据)
    │   ├─→ Neo4j (关系数据)
    │   └─→ RAG查询 (语义数据)
    │       ↓
    ├─→ [Parallel Group] 生成可视化
    │   ├─→ [Task] generate_charts (pyecharts)
    │   ├─→ [Task] generate_maps (folium)
    │   ├─→ [Task] generate_wordcloud (wordcloud)
    │   └─→ [Task] generate_network_graph (pyvis)
    │       ↓
    ├─→ [Task] render_report_template (Jinja2)
    │       ↓
    └─→ [Parallel Group] 导出多格式
        ├─→ [Task] export_to_word (python-docx)
        ├─→ [Task] export_to_pdf (weasyprint)
        └─→ [Task] export_to_html (jinja2)
```

**触发方式**：
```python
# 用户请求报告后自动生成
task = generate_report_chain.delay(report_config)
return {"task_id": task.id}
```

**涉及的工具**：
- pyecharts（图表生成）
- folium（地图可视化）
- wordcloud（词云）
- pyvis（网络图）
- python-docx（Word导出）
- weasyprint（PDF导出）
- Jinja2（模板渲染）

### 3.7 CrewAI多智能体协作流（Multi-Agent Pipeline）

```
复杂任务请求
    ↓
[API] /api/v1/agents/coordinate
    ↓
[Task] crew_coordinate_task
    ├─→ [Agent] CoordinatorAgent (任务分解)
    │       ↓
    ├─→ [Sequential Workflow]
    │   ├─→ [Agent] TranscriptAgent (文本处理)
    │   ├─→ [Agent] EntityAgent (实体识别)
    │   ├─→ [Agent] RelationAgent (关系抽取)
    │   ├─→ [Agent] SearchAgent (信息检索)
    │   └─→ [Agent] SummaryAgent (结果汇总)
    │       ↓
    └─→ [Result] 返回协作结果
```

**触发方式**：
```python
# 用户提交复杂任务后自动协调
crew_result = crew.kickoff(inputs={"task": user_task})
return crew_result
```

**涉及的工具**：
- CrewAI（多智能体框架）
- Ollama（本地LLM）

## 四、工具互联矩阵

| 工具 | 触发源 | 触发目标 | 触发条件 |
|------|--------|----------|----------|
| markitdown | 文档上传API | vectorize_and_store, extract_entities | 文档转换成功 |
| Whisper | 音频上传API | process_document_chain | 转录完成 |
| crawl4ai/gecco/等 | 爬虫API | process_document_chain | 爬取成功 |
| HanLP | 文档处理/RAG查询 | Neo4j, PostgreSQL | 实体提取完成 |
| ChromaDB | vectorize任务 | - | 存储完成 |
| Neo4j | extract_entities任务 | - | 图谱构建完成 |
| Whoosh | fulltext_index任务 | - | 索引建立完成 |
| PostgreSQL | save_to_db任务 | - | 数据保存完成 |
| RAG查询 | 用户查询API | Ollama/OpenAI | 检索完成 |
| pyecharts/folium | 报告生成 | python-docx, weasyprint | 图表生成完成 |

## 五、自动触发机制实现

### 5.1 Celery Chain（串行链）

```python
from celery import chain

# 示例：爬取 → 处理 → 索引
workflow = chain(
    crawl_url.s(url),
    process_document_chain.s(),
    notify_user.s()
)
workflow.apply_async()
```

### 5.2 Celery Group（并行组）

```python
from celery import group

# 示例：文档处理的4个并行任务
parallel_tasks = group([
    vectorize_and_store.s(data),
    extract_entities.s(data),
    fulltext_index.s(data),
    save_to_db.s(data),
])
result = parallel_tasks.apply_async()
```

### 5.3 Celery Chord（并行后汇总）

```python
from celery import chord

# 示例：多路检索 → RRF融合
workflow = chord([
    vector_search.s(query),
    fulltext_search.s(query),
    graph_search.s(query),
    keyword_search.s(query),
])(reciprocal_rank_fusion.s())
workflow.apply_async()
```

### 5.4 任务间信号传递

```python
# 文档处理完成后自动触发后续任务
@celery_app.task
def process_document_chain(file_path: str):
    # 步骤1：转换
    markdown_result = convert_to_markdown(file_path)
    
    # 步骤2：并行处理
    parallel_tasks = group([
        vectorize_and_store.s(markdown_result),
        extract_entities.s(markdown_result),
        fulltext_index.s(markdown_result),
        save_to_db.s(markdown_result),
    ])
    
    # 自动执行并等待结果
    results = parallel_tasks.apply_async()
    all_results = results.get(timeout=300)
    
    # 步骤3：通知用户（可选）
    if all(r.get("success") for r in all_results):
        notify_user.delay(file_path, "处理完成")
    
    return {"success": True, "results": all_results}
```

## 六、任务队列路由策略

```python
# Celery路由配置
CELERY_ROUTES = {
    # 文档处理队列（CPU密集）
    "app.tasks.document_tasks.*": {"queue": "documents"},
    
    # 音频处理队列（GPU密集）
    "app.tasks.audio_tasks.*": {"queue": "audio"},
    
    # 爬虫队列（IO密集 + 限速）
    "app.tasks.crawler_tasks.*": {"queue": "crawler"},
    
    # RAG查询队列（高优先级）
    "app.tasks.rag_tasks.*": {"queue": "rag"},
    
    # 知识图谱队列（内存密集）
    "app.tasks.graph_tasks.*": {"queue": "graph"},
    
    # 报告生成队列（低优先级）
    "app.tasks.report_tasks.*": {"queue": "reports"},
}
```

## 七、失败重试与容错

```python
# 自动重试配置
@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def robust_task(self, data):
    try:
        # 执行任务
        result = process_data(data)
        return result
    except Exception as exc:
        # 记录错误
        logger.error(f"Task {self.request.id} failed: {exc}")
        raise
```

## 八、实时进度通知

```python
# WebSocket推送任务进度
from celery.signals import task_prerun, task_postrun, task_failure

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    # 推送"任务开始"消息
    websocket_manager.broadcast({
        "task_id": task_id,
        "status": "started",
        "task_name": task.name
    })

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **kwargs):
    # 推送"任务完成"消息
    websocket_manager.broadcast({
        "task_id": task_id,
        "status": "completed",
        "result": retval
    })

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    # 推送"任务失败"消息
    websocket_manager.broadcast({
        "task_id": task_id,
        "status": "failed",
        "error": str(exception)
    })
```

## 九、零成本运行配置

所有工具均可使用开源/本地方案：

| 功能 | 付费API | 零成本替代 |
|------|---------|-----------|
| 文档转换 | - | markitdown（开源） |
| 语音识别 | OpenAI Whisper API | Whisper本地版 |
| 向量化 | OpenAI Embeddings | sentence-transformers |
| 向量存储 | Pinecone | ChromaDB（本地） |
| 全文检索 | Elasticsearch | Whoosh（纯Python） |
| 知识图谱 | Neo4j Aura | Neo4j社区版（本地） |
| NLP处理 | Google NLP API | HanLP（开源） |
| LLM生成 | OpenAI/Anthropic | Ollama + qwen2.5 |
| 爬虫服务 | Bright Data | crawl4ai, gecco（开源） |
| 数据库 | AWS RDS | PostgreSQL（本地） |
| 任务队列 | AWS SQS | Celery + Redis（本地） |
| 图表生成 | - | pyecharts（开源） |
| PDF导出 | - | weasyprint（开源） |

## 十、快速启动命令

```bash
# 1. 启动所有服务
./start_services.sh

# 2. 启动Celery Worker（6个队列）
celery -A app.celery_app worker \
    -Q documents,audio,crawler,rag,graph,reports,default \
    --loglevel=info \
    --concurrency=4

# 3. 启动Celery Beat（定时任务，可选）
celery -A app.celery_app beat --loglevel=info

# 4. 启动Flower（监控界面，可选）
celery -A app.celery_app flower --port=5555

# 5. 启动FastAPI服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：
- API文档：http://localhost:8000/docs
- Flower监控：http://localhost:5555
- Neo4j浏览器：http://localhost:7474

## 十一、API使用示例

### 11.1 上传文档并自动处理

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
    -F "file=@report.pdf"

# 响应
{
    "success": true,
    "message": "文档上传成功，正在自动处理",
    "task_id": "abc123",
    "status_url": "/api/v1/documents/status/abc123"
}

# 查询处理状态
curl "http://localhost:8000/api/v1/documents/status/abc123"
```

### 11.2 上传音频并自动转录+处理

```bash
curl -X POST "http://localhost:8000/api/v1/audio/upload" \
    -F "file=@interview.mp3" \
    -F "auto_process=true"

# 自动执行：转录 → 文档处理 → 向量化 → 实体识别 → 索引 → 存储
```

### 11.3 爬取新闻并自动处理

```bash
curl -X POST "http://localhost:8000/api/v1/crawler/news" \
    -H "Content-Type: application/json" \
    -d '{
        "url": "https://news.example.com/article/123",
        "auto_process": true
    }'

# 自动执行：智能爬取 → 新闻提取 → 文档处理流
```

### 11.4 RAG查询（四路检索+融合）

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
    -H "Content-Type: application/json" \
    -d '{
        "query": "方言保护的现状和挑战",
        "top_k": 5
    }'

# 自动执行：实体识别 → 向量检索 + 全文检索 + 图谱检索 + 关键词检索 → RRF融合 → LLM生成
```

### 11.5 生成分析报告

```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "title": "方言调研分析报告",
        "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "include_charts": true,
        "include_maps": true,
        "format": ["word", "pdf"]
    }'

# 自动执行：数据查询 → 图表生成 → 模板渲染 → 多格式导出
```

## 十二、监控与调试

### 12.1 查看任务状态

```python
from app.celery_app import celery_app

# 查询任务状态
task_result = celery_app.AsyncResult(task_id)
print(task_result.state)  # PENDING, STARTED, SUCCESS, FAILURE
print(task_result.result)  # 任务返回值
```

### 12.2 Flower监控界面

访问 http://localhost:5555 可以查看：
- 实时任务执行情况
- Worker状态和性能
- 任务成功/失败统计
- 任务执行时间分布

### 12.3 日志追踪

```python
import logging
logger = logging.getLogger(__name__)

@celery_app.task
def my_task(data):
    logger.info(f"Task started with data: {data}")
    # ...
    logger.info(f"Task completed")
```

## 十三、性能优化建议

1. **并行化**：充分利用group()并行执行独立任务
2. **预取优化**：设置worker_prefetch_multiplier=1避免任务堆积
3. **结果后端**：使用Redis而非数据库作为result_backend
4. **任务超时**：设置合理的task_time_limit和task_soft_time_limit
5. **连接池**：配置数据库和Redis连接池大小
6. **批处理**：对大量小任务使用chunks()批量处理
7. **缓存**：使用Redis缓存频繁查询的结果

## 十四、下一步计划

- [ ] 实现WebSocket实时进度推送
- [ ] 添加定时任务（每日爬取新闻、定期生成报告）
- [ ] 实现任务优先级队列
- [ ] 添加分布式追踪（OpenTelemetry）
- [ ] 实现任务去重机制
- [ ] 添加更多可视化类型
- [ ] 支持批量文档上传和处理
- [ ] 实现增量知识图谱更新
