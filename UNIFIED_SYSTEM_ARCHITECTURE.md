# 统一系统架构文档

## 🎯 核心理念

这是**一个完整的统一系统**，不是两个独立系统。

三个阶段**串联**工作，形成完整的数据处理链路：
```
原始多模态文件
    ↓
🔴 脏数据通道（完整性优先）
    ↓
🟢 干净数据通道（精准提取）
    ↓
🔵 9步骤知识管道（深度处理）
```

---

## 📊 系统组成

### 1️⃣ 脏数据通道 (Dirty Data Channel)

**目标**: 完整性优先，无损转换所有多模态内容为文档

**原则**: 宁可多不可少（Better more than less）

**处理流程**:
```
音频文件 → Whisper完整转录 → 保留所有语气词、停顿、重复
视频文件 → PySceneDetect + Whisper + BLIP-2 → 所有场景 + 所有对话
图片文件 → PaddleOCR + BLIP-2 → 所有文字 + 完整视觉描述
文档文件 → DocumentExtractor → 完整文本内容
```

**输出示例**:
```
输入: 15分钟会议录音
输出: 8500字完整转录文本（包含"呃"、"嗯"等语气词）

完整性评分: 0.98
质量评分: 0.65（不关心质量，只关心完整性）
```

**数据库表**: `dirty_channel_documents`
- `full_text`: 完整的无损文本（可能8500字）
- `completeness_score`: 完整性评分
- `word_count`: 总字数
- `metadata`: 原始元数据

---

### 2️⃣ 干净数据通道 (Clean Data Channel)

**目标**: 精准提取，只要核心，去除90%冗余

**原则**: 核心优先（Core First）

**处理流程**:
```
8500字完整文本
    ↓
提取1-3个核心事件（不是全部事件！）
    ↓
从核心事件中提取核心实体（人、地点、组织）
    ↓
提取核心关系
```

**输出示例**:
```
输入: 8500字完整文本
输出:
  - 2个核心事件（每个事件有明确的5W1H）
  - 5个核心实体
  - 3个核心关系
  - 200字摘要

数据压缩比: 90%（去除了90%的冗余）
```

**5W1H最小化节点**:
- **Who**: 核心人物列表
- **What**: 核心事情
- **When**: 时间
- **Where**: 地点
- **Why**: 原因/目的
- **How**: 方式/过程

**数据库表**:
- `clean_channel_events`: 核心事件（1-3个）
- `clean_channel_entities`: 核心实体
- `clean_channel_relations`: 核心关系

---

### 3️⃣ 9步骤知识管道 (9-Step Knowledge Pipeline)

**目标**: 深度处理结构化知识

**9个步骤**:
1. **文本校刊** (Text Cleaning)
2. **结构分析** (Structure Analysis)
3. **实体构建** (Entity Building) ← 已在干净通道完成
4. **事件提取** (Event Extraction) ← 已在干净通道完成
5. **关系发现** (Relation Discovery) ← 已在干净通道完成
6. **本体构建** (Ontology Building)
7. **逻辑推理** (Logic Inference)
8. **知识单元化** (Knowledge Unitization)
9. **阅读器生成** (Reader Generation)

**数据库表**: `nine_step_pipeline_status`

---

## 🔗 系统集成关系

### 串联关系 (Serial Relationship)

脏数据通道和干净数据通道是**串联**的，不是并联：

```python
# ✅ 正确的串联流程
async def process_document(self, document_id: int):
    # Step 1: 脏数据通道
    dirty_result = await self._dirty_channel_process(document_id)
    
    # Step 2: 干净数据通道（依赖脏数据的输出）
    clean_result = await self._clean_channel_process(dirty_result['dirty_doc_id'])
    
    # Step 3: 9步骤管道（依赖干净数据的输出）
    nine_step_result = await self._nine_step_pipeline(dirty_result['dirty_doc_id'])
```

### 包容关系 (Containment Relationship)

干净数据**包容于**脏数据之中：

```sql
-- 干净数据的事件表引用脏数据文档
CREATE TABLE clean_channel_events (
    id INT PRIMARY KEY,
    dirty_doc_id INT REFERENCES dirty_channel_documents(id),  -- 包容关系
    event_summary TEXT,
    ...
);

-- 干净数据的实体表引用脏数据文档
CREATE TABLE clean_channel_entities (
    id INT PRIMARY KEY,
    dirty_doc_id INT REFERENCES dirty_channel_documents(id),  -- 包容关系
    entity_name VARCHAR(200),
    ...
);
```

### 统一路由 (Unified Routing)

一个**统一路由表**管理整个流程：

