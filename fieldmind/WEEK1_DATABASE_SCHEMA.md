# FieldMind 数据库完整结构分析
生成时间: 2026-09-13T12:31:20.380229
数据库路径: /Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db

## 概览

- 总表数: 102


## 表: `ai_questions`

- 记录数: **0**
- 列数: 12
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) |  |  |  |
| 3 | `question` | TEXT | ✅ |  |  |
| 4 | `question_type` | VARCHAR(50) | ✅ |  |  |
| 5 | `trigger_context` | JSON |  |  |  |
| 6 | `user_answer` | TEXT |  |  |  |
| 7 | `answered_at` | DATETIME |  |  |  |
| 8 | `learning_result` | JSON |  |  |  |
| 9 | `is_answered` | INTEGER | ✅ |  |  |
| 10 | `is_useful` | INTEGER |  |  |  |
| 11 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `alembic_version`

- 记录数: **1**
- 列数: 1
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `version_num` | VARCHAR(32) | ✅ |  | 🔑 |

### 示例数据（前3条）

| version_num |
|---|
| 008_add_tfidf_clustering |

---

## 表: `analysis_reports`

- 记录数: **0**
- 列数: 25
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `tier` | VARCHAR(20) | ✅ |  |  |
| 2 | `title` | VARCHAR(500) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `document_ids` | JSON |  |  |  |
| 5 | `context_ids` | JSON |  |  |  |
| 6 | `entity_ids` | JSON |  |  |  |
| 7 | `skill_ids` | JSON |  |  |  |
| 8 | `content` | JSON |  |  |  |
| 9 | `word_count` | INTEGER |  |  |  |
| 10 | `section_count` | INTEGER |  |  |  |
| 11 | `chart_count` | INTEGER |  |  |  |
| 12 | `file_path` | VARCHAR(1000) |  |  |  |
| 13 | `file_format` | VARCHAR(20) |  |  |  |
| 14 | `file_size` | INTEGER |  |  |  |
| 15 | `status` | VARCHAR(50) |  |  |  |
| 16 | `progress` | INTEGER |  |  |  |
| 17 | `error_message` | TEXT |  |  |  |
| 18 | `task_id` | VARCHAR(100) |  |  |  |
| 19 | `generation_config` | JSON |  |  |  |
| 20 | `quality_score` | FLOAT |  |  |  |
| 21 | `created_by` | VARCHAR(36) |  |  |  |
| 22 | `created_at` | DATETIME | ✅ |  |  |
| 23 | `completed_at` | DATETIME |  |  |  |
| 24 | `updated_at` | DATETIME |  |  |  |

---

## 表: `analysis_results`

- 记录数: **0**
- 列数: 12
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `created_by` | VARCHAR(36) |  |  |  |
| 3 | `analysis_type` | VARCHAR(50) | ✅ |  |  |
| 4 | `title` | VARCHAR(200) | ✅ |  |  |
| 5 | `description` | TEXT |  |  |  |
| 6 | `parameters` | JSON |  |  |  |
| 7 | `result` | JSON | ✅ |  |  |
| 8 | `created_at` | DATETIME |  |  |  |
| 9 | `updated_at` | DATETIME |  |  |  |
| 10 | `view_count` | INTEGER |  |  |  |
| 11 | `rating` | FLOAT |  |  |  |

---

## 表: `analysis_statements`

- 记录数: **0**
- 列数: 8
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `analysis_id` | INTEGER | ✅ |  |  |
| 2 | `statement_text` | TEXT | ✅ |  |  |
| 3 | `statement_type` | VARCHAR(50) |  |  |  |
| 4 | `section` | VARCHAR(100) |  |  |  |
| 5 | `order_index` | INTEGER |  |  |  |
| 6 | `confidence_score` | FLOAT |  |  |  |
| 7 | `created_at` | DATETIME |  |  |  |

---

## 表: `audit_logs`

- 记录数: **0**
- 列数: 16
- 索引数: 10

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `timestamp` | DATETIME | ✅ |  |  |
| 2 | `actor_type` | VARCHAR(6) | ✅ |  |  |
| 3 | `actor_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `action` | VARCHAR(11) | ✅ |  |  |
| 5 | `resource_type` | VARCHAR(50) | ✅ |  |  |
| 6 | `resource_id` | VARCHAR(36) | ✅ |  |  |
| 7 | `resource_name` | VARCHAR(500) |  |  |  |
| 8 | `project_id` | VARCHAR(36) |  |  |  |
| 9 | `changes` | JSON |  |  |  |
| 10 | `ai_model` | VARCHAR(100) |  |  |  |
| 11 | `ai_prompt` | TEXT |  |  |  |
| 12 | `result` | VARCHAR(7) | ✅ |  |  |
| 13 | `error_message` | TEXT |  |  |  |
| 14 | `extra_metadata` | JSON |  |  |  |
| 15 | `duration_ms` | INTEGER |  |  |  |

---

## 表: `background_learning_tasks`

- 记录数: **0**
- 列数: 26
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `task_type` | VARCHAR(23) | ✅ |  |  |
| 2 | `task_name` | VARCHAR(200) | ✅ |  |  |
| 3 | `task_description` | TEXT | ✅ |  |  |
| 4 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 5 | `triggered_by_user_id` | VARCHAR(36) |  |  |  |
| 6 | `task_config` | JSON | ✅ |  |  |
| 7 | `priority` | VARCHAR(6) | ✅ |  |  |
| 8 | `scheduled_at` | DATETIME | ✅ |  |  |
| 9 | `is_recurring` | BOOLEAN | ✅ |  |  |
| 10 | `recurrence_pattern` | VARCHAR(100) |  |  |  |
| 11 | `status` | VARCHAR(9) | ✅ |  |  |
| 12 | `started_at` | DATETIME |  |  |  |
| 13 | `completed_at` | DATETIME |  |  |  |
| 14 | `duration_seconds` | FLOAT |  |  |  |
| 15 | `learning_results` | JSON |  |  |  |
| 16 | `discoveries` | JSON |  |  |  |
| 17 | `error_message` | TEXT |  |  |  |
| 18 | `error_stack` | TEXT |  |  |  |
| 19 | `retry_count` | INTEGER |  |  |  |
| 20 | `max_retries` | INTEGER |  |  |  |
| 21 | `progress_percentage` | FLOAT |  |  |  |
| 22 | `progress_message` | VARCHAR(200) |  |  |  |
| 23 | `created_at` | DATETIME | ✅ |  |  |
| 24 | `updated_at` | DATETIME | ✅ |  |  |
| 25 | `extra_metadata` | JSON |  |  |  |

---

## 表: `batch_operations`

- 记录数: **0**
- 列数: 11
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `batch_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | INTEGER | ✅ |  |  |
| 3 | `operation_type` | VARCHAR(50) | ✅ |  |  |
| 4 | `total_items` | INTEGER |  |  |  |
| 5 | `completed_items` | INTEGER |  |  |  |
| 6 | `failed_items` | INTEGER |  |  |  |
| 7 | `status` | VARCHAR(20) |  |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |
| 9 | `completed_at` | DATETIME |  |  |  |
| 10 | `extra_data` | JSON |  |  |  |

---

## 表: `chat_messages`

- 记录数: **0**
- 列数: 7
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `session_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `role` | VARCHAR(20) | ✅ |  |  |
| 3 | `content` | TEXT | ✅ |  |  |
| 4 | `sources` | JSON |  |  |  |
| 5 | `message_metadata` | JSON |  |  |  |
| 6 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `chat_sessions`

- 记录数: **0**
- 列数: 8
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) |  |  |  |
| 2 | `title` | VARCHAR(500) |  |  |  |
| 3 | `context` | JSON |  |  |  |
| 4 | `message_count` | INTEGER |  |  |  |
| 5 | `created_at` | DATETIME | ✅ |  |  |
| 6 | `updated_at` | DATETIME |  |  |  |
| 7 | `last_message_at` | DATETIME |  |  |  |

---

## 表: `chunk_entities`

- 记录数: **0**
- 列数: 8
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `chunk_id` | VARCHAR(50) | ✅ |  |  |
| 2 | `entity_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `confidence` | FLOAT |  |  |  |
| 4 | `mention_context` | TEXT |  |  |  |
| 5 | `position_start` | INTEGER |  |  |  |
| 6 | `position_end` | INTEGER |  |  |  |
| 7 | `created_at` | DATETIME | ✅ | CURRENT_TIMESTAMP |  |

---

## 表: `chunks_fts_simple`

- 记录数: **1036**
- 列数: 2
- 索引数: 0

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `chunk_id` |  |  |  |  |
| 1 | `text` |  |  |  |  |

---

## 表: `chunks_fts_simple_config`

- 记录数: **1**
- 列数: 2
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `k` |  | ✅ |  | 🔑 |
| 1 | `v` |  |  |  |  |

### 示例数据（前3条）

| k | v |
|---|---|
| version | 4 |

---

## 表: `chunks_fts_simple_data`

- 记录数: **250**
- 列数: 2
- 索引数: 0

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER |  |  | 🔑 |
| 1 | `block` | BLOB |  |  |  |

---

## 表: `chunks_fts_simple_docsize`

- 记录数: **1036**
- 列数: 2
- 索引数: 0

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER |  |  | 🔑 |
| 1 | `sz` | BLOB |  |  |  |

---

## 表: `chunks_fts_simple_idx`

- 记录数: **248**
- 列数: 3
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `segid` |  | ✅ |  | 🔑 |
| 1 | `term` |  | ✅ |  | 🔑 |
| 2 | `pgno` |  |  |  |  |

---

## 表: `citations`

