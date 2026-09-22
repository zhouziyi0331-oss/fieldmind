# FieldMind 系统全面深度分析与重新整合架构设计

## 📊 系统规模（真实数据）

### 数据库层
- **总表数**: 113 张表
- **总服务文件**: 256 个 Python 文件
- **服务模块**: 13 个主要模块

### 核心模块清单

| 模块 | 路径 | 功能 | 表数量 |
|------|------|------|--------|
| 知识流水线 | `services/knowledge_pipeline/` | 九步知识构建 | ~10 |
| 分析服务 | `services/analysis/` | 数据分析 | ~8 |
| NLP 服务 | `services/nlp/` | 自然语言处理 | ~5 |
| 知识图谱 | `services/kg/` | 知识图谱构建 | ~6 |
| 量化服务 | `services/quantification/` | 文本量化 | ~4 |
| 技能系统 | `services/skills/` | AI 技能管理 | ~7 |
| 工作流 | `services/workflow/` | 工作流引擎 | ~5 |
| Agent | `services/agents/` | AI Agent | ~8 |
| 记忆系统 | `services/memory/` | 长期记忆 | ~6 |
| 爬虫 | `services/crawler/` | 网页爬虫 | ~3 |
| 插件 | `services/plugins/` | 插件系统 | ~2 |
| 缩影系统 | **新增** | 知识缩影 | 1 |

---

## 🔍 深度扫描：所有数据表分类

### 核心文档处理表（15张）
```
project_documents          # 文档主表
document_chunks            # 文本分块
document_metadata          # 文档元数据
document_tags              # 文档标签
document_citations         # 文档引用
document_entities          # 文档实体关联
project_document_assets    # 文档资产
project_document_tags      # 项目文档标签
documents                  # 旧文档表（可能重复）
source_files               # 源文件
embeddings                 # 向量嵌入
chunks_fts_simple*         # FTS5 搜索索引（5张辅助表）
```

### 知识构建表（15张）
```
entities                   # 实体表（Step 3）
entity_relations           # 实体关系（Step 5）
entity_evidences           # 实体证据
entity_statistics          # 实体统计
chunk_entities             # Chunk-实体关联

timeline_events            # 时间线事件（Step 4）
metrics_events             # 指标事件

object_relations           # 对象关系
fieldmind_objects          # FieldMind 对象

fact_statements            # 事实陈述
statement_sources          # 陈述来源
analysis_statements        # 分析陈述

contexts                   # 上下文
project_contexts           # 项目上下文
```

### 分析与洞察表（12张）
```
analysis_results           # 分析结果
analysis_reports           # 分析报告
quality_reports            # 质量报告
user_analysis_dimensions   # 用户分析维度

structured_insights        # 结构化洞察
learning_insights          # 学习洞察
feedback_analyses          # 反馈分析

pattern_library            # 模式库
pattern_clusters           # 模式聚类
pattern_matches            # 模式匹配

topic_statistics           # 主题统计
user_thinking_patterns     # 用户思维模式
```

### AI 与学习系统表（18张）
```
# AI 问答
ai_questions               # AI 问题
chat_messages              # 聊天消息
chat_sessions              # 聊天会话
project_chat_messages      # 项目聊天
project_chat_sessions      # 项目聊天会话

# 技能系统
skills                     # 技能
generated_skills           # 生成的技能
skill_validations          # 技能验证
skill_validation_feedback  # 技能验证反馈
skill_test_results         # 技能测试结果
skill_optimizations        # 技能优化

# 学习系统
background_learning_tasks  # 后台学习任务
learning_logs              # 学习日志
learning_checkpoints       # 学习检查点
learning_schedules         # 学习计划
feedback_loops             # 反馈循环
improvement_tasks          # 改进任务
```

### 工作流与任务表（11张）
```
workflow_templates         # 工作流模板
workflow_executions        # 工作流执行
workflow_steps             # 工作流步骤

scheduled_tasks            # 计划任务
scheduled_task_executions  # 任务执行记录
processing_tasks           # 处理任务
batch_operations           # 批量操作

execution_records          # 执行记录
workload_calculations      # 工作负载计算

success_patterns           # 成功模式
optimization_recommendations # 优化建议
```

