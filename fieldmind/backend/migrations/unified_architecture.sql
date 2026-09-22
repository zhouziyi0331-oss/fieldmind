-- ======================================================
-- FieldMind 统一架构数据库迁移脚本
-- 创建时间: 2024-09-14
-- 目的: 统一所有模块的数据模型，实现真正的端到端整合
-- ======================================================

-- ============================================================
-- Layer 1: 原始数据层扩展（扩展现有表）
-- ============================================================

-- 扩展 document_chunks 表（添加 Step 1-2 的字段）
ALTER TABLE document_chunks ADD COLUMN cleaned_text TEXT;              -- Step 1: 清洗后的文本
ALTER TABLE document_chunks ADD COLUMN structure_type TEXT;            -- Step 2: 结构类型
ALTER TABLE document_chunks ADD COLUMN structure_level INTEGER;        -- Step 2: 结构层级
ALTER TABLE document_chunks ADD COLUMN parent_chunk_id INTEGER;        -- Step 2: 父节点 ID

-- 创建文档结构表（Step 2: 结构分析）
CREATE TABLE IF NOT EXISTS document_structure (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,

    -- 结构信息
    node_type TEXT NOT NULL,                -- 'chapter', 'section', 'paragraph', 'list', 'table'
    node_level INTEGER NOT NULL DEFAULT 0,  -- 层级深度（0=根，1=章，2=节...）
    title TEXT,

    -- 层次关系
    parent_id INTEGER,                      -- 父节点 ID
    sequence_order INTEGER NOT NULL,        -- 同层内的顺序

    -- 内容
    content_summary TEXT,

    -- 元数据
    metadata JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_id) REFERENCES document_structure(id) ON DELETE CASCADE
);

CREATE INDEX idx_doc_structure_document ON document_structure(document_id);
CREATE INDEX idx_doc_structure_parent ON document_structure(parent_id);
CREATE INDEX idx_doc_structure_level ON document_structure(node_level);


-- ============================================================
-- Layer 2: 结构化知识层（统一表结构）
-- ============================================================

-- 统一实体表（Step 3: 实体构建）
CREATE TABLE IF NOT EXISTS entities_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT UNIQUE NOT NULL,         -- 全局唯一 ID（格式：entity_uuid）
    document_id INTEGER NOT NULL,

    -- 基本信息
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,              -- 'person', 'location', 'organization', 'event', 'concept', 'object'
    entity_category TEXT,                   -- 细分类

    -- 出现位置
    chunk_ids TEXT,                         -- JSON 数组：出现的所有 chunk ID
    first_mention_chunk_id INTEGER,

    -- 统计信息
    mention_count INTEGER DEFAULT 0,
    confidence REAL DEFAULT 1.0,

    -- 属性（JSON 格式，灵活存储）
    properties TEXT,                        -- JSON: {"age": 30, "gender": "male", ...}

    -- 描述
    description TEXT,

    -- 来源追溯
    extraction_method TEXT,                 -- 'NER', 'rule', 'pattern', 'manual', 'inference'
    source_chunks TEXT,                     -- JSON 数组：证据来源

    -- 消歧
    canonical_entity_id TEXT,               -- 消歧后的标准实体 ID
    aliases TEXT,                           -- JSON 数组：别名

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_entities_unified_document ON entities_unified(document_id);
CREATE INDEX idx_entities_unified_type ON entities_unified(entity_type);
CREATE INDEX idx_entities_unified_name ON entities_unified(entity_name);
CREATE INDEX idx_entities_unified_canonical ON entities_unified(canonical_entity_id);


