# FieldMind 蒸馏Skills系统

## 概述

FieldMind的蒸馏功能已从硬编码逻辑迁移到**Skills驱动架构**，遵循SBPACK 2.0和Cangjie v2.0.0方法论标准。

### 核心价值

- **可配置**: Skills可独立修改和升级，无需改动引擎核心
- **标准化**: 遵循WorkBuddy的SBPACK 2.0蒸馏协议
- **可扩展**: 新增知识单元类型只需添加新Skill
- **可测试**: 每个Skill独立测试，质量可控
- **可溯源**: 每个提取结果追溯到具体Skill和版本

---

## 架构设计

```
DistillationEngine (引擎层)
    ↓
SkillRegistry (注册表层)
    ↓
Individual Skills (执行层)
    ↓
DistilledUnit (存储层)
```

### 1. DistillationEngine
**位置**: `backend/src/app/services/distillation_engine.py`

**职责**:
- 加载项目结构化数据（chunks, entities, relations, events）
- 调用Skills注册表
- 协调6类知识单元提取
- 将提取结果保存为DistilledUnit

**关键方法**:
```python
distill_project(project_id) -> Dict[str, Any]
_extract_with_skill(project_id, skill_name, data, unit_type) -> List[DistilledUnit]
```

### 2. SkillRegistry
**位置**: `backend/src/app/skills/skill_registry.py`

**职责**:
- 注册和管理所有蒸馏Skills
- 提供Skill查找和元数据访问
- 支持动态加载Skills

**关键方法**:
```python
register_skill(name, skill_class, metadata)
get_skill(name) -> Skill
list_skills() -> List[str]
initialize_distillation_skills() -> SkillRegistry
```

---

## 6类蒸馏Skills

### 1. 洞察 (Insights)
**Skill**: `extract_insights.py`  
**方法论**: Entity + Event Density Analysis  
**输出**: 高频主题、事件密集区域、趋势识别

**提取逻辑**:
- 高频实体分析（出现≥5次）
- 事件密度分析（chunk内≥3个事件）
- 实体类型分布趋势（占比>40%）

**输出字段**:
```json
{
  "content": "洞察内容",
  "category": "高频主题|事件密度|趋势识别",
  "evidence": {"entity_name": "...", "frequency": 10},
  "credibility": 0.7-0.95,
  "confidence": 0.6-0.9,
  "source_chunks": [1, 2, 3]
}
```

---

### 2. 原话 (Quotes)
**Skill**: `extract_quotes.py`  
**方法论**: Quote Mining  
**输出**: 带说话人和情感分析的引用

**提取逻辑**:
- 识别引号模式（中英文引号、日文引号）
- 说话人识别（前50字符内查找"XXX说"）
- 情感分类（强烈正面/正面/中性/负面/强烈负面）
- 上下文提取（前后各30字符）

**输出字段**:
```json
{
  "content": "引用内容",
  "speaker": "说话人姓名",
  "emotion": "中性|正面|负面",
  "context": "...上下文...",
  "credibility": 0.9,
  "confidence": 0.85,
  "source_chunks": [5]
}
```

---

### 3. 思维模型 (Models/Knowledge Points)
**Skill**: `extract_knowledge_points.py`  
**方法论**: SBPACK 2.0 Knowledge Track  
**输出**: 独立判断的概念、主张、原理

**提取逻辑**:
- 遵循SBPACK 2.0知识轨标准
- 必须字段：statement, explanation, whyItMatters, scope, conditions, boundaries, counterexamples, evidenceRefs
- 验证规则：不含执行步骤、完整性检查、去重

**输出字段**:
```json
{
  "content": "知识点陈述",
  "structure": {
    "statement": "核心陈述",
    "explanation": "解释",
    "whyItMatters": "为什么重要",
    "scope": "适用范围",
    "conditions": "前置条件",
    "boundaries": "边界限制",
    "counterexamples": "反例",
    "evidenceRefs": ["chunk_1", "chunk_2"]
  },
  "credibility": 0.8,
  "confidence": 0.75,
  "source_chunks": [10, 11]
}
```