- 记录数: **0**
- 列数: 20
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `title` | VARCHAR(500) | ✅ |  |  |
| 2 | `authors` | JSON |  |  |  |
| 3 | `year` | VARCHAR(20) |  |  |  |
| 4 | `publication` | VARCHAR(300) |  |  |  |
| 5 | `publisher` | VARCHAR(200) |  |  |  |
| 6 | `doi` | VARCHAR(200) |  |  |  |
| 7 | `isbn` | VARCHAR(50) |  |  |  |
| 8 | `url` | VARCHAR(1000) |  |  |  |
| 9 | `abstract` | TEXT |  |  |  |
| 10 | `notes` | TEXT |  |  |  |
| 11 | `citation_type` | VARCHAR(50) | ✅ |  |  |
| 12 | `tags` | JSON |  |  |  |
| 13 | `project_id` | INTEGER | ✅ |  |  |
| 14 | `cited_count` | INTEGER |  |  |  |
| 15 | `added_at` | DATETIME | ✅ |  |  |
| 16 | `updated_at` | DATETIME |  |  |  |
| 17 | `added_by` | INTEGER |  |  |  |
| 18 | `bibtex` | TEXT |  |  |  |
| 19 | `extra_metadata` | JSON |  |  |  |

---

## 表: `contexts`

- 记录数: **0**
- 列数: 19
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `context_type` | VARCHAR(50) | ✅ |  |  |
| 2 | `title` | VARCHAR(500) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `is_main` | BOOLEAN |  |  |  |
| 5 | `parent_context_id` | VARCHAR(36) |  |  |  |
| 6 | `entities` | JSON |  |  |  |
| 7 | `timeline` | JSON |  |  |  |
| 8 | `graph_data` | JSON |  |  |  |
| 9 | `documents` | JSON |  |  |  |
| 10 | `entity_count` | INTEGER |  |  |  |
| 11 | `document_count` | INTEGER |  |  |  |
| 12 | `event_count` | INTEGER |  |  |  |
| 13 | `summary` | TEXT |  |  |  |
| 14 | `key_findings` | JSON |  |  |  |
| 15 | `visualization_config` | JSON |  |  |  |
| 16 | `created_at` | DATETIME | ✅ |  |  |
| 17 | `updated_at` | DATETIME |  |  |  |
| 18 | `analyzed_at` | DATETIME |  |  |  |

---

## 表: `conversation_memory`

- 记录数: **0**
- 列数: 12
- 索引数: 6

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) |  |  |  |
| 3 | `conversation_content` | TEXT | ✅ |  |  |
| 4 | `user_message` | TEXT | ✅ |  |  |
| 5 | `ai_response` | TEXT |  |  |  |
| 6 | `extracted_patterns` | JSON |  |  |  |
| 7 | `topic` | VARCHAR(200) |  |  |  |
| 8 | `tags` | JSON |  |  |  |
| 9 | `learning_status` | VARCHAR(8) | ✅ |  |  |
| 10 | `timestamp` | DATETIME | ✅ |  |  |
| 11 | `extra_metadata` | JSON |  |  |  |

---

## 表: `data_lineage`

- 记录数: **0**
- 列数: 13
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `source_type` | VARCHAR(12) | ✅ |  |  |
| 2 | `source_resource_type` | VARCHAR(15) |  |  |  |
| 3 | `source_id` | VARCHAR(36) |  |  |  |
| 4 | `source_detail` | JSON |  |  |  |
| 5 | `target_type` | VARCHAR(15) | ✅ |  |  |
| 6 | `target_id` | VARCHAR(36) | ✅ |  |  |
| 7 | `target_detail` | JSON |  |  |  |
| 8 | `relationship_type` | VARCHAR(14) | ✅ |  |  |
| 9 | `project_id` | VARCHAR(36) |  |  |  |
| 10 | `created_at` | DATETIME | ✅ |  |  |
| 11 | `created_by` | VARCHAR(36) |  |  |  |
| 12 | `extra_metadata` | JSON |  |  |  |

---

## 表: `data_versions`

- 记录数: **0**
- 列数: 16
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `resource_type` | VARCHAR(15) | ✅ |  |  |
| 2 | `resource_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `version_number` | INTEGER | ✅ |  |  |
| 4 | `version_tag` | VARCHAR(100) |  |  |  |
| 5 | `content` | TEXT |  |  |  |
| 6 | `content_hash` | VARCHAR(64) |  |  |  |
| 7 | `change_type` | VARCHAR(6) | ✅ |  |  |
| 8 | `change_summary` | TEXT |  |  |  |
| 9 | `change_detail` | JSON |  |  |  |
| 10 | `change_reason` | TEXT |  |  |  |
| 11 | `changed_by_type` | VARCHAR(20) | ✅ |  |  |
| 12 | `changed_by` | VARCHAR(36) | ✅ |  |  |
| 13 | `project_id` | VARCHAR(36) |  |  |  |
| 14 | `created_at` | DATETIME | ✅ |  |  |
| 15 | `extra_metadata` | JSON |  |  |  |

---

## 表: `document_chunks`

- 记录数: **1036**
- 列数: 41
- 索引数: 9

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `chunk_id` | VARCHAR(100) | ✅ |  |  |
| 2 | `document_id` | INTEGER | ✅ |  |  |
| 3 | `project_id` | INTEGER | ✅ |  |  |
| 4 | `chunk_index` | INTEGER | ✅ |  |  |
| 5 | `text` | TEXT | ✅ |  |  |
| 6 | `text_length` | INTEGER |  |  |  |
| 7 | `chunk_text` | TEXT | ✅ |  |  |
| 8 | `chunk_size` | INTEGER | ✅ |  |  |
| 9 | `total_chunks` | INTEGER |  |  |  |
| 10 | `token_count` | INTEGER |  |  |  |
| 11 | `start_pos` | INTEGER |  |  |  |
| 12 | `end_pos` | INTEGER |  |  |  |
| 13 | `page_number` | INTEGER |  |  |  |
| 14 | `speaker` | VARCHAR(100) |  |  |  |
| 15 | `timestamp_start` | INTEGER |  |  |  |
| 16 | `timestamp_end` | INTEGER |  |  |  |
| 17 | `embedding` | JSON |  |  |  |
| 18 | `embedding_model` | VARCHAR(100) |  |  |  |
| 19 | `chunk_metadata` | JSON |  |  |  |
| 20 | `prev_chunk_id` | VARCHAR(100) |  |  |  |
| 21 | `next_chunk_id` | VARCHAR(100) |  |  |  |
| 22 | `vectorized_at` | DATETIME |  |  |  |
| 23 | `chapter_title` | VARCHAR(500) |  |  |  |
| 24 | `section_title` | VARCHAR(500) |  |  |  |
| 25 | `subsection_title` | VARCHAR(500) |  |  |  |
| 26 | `key_entities` | JSON |  |  |  |
| 27 | `domain_tags` | JSON |  |  |  |
| 28 | `primary_domain` | VARCHAR(100) |  |  |  |
| 29 | `temporal_context` | VARCHAR(200) |  |  |  |
| 30 | `spatial_context` | VARCHAR(200) |  |  |  |
| 31 | `chunk_role` | VARCHAR(50) |  |  |  |
| 32 | `chunk_summary` | TEXT |  |  |  |
| 33 | `enhanced_text` | TEXT |  |  |  |
| 34 | `enhancement_confidence` | INTEGER |  |  |  |
| 35 | `is_table_chunk` | INTEGER |  |  |  |
| 36 | `table_sheet_name` | VARCHAR(200) |  |  |  |
| 37 | `table_row_range` | VARCHAR(50) |  |  |  |
| 38 | `structured_data` | JSON |  |  |  |
| 39 | `metadata` | JSON |  |  |  |
| 40 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `document_citations`

- 记录数: **0**
- 列数: 7
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `document_id` | INTEGER | ✅ |  |  |
| 2 | `citation_id` | INTEGER | ✅ |  |  |
| 3 | `page_number` | INTEGER |  |  |  |
| 4 | `location_text` | VARCHAR(500) |  |  |  |
| 5 | `context` | TEXT |  |  |  |
| 6 | `created_at` | DATETIME |  |  |  |

---

## 表: `document_entities`

- 记录数: **0**
- 列数: 8
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | BIGINT | ✅ |  | 🔑 |
| 1 | `document_id` | VARCHAR(50) | ✅ |  |  |
| 2 | `entity_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `mentions` | INTEGER |  |  |  |
| 4 | `confidence` | FLOAT |  |  |  |
| 5 | `context` | TEXT |  |  |  |
| 6 | `positions` | JSON |  |  |  |
| 7 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `document_metadata`

