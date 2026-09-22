# FieldMind 统一数据流架构

## 问题诊断

### 当前断联问题：
1. ❌ **九步知识流水线（knowledge_pipeline/）** - 独立实现，未连接到主系统
2. ❌ **原有文档处理管道（document_pipeline.py）** - 独立运行，不经过九步流水线
3. ❌ **数据契约（contracts.py）** - 存在但未应用到九步流水线
4. ❌ **事件总线（event_bus.py）** - 独立实现，未接入主API
5. ❌ **知识图谱服务** - 独立实现，未与前端API集成
6. ❌ **缩影系统（summary/）** - 独立实现，未自动触发

### 根本原因：
**数据流是断裂的** - 每个模块都是独立的"孤岛"，没有真正串联成统一系统。

---

## 统一架构设计

### 完整数据流（端到端）

```
前端上传
    ↓
[API Gateway] (main.py + routes/)
    ↓
[脏数据通道] document_processing_pipeline_v2.py
    ├─ 多模态解析（PDF/Word/Audio/Video）
    ├─ 文本提取
    ├─ 时间标准化
    └─ 输出：结构化MD文档
    ↓
[数据契约验证] contracts.py
    └─ 验证数据是否符合"干净数据"标准
    ↓
[干净数据通道] knowledge_pipeline/ (9步)
    ├─ Step 1: 文本清洗
    ├─ Step 2: 结构分析
    ├─ Step 3: 实体提取
    ├─ Step 4: 事件提取
    ├─ Step 5: 关系发现
    ├─ Step 6: 本体构建
    ├─ Step 7: 逻辑推理
    ├─ Step 8: 知识单元化
    └─ Step 9: Reader生成
    ↓
[事件总线] event_bus.py
    └─ 发布 KNOWLEDGE_UNITS_CREATED 事件
    ↓
[自动触发] event_handler_registry.py
    └─ 监听事件 → 自动调用缩影生成
    ↓
[缩影系统] summary/enhanced_summary_generator.py
    ├─ 读取所有知识组件
    ├─ 生成三级缩影
    └─ 关联知识图谱/Wiki/本体
    ↓
[知识图谱中台] knowledge_graph/
    ├─ 查询服务
    ├─ 可视化API
    └─ 分析服务
    ↓
前端展示
```

---

## 整合计划（5步）

### Step 1: 修改文档上传API，接入完整流水线
**文件：** `backend/src/app/api/documents.py`
- 修改上传接口，调用完整流水线
- 脏数据通道 → 契约验证 → 干净数据通道 → 事件发布

### Step 2: 创建统一管道协调器
**文件：** `backend/src/app/services/unified_pipeline_coordinator.py`
- 串联所有处理步骤
- 数据契约验证
- 错误处理和回滚

### Step 3: 接入事件总线到主流程
**文件：** 修改 `knowledge_pipeline/pipeline_orchestrator.py`
- 完成九步后自动发布事件
- 触发缩影生成

### Step 4: 整合知识图谱API到前端路由
**文件：** `backend/src/app/api/knowledge_graph.py`
- 注册到main.py
- 连接前端可视化组件

### Step 5: 端到端测试和验证
**文件：** `backend/tests/integration/test_unified_flow.py`
- 完整流程测试
- 数据连接率验证

---

## 数据契约定义

### 脏数据 → 干净数据的标准

```python
# 脏数据（Raw）
{
    "raw_content": bytes,
    "mime_type": str,
    "filename": str
}

# 契约验证条件
class CleanDataContract:
    required_fields = [
        "document_id",
        "text_content",      # 必须是纯文本
        "word_count",        # 必须 > 0
        "file_type",         # 必须是支持的类型
        "created_at",        # 必须有时间戳
        "metadata"           # 必须包含元数据
    ]
    
    @staticmethod
    def validate(data: dict) -> tuple[bool, list[str]]:
        """验证数据是否符合干净数据标准"""
        errors = []
        
        for field in CleanDataContract.required_fields:
            if field not in data:
                errors.append(f"缺少字段: {field}")
        
        if data.get("word_count", 0) <= 0:
            errors.append("文档内容为空")
        
        if data.get("text_content") and not isinstance(data["text_content"], str):
            errors.append("text_content 必须是字符串")
        
        return len(errors) == 0, errors

# 干净数据（Clean）- 可进入九步流水线
{
    "document_id": int,
    "text_content": str,     # 纯文本
    "word_count": int,       # > 0
    "file_type": str,
    "created_at": datetime,
    "metadata": {
        "source_level": str,  # RAW_MATERIAL/FIRST_HAND/...
        "document_date": datetime,
        "tags": list,
        "confidence": float
    }
}
```

---

## 执行顺序

1. ✅ 创建此架构文档
2. ⏳ 创建数据契约验证器
3. ⏳ 创建统一管道协调器
4. ⏳ 修改文档上传API
5. ⏳ 接入事件总线
6. ⏳ 整合知识图谱API
7. ⏳ 端到端测试

---

## 成功标准

- ✅ 前端上传 → 自动经过所有流水线 → 最终生成缩影
- ✅ 数据连接率 ≥ 95%
- ✅ 所有模块通过契约验证
- ✅ 事件总线自动触发所有下游服务
- ✅ 知识图谱可视化正常显示
- ✅ 0 人工干预

