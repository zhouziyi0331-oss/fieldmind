# KnowledgeAgent - 知识构建专员

## 概述

KnowledgeAgent 是 FieldMind 系统的第二个 Agent，负责从 TranscriptAgent 的输出中提取实体、关系，构建知识图谱，并支持跨文档实时合并。

## 职责定位

✅ **做什么：**
- 从文本中提取实体（人物、地名、机构、时间、文化概念）
- 提取实体间关系（亲缘、师徒、行为、空间、时间）
- 共现分析（句子级窗口）
- 跨文档实时合并（同名/同义实体）
- 构建知识图谱（NetworkX）
- 输出多种格式（D3.js 力导向图、思维导图）

❌ **不做什么：**
- 不进行分析、解释、推理（只构建结构）
- 不生成报告或总结

## 工作流程

```
TranscriptAgent 输出
    ↓
KnowledgeAgent 处理
    ├─ Step 1: 加载已有知识图谱（跨文档合并）
    ├─ Step 2: 实体提取
    │   ├─ 复用 TranscriptAgent 的核心人物
    │   ├─ DynamicDiscoveryEngine 补充通用实体
    │   ├─ 规则匹配：细粒度地名（村史馆、祠堂、古树、菜地等）
    │   └─ 规则匹配：文化概念（山歌、蜡染、刺绣、祭祀等）
    ├─ Step 3: 关系提取
    │   ├─ 基于共现推断（同一句话中的实体可能有关系）
    │   ├─ 规则模板匹配（亲缘、师徒、空间、参与等）
    │   └─ [TODO] LLM 辅助提取复杂关系
    ├─ Step 4: 共现分析
    │   └─ 句子级窗口，统计共现频次
    ├─ Step 5: 实时合并到知识图谱
    │   ├─ 实体合并：同名实体累加提及次数
    │   ├─ 关系去重
    │   └─ 共现累加
    └─ Step 6: 构建图结构 + 多格式输出
        ├─ NetworkX 图结构
        ├─ D3.js 力导向图数据
        └─ 思维导图数据
```

## 实体类型

| 类型 | 说明 | 示例 |
|------|------|------|
| **人物** | 访谈对象、提及的人 | 鐘百拜、村长、老师 |
| **地名-行政** | 县、市、村、寨 | 贵阳市、掉烟村 |
| **地名-地标** | 具体位置点 | 村史馆、档案馆、菜地、大树、井 |
| **机构** | 组织、单位 | 民族博物馆、学校 |
| **时间** | 时间点、时间段 | 2024年、今天、3天前、昨天 |
| **文化概念-传统** | 传统文化事项 | 山歌、蜡染、刺绣、舞蹈、手工艺 |
| **文化概念-仪式** | 仪式活动 | 祭祀、婚礼、节日、祭祖 |

## 关系类型

| 关系类型 | 说明 | 示例 |
|----------|------|------|
| **亲缘关系** | 家庭关系 | 张三是李四的父亲 |
| **师徒关系** | 教学传承 | 鐘百拜教学生舞蹈 |
| **教授** | 知识传递 | A教B手工艺 |
| **参与** | 参加活动/事件 | 村民参与祭祀 |
| **位于** | 空间关系 | 某事在某地发生 |
| **关联** | 通用关联 | A和B有联系 |

## 输出格式

### 1. 完整知识图谱 JSON

```json
{
  "实体列表": [
    {
      "实体ID": "entity_0001",
      "实体名称": "思維斯",
      "实体类型": "人物",
      "提及次数": 23,
      "出现文档": ["doc_999"],
      "上下文片段": ["...", "..."],
      "关联实体": [],
      "首次出现时间戳": 0.0
    }
  ],
  "关系列表": [
    {
      "关系ID": "rel_0001",
      "主体": "舞蹈",
      "关系类型": "位于",
      "客体": "祭祀",
      "上下文": "...",
      "时间戳": 0.0,
      "来源文档": "doc_999",
      "置信度": 0.8
    }
  ],
  "共现分析": [
    {
      "共现实体组": ["祭祀", "舞蹈", "雪山"],
      "共现频次": 1,
      "窗口类型": "句子级",
      "关联话题": ""
    }
  ],
  "知识图谱统计": {
    "节点总数": 5,
    "边总数": 3,
    "核心节点": ["思維斯", "舞蹈", "邓小平", "雪山", "祭祀"],
    "社区聚类": []
  },
  "可视化数据": {
    "d3_graph": {...},
    "mindmap": {...}
  }
}
```

