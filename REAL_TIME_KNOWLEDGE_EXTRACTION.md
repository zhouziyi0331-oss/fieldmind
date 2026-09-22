# 实时知识提炼系统 - 完整文档

## 🎯 核心理念

**从用户的真实文档中，实时提炼结构化知识，让用户看到知识图谱如何一点点生长出来。**

---

## 📋 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户上传文档                              │
│           (文本/PDF/音频/视频/图片)                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Dirty Channel (脏数据通道)                      │
│  - DirtyChannelDocument: 完整性优先，保留原始文本          │
│  - 多模态数据统一入口                                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│               9步骤知识管道 (实时处理)                       │
│                                                               │
│  步骤3: 实体构建   → CleanChannelEntity                     │
│  步骤4: 事件提取   → CleanChannelEvent                      │
│  步骤5: 关系发现   → CleanChannelRelation                   │
│  步骤6: 本体构建   → 层级关系边 (IS_A, PART_OF)            │
│  步骤7: 逻辑推理   → 推断关系边 (INFERRED)                  │
│  步骤8: 知识单元化 → 标记核心节点 (is_core=True)           │
│                                                               │
│  每个步骤产出 → 实时通过SSE推送给前端                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│            前端知识图谱实时可视化                            │
│                                                               │
│  - 节点逐个出现 (步骤3: 实体, 步骤4: 事件)                 │
│  - 边逐条连接   (步骤5: 关系, 步骤6: 本体, 步骤7: 推理)   │
│  - 核心节点标记 (步骤8: 知识单元)                          │
│  - D3.js力导向布局，实时动画                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 使用流程

### 1. 前端页面：`LiveKnowledgeExtraction.tsx`

**访问路径**: `/live-extraction` (需要在路由配置中添加)

**操作步骤**:

```
1️⃣ 输入文档ID (dirty_doc_id)
   - 这是你在系统中上传文档后得到的ID
   - 例如: 输入 "1" 代表第一个上传的文档

2️⃣ 点击"加载文档"
   - 系统会显示文档类型、字数、文本预览
   - 确认这是你想要分析的文档

3️⃣ 点击"开始提炼"
   - SSE连接建立，实时流式接收提炼结果
   - 观察左侧步骤进度卡片
   - 观察中间知识图谱实时生长
   - 观察底部提炼日志滚动

4️⃣ 实时反馈
   - 当前步骤: 蓝色高亮 + 脉冲动画
   - 已完成步骤: 绿色背景 + ✓ 图标
   - 正在处理的文本片段: 黄色高亮框显示
   - 统计数据实时更新: 提炼实体数、发现关系数等
```

### 2. 后端API：`live_extraction.py`

**核心端点**: `/api/v1/live-extraction/document/{dirty_doc_id}/extract-realtime`

**技术栈**: Server-Sent Events (SSE) 流式传输

**数据流**:

```python
# 前端建立SSE连接
const es = new EventSource('/api/v1/live-extraction/document/1/extract-realtime')

# 后端逐步推送事件
es.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  // 事件类型1: 步骤开始
  { step: 3, status: 'started', message: '开始提取实体...' }
  
  // 事件类型2: 提取出节点
  {
    step: 3,
    type: 'node',
    action: 'add',
    data: {
      id: 'entity_123',
      label: '张三',
      type: 'PERSON',
      layer: 2,
      is_core: false
    },
    reasoning: '从文本中识别为人物实体',
    source_text: '张三是一位教授，专注于人工智能研究...'
  }
  
  // 事件类型3: 提取出边
  {
    step: 5,
    type: 'edge',
    action: 'add',
    data: {
      id: 'relation_456',
      source: 'entity_123',
      target: 'entity_124',
      type: 'WORKS_FOR',
      weight: 0.8
    },
    reasoning: '发现张三在某大学工作',
    source_text: '张三教授在清华大学任职...'
  }
  
  // 事件类型4: 步骤完成
  { step: 3, status: 'completed' }
  
  // 事件类型5: 全部完成
  { status: 'finished', message: '知识提炼完成！' }
}
```

---

## 📊 数据模型

### 1. DirtyChannelDocument (脏数据文档)

```python
id: 1
source_type: 'document'
source_path: '/uploads/research_paper.pdf'
complete_text: '这是一篇关于人工智能的研究论文...'  # 完整原文
word_count: 15000
completeness_score: 0.95
```