### 用户与权限表（12张）
```
users                      # 用户
projects                   # 项目
project_members            # 项目成员
project_invites            # 项目邀请

roles                      # 角色
permissions                # 权限
role_permissions           # 角色权限
user_roles                 # 用户角色
resource_ownership         # 资源所有权

user_annotations           # 用户标注
user_taggings              # 用户标签
user_feeding_sessions      # 用户喂养会话
```

### 质量与监控表（10张）
```
audit_logs                 # 审计日志
project_activity_logs      # 项目活动日志

performance_metrics        # 性能指标
project_metrics            # 项目指标
metrics_snapshots          # 指标快照
loop_metrics               # 循环指标

data_lineage               # 数据血缘
data_versions              # 数据版本
lineage_query_cache        # 血缘查询缓存

source_verifications       # 来源验证
```

### 记忆与缓存表（5张）
```
conversation_memory        # 对话记忆
project_memories           # 项目记忆
citations                  # 引用
tags                       # 标签
value_exhibitions          # 价值展示
```

### 其他表（15张）
```
reports                    # 报告
industry_categories        # 行业分类

# 缩影系统（新增）
file_summaries             # 文件缩影
file_summaries_fts*        # FTS5 索引（5张辅助表）

# 系统表
alembic_version            # 数据库版本
sqlite_sequence            # SQLite 序列

# 临时表
_alembic_tmp_entity_relations
```

---

## ⚠️ 核心问题：数据孤岛严重

### 问题 1：九步流水线数据不完整

| 步骤 | 应有的表 | 实际存在的表 | 数据完整性 |
|------|---------|------------|-----------|
| Step 1: 文本校刊 | `cleaned_texts` | ❌ 可能在 chunks | 10% |
| Step 2: 结构分析 | `document_structure` | ❌ 不存在 | 0% |
| Step 3: 实体构建 | `entities` | ✅ 存在（1,132条） | 60% |
| Step 4: 事件提取 | `events` | ⚠️ `timeline_events` | 30% |
| Step 5: 关系发现 | `relationships` | ⚠️ `entity_relations` | 40% |
| Step 6: 本体构建 | `ontology_*` | ❌ 不存在 | 0% |
| Step 7: 逻辑推理 | `inference_*` | ❌ 不存在 | 0% |
| Step 8: 知识单元化 | `knowledge_units` | ❌ 不存在 | 0% |
| Step 9: 阅读器生成 | `reader_*` / `wiki_*` | ❌ 不存在 | 0% |

### 问题 2：各模块数据不互通

```
【文档上传】
    ↓
project_documents
    ↓
【内容提取】→ document_chunks
    ↓
【分块存储】→ embeddings
    ↓
【九步流水线？】
    ├→ entities (孤立)
    ├→ entity_relations (孤立)
    ├→ timeline_events (孤立)
    └→ 其他步骤？（缺失）
    
【分析系统】（独立运行）
    ├→ analysis_results
    ├→ analysis_reports
    └→ structured_insights
    
【技能系统】（独立运行）
    ├→ skills
    ├→ skill_validations
    └→ generated_skills
    
【工作流系统】（独立运行）
    ├→ workflow_templates
    └→ workflow_executions
    
【Agent 系统】（独立运行）
    └→ chat_sessions
    
【学习系统】（独立运行）
    ├→ learning_logs
    └→ feedback_loops
    
【缩影系统】（新增，孤立）
    └→ file_summaries
```

### 问题 3：没有统一的数据总线

每个模块都有自己的表，但缺少：
- ❌ 统一的事件总线（连接所有模块）
- ❌ 统一的知识图谱（汇总所有知识）
- ❌ 统一的元数据层（描述数据关系）
- ❌ 统一的查询接口（跨模块查询）

---

## 🎯 重新设计：统一整合架构

