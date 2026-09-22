-- 文档化规则层 - 数据库表设计

-- =====================================================
-- 表1: 文档规范化日志表
-- 记录每个文件的文档化处理过程和脏数据处理
-- =====================================================
CREATE TABLE IF NOT EXISTS document_normalization_logs (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,                    -- 关联 project_documents.id
    file_type VARCHAR(50) NOT NULL,              -- 文件类型（audio/video/table/document/image）
    normalization_rule VARCHAR(100) NOT NULL,    -- 使用的规则（AudioToTextRule/TableToTextRule等）

    -- 处理前后内容（用于审计）
    original_content_sample TEXT,                -- 原始内容样本（前1000字符）
    normalized_content_sample TEXT,              -- 规范化后内容样本（前1000字符）

    -- 脏数据处理记录
    dirty_data_found JSONB,                      -- 发现的脏数据：[{type, location, description}]
    dirty_data_handled JSONB,                    -- 如何处理的：[{type, action, before, after}]

    -- 完整性指标
    completeness_score FLOAT DEFAULT 0.0,        -- 完整性分数（0-1）
    completeness_details JSONB,                  -- 完整性详情

    -- 质量指标
    confidence FLOAT DEFAULT 1.0,                -- 整体置信度（0-1）
    quality_issues JSONB,                        -- 质量问题列表

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_time_ms INTEGER,                  -- 处理耗时（毫秒）

    -- 索引
    CONSTRAINT fk_file FOREIGN KEY (file_id) REFERENCES project_documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_normalization_logs_file_id ON document_normalization_logs(file_id);
CREATE INDEX idx_normalization_logs_file_type ON document_normalization_logs(file_type);
CREATE INDEX idx_normalization_logs_created_at ON document_normalization_logs(created_at DESC);


-- =====================================================
-- 表2: 文件规范化内容表
-- 存储规范化后的结构化内容
-- =====================================================
CREATE TABLE IF NOT EXISTS file_normalized_content (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,                    -- 关联 project_documents.id

    -- 内容类型
    content_type VARCHAR(50) NOT NULL,           -- text/table/formula/visual_description/audio_transcript/scene_description

    -- 内容本体
    content TEXT NOT NULL,                       -- 实际内容

    -- 结构化元数据
    metadata JSONB,                              -- 类型特定的元数据

    -- 来源追溯
    source_location JSONB,                       -- 来源位置：{page, time, bbox, etc.}
    extraction_method VARCHAR(100),              -- 提取方法（ocr/asr/vision_model/text_extraction）

    -- 质量指标
    confidence FLOAT DEFAULT 1.0,                -- 置信度（0-1）
    is_verified BOOLEAN DEFAULT FALSE,           -- 是否人工验证过

    -- 排序和分组
    sequence INTEGER DEFAULT 0,                  -- 在文件中的顺序
    parent_id INTEGER,                           -- 父内容ID（用于层级结构）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    CONSTRAINT fk_file FOREIGN KEY (file_id) REFERENCES project_documents(id) ON DELETE CASCADE,
    CONSTRAINT fk_parent FOREIGN KEY (parent_id) REFERENCES file_normalized_content(id) ON DELETE SET NULL
);

CREATE INDEX idx_normalized_content_file_id ON file_normalized_content(file_id);
CREATE INDEX idx_normalized_content_type ON file_normalized_content(content_type);
CREATE INDEX idx_normalized_content_sequence ON file_normalized_content(file_id, sequence);
CREATE INDEX idx_normalized_content_parent ON file_normalized_content(parent_id);


-- =====================================================
-- 表3: 脏数据处理规则配置表
-- 可配置的脏数据处理规则
-- =====================================================
CREATE TABLE IF NOT EXISTS dirty_data_rules (
    id SERIAL PRIMARY KEY,

    -- 规则标识
    rule_name VARCHAR(100) NOT NULL UNIQUE,      -- 规则名称（remove_filler_words/fix_ocr_errors等）
    rule_type VARCHAR(50) NOT NULL,              -- 规则类型（preprocessing/postprocessing/validation）

    -- 适用范围
    applicable_file_types TEXT[],                -- 适用的文件类型

    -- 规则定义
    rule_config JSONB NOT NULL,                  -- 规则配置：{pattern, action, threshold, etc.}

    -- 启用状态
    is_enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,                  -- 优先级（数字越大越优先）

    -- 说明
    description TEXT,
    examples JSONB,                              -- 示例：{before, after}

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dirty_data_rules_enabled ON dirty_data_rules(is_enabled);
CREATE INDEX idx_dirty_data_rules_type ON dirty_data_rules(rule_type);


-- =====================================================
-- 表4: 文件完整性检查记录表
-- 记录每个文件的完整性检查结果
-- =====================================================
CREATE TABLE IF NOT EXISTS file_completeness_checks (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,                    -- 关联 project_documents.id

    -- 检查类型
    check_type VARCHAR(50) NOT NULL,             -- audio_coverage/page_extraction/ocr_coverage/formula_recognition

    -- 检查结果
    is_passed BOOLEAN NOT NULL,                  -- 是否通过
    score FLOAT,                                 -- 得分（0-1）

    -- 详细信息
    details JSONB,                               -- 检查详情
    issues JSONB,                                -- 发现的问题
    recommendations JSONB,                       -- 改进建议

    -- 时间戳
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 索引
    CONSTRAINT fk_file FOREIGN KEY (file_id) REFERENCES project_documents(id) ON DELETE CASCADE
);

CREATE INDEX idx_completeness_checks_file_id ON file_completeness_checks(file_id);
CREATE INDEX idx_completeness_checks_type ON file_completeness_checks(check_type);
CREATE INDEX idx_completeness_checks_passed ON file_completeness_checks(is_passed);


-- =====================================================
-- 视图：文件处理完整报告
-- 聚合所有相关信息
-- =====================================================
CREATE OR REPLACE VIEW file_processing_report AS
SELECT
    pd.id AS file_id,
    pd.original_filename,
    pd.file_type,
    pd.file_size,
    pd.status,

    -- 规范化信息
    dnl.normalization_rule,
    dnl.completeness_score,
    dnl.confidence,
    dnl.processing_time_ms,
    jsonb_array_length(COALESCE(dnl.dirty_data_found, '[]'::jsonb)) AS dirty_data_count,

    -- 内容统计
    COUNT(DISTINCT fnc.id) AS normalized_content_count,
    COUNT(DISTINCT fnc.content_type) AS content_type_count,

    -- 完整性检查
    COUNT(CASE WHEN fcc.is_passed THEN 1 END) AS completeness_checks_passed,
    COUNT(fcc.id) AS completeness_checks_total,

    -- 时间戳
    pd.created_at AS uploaded_at,
    dnl.created_at AS normalized_at

FROM project_documents pd
LEFT JOIN document_normalization_logs dnl ON pd.id = dnl.file_id
LEFT JOIN file_normalized_content fnc ON pd.id = fnc.file_id
LEFT JOIN file_completeness_checks fcc ON pd.id = fcc.file_id
GROUP BY
    pd.id,
    pd.original_filename,
    pd.file_type,
    pd.file_size,
    pd.status,
    dnl.normalization_rule,
    dnl.completeness_score,
    dnl.confidence,
    dnl.processing_time_ms,
    dnl.dirty_data_found,
    pd.created_at,
    dnl.created_at;


-- =====================================================
-- 默认脏数据处理规则
-- =====================================================

-- 规则1：去除音频口头禅
INSERT INTO dirty_data_rules (rule_name, rule_type, applicable_file_types, rule_config, description, examples) VALUES
('remove_filler_words', 'preprocessing', ARRAY['audio', 'video'],
 '{"patterns": ["嗯", "啊", "那个", "这个", "呃"], "action": "remove", "threshold": 0.8}'::jsonb,
 '去除无意义的口头禅',
 '[{"before": "嗯嗯嗯，那个，我觉得", "after": "我觉得"}]'::jsonb);

-- 规则2：修正常见OCR错别字
INSERT INTO dirty_data_rules (rule_name, rule_type, applicable_file_types, rule_config, description, examples) VALUES
('fix_ocr_errors', 'postprocessing', ARRAY['document', 'image'],
 '{"replacements": {"0": "○", "l": "I"}, "action": "replace", "threshold": 0.9}'::jsonb,
 '修正常见的OCR识别错误',
 '[{"before": "这是第l条", "after": "这是第1条"}]'::jsonb);

-- 规则3：识别并保留有情感含义的语气词
INSERT INTO dirty_data_rules (rule_name, rule_type, applicable_file_types, rule_config, description, examples) VALUES
('keep_emotional_words', 'preprocessing', ARRAY['audio', 'video'],
 '{"patterns": ["唉", "哎哟", "哇", "嘿"], "action": "keep_and_tag", "tag": "[情感]"}'::jsonb,
 '保留有情感含义的语气词',
 '[{"before": "唉，真难啊", "after": "[情感:唉] 真难啊"}]'::jsonb);

-- 规则4：表格单位识别
INSERT INTO dirty_data_rules (rule_name, rule_type, applicable_file_types, rule_config, description, examples) VALUES
('recognize_table_units', 'postprocessing', ARRAY['table'],
 '{"units": ["元", "万元", "亩", "公斤", "吨"], "action": "extract_and_tag"}'::jsonb,
 '识别表格中的单位',
 '[{"before": "收入 100", "after": "收入 100万元"}]'::jsonb);


-- =====================================================
-- 函数：获取文件的脏数据处理报告
-- =====================================================
CREATE OR REPLACE FUNCTION get_dirty_data_report(p_file_id INTEGER)
RETURNS TABLE(
    dirty_data_type VARCHAR,
    count INTEGER,
    examples JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (jsonb_array_elements(dirty_data_found)->>'type')::VARCHAR AS dirty_data_type,
        COUNT(*)::INTEGER AS count,
        jsonb_agg(jsonb_array_elements(dirty_data_found)) AS examples
    FROM document_normalization_logs
    WHERE file_id = p_file_id
    GROUP BY (jsonb_array_elements(dirty_data_found)->>'type');
END;
$$ LANGUAGE plpgsql;


-- =====================================================
-- 注释
-- =====================================================
COMMENT ON TABLE document_normalization_logs IS '文档规范化日志表 - 记录文档化处理过程';
COMMENT ON TABLE file_normalized_content IS '文件规范化内容表 - 存储规范化后的结构化内容';
COMMENT ON TABLE dirty_data_rules IS '脏数据处理规则配置表 - 可配置的处理规则';
COMMENT ON TABLE file_completeness_checks IS '文件完整性检查记录表 - 记录完整性检查结果';
COMMENT ON VIEW file_processing_report IS '文件处理完整报告视图 - 聚合所有处理信息';
