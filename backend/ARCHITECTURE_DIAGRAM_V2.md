# FieldMind 6-Agent v2 架构图

## 整体架构

```
┌────────────────────────────────────────────────────────────────────────┐
│                          FieldMind Backend                              │
│                         6-Agent v2 架构                                 │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                           输入层 (Input)                                │
├────────────────────────────────────────────────────────────────────────┤
│  音频/视频文件  │  文档 (PDF/DOCX)  │  纯文本  │  API请求             │
└────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌────────────────────────────────────────────────────────────────────────┐
│                        Agent Pipeline (流水线)                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐         ┌──────────────────┐                   │
│  │ IngestionAgent   │   →     │ ChunkingAgent    │                   │
│  │ 数据摄取         │         │ 文档分块         │                   │
│  └────────┬─────────┘         └────────┬─────────┘                   │
│           │                             │                              │
│           └──────── [transcript] ───────┴──── [chunking] ─────┐      │
│                                                                 │      │
│                    ┌──────────────────┐                        │      │
│                    │VectorizationAgent│  ←─────────────────────┘      │
│                    │向量化            │                               │
│                    └────────┬─────────┘                               │
│                             │                                          │
│                     [embedding]                                        │
│                             │                                          │
│  ┌──────────────────┐      │       ┌──────────────────┐             │
│  │ KnowledgeAgent   │  ←───┴────→  │ SynthesisAgent   │             │
│  │ 知识构建         │              │ 综合分析         │             │
│  └────────┬─────────┘              └────────┬─────────┘             │
│           │                                  │                        │
│           └──────── [entity/relation] ───────┴──── [synthesis] ───┐  │
│                                                                     │  │
│                    ┌──────────────────┐                            │  │
│                    │  ReportAgent     │  ←─────────────────────────┘  │
│                    │  报告生成        │                               │
│                    └────────┬─────────┘                               │
│                             │                                          │
│                         [skills]                                       │
└─────────────────────────────┼──────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────┐
│                         工具函数层 (Tools)                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ transcript/     │  │ entity/         │  │ relation/       │      │
│  │                 │  │                 │  │                 │      │
│  │ transcribe_     │  │ extract_        │  │ extract_        │      │
│  │ audio()         │  │ entities()      │  │ relations()     │      │
│  │                 │  │                 │  │                 │      │
│  │ clean_          │  │                 │  │                 │      │
│  │ transcript()    │  │                 │  │                 │      │
│  │                 │  │                 │  │                 │      │
│  │ extract_        │  │                 │  │                 │      │
│  │ metrics()       │  │                 │  │                 │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│                                                                         │
│  ┌─────────────────┐                                                   │
│  │ summary/        │                                                   │
│  │                 │                                                   │
│  │ analyze_with_   │                                                   │
│  │ skills()        │                                                   │
│  │                 │                                                   │
│  │ [6大Skills]     │                                                   │
│  └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────┬──────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────┐
│                         服务层 (Services)                               │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WhisperService  │  LACService  │  VectorService  │  SkillRegistry    │
│  (音频转录)      │  (NER)       │  (向量搜索)     │  (Skills管理)     │
│                                                                         │
└─────────────────────────────┬──────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────┐
│                        数据层 (Data Layer)                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ PostgreSQL      │  │ Qdrant          │  │ Redis           │      │
│  │ (结构化数据)    │  │ (向量数据库)    │  │ (缓存)          │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────────┐
│                          输出层 (Output)                                │
├────────────────────────────────────────────────────────────────────────┤
│  JSON API  │  知识图谱  │  分析报告  │  导出文件 (PDF/DOCX)           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 数据流详解

### 1. 音频/视频处理流程

```
音频文件 (audio.mp3)
    ↓
[IngestionAgent]
    ├─→ transcribe_audio() ──→ Whisper API
    │       ↓
    │   转录文本 + 时间轴
    │       ↓
    └─→ clean_transcript() ──→ 清洗文本
            ↓
        标准化文本
            ↓
[ChunkingAgent]
    └─→ 智能分块 (语义边界)
            ↓
        DocumentChunk[]
            ↓
[VectorizationAgent]
    └─→ 生成向量 → Qdrant
            ↓
[KnowledgeAgent]
    ├─→ extract_entities() ──→ LACService
    │       ↓
    │   实体列表
    │       ↓
    └─→ extract_relations() ──→ 关系抽取
            ↓
        知识图谱
            ↓
[SynthesisAgent]
    └─→ 主题聚类 + 趋势分析
            ↓