-- 统一事件表（Step 4: 事件提取）
CREATE TABLE IF NOT EXISTS events_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,          -- 全局唯一 ID（格式：event_uuid）
    document_id INTEGER NOT NULL,

    -- 事件信息
    event_type TEXT NOT NULL,               -- 'action', 'state_change', 'occurrence', 'process'
    event_name TEXT,
    description TEXT,

    -- 出现位置
    chunk_ids TEXT,                         -- JSON 数组

    -- 时间信息
    temporal_expression TEXT,               -- 原始时间表达（如："2023年6月"）
    normalized_time_start TEXT,             -- 规范化开始时间（ISO 8601）
    normalized_time_end TEXT,               -- 规范化结束时间
    time_confidence REAL DEFAULT 0.5,

    -- 空间信息
    spatial_expression TEXT,                -- 原始地点表达
    normalized_location TEXT,               -- 规范化地点
    location_confidence REAL DEFAULT 0.5,

    -- 参与者（JSON 数组）
    participants TEXT,                      -- [{"entity_id": "...", "role": "agent/patient/..."}]

    -- 因果关系
    causes TEXT,                            -- JSON 数组：原因事件 ID
    effects TEXT,                           -- JSON 数组：结果事件 ID

    -- 来源
    extraction_method TEXT,
    source_chunks TEXT,                     -- JSON 数组
    confidence REAL DEFAULT 1.0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_events_unified_document ON events_unified(document_id);
CREATE INDEX idx_events_unified_type ON events_unified(event_type);
CREATE INDEX idx_events_unified_time ON events_unified(normalized_time_start);


