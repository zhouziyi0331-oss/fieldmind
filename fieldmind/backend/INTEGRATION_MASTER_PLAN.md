# FieldMind 数据流整合 - 总规划

## 📊 当前系统真实状态（经过深度诊断）

### 现有数据流路径

```
前端上传 
  ↓
documents.py::upload_document()
  ↓
upload_project_document() → 保存到 project_documents 表
  ↓
submit_task(document_id) 
  ↓
background_tasks.py::submit_document_task()
  ↓
DocumentProcessor.process_document_async() [线程池执行]
  ├─ 1. load_document()
  ├─ 2. extract_content() [调用 IngestionAgent]
  ├─ 3. save_content() → text_content 保存到数据库
  ├─ 4. chunk_and_quantify() → 创建 document_chunks
  ├─ 5. extract_keywords()
  ├─ 6. run_deep_processing() → DocumentProcessingPipelineComplete
  ├─ 7. generate_summary() → FileSummaryGenerator（旧版缩影）
  └─ 8. finalize() → status = 'completed'
```

### ❌ 断联点诊断

**断联点 #1: 九步流水线完全游离**
- `knowledge_pipeline/pipeline_orchestrator.py` 存在但**从未被调用**
- `DocumentProcessor.run_deep_processing()` 调用的是 `DocumentProcessingPipelineComplete`（旧版）
- 九步流水线与主系统 0% 集成

**断联点 #2: 数据契约未应用**
- `contracts.py` 存在但未被任何模块导入
- 没有脏数据→干净数据的验证门控
- 数据直接进入处理流程，无质量保证

**断联点 #3: 事件总线未触发**
- `event_bus.py` 和 `event_handler_registry.py` 完整实现
- 但 `DocumentProcessor` 不发布任何事件
- `pipeline_orchestrator.py` 发布事件但从未被调用
- 缩影系统不会自动触发

**断联点 #4: 新旧系统混杂**
- 旧版: `DocumentProcessingPipelineComplete`、`FileSummaryGenerator`
- 新版: `knowledge_pipeline/*`、`enhanced_summary_generator.py`
- 旧版在运行，新版被忽略

**断联点 #5: 知识图谱未接入**
- `knowledge_graph/*` 完整实现
- API 路由 `knowledge_graph.py` 未注册到 `main.py`
- 前端无法访问知识图谱数据

---

## 🎯 整合目标（可验证指标）

### 核心目标
1. **数据流完整性**: 上传→契约验证→九步流水线→事件总线→缩影生成→知识图谱，全链路贯通
2. **数据连接率**: 从 30% 提升到 ≥95%
3. **自动化率**: 100%（0 人工干预）
4. **可追溯性**: 每个数据片段都能追溯到源文档和处理步骤

### 可验证指标
- ✅ 每个上传的文档都经过九步流水线
- ✅ 每个文档都有数据契约验证记录
- ✅ 每个流水线完成后自动发布事件
- ✅ 每个文档自动生成新版缩影（包含 KG/Wiki/本体关联）
- ✅ 知识图谱可通过 API 查询和可视化
- ✅ 前端可实时看到处理进度（9 步）

---

## 📋 整合计划（10 个阶段）

### 阶段 1: 创建统一管道协调器 ✅
**目标**: 串联所有处理步骤，替代 `DocumentProcessor`

**文件**: `backend/src/app/services/unified_pipeline_coordinator.py`

**功能**:
```python
class UnifiedPipelineCoordinator:
    """统一管道协调器 - 串联脏数据通道、契约验证、九步流水线、事件总线"""
    
    def process_document(self, document_id: int) -> Dict[str, Any]:
        """
        完整处理流程:
        1. 加载文档
        2. 提取内容（脏数据通道）
        3. 数据契约验证
        4. 转换为干净数据
        5. 进入九步知识流水线
        6. 发布流水线完成事件
        7. 自动触发缩影生成
        8. 更新知识图谱
        9. 完成处理
        """
```

**验收标准**:
- ✅ 代码完整可运行
- ✅ 包含所有 9 步的调用
- ✅ 包含数据契约验证
- ✅ 包含事件发布
- ✅ 有详细日志输出
- ✅ 有错误处理和回滚

---

### 阶段 2: 修改后台任务处理器 ✅
**目标**: 将 `background_tasks.py` 的 `DocumentProcessor` 替换为 `UnifiedPipelineCoordinator`