---

### 4. 案例 (Cases)
**Skill**: `extract_cases.py`  
**方法论**: Keyword Matching + Quality Scoring  
**输出**: 结构化案例（BAR结构）

**提取逻辑**:
- 案例标识关键词匹配
- BAR结构提取（Background, Action, Result）
- 质量评分（0-1分）
- 可复用性评估

**输出字段**:
```json
{
  "content": "案例完整描述",
  "structure": {
    "background": "背景",
    "action": "行动",
    "result": "结果"
  },
  "quality_score": 0.8,
  "reusability": "高|中|低",
  "credibility": 0.7-0.9,
  "confidence": 0.75,
  "source_chunks": [15]
}
```

---

### 5. 行动建议 (Actions)
**Skill**: `extract_actions.py`  
**方法论**: Gap + Trend Analysis  
**输出**: 可执行的行动建议

**提取逻辑**:
- 问题识别（问题关键词）
- 机会识别（机会关键词）
- 趋势分析（高频实体≥5次）
- 优先级排序（高/中/低）

**输出字段**:
```json
{
  "content": "行动建议内容",
  "category": "问题解决|机会把握|趋势应对",
  "priority": "高|中|低",
  "rationale": "建议理由",
  "credibility": 0.65-0.7,
  "confidence": 0.6-0.7,
  "source_chunks": [20, 21]
}
```

---

### 6. 方法论 (Methods/Cangjie Skills)
**Skill**: `extract_cangjie_skills.py`  
**方法论**: Cangjie v2.0.0 + RIA++  
**输出**: 可执行技能（带压力测试）

**提取逻辑**:
- RIA++结构（Rationale, Interpretation, Application-Original, Application-Future, Execution, Boundaries）
- 压力测试设计（should-trigger, should-not-trigger, boundary）
- 质量验证（V1: 触发检查, V2: 执行完整性, V3: 边界清晰度）

**输出字段**:
```json
{
  "content": "技能名称和描述",
  "structure": {
    "rationale": "为什么需要这个技能",
    "interpretation": "技能的核心逻辑",
    "application_original": "原始应用场景",
    "application_future": "未来可扩展应用",
    "execution": ["步骤1", "步骤2"],
    "boundaries": "不适用场景"
  },
  "pressure_tests": {
    "should_trigger": ["场景1", "场景2"],
    "should_not_trigger": ["场景3"],
    "boundary_cases": ["边界场景"]
  },
  "credibility": 0.8,
  "confidence": 0.75,
  "source_chunks": [25, 26]
}
```

---

## 数据流

### 输入
```python
{
  "chunks": [{"id": 1, "content": "...", "document_id": 1}],
  "entities": [{"id": 1, "entity_name": "...", "entity_type": "..."}],
  "relations": [{"source_entity_id": 1, "target_entity_id": 2}],
  "events": [{"event_type": "...", "event_date": "..."}]
}
```

### 处理
1. `DistillationEngine.distill_project(project_id)`
2. 加载结构化数据
3. 对每个知识单元类型调用对应Skill
4. Skill返回提取结果列表
5. 转换为`DistilledUnit`对象
6. 批量保存到数据库

### 输出
```python
{
  "project_id": 1,
  "total_units": 45,
  "breakdown": {
    "insights": 8,
    "quotes": 12,
    "models": 5,
    "cases": 7,
    "actions": 9,
    "methods": 4
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Skill开发规范

### 1. Skill类结构
```python
class ExtractXXXSkill:
    """Skill描述"""
    
    METADATA = {
        "name": "extract_xxx",
        "version": "1.0.0",
        "type": "extraction_type",
        "output_type": "知识单元类型"
    }
    
    def __init__(self, db_session):
        self.db = db_session
    
    def extract(self, chunks, entities, relations, events) -> List[Dict[str, Any]]:
        """提取逻辑"""
        pass