- 记录数: **0**
- 列数: 6
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | BIGINT | ✅ |  | 🔑 |
| 1 | `document_id` | VARCHAR(50) | ✅ |  |  |
| 2 | `metadata_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `metadata` | JSON | ✅ |  |  |
| 4 | `confidence` | FLOAT |  |  |  |
| 5 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `document_tags`

- 记录数: **0**
- 列数: 5
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `document_id` | VARCHAR(50) | ✅ |  | 🔑 |
| 1 | `tag_id` | BIGINT | ✅ |  | 🔑 |
| 2 | `confidence` | FLOAT |  |  |  |
| 3 | `created_by` | VARCHAR(50) |  |  |  |
| 4 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `documents`

- 记录数: **0**
- 列数: 15
- 索引数: 10

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(50) | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `name` | VARCHAR(500) | ✅ |  |  |
| 3 | `type` | VARCHAR(8) | ✅ |  |  |
| 4 | `mime_type` | VARCHAR(100) |  |  |  |
| 5 | `size` | BIGINT |  |  |  |
| 6 | `storage_path` | VARCHAR(1000) | ✅ |  |  |
| 7 | `hash` | VARCHAR(64) |  |  |  |
| 8 | `status` | VARCHAR(10) | ✅ |  |  |
| 9 | `error_message` | TEXT |  |  |  |
| 10 | `task_id` | VARCHAR(100) |  |  |  |
| 11 | `uploaded_at` | DATETIME |  |  |  |
| 12 | `processed_at` | DATETIME |  |  |  |
| 13 | `created_at` | DATETIME | ✅ |  |  |
| 14 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `embeddings`

- 记录数: **0**
- 列数: 7
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | BIGINT | ✅ |  | 🔑 |
| 1 | `entity_type` | VARCHAR(8) | ✅ |  |  |
| 2 | `entity_id` | VARCHAR(50) | ✅ |  |  |
| 3 | `model` | VARCHAR(100) | ✅ |  |  |
| 4 | `vector_dimension` | INTEGER | ✅ |  |  |
| 5 | `vector_data` | BLOB | ✅ |  |  |
| 6 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `entities`

- 记录数: **1132**
- 列数: 16
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `text` | VARCHAR(500) | ✅ |  |  |
| 2 | `type` | VARCHAR(50) | ✅ |  |  |
| 3 | `canonical_form` | VARCHAR(500) |  |  |  |
| 4 | `description` | TEXT |  |  |  |
| 5 | `metadata` | JSON |  |  |  |
| 6 | `aliases` | JSON |  |  |  |
| 7 | `document_ids` | JSON |  |  |  |
| 8 | `first_mentioned_doc` | VARCHAR(36) |  |  |  |
| 9 | `confidence` | FLOAT |  |  |  |
| 10 | `mention_count` | INTEGER |  |  |  |
| 11 | `name` | VARCHAR(500) |  |  |  |
| 12 | `entity_type` | VARCHAR(50) |  |  |  |
| 13 | `properties` | JSON |  |  |  |
| 14 | `created_at` | DATETIME | ✅ |  |  |
| 15 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `entity_evidences`

- 记录数: **0**
- 列数: 17
- 索引数: 8

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `entity_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `document_id` | INTEGER | ✅ |  |  |
| 3 | `chunk_id` | VARCHAR(100) | ✅ |  |  |
| 4 | `text` | TEXT | ✅ |  |  |
| 5 | `context` | TEXT |  |  |  |
| 6 | `media_type` | VARCHAR(20) |  |  |  |
| 7 | `timestamp_start` | FLOAT |  |  |  |
| 8 | `timestamp_end` | FLOAT |  |  |  |
| 9 | `timestamp_display` | VARCHAR(50) |  |  |  |
| 10 | `speaker` | VARCHAR(200) |  |  |  |
| 11 | `page_number` | INTEGER |  |  |  |
| 12 | `position_start` | INTEGER |  |  |  |
| 13 | `position_end` | INTEGER |  |  |  |
| 14 | `confidence` | FLOAT |  |  |  |
| 15 | `category` | VARCHAR(50) |  |  |  |
| 16 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `entity_relations`

- 记录数: **41**
- 列数: 9
- 索引数: 8

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | BIGINT | ✅ |  | 🔑 |
| 1 | `source_entity_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `target_entity_id` | BIGINT | ✅ |  |  |
| 3 | `relation_type` | VARCHAR(100) | ✅ |  |  |
| 4 | `confidence` | FLOAT |  |  |  |
| 5 | `source_documents` | JSON |  |  |  |
| 6 | `metadata` | JSON |  |  |  |
| 7 | `created_at` | DATETIME | ✅ |  |  |
| 8 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `entity_statistics`

- 记录数: **212**
- 列数: 6
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `entity_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `entity_name` | VARCHAR(255) | ✅ |  |  |
| 4 | `count` | INTEGER |  |  |  |
| 5 | `last_updated` | DATETIME |  |  |  |

---

## 表: `execution_records`

- 记录数: **0**
- 列数: 29
- 索引数: 9

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `execution_type` | VARCHAR(13) | ✅ |  |  |
| 4 | `execution_name` | VARCHAR(200) | ✅ |  |  |
| 5 | `execution_description` | TEXT |  |  |  |
| 6 | `workflow_id` | VARCHAR(36) |  |  |  |
| 7 | `skill_id` | INTEGER |  |  |  |
| 8 | `task_id` | VARCHAR(36) |  |  |  |
| 9 | `input_data` | JSON | ✅ |  |  |
| 10 | `execution_steps` | JSON |  |  |  |
| 11 | `status` | VARCHAR(15) | ✅ |  |  |
| 12 | `output_data` | JSON |  |  |  |
| 13 | `error_message` | TEXT |  |  |  |
| 14 | `error_stack` | TEXT |  |  |  |
| 15 | `duration_seconds` | FLOAT |  |  |  |
| 16 | `cpu_usage_percent` | FLOAT |  |  |  |
| 17 | `memory_usage_mb` | FLOAT |  |  |  |
| 18 | `api_calls_count` | INTEGER |  |  |  |
| 19 | `tokens_used` | INTEGER |  |  |  |
| 20 | `quality_score` | FLOAT |  |  |  |
| 21 | `user_rating` | INTEGER |  |  |  |
| 22 | `user_feedback` | TEXT |  |  |  |
| 23 | `extracted_features` | JSON |  |  |  |
| 24 | `started_at` | DATETIME | ✅ |  |  |
| 25 | `completed_at` | DATETIME |  |  |  |
| 26 | `created_at` | DATETIME | ✅ |  |  |
| 27 | `updated_at` | DATETIME | ✅ |  |  |
| 28 | `extra_metadata` | JSON |  |  |  |

---

## 表: `fact_statements`

- 记录数: **1035**
- 列数: 21
- 索引数: 8

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `fid` | VARCHAR(100) | ✅ |  |  |
| 2 | `source_fid` | VARCHAR(100) |  |  |  |
| 3 | `derived_from_chain` | JSON |  |  |  |
| 4 | `project_id` | INTEGER | ✅ |  |  |
| 5 | `document_id` | INTEGER |  |  |  |
| 6 | `statement_text` | TEXT | ✅ |  |  |
| 7 | `statement_type` | VARCHAR(50) |  |  |  |
| 8 | `start_sec` | FLOAT |  |  |  |
| 9 | `end_sec` | FLOAT |  |  |  |
| 10 | `entity_names` | JSON |  |  |  |
| 11 | `entity_fids` | JSON |  |  |  |
| 12 | `event_summary` | VARCHAR(500) |  |  |  |
| 13 | `event_fid` | VARCHAR(100) |  |  |  |
| 14 | `keywords` | JSON |  |  |  |
| 15 | `context_before` | TEXT |  |  |  |
| 16 | `context_after` | TEXT |  |  |  |
| 17 | `confidence_score` | FLOAT |  |  |  |
| 18 | `importance_score` | FLOAT |  |  |  |
| 19 | `vector_id` | VARCHAR(200) |  |  |  |
| 20 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `feedback_analyses`

- 记录数: **0**
- 列数: 10
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `feedback_loop_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `feedback_type` | VARCHAR(16) | ✅ |  |  |
| 4 | `feedback_source` | VARCHAR(100) | ✅ |  |  |
| 5 | `sentiment_analysis` | JSON |  |  |  |
| 6 | `root_cause_analysis` | JSON |  |  |  |
| 7 | `impact_assessment` | JSON | ✅ |  |  |
| 8 | `actionable_insights` | JSON | ✅ |  |  |
| 9 | `analyzed_at` | DATETIME | ✅ |  |  |

---

## 表: `feedback_loops`

- 记录数: **0**
- 列数: 25
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `execution_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `skill_id` | VARCHAR(36) |  |  |  |
| 3 | `pattern_id` | VARCHAR(36) |  |  |  |
| 4 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 5 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 6 | `execution_context` | JSON | ✅ |  |  |
| 7 | `execution_result` | JSON | ✅ |  |  |
| 8 | `feedback_collected` | JSON | ✅ |  |  |
| 9 | `feedback_sentiment` | VARCHAR(8) | ✅ |  |  |
| 10 | `feedback_score` | FLOAT | ✅ |  |  |
| 11 | `insights_learned` | JSON |  |  |  |
| 12 | `lessons_extracted` | JSON |  |  |  |
| 13 | `improvements_proposed` | JSON |  |  |  |
| 14 | `improvements_applied` | JSON |  |  |  |
| 15 | `loop_completed` | BOOLEAN | ✅ |  |  |
| 16 | `completion_percentage` | FLOAT |  |  |  |
| 17 | `execution_started_at` | DATETIME | ✅ |  |  |
| 18 | `feedback_received_at` | DATETIME |  |  |  |
| 19 | `learning_completed_at` | DATETIME |  |  |  |
| 20 | `improvements_proposed_at` | DATETIME |  |  |  |
| 21 | `loop_closed_at` | DATETIME |  |  |  |
| 22 | `created_at` | DATETIME | ✅ |  |  |
| 23 | `updated_at` | DATETIME | ✅ |  |  |
| 24 | `extra_metadata` | JSON |  |  |  |

---

## 表: `fieldmind_objects`

