-- ======================================================
-- FieldMind 知识缩影系统 - 数据库表设计
-- 创建时间: 2024-09-14
-- 功能: 为每个文档自动生成知识缩影卡片
-- ======================================================

-- 1. 文件缩影主表（每个文件一条缩影）
CREATE TABLE IF NOT EXISTS file_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL UNIQUE,
    project_id INTEGER NOT NULL,

    -- ============ 摘要内容 ============
    -- 一句话摘要（用于列表页快速浏览）
    one_line_summary TEXT,

    -- 完整摘要（200-500字，用于详情页展示）
    full_summary TEXT,

    -- ============ 核心信息（JSON格式） ============
    -- 核心关键词（从 extra_data.keywords 提取）
    -- 格式: [{"word":"山歌","count":34,"rank":1,"tfidf":0.89}, ...]
    top_keywords TEXT,

    -- 核心实体（从 entities 表聚合，如果有）
    -- 格式: [{"name":"王大爷","type":"person","mention_count":15}, ...]
    top_entities TEXT,

    -- 核心主题（从 topic_clusters 表聚合，如果有）
    -- 格式: [{"topic_id":1,"topic_name":"非遗传承","weight":0.76}, ...]
    top_topics TEXT,

    -- 核心事件（从 events 表聚合，如果有）
    -- 格式: [{"name":"山歌培训班停办","date":"2023.06","event_type":"社会"}, ...]
    top_events TEXT,

    -- ============ 量化指标 ============
    word_count INTEGER DEFAULT 0,              -- 总字数
    chunk_count INTEGER DEFAULT 0,             -- 总分块数
    avg_chunk_length REAL DEFAULT 0,           -- 平均分块长度

    -- 情感指标（可选，后续可集成情感分析）
    emotion_polarity REAL,                     -- 情绪极性（-1到1，负面到正面）
    subjectivity REAL,                         -- 主观性（0到1，客观到主观）

    -- ============ 维度标签 ============
    primary_dimension TEXT,                    -- 主要维度（如：非遗、民俗、历史）
    secondary_dimensions TEXT,                 -- 次要维度（JSON数组）

    -- ============ 时空上下文 ============
    time_start TEXT,                           -- 时间范围开始
    time_end TEXT,                             -- 时间范围结束
    spatial_context TEXT,                      -- 空间上下文（如：贵州村寨）

    -- ============ 关联文档 ============
    -- 格式: [{"document_id":2,"title":"山歌表演","similarity":0.89,"overlap_keywords":5}, ...]
    related_documents TEXT,

    -- ============ 生成状态 ============
    status TEXT DEFAULT 'pending',             -- pending / generating / done / error
    generated_at TEXT,                         -- 生成时间
    error_message TEXT,                        -- 错误信息（如果生成失败）

    -- ============ 时间戳 ============
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- ============ 外键约束 ============
    FOREIGN KEY (document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- 2. 普通索引（提升查询性能）
CREATE INDEX IF NOT EXISTS idx_file_summary_project ON file_summaries(project_id);
CREATE INDEX IF NOT EXISTS idx_file_summary_status ON file_summaries(status);
CREATE INDEX IF NOT EXISTS idx_file_summary_dimension ON file_summaries(primary_dimension);
CREATE INDEX IF NOT EXISTS idx_file_summary_created ON file_summaries(created_at DESC);

-- 3. FTS5 全文搜索索引（支持关键词搜索）
CREATE VIRTUAL TABLE IF NOT EXISTS file_summaries_fts USING fts5(
    one_line_summary,
    full_summary,
    top_keywords,
    content=file_summaries,
    content_rowid=id,
    tokenize='unicode61'
);

-- 4. 触发器：自动更新 FTS 索引
-- 插入时同步到 FTS
CREATE TRIGGER IF NOT EXISTS file_summaries_ai AFTER INSERT ON file_summaries BEGIN
    INSERT INTO file_summaries_fts(rowid, one_line_summary, full_summary, top_keywords)
    VALUES (new.id, new.one_line_summary, new.full_summary, new.top_keywords);
END;

-- 删除时同步删除 FTS
CREATE TRIGGER IF NOT EXISTS file_summaries_ad AFTER DELETE ON file_summaries BEGIN
    DELETE FROM file_summaries_fts WHERE rowid = old.id;
END;

-- 更新时同步更新 FTS
CREATE TRIGGER IF NOT EXISTS file_summaries_au AFTER UPDATE ON file_summaries BEGIN
    UPDATE file_summaries_fts
    SET one_line_summary = new.one_line_summary,
        full_summary = new.full_summary,
        top_keywords = new.top_keywords
    WHERE rowid = new.id;
END;

-- 5. 触发器：自动更新 updated_at
CREATE TRIGGER IF NOT EXISTS file_summaries_update_timestamp
AFTER UPDATE ON file_summaries
BEGIN
    UPDATE file_summaries
    SET updated_at = datetime('now')
    WHERE id = NEW.id;
END;

-- ======================================================
-- 验证表结构
-- ======================================================
-- 查看创建的表
SELECT '✅ file_summaries 表创建成功' AS result;
SELECT COUNT(*) AS table_count FROM sqlite_master WHERE type='table' AND name='file_summaries';

-- 查看索引
SELECT '✅ 索引创建成功' AS result;
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='file_summaries';

-- 查看 FTS5 虚拟表
SELECT '✅ FTS5 全文搜索索引创建成功' AS result;
SELECT COUNT(*) AS fts_count FROM sqlite_master WHERE type='table' AND name='file_summaries_fts';

-- 查看触发器
SELECT '✅ 触发器创建成功' AS result;
SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='file_summaries';
