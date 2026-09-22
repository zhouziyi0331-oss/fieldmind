-- ID 统一迁移脚本
-- 用途：将现有数据库的 ID 迁移到统一格式

-- 1. 备份现有数据
CREATE TABLE projects_backup AS SELECT * FROM projects;
CREATE TABLE documents_backup AS SELECT * FROM documents;
CREATE TABLE chunks_backup AS SELECT * FROM chunks;
CREATE TABLE entities_backup AS SELECT * FROM entities;
CREATE TABLE relations_backup AS SELECT * FROM relations;

-- 2. 添加新 ID 列
ALTER TABLE projects ADD COLUMN new_id VARCHAR(20);
ALTER TABLE documents ADD COLUMN new_id VARCHAR(20);
ALTER TABLE chunks ADD COLUMN new_id VARCHAR(20);
ALTER TABLE entities ADD COLUMN new_id VARCHAR(20);
ALTER TABLE relations ADD COLUMN new_id VARCHAR(20);

-- 3. 生成新 ID
UPDATE projects SET new_id = 'proj_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE documents SET new_id = 'doc_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE chunks SET new_id = 'chk_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE entities SET new_id = 'ent_' || substring(md5(id::text || created_at::text) from 1 for 12);
UPDATE relations SET new_id = 'rel_' || substring(md5(id::text || created_at::text) from 1 for 12);

-- 4. 创建 ID 映射表（用于外键更新）
CREATE TABLE id_mapping (
    table_name VARCHAR(50),
    old_id TEXT,
    new_id VARCHAR(20),
    PRIMARY KEY (table_name, old_id)
);

INSERT INTO id_mapping SELECT 'projects', id, new_id FROM projects;
INSERT INTO id_mapping SELECT 'documents', id, new_id FROM documents;
INSERT INTO id_mapping SELECT 'chunks', id, new_id FROM chunks;
INSERT INTO id_mapping SELECT 'entities', id, new_id FROM entities;
INSERT INTO id_mapping SELECT 'relations', id, new_id FROM relations;

-- 5. 更新外键引用
-- 示例：更新 documents 表的 project_id
UPDATE documents d
SET project_id = m.new_id
FROM id_mapping m
WHERE m.table_name = 'projects'
  AND m.old_id = d.project_id;

-- 6. 替换主键
ALTER TABLE projects DROP CONSTRAINT projects_pkey;
ALTER TABLE projects DROP COLUMN id;
ALTER TABLE projects RENAME COLUMN new_id TO id;
ALTER TABLE projects ADD PRIMARY KEY (id);

-- 重复以上步骤，迁移所有表...

-- 7. 验证
SELECT 'projects' AS table_name, COUNT(*) AS count FROM projects
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'chunks', COUNT(*) FROM chunks
UNION ALL
SELECT 'entities', COUNT(*) FROM entities
UNION ALL
SELECT 'relations', COUNT(*) FROM relations;

-- 8. 清理
-- 确认无误后，删除备份表
-- DROP TABLE projects_backup;
-- DROP TABLE documents_backup;
-- ...