- 记录数: **852**
- 列数: 10
- 索引数: 0

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `fid` | VARCHAR(100) | ✅ |  |  |
| 2 | `object_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `source_fid` | VARCHAR(100) |  |  |  |
| 4 | `derived_from_chain` | JSON |  |  |  |
| 5 | `storage_info` | JSON | ✅ |  |  |
| 6 | `object_metadata` | JSON |  |  |  |
| 7 | `project_id` | INTEGER | ✅ |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |
| 9 | `updated_at` | DATETIME |  |  |  |

---

## 表: `generated_skills`

- 记录数: **0**
- 列数: 35
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `skill_name` | VARCHAR(200) | ✅ |  |  |
| 2 | `skill_description` | TEXT | ✅ |  |  |
| 3 | `skill_category` | VARCHAR(100) |  |  |  |
| 4 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 5 | `generated_by_user_id` | VARCHAR(36) |  |  |  |
| 6 | `generation_method` | VARCHAR(14) | ✅ |  |  |
| 7 | `source_pattern_id` | VARCHAR(36) |  |  |  |
| 8 | `source_execution_ids` | JSON |  |  |  |
| 9 | `skill_code` | TEXT | ✅ |  |  |
| 10 | `skill_parameters` | JSON | ✅ |  |  |
| 11 | `skill_dependencies` | JSON |  |  |  |
| 12 | `applicable_contexts` | JSON | ✅ |  |  |
| 13 | `quality_score` | FLOAT |  |  |  |
| 14 | `confidence_score` | FLOAT | ✅ |  |  |
| 15 | `complexity_score` | FLOAT |  |  |  |
| 16 | `test_cases_passed` | INTEGER |  |  |  |
| 17 | `test_cases_total` | INTEGER |  |  |  |
| 18 | `test_success_rate` | FLOAT |  |  |  |
| 19 | `usage_count` | INTEGER | ✅ |  |  |
| 20 | `success_count` | INTEGER | ✅ |  |  |
| 21 | `failure_count` | INTEGER | ✅ |  |  |
| 22 | `avg_execution_time` | FLOAT |  |  |  |
| 23 | `status` | VARCHAR(10) | ✅ |  |  |
| 24 | `is_active` | BOOLEAN | ✅ |  |  |
| 25 | `generated_at` | DATETIME | ✅ |  |  |
| 26 | `tested_at` | DATETIME |  |  |  |
| 27 | `validated_at` | DATETIME |  |  |  |
| 28 | `deployed_at` | DATETIME |  |  |  |
| 29 | `ai_model_used` | VARCHAR(100) |  |  |  |
| 30 | `ai_prompt` | TEXT |  |  |  |
| 31 | `ai_response` | TEXT |  |  |  |
| 32 | `created_at` | DATETIME | ✅ |  |  |
| 33 | `updated_at` | DATETIME | ✅ |  |  |
| 34 | `extra_metadata` | JSON |  |  |  |

---

## 表: `improvement_tasks`

- 记录数: **0**
- 列数: 21
- 索引数: 9

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `feedback_loop_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `skill_id` | VARCHAR(36) |  |  |  |
| 3 | `optimization_id` | VARCHAR(36) |  |  |  |
| 4 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 5 | `task_title` | VARCHAR(200) | ✅ |  |  |
| 6 | `task_description` | TEXT | ✅ |  |  |
| 7 | `improvement_type` | VARCHAR(100) | ✅ |  |  |
| 8 | `priority` | VARCHAR(8) | ✅ |  |  |
| 9 | `expected_impact` | TEXT |  |  |  |
| 10 | `estimated_effort` | VARCHAR(50) |  |  |  |
| 11 | `implementation_plan` | JSON |  |  |  |
| 12 | `status` | VARCHAR(50) | ✅ |  |  |
| 13 | `assigned_to` | VARCHAR(36) |  |  |  |
| 14 | `progress_percentage` | FLOAT |  |  |  |
| 15 | `completion_result` | JSON |  |  |  |
| 16 | `created_at` | DATETIME | ✅ |  |  |
| 17 | `started_at` | DATETIME |  |  |  |
| 18 | `completed_at` | DATETIME |  |  |  |
| 19 | `updated_at` | DATETIME | ✅ |  |  |
| 20 | `extra_metadata` | JSON |  |  |  |

---

## 表: `industry_categories`

- 记录数: **0**
- 列数: 13
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `category_id` | VARCHAR(100) | ✅ |  |  |
| 2 | `name` | VARCHAR(200) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `document_count` | INTEGER | ✅ |  |  |
| 5 | `entity_count` | INTEGER | ✅ |  |  |
| 6 | `overview` | JSON |  |  |  |
| 7 | `detailed_analysis` | JSON |  |  |  |
| 8 | `statistics` | JSON |  |  |  |
| 9 | `trends` | JSON |  |  |  |
| 10 | `created_at` | DATETIME | ✅ |  |  |
| 11 | `updated_at` | DATETIME | ✅ |  |  |
| 12 | `last_analyzed` | DATETIME |  |  |  |

---

## 表: `learning_checkpoints`

- 记录数: **0**
- 列数: 9
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `task_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `checkpoint_name` | VARCHAR(200) | ✅ |  |  |
| 4 | `checkpoint_description` | TEXT |  |  |  |
| 5 | `state_snapshot` | JSON | ✅ |  |  |
| 6 | `can_resume_from` | BOOLEAN |  |  |  |
| 7 | `resume_instructions` | JSON |  |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `learning_insights`

- 记录数: **0**
- 列数: 17
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `task_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `insight_type` | VARCHAR(100) | ✅ |  |  |
| 4 | `insight_title` | VARCHAR(200) | ✅ |  |  |
| 5 | `insight_description` | TEXT | ✅ |  |  |
| 6 | `insight_data` | JSON | ✅ |  |  |
| 7 | `importance_score` | FLOAT | ✅ |  |  |
| 8 | `actionability_score` | FLOAT | ✅ |  |  |
| 9 | `confidence_score` | FLOAT | ✅ |  |  |
| 10 | `suggested_actions` | JSON |  |  |  |
| 11 | `is_reviewed` | BOOLEAN |  |  |  |
| 12 | `is_acted_upon` | BOOLEAN |  |  |  |
| 13 | `action_taken` | JSON |  |  |  |
| 14 | `discovered_at` | DATETIME | ✅ |  |  |
| 15 | `reviewed_at` | DATETIME |  |  |  |
| 16 | `acted_upon_at` | DATETIME |  |  |  |

---

## 表: `learning_logs`

- 记录数: **0**
- 列数: 12
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `learning_source` | VARCHAR(50) | ✅ |  |  |
| 3 | `source_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `learned_content` | JSON | ✅ |  |  |
| 5 | `applied_to_skill` | VARCHAR(36) |  |  |  |
| 6 | `confidence` | FLOAT | ✅ |  |  |
| 7 | `status` | VARCHAR(8) | ✅ |  |  |
| 8 | `user_confirmed` | INTEGER |  |  |  |
| 9 | `user_feedback` | TEXT |  |  |  |
| 10 | `created_at` | DATETIME | ✅ |  |  |
| 11 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `learning_schedules`

- 记录数: **0**
- 列数: 19
- 索引数: 6

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `schedule_name` | VARCHAR(200) | ✅ |  |  |
| 2 | `schedule_description` | TEXT | ✅ |  |  |
| 3 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `task_type` | VARCHAR(23) | ✅ |  |  |
| 5 | `cron_expression` | VARCHAR(100) | ✅ |  |  |
| 6 | `timezone` | VARCHAR(50) |  |  |  |
| 7 | `task_config_template` | JSON | ✅ |  |  |
| 8 | `priority` | VARCHAR(6) | ✅ |  |  |
| 9 | `is_active` | BOOLEAN | ✅ |  |  |
| 10 | `last_run_at` | DATETIME |  |  |  |
| 11 | `next_run_at` | DATETIME |  |  |  |
| 12 | `last_task_id` | VARCHAR(36) |  |  |  |
| 13 | `total_runs` | INTEGER |  |  |  |
| 14 | `successful_runs` | INTEGER |  |  |  |
| 15 | `failed_runs` | INTEGER |  |  |  |
| 16 | `created_at` | DATETIME | ✅ |  |  |
| 17 | `updated_at` | DATETIME | ✅ |  |  |
| 18 | `extra_metadata` | JSON |  |  |  |

---

## 表: `lineage_query_cache`

- 记录数: **0**
- 列数: 9
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `resource_type` | VARCHAR(15) | ✅ |  |  |
| 2 | `resource_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `query_type` | VARCHAR(50) | ✅ |  |  |
| 4 | `depth` | INTEGER | ✅ |  |  |
| 5 | `result` | JSON | ✅ |  |  |
| 6 | `cached_at` | DATETIME | ✅ |  |  |
| 7 | `expires_at` | DATETIME | ✅ |  |  |
| 8 | `hit_count` | INTEGER | ✅ |  |  |

---

## 表: `loop_metrics`

- 记录数: **0**
- 列数: 21
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `period_start` | DATETIME | ✅ |  |  |
| 3 | `period_end` | DATETIME | ✅ |  |  |
| 4 | `total_loops` | INTEGER |  |  |  |
| 5 | `completed_loops` | INTEGER |  |  |  |
| 6 | `avg_loop_duration_hours` | FLOAT |  |  |  |
| 7 | `total_feedback_received` | INTEGER |  |  |  |
| 8 | `positive_feedback_count` | INTEGER |  |  |  |
| 9 | `negative_feedback_count` | INTEGER |  |  |  |
| 10 | `avg_feedback_score` | FLOAT |  |  |  |
| 11 | `insights_generated` | INTEGER |  |  |  |
| 12 | `patterns_discovered` | INTEGER |  |  |  |
| 13 | `lessons_learned` | INTEGER |  |  |  |
| 14 | `improvements_proposed` | INTEGER |  |  |  |
| 15 | `improvements_implemented` | INTEGER |  |  |  |
| 16 | `avg_improvement_impact` | FLOAT |  |  |  |
| 17 | `skill_quality_improvement` | FLOAT |  |  |  |
| 18 | `performance_improvement` | FLOAT |  |  |  |
| 19 | `user_satisfaction_improvement` | FLOAT |  |  |  |
| 20 | `calculated_at` | DATETIME | ✅ |  |  |

---

## 表: `metrics_events`

- 记录数: **0**
- 列数: 7
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `event_type` | VARCHAR(100) | ✅ |  |  |
| 3 | `metric_changes` | JSON | ✅ |  |  |
| 4 | `triggered_by` | VARCHAR(36) |  |  |  |
| 5 | `trigger_context` | JSON |  |  |  |
| 6 | `occurred_at` | DATETIME | ✅ |  |  |

---

## 表: `metrics_snapshots`

