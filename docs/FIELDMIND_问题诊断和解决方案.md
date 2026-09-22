# FieldMind 系统问题诊断和解决方案

生成时间: 2026-08-19 13:25

---

## 🔍 当前问题诊断

### 问题1：chunks没有保存到数据库
**现象：**
- 后端日志显示"成功向量化X个chunks"
- 但是数据库中`document_chunks`表为空
- 前端显示chunk_count = 0

**根本原因：**
1. `DocumentProcessingPipeline`只将chunks保存到ChromaDB（向量数据库）
2. **没有保存到SQLite的document_chunks表**
3. Pipeline.process_document()返回的result中**不包含chunks数据**

**日志证据：**
```
✅ Pipeline处理成功: 6个块已向量化
⚠️ Pipeline返回的chunks为空，尝试重新生成...
❌ 保存chunks失败: Table 'pipeline_executions' is already defined
```

### 问题2：自动分析流程不完整
**现象：**
- 文档上传后只完成了基础处理（提取、分块、向量化）
- 没有自动执行：
  - 关键词提取
  - 知识图谱构建
  - 可视化看板生成
  - 时间线构建
  - 三层分析报告生成

**根本原因：**
- `background_tasks.py`中的`process_document_async`只调用了基础的pipeline
- 没有调用后续的分析流程
- 我创建的`document_auto_analysis.py`没有被集成

### 问题3：音频转录全部失败
**现象：**
- 所有`.wav`音频文件status = "failed"

**根本原因：**
- Whisper模型需要手动加载
- 可能缺少OpenAI API Key配置

---

## ✅ 已经完成的工作

1. **API修复**
   - document/list/status API返回正确的chunk_count
   - 从document_chunks表实时查询

2. **word_count修复**
   - 修复了现有已处理文档的word_count
   - 从chunks的text_length计算

3. **自动化触发**
   - 修改了上传API，自动调用`process_document_async`

4. **代码修改**
   - 在`background_tasks.py`中添加了chunks保存逻辑
   - 在`document_processing_pipeline_complete.py`中添加了chunks保存逻辑

---

## ❌ 没有解决的核心问题

### 为什么chunks没有保存到数据库？

**技术细节：**
1. `DocumentProcessingPipeline.process_document()` 返回：
   ```python
   {
       "success": True,
       "chunks_count": 6,
       "processing_time": 35.2,
       # ⚠️ 没有返回chunks数据！
   }
   ```

2. 我添加的保存代码尝试从`result.get('chunks', [])`获取chunks
   - **但是result中没有chunks字段**
   - 导致`chunks_data = []`
   - 无法保存

3. Pipeline内部有chunks数据，但是：
   - Chunks被保存到ChromaDB
   - **没有被返回给调用者**
   - **没有被保存到SQLite**

---

## 🔧 完整解决方案

### 方案A：修改Pipeline返回chunks数据（推荐）

修改`document_processing_pipeline_complete.py`的返回值：

```python
# 在process_document方法的最后，修改return语句
return {
    "success": True,
    "document_id": document_id,
    "chunks_count": len(vectorized_chunks),
    "processing_time": processing_time,
    "chunks": vectorized_chunks,  # ✅ 添加这一行
    "checkpoint": None
}
```

然后`background_tasks.py`中的保存代码就能正常工作。

### 方案B：直接在Pipeline内部保存（更可靠）

在`document_processing_pipeline_complete.py`的ChromaDB保存之后，直接保存到SQLite：

```python
# 阶段3: 存储到ChromaDB
# ... 现有代码 ...

# 阶段3.5: 保存到SQLite
logger.info(f"💾 阶段3.5: 保存chunks到SQLite")
from app.models.pipeline_state import DocumentChunk
import uuid

# 清除旧chunks
self.db.query(DocumentChunk).filter(
    DocumentChunk.document_id == document_id
).delete()

# 保存新chunks
for i, chunk_data in enumerate(vectorized_chunks):
    chunk = DocumentChunk(
        chunk_id=f"doc_{document_id}_chunk_{i}_{uuid.uuid4().hex[:8]}",
        document_id=document_id,
        project_id=project_id,
        text=chunk_data['text'],
        text_length=len(chunk_data['text']),
        chunk_index=i,
        total_chunks=len(vectorized_chunks),
        embedding=None,
        embedding_model="sentence-transformers",
        created_at=datetime.utcnow(),
        vectorized_at=datetime.utcnow()
    )
    self.db.add(chunk)

self.db.commit()
logger.info(f"✅ 已保存{len(vectorized_chunks)}个chunks到SQLite")
```

**我已经在第228行添加了这段代码，但是它没有被执行！**

原因是有一个**数据库模型冲突错误**：
```
Table 'pipeline_executions' is already defined
```

### 方案C：修复数据库模型冲突

**问题根源：**
`app/models/pipeline_state.py`被多次导入，导致SQLAlchemy表重复定义。