**文件**: `backend/src/app/services/background_tasks.py`

**修改内容**:
```python
# 旧代码（删除）
def process_document_async(document_id: int):
    processor = DocumentProcessor(db, document_id)
    processor.run_deep_processing()  # 调用旧版 pipeline
    processor.generate_summary()      # 调用旧版 summary

# 新代码（替换）
def process_document_async(document_id: int):
    from app.services.unified_pipeline_coordinator import UnifiedPipelineCoordinator
    
    coordinator = UnifiedPipelineCoordinator(db)
    result = coordinator.process_document(document_id)
    
    # 完整流程：契约验证 → 九步流水线 → 事件发布 → 缩影生成
```

**验收标准**:
- ✅ 移除所有对 `DocumentProcessingPipelineComplete` 的调用
- ✅ 移除所有对 `FileSummaryGenerator` 的调用
- ✅ 使用新的 `UnifiedPipelineCoordinator`
- ✅ 保留现有的错误处理和通知机制

---

### 阶段 3: 集成数据契约验证 ✅
**目标**: 在进入九步流水线前验证数据质量

**文件**: `backend/src/app/services/unified_pipeline_coordinator.py`

**集成点**:
```python
# 在 process_document() 中
def process_document(self, document_id: int):
    # ... 提取内容后 ...
    
    # 转换为干净数据
    clean_data = DirtyToCleanConverter.convert(
        raw_data={'filename': doc.filename, 'file_type': doc.file_type},
        extracted_text=content,
        document_id=document_id
    )
    
    # 验证契约
    is_valid, errors = CleanDataContract.validate(clean_data)
    if not is_valid:
        raise DataContractViolation(f"数据契约验证失败: {errors}")
    
    # 检查门控
    can_enter, reason = PipelineGate.can_enter_knowledge_pipeline(clean_data)
    if not can_enter:
        raise PipelineGateRejection(reason)
    
    # 记录验证通过
    self._record_contract_validation(document_id, clean_data)
    
    # 进入九步流水线 ...
```

**验收标准**:
- ✅ 每个文档都有契约验证记录
- ✅ 不符合契约的文档被拒绝并标记
- ✅ 验证结果保存到 `extra_data` 字段
- ✅ 日志清晰记录验证过程

---

### 阶段 4: 接入九步知识流水线 ✅
**目标**: 将 `knowledge_pipeline/pipeline_orchestrator.py` 集成到主流程

**文件**: `backend/src/app/services/unified_pipeline_coordinator.py`

**集成点**:
```python
def process_document(self, document_id: int):
    # ... 契约验证通过后 ...
    
    # 调用九步流水线
    from app.services.knowledge_pipeline.pipeline_orchestrator import KnowledgePipeline
    
    pipeline = KnowledgePipeline(self.db)
    pipeline_result = pipeline.run(
        document_id=document_id,
        skip_steps=None  # 执行所有步骤
    )
    
    if not pipeline_result['success']:
        raise PipelineExecutionError(
            f"九步流水线失败: {pipeline_result.get('error')}"
        )
    
    # 记录流水线结果
    self._record_pipeline_execution(document_id, pipeline_result)
    
    # 继续后续步骤 ...
```

**验收标准**:
- ✅ 九步流水线被完整执行
- ✅ 每一步的结果都被记录
- ✅ 失败时有清晰的错误信息
- ✅ 执行时间被监控

---

### 阶段 5: 集成事件总线 ✅
**目标**: 流水线完成后自动发布事件，触发下游服务

**文件**: `backend/src/app/services/knowledge_pipeline/pipeline_orchestrator.py`

**修改内容**:
```python
# 在 KnowledgePipeline.run() 完成后
def run(self, document_id: int, skip_steps: list = None):
    # ... 执行九步 ...
    
    # 发布流水线完成事件
    publish_event(
        event_type=EventTypes.PIPELINE_COMPLETED,
        payload={
            'document_id': document_id,
            'project_id': project_id,
            'steps_completed': len(results),
            'elapsed_time': elapsed_time,
            'entities_count': results.get(3, {}).get('entities_count', 0),
            'events_count': results.get(4, {}).get('events_count', 0),
            'relationships_count': results.get(5, {}).get('relationships_count', 0),
            'knowledge_units_count': results.get(8, {}).get('units_count', 0)
        },
        publisher='KnowledgePipeline'
    )
    
    # 特别发布 KNOWLEDGE_UNITS_CREATED 事件（触发缩影生成）
    if 8 in results:  # Step 8 成功
        publish_event(
            event_type=EventTypes.KNOWLEDGE_UNITS_CREATED,
            payload={
                'document_id': document_id,
                'project_id': project_id,
                'units_count': results[8].get('units_count', 0)
            },
            publisher='KnowledgePipeline'
        )
```

