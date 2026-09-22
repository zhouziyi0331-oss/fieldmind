# P0 优化：统一 ID 体系与数据主权架构

生成时间: 2026-09-13 16:10:12

---

## 一、统一 ID 规范

### 1.1 ID 格式

**格式**: `{prefix}_{uuid12}`

**示例**:
- 项目: `proj_a1b2c3d4e5f6`
- 文档: `doc_1234567890ab`
- Chunk: `chk_fedcba098765`
- 实体: `ent_aabbccddee00`

### 1.2 实体类型前缀

| 实体类型 | 前缀 | 示例 |
|---------|------|------|
| 项目 | `proj` | `proj_a1b2c3d4e5f6` |
| 用户 | `user` | `user_123456789abc` |
| 文档 | `doc` | `doc_abcdef012345` |
| Chunk | `chk` | `chk_111222333444` |
| 实体 | `ent` | `ent_aabbccddee00` |
| 关系 | `rel` | `rel_112233445566` |
| Skill | `skl` | `skl_aabbcc112233` |
| 模式 | `pat` | `pat_123abc456def` |

### 1.3 规则

1. ✅ **所有数据库使用相同 ID**
   - PostgreSQL、Neo4j、ChromaDB、Redis 都用同一套 ID
   - 不允许各数据库自行生成 ID

2. ✅ **PostgreSQL 是 ID 唯一生成源**
   - 所有 ID 在 PostgreSQL 生成
   - 其他数据库从 PostgreSQL 同步

3. ✅ **ID 永不改变**
   - ID 一旦生成，永久有效
   - 不随数据迁移、重建而改变

4. ✅ **ID 可验证**
   - 通过正则表达式验证格式
   - 可从 ID 提取实体类型

---

## 二、数据主权架构

### 2.1 四层架构

```
┌──────────────────────────────────────────────────────────────┐
│                     数据主权架构                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  主权层 (PostgreSQL)                               │    │
│  │  - 所有结构化数据的唯一写入口                       │    │
│  │  - 生成全局唯一 ID                                  │    │
│  │  - 发布数据变更事件                                 │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   │ (事件驱动同步)                         │
│  ┌────────────────▼───────────────────────────────────┐    │
│  │  索引层                                             │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  Neo4j (图查询)                              │  │    │
│  │  │  - 从 PostgreSQL 同步实体+关系               │  │    │
│  │  │  - 提供图遍历和路径查询                      │  │    │
│  │  │  - 只读，不创建数据                          │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  ChromaDB (向量检索)                         │  │    │
│  │  │  - 从 PostgreSQL 同步 chunk+embedding        │  │    │
│  │  │  - 提供语义相似度搜索                        │  │    │
│  │  │  - 只读，不创建数据                          │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │  Redis (缓存)                                │  │    │
│  │  │  - 缓存高频查询结果                          │  │    │
│  │  │  - 有明确过期时间                            │  │    │
│  │  │  - 可随时清空重建                            │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 核心原则

| 原则 | 说明 |
|------|------|
| **单一主权** | 所有写操作只在 PostgreSQL |
| **统一 ID** | 四库使用相同的 ID 体系 |
| **事件驱动** | PostgreSQL 变更通过事件同步 |
| **可重建** | 索引层可随时从主权层重建 |
| **最终一致性** | 允许短暂延迟，保证最终一致 |

### 2.3 数据流

**写入流程**:
```
Client → API
    ↓
API → PostgreSQL (唯一写入)
    ↓
PostgreSQL → Event Bus
    ↓
Event Bus → Neo4j/ChromaDB/Redis (异步同步)
```

**查询流程**:
```
Client → API
    ↓
API → Redis (检查缓存)
    ↓ (缓存未命中)
Query Orchestrator
    ├─→ PostgreSQL (主数据)
    ├─→ Neo4j (图关系)
    └─→ ChromaDB (相似度)
    ↓