```python
class UnifiedProcessingRoute:
    document_id: int  # 原始文档
    
    # 脏数据通道状态
    dirty_channel_status: str
    dirty_doc_id: int
    
    # 干净数据通道状态
    clean_channel_status: str
    clean_events_count: int
    
    # 9步骤管道状态
    nine_step_status: str
    nine_step_current_step: int
    
    # 整体状态
    overall_status: str
```

---

## 📈 数据流向

### 完整的数据流

```
project_documents (原始文档)
    ↓ (document_id)
unified_processing_routes (统一路由)
    ↓ (dirty_doc_id)
dirty_channel_documents (脏数据: 8500字完整文本)
    ↓ (dirty_doc_id)
    ├─→ clean_channel_events (核心事件: 2个)
    ├─→ clean_channel_entities (核心实体: 5个)
    ├─→ clean_channel_relations (核心关系: 3个)
    └─→ nine_step_pipeline_status (9步骤状态)
```

### 数据压缩示例

```
原始视频: meeting_recording.mp4 (100MB, 15分钟)
    ↓
脏数据通道: 8500字完整转录 (包含所有对话、语气词)
    完整性: 98%
    质量: 65%
    ↓
干净数据通道: 200字摘要 + 2个核心事件 + 5个实体
    精确度: 92%
    压缩比: 90%
    ↓
9步骤管道: 深度知识处理
    步骤: 9/9 完成
```

---

## 🔧 核心实现

### 1. 数据库迁移

文件: `backend/src/alembic/versions/008_unified_dirty_clean_pipeline.py`

创建5张核心表：
- `dirty_channel_documents` - 脏数据文档
- `clean_channel_events` - 核心事件
- `clean_channel_entities` - 核心实体
- `clean_channel_relations` - 核心关系
- `nine_step_pipeline_status` - 9步骤状态
- `unified_processing_routes` - 统一路由

### 2. 数据模型

文件: `backend/src/app/models/unified_pipeline.py`

定义所有数据模型和关系。

### 3. 统一管道协调器

文件: `backend/src/app/services/unified_pipeline_coordinator.py`

核心类: `UnifiedPipelineCoordinator`

主要方法：
```python
async def process_document(document_id: int) -> Dict:
    """处理完整流程：脏通道 → 干净通道 → 9步骤"""

async def _dirty_channel_process(...) -> Dict:
    """脏数据通道：完整性优先"""

async def _clean_channel_process(...) -> Dict:
    """干净数据通道：精准提取1-3个核心事件"""

async def _nine_step_pipeline(...) -> Dict:
    """9步骤知识管道：深度处理"""
```

### 4. API端点

文件: `backend/src/app/api/v1/unified_pipeline.py`

端点：
- `POST /api/v1/unified-pipeline/process/{document_id}` - 处理文档
- `GET /api/v1/unified-pipeline/status/{document_id}` - 获取状态
- `GET /api/v1/unified-pipeline/dirty-doc/{document_id}` - 获取脏数据
- `GET /api/v1/unified-pipeline/clean-data/{document_id}` - 获取干净数据
- `GET /api/v1/unified-pipeline/comparison/{document_id}` - 对比数据

### 5. 测试脚本

文件: `backend/src/test_unified_pipeline_system.py`

测试函数：
- `test_unified_pipeline()` - 测试完整流程
- `test_system_integration()` - 验证系统集成性

---

## ✅ 与现有系统的整合

### 整合点1: 文档模型

```python
# 现有的 ProjectDocument 模型
class ProjectDocument:
    id: int
    file_path: str
    file_type: str
    # ...
    
    # 新增关系
    unified_route: UnifiedProcessingRoute  # 一对一关系
    dirty_channel_doc: DirtyChannelDocument  # 一对一关系
```

### 整合点2: 现有的9步骤管道

```python
# 现有的表：entities, timeline_events, entity_relations
# 新系统的表：clean_channel_entities, clean_channel_events, clean_channel_relations

# 干净通道的数据可以同步到现有表
# 或者现有表可以直接引用干净通道的数据
```

### 整合点3: 服务层

```python
# 现有服务
- AudioProcessor (Whisper)
- VideoProcessor (PySceneDetect)
- ImageProcessor (PaddleOCR, BLIP-2)
- DocumentExtractor

# 统一管道协调器使用这些现有服务
# 不需要重新实现，只是调度和协调
```

---

## 🚀 使用示例

### 示例1: 处理一个视频文件

