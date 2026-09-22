# Week 3 - Day 3: document_chunks 表改造分析
执行日期: 2026-09-13

---

## 📊 现有表结构分析

### 当前 document_chunks 表字段（41 个字段）

#### ✅ 已有的基础字段
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| id | INTEGER | 主键 | ✅ 已有 |
| chunk_id | VARCHAR(100) | 统一 ID | ✅ 已有 |
| document_id | INTEGER | 文档 ID | ✅ 已有 |
| project_id | INTEGER | 项目 ID | ✅ 已有 |
| chunk_index | INTEGER | 块索引 | ✅ 已有 |
| text | TEXT | 文本内容 | ✅ 已有 |
| chunk_text | TEXT | 块文本 | ✅ 已有（重复？）|
| text_length | INTEGER | 文本长度 | ✅ 已有 |
| chunk_size | INTEGER | 块大小 | ✅ 已有（重复？）|
| token_count | INTEGER | token 数量 | ✅ 已有 |

#### ✅ 已有的位置信息
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| start_pos | INTEGER | 起始位置 | ✅ 已有 |
| end_pos | INTEGER | 结束位置 | ✅ 已有 |
| page_number | INTEGER | 页码 | ✅ 已有 |
| chapter_title | VARCHAR(500) | 章节标题 | ✅ 已有 |
| section_title | VARCHAR(500) | 节标题 | ✅ 已有 |
| subsection_title | VARCHAR(500) | 子节标题 | ✅ 已有 |

#### ✅ 已有的说话人信息
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| speaker | VARCHAR(100) | 说话人 | ✅ 已有 |
| timestamp_start | INTEGER | 时间戳开始 | ✅ 已有 |
| timestamp_end | INTEGER | 时间戳结束 | ✅ 已有 |

#### ✅ 已有的向量化信息
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| embedding | JSON | 向量 | ✅ 已有 |
| embedding_model | VARCHAR(100) | 模型名称 | ✅ 已有 |
| vectorized_at | DATETIME | 向量化时间 | ✅ 已有 |

#### ✅ 已有的实体与分类
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| key_entities | JSON | 关键实体 | ✅ 已有 |
| domain_tags | JSON | 领域标签 | ✅ 已有 |
| primary_domain | VARCHAR(100) | 主要领域 | ✅ 已有 |

#### ✅ 已有的上下文信息
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| temporal_context | VARCHAR(200) | 时间上下文 | ✅ 已有 |
| spatial_context | VARCHAR(200) | 空间上下文 | ✅ 已有 |
| chunk_role | VARCHAR(50) | 块角色 | ✅ 已有 |
| chunk_summary | TEXT | 块摘要 | ✅ 已有 |

#### ✅ 已有的增强信息
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| enhanced_text | TEXT | 增强文本 | ✅ 已有 |
| enhancement_confidence | INTEGER | 增强置信度 | ✅ 已有 |

#### ✅ 已有的表格信息
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| is_table_chunk | INTEGER | 是否表格块 | ✅ 已有 |
| table_sheet_name | VARCHAR(200) | 表格sheet名 | ✅ 已有 |
| table_row_range | VARCHAR(50) | 表格行范围 | ✅ 已有 |
| structured_data | JSON | 结构化数据 | ✅ 已有 |

#### ✅ 已有的其他字段
| 字段 | 类型 | 说明 | 状态 |
|------|------|------|------|
| prev_chunk_id | VARCHAR(100) | 前一个块ID | ✅ 已有 |
| next_chunk_id | VARCHAR(100) | 下一个块ID | ✅ 已有 |
| chunk_metadata | JSON | 块元数据 | ✅ 已有 |
| metadata | JSON | 元数据 | ✅ 已有（重复？）|
| total_chunks | INTEGER | 总块数 | ✅ 已有 |
| created_at | DATETIME | 创建时间 | ✅ 已有 |

---

## 🆕 需要添加的字段（根据设计方案）

### 高优先级字段（P0）