合并结果 → Redis (写缓存) → Client
```

---

## 三、增强的表结构

### 3.1 Chunks 表（增强版）

新增字段让 chunk 从诞生起就携带完整信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| `speaker` | VARCHAR(255) | 说话人标识 |
| `speaker_role` | VARCHAR(100) | 说话人角色 |
| `timestamp_start` | FLOAT | 音频起始时间 |
| `timestamp_end` | FLOAT | 结束时间 |
| `sentiment_polarity` | FLOAT | 情感极性 [-1, 1] |
| `sentiment_subjectivity` | FLOAT | 主观性 [0, 1] |
| `emotion_scores` | JSONB | 多维情绪分数 |
| `dimension_category` | VARCHAR(100) | 一级维度 |
| `dimension_sub_category` | VARCHAR(100) | 二级维度 |
| `entities` | JSONB | 预标注实体 |
| `keywords` | JSONB | 关键词列表 |

**乘法效应**:
- 切分时同步完成：说话人标注、情绪量化、实体识别、维度归类
- 任何一个 chunk，都能直接回答：谁说的、什么情绪、属于什么维度、涉及什么实体

### 3.2 Entities 表（增强版）

新增字段让实体携带生命周期信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| `mention_count` | INTEGER | 提及次数 |
| `sentiment_avg` | FLOAT | 平均情感值 |
| `first_appearance` | TIMESTAMP | 首次出现时间 |
| `last_appearance` | TIMESTAMP | 最后出现时间 |
| `related_entities` | JSONB | 关联实体列表 |
| `related_events` | JSONB | 关联事件列表 |
| `timeline` | JSONB | 时间线 |

**乘法效应**:
- 实体节点不只是"名字"，而是"名字 + 提及次数 + 情绪变化 + 关联事件"

### 3.3 Skills 表（增强版）

新增字段让 Skill 从分析中自动生长：

| 字段 | 类型 | 说明 |
|------|------|------|
| `source_project_id` | VARCHAR(20) | 从哪个项目生成 |
| `source_data` | JSONB | 基于哪些数据 |
| `auto_generated` | BOOLEAN | 是否自动生成 |
| `version` | VARCHAR(20) | 版本号 |
| `parent_skill_id` | VARCHAR(20) | 上一版本 |
| `usage_count` | INTEGER | 使用次数 |
| `success_count` | INTEGER | 成功次数 |
| `feedback_score` | FLOAT | 用户反馈评分 |

**乘法效应**:
- Skill 记录来源项目、基于数据、版本号
- 用户反馈自动调整权重

### 3.4 Knowledge Base 表（新增）

组织知识库，报告结论回流：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | VARCHAR(50) | case/template/insight/lesson |
| `title` | VARCHAR(500) | 标题 |
| `content` | TEXT | 内容 |
| `source_project_id` | VARCHAR(20) | 来源项目 |
| `source_report_id` | VARCHAR(20) | 来源报告 |
| `related_skills` | JSONB | 关联 Skill |
| `reuse_count` | INTEGER | 复用次数 |

**乘法效应**:
- 报告结论自动进入知识库
- 新项目自动推荐相似案例、模板、Skill

---

## 四、实施步骤

### Phase 1: ID 统一（1周）

1. ✅ 定义 ID 规范
2. ⏳ 创建 ID 生成器
3. ⏳ 执行 ID 迁移脚本
4. ⏳ 验证四库 ID 一致性

### Phase 2: 表结构升级（1周）

1. ⏳ 升级 chunks 表
2. ⏳ 升级 entities 表
3. ⏳ 升级 skills 表
4. ⏳ 创建 knowledge_base 表

### Phase 3: 数据同步（1周）

1. ⏳ 实现事件总线
2. ⏳ 实现 PostgreSQL → Neo4j 同步
3. ⏳ 实现 PostgreSQL → ChromaDB 同步
4. ⏳ 实现 Redis 缓存策略

### Phase 4: API 收敛（1周）

1. ⏳ 确保所有写操作只通过 PostgreSQL
2. ⏳ 禁止其他库的直接写入
3. ⏳ 实现查询编排器
4. ⏳ 测试数据一致性

---

## 五、验证清单

- [ ] 所有实体 ID 符合统一格式
- [ ] PostgreSQL、Neo4j、ChromaDB、Redis 使用相同 ID
- [ ] 所有写操作只在 PostgreSQL 发生
- [ ] Neo4j 数据与 PostgreSQL 一致
- [ ] ChromaDB 数据与 PostgreSQL 一致
- [ ] Redis 缓存有明确过期时间
- [ ] chunk 携带完整信息（说话人、情绪、维度、实体）
- [ ] entity 携带生命周期信息
- [ ] skill 记录来源和版本
- [ ] knowledge_base 正常运作

---

**FieldMind P0 优化项目**
统一 ID 体系与数据主权架构
Version 1.0
