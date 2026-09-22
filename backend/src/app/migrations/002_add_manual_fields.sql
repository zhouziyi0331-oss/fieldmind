-- 添加手动新增标记字段
-- Migration: 002_add_manual_fields
-- Description: 为知识图谱节点和关系添加 is_manual 和 pipeline_step 字段，用于区分手动添加和AI提取的数据
-- Created: 2024-01-XX

-- 1. 为 clean_channel_entities 表添加字段
ALTER TABLE clean_channel_entities
ADD COLUMN is_manual BOOLEAN DEFAULT FALSE COMMENT '是否手动添加';

ALTER TABLE clean_channel_entities
ADD COLUMN pipeline_step INTEGER DEFAULT 3 COMMENT '来源管道步骤，0表示手动添加，3表示实体提取步骤';

-- 2. 为 clean_channel_events 表添加字段
ALTER TABLE clean_channel_events
ADD COLUMN is_manual BOOLEAN DEFAULT FALSE COMMENT '是否手动添加';

ALTER TABLE clean_channel_events
ADD COLUMN pipeline_step INTEGER DEFAULT 4 COMMENT '来源管道步骤，0表示手动添加，4表示事件提取步骤';

-- 3. 为 clean_channel_relations 表添加字段
ALTER TABLE clean_channel_relations
ADD COLUMN is_manual BOOLEAN DEFAULT FALSE COMMENT '是否手动添加';

ALTER TABLE clean_channel_relations
ADD COLUMN pipeline_step INTEGER DEFAULT 5 COMMENT '来源管道步骤，0表示手动添加，5表示关系发现步骤';

-- 4. 为现有数据设置默认值（已存在的数据都是AI提取的）
UPDATE clean_channel_entities SET is_manual = FALSE, pipeline_step = 3 WHERE is_manual IS NULL;
UPDATE clean_channel_events SET is_manual = FALSE, pipeline_step = 4 WHERE is_manual IS NULL;
UPDATE clean_channel_relations SET is_manual = FALSE, pipeline_step = 5 WHERE is_manual IS NULL;

-- 5. 创建索引以提高查询性能
CREATE INDEX idx_entities_is_manual ON clean_channel_entities(is_manual);
CREATE INDEX idx_entities_pipeline_step ON clean_channel_entities(pipeline_step);
CREATE INDEX idx_events_is_manual ON clean_channel_events(is_manual);
CREATE INDEX idx_events_pipeline_step ON clean_channel_events(pipeline_step);
CREATE INDEX idx_relations_is_manual ON clean_channel_relations(is_manual);
CREATE INDEX idx_relations_pipeline_step ON clean_channel_relations(pipeline_step);

-- 说明：
-- is_manual = TRUE: 用户通过前端对话框手动添加的节点/关系
-- is_manual = FALSE: AI管道自动提取的节点/关系
-- pipeline_step = 0: 手动添加
-- pipeline_step = 3: AI实体提取步骤
-- pipeline_step = 4: AI事件提取步骤
-- pipeline_step = 5: AI关系发现步骤