[ReportAgent]
    └─→ analyze_with_skills() ──→ 6大Skills
            ↓
        最终报告
```

### 2. 文档处理流程

```
PDF/DOCX文件
    ↓
[IngestionAgent]
    └─→ 提取纯文本
            ↓
        文本内容
            ↓
[ChunkingAgent]
    └─→ 按章节/段落分块
            ↓
[VectorizationAgent → KnowledgeAgent → SynthesisAgent → ReportAgent]
        (与音频流程相同)
```

### 3. 知识图谱构建流程

```
文本内容
    ↓
[KnowledgeAgent]
    │
    ├─→ extract_entities(text)
    │       ↓
    │   原始实体列表
    │       ↓
    │   实体合并 (相似度 > 0.85)
    │       ↓
    │   去重后实体列表
    │
    ├─→ extract_relations(text, entities)
    │       ↓
    │   三元组 (head, relation, tail)
    │       ↓
    │   关系验证 + 置信度评分
    │       ↓
    │   高置信关系列表
    │
    └─→ 构建NetworkX图
            ↓
        知识图谱
            ├─→ nodes (实体)
            ├─→ edges (关系)
            └─→ communities (社区检测)
```

---

## 组件职责矩阵

| 组件 | 输入 | 输出 | 使用工具 | 数据库操作 |
|------|------|------|----------|-----------|
| **IngestionAgent** | 文件路径 | 标准化文本 | `transcribe_audio()` | INSERT Document |
| **ChunkingAgent** | 文本 | 文本块列表 | - | INSERT DocumentChunk |
| **VectorizationAgent** | 文本块ID | 向量 | - | INSERT到Qdrant |
| **KnowledgeAgent** | 文档ID | 知识图谱 | `extract_entities()`<br>`extract_relations()` | INSERT Entity/Relation |
| **SynthesisAgent** | 项目ID | 综合分析 | - | SELECT跨文档数据 |
| **ReportAgent** | 项目ID | 最终报告 | `analyze_with_skills()` | SELECT所有数据 |

---

## 工具函数依赖图

```
transcribe_audio()
    ├─→ WhisperService (音频→文字)
    ├─→ cultural_classifier (文化分类)
    └─→ pydub (音频处理)

extract_entities()
    ├─→ LACService (NER)
    ├─→ SentenceTransformer (相似度)
    └─→ jieba (分词)

extract_relations()
    ├─→ RELATION_PATTERNS (正则规则)
    ├─→ spaCy (句法分析)
    └─→ extract_entities() (实体输入)

analyze_with_skills()
    ├─→ SkillRegistry (Skills管理)
    └─→ 6大Skills
            ├─→ heritage_dadi
            ├─→ business_feasibility
            ├─→ multi_village_sop
            ├─→ literature_market_research
            ├─→ xiangtu_china
            └─→ sacred_memory
```

---

## 数据库Schema

### PostgreSQL表结构

```sql
-- 项目表
Project
    ├─ id: int
    ├─ name: varchar
    ├─ created_at: timestamp
    └─ metadata: jsonb

-- 文档表
Document
    ├─ id: int
    ├─ project_id: int (FK)
    ├─ file_path: varchar
    ├─ content_text: text
    ├─ metadata: jsonb
    └─ created_at: timestamp

-- 文档块表
DocumentChunk
    ├─ id: int
    ├─ document_id: int (FK)
    ├─ text: text
    ├─ start_pos: int
    ├─ end_pos: int
    ├─ chunk_index: int
    └─ metadata: jsonb

-- 实体表
Entity
    ├─ id: int
    ├─ text: varchar
    ├─ type: varchar (PER/ORG/LOC/TIME/CONCEPT)
    ├─ document_id: int (FK)
    ├─ confidence: float
    └─ metadata: jsonb

-- 关系表
Relation
    ├─ id: int
    ├─ head_entity_id: int (FK)
    ├─ relation_type: varchar
    ├─ tail_entity_id: int (FK)
    ├─ confidence: float
    └─ evidence: text
```

### Qdrant向量索引

```
Collection: document_chunks
    ├─ vector: float[768]  (embedding维度)
    ├─ payload:
    │   ├─ chunk_id: int
    │   ├─ document_id: int
    │   ├─ text: str
    │   └─ metadata: dict
    └─ index: HNSW
```

---

## 6大Skills详解

```
analyze_with_skills(content, enabled_skills)
    ↓