**解决方法：**
在`pipeline_state.py`的所有表定义中添加`extend_existing=True`：

```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = {'extend_existing': True}  # ✅ 添加这一行
    
    id = Column(Integer, primary_key=True)
    # ... 其他字段
```

对所有表（PipelineExecution, DocumentChunk等）都添加这个参数。

---

## 🎯 推荐实施步骤

### 步骤1：修复数据库模型冲突（最紧急）

修改`/Users/alwan/FieldMind/backend/src/app/models/pipeline_state.py`：

```python
# 找到每个class定义，添加extend_existing

class PipelineExecution(Base):
    __tablename__ = "pipeline_executions"
    __table_args__ = {'extend_existing': True}
    # ...

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = {'extend_existing': True}
    # ...

# 对所有表都添加
```

### 步骤2：验证Pipeline是否保存chunks

修改`document_processing_pipeline_complete.py`，在第228行之后添加强制日志：

```python
# 阶段3.5: 保存到SQLite
logger.info(f"🔴🔴🔴 [CRITICAL] 开始保存{len(vectorized_chunks)}个chunks到SQLite")
logger.info(f"🔴🔴🔴 [CRITICAL] document_id={document_id}, project_id={project_id}")
```

重启后端，上传文档，检查日志中是否出现`🔴🔴🔴`。

### 步骤3：如果步骤2仍然没有执行

说明代码流程在到达第228行之前就返回了。需要：
1. 在第178行（ChromaDB保存之后）添加日志
2. 在第220行添加日志
3. 找到代码提前返回的位置

### 步骤4：实现完整的自动分析流程

修复chunks保存后，集成完整的分析流程：

```python
# 在background_tasks.py中，pipeline执行成功后添加：

# 5. 关键词提取
keywords = extract_keywords(document_id, db)

# 6. 知识图谱构建
knowledge_graph = build_knowledge_graph(document_id, db)

# 7. 生成报告
reports = generate_three_layer_reports(document_id, db)

# 8. 更新文档详情
update_document_analysis_results(document_id, {
    'keywords': keywords,
    'knowledge_graph': knowledge_graph,
    'reports': reports
}, db)
```

### 步骤5：配置音频转录

在`.env`中添加：
```
OPENAI_API_KEY=your_api_key_here
WHISPER_MODEL=base  # 或 small, medium, large
```

或者使用本地Whisper模型（需要下载）。

---

## 📊 当前数据统计

```
总文档: 17个
├── 已处理（有chunks）: 1个（文档ID 1005，411 chunks）
├── 处理完成但无chunks: 9个（显示completed但chunk_count=0）
└── 失败（音频）: 7个
```

**关键发现：**
- 只有文档1005有chunks（411个）
- 这可能是唯一一个用旧流程处理的文档
- 从文档1006开始，所有文档都用了新的Pipeline
- **新Pipeline没有保存chunks到数据库**

---

## 💡 临时解决方案（手动修复）

如果想先让系统可用，可以手动从ChromaDB导出chunks到SQLite：

```python
# 运行一次性修复脚本
from app.core.rag_engine import rag_engine
from app.models.pipeline_state import DocumentChunk
from app.core.database import SessionLocal
import uuid

db = SessionLocal()

# 获取ChromaDB中的所有数据
all_data = rag_engine.collection.get()

# 按document_id分组
chunks_by_doc = {}
for i, doc_id in enumerate(all_data['metadatas']):
    doc_id = doc_id['document_id']
    if doc_id not in chunks_by_doc:
        chunks_by_doc[doc_id] = []
    
    chunks_by_doc[doc_id].append({
        'text': all_data['documents'][i],
        'metadata': all_data['metadatas'][i]
    })

# 保存到SQLite
for doc_id, chunks in chunks_by_doc.items():
    for i, chunk_data in enumerate(chunks):
        chunk = DocumentChunk(
            chunk_id=f"doc_{doc_id}_chunk_{i}_{uuid.uuid4().hex[:8]}",
            document_id=doc_id,
            project_id=chunk_data['metadata'].get('project_id'),
            text=chunk_data['text'],
            text_length=len(chunk_data['text']),
            chunk_index=i,
            total_chunks=len(chunks),
            created_at=datetime.utcnow()
        )
        db.add(chunk)

db.commit()
print(f"✅ 已从ChromaDB迁移{sum(len(c) for c in chunks_by_doc.values())}个chunks")
```

---

## 🎬 下一步行动

**我现在应该：**

1. **修复数据库模型冲突** - 添加extend_existing=True
2. **验证chunks保存代码是否执行** - 添加强制日志
3. **如果还不行，使用临时修复方案** - 从ChromaDB迁移数据
4. **实现完整的自动分析流程** - 集成所有Agent
5. **配置音频转录** - Whisper设置

**请告诉我：你想让我先做哪一个？**

或者，你有其他想法？