#### 1. 说话人详细信息
```sql
-- speaker 字段已存在，但需要增强
ALTER TABLE document_chunks ADD COLUMN speaker_id VARCHAR(50);  -- 说话人实体ID
ALTER TABLE document_chunks ADD COLUMN speaker_role VARCHAR(100);  -- 说话人角色
ALTER TABLE document_chunks ADD COLUMN speaker_confidence FLOAT;  -- 识别置信度
```

#### 2. 情感量化指标
```sql
ALTER TABLE document_chunks ADD COLUMN emotion_polarity FLOAT;  -- 情感极性 [-1, 1]
ALTER TABLE document_chunks ADD COLUMN emotion_intensity FLOAT;  -- 情感强度 [0, 1]
ALTER TABLE document_chunks ADD COLUMN subjectivity FLOAT;  -- 主观性 [0, 1]
ALTER TABLE document_chunks ADD COLUMN sentiment_label VARCHAR(50);  -- positive/negative/neutral
```

#### 3. 维度分类（增强）
```sql
-- primary_domain 和 domain_tags 已存在，但需要标准化
ALTER TABLE document_chunks ADD COLUMN dimension_category VARCHAR(100);  -- 维度类别
ALTER TABLE document_chunks ADD COLUMN dimension_sub_category VARCHAR(100);  -- 维度子类别
ALTER TABLE document_chunks ADD COLUMN dimension_tags JSON;  -- 维度标签数组
ALTER TABLE document_chunks ADD COLUMN dimension_confidence FLOAT;  -- 分类置信度
```

#### 4. 关键词提取
```sql
ALTER TABLE document_chunks ADD COLUMN keywords JSON;  -- 关键词数组
ALTER TABLE document_chunks ADD COLUMN entities_count INTEGER DEFAULT 0;  -- 实体数量
```

#### 5. 质量指标
```sql
ALTER TABLE document_chunks ADD COLUMN quality_score FLOAT;  -- 综合质量评分
ALTER TABLE document_chunks ADD COLUMN completeness_score FLOAT;  -- 完整性评分
ALTER TABLE document_chunks ADD COLUMN relevance_score FLOAT;  -- 相关性评分
ALTER TABLE document_chunks ADD COLUMN has_context BOOLEAN DEFAULT 1;  -- 是否有上下文
```

#### 6. 同步状态
```sql
ALTER TABLE document_chunks ADD COLUMN synced_to_chromadb BOOLEAN DEFAULT 0;
ALTER TABLE document_chunks ADD COLUMN chromadb_synced_at DATETIME;
ALTER TABLE document_chunks ADD COLUMN sync_version INTEGER DEFAULT 1;
ALTER TABLE document_chunks ADD COLUMN updated_at DATETIME;  -- 更新时间
```

---

## 📋 字段映射关系

### 已有字段 vs 设计方案

| 设计方案字段 | 现有字段 | 状态 | 操作 |
|-------------|---------|------|------|
| chunk_id | chunk_id | ✅ 已有 | 保持 |
| text | text, chunk_text | ✅ 已有（重复）| 统一使用 text |
| text_length | text_length, chunk_size | ✅ 已有（重复）| 统一使用 text_length |
| word_count | token_count | ✅ 已有 | 重命名？|
| speaker | speaker | ✅ 已有 | 增强 |
| speaker_id | - | ❌ 缺失 | 新增 |
| speaker_role | - | ❌ 缺失 | 新增 |
| speaker_confidence | - | ❌ 缺失 | 新增 |
| emotion_polarity | - | ❌ 缺失 | 新增 |
| emotion_intensity | - | ❌ 缺失 | 新增 |
| subjectivity | - | ❌ 缺失 | 新增 |
| sentiment_label | - | ❌ 缺失 | 新增 |
| dimension_category | primary_domain | ⚠️ 类似 | 标准化 |
| dimension_sub_category | - | ❌ 缺失 | 新增 |
| dimension_tags | domain_tags | ⚠️ 类似 | 标准化 |
| dimension_confidence | - | ❌ 缺失 | 新增 |
| keywords | - | ❌ 缺失 | 新增 |
| entities | key_entities | ⚠️ 类似 | 标准化 |
| entities_count | - | ❌ 缺失 | 新增 |
| quality_score | - | ❌ 缺失 | 新增 |
| completeness_score | - | ❌ 缺失 | 新增 |
| relevance_score | - | ❌ 缺失 | 新增 |
| embedding_id | - | ❌ 缺失 | 新增（与 chunk_id 相同）|
| synced_to_chromadb | - | ❌ 缺失 | 新增 |
| chromadb_synced_at | - | ❌ 缺失 | 新增 |