**验收标准**:
- ✅ 每个流水线完成后都发布事件
- ✅ 事件包含完整的上下文信息
- ✅ 事件被正确记录到数据库
- ✅ 下游服务能接收到事件

---

### 阶段 6: 自动触发缩影生成 ✅
**目标**: 监听 `KNOWLEDGE_UNITS_CREATED` 事件，自动生成新版缩影

**文件**: `backend/src/app/services/event_handlers/event_handler_registry.py`

**确认现有代码**:
```python
# 已有的事件处理器
@event_handler_registry.register(EventTypes.KNOWLEDGE_UNITS_CREATED)
def handle_knowledge_units_created(event_data: Dict[str, Any]):
    """知识单元创建完成 → 自动生成缩影"""
    document_id = event_data.get('document_id')
    
    from app.services.summary.enhanced_summary_generator import EnhancedSummaryGenerator
    
    generator = EnhancedSummaryGenerator(db)
    summary = generator.generate_summary(document_id)
    
    # 保存缩影到数据库 ...
```

**需要修改**:
- ✅ 确认事件处理器被正确注册
- ✅ 确认事件总线会调用处理器
- ✅ 添加错误处理（缩影生成失败不应阻断主流程）
- ✅ 添加详细日志

**验收标准**:
- ✅ 九步流水线完成后，自动触发缩影生成
- ✅ 缩影包含知识图谱、Wiki、本体的关联
- ✅ 缩影生成失败不影响文档状态
- ✅ 缩影结果保存到 `document_summaries` 表

---

### 阶段 7: 注册知识图谱 API ✅
**目标**: 将知识图谱 API 注册到 FastAPI，使前端可访问

**文件**: `backend/src/app/main.py`

**修改内容**:
```python
# 在 main.py 中添加
from app.api import knowledge_graph

# 注册路由
app.include_router(
    knowledge_graph.router,
    prefix="/api/knowledge-graph",
    tags=["knowledge-graph"]
)
```

**文件**: `backend/src/app/api/knowledge_graph.py`

**确认 API 端点**:
- ✅ `GET /api/knowledge-graph/nodes` - 查询节点
- ✅ `GET /api/knowledge-graph/edges` - 查询边
- ✅ `GET /api/knowledge-graph/query` - 统一查询接口
- ✅ `GET /api/knowledge-graph/visualization` - 可视化数据
- ✅ `GET /api/knowledge-graph/analysis` - 图分析

**验收标准**:
- ✅ 所有 API 端点可通过 `/docs` 访问
- ✅ 前端可成功调用 API
- ✅ 返回数据格式符合前端需求
- ✅ 包含错误处理和数据验证

---

### 阶段 8: 创建进度追踪 API ✅
**目标**: 前端可实时查看九步流水线的执行进度

**文件**: `backend/src/app/api/documents.py`

**新增端点**:
```python
@router.get("/{document_id}/pipeline-progress")
def get_pipeline_progress(document_id: int, db: Session = Depends(get_db)):
    """
    获取文档的流水线执行进度
    
    返回:
    {
        "document_id": 123,
        "pipeline_status": "processing",
        "current_step": 5,
        "total_steps": 9,
        "steps": [
            {"step": 1, "name": "text_cleaning", "status": "completed", "elapsed_time": 0.5},
            {"step": 2, "name": "structure_analysis", "status": "completed", "elapsed_time": 1.2},
            ...
            {"step": 5, "name": "relationship_discovery", "status": "running", "elapsed_time": null},
            {"step": 6, "name": "ontology_construction", "status": "pending", "elapsed_time": null},
            ...
        ],
        "contract_validation": {
            "status": "passed",
            "validated_at": "2024-01-01T10:00:00Z"
        }
    }
    """
```

**验收标准**:
- ✅ 前端可轮询此 API 获取进度
- ✅ 进度数据实时更新
- ✅ 包含每一步的状态和耗时
- ✅ 包含契约验证结果