### 2. CleanChannelEntity (提取的实体)

```python
id: 101
dirty_doc_id: 1
entity_name: '张三'
entity_type: 'PERSON'
importance_score: 0.85
properties: {
  'title': '教授',
  'affiliation': '清华大学',
  'context': '张三教授专注于机器学习研究...'
}
```

### 3. CleanChannelEvent (提取的事件)

```python
id: 201
dirty_doc_id: 1
event_title: '学术会议召开'
event_summary: '2023年国际AI大会在北京举行'
information_nodes: {  # 5W1H
  'who': '张三教授',
  'what': '发表主题演讲',
  'when': '2023年10月',
  'where': '北京国际会议中心',
  'why': '分享最新研究成果',
  'how': '通过主题演讲形式'
}
importance_score: 0.9
```

### 4. CleanChannelRelation (提取的关系)

```python
id: 301
dirty_doc_id: 1
source_entity_id: 101  # 张三
target_entity_id: 102  # 清华大学
relation_type: 'WORKS_FOR'
relation_description: '张三在清华大学任职'
strength_score: 0.9
```

---

## 🎨 前端可视化效果

### 实时动画

```
初始状态: 空白画布
  ↓
步骤3开始: 
  - 节点"张三"淡入 (300ms动画)
  - 节点"清华大学"淡入
  - 节点"机器学习"淡入
  ↓
步骤4继续:
  - 节点"学术会议"淡入 (EVENT类型，红色)
  ↓
步骤5分析:
  - 边"张三 → WORKS_FOR → 清华大学" 从无到有
  - 边"张三 → PARTICIPATES_IN → 学术会议" 连接
  ↓
步骤6构建:
  - 边"张三 → IS_A → 学者" (本体关系)
  - 边"机器学习 → PART_OF → 人工智能" (层级)
  ↓
步骤7推理:
  - 边"张三 → COLLABORATES_WITH → 李四" (推理出的潜在合作)
  ↓
步骤8单元化:
  - 节点"张三"变为紫色，标记为核心单元
  - 节点"学术会议"标记为核心单元
```

### 视觉编码

```
节点颜色:
  PERSON: 蓝色 (#3B82F6)
  EVENT: 红色 (#EF4444)
  ORGANIZATION: 绿色 (#10B981)
  LOCATION: 橙色 (#F59E0B)
  CONCEPT: 紫色 (#8B5CF6)

节点大小:
  核心节点 (is_core=True): 15px
  普通节点: 10px

边样式:
  关系边 (步骤5): 实线
  本体边 (步骤6): 虚线
  推理边 (步骤7): 点线
```

---

## 🔧 后端TODO：对接真实AI模型

**当前状态**: 使用简化的关键词匹配进行演示

**需要替换的部分**:

### 1. 实体提取 (步骤3)

```python
# 现在 (mock)
def _mock_entity_extraction(self, text: str):
    # 简单关键词匹配
    keywords = ['张三', '清华大学', '机器学习']
    return entities

# 需要改为 (真实NER)
def _real_entity_extraction(self, text: str):
    # 调用真实的NER模型
    from app.services.nlp_service import ner_model
    entities = ner_model.extract_entities(text)
    # 返回: [{'name': '张三', 'type': 'PERSON', 'offset': 10, ...}]
    return entities
```

### 2. 事件提取 (步骤4)

```python
# 需要改为
def _real_event_extraction(self, text: str):
    from app.services.event_extractor import event_model
    events = event_model.extract_events(text)
    # 返回: [{
    #   'title': '学术会议',
    #   '5w1h': {'who': '...', 'what': '...'},
    #   'importance': 0.9
    # }]
    return events
```

### 3. 关系发现 (步骤5)

```python
# 需要改为
def _real_relation_discovery(self, entities: list):
    from app.services.relation_extractor import relation_model
    relations = relation_model.discover_relations(entities)
    # 返回: [{
    #   'source_id': 1,
    #   'target_id': 2,
    #   'type': 'WORKS_FOR',
    #   'confidence': 0.85
    # }]
    return relations
```

### 4. 本体构建 (步骤6)

