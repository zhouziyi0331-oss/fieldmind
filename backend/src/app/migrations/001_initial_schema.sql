-- FieldMind 初始数据库Schema
-- 创建时间: 2024-01-20
-- 版本: 1.0.0

-- ============================================
-- 1. 文档主表
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(50) PRIMARY KEY COMMENT '文档唯一ID',
    project_id INTEGER NOT NULL COMMENT '项目ID',
    name VARCHAR(500) NOT NULL COMMENT '文件名',
    type ENUM('document', 'image', 'audio', 'video', 'table', 'other') NOT NULL COMMENT '文件类型',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    file_size BIGINT COMMENT '文件大小（字节）',
    file_path VARCHAR(1000) NOT NULL COMMENT '对象存储路径',
    hash VARCHAR(64) UNIQUE COMMENT 'SHA256哈希，用于去重',
    status ENUM('uploaded', 'queued', 'processing', 'completed', 'failed') DEFAULT 'uploaded' COMMENT '处理状态',
    error_message TEXT COMMENT '错误信息',
    task_id VARCHAR(100) COMMENT '处理任务ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    INDEX idx_project (project_id),
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_hash (hash),
    INDEX idx_created (created_at),
    INDEX idx_project_type (project_id, type),
    INDEX idx_project_status (project_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档主表';

-- ============================================
-- 2. 元数据表（JSON存储）
-- ============================================
CREATE TABLE IF NOT EXISTS document_metadata (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '元数据ID',
    document_id VARCHAR(50) NOT NULL COMMENT '文档ID',
    metadata_type VARCHAR(50) NOT NULL COMMENT '元数据类型：exif, transcript, ocr, structure等',
    metadata JSON NOT NULL COMMENT '元数据内容（JSON格式）',
    confidence FLOAT COMMENT '置信度（0-1）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_type (metadata_type),
    INDEX idx_document_type (document_id, metadata_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档元数据表';

-- ============================================
-- 3. 实体表
-- ============================================
CREATE TABLE IF NOT EXISTS entities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '实体ID',
    text VARCHAR(500) NOT NULL COMMENT '实体文本',
    type ENUM('PERSON', 'ORG', 'LOCATION', 'DATE', 'TIME', 'CONCEPT', 'OTHER') NOT NULL COMMENT '实体类型',
    canonical_form VARCHAR(500) COMMENT '标准化形式，用于消歧',
    description TEXT COMMENT '实体描述',
    metadata JSON COMMENT '额外元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    UNIQUE KEY uk_text_type (text, type),
    INDEX idx_type (type),
    INDEX idx_canonical (canonical_form),
    FULLTEXT INDEX ft_text (text, canonical_form)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实体表';

-- ============================================
-- 4. 文档-实体关系表
-- ============================================
CREATE TABLE IF NOT EXISTS document_entities (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '关系ID',
    document_id VARCHAR(50) NOT NULL COMMENT '文档ID',
    entity_id BIGINT NOT NULL COMMENT '实体ID',
    mentions INTEGER DEFAULT 1 COMMENT '出现次数',
    confidence FLOAT COMMENT '置信度（0-1）',
    context TEXT COMMENT '出现的上下文',
    positions JSON COMMENT '出现的位置列表',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    UNIQUE KEY uk_doc_entity (document_id, entity_id),
    INDEX idx_document (document_id),
    INDEX idx_entity (entity_id),
    INDEX idx_confidence (confidence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档-实体关系表';

-- ============================================
-- 5. 实体关系表
-- ============================================
CREATE TABLE IF NOT EXISTS entity_relations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '关系ID',
    source_entity_id BIGINT NOT NULL COMMENT '源实体ID',
    target_entity_id BIGINT NOT NULL COMMENT '目标实体ID',
    relation_type VARCHAR(100) NOT NULL COMMENT '关系类型：works_for, located_in, part_of等',
    confidence FLOAT COMMENT '置信度（0-1）',
    source_documents JSON COMMENT '支持该关系的文档ID列表',
    metadata JSON COMMENT '额外元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (source_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
    INDEX idx_source (source_entity_id),
    INDEX idx_target (target_entity_id),
    INDEX idx_type (relation_type),
    INDEX idx_source_type (source_entity_id, relation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实体关系表';

-- ============================================
-- 6. 标签表
-- ============================================
CREATE TABLE IF NOT EXISTS tags (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '标签ID',
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '标签名称',
    category VARCHAR(50) COMMENT '标签分类：manual, auto, ai',
    color VARCHAR(7) COMMENT 'HEX颜色代码',
    description TEXT COMMENT '标签描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_category (category),
    FULLTEXT INDEX ft_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签表';

-- ============================================
-- 7. 文档-标签关系表
-- ============================================
CREATE TABLE IF NOT EXISTS document_tags (
    document_id VARCHAR(50) NOT NULL COMMENT '文档ID',
    tag_id BIGINT NOT NULL COMMENT '标签ID',
    confidence FLOAT COMMENT 'AI标签的置信度（0-1）',
    created_by VARCHAR(50) COMMENT '创建者：system或用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (document_id, tag_id),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    INDEX idx_tag (tag_id),
    INDEX idx_confidence (confidence)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档-标签关系表';

-- ============================================
-- 8. 文本分块表（用于RAG）
-- ============================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id VARCHAR(50) PRIMARY KEY COMMENT '分块ID',
    document_id VARCHAR(50) NOT NULL COMMENT '文档ID',
    chunk_index INTEGER NOT NULL COMMENT '分块索引',
    text TEXT NOT NULL COMMENT '分块文本内容',
    token_count INTEGER COMMENT 'Token数量',
    start_pos INTEGER COMMENT '开始位置',
    end_pos INTEGER COMMENT '结束位置',
    metadata JSON COMMENT '额外元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_chunk (document_id, chunk_index),
    FULLTEXT INDEX ft_text (text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文本分块表';

-- ============================================
-- 9. 向量嵌入表
-- ============================================
CREATE TABLE IF NOT EXISTS embeddings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '嵌入ID',
    entity_type ENUM('document', 'chunk', 'image', 'entity') NOT NULL COMMENT '实体类型',
    entity_id VARCHAR(50) NOT NULL COMMENT '实体ID',
    model VARCHAR(100) NOT NULL COMMENT '模型名称：text-embedding-3-large等',
    vector_dimension INTEGER NOT NULL COMMENT '向量维度',
    vector_data BLOB NOT NULL COMMENT '向量数据（二进制存储）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_model (model),
    UNIQUE KEY uk_entity_model (entity_type, entity_id, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='向量嵌入表';

-- 注意：向量检索将使用pgvector（PostgreSQL）或专门的向量数据库
-- 此表用于MySQL环境下的基础存储

-- ============================================
-- 10. 时间线事件表
-- ============================================
CREATE TABLE IF NOT EXISTS timeline_events (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '事件ID',
    document_id VARCHAR(50) NOT NULL COMMENT '文档ID',
    event_time TIMESTAMP NOT NULL COMMENT '事件时间',
    event_type VARCHAR(50) COMMENT '事件类型：created, uploaded, mentioned, photo_taken等',
    description TEXT COMMENT '事件描述',
    metadata JSON COMMENT '额外元数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_time (event_time),
    INDEX idx_type (event_type),
    INDEX idx_document_time (document_id, event_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='时间线事件表';

-- ============================================
-- 11. 处理任务表（追踪处理状态）
-- ============================================
CREATE TABLE IF NOT EXISTS processing_tasks (
    id VARCHAR(100) PRIMARY KEY COMMENT '任务ID（Celery Task ID）',
    document_id VARCHAR(50) NOT NULL COMMENT '文档ID',
    task_type VARCHAR(50) NOT NULL COMMENT '任务类型：classify, extract, embed等',
    status ENUM('pending', 'running', 'success', 'failed', 'retry') DEFAULT 'pending' COMMENT '任务状态',
    progress INTEGER DEFAULT 0 COMMENT '进度（0-100）',
    result JSON COMMENT '任务结果',
    error TEXT COMMENT '错误信息',
    retry_count INTEGER DEFAULT 0 COMMENT '重试次数',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_status (status),
    INDEX idx_type (task_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='处理任务表';

-- ============================================
-- 12. 数据质量报告表
-- ============================================
CREATE TABLE IF NOT EXISTS quality_reports (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '报告ID',
    document_id VARCHAR(50) NOT NULL COMMENT '文档ID',
    check_type VARCHAR(50) NOT NULL COMMENT '检查类型：completeness, consistency, accuracy等',
    score FLOAT COMMENT '质量分数（0-1）',
    issues JSON COMMENT '问题列表',
    recommendations JSON COMMENT '建议列表',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    INDEX idx_type (check_type),
    INDEX idx_score (score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据质量报告表';

-- ============================================
-- 插入初始数据
-- ============================================

-- 插入系统默认标签
INSERT INTO tags (name, category, color, description) VALUES
('重要', 'manual', '#EF4444', '重要文档'),
('紧急', 'manual', '#F59E0B', '紧急处理'),
('已审核', 'manual', '#10B981', '已完成审核'),
('待处理', 'manual', '#6B7280', '等待处理'),
('归档', 'manual', '#8B5CF6', '已归档文档');

-- ============================================
-- 创建视图
-- ============================================

-- 文档详情视图（包含统计信息）
CREATE OR REPLACE VIEW document_details AS
SELECT
    d.id,
    d.project_id,
    d.name,
    d.type,
    d.mime_type,
    d.file_size,
    d.hash,
    d.status,
    d.created_at,
    d.updated_at,
    COUNT(DISTINCT de.entity_id) as entity_count,
    COUNT(DISTINCT dt.tag_id) as tag_count,
    COUNT(DISTINCT dc.id) as chunk_count,
    GROUP_CONCAT(DISTINCT t.name) as tag_names
FROM documents d
LEFT JOIN document_entities de ON d.id = de.document_id
LEFT JOIN document_tags dt ON d.id = dt.document_id
LEFT JOIN tags t ON dt.tag_id = t.id
LEFT JOIN document_chunks dc ON d.id = dc.document_id
GROUP BY d.id;

-- ============================================
-- 数据库配置优化
-- ============================================

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 性能优化设置（仅用于开发环境参考）
-- SET GLOBAL innodb_buffer_pool_size = 2147483648; -- 2GB
-- SET GLOBAL max_connections = 200;
-- SET GLOBAL query_cache_size = 67108864; -- 64MB

-- ============================================
-- 完成
-- ============================================

SELECT '数据库Schema创建完成！' as message;
SELECT COUNT(*) as table_count FROM information_schema.tables
WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE';