- 记录数: **0**
- 列数: 18
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `snapshot_date` | DATETIME | ✅ |  |  |
| 3 | `files_processed` | INTEGER | ✅ |  |  |
| 4 | `keywords_extracted` | INTEGER | ✅ |  |  |
| 5 | `knowledge_nodes` | INTEGER | ✅ |  |  |
| 6 | `knowledge_edges` | INTEGER | ✅ |  |  |
| 7 | `reports_generated` | INTEGER | ✅ |  |  |
| 8 | `accuracy_rate` | FLOAT | ✅ |  |  |
| 9 | `completion_rate` | FLOAT | ✅ |  |  |
| 10 | `avg_workflow_duration` | FLOAT | ✅ |  |  |
| 11 | `total_workflows` | INTEGER | ✅ |  |  |
| 12 | `successful_workflows` | INTEGER | ✅ |  |  |
| 13 | `failed_workflows` | INTEGER | ✅ |  |  |
| 14 | `total_time_saved` | FLOAT | ✅ |  |  |
| 15 | `efficiency_multiplier` | FLOAT | ✅ |  |  |
| 16 | `metrics_data` | JSON |  |  |  |
| 17 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `object_relations`

- 记录数: **997**
- 列数: 11
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `from_fid` | VARCHAR(100) | ✅ |  |  |
| 2 | `to_fid` | VARCHAR(100) | ✅ |  |  |
| 3 | `relation_type` | VARCHAR(50) | ✅ |  |  |
| 4 | `confidence` | FLOAT |  |  |  |
| 5 | `strength` | FLOAT |  |  |  |
| 6 | `evidence_fids` | JSON |  |  |  |
| 7 | `relation_data` | JSON |  |  |  |
| 8 | `project_id` | INTEGER | ✅ |  |  |
| 9 | `created_at` | DATETIME | ✅ |  |  |
| 10 | `discovered_at` | DATETIME |  |  |  |

---

## 表: `optimization_recommendations`

- 记录数: **0**
- 列数: 17
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `skill_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `recommendation_type` | VARCHAR(12) | ✅ |  |  |
| 4 | `recommendation_title` | VARCHAR(200) | ✅ |  |  |
| 5 | `recommendation_description` | TEXT | ✅ |  |  |
| 6 | `analysis_data` | JSON | ✅ |  |  |
| 7 | `suggested_solution` | JSON | ✅ |  |  |
| 8 | `priority_score` | FLOAT | ✅ |  |  |
| 9 | `potential_improvement` | FLOAT |  |  |  |
| 10 | `is_accepted` | BOOLEAN |  |  |  |
| 11 | `is_applied` | BOOLEAN |  |  |  |
| 12 | `related_optimization_id` | VARCHAR(36) |  |  |  |
| 13 | `generated_at` | DATETIME | ✅ |  |  |
| 14 | `accepted_at` | DATETIME |  |  |  |
| 15 | `applied_at` | DATETIME |  |  |  |
| 16 | `extra_metadata` | JSON |  |  |  |

---

## 表: `pattern_clusters`

- 记录数: **0**
- 列数: 12
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `cluster_name` | VARCHAR(200) | ✅ |  |  |
| 2 | `cluster_description` | TEXT | ✅ |  |  |
| 3 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `centroid_features` | JSON | ✅ |  |  |
| 5 | `member_pattern_ids` | JSON | ✅ |  |  |
| 6 | `member_count` | INTEGER | ✅ |  |  |
| 7 | `avg_confidence` | FLOAT |  |  |  |
| 8 | `avg_success_rate` | FLOAT |  |  |  |
| 9 | `created_at` | DATETIME | ✅ |  |  |
| 10 | `updated_at` | DATETIME | ✅ |  |  |
| 11 | `extra_metadata` | JSON |  |  |  |

---

## 表: `pattern_library`

- 记录数: **0**
- 列数: 28
- 索引数: 6

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `pattern_name` | VARCHAR(200) | ✅ |  |  |
| 2 | `pattern_type` | VARCHAR(14) | ✅ |  |  |
| 3 | `pattern_description` | TEXT | ✅ |  |  |
| 4 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 5 | `discovered_by_user_id` | VARCHAR(36) |  |  |  |
| 6 | `pattern_definition` | JSON | ✅ |  |  |
| 7 | `pattern_features` | JSON | ✅ |  |  |
| 8 | `applicable_scenarios` | JSON | ✅ |  |  |
| 9 | `detection_count` | INTEGER | ✅ |  |  |
| 10 | `usage_count` | INTEGER | ✅ |  |  |
| 11 | `success_count` | INTEGER | ✅ |  |  |
| 12 | `failure_count` | INTEGER | ✅ |  |  |
| 13 | `confidence_score` | FLOAT | ✅ |  |  |
| 14 | `avg_success_rate` | FLOAT |  |  |  |
| 15 | `avg_quality_score` | FLOAT |  |  |  |
| 16 | `avg_duration_seconds` | FLOAT |  |  |  |
| 17 | `source_execution_ids` | JSON | ✅ |  |  |
| 18 | `source_pattern_id` | VARCHAR(36) |  |  |  |
| 19 | `status` | VARCHAR(10) | ✅ |  |  |
| 20 | `validated_at` | DATETIME |  |  |  |
| 21 | `activated_at` | DATETIME |  |  |  |
| 22 | `deprecated_at` | DATETIME |  |  |  |
| 23 | `first_detected_at` | DATETIME | ✅ |  |  |
| 24 | `last_used_at` | DATETIME |  |  |  |
| 25 | `created_at` | DATETIME | ✅ |  |  |
| 26 | `updated_at` | DATETIME | ✅ |  |  |
| 27 | `extra_metadata` | JSON |  |  |  |

---

## 表: `pattern_matches`

- 记录数: **0**
- 列数: 12
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `pattern_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `execution_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 5 | `match_score` | FLOAT | ✅ |  |  |
| 6 | `match_reason` | JSON | ✅ |  |  |
| 7 | `was_applied` | INTEGER | ✅ |  |  |
| 8 | `application_result` | VARCHAR(50) |  |  |  |
| 9 | `application_feedback` | TEXT |  |  |  |
| 10 | `matched_at` | DATETIME | ✅ |  |  |
| 11 | `applied_at` | DATETIME |  |  |  |

---

## 表: `performance_metrics`

- 记录数: **0**
- 列数: 16
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `skill_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `execution_id` | VARCHAR(36) |  |  |  |
| 3 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `execution_time` | FLOAT | ✅ |  |  |
| 5 | `cpu_usage_percent` | FLOAT |  |  |  |
| 6 | `memory_usage_mb` | FLOAT |  |  |  |
| 7 | `api_calls_count` | INTEGER |  |  |  |
| 8 | `tokens_used` | INTEGER |  |  |  |
| 9 | `success` | BOOLEAN | ✅ |  |  |
| 10 | `quality_score` | FLOAT |  |  |  |
| 11 | `error_type` | VARCHAR(100) |  |  |  |
| 12 | `input_size` | INTEGER |  |  |  |
| 13 | `output_size` | INTEGER |  |  |  |
| 14 | `complexity_level` | VARCHAR(50) |  |  |  |
| 15 | `measured_at` | DATETIME | ✅ |  |  |

---

## 表: `permissions`

- 记录数: **0**
- 列数: 11
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `code` | VARCHAR(100) | ✅ |  |  |
| 2 | `display_name` | VARCHAR(200) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `resource_type` | VARCHAR(15) | ✅ |  |  |
| 5 | `action` | VARCHAR(6) | ✅ |  |  |
| 6 | `scope` | JSON |  |  |  |
| 7 | `is_system` | BOOLEAN | ✅ |  |  |
| 8 | `is_active` | BOOLEAN | ✅ |  |  |
| 9 | `created_at` | DATETIME | ✅ |  |  |
| 10 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `processing_tasks`

- 记录数: **0**
- 列数: 12
- 索引数: 7

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(100) | ✅ |  | 🔑 |
| 1 | `document_id` | VARCHAR(50) | ✅ |  |  |
| 2 | `task_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `status` | VARCHAR(7) | ✅ |  |  |
| 4 | `progress` | INTEGER |  |  |  |
| 5 | `result` | JSON |  |  |  |
| 6 | `error` | TEXT |  |  |  |
| 7 | `retry_count` | INTEGER |  |  |  |
| 8 | `started_at` | DATETIME |  |  |  |
| 9 | `completed_at` | DATETIME |  |  |  |
| 10 | `created_at` | DATETIME | ✅ |  |  |
| 11 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `project_activity_logs`

- 记录数: **0**
- 列数: 8
- 索引数: 6

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER |  |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `user_id` | INTEGER | ✅ |  |  |
| 3 | `action` | VARCHAR(50) | ✅ |  |  |
| 4 | `target_type` | VARCHAR(50) |  |  |  |
| 5 | `target_id` | INTEGER |  |  |  |
| 6 | `details` | TEXT |  |  |  |
| 7 | `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

---

## 表: `project_chat_messages`

- 记录数: **0**
- 列数: 8
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `session_id` | INTEGER | ✅ |  |  |
| 2 | `role` | VARCHAR(20) | ✅ |  |  |
| 3 | `content` | TEXT | ✅ |  |  |
| 4 | `thinking_process` | TEXT |  |  |  |
| 5 | `sources` | JSON |  |  |  |
| 6 | `extra_data` | JSON |  |  |  |
| 7 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `project_chat_sessions`

- 记录数: **0**
- 列数: 9
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `name` | VARCHAR(200) | ✅ |  |  |
| 3 | `document_ids` | JSON |  |  |  |
| 4 | `config` | JSON |  |  |  |
| 5 | `message_count` | INTEGER |  |  |  |
| 6 | `created_at` | DATETIME | ✅ |  |  |
| 7 | `updated_at` | DATETIME |  |  |  |
| 8 | `last_message_at` | DATETIME |  |  |  |

---

## 表: `project_contexts`

- 记录数: **0**
- 列数: 12
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `name` | VARCHAR(200) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `level` | INTEGER |  |  |  |
| 5 | `parent_id` | INTEGER |  |  |  |
| 6 | `keywords` | JSON |  |  |  |
| 7 | `document_ids` | JSON |  |  |  |
| 8 | `entities` | JSON |  |  |  |
| 9 | `timeline_events` | JSON |  |  |  |
| 10 | `created_at` | DATETIME | ✅ |  |  |
| 11 | `updated_at` | DATETIME |  |  |  |