---

## 🔧 改造策略

### 策略 1: 最小改动（推荐）
**原则**: 充分利用现有字段，只添加缺失的关键字段

**操作**:
1. 保留所有现有字段
2. 添加 16 个新字段（情感、质量、同步状态）
3. 创建字段映射函数，统一访问接口
4. 逐步迁移数据到标准化格式

**优势**:
- ✅ 风险低，不破坏现有数据
- ✅ 向后兼容
- ✅ 可逐步迁移

**劣势**:
- ⚠️ 字段较多（57 个）
- ⚠️ 有重复字段

### 策略 2: 完全重构（高风险）
**原则**: 创建新表，完全按设计方案实现

**操作**:
1. 创建 chunks_v2 新表
2. 迁移所有数据到新表
3. 删除旧表，重命名新表

**优势**:
- ✅ 结构清晰
- ✅ 无冗余字段

**劣势**:
- ❌ 风险高
- ❌ 需要修改大量代码
- ❌ 可能破坏现有功能

### ✅ 推荐：策略 1（最小改动）

---

## 📝 具体实施计划

### 步骤 1: 添加新字段（不破坏现有数据）

```sql
-- 说话人增强
ALTER TABLE document_chunks ADD COLUMN speaker_id VARCHAR(50);
ALTER TABLE document_chunks ADD COLUMN speaker_role VARCHAR(100);
ALTER TABLE document_chunks ADD COLUMN speaker_confidence FLOAT;

-- 情感量化
ALTER TABLE document_chunks ADD COLUMN emotion_polarity FLOAT;
ALTER TABLE document_chunks ADD COLUMN emotion_intensity FLOAT;
ALTER TABLE document_chunks ADD COLUMN subjectivity FLOAT;
ALTER TABLE document_chunks ADD COLUMN sentiment_label VARCHAR(50);

-- 维度分类增强
ALTER TABLE document_chunks ADD COLUMN dimension_category VARCHAR(100);
ALTER TABLE document_chunks ADD COLUMN dimension_sub_category VARCHAR(100);
ALTER TABLE document_chunks ADD COLUMN dimension_tags JSON;
ALTER TABLE document_chunks ADD COLUMN dimension_confidence FLOAT;

-- 关键词
ALTER TABLE document_chunks ADD COLUMN keywords JSON;
ALTER TABLE document_chunks ADD COLUMN entities_count INTEGER DEFAULT 0;

-- 质量指标
ALTER TABLE document_chunks ADD COLUMN quality_score FLOAT;
ALTER TABLE document_chunks ADD COLUMN completeness_score FLOAT;
ALTER TABLE document_chunks ADD COLUMN relevance_score FLOAT;
ALTER TABLE document_chunks ADD COLUMN has_context INTEGER DEFAULT 1;

-- 同步状态
ALTER TABLE document_chunks ADD COLUMN synced_to_chromadb INTEGER DEFAULT 0;
ALTER TABLE document_chunks ADD COLUMN chromadb_synced_at DATETIME;
ALTER TABLE document_chunks ADD COLUMN sync_version INTEGER DEFAULT 1;
ALTER TABLE document_chunks ADD COLUMN updated_at DATETIME;
ALTER TABLE document_chunks ADD COLUMN embedding_id VARCHAR(100);
```