-- 统一关系表（Step 5: 关系发现）
CREATE TABLE IF NOT EXISTS relationships_unified (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relationship_id TEXT UNIQUE NOT NULL,   -- 全局唯一 ID（格式：rel_uuid）
    document_id INTEGER NOT NULL,

    -- 关系三元组
    subject_id TEXT NOT NULL,               -- 主体实体/事件 ID
    subject_type TEXT NOT NULL,             -- 'entity' or 'event'
    predicate TEXT NOT NULL,                -- 关系类型（如：'参与', '发生于', '导致'）
    object_id TEXT NOT NULL,                -- 客体实体/事件 ID
    object_type TEXT NOT NULL,              -- 'entity' or 'event'

    -- 关系属性
    properties TEXT,                        -- JSON: 额外属性
    confidence REAL DEFAULT 1.0,

    -- 上下文
    context_chunk_ids TEXT,                 -- JSON 数组
    temporal_context TEXT,                  -- 时间上下文
    spatial_context TEXT,                   -- 空间上下文

    -- 来源
    extraction_method TEXT,                 -- 'pattern', 'dependency', 'semantic', 'manual'
    source_chunks TEXT,                     -- JSON 数组
    evidence TEXT,                          -- 证据文本

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_relationships_unified_document ON relationships_unified(document_id);
CREATE INDEX idx_relationships_unified_subject ON relationships_unified(subject_id);
CREATE INDEX idx_relationships_unified_object ON relationships_unified(object_id);
CREATE INDEX idx_relationships_unified_predicate ON relationships_unified(predicate);


-- ============================================================
-- Layer 3: 语义知识层（新增表）
-- ============================================================

-- 本体概念表（Step 6: 本体构建）
CREATE TABLE IF NOT EXISTS ontology_concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id TEXT UNIQUE NOT NULL,        -- 全局唯一 ID（格式：concept_uuid）
    project_id INTEGER,

    -- 概念信息
    concept_name TEXT NOT NULL,
    concept_type TEXT NOT NULL,             -- 'class', 'property', 'individual', 'relation'
    definition TEXT,

    -- 本体层次
    parent_concept_id TEXT,                 -- 父概念 ID（IS-A 关系）
    hierarchy_level INTEGER DEFAULT 0,

    -- 属性定义
    properties TEXT,                        -- JSON: 概念的属性定义
    constraints TEXT,                       -- JSON: 约束条件

    -- 实例
    instances TEXT,                         -- JSON 数组：该概念的实例 ID 列表
    instance_count INTEGER DEFAULT 0,

    -- 关系
    related_concepts TEXT,                  -- JSON 数组：相关概念

    -- 来源
    source_documents TEXT,                  -- JSON 数组：来源文档 ID

    -- 统计
    usage_count INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_ontology_concepts_project ON ontology_concepts(project_id);
CREATE INDEX idx_ontology_concepts_type ON ontology_concepts(concept_type);
CREATE INDEX idx_ontology_concepts_parent ON ontology_concepts(parent_concept_id);


-- 推理结果表（Step 7: 逻辑推理）
CREATE TABLE IF NOT EXISTS inference_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inference_id TEXT UNIQUE NOT NULL,      -- 全局唯一 ID（格式：inference_uuid）
    document_id INTEGER,
    project_id INTEGER,

    -- 推理信息
    inference_type TEXT NOT NULL,           -- 'deductive', 'inductive', 'abductive', 'analogical'
    inference_rule TEXT,                    -- 推理规则

    -- 前提
    premises TEXT NOT NULL,                 -- JSON 数组: [{"type": "fact/rule", "id": "...", "content": "..."}]

    -- 结论
    conclusion_type TEXT NOT NULL,          -- 'entity', 'relationship', 'event', 'fact', 'pattern'
    conclusion_id TEXT,                     -- 结论对象的 ID
    conclusion_description TEXT,

    -- 置信度
    confidence REAL DEFAULT 0.5,

    -- 解释
    explanation TEXT,
    reasoning_chain TEXT,                   -- JSON 数组：推理链

    -- 验证
    validation_status TEXT DEFAULT 'pending', -- 'pending', 'confirmed', 'rejected', 'uncertain'
    validation_feedback TEXT,
    validated_by TEXT,                      -- 验证者（用户 ID 或系统）
    validated_at TIMESTAMP,

    -- 应用
    applied_count INTEGER DEFAULT 0,
    last_applied_at TIMESTAMP,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_inference_results_document ON inference_results(document_id);
CREATE INDEX idx_inference_results_project ON inference_results(project_id);
CREATE INDEX idx_inference_results_type ON inference_results(inference_type);
CREATE INDEX idx_inference_results_status ON inference_results(validation_status);


-- 知识单元表（Step 8: 知识单元化）
CREATE TABLE IF NOT EXISTS knowledge_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id TEXT UNIQUE NOT NULL,           -- 全局唯一 ID（格式：ku_uuid）
    document_id INTEGER,
    project_id INTEGER,

    -- 知识单元类型
    unit_type TEXT NOT NULL,                -- 'fact', 'rule', 'pattern', 'insight', 'conclusion', 'hypothesis'
    unit_category TEXT,

    -- 内容
    title TEXT,
    summary TEXT NOT NULL,
    full_content TEXT,                      -- JSON: 完整的结构化内容

    -- 组成部分（JSON 数组）
    entities TEXT,                          -- 涉及的实体 ID
    events TEXT,                            -- 涉及的事件 ID
    relationships TEXT,                     -- 涉及的关系 ID
    ontology_concepts TEXT,                 -- 涉及的本体概念 ID
    inferences TEXT,                        -- 涉及的推理 ID

    -- 向量表示
    embedding BLOB,

    -- 质量评分
    quality_score REAL DEFAULT 0.5,
    completeness_score REAL DEFAULT 0.5,
    reliability_score REAL DEFAULT 0.5,

    -- 标签
    tags TEXT,                              -- JSON 数组

    -- 应用
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_knowledge_units_document ON knowledge_units(document_id);
CREATE INDEX idx_knowledge_units_project ON knowledge_units(project_id);
CREATE INDEX idx_knowledge_units_type ON knowledge_units(unit_type);
CREATE INDEX idx_knowledge_units_quality ON knowledge_units(quality_score);


-- 阅读器模板表（Step 9: 阅读器生成）
CREATE TABLE IF NOT EXISTS reader_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT UNIQUE NOT NULL,       -- 全局唯一 ID（格式：template_uuid）
    project_id INTEGER,

    -- 模板信息
    template_name TEXT NOT NULL,
    template_type TEXT NOT NULL,            -- 'entity_card', 'event_timeline', 'network_graph', 'wiki_page', 'summary_view'
    description TEXT,

    -- 模板结构
    structure TEXT NOT NULL,                -- JSON: 模板的结构定义
    style TEXT,                             -- JSON: 样式定义

    -- 数据绑定
    data_sources TEXT,                      -- JSON: 数据来源配置
    query_templates TEXT,                   -- JSON: 查询模板

    -- 版本
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,

    -- 统计
    usage_count INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_reader_templates_project ON reader_templates(project_id);
CREATE INDEX idx_reader_templates_type ON reader_templates(template_type);


-- Wiki 页面表（Step 9: Wiki 生成）
CREATE TABLE IF NOT EXISTS wiki_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id TEXT UNIQUE NOT NULL,           -- 全局唯一 ID（格式：wiki_uuid）
    project_id INTEGER NOT NULL,

    -- 页面信息
    page_title TEXT NOT NULL,
    page_type TEXT NOT NULL,                -- 'entity', 'event', 'concept', 'topic', 'index', 'summary'
    target_id TEXT,                         -- 关联的实体/事件/概念 ID

    -- 内容
    content_markdown TEXT,
    content_html TEXT,
    content_json TEXT,                      -- JSON: 结构化内容

    -- 元数据
    tags TEXT,                              -- JSON 数组
    category TEXT,

    -- 链接
    inbound_links TEXT,                     -- JSON 数组：入链页面 ID
    outbound_links TEXT,                    -- JSON 数组：出链页面 ID

    -- 版本
    version INTEGER DEFAULT 1,
    previous_version_id TEXT,

    -- 统计
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP,

    -- 状态
    status TEXT DEFAULT 'published',        -- 'draft', 'published', 'archived'

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX idx_wiki_pages_project ON wiki_pages(project_id);
CREATE INDEX idx_wiki_pages_type ON wiki_pages(page_type);
CREATE INDEX idx_wiki_pages_target ON wiki_pages(target_id);
CREATE INDEX idx_wiki_pages_status ON wiki_pages(status);


-- ============================================================
-- Layer 4: 统一知识中台（知识图谱 + 事件总线）
-- ============================================================

-- 知识图谱节点表
CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT UNIQUE NOT NULL,           -- 全局唯一 ID（格式：node_uuid）
    node_type TEXT NOT NULL,                -- 'entity', 'event', 'concept', 'document', 'knowledge_unit'

    -- 来源
    source_table TEXT NOT NULL,             -- 来源表名
    source_id TEXT NOT NULL,                -- 来源表的 ID

    -- 节点信息
    label TEXT NOT NULL,
    display_name TEXT,
    description TEXT,
    properties TEXT,                        -- JSON: 节点属性

    -- 向量
    embedding BLOB,

    -- 统计
    degree INTEGER DEFAULT 0,               -- 度数（连接数）
    in_degree INTEGER DEFAULT 0,            -- 入度
    out_degree INTEGER DEFAULT 0,           -- 出度

    -- 重要性评分
    importance_score REAL DEFAULT 0.5,
    centrality_score REAL DEFAULT 0.0,
    pagerank_score REAL DEFAULT 0.0,

    -- 标签
    tags TEXT,                              -- JSON 数组

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kg_nodes_type ON knowledge_graph_nodes(node_type);
CREATE INDEX idx_kg_nodes_source ON knowledge_graph_nodes(source_table, source_id);
CREATE INDEX idx_kg_nodes_importance ON knowledge_graph_nodes(importance_score DESC);
CREATE UNIQUE INDEX idx_kg_nodes_source_unique ON knowledge_graph_nodes(source_table, source_id);


-- 知识图谱边表
CREATE TABLE IF NOT EXISTS knowledge_graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edge_id TEXT UNIQUE NOT NULL,           -- 全局唯一 ID（格式：edge_uuid）

    -- 边信息
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,                -- 关系类型
    edge_label TEXT,

    -- 属性
    properties TEXT,                        -- JSON: 边属性
    weight REAL DEFAULT 1.0,
    confidence REAL DEFAULT 1.0,

    -- 方向
    is_directed BOOLEAN DEFAULT TRUE,

    -- 来源
    source_table TEXT,
    source_id TEXT,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (source_node_id) REFERENCES knowledge_graph_nodes(node_id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES knowledge_graph_nodes(node_id) ON DELETE CASCADE
);

CREATE INDEX idx_kg_edges_source ON knowledge_graph_edges(source_node_id);
CREATE INDEX idx_kg_edges_target ON knowledge_graph_edges(target_node_id);
CREATE INDEX idx_kg_edges_type ON knowledge_graph_edges(edge_type);
CREATE UNIQUE INDEX idx_kg_edges_unique ON knowledge_graph_edges(source_node_id, target_node_id, edge_type);


-- 系统事件表（事件总线）
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,          -- 全局唯一 ID（格式：evt_uuid）

    -- 事件信息
    event_type TEXT NOT NULL,               -- 'document.uploaded', 'pipeline.step_completed', 'knowledge.updated'
    event_category TEXT NOT NULL,           -- 'document', 'pipeline', 'knowledge', 'analysis', 'user'
    event_name TEXT,

    -- 事件数据
    payload TEXT NOT NULL,                  -- JSON: 事件载荷

    -- 发布者
    publisher TEXT NOT NULL,                -- 发布模块/服务

    -- 订阅者
    subscribers TEXT,                       -- JSON 数组：订阅该事件的模块

    -- 状态
    status TEXT DEFAULT 'published',        -- 'published', 'processing', 'consumed', 'failed'
    consumed_by TEXT,                       -- JSON 数组：已消费的模块列表

    -- 优先级
    priority INTEGER DEFAULT 5,             -- 1-10，数字越小优先级越高

    -- 重试
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consumed_at TIMESTAMP,

    -- 过期时间（事件保留时间）
    expires_at TIMESTAMP
);