### 核心设计原则

1. **单一数据源**：所有知识最终汇总到统一的知识图谱
2. **事件驱动**：模块间通过事件总线通信
3. **分层架构**：原始数据 → 结构化知识 → 语义知识 → 应用层
4. **双向追溯**：从缩影能追溯到原始数据，从原始数据能生成缩影

### 新架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      应用层（用户界面）                          │
├─────────────────────────────────────────────────────────────────┤
│ 缩影视图 │ 知识图谱 │ 分析报告 │ 聊天对话 │ 工作流 │ 技能库    │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  统一知识中台（新增）                            │
├─────────────────────────────────────────────────────────────────┤
│ • 知识图谱统一存储（Neo4j / 图数据库）                          │
│ • 事件总线（连接所有模块）                                       │
│ • 统一查询引擎（跨模块查询）                                     │
│ • 元数据管理（描述数据关系）                                     │
│ • 缓存层（加速查询）                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  语义知识层（深度知识）                          │
├─────────────────────────────────────────────────────────────────┤
│ Step 6: 本体构建    → ontology_concepts                         │
│ Step 7: 逻辑推理    → inference_results                         │
│ Step 8: 知识单元化  → knowledge_units                           │
│ Step 9: 阅读器生成  → reader_templates / wiki_pages            │
│                                                                 │
│ 关联：                                                           │
│ • 实体消歧（entity disambiguation）                             │
│ • 关系推理（relation inference）                                │
│ • 知识补全（knowledge completion）                              │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  结构化知识层（中层知识）                        │
├─────────────────────────────────────────────────────────────────┤
│ Step 3: 实体构建    → entities (统一结构)                       │
│ Step 4: 事件提取    → events (统一结构)                         │
│ Step 5: 关系发现    → relationships (统一结构)                  │
│                                                                 │
│ 关联模块：                                                       │
│ • 分析系统 → analysis_results                                   │
│ • 模式识别 → pattern_library                                    │
│ • 主题聚类 → topic_statistics                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  原始数据层（浅层数据）                          │
├─────────────────────────────────────────────────────────────────┤
│ Step 1: 文本校刊    → document_chunks (cleaned_text 字段)       │
│ Step 2: 结构分析    → document_structure (新增)                 │
│                                                                 │
│ 基础存储：                                                       │
│ • 文档主表 → project_documents                                  │
│ • 文本分块 → document_chunks                                    │
│ • 向量嵌入 → embeddings                                         │
│ • 元数据 → document_metadata                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                  事件总线（模块间通信）                          │
├─────────────────────────────────────────────────────────────────┤
│ • document.uploaded       → 触发九步流水线                      │
│ • pipeline.step_completed → 更新知识图谱                        │
│ • knowledge.updated       → 触发缩影重新生成                    │
│ • summary.generated       → 通知分析系统                        │
│ • analysis.completed      → 触发技能学习                        │
│ • skill.learned           → 更新工作流                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 重新设计的数据模型（统一模型）

### Layer 1: 原始数据层（已有，需调整）

#### document_chunks（文本分块 - 扩展字段）
```sql
ALTER TABLE document_chunks ADD COLUMN cleaned_text TEXT;      -- Step 1
ALTER TABLE document_chunks ADD COLUMN structure_type TEXT;     -- Step 2
ALTER TABLE document_chunks ADD COLUMN structure_level INTEGER; -- Step 2
ALTER TABLE document_chunks ADD COLUMN parent_chunk_id INTEGER; -- Step 2
```

#### document_structure（新增 - Step 2）
```sql
CREATE TABLE document_structure (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    node_type TEXT,          -- 'chapter', 'section', 'paragraph'
    node_level INTEGER,      -- 层级深度
    title TEXT,
    parent_id INTEGER,       -- 父节点
    sequence_order INTEGER,  -- 顺序
    metadata JSON,
    created_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES project_documents(id),
    FOREIGN KEY (chunk_id) REFERENCES document_chunks(id),
    FOREIGN KEY (parent_id) REFERENCES document_structure(id)
);
```