---

## 表: `project_document_assets`

- 记录数: **368**
- 列数: 9
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `document_id` | INTEGER | ✅ |  |  |
| 2 | `asset_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `content` | TEXT |  |  |  |
| 4 | `storage_path` | VARCHAR(1000) |  |  |  |
| 5 | `asset_metadata` | JSON |  |  |  |
| 6 | `status` | VARCHAR(30) | ✅ |  |  |
| 7 | `created_at` | DATETIME | ✅ |  |  |
| 8 | `updated_at` | DATETIME |  |  |  |

---

## 表: `project_document_tags`

- 记录数: **461**
- 列数: 7
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `document_id` | INTEGER | ✅ |  |  |
| 2 | `name` | VARCHAR(100) | ✅ |  |  |
| 3 | `category` | VARCHAR(50) | ✅ |  |  |
| 4 | `source` | VARCHAR(50) | ✅ |  |  |
| 5 | `confidence` | INTEGER |  |  |  |
| 6 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `project_documents`

- 记录数: **36**
- 列数: 26
- 索引数: 6

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `filename` | VARCHAR(500) | ✅ |  |  |
| 3 | `original_filename` | VARCHAR(500) | ✅ |  |  |
| 4 | `file_type` | VARCHAR(50) | ✅ |  |  |
| 5 | `file_path` | VARCHAR(1000) | ✅ |  |  |
| 6 | `file_size` | INTEGER |  |  |  |
| 7 | `file_hash` | VARCHAR(64) |  |  |  |
| 8 | `mime_type` | VARCHAR(150) |  |  |  |
| 9 | `text_content` | TEXT |  |  |  |
| 10 | `summary` | TEXT |  |  |  |
| 11 | `vector_collection` | VARCHAR(200) |  |  |  |
| 12 | `chunk_count` | INTEGER |  |  |  |
| 13 | `entities` | JSON |  |  |  |
| 14 | `keywords` | JSON |  |  |  |
| 15 | `extracted_entities` | JSON |  |  |  |
| 16 | `auto_clusters` | JSON |  |  |  |
| 17 | `data_profile` | JSON |  |  |  |
| 18 | `extra_data` | JSON |  |  |  |
| 19 | `status` | VARCHAR(50) |  |  |  |
| 20 | `processing_progress` | INTEGER |  |  |  |
| 21 | `error_message` | TEXT |  |  |  |
| 22 | `word_count` | INTEGER |  |  |  |
| 23 | `created_at` | DATETIME | ✅ |  |  |
| 24 | `processed_at` | DATETIME |  |  |  |
| 25 | `updated_at` | DATETIME |  |  |  |

---

## 表: `project_invites`

- 记录数: **0**
- 列数: 10
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER |  |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `invite_code` | VARCHAR(100) | ✅ |  |  |
| 3 | `role` | VARCHAR(20) | ✅ |  |  |
| 4 | `created_by` | INTEGER | ✅ |  |  |
| 5 | `expires_at` | TIMESTAMP | ✅ |  |  |
| 6 | `is_used` | BOOLEAN |  | 0 |  |
| 7 | `used_by` | INTEGER |  |  |  |
| 8 | `used_at` | TIMESTAMP |  |  |  |
| 9 | `created_at` | TIMESTAMP |  | CURRENT_TIMESTAMP |  |

---

## 表: `project_members`

- 记录数: **0**
- 列数: 8
- 索引数: 8

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `role_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `is_active` | BOOLEAN | ✅ |  |  |
| 5 | `joined_at` | DATETIME | ✅ |  |  |
| 6 | `invited_by` | VARCHAR(36) |  |  |  |
| 7 | `note` | TEXT |  |  |  |

---

## 表: `project_memories`

- 记录数: **0**
- 列数: 13
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `memory_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `content` | TEXT | ✅ |  |  |
| 4 | `summary` | TEXT |  |  |  |
| 5 | `vector_id` | VARCHAR(200) |  |  |  |
| 6 | `source_type` | VARCHAR(50) |  |  |  |
| 7 | `source_id` | VARCHAR(200) |  |  |  |
| 8 | `extra_data` | JSON |  |  |  |
| 9 | `access_count` | INTEGER |  |  |  |
| 10 | `relevance_score` | INTEGER |  |  |  |
| 11 | `created_at` | DATETIME | ✅ |  |  |
| 12 | `last_accessed_at` | DATETIME |  |  |  |

---

## 表: `project_metrics`

- 记录数: **0**
- 列数: 18
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `files_processed` | INTEGER | ✅ |  |  |
| 3 | `keywords_extracted` | INTEGER | ✅ |  |  |
| 4 | `knowledge_nodes` | INTEGER | ✅ |  |  |
| 5 | `knowledge_edges` | INTEGER | ✅ |  |  |
| 6 | `reports_generated` | INTEGER | ✅ |  |  |
| 7 | `accuracy_rate` | FLOAT | ✅ |  |  |
| 8 | `completion_rate` | FLOAT | ✅ |  |  |
| 9 | `avg_workflow_duration` | FLOAT | ✅ |  |  |
| 10 | `total_workflows` | INTEGER | ✅ |  |  |
| 11 | `successful_workflows` | INTEGER | ✅ |  |  |
| 12 | `failed_workflows` | INTEGER | ✅ |  |  |
| 13 | `total_time_saved` | FLOAT | ✅ |  |  |
| 14 | `efficiency_multiplier` | FLOAT | ✅ |  |  |
| 15 | `detailed_metrics` | JSON |  |  |  |
| 16 | `last_updated` | DATETIME | ✅ |  |  |
| 17 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `projects`

- 记录数: **1**
- 列数: 17
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `name` | VARCHAR(200) | ✅ |  |  |
| 2 | `description` | TEXT |  |  |  |
| 3 | `settings` | JSON |  |  |  |
| 4 | `document_count` | INTEGER |  |  |  |
| 5 | `context_count` | INTEGER |  |  |  |
| 6 | `chat_session_count` | INTEGER |  |  |  |
| 7 | `entity_count` | INTEGER |  |  |  |
| 8 | `keyword_count` | INTEGER |  |  |  |
| 9 | `total_words` | INTEGER |  |  |  |
| 10 | `total_chunks` | INTEGER |  |  |  |
| 11 | `owner_id` | VARCHAR(36) | ✅ |  |  |
| 12 | `is_archived` | BOOLEAN |  |  |  |
| 13 | `status` | VARCHAR(50) |  |  |  |
| 14 | `created_at` | DATETIME | ✅ |  |  |
| 15 | `updated_at` | DATETIME |  |  |  |
| 16 | `last_activity_at` | DATETIME |  |  |  |

### 示例数据（前3条）

| id | name | description | settings | document_count | context_count | chat_session_count | entity_count | keyword_count | total_words | total_chunks | owner_id | is_archived | status | created_at | updated_at | last_activity_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 测试项目 | 端到端测试项目 | {"stats": {"total_documents": 36, "completed_do... | 36 | 0 | 0 | 1089 | 0 | 171796 | 0 | 6410a3e8-6b21-4c73-91e1-34441ce3448f | 0 | active | 2026-08-22 11:34:45.696769 | 2026-08-27 04:33:39 | 2026-08-27 04:33:39 |

---

## 表: `quality_reports`

- 记录数: **0**
- 列数: 7
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | BIGINT | ✅ |  | 🔑 |
| 1 | `document_id` | VARCHAR(50) | ✅ |  |  |
| 2 | `check_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `score` | FLOAT |  |  |  |
| 4 | `issues` | JSON |  |  |  |
| 5 | `recommendations` | JSON |  |  |  |
| 6 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `reports`

- 记录数: **0**
- 列数: 16
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `task_id` | VARCHAR(100) |  |  |  |
| 2 | `title` | VARCHAR(500) | ✅ |  |  |
| 3 | `report_type` | VARCHAR(8) | ✅ |  |  |
| 4 | `status` | VARCHAR(10) | ✅ |  |  |
| 5 | `progress` | INTEGER | ✅ |  |  |
| 6 | `config` | JSON |  |  |  |
| 7 | `data_sources` | JSON |  |  |  |
| 8 | `content` | JSON |  |  |  |
| 9 | `file_path` | VARCHAR(500) |  |  |  |
| 10 | `file_format` | VARCHAR(20) |  |  |  |
| 11 | `file_size` | VARCHAR(50) |  |  |  |
| 12 | `download_url` | VARCHAR(500) |  |  |  |
| 13 | `error_message` | TEXT |  |  |  |
| 14 | `created_at` | DATETIME | ✅ |  |  |
| 15 | `completed_at` | DATETIME |  |  |  |

---

## 表: `resource_ownership`

- 记录数: **0**
- 列数: 6
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `resource_type` | VARCHAR(15) | ✅ |  |  |
| 2 | `resource_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `owner_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `project_id` | VARCHAR(36) |  |  |  |
| 5 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `role_permissions`