CREATE INDEX idx_system_events_type ON system_events(event_type);
CREATE INDEX idx_system_events_category ON system_events(event_category);
CREATE INDEX idx_system_events_status ON system_events(status);
CREATE INDEX idx_system_events_created ON system_events(created_at DESC);
CREATE INDEX idx_system_events_priority ON system_events(priority, created_at);


-- 统一元数据表
CREATE TABLE IF NOT EXISTS unified_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metadata_id TEXT UNIQUE NOT NULL,       -- 全局唯一 ID（格式：meta_uuid）

    -- 目标对象
    target_type TEXT NOT NULL,              -- 'document', 'entity', 'event', 'summary', 'knowledge_unit'
    target_id TEXT NOT NULL,

    -- 元数据
    metadata_key TEXT NOT NULL,
    metadata_value TEXT,
    metadata_type TEXT DEFAULT 'string',    -- 'string', 'number', 'boolean', 'json', 'reference'

    -- 来源
    source_module TEXT,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_unified_metadata_target ON unified_metadata(target_type, target_id);
CREATE INDEX idx_unified_metadata_key ON unified_metadata(metadata_key);
CREATE UNIQUE INDEX idx_unified_metadata_unique ON unified_metadata(target_type, target_id, metadata_key);


-- ============================================================
-- Layer 5: 缩影系统整合（扩展现有表）
-- ============================================================