### Layer 2: 结构化知识层（已有，需统一）

#### entities（实体 - Step 3 - 统一结构）
```sql
-- 重新设计 entities 表（统一所有实体类型）
CREATE TABLE entities_unified (
    id INTEGER PRIMARY KEY,
    entity_id TEXT UNIQUE NOT NULL,      -- 全局唯一 ID
    document_id INTEGER NOT NULL,
    chunk_ids JSON,                       -- 出现的所有 chunk
    
    -- 基本信息
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,            -- 'person', 'location', 'event', 'concept'
    entity_category TEXT,                 -- 细分类
    
    -- 统计信息
    mention_count INTEGER DEFAULT 0,
    first_mention_chunk_id INTEGER,
    confidence REAL,
    
    -- 属性（JSON）
    properties JSON,                      -- 灵活存储各类属性
    
    -- 来源追溯
    extraction_method TEXT,               -- 'NER', 'rule', 'manual'
    source_chunks JSON,                   -- 证据来源
    
    -- 链接
    canonical_entity_id TEXT,             -- 消歧后的标准实体
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES project_documents(id)
);
```

#### events（事件 - Step 4 - 统一结构）
```sql
CREATE TABLE events_unified (
    id INTEGER PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    document_id INTEGER NOT NULL,
    chunk_ids JSON,
    
    -- 事件信息
    event_type TEXT NOT NULL,            -- 'action', 'state_change', 'occurrence'
    event_name TEXT,
    description TEXT,
    
    -- 时间信息
    temporal_expression TEXT,            -- 原始时间表达
    normalized_time_start TEXT,          -- 规范化开始时间
    normalized_time_end TEXT,            -- 规范化结束时间
    time_confidence REAL,
    
    -- 空间信息
    spatial_expression TEXT,
    normalized_location TEXT,
    location_confidence REAL,
    
    -- 参与者（JSON）
    participants JSON,                   -- [{"entity_id": "...", "role": "agent"}]
    
    -- 因果关系
    causes JSON,                         -- 原因事件
    effects JSON,                        -- 结果事件
    
    -- 来源
    extraction_method TEXT,
    source_chunks JSON,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES project_documents(id)
);
```

#### relationships（关系 - Step 5 - 统一结构）
```sql
CREATE TABLE relationships_unified (
    id INTEGER PRIMARY KEY,
    relationship_id TEXT UNIQUE NOT NULL,
    document_id INTEGER NOT NULL,
    
    -- 关系三元组
    subject_id TEXT NOT NULL,            -- 主体实体 ID
    subject_type TEXT,                   -- 主体类型
    predicate TEXT NOT NULL,             -- 关系类型
    object_id TEXT NOT NULL,             -- 客体实体 ID
    object_type TEXT,                    -- 客体类型
    
    -- 关系属性
    properties JSON,
    confidence REAL,
    
    -- 上下文
    context_chunk_ids JSON,
    temporal_context TEXT,               -- 时间上下文
    spatial_context TEXT,                -- 空间上下文
    
    -- 来源
    extraction_method TEXT,
    source_chunks JSON,
    evidence TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES project_documents(id)
);
```

### Layer 3: 语义知识层（新增 - Step 6-9）

