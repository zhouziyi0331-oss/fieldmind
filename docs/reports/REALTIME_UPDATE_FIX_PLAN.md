# 实时更新和工作流串联修复方案

## 问题分析

### 问题1：没有渐进式实时更新
**现状**：
- WebSocket基础设施已存在（前端`WebSocketService.swift` + 后端`websocket.py`）
- 但`background_tasks.py`处理文档时**从未调用`notify_frontend()`**
- 导致前端只能看到最终结果，无法看到处理进度

**用户期望**：
```
上传文档 → 立即显示"开始处理"
→ 提取文本完成 → 推送更新 → 前端显示进度
→ 分块完成 → 推送更新 → 前端显示进度
→ 向量化完成 → 推送更新 → 前端显示进度
→ 实体提取完成 → 推送更新 → 前端显示进度
→ 质量检查完成 → 推送更新 → 前端显示结果
→ 触发知识图谱 → 推送更新 → 前端显示新图谱
```

### 问题2：功能板块工作流顺序和关联不明确
**现状**：
- `workflow_chain.py`实现了自动触发逻辑
- 但没有明确定义各功能板块的依赖关系和数据流向
- 缺少"功能板块一个个做的关联顺序"的可视化定义

**需要建立的工作流**：
```
[文档处理板块]
    ↓ 完成后触发
[实体同步板块]
    ↓ 数据流向
[知识图谱板块] (需要≥3文档, ≥10实体)
    ↓ 完成后触发
[产业分析板块] (需要≥5文档, ≥20实体)
    ↓ 数据流向
[Dashboard板块] (聚合所有数据)
```

## 修复方案

### 修复1：在每个处理步骤后发送实时更新

修改`background_tasks.py`中的`process_document_async()`函数：

**步骤1：文档开始处理**
```python
doc.status = "processing"
db.commit()
notify_frontend(doc.project_id, document_id, "processing", {
    "step": "started",
    "message": "开始处理文档"
})
```

**步骤2：内容提取完成**
```python
if content:
    doc.text_content = content
    db.commit()
    notify_frontend(doc.project_id, document_id, "processing", {
        "step": "content_extracted",
        "message": f"提取了{len(content)}字符",
        "word_count": doc.word_count
    })
```

**步骤3：向量化完成**
```python
if result.get('success'):
    chunks_count = result.get('chunks_count')
    db.commit()
    notify_frontend(doc.project_id, document_id, "processing", {
        "step": "vectorized",
        "message": f"向量化完成：{chunks_count}个块",
        "chunks_count": chunks_count
    })
```

**步骤4：实体提取完成**
```python
doc.extracted_entities = merged_entities[:50]
db.commit()
notify_frontend(doc.project_id, document_id, "processing", {
    "step": "entities_extracted",
    "message": f"提取了{len(merged_entities)}个实体",
    "entity_count": len(merged_entities)
})
```

**步骤5：质量检查完成**
```python
db.commit()
notify_frontend(doc.project_id, document_id, doc.status, {
    "step": "quality_checked",
    "quality_score": quality_result['score'],
    "quality_level": doc.extra_data['quality_level'],
    "message": "质量检查完成"
})
```

**步骤6：工作流串联触发**
```python
workflow_chain.trigger_next_workflows(doc, db)

# 推送项目统计更新
notify_project_stats_update(doc.project_id, db)
```

### 修复2：建立功能板块工作流编排器

创建`app/services/module_workflow_orchestrator.py`：