### 步骤 2: 创建字段映射函数

```python
def get_chunk_unified_fields(chunk_row: Dict) -> Dict:
    """
    将数据库记录映射到统一的字段格式
    
    处理字段重复和命名不一致的问题
    """
    return {
        # 基础字段
        "chunk_id": chunk_row.get("chunk_id"),
        "text": chunk_row.get("text") or chunk_row.get("chunk_text"),
        "text_length": chunk_row.get("text_length") or chunk_row.get("chunk_size"),
        "word_count": chunk_row.get("token_count"),
        
        # 说话人
        "speaker": chunk_row.get("speaker"),
        "speaker_id": chunk_row.get("speaker_id"),
        "speaker_role": chunk_row.get("speaker_role"),
        "speaker_confidence": chunk_row.get("speaker_confidence"),
        
        # 情感
        "emotion_polarity": chunk_row.get("emotion_polarity"),
        "emotion_intensity": chunk_row.get("emotion_intensity"),
        "subjectivity": chunk_row.get("subjectivity"),
        "sentiment_label": chunk_row.get("sentiment_label"),
        
        # 维度（优先使用新字段）
        "dimension_category": chunk_row.get("dimension_category") or chunk_row.get("primary_domain"),
        "dimension_tags": chunk_row.get("dimension_tags") or chunk_row.get("domain_tags"),
        
        # 实体（优先使用新字段）
        "entities": chunk_row.get("key_entities"),
        "entities_count": chunk_row.get("entities_count"),
        
        # 关键词
        "keywords": chunk_row.get("keywords"),
        
        # 质量
        "quality_score": chunk_row.get("quality_score"),
        "completeness_score": chunk_row.get("completeness_score"),
        "relevance_score": chunk_row.get("relevance_score"),
        
        # 向量化
        "embedding": chunk_row.get("embedding"),
        "embedding_id": chunk_row.get("embedding_id") or chunk_row.get("chunk_id"),
        
        # 同步状态
        "synced_to_chromadb": chunk_row.get("synced_to_chromadb"),
        "chromadb_synced_at": chunk_row.get("chromadb_synced_at"),
    }
```

### 步骤 3: 创建索引

```sql
-- 为新字段创建索引
CREATE INDEX idx_chunks_speaker_id ON document_chunks(speaker_id);
CREATE INDEX idx_chunks_dimension_category ON document_chunks(dimension_category);
CREATE INDEX idx_chunks_sentiment ON document_chunks(emotion_polarity);
CREATE INDEX idx_chunks_quality ON document_chunks(quality_score);
CREATE INDEX idx_chunks_synced ON document_chunks(synced_to_chromadb);
CREATE INDEX idx_chunks_embedding_id ON document_chunks(embedding_id);
```

---

## 📊 改造后的表结构

### 总字段数: 57 个
- 原有字段: 41 个 ✅
- 新增字段: 23 个 🆕
- 废弃字段: 7 个（标记但保留）⚠️

### 字段分类
1. **基础信息** (10 个)
2. **位置信息** (9 个)
3. **说话人信息** (6 个) - 增强 ✅
4. **情感量化** (4 个) - 新增 🆕
5. **维度分类** (7 个) - 增强 ✅
6. **实体与关键词** (4 个) - 增强 ✅
7. **质量指标** (4 个) - 新增 🆕
8. **向量化** (4 个)
9. **表格信息** (4 个)
10. **同步状态** (5 个) - 新增 🆕

---

## ✅ 验收标准

### 结构验收
- [ ] 所有新字段已添加
- [ ] 所有索引已创建
- [ ] 字段映射函数正常工作
- [ ] 无数据丢失

### 功能验收
- [ ] 情感分析数据可以写入
- [ ] 维度分类数据可以写入
- [ ] 质量评分可以计算
- [ ] 同步状态可以追踪

### 性能验收
- [ ] 查询性能未下降
- [ ] 索引正常工作
- [ ] 插入性能可接受

---

**下一步**: 执行字段添加脚本