-- 扩展 file_summaries 表（关联知识图谱和 Wiki）
ALTER TABLE file_summaries ADD COLUMN knowledge_graph_node_id TEXT;
ALTER TABLE file_summaries ADD COLUMN knowledge_units TEXT;           -- JSON 数组：关联的知识单元 ID
ALTER TABLE file_summaries ADD COLUMN wiki_page_id TEXT;
ALTER TABLE file_summaries ADD COLUMN ontology_tags TEXT;             -- JSON 数组：本体标签
ALTER TABLE file_summaries ADD COLUMN inference_count INTEGER DEFAULT 0;
ALTER TABLE file_summaries ADD COLUMN relationships_count INTEGER DEFAULT 0;


-- ======================================================
-- 验证脚本
-- ======================================================

-- 验证所有新表是否创建成功
SELECT
    '✅ 统一数据模型创建完成' AS status,
    COUNT(*) AS new_tables_count
FROM sqlite_master
WHERE type='table'
AND name IN (
    'document_structure',
    'entities_unified',
    'events_unified',
    'relationships_unified',
    'ontology_concepts',
    'inference_results',
    'knowledge_units',
    'reader_templates',
    'wiki_pages',
    'knowledge_graph_nodes',
    'knowledge_graph_edges',
    'system_events',
    'unified_metadata'
);

-- 验证索引
SELECT '✅ 索引创建完成' AS status, COUNT(*) AS index_count
FROM sqlite_master
WHERE type='index'
AND name LIKE 'idx_%';