```

### 2. 输出格式要求
每个Skill返回的字典必须包含：
- `content` (str): 知识单元核心内容
- `credibility` (float): 可信度 0-1
- `confidence` (float): 置信度 0-1
- `source_chunks` (list): 来源chunk ID列表

可选字段：
- `category` (str): 分类
- `evidence` (dict): 证据数据
- `structure` (dict): 结构化数据
- 其他Skill特定字段

### 3. 注册Skill
在 `skill_registry.py` 的 `initialize_distillation_skills()` 中注册：

```python
registry.register_skill("extract_xxx", ExtractXXXSkill, {
    "type": "extraction_type",
    "output_type": "知识单元类型",
    "methodology": "方法论名称"
})
```

---

## 质量保证

### 1. 可信度评分 (Credibility)
- 基于数据来源质量
- 高频/直接引用: 0.8-0.95
- 推断/分析: 0.6-0.75

### 2. 置信度评分 (Confidence)
- 基于提取算法确定性
- 精确匹配: 0.8-0.9
- 模糊匹配: 0.6-0.75

### 3. 可溯源性
- 每个知识单元记录 `source_chunks`
- 支持追溯到原始文档位置
- API endpoint: `GET /api/distillation/units/{unit_id}/sources`

---

## 与前端集成

### API Endpoints
```
POST /api/distillation/distill/{project_id}  # 触发蒸馏
GET  /api/distillation/units                 # 获取知识单元列表
GET  /api/distillation/units/{unit_id}       # 获取单元详情
GET  /api/distillation/units/{unit_id}/sources  # 获取来源追溯
```

### 前端页面
- `/projects/:projectId/distillation` - 知识库主页
- `/projects/:projectId/distillation/:unitId` - 单元详情页

### UI组件
- `DistillationEntry.tsx` - 入口组件
- `Distillation.tsx` - 列表页面
- `DistillationDetail.tsx` - 详情页面

---

## 测试策略

### 1. 单元测试
每个Skill独立测试：
```python
def test_extract_insights_skill():
    skill = ExtractInsightsSkill(db)
    results = skill.extract(chunks, entities, relations, events)
    assert len(results) > 0
    assert all("content" in r for r in results)
```

### 2. 集成测试
测试完整蒸馏流程：
```python
def test_distillation_engine_integration():
    engine = DistillationEngine(db)
    result = engine.distill_project(project_id)
    assert result["total_units"] > 0
```

### 3. 性能测试
不同数据量下的性能：
- 100 chunks → ~3s
- 500 chunks → ~12s
- 1000 chunks → ~25s

---

## 未来扩展

### 1. LLM增强
部分Skills可选接入LLM进行质量提升：
- 思维模型提取可用LLM识别因果关系
- 行动建议可用LLM生成更精准建议

### 2. 自定义Skills
用户可上传自定义Skill脚本：
```python
# custom_skill.py
class MyCustomSkill:
    METADATA = {"name": "my_skill", ...}
    def extract(self, chunks, entities, relations, events):
        # 自定义逻辑
        pass
```

### 3. Skill版本管理
支持多版本Skill并存，回滚到历史版本

### 4. Skill市场
社区贡献和分享Skills

---

## 参考文档

1. **SBPACK 2.0协议**  
   `/Users/alwan/Downloads/直接给WorkBuddy-开始蒸馏-中文表达1.4.4-交付/01-给WorkBuddy的最终提示词.md`

2. **Cangjie v2.0.0方法论**  
   同上文档中的Skill Track部分

3. **FieldMind蒸馏完整设计**  
   `FIELDMIND_COMPLETE_DISTILLATION_SYSTEM.md`

---

## 总结

FieldMind的Skills系统将蒸馏功能从"硬编码算法"升级为"可配置标准化流程"，实现了：

✅ **标准化**: 遵循SBPACK 2.0和Cangjie v2.0.0  
✅ **可扩展**: 新增知识类型只需添加Skill  
✅ **可测试**: 每个Skill独立测试  
✅ **可溯源**: 完整的来源追溯链  
✅ **高质量**: 双评分机制（credibility + confidence）

这是FieldMind从"数据整理工具"进化为"智能知识系统"的关键一步。