- 记录数: **0**
- 列数: 3
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `role_id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `permission_id` | VARCHAR(36) | ✅ |  | 🔑 |
| 2 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `roles`

- 记录数: **0**
- 列数: 12
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `name` | VARCHAR(100) | ✅ |  |  |
| 2 | `display_name` | VARCHAR(200) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `is_system` | BOOLEAN | ✅ |  |  |
| 5 | `is_default` | BOOLEAN | ✅ |  |  |
| 6 | `project_id` | VARCHAR(36) |  |  |  |
| 7 | `priority` | INTEGER | ✅ |  |  |
| 8 | `is_active` | BOOLEAN | ✅ |  |  |
| 9 | `created_at` | DATETIME | ✅ |  |  |
| 10 | `updated_at` | DATETIME | ✅ |  |  |
| 11 | `created_by` | VARCHAR(36) |  |  |  |

---

## 表: `scheduled_task_executions`

- 记录数: **0**
- 列数: 7
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `task_id` | INTEGER | ✅ |  |  |
| 2 | `started_at` | DATETIME | ✅ |  |  |
| 3 | `completed_at` | DATETIME |  |  |  |
| 4 | `status` | VARCHAR(20) |  |  |  |
| 5 | `result` | JSON |  |  |  |
| 6 | `error_message` | TEXT |  |  |  |

---

## 表: `scheduled_tasks`

- 记录数: **0**
- 列数: 14
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `task_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | INTEGER |  |  |  |
| 3 | `name` | VARCHAR(200) | ✅ |  |  |
| 4 | `description` | TEXT |  |  |  |
| 5 | `task_type` | VARCHAR(50) | ✅ |  |  |
| 6 | `cron_expression` | VARCHAR(100) | ✅ |  |  |
| 7 | `is_active` | BOOLEAN |  |  |  |
| 8 | `config` | JSON |  |  |  |
| 9 | `created_at` | DATETIME | ✅ |  |  |
| 10 | `updated_at` | DATETIME |  |  |  |
| 11 | `last_run_at` | DATETIME |  |  |  |
| 12 | `next_run_at` | DATETIME |  |  |  |
| 13 | `created_by` | INTEGER |  |  |  |

---

## 表: `skill_optimizations`

- 记录数: **0**
- 列数: 26
- 索引数: 6

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `skill_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `triggered_by_user_id` | VARCHAR(36) |  |  |  |
| 4 | `optimization_type` | VARCHAR(12) | ✅ |  |  |
| 5 | `optimization_title` | VARCHAR(200) | ✅ |  |  |
| 6 | `optimization_description` | TEXT | ✅ |  |  |
| 7 | `identified_issues` | JSON | ✅ |  |  |
| 8 | `proposed_changes` | JSON | ✅ |  |  |
| 9 | `before_metrics` | JSON |  |  |  |
| 10 | `after_metrics` | JSON |  |  |  |
| 11 | `improvement_percentage` | FLOAT |  |  |  |
| 12 | `is_effective` | BOOLEAN |  |  |  |
| 13 | `validation_score` | FLOAT |  |  |  |
| 14 | `ab_test_data` | JSON |  |  |  |
| 15 | `status` | VARCHAR(9) | ✅ |  |  |
| 16 | `proposed_at` | DATETIME | ✅ |  |  |
| 17 | `tested_at` | DATETIME |  |  |  |
| 18 | `validated_at` | DATETIME |  |  |  |
| 19 | `applied_at` | DATETIME |  |  |  |
| 20 | `reverted_at` | DATETIME |  |  |  |
| 21 | `can_revert` | BOOLEAN |  |  |  |
| 22 | `revert_reason` | TEXT |  |  |  |
| 23 | `created_at` | DATETIME | ✅ |  |  |
| 24 | `updated_at` | DATETIME | ✅ |  |  |
| 25 | `extra_metadata` | JSON |  |  |  |

---

## 表: `skill_test_results`

- 记录数: **0**
- 列数: 11
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `skill_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `test_case_name` | VARCHAR(200) | ✅ |  |  |
| 4 | `test_input` | JSON | ✅ |  |  |
| 5 | `expected_output` | JSON |  |  |  |
| 6 | `actual_output` | JSON |  |  |  |
| 7 | `test_passed` | BOOLEAN | ✅ |  |  |
| 8 | `error_message` | TEXT |  |  |  |
| 9 | `execution_time` | FLOAT |  |  |  |
| 10 | `tested_at` | DATETIME | ✅ |  |  |

---

## 表: `skill_validation_feedback`

- 记录数: **0**
- 列数: 9
- 索引数: 4

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `skill_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `is_approved` | BOOLEAN | ✅ |  |  |
| 5 | `validation_rating` | INTEGER |  |  |  |
| 6 | `feedback_text` | TEXT |  |  |  |
| 7 | `improvement_suggestions` | JSON |  |  |  |
| 8 | `validated_at` | DATETIME | ✅ |  |  |

---

## 表: `skill_validations`

- 记录数: **0**
- 列数: 11
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `skill_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `syntax_check` | BOOLEAN |  |  |  |
| 3 | `dependencies_ok` | BOOLEAN |  |  |  |
| 4 | `test_passed` | BOOLEAN |  |  |  |
| 5 | `can_activate` | BOOLEAN |  |  |  |
| 6 | `errors` | JSON |  |  |  |
| 7 | `warnings` | JSON |  |  |  |
| 8 | `test_output` | TEXT |  |  |  |
| 9 | `execution_time` | VARCHAR(50) |  |  |  |
| 10 | `validated_at` | DATETIME | ✅ |  |  |

---

## 表: `skills`

- 记录数: **0**
- 列数: 17
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `name` | VARCHAR(200) | ✅ |  |  |
| 2 | `description` | TEXT |  |  |  |
| 3 | `version` | VARCHAR(50) | ✅ |  |  |
| 4 | `status` | VARCHAR(10) | ✅ |  |  |
| 5 | `category` | VARCHAR(13) | ✅ |  |  |
| 6 | `file_path` | VARCHAR(500) | ✅ |  |  |
| 7 | `file_size` | VARCHAR(50) |  |  |  |
| 8 | `file_hash` | VARCHAR(64) |  |  |  |
| 9 | `can_be_applied` | BOOLEAN | ✅ |  |  |
| 10 | `validation_result` | JSON |  |  |  |
| 11 | `author` | VARCHAR(200) |  |  |  |
| 12 | `dependencies` | JSON |  |  |  |
| 13 | `config` | JSON |  |  |  |
| 14 | `created_at` | DATETIME | ✅ |  |  |
| 15 | `updated_at` | DATETIME | ✅ |  |  |
| 16 | `last_tested` | DATETIME |  |  |  |

---

## 表: `source_files`

- 记录数: **0**
- 列数: 15
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `file_name` | VARCHAR(500) | ✅ |  |  |
| 3 | `file_type` | VARCHAR(50) | ✅ |  |  |
| 4 | `file_path` | TEXT | ✅ |  |  |
| 5 | `file_size` | INTEGER |  |  |  |
| 6 | `file_hash` | VARCHAR(64) | ✅ |  |  |
| 7 | `uploaded_by` | VARCHAR(36) | ✅ |  |  |
| 8 | `uploaded_at` | DATETIME | ✅ |  |  |
| 9 | `extracted_content` | JSON |  |  |  |
| 10 | `is_processed` | INTEGER | ✅ |  |  |
| 11 | `processed_at` | DATETIME |  |  |  |
| 12 | `is_active` | INTEGER | ✅ |  |  |
| 13 | `deleted_at` | DATETIME |  |  |  |
| 14 | `extra_metadata` | JSON |  |  |  |

---

## 表: `source_verifications`

- 记录数: **0**
- 列数: 6
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `statement_source_id` | INTEGER | ✅ |  |  |
| 2 | `verified_by` | VARCHAR(36) |  |  |  |
| 3 | `status` | VARCHAR(20) | ✅ |  |  |
| 4 | `notes` | TEXT |  |  |  |
| 5 | `created_at` | DATETIME |  |  |  |

---

## 表: `statement_sources`

- 记录数: **0**
- 列数: 10
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `statement_id` | INTEGER | ✅ |  |  |
| 2 | `source_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `source_chunk_id` | INTEGER |  |  |  |
| 4 | `source_document_id` | INTEGER |  |  |  |
| 5 | `position_info` | JSON |  |  |  |
| 6 | `relevance_score` | FLOAT |  |  |  |
| 7 | `confidence_score` | FLOAT |  |  |  |
| 8 | `quoted_text` | TEXT |  |  |  |
| 9 | `created_at` | DATETIME |  |  |  |

---

## 表: `structured_insights`

- 记录数: **1125**
- 列数: 18
- 索引数: 8

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `document_id` | INTEGER | ✅ |  |  |
| 2 | `project_id` | INTEGER | ✅ |  |  |
| 3 | `chunk_index` | INTEGER | ✅ |  |  |
| 4 | `original_text` | TEXT | ✅ |  |  |
| 5 | `cleaned_text` | TEXT | ✅ |  |  |
| 6 | `topics` | VARCHAR(255) |  |  |  |
| 7 | `auto_cluster_id` | INTEGER |  |  |  |
| 8 | `auto_topic_name` | VARCHAR(255) |  |  |  |
| 9 | `dynamic_tags` | JSON |  |  |  |
| 10 | `persons` | TEXT |  |  |  |
| 11 | `locations` | TEXT |  |  |  |
| 12 | `start_time` | FLOAT |  |  |  |
| 13 | `end_time` | FLOAT |  |  |  |
| 14 | `word_count` | INTEGER |  |  |  |
| 15 | `extra_metadata` | JSON |  |  |  |
| 16 | `created_at` | DATETIME |  |  |  |
| 17 | `processed_at` | DATETIME |  |  |  |

---

## 表: `success_patterns`

- 记录数: **0**
- 列数: 18
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `pattern_name` | VARCHAR(200) | ✅ |  |  |
| 2 | `pattern_description` | TEXT | ✅ |  |  |
| 3 | `pattern_type` | VARCHAR(50) | ✅ |  |  |
| 4 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 5 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 6 | `pattern_signature` | JSON | ✅ |  |  |
| 7 | `applicable_contexts` | JSON | ✅ |  |  |
| 8 | `occurrence_count` | INTEGER | ✅ |  |  |
| 9 | `success_count` | INTEGER | ✅ |  |  |
| 10 | `confidence_score` | FLOAT | ✅ |  |  |
| 11 | `avg_quality_score` | FLOAT |  |  |  |
| 12 | `source_execution_ids` | JSON | ✅ |  |  |
| 13 | `first_observed_at` | DATETIME | ✅ |  |  |
| 14 | `last_observed_at` | DATETIME | ✅ |  |  |
| 15 | `created_at` | DATETIME | ✅ |  |  |
| 16 | `updated_at` | DATETIME | ✅ |  |  |
| 17 | `extra_metadata` | JSON |  |  |  |

---

## 表: `tags`

- 记录数: **0**
- 列数: 6
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | BIGINT | ✅ |  | 🔑 |
| 1 | `name` | VARCHAR(100) | ✅ |  |  |
| 2 | `category` | VARCHAR(50) |  |  |  |
| 3 | `color` | VARCHAR(7) |  |  |  |
| 4 | `description` | TEXT |  |  |  |
| 5 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `timeline_events`

- 记录数: **0**
- 列数: 13
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `date` | DATETIME | ✅ |  |  |
| 2 | `title` | VARCHAR(500) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `category` | VARCHAR(100) |  |  |  |
| 5 | `entities` | JSON |  |  |  |
| 6 | `document_ids` | JSON |  |  |  |
| 7 | `location` | JSON |  |  |  |
| 8 | `source` | VARCHAR(200) |  |  |  |
| 9 | `confidence` | FLOAT |  |  |  |
| 10 | `tags` | JSON |  |  |  |
| 11 | `created_at` | DATETIME | ✅ |  |  |
| 12 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `topic_statistics`

- 记录数: **9**
- 列数: 5
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | INTEGER | ✅ |  | 🔑 |
| 1 | `project_id` | INTEGER | ✅ |  |  |
| 2 | `topic` | VARCHAR(50) | ✅ |  |  |
| 3 | `count` | INTEGER |  |  |  |
| 4 | `last_updated` | DATETIME |  |  |  |

---

## 表: `user_analysis_dimensions`

- 记录数: **0**
- 列数: 10
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `project_id` | VARCHAR(36) | ✅ |  |  |
| 3 | `dimension_name` | VARCHAR(200) | ✅ |  |  |
| 4 | `description` | TEXT |  |  |  |
| 5 | `keywords` | JSON | ✅ |  |  |
| 6 | `priority` | INTEGER | ✅ |  |  |
| 7 | `vector_config` | JSON |  |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |
| 9 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `user_annotations`

- 记录数: **0**
- 列数: 13
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `resource_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `resource_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `project_id` | VARCHAR(36) |  |  |  |
| 5 | `annotation_type` | VARCHAR(9) | ✅ |  |  |
| 6 | `content` | TEXT | ✅ |  |  |
| 7 | `position` | JSON |  |  |  |
| 8 | `tags` | JSON |  |  |  |
| 9 | `highlighted_text` | TEXT |  |  |  |
| 10 | `learning_status` | VARCHAR(8) | ✅ |  |  |
| 11 | `created_at` | DATETIME | ✅ |  |  |
| 12 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `user_feeding_sessions`

- 记录数: **0**
- 列数: 9
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `session_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `content` | TEXT | ✅ |  |  |
| 4 | `structured_data` | JSON |  |  |  |
| 5 | `generated_skill_id` | VARCHAR(36) |  |  |  |
| 6 | `is_confirmed` | INTEGER | ✅ |  |  |
| 7 | `confirmed_at` | DATETIME |  |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `user_roles`