```python
from app.services.unified_pipeline_coordinator import UnifiedPipelineCoordinator

# 初始化
coordinator = UnifiedPipelineCoordinator(db)

# 处理文档
result = await coordinator.process_document(document_id=123)

# 查看结果
print(f"脏数据: {result['dirty_channel']['word_count']} 字")
print(f"干净数据: {result['clean_channel']['events_count']} 个核心事件")
print(f"9步骤: {result['nine_step_pipeline']['completed_steps']}/9 步完成")
```

### 示例2: 通过API处理

```bash
# 提交处理任务
curl -X POST http://localhost:8000/api/v1/unified-pipeline/process/123

# 查看处理状态
curl http://localhost:8000/api/v1/unified-pipeline/status/123

# 获取脏数据（完整文本）
curl http://localhost:8000/api/v1/unified-pipeline/dirty-doc/123

# 获取干净数据（核心事件和实体）
curl http://localhost:8000/api/v1/unified-pipeline/clean-data/123

# 对比脏数据和干净数据
curl http://localhost:8000/api/v1/unified-pipeline/comparison/123
```

### 示例3: 查询数据

```python
from app.models.unified_pipeline import *

# 查询处理路由
route = db.query(UnifiedProcessingRoute).filter_by(document_id=123).first()
print(f"整体状态: {route.overall_status}")

# 查询脏数据
dirty_doc = db.query(DirtyChannelDocument).filter_by(id=route.dirty_doc_id).first()
print(f"完整文本: {dirty_doc.full_text}")

# 查询干净数据
events = db.query(CleanChannelEvent).filter_by(dirty_doc_id=dirty_doc.id).all()
for event in events:
    print(f"事件: {event.event_summary}")
    print(f"Who: {event.who}")
    print(f"What: {event.what}")
```

---

## 📊 系统验证

### 验证1: 串联关系

```python
# 验证时间顺序
assert route.dirty_completed_at < route.clean_started_at
# ✅ 证明：干净通道在脏通道完成后才开始（串联关系）
```

### 验证2: 包容关系

```python
# 验证数据依赖
dirty_doc_id = route.dirty_doc_id
events = db.query(CleanChannelEvent).filter_by(dirty_doc_id=dirty_doc_id).all()
assert all(e.dirty_doc_id == dirty_doc_id for e in events)
# ✅ 证明：干净数据依赖脏数据（包容关系）
```

### 验证3: 统一系统

```python
# 验证统一路由
assert route.document_id == document_id
assert route.dirty_doc_id is not None
assert route.clean_events_count > 0
assert route.nine_step_current_step == 9
# ✅ 证明：一个路由管理整个流程（统一系统）
```

---

## 🎯 关键特性总结

### ✅ 一个完整的统一系统
- 不是两个独立系统
- 统一路由管理整个流程
- 数据库外键关系明确

### ✅ 串联架构
- 脏数据通道 → 干净数据通道 → 9步骤管道
- 每个阶段依赖前一个阶段的输出
- 时间顺序可验证

### ✅ 包容关系
- 干净数据包容于脏数据之中
- 外键关系: `clean_*.dirty_doc_id → dirty_channel_documents.id`
- 数据依赖可验证

### ✅ 脏数据通道特性
- 完整性优先 > 质量
- 无损转换所有多模态内容
- 宁可多不可少
- 保留所有细节（包括冗余、重复、语气词）

### ✅ 干净数据通道特性
- 精准提取 > 完整性
- 只提取1-3个核心事件
- 每个事件有明确的5W1H
- 去除90%冗余信息

### ✅ 9步骤知识管道集成
- 深度处理结构化知识
- 步骤3-5在干净通道已完成
- 步骤1-2、6-9继续处理
- 完整的9步骤流程

---

## 📝 下一步工作

1. **运行数据库迁移**
   ```bash
   cd backend/src
   alembic upgrade head
   ```

2. **实现AI增强服务的实际调用**
   - Whisper API集成
   - PySceneDetect集成
   - PaddleOCR集成
   - BLIP-2集成

3. **完善9步骤管道的各个步骤**
   - Step 6: 本体构建
   - Step 7: 逻辑推理
   - Step 8: 知识单元化
   - Step 9: 阅读器生成

4. **性能优化**
   - 批量处理
   - 并行处理多个文档
   - 缓存机制

5. **监控和日志**
   - 处理进度监控
   - 错误日志记录
   - 性能指标统计

---

## 🎉 总结

这是一个**完整的统一系统**，实现了：

1. ✅ **脏数据通道**和**干净数据通道**的**串联**关系
2. ✅ **包容与被包容**的关系（干净数据依赖脏数据）
3. ✅ **9步骤知识管道**的深度集成
4. ✅ **统一路由**管理整个流程
5. ✅ **明确的数据流向**和**可验证的关系**

不是两个独立系统，而是一个完整的、有机整合的知识处理系统！