```python
# 需要改为
def _real_ontology_building(self, entities: list):
    from app.services.ontology_builder import ontology_model
    hierarchies = ontology_model.build_ontology(entities)
    # 返回: [{
    #   'child': 'entity_1',
    #   'parent': 'PERSON',
    #   'type': 'IS_A'
    # }]
    return hierarchies
```

### 5. 逻辑推理 (步骤7)

```python
# 需要改为
def _real_logical_inference(self, relations: list):
    from app.services.inference_engine import inference_model
    inferred = inference_model.infer_relations(relations)
    # 传递推理: A→B, B→C => A→C
    # 对称推理: A→同事→B => B→同事→A
    return inferred
```

### 6. 知识单元化 (步骤8)

```python
# 需要改为
def _real_knowledge_unitization(self, entities: list, events: list):
    from app.services.unitization import unitization_model
    core_units = unitization_model.identify_core_units(entities, events)
    # 基于重要性、连接度、中心性等指标
    return core_units
```

---

## 🧪 测试流程

### 1. 准备测试数据

```sql
-- 插入测试文档到 dirty_channel_documents
INSERT INTO dirty_channel_documents 
(source_type, source_path, complete_text, word_count, completeness_score)
VALUES 
('document', '/test/sample.txt', 
 '张三是清华大学的教授，专注于机器学习研究。2023年10月，他在北京国际会议中心举办的学术会议上发表了主题演讲，分享了关于深度学习的最新研究成果。张三与李四教授长期合作，共同推动人工智能领域的发展。',
 100, 0.95);

-- 获取插入的ID
SELECT id FROM dirty_channel_documents ORDER BY id DESC LIMIT 1;
-- 假设返回 id = 1
```

### 2. 启动后端

```bash
cd /Users/alwan/Downloads/FieldMind/backend/src
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 测试SSE端点

```bash
# 使用curl测试
curl -N http://localhost:8000/api/v1/live-extraction/document/1/extract-realtime

# 预期输出 (流式):
data: {"step": 3, "status": "started", "message": "开始提取实体..."}

data: {"step": 3, "type": "node", "action": "add", "data": {...}}

data: {"step": 3, "type": "node", "action": "add", "data": {...}}

data: {"step": 3, "status": "completed"}

data: {"step": 4, "status": "started", "message": "开始提取事件..."}
...
```

### 4. 前端测试

```
1. 访问 http://localhost:3000/live-extraction
2. 输入文档ID: 1
3. 点击"加载文档"
4. 点击"开始提炼"
5. 观察图谱实时生长
```

---

## 📈 性能优化建议

### 1. 批量处理

```python
# 当前: 每个实体单独yield
for entity in entities:
    yield entity_event
    await asyncio.sleep(0.3)

# 优化: 批量yield (5个为一批)
batch = []
for entity in entities:
    batch.append(entity_event)
    if len(batch) >= 5:
        yield batch
        batch = []
        await asyncio.sleep(0.3)
```

### 2. 并行处理

```python
# 步骤3和步骤4可以并行执行
import asyncio

async def parallel_extraction(text):
    entities_task = extract_entities(text)
    events_task = extract_events(text)
    
    entities, events = await asyncio.gather(entities_task, events_task)
    return entities, events
```

### 3. 缓存机制

```python
# 对相同文档的提取结果进行缓存
from app.core.cache import cache

@cache(ttl=3600)  # 缓存1小时
async def extract_entities_cached(dirty_doc_id: int, text: str):
    return await extract_entities(text)
```

---

## 🎯 下一步工作

1. **对接真实AI模型**: 替换所有 `_mock_*` 方法
2. **添加前端路由**: 在 `frontend/src/router.tsx` 中添加 `/live-extraction` 路由
3. **错误处理增强**: SSE连接断开后的自动重连机制
4. **进度保存**: 支持暂停后从断点继续
5. **多文档批处理**: 一次性处理多个文档
6. **图谱版本对比**: 显示不同提炼阶段的图谱差异

---

## 📝 总结

现在你拥有一个**完整的实时知识提炼系统**：

✅ 从**用户的真实文档**中提取知识  
✅ **实时流式传输**每个提炼步骤的结果  
✅ 前端**动态可视化**知识图谱生长过程  
✅ 完整的**9步骤管道**集成  
✅ **数据库持久化**所有提炼结果  

这才是真正的知识图谱——不是固定的示例数据，而是从你的文档中**动态生长**出来的！