- 记录数: **0**
- 列数: 5
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `user_id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `role_id` | VARCHAR(36) | ✅ |  | 🔑 |
| 2 | `project_id` | VARCHAR(36) |  |  |  |
| 3 | `created_at` | DATETIME | ✅ |  |  |
| 4 | `created_by` | VARCHAR(36) |  |  |  |

---

## 表: `user_taggings`

- 记录数: **0**
- 列数: 10
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `entity_type` | VARCHAR(50) | ✅ |  |  |
| 3 | `entity_id` | VARCHAR(36) | ✅ |  |  |
| 4 | `project_id` | VARCHAR(36) |  |  |  |
| 5 | `tags` | JSON | ✅ |  |  |
| 6 | `categories` | JSON |  |  |  |
| 7 | `learning_status` | VARCHAR(8) | ✅ |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |
| 9 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `user_thinking_patterns`

- 记录数: **0**
- 列数: 10
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `user_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `pattern_type` | VARCHAR(12) | ✅ |  |  |
| 3 | `pattern_content` | JSON | ✅ |  |  |
| 4 | `frequency` | INTEGER | ✅ |  |  |
| 5 | `confidence` | FLOAT | ✅ |  |  |
| 6 | `learned_from` | JSON |  |  |  |
| 7 | `applied_to_skills` | JSON |  |  |  |
| 8 | `last_updated` | DATETIME | ✅ |  |  |
| 9 | `created_at` | DATETIME | ✅ |  |  |

---

## 表: `users`

- 记录数: **1**
- 列数: 9
- 索引数: 5

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `email` | VARCHAR(255) | ✅ |  |  |
| 2 | `username` | VARCHAR(100) | ✅ |  |  |
| 3 | `hashed_password` | VARCHAR(255) | ✅ |  |  |
| 4 | `role` | VARCHAR(10) | ✅ |  |  |
| 5 | `is_active` | BOOLEAN | ✅ |  |  |
| 6 | `created_at` | DATETIME | ✅ |  |  |
| 7 | `updated_at` | DATETIME | ✅ |  |  |
| 8 | `last_login` | DATETIME |  |  |  |

### 示例数据（前3条）

| id | email | username | hashed_password | role | is_active | created_at | updated_at | last_login |
|---|---|---|---|---|---|---|---|---|
| 6410a3e8-6b21-4c73-91e1-34441ce3448f | test@example.com | test_user | test_hash | RESEARCHER | 1 | 2026-08-22 11:34:45.693411 | 2026-08-22 11:34:45.693415 | NULL |

---

## 表: `value_exhibitions`

- 记录数: **0**
- 列数: 11
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `task_type` | VARCHAR(100) | ✅ |  |  |
| 2 | `display_name` | VARCHAR(200) | ✅ |  |  |
| 3 | `display_icon` | VARCHAR(50) |  |  |  |
| 4 | `display_order` | INTEGER | ✅ |  |  |
| 5 | `unit_value` | JSON | ✅ |  |  |
| 6 | `calculation_formula` | TEXT |  |  |  |
| 7 | `description_template` | TEXT |  |  |  |
| 8 | `is_active` | INTEGER | ✅ |  |  |
| 9 | `created_at` | DATETIME | ✅ |  |  |
| 10 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `workflow_executions`

- 记录数: **0**
- 列数: 18
- 索引数: 1

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `workflow_id` | VARCHAR(36) |  |  |  |
| 2 | `project_id` | INTEGER |  |  |  |
| 3 | `project_name` | VARCHAR(200) |  |  |  |
| 4 | `input_data` | JSON |  |  |  |
| 5 | `status` | VARCHAR(50) |  |  |  |
| 6 | `current_step` | INTEGER |  |  |  |
| 7 | `total_steps` | INTEGER | ✅ |  |  |
| 8 | `step_results` | JSON |  |  |  |
| 9 | `output_data` | JSON |  |  |  |
| 10 | `error_message` | TEXT |  |  |  |
| 11 | `duration_seconds` | FLOAT |  |  |  |
| 12 | `start_time` | DATETIME |  |  |  |
| 13 | `end_time` | DATETIME |  |  |  |
| 14 | `executed_by` | VARCHAR(36) |  |  |  |
| 15 | `task_id` | VARCHAR(100) |  |  |  |
| 16 | `created_at` | DATETIME | ✅ |  |  |
| 17 | `updated_at` | DATETIME |  |  |  |

---

## 表: `workflow_steps`

- 记录数: **0**
- 列数: 17
- 索引数: 3

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `execution_id` | VARCHAR(36) | ✅ |  |  |
| 2 | `step_name` | VARCHAR(20) | ✅ |  |  |
| 3 | `step_order` | INTEGER | ✅ |  |  |
| 4 | `step_display_name` | VARCHAR(200) | ✅ |  |  |
| 5 | `status` | VARCHAR(9) | ✅ |  |  |
| 6 | `input_data` | JSON |  |  |  |
| 7 | `output_data` | JSON |  |  |  |
| 8 | `started_at` | DATETIME |  |  |  |
| 9 | `completed_at` | DATETIME |  |  |  |
| 10 | `duration_seconds` | FLOAT |  |  |  |
| 11 | `error_message` | TEXT |  |  |  |
| 12 | `error_stack` | TEXT |  |  |  |
| 13 | `retry_count` | INTEGER | ✅ |  |  |
| 14 | `extra_metadata` | JSON |  |  |  |
| 15 | `created_at` | DATETIME | ✅ |  |  |
| 16 | `updated_at` | DATETIME | ✅ |  |  |

---

## 表: `workflow_templates`

- 记录数: **0**
- 列数: 11
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `name` | VARCHAR(200) | ✅ |  |  |
| 2 | `display_name` | VARCHAR(200) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `steps_definition` | JSON | ✅ |  |  |
| 5 | `is_default` | INTEGER | ✅ |  |  |
| 6 | `is_active` | INTEGER | ✅ |  |  |
| 7 | `usage_count` | INTEGER | ✅ |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |
| 9 | `updated_at` | DATETIME | ✅ |  |  |
| 10 | `created_by` | VARCHAR(36) |  |  |  |

---

## 表: `workload_calculations`

- 记录数: **0**
- 列数: 10
- 索引数: 2

### 字段结构

| # | 字段名 | 类型 | 非空 | 默认值 | 主键 |
|---|--------|------|------|--------|------|
| 0 | `id` | VARCHAR(36) | ✅ |  | 🔑 |
| 1 | `task_type` | VARCHAR(100) | ✅ |  |  |
| 2 | `task_display_name` | VARCHAR(200) | ✅ |  |  |
| 3 | `description` | TEXT |  |  |  |
| 4 | `manual_hours_per_task` | FLOAT | ✅ |  |  |
| 5 | `task_count` | INTEGER | ✅ |  |  |
| 6 | `total_manual_hours` | FLOAT | ✅ |  |  |
| 7 | `is_active` | INTEGER | ✅ |  |  |
| 8 | `created_at` | DATETIME | ✅ |  |  |
| 9 | `updated_at` | DATETIME | ✅ |  |  |

---