### 2. D3.js 力导向图格式

```json
{
  "nodes": [
    {
      "id": "思維斯",
      "type": "人物",
      "mentions": 23,
      "group": 1
    }
  ],
  "links": [
    {
      "source": "舞蹈",
      "target": "祭祀",
      "type": "位于",
      "weight": 0.8
    }
  ]
}
```

**节点分组（group）：**
- 1 = 人物
- 2 = 地名-行政
- 3 = 地名-地标
- 4 = 文化概念-传统
- 5 = 文化概念-仪式
- 6 = 机构
- 7 = 通用实体

### 3. 思维导图格式（simple-mind-map）

```json
{
  "root": {
    "data": {
      "text": "思維斯",
      "type": "人物"
    },
    "children": [
      {
        "data": {"text": "教授"},
        "children": [
          {"data": {"text": "舞蹈"}}
        ]
      }
    ]
  }
}
```

## 跨文档合并逻辑

### 实时合并策略

每处理一个新文档时：

```python
# 1. 实体合并
if 实体名称相同:
    累加提及次数
    合并出现文档列表
    扩展上下文片段（保留前10个）
else:
    添加新实体

# 2. 关系去重
直接追加新关系（后续可优化去重逻辑）

# 3. 共现累加
直接追加新共现（后续可优化合并逻辑）
```

### 未来优化方向

- **向量相似度合并**：使用 sentence-transformers 判断同义实体
- **关系去重**：合并相同的（主体、关系类型、客体）三元组
- **共现合并**：累加跨文档的共现频次

## 测试结果

### 测试数据
- **文档**：doc_999（19628字符，2647个片段）
- **已有人物**：思維斯(23次)、邓小平(4次)、雪山(3次)

### 提取结果

**实体列表（5个）：**
- 人物：思維斯(23次)、邓小平(4次)、雪山(3次)
- 文化概念-传统：舞蹈(9次)
- 文化概念-仪式：祭祀(1次)

**关系列表（3个）：**
- 舞蹈 --[位于]--> 祭祀
- 舞蹈 --[位于]--> 雪山
- 祭祀 --[位于]--> 雪山

**共现分析（1组）：**
- 祭祀 + 舞蹈 + 雪山：共现1次

**知识图谱：**
- 节点：5个
- 边：3条
- 核心节点：思維斯、舞蹈、邓小平、雪山、祭祀

**可视化数据：**
- D3.js 力导向图：5个节点、3条边 ✅
- 思维导图：根节点"思維斯"，0个分支（因为思維斯未参与关系）

## 使用方法

### 1. 导入 Agent

```python
from app.services.agents.knowledge_agent import KnowledgeAgent

agent = KnowledgeAgent()
```

### 2. 准备输入数据

```python
task_input = {
    "doc_id": "doc_999",
    "text": "清洗后的文本",
    "segments": [...],  # 时间戳信息
    "existing_entities": [
        {"name": "鐘百拜", "mentions": 30, "contexts": [...]}
    ],
    "enable_llm": False  # 是否启用LLM辅助
}
```

### 3. 执行知识构建

```python
result = await agent.execute(task_input)

# 输出结果
entities = result["实体列表"]
relations = result["关系列表"]
d3_data = result["可视化数据"]["d3_graph"]
```

### 4. 保存到文件

```python
import json
from pathlib import Path

output_dir = Path("uploads/knowledge")
output_dir.mkdir(parents=True, exist_ok=True)

# 保存 D3.js 数据
with open(output_dir / f"{doc_id}_d3_graph.json", 'w', encoding='utf-8') as f:
    json.dump(d3_data, f, ensure_ascii=False, indent=2)
```

## 技术栈