#### ontology_concepts（本体概念 - Step 6）
```sql
CREATE TABLE ontology_concepts (
    id INTEGER PRIMARY KEY,
    concept_id TEXT UNIQUE NOT NULL,
    project_id INTEGER,
    
    -- 概念信息
    concept_name TEXT NOT NULL,
    concept_type TEXT,                   -- 'class', 'property', 'individual'
    definition TEXT,
    
    -- 本体层次
    parent_concept_id TEXT,              -- 父概念
    hierarchy_level INTEGER,
    
    -- 属性定义
    properties JSON,                     -- 概念的属性定义
    constraints JSON,                    -- 约束条件
    
    -- 实例
    instances JSON,                      -- 该概念的实例列表
    
    -- 关系
    related_concepts JSON,               -- 相关概念
    
    -- 来源
    source_documents JSON,               -- 来源文档
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### inference_results（推理结果 - Step 7）
```sql
CREATE TABLE inference_results (
    id INTEGER PRIMARY KEY,
    inference_id TEXT UNIQUE NOT NULL,
    document_id INTEGER,
    project_id INTEGER,
    
    -- 推理信息
    inference_type TEXT NOT NULL,        -- 'deductive', 'inductive', 'abductive'
    inference_rule TEXT,
    
    -- 前提
    premises JSON,                       -- [{"type": "fact", "id": "..."}]
    
    -- 结论
    conclusion_type TEXT,                -- 'entity', 'relationship', 'event'
    conclusion_id TEXT,
    conclusion_description TEXT,
    
    -- 置信度
    confidence REAL,
    
    -- 解释
    explanation TEXT,
    reasoning_chain JSON,                -- 推理链
    
    -- 验证
    validation_status TEXT,              -- 'pending', 'confirmed', 'rejected'
    validation_feedback TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### knowledge_units（知识单元 - Step 8）
```sql
CREATE TABLE knowledge_units (
    id INTEGER PRIMARY KEY,
    unit_id TEXT UNIQUE NOT NULL,
    document_id INTEGER,
    project_id INTEGER,
    
    -- 知识单元类型
    unit_type TEXT NOT NULL,             -- 'fact', 'rule', 'pattern', 'insight'
    unit_category TEXT,
    
    -- 内容
    title TEXT,
    summary TEXT,
    full_content JSON,                   -- 完整的结构化内容
    
    -- 组成部分
    entities JSON,                       -- 涉及的实体
    events JSON,                         -- 涉及的事件
    relationships JSON,                  -- 涉及的关系
    ontology_concepts JSON,              -- 涉及的本体概念
    inferences JSON,                     -- 涉及的推理
    
    -- 向量表示
    embedding BLOB,
    
    -- 质量评分
    quality_score REAL,
    completeness_score REAL,
    
    -- 应用
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### reader_templates（阅读器模板 - Step 9）
```sql
CREATE TABLE reader_templates (
    id INTEGER PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    project_id INTEGER,
    
    -- 模板信息
    template_name TEXT NOT NULL,
    template_type TEXT,                  -- 'entity_card', 'timeline', 'network', 'wiki_page'
    
    -- 模板结构
    structure JSON,                      -- 模板的结构定义
    style JSON,                          -- 样式定义
    
    -- 数据绑定
    data_sources JSON,                   -- 数据来源配置
    query_templates JSON,                -- 查询模板
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### wiki_pages（Wiki 页面 - Step 9）
```sql
CREATE TABLE wiki_pages (
    id INTEGER PRIMARY KEY,
    page_id TEXT UNIQUE NOT NULL,
    project_id INTEGER,
    
    -- 页面信息
    page_title TEXT NOT NULL,
    page_type TEXT,                      -- 'entity', 'event', 'concept', 'topic'
    target_id TEXT,                      -- 关联的实体/事件/概念 ID
    
    -- 内容
    content_markdown TEXT,
    content_html TEXT,
    content_json JSON,                   -- 结构化内容
    
    -- 元数据
    tags JSON,
    category TEXT,
    
    -- 链接
    inbound_links JSON,                  -- 入链
    outbound_links JSON,                 -- 出链
    
    -- 版本
    version INTEGER DEFAULT 1,
    previous_version_id TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Layer 4: 统一知识中台（新增）

#### knowledge_graph_nodes（知识图谱节点）
```sql
CREATE TABLE knowledge_graph_nodes (
    id INTEGER PRIMARY KEY,
    node_id TEXT UNIQUE NOT NULL,
    node_type TEXT NOT NULL,             -- 'entity', 'event', 'concept', 'document'
    source_table TEXT,                   -- 来源表
    source_id TEXT,                      -- 来源表的 ID
    
    -- 节点信息
    label TEXT NOT NULL,
    properties JSON,
    
    -- 向量
    embedding BLOB,
    
    -- 统计
    degree INTEGER DEFAULT 0,            -- 度数
    importance_score REAL,               -- 重要性评分
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### knowledge_graph_edges（知识图谱边）
```sql
CREATE TABLE knowledge_graph_edges (
    id INTEGER PRIMARY KEY,
    edge_id TEXT UNIQUE NOT NULL,
    
    -- 边信息
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    
    -- 属性
    properties JSON,
    weight REAL DEFAULT 1.0,
    confidence REAL,
    
    -- 来源
    source_table TEXT,
    source_id TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (source_node_id) REFERENCES knowledge_graph_nodes(node_id),
    FOREIGN KEY (target_node_id) REFERENCES knowledge_graph_nodes(node_id)
);
```

#### system_events（事件总线）
```sql
CREATE TABLE system_events (
    id INTEGER PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    
    -- 事件信息
    event_type TEXT NOT NULL,            -- 'document.uploaded', 'pipeline.completed'
    event_category TEXT,                 -- 'document', 'pipeline', 'knowledge', 'analysis'
    
    -- 事件数据
    payload JSON,
    
    -- 发布者
    publisher TEXT,                      -- 发布模块
    
    -- 订阅者
    subscribers JSON,                    -- 订阅该事件的模块
    
    -- 状态
    status TEXT,                         -- 'published', 'consumed'
    consumed_by JSON,                    -- 已消费的模块列表
    
    created_at TIMESTAMP
);
```

#### unified_metadata（统一元数据）
```sql
CREATE TABLE unified_metadata (
    id INTEGER PRIMARY KEY,
    metadata_id TEXT UNIQUE NOT NULL,
    
    -- 目标对象
    target_type TEXT NOT NULL,           -- 'document', 'entity', 'event', 'summary'
    target_id TEXT NOT NULL,
    
    -- 元数据
    metadata_key TEXT NOT NULL,
    metadata_value TEXT,
    metadata_type TEXT,                  -- 'string', 'number', 'json', 'reference'
    
    -- 来源
    source_module TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Layer 5: 缩影系统（已有，需整合）

#### file_summaries（文件缩影 - 整合所有层数据）
```sql
-- 保留现有结构，增加字段
ALTER TABLE file_summaries ADD COLUMN knowledge_graph_node_id TEXT;
ALTER TABLE file_summaries ADD COLUMN knowledge_units JSON;
ALTER TABLE file_summaries ADD COLUMN wiki_page_id TEXT;
ALTER TABLE file_summaries ADD COLUMN ontology_tags JSON;
ALTER TABLE file_summaries ADD COLUMN inference_count INTEGER DEFAULT 0;
```

---

## 🔄 完整数据流（重新设计）

### 流程 1：文档上传到知识构建（端到端）

```
1. 用户上传文档
   ↓
2. 保存到 project_documents
   ↓
3. 发布事件: document.uploaded
   ↓
4. 【九步流水线启动】
   
   Step 1: 文本校刊
   ├→ 清洗文本
   ├→ 更新 document_chunks.cleaned_text
   └→ 发布事件: pipeline.step1.completed
   
   Step 2: 结构分析
   ├→ 分析篇章结构
   ├→ 写入 document_structure
   ├→ 更新 document_chunks.structure_type
   └→ 发布事件: pipeline.step2.completed
   
   Step 3: 实体构建
   ├→ 抽取实体
   ├→ 写入 entities_unified
   ├→ 创建知识图谱节点 → knowledge_graph_nodes
   └→ 发布事件: entities.extracted
   
   Step 4: 事件提取
   ├→ 识别事件
   ├→ 写入 events_unified
   ├→ 创建知识图谱节点 → knowledge_graph_nodes
   └→ 发布事件: events.extracted
   
   Step 5: 关系发现
   ├→ 发现关系
   ├→ 写入 relationships_unified
   ├→ 创建知识图谱边 → knowledge_graph_edges
   └→ 发布事件: relationships.discovered
   
   Step 6: 本体构建
   ├→ 构建本体
   ├→ 写入 ontology_concepts
   ├→ 更新知识图谱
   └→ 发布事件: ontology.built
   
   Step 7: 逻辑推理
   ├→ 执行推理
   ├→ 写入 inference_results
   ├→ 创建推理链
   └→ 发布事件: inference.completed
   
   Step 8: 知识单元化
   ├→ 组织知识单元
   ├→ 写入 knowledge_units
   ├→ 生成向量
   └→ 发布事件: knowledge_units.created
   
   Step 9: 阅读器生成
   ├→ 应用模板 → reader_templates
   ├→ 生成 Wiki 页面 → wiki_pages
   ├→ 生成可视化
   └→ 发布事件: reader.generated
   
   ↓
5. 发布事件: pipeline.completed
   ↓
6. 【缩影系统监听事件】
   ├→ 读取所有九步数据
   ├→ 聚合生成缩影
   ├→ 写入 file_summaries
   ├→ 关联 knowledge_graph_node_id
   ├→ 关联 wiki_page_id
   └→ 发布事件: summary.generated
   ↓
7. 【其他系统响应】
   ├→ 分析系统: 更新 analysis_results
   ├→ 技能系统: 学习新模式
   ├→ 工作流系统: 触发下一步
   └→ Agent 系统: 更新知识库
```

---

## 📊 重新设计后的系统整合度

### 整合前（当前状态）
```
数据连接率: 30%
模块独立: 12 个独立模块
数据孤岛: 严重（每个模块独立存储）
查询效率: 低（需要多次跨表查询）
知识利用: 低（知识分散，难以关联）
```

### 整合后（目标状态）
```
数据连接率: 95%+
统一知识中台: 1 个知识图谱汇总所有知识
事件总线: 所有模块通过事件通信
查询效率: 高（统一查询接口）
知识利用: 高（知识图谱连接一切）
```

---

## 📋 实施计划（7天）

### Day 1: 数据模型统一
- 创建新表（document_structure, *_unified, ontology_*, inference_*, knowledge_units, reader_templates, wiki_pages）
- 创建知识图谱表（knowledge_graph_nodes, knowledge_graph_edges）
- 创建事件总线表（system_events）
- 创建元数据表（unified_metadata）

### Day 2-3: 九步流水线重构
- 重写 Step 1-2（文本校刊、结构分析）
- 重写 Step 3-5（实体、事件、关系 - 写入统一表）
- 实现 Step 6-9（本体、推理、知识单元、阅读器）
- 每步完成后发布事件

### Day 4: 知识图谱构建
- 实现知识图谱生成器
- 监听九步流水线事件
- 实时更新 knowledge_graph_nodes 和 knowledge_graph_edges
- 实现统一查询接口

### Day 5: 缩影系统重构
- 修改缩影生成器，读取所有九步数据
- 关联知识图谱节点
- 关联 Wiki 页面
- 实现事件监听机制

### Day 6: 事件总线实现
- 实现事件发布订阅机制
- 连接所有模块
- 实现异步事件处理

### Day 7: 端到端测试
- 上传测试文档
- 验证九步流水线完整执行
- 验证知识图谱生成
- 验证缩影系统整合
- 验证跨模块查询

---

## 🎯 验收标准

### 数据完整性
- [ ] 上传文档后，九步流水线所有步骤都执行
- [ ] 每步的数据都正确存储到对应表
- [ ] 知识图谱正确生成节点和边
- [ ] 缩影系统读取到所有九步数据

### 数据连接性
- [ ] 从缩影能追溯到原始文档
- [ ] 从实体能查到所有相关文档
- [ ] 从事件能查到所有参与实体
- [ ] 跨模块查询响应时间 < 500ms

### 系统整合度
- [ ] 事件总线正常工作
- [ ] 所有模块能接收和响应事件
- [ ] 知识图谱汇总所有知识
- [ ] 统一查询接口正常工作

---

这个方案是否符合你的要求？我需要立即开始实施吗？