---

### 阶段 9: 端到端测试 ✅
**目标**: 验证完整数据流，确保 100% 集成

**文件**: `backend/tests/integration/test_unified_data_flow.py`

**测试用例**:
```python
def test_complete_data_flow():
    """测试完整数据流：上传 → 契约验证 → 九步流水线 → 事件发布 → 缩影生成"""
    
    # 1. 上传文档
    doc = upload_test_document()
    
    # 2. 等待处理完成
    wait_for_completion(doc.id)
    
    # 3. 验证契约记录
    assert_contract_validation_recorded(doc.id)
    
    # 4. 验证九步流水线执行
    assert_pipeline_executed(doc.id, expected_steps=9)
    
    # 5. 验证事件发布
    assert_events_published(doc.id, expected_events=[
        'PIPELINE_STARTED',
        'PIPELINE_COMPLETED',
        'KNOWLEDGE_UNITS_CREATED'
    ])
    
    # 6. 验证缩影生成
    summary = get_document_summary(doc.id)
    assert summary is not None
    assert 'knowledge_graph_associations' in summary
    
    # 7. 验证知识图谱
    kg_nodes = get_kg_nodes(document_id=doc.id)
    assert len(kg_nodes) > 0
    
    # 8. 验证数据连接率
    connectivity = calculate_connectivity_rate(doc.id)
    assert connectivity >= 0.95  # ≥95%
```

**验收标准**:
- ✅ 所有测试用例通过
- ✅ 数据连接率 ≥95%
- ✅ 处理时间在可接受范围内
- ✅ 无数据丢失或断联

---

### 阶段 10: 前端集成和文档 ✅
**目标**: 更新前端，展示新功能；编写完整文档

**前端修改**:
1. 文档上传页面：显示九步流水线进度条
2. 文档详情页面：显示契约验证结果、流水线执行详情
3. 知识图谱页面：调用新的 KG API，展示可视化
4. 缩影展示页面：显示新版缩影（包含 KG/Wiki/本体关联）

**文档**:
1. `UNIFIED_DATA_FLOW_ARCHITECTURE.md` - 架构文档
2. `API_INTEGRATION_GUIDE.md` - API 集成指南
3. `FRONTEND_INTEGRATION_GUIDE.md` - 前端集成指南
4. `DEPLOYMENT_GUIDE.md` - 部署指南

**验收标准**:
- ✅ 前端可正常使用所有新功能
- ✅ 所有文档完整清晰
- ✅ 包含示例代码和截图
- ✅ 包含故障排查指南

---

## 🔍 验收总清单

### 功能完整性
- [ ] 每个上传的文档都经过数据契约验证
- [ ] 每个文档都经过完整的九步流水线
- [ ] 每个流水线完成后都自动生成缩影
- [ ] 知识图谱可通过 API 访问
- [ ] 前端可实时查看处理进度

### 数据完整性
- [ ] 数据连接率 ≥95%
- [ ] 所有知识组件都可追溯到源文档
- [ ] 契约验证记录完整
- [ ] 事件日志完整

### 性能
- [ ] 平均处理时间 <10 秒/文档
- [ ] 九步流水线执行时间合理
- [ ] 缩影生成时间 <5 秒
- [ ] API 响应时间 <1 秒

### 稳定性
- [ ] 错误处理完善
- [ ] 失败时有清晰的错误信息
- [ ] 支持重试机制
- [ ] 无数据丢失

### 可维护性
- [ ] 代码结构清晰
- [ ] 日志详细完整
- [ ] 文档齐全
- [ ] 测试覆盖率 ≥80%

---

## 📅 执行计划

### Week 1: 核心整合（阶段 1-4）
- Day 1-2: 创建统一管道协调器
- Day 3: 修改后台任务处理器
- Day 4: 集成数据契约验证
- Day 5: 接入九步知识流水线

### Week 2: 事件和服务（阶段 5-7）
- Day 1: 集成事件总线
- Day 2: 自动触发缩影生成
- Day 3: 注册知识图谱 API

### Week 3: 测试和交付（阶段 8-10）
- Day 1-2: 创建进度追踪 API
- Day 3-4: 端到端测试
- Day 5: 前端集成和文档

---

## 🚀 开始执行

现在进入 **阶段 1: 创建统一管道协调器**