| 功能 | 工具 | 版本 |
|------|------|------|
| NER（中文） | DynamicDiscoveryEngine | 自研 |
| 句法分析 | jieba | - |
| 向量相似度 | sentence-transformers | all-MiniLM-L6-v2 |
| 知识图谱 | NetworkX | 3.6.1 |
| 前端可视化 | D3.js | 7.9.0 |
| 思维导图 | simple-mind-map | 0.14.0-fix.3 |

## 待实现功能

### 高优先级
1. **LLM 辅助关系提取**
   - 使用 GPT/Claude 提取复杂关系
   - 识别隐含关系（如"师徒关系"从"跟...学"推断）

2. **数据库持久化**
   - 设计 knowledge_graph 表
   - 设计 entity_relations 表
   - 实现增量更新逻辑

3. **时间戳精确提取**
   - 从 segments 中匹配实体出现的精确时间
   - 用于时间线可视化

### 中优先级
4. **向量相似度实体消歧**
   - 识别同义实体（如"鐘老师" = "鐘百拜"）
   - 识别指代消解（如"他" → "鐘百拜"）

5. **关系置信度优化**
   - 基于上下文质量评分
   - 基于实体重要性评分

6. **社区检测算法优化**
   - Louvain 算法
   - 用 LLM 为每个社区生成主题名称

### 低优先级
7. **Neo4j 集成**
   - 导出 Cypher 脚本
   - 支持复杂图查询

8. **增量更新优化**
   - 智能检测变更
   - 只更新受影响的子图

## 文件结构

```
backend/
├── src/app/services/agents/
│   └── knowledge_agent.py          # KnowledgeAgent 实现
├── test_knowledge_agent.py         # 测试脚本
└── uploads/knowledge/              # 输出目录
    ├── doc_999_knowledge_graph.json   # 完整知识图谱
    ├── doc_999_d3_graph.json          # D3.js 数据
    └── doc_999_mindmap.json           # 思维导图数据
```

## 运行测试

```bash
cd /Users/alwan/FieldMind/backend
python3 test_knowledge_agent.py
```

## 测试覆盖

- ✅ 实体提取（复用 + 规则匹配 + DynamicDiscovery）
- ✅ 关系提取（基于共现推断 + 规则模板）
- ✅ 共现分析（句子级窗口）
- ✅ 知识图谱构建（NetworkX）
- ✅ 多格式输出（D3.js + 思维导图）
- ✅ 跨文档合并机制（框架已就绪）

## 常见问题

### Q1: 为什么关系数量很少？
A: 当前只使用规则模板匹配，准确率高但召回率低。未来会加入 LLM 辅助提取，大幅提升关系数量。

### Q2: 如何提高实体识别准确率？
A: 
1. 扩展地标词典（LANDMARK_KEYWORDS）
2. 扩展文化概念词典（CULTURE_TRADITIONAL、CULTURE_RITUAL）
3. 启用 DynamicDiscoveryEngine 的 NER 功能

### Q3: D3.js 数据如何在前端使用？
A: 参考 D3.js force-directed graph 示例：
```javascript
const data = await fetch('/api/knowledge/doc_999/d3').then(r => r.json());
const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d => d.id))
  .force("charge", d3.forceManyBody())
  .force("center", d3.forceCenter(width / 2, height / 2));
```

### Q4: 跨文档合并什么时候触发？
A: 每次调用 `execute()` 时，会先调用 `_load_existing_knowledge_graph()`加载已有知识图谱，然后实时合并新文档的数据。这是**实时合并**策略。

## 更新日志

### 2026-08-13
- ✅ 创建 KnowledgeAgent 基础结构
- ✅ 实现实体提取（复用 + 规则 + DynamicDiscovery）
- ✅ 实现关系提取（基于共现推断 + 规则模板）
- ✅ 实现共现分析（句子级窗口）
- ✅ 实现知识图谱构建（NetworkX）
- ✅ 实现多格式输出（D3.js + 思维导图）
- ✅ 修复 D3.js 数据生成问题（`if not self.graph` → `if self.graph is None`）
- ✅ 优化关系提取逻辑（只保留两端都是实体的高质量关系）
- ✅ 完成测试脚本并验证通过