```python
"""
功能板块工作流编排器
定义各功能板块的执行顺序、依赖关系和数据流向
"""

class ModuleWorkflowOrchestrator:
    """
    功能板块编排：
    1. [文档处理] → 2. [实体同步] → 3. [知识图谱] → 4. [产业分析] → 5. [Dashboard]
    """
    
    def execute_module_chain(self, document, db: Session):
        """执行完整的功能板块链条"""
        
        # 阶段1: 文档处理（已完成，由background_tasks.py处理）
        # 输出：text_content, extracted_entities, chunks
        
        # 阶段2: 实体同步到entities表
        self._module_sync_entities(document, db)
        # 输出：entities表更新，entity_count增加
        
        # 阶段3: 检查是否触发知识图谱构建
        if self._should_trigger_knowledge_graph(document.project_id, db):
            self._module_build_knowledge_graph(document.project_id, db)
            # 输出：neo4j图谱，relationships表
        
        # 阶段4: 检查是否触发产业分析
        if self._should_trigger_industry_analysis(document.project_id, db):
            self._module_generate_industry_analysis(document.project_id, db)
            # 输出：industry_insights表
        
        # 阶段5: 刷新Dashboard统计
        self._module_refresh_dashboard(document.project_id, db)
        # 输出：dashboard缓存更新
    
    def _module_sync_entities(self, document, db):
        """阶段2: 实体同步板块"""
        notify_module_start("entity_sync", document.project_id)
        # ... 同步逻辑 ...
        notify_module_complete("entity_sync", document.project_id, result)
    
    def _module_build_knowledge_graph(self, project_id, db):
        """阶段3: 知识图谱构建板块"""
        notify_module_start("knowledge_graph", project_id)
        # ... 构建逻辑 ...
        notify_module_complete("knowledge_graph", project_id, result)
    
    def _module_generate_industry_analysis(self, project_id, db):
        """阶段4: 产业分析生成板块"""
        notify_module_start("industry_analysis", project_id)
        # ... 分析逻辑 ...
        notify_module_complete("industry_analysis", project_id, result)
    
    def _module_refresh_dashboard(self, project_id, db):
        """阶段5: Dashboard数据刷新板块"""
        notify_module_start("dashboard_refresh", project_id)
        # ... 刷新逻辑 ...
        notify_module_complete("dashboard_refresh", project_id, result)
```

### 修复3：扩展WebSocket消息类型

在`app/core/websocket.py`添加新的通知方法：

```python
async def notify_module_status(self, project_id: int, module_name: str, status: str, data: dict = None):
    """通知功能板块状态变化"""
    message = {
        "type": "module_status",
        "module": module_name,  # "entity_sync", "knowledge_graph", "industry_analysis"
        "status": status,       # "started", "processing", "completed", "failed"
        "data": data or {},
        "timestamp": datetime.utcnow().isoformat()
    }
    await self.broadcast_to_project(message, project_id)

async def notify_processing_progress(self, project_id: int, document_id: int, step: str, progress: float, message: str):
    """通知处理进度"""
    message = {
        "type": "processing_progress",
        "document_id": document_id,
        "step": step,           # "content_extracted", "vectorized", "entities_extracted"
        "progress": progress,   # 0.0 - 1.0
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    await self.broadcast_to_project(message, project_id)
```

## 实施顺序

1. **先修复实时更新**（修复1） - 让用户能看到处理进度
2. **再建立功能板块编排**（修复2） - 明确各板块关联
3. **最后扩展前端监听**（修复3） - 前端显示板块状态

## 预期效果

### 用户上传文档后看到的实时更新：
```
08:00:01 - 📄 开始处理文档
08:00:05 - ✅ 提取了12,345字符
08:00:15 - ✅ 向量化完成：45个块
08:00:25 - ✅ 提取了23个实体
08:00:30 - ✅ 质量检查通过（得分：85.5）
08:00:31 - 🔗 开始实体同步...
08:00:32 - ✅ 实体已同步到知识库
08:00:33 - 🧠 触发知识图谱构建...
08:00:45 - ✅ 知识图谱更新完成
08:00:46 - 📊 Dashboard已刷新
```

### 功能板块依赖关系清晰可见：
```
[文档1完成] → [同步3个实体] → [Dashboard更新]
[文档2完成] → [同步5个实体] → [Dashboard更新]
[文档3完成] → [同步8个实体] → [触发知识图谱] → [图谱构建完成] → [Dashboard更新]
[文档4完成] → [同步12个实体] → [知识图谱增量更新] → [Dashboard更新]
[文档5完成] → [同步15个实体] → [触发产业分析] → [分析报告生成] → [Dashboard更新]
```