┌──────────────────────────────────────────┐
│         SkillRegistry                     │
├──────────────────────────────────────────┤
│                                           │
│  1. heritage_dadi                        │
│     ├─ 识别文化遗产元素                  │
│     ├─ 评估保护价值                      │
│     └─ 生成保护建议                      │
│                                           │
│  2. business_feasibility                 │
│     ├─ 市场潜力分析                      │
│     ├─ 成本效益评估                      │
│     └─ 商业模式建议                      │
│                                           │
│  3. multi_village_sop                    │
│     ├─ 跨村落对比                        │
│     ├─ 标准化流程                        │
│     └─ 最佳实践提取                      │
│                                           │
│  4. literature_market_research           │
│     ├─ 文献综述                          │
│     ├─ 市场趋势                          │
│     └─ 引文分析                          │
│                                           │
│  5. xiangtu_china                        │
│     ├─ 社会结构分析                      │
│     ├─ 传统秩序研究                      │
│     └─ 理论框架应用                      │
│                                           │
│  6. sacred_memory                        │
│     ├─ 仪式分析                          │
│     ├─ 集体记忆提取                      │
│     └─ 象征意义解读                      │
│                                           │
└──────────────────────────────────────────┘
    ↓
skills_summary + recommendations
```

---

## 性能指标

### 处理速度 (单文件)

| 文件类型 | 大小 | Agent | 预计时间 |
|---------|------|-------|---------|
| 音频 | 10分钟 | Ingestion | ~30秒 |
| 视频 | 10分钟 | Ingestion | ~45秒 |
| PDF | 50页 | Ingestion | ~10秒 |
| 文本 | 10000字 | Chunking | <1秒 |
| 文本块 | 100个 | Vectorization | ~5秒 |
| 文档 | 1个 | Knowledge | ~3秒 |
| 项目 | 10文档 | Synthesis | ~10秒 |
| 项目 | 10文档 | Report | ~15秒 |

### 资源消耗

| 组件 | CPU | 内存 | GPU | 备注 |
|------|-----|------|-----|------|
| WhisperService | 高 | 2GB | 可选 | GPU加速可提升5x |
| LACService | 中 | 500MB | - | CPU运行 |
| VectorService | 低 | 1GB | - | 批量优化 |
| Skills | 中 | 800MB | - | 并行执行 |

---

## 扩展性设计

### 水平扩展

```
                 Load Balancer
                       ↓
    ┌──────────────────┼──────────────────┐
    ↓                  ↓                  ↓
Worker 1          Worker 2          Worker 3
(Agent Pool)      (Agent Pool)      (Agent Pool)
    ↓                  ↓                  ↓
    └──────────────────┴──────────────────┘
                       ↓
              Shared Database
           (PostgreSQL + Qdrant)
```

### 插件式Skills

```python
# 添加新Skill
from app.tools.summary.skill_analyzer import SkillRegistry

class CustomSkill:
    def analyze(self, content: str) -> Dict:
        # 自定义分析逻辑
        return {'findings': [...]}

# 注册
registry = SkillRegistry()
registry.register('custom_skill', CustomSkill())
```

---

## 监控指标

### 关键指标 (KPI)

```
┌─────────────────────────────────────┐
│ Agent Pipeline监控面板              │
├─────────────────────────────────────┤
│                                      │
│ 吞吐量: 50 文档/小时                │
│ 平均延迟: 2.3秒/文档                │
│ 错误率: 0.5%                        │
│ 资源利用率: CPU 65%, 内存 4.2GB     │
│                                      │
│ Agent状态:                          │
│ ├─ Ingestion: ✅ 正常               │
│ ├─ Chunking: ✅ 正常                │
│ ├─ Vectorization: ✅ 正常           │
│ ├─ Knowledge: ⚠️ 队列堆积           │
│ ├─ Synthesis: ✅ 正常               │
│ └─ Report: ✅ 正常                  │
│                                      │
└─────────────────────────────────────┘
```

---

## 版本历史

### v2.0 (2026-08-14) - 当前版本
- ✅ 6-Agent v2流水线架构
- ✅ 工具函数层独立
- ✅ 向后兼容旧Agent

### v1.x (遗留)
- Coordinator + SuperAgent模式
- 紧耦合架构

---

## 相关文档

- [API文档](API_DOCUMENTATION_V2.md)
- [迁移指南](MIGRATION_GUIDE_PHASE4.md)
- [测试报告](PHASE5_INTEGRATION_TEST_REPORT.md)
