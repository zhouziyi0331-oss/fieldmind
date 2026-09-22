# FieldMind "1+1>2" 乘法效应架构改造方案

## 📋 改造目标

将 FieldMind 从"功能堆叠"升级为"知识传递"，让每个功能的输出成为下一个功能的"增强输入"，实现 1+1>2 的乘法效应。

---

## 一、诊断报告：当前问题

### 现状：功能堆叠模式

```
上传 → 转录 → 切分 → 量化 → 向量化 → 实体抽取 → 关系抽取 → 知识图谱 → 分析 → 报告
```

### 核心问题

| 现象 | 本质 | 后果 |
|------|------|------|
| 转录完，切分要重新读一遍文本 | 转录的输出没有被切分"理解" | 重复计算，性能浪费 |
| 量化完，知识图谱不知道有量化指标 | 量化结果没有进入图谱的"属性" | 数据孤岛，无法关联分析 |
| 关系抽取完，报告里看不到关系 | 关系结果没有进入报告的"依据" | 分析缺乏依据 |
| 报告生成完，经验没有沉淀 | 报告的输出没有回流到 Skill | 每次从零开始 |
| 新项目开始，一切从零 | 上一个项目的所有积累没有"复用" | 无复利效应 |

---

## 二、核心设计原则

> **每个功能的输出，必须成为下一个功能的"增强输入"，而不是独立数据。**

### 三大原则

1. **信息携带原则** - 数据从诞生那刻起就带全部信息
2. **知识传递原则** - 每个环节的"理解"向下传递
3. **经验沉淀原则** - 所有判断自动回流为可复用资产

---

## 三、四大乘法改造

### 乘法 1：转录 × 切分 × 量化 = "有身份的 chunk"

#### 1.1 Chunk 表完整字段设计

```sql
CREATE TABLE chunks (
    -- ========== 基础字段 ==========
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id VARCHAR(50) UNIQUE NOT NULL,  -- 格式: chk_{uuid}
    document_id UUID NOT NULL REFERENCES documents(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    
    -- ========== 核心内容 ==========
    text TEXT NOT NULL,
    text_length INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    
    -- ========== 时间与位置 ==========
    chunk_index INTEGER NOT NULL,  -- 在文档中的顺序
    timestamp_start FLOAT,  -- 音频/视频的起始时间（秒）
    timestamp_end FLOAT,    -- 音频/视频的结束时间（秒）
    page_number INTEGER,    -- PDF 页码
    position_start INTEGER, -- 在原文中的起始位置
    position_end INTEGER,   -- 在原文中的结束位置
    
    -- ========== 说话人信息（新增）==========
    speaker VARCHAR(200),   -- 说话人名称
    speaker_id UUID REFERENCES entities(id),  -- 说话人实体 ID
    speaker_role VARCHAR(100),  -- 说话人角色（受访者、调研员等）
    speaker_confidence FLOAT,   -- 说话人识别置信度 [0-1]
    
    -- ========== 情感量化指标（新增）==========
    emotion_polarity FLOAT,     -- 情感极性 [-1 到 1]，负=消极，正=积极
    emotion_intensity FLOAT,    -- 情感强度 [0-1]
    subjectivity FLOAT,         -- 主观性 [0-1]，0=客观陈述，1=主观意见
    sentiment_label VARCHAR(50), -- 情感标签：positive/negative/neutral
    
    -- ========== 维度归类（新增）==========
    dimension_category VARCHAR(100),     -- 一级维度：非遗/经济/教育/医疗等
    dimension_sub_category VARCHAR(100), -- 二级维度：山歌传承/手工艺等
    dimension_tags JSONB,                -- 多个维度标签 ["非遗", "传承危机"]
    dimension_confidence FLOAT,          -- 维度分类置信度
    
    -- ========== 关键词与实体（新增）==========
    keywords JSONB,  -- 提取的关键词 ["山歌", "布依族", "传承"]
    entities JSONB,  -- 识别的实体 [{"id": "ent_123", "name": "王大爷", "type": "person"}]
    entities_count INTEGER DEFAULT 0,
    
    -- ========== 主题与分类（新增）==========
    topics JSONB,    -- 主题标签 ["文化传承", "非遗保护"]
    topic_weights JSONB,  -- 主题权重 {"文化传承": 0.8, "非遗保护": 0.6}
    
    -- ========== 质量指标（新增）==========
    quality_score FLOAT,     -- 质量评分 [0-1]
    completeness_score FLOAT, -- 完整性评分
    relevance_score FLOAT,    -- 相关性评分
    has_context BOOLEAN DEFAULT TRUE,  -- 是否有足够上下文
    
    -- ========== 向量化 ==========
    embedding_id VARCHAR(100),  -- ChromaDB 中的向量 ID
    embedding_model VARCHAR(100), -- 使用的嵌入模型
    embedding_version VARCHAR(50), -- 模型版本
    
    -- ========== 关联信息 ==========
    parent_chunk_id UUID REFERENCES chunks(id),  -- 父 chunk（如果是拆分的）
    related_chunks JSONB,  -- 相关 chunk ID 列表
    
    -- ========== 处理状态 ==========
    processing_status VARCHAR(50) DEFAULT 'pending',  -- pending/processing/completed/failed
    processed_at TIMESTAMP,
    
    -- ========== 元数据 ==========
    metadata JSONB,  -- 其他自定义元数据
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_chunks_document ON chunks(document_id);
CREATE INDEX idx_chunks_project ON chunks(project_id);
CREATE INDEX idx_chunks_speaker ON chunks(speaker_id);
CREATE INDEX idx_chunks_dimension ON chunks(dimension_category, dimension_sub_category);
CREATE INDEX idx_chunks_sentiment ON chunks(emotion_polarity);
CREATE INDEX idx_chunks_entities ON chunks USING GIN(entities);
CREATE INDEX idx_chunks_keywords ON chunks USING GIN(keywords);
CREATE INDEX idx_chunks_timestamp ON chunks(timestamp_start, timestamp_end);
```

#### 1.2 Chunk 生成流程改造

**旧流程（三步分离）：**
```
步骤1: 转录 → 纯文本
步骤2: 切分 → chunk + text
步骤3: 量化 → 情感值写入 chunk
步骤4: 实体识别 → 实体写入单独表
```

**新流程（一步完成）：**
```python
def create_enriched_chunk(
    text: str,
    document_id: str,
    audio_segment: Optional[AudioSegment] = None,
    context: Dict = None
) -> EnrichedChunk:
    """
    一次性生成带全部信息的 chunk
    """
    chunk = {
        "chunk_id": f"chk_{uuid.uuid4().hex[:12]}",
        "document_id": document_id,
        "project_id": context.get("project_id"),
        "text": text,
        "text_length": len(text),
        "word_count": len(text.split()),
        "chunk_index": context.get("chunk_index", 0),
    }
    
    # 1️⃣ 如果是音频，同步识别说话人
    if audio_segment:
        speaker_info = identify_speaker(audio_segment)
        chunk.update({
            "speaker": speaker_info["name"],
            "speaker_id": speaker_info["entity_id"],
            "speaker_role": speaker_info["role"],
            "speaker_confidence": speaker_info["confidence"],
            "timestamp_start": audio_segment.start_time,
            "timestamp_end": audio_segment.end_time,
        })
    
    # 2️⃣ 同步进行情感量化
    sentiment = analyze_sentiment(text)
    chunk.update({
        "emotion_polarity": sentiment["polarity"],
        "emotion_intensity": sentiment["intensity"],
        "subjectivity": sentiment["subjectivity"],
        "sentiment_label": sentiment["label"],
    })
    
    # 3️⃣ 同步进行关键词提取
    keywords = extract_keywords(text, top_k=10)
    chunk["keywords"] = keywords
    
    # 4️⃣ 同步进行实体识别
    entities = extract_entities(text)
    chunk["entities"] = [
        {
            "id": ent["id"],
            "name": ent["name"],
            "type": ent["type"],
            "confidence": ent["confidence"]
        }
        for ent in entities
    ]
    chunk["entities_count"] = len(entities)
    
    # 5️⃣ 同步进行维度分类
    dimension = classify_dimension(text, keywords, entities)
    chunk.update({
        "dimension_category": dimension["category"],
        "dimension_sub_category": dimension["sub_category"],
        "dimension_tags": dimension["tags"],
        "dimension_confidence": dimension["confidence"],
    })
    
    # 6️⃣ 同步进行主题识别
    topics = identify_topics(text, context.get("project_topics", []))
    chunk["topics"] = [t["name"] for t in topics]
    chunk["topic_weights"] = {t["name"]: t["weight"] for t in topics}
    
    # 7️⃣ 计算质量指标
    quality = assess_chunk_quality(text, entities, keywords)
    chunk.update({
        "quality_score": quality["overall"],
        "completeness_score": quality["completeness"],
        "relevance_score": quality["relevance"],
        "has_context": quality["has_context"],
    })
    
    # 8️⃣ 生成向量（异步）
    chunk["embedding_id"] = f"emb_{chunk['chunk_id']}"
    chunk["embedding_model"] = "text-embedding-3-large"
    
    # 9️⃣ 设置状态
    chunk["processing_status"] = "completed"
    chunk["processed_at"] = datetime.now()
    
    return chunk
```

#### 1.3 乘法效应

| 功能 | 原来 | 现在 | 效果 |
|------|------|------|------|
| 切分 | 只按字数切 | 按说话人边界 + 语义边界切 | chunk 更连贯 |
| 量化 | 单独一步 | 切分时同步完成 | 节省 30% 处理时间 |
| 实体识别 | 后置处理 | 切分时同步完成 | chunk 自带实体信息 |
| 维度分类 | 手动标注 | 自动分类 + 置信度 | 100% 覆盖 |
| 搜索 | 只能按文本 | 可按说话人、情绪、维度搜索 | 搜索精度提升 50% |
| 分析 | 需要重新读 chunk | chunk 自带所有分析数据 | 分析速度提升 3 倍 |

---

### 乘法 2：实体 × 关系 × 时间线 = "有生命的知识图谱"

#### 2.1 实体表完整字段设计

```sql
CREATE TABLE entities (
    -- ========== 基础字段 ==========
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id VARCHAR(50) UNIQUE NOT NULL,  -- 格式: ent_{uuid}
    project_id UUID NOT NULL REFERENCES projects(id),
    
    -- ========== 实体基本信息 ==========
    name VARCHAR(500) NOT NULL,
    name_normalized VARCHAR(500),  -- 标准化名称
    aliases JSONB,  -- 别名 ["王师傅", "老王"]
    type VARCHAR(100) NOT NULL,  -- person/location/organization/concept/event
    sub_type VARCHAR(100),  -- 细分类型：传承人/村落/非遗项目等
    
    -- ========== 描述与属性 ==========
    description TEXT,
    attributes JSONB,  -- 自定义属性 {"年龄": 68, "职业": "山歌传承人"}
    
    -- ========== 生命周期信息（新增）==========
    mention_count INTEGER DEFAULT 0,  -- 被提及次数
    first_mention_at TIMESTAMP,       -- 首次提及时间
    last_mention_at TIMESTAMP,        -- 最后提及时间
    first_appearance DATE,            -- 首次出现日期（业务时间）
    last_appearance DATE,             -- 最后出现日期（业务时间）
    appearance_frequency JSONB,       -- 时间分布 {"2024-01": 5, "2024-02": 8}
    
    -- ========== 情感轨迹（新增）==========
    sentiment_avg FLOAT,              -- 平均情感值
    sentiment_trend VARCHAR(50),      -- 情感趋势：rising/falling/stable
    sentiment_timeline JSONB,         -- 情感时间线
    /*
    [
        {"date": "2024-01-15", "value": 0.65, "context": "首次访谈"},
        {"date": "2024-03-20", "value": -0.2, "context": "提到传承危机"}
    ]
    */
    
    -- ========== 关联信息（新增）==========
    related_entities JSONB,   -- 关联实体 [{"id": "ent_456", "name": "山歌", "relation": "传承"}]
    related_events JSONB,     -- 关联事件 ["山歌培训班停办", "非遗申报"]
    related_documents JSONB,  -- 关联文档 ID 列表
    related_chunks_count INTEGER DEFAULT 0,
    
    -- ========== 重要性指标（新增）==========
    importance_score FLOAT,   -- 重要性评分 [0-1]
    centrality_score FLOAT,   -- 网络中心性（基于关系数量）
    influence_score FLOAT,    -- 影响力评分
    
    -- ========== 时间线事件（新增）==========
    timeline JSONB,  -- 完整时间线
    /*
    [
        {
            "date": "2024-01-15",
            "event_type": "first_mention",
            "title": "首次提及",
            "context": "访谈山歌传承",
            "chunk_id": "chk_001",
            "sentiment": 0.65
        },
        {
            "date": "2024-03-20",
            "event_type": "sentiment_shift",
            "title": "情绪转折",
            "context": "提到年轻人不学，情绪低落",
            "chunk_id": "chk_045",
            "sentiment": -0.2
        }
    ]
    */
    
    -- ========== 维度归属（新增）==========
    dimensions JSONB,  -- 所属维度 ["非遗", "文化传承"]
    primary_dimension VARCHAR(100),  -- 主要维度
    
    -- ========== 数据来源 ==========
    source_type VARCHAR(100),  -- 来源：manual/auto_extracted/imported
    source_confidence FLOAT,   -- 识别置信度
    verified BOOLEAN DEFAULT FALSE,  -- 是否人工验证
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP,
    
    -- ========== Neo4j 同步 ==========
    neo4j_node_id VARCHAR(100),  -- Neo4j 中的节点 ID
    synced_to_neo4j BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMP,
    
    -- ========== 元数据 ==========
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_entities_project ON entities(project_id);
CREATE INDEX idx_entities_type ON entities(type, sub_type);
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_entities_mentions ON entities(mention_count DESC);
CREATE INDEX idx_entities_importance ON entities(importance_score DESC);
CREATE INDEX idx_entities_sentiment ON entities(sentiment_avg);
CREATE INDEX idx_entities_dimensions ON entities USING GIN(dimensions);
```

#### 2.2 实体自动更新流程

```python
class EntityLifecycleManager:
    """实体生命周期管理器"""
    
    def on_entity_mentioned(self, entity_id: str, chunk: Dict):
        """
        当实体在新的 chunk 中被提及时，自动更新其生命周期信息
        """
        entity = db.query("SELECT * FROM entities WHERE entity_id = %s", entity_id)
        
        # 1️⃣ 更新提及统计
        entity["mention_count"] += 1
        entity["last_mention_at"] = datetime.now()
        
        if not entity["first_mention_at"]:
            entity["first_mention_at"] = datetime.now()
        
        # 2️⃣ 更新业务时间
        chunk_date = extract_date_from_chunk(chunk)
        if chunk_date:
            if not entity["first_appearance"] or chunk_date < entity["first_appearance"]:
                entity["first_appearance"] = chunk_date
            if not entity["last_appearance"] or chunk_date > entity["last_appearance"]:
                entity["last_appearance"] = chunk_date
        
        # 3️⃣ 更新情感轨迹
        if chunk.get("emotion_polarity") is not None:
            # 计算新的平均情感值
            old_avg = entity["sentiment_avg"] or 0
            old_count = entity["mention_count"] - 1
            new_avg = (old_avg * old_count + chunk["emotion_polarity"]) / entity["mention_count"]
            entity["sentiment_avg"] = new_avg
            
            # 添加到情感时间线
            sentiment_timeline = entity.get("sentiment_timeline", [])
            sentiment_timeline.append({
                "date": chunk_date or datetime.now().date(),
                "value": chunk["emotion_polarity"],
                "context": chunk["text"][:100],
                "chunk_id": chunk["chunk_id"]
            })
            entity["sentiment_timeline"] = sentiment_timeline
            
            # 分析情感趋势
            entity["sentiment_trend"] = analyze_sentiment_trend(sentiment_timeline)
        
        # 4️⃣ 更新时间线事件
        timeline = entity.get("timeline", [])
        
        # 检测重要事件
        event = self.detect_event(entity, chunk)
        if event:
            timeline.append({
                "date": chunk_date or datetime.now().date(),
                "event_type": event["type"],
                "title": event["title"],
                "context": chunk["text"][:200],
                "chunk_id": chunk["chunk_id"],
                "sentiment": chunk.get("emotion_polarity")
            })
            entity["timeline"] = timeline
        
        # 5️⃣ 更新关联信息
        if chunk.get("entities"):
            related = entity.get("related_entities", [])
            for ent in chunk["entities"]:
                if ent["id"] != entity_id and ent["id"] not in [r["id"] for r in related]:
                    related.append({
                        "id": ent["id"],
                        "name": ent["name"],
                        "relation": "co_occurrence"  # 可以后续细化
                    })
            entity["related_entities"] = related
        
        # 6️⃣ 更新重要性指标
        entity["importance_score"] = calculate_importance(entity)
        entity["centrality_score"] = calculate_centrality(entity)
        
        # 7️⃣ 保存
        db.execute("UPDATE entities SET ... WHERE entity_id = %s", entity_id)
        
        # 8️⃣ 同步到 Neo4j
        self.sync_to_neo4j(entity)
    
    def detect_event(self, entity: Dict, chunk: Dict) -> Optional[Dict]:
        """检测是否有重要事件"""
        # 首次提及
        if entity["mention_count"] == 1:
            return {
                "type": "first_mention",
                "title": "首次提及"
            }
        
        # 情感转折（变化超过 0.5）
        if len(entity.get("sentiment_timeline", [])) > 0:
            last_sentiment = entity["sentiment_timeline"][-1]["value"]
            current_sentiment = chunk.get("emotion_polarity", 0)
            if abs(current_sentiment - last_sentiment) > 0.5:
                return {
                    "type": "sentiment_shift",
                    "title": "情绪转折"
                }
        
        # 长时间未提及后再次出现
        if entity["last_mention_at"]:
            days_gap = (datetime.now() - entity["last_mention_at"]).days
            if days_gap > 30:
                return {
                    "type": "reappearance",
                    "title": "再次提及"
                }
        
        return None
```

#### 2.3 乘法效应

| 功能 | 原来 | 现在 | 效果 |
|------|------|------|------|
| 实体识别 | 只有名字和类型 | 携带提及次数、情感、时间线 | 实体"活"起来了 |
| 时间线 | 独立页面，手动构建 | 自动生成，嵌入实体 | 零成本获得时间线 |
| 情感分析 | 只有当前情绪 | 有情感轨迹、趋势 | 能看到情绪变化 |
| 关系网络 | 静态关系 | 带时间、情感的动态关系 | 能分析关系演化 |
| 报告生成 | 只能写"王大爷被提及" | 可以写"王大爷的情绪从0.65下降到-0.2" | 报告更有洞察力 |

---

### 乘法 3：分析 × 报告 × Skill = "可复用的判断"

#### 3.1 Skill 表设计

```sql
CREATE TABLE skills (
    -- ========== 基础字段 ==========
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id VARCHAR(50) UNIQUE NOT NULL,  -- 格式: sk_{uuid}
    
    -- ========== Skill 基本信息 ==========
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),  -- analysis/validation/recommendation/automation
    
    -- ========== 触发条件 ==========
    trigger_type VARCHAR(100),  -- dimension/entity_type/keyword/manual
    trigger_conditions JSONB,
    /*
    {
        "dimension": "非遗",
        "keywords": ["传承", "危机"],
        "entity_types": ["person", "concept"]
    }
    */
    
    -- ========== 规则定义 ==========
    rules JSONB,
    /*
    [
        {
            "rule_id": "r001",
            "condition": "传承人平均年龄 > 65",
            "action": "标记为'高风险'",
            "confidence": 0.85,
            "source": "布依族村落项目"
        },
        {
            "rule_id": "r002",
            "condition": "年轻人参与率 < 20%",
            "action": "标记为'传承断层'",
            "confidence": 0.92,
            "source": "布依族村落项目"
        }
    ]
    */
    
    -- ========== 来源追踪（新增）==========
    created_from_project_id UUID REFERENCES projects(id),
    created_from_project_name VARCHAR(200),
    based_on_data JSONB,  -- 基于什么数据生成
    /*
    {
        "entities": ["ent_001", "ent_002"],
        "chunks": ["chk_001", "chk_002"],
        "analysis_results": ["analysis_123"]
    }
    */
    
    -- ========== 版本管理（新增）==========
    version VARCHAR(50) DEFAULT 'v1.0',
    parent_skill_id UUID REFERENCES skills(id),  -- 如果是升级版本
    version_history JSONB,  -- 版本变更历史
    
    -- ========== 使用统计（新增）==========
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    success_rate FLOAT,
    
    -- ========== 用户反馈（新增）==========
    user_feedback JSONB,  -- 用户反馈记录
    avg_rating FLOAT,
    
    -- ========== 权重调整（新增）==========
    rule_weights JSONB,  -- 每条规则的权重（根据反馈调整）
    /*
    {
        "r001": 0.85,  // 初始 confidence
        "r002": 0.95   // 经过 5 次正反馈后提升
    }
    */
    
    -- ========== 适用范围 ==========
    applicable_dimensions JSONB,  -- 适用的维度
    applicable_projects JSONB,    -- 适用的项目类型
    
    -- ========== 状态 ==========
    status VARCHAR(50) DEFAULT 'draft',  -- draft/active/archived
    activated_at TIMESTAMP,
    
    -- ========== 元数据 ==========
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- 索引
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_trigger ON skills(trigger_type);
CREATE INDEX idx_skills_project ON skills(created_from_project_id);
CREATE INDEX idx_skills_usage ON skills(usage_count DESC);
CREATE INDEX idx_skills_success_rate ON skills(success_rate DESC);
```

#### 3.2 Skill 自动生长机制

```python
class SkillGrowthEngine:
    """Skill 自动生长引擎"""
    
    def analyze_and_generate_skill(self, analysis_result: Dict, project: Dict):
        """
        从分析结果中自动提取判断规则，生成 Skill 草稿
        """
        # 1️⃣ 识别分析中的判断逻辑
        judgments = self.extract_judgments(analysis_result)
        
        if not judgments:
            return None
        
        # 2️⃣ 生成 Skill 草稿
        skill = {
            "skill_id": f"sk_{uuid.uuid4().hex[:12]}",
            "name": f"{project['name']} - {analysis_result['dimension']}风险评估",
            "description": f"从{project['name']}项目中自动生成的风险评估规则",
            "category": "analysis",
            "trigger_type": "dimension",
            "trigger_conditions": {
                "dimension": analysis_result["dimension"],
                "keywords": analysis_result.get("keywords", [])
            },
            "rules": judgments,
            "created_from_project_id": project["id"],
            "created_from_project_name": project["name"],
            "based_on_data": {
                "entities": analysis_result.get("entity_ids", []),
                "chunks": analysis_result.get("chunk_ids", []),
                "analysis_id": analysis_result["id"]
            },
            "version": "v1.0",
            "status": "draft",
            "usage_count": 0
        }
        
        # 3️⃣ 计算初始权重
        skill["rule_weights"] = {
            rule["rule_id"]: rule["confidence"]
            for rule in judgments
        }
        
        # 4️⃣ 保存草稿
        db.insert("skills", skill)
        
        # 5️⃣ 通知用户审核
        self.notify_user_for_review(skill)
        
        return skill
    
    def extract_judgments(self, analysis_result: Dict) -> List[Dict]:
        """从分析结果中提取判断规则"""
        judgments = []
        
        # 示例：如果分析结果中有"传承人平均年龄68岁，已属高龄"
        if "传承人" in analysis_result.get("text", ""):
            # 使用 LLM 提取判断逻辑
            prompt = f"""
            从以下分析结论中提取判断规则：
            
            {analysis_result['text']}
            
            输出格式：
            {{
                "condition": "具体条件（如：传承人平均年龄 > 65）",
                "action": "判断结论（如：标记为高风险）",
                "confidence": 0.85
            }}
            """
            
            extracted = llm_extract(prompt)
            
            if extracted:
                judgments.append({
                    "rule_id": f"r{len(judgments)+1:03d}",
                    "condition": extracted["condition"],
                    "action": extracted["action"],
                    "confidence": extracted["confidence"],
                    "source": analysis_result.get("project_name")
                })
        
        return judgments
    
    def apply_skill(self, skill: Dict, context: Dict) -> Dict:
        """应用 Skill 进行判断"""
        results = []
        
        for rule in skill["rules"]:
            # 评估条件
            if self.evaluate_condition(rule["condition"], context):
                # 应用权重
                weight = skill["rule_weights"].get(rule["rule_id"], rule["confidence"])
                
                results.append({
                    "rule_id": rule["rule_id"],
                    "matched": True,
                    "action": rule["action"],
                    "confidence": weight
                })
        
        # 更新使用统计
        db.execute(
            "UPDATE skills SET usage_count = usage_count + 1 WHERE skill_id = %s",
            skill["skill_id"]
        )
        
        return {
            "skill_id": skill["skill_id"],
            "matched_rules": results,
            "overall_confidence": sum(r["confidence"] for r in results) / len(results) if results else 0
        }
    
    def update_from_feedback(self, skill_id: str, feedback: Dict):
        """根据用户反馈更新 Skill 权重"""
        skill = db.query("SELECT * FROM skills WHERE skill_id = %s", skill_id)
        
        if feedback["result"] == "success":
            skill["success_count"] += 1
            # 提升相关规则的权重
            for rule_id in feedback.get("matched_rules", []):
                current_weight = skill["rule_weights"].get(rule_id, 0.5)
                skill["rule_weights"][rule_id] = min(current_weight + 0.05, 1.0)
        else:
            skill["failure_count"] += 1
            # 降低相关规则的权重
            for rule_id in feedback.get("matched_rules", []):
                current_weight = skill["rule_weights"].get(rule_id, 0.5)
                skill["rule_weights"][rule_id] = max(current_weight - 0.05, 0.1)
        
        # 更新成功率
        total = skill["success_count"] + skill["failure_count"]
        skill["success_rate"] = skill["success_count"] / total if total > 0 else 0
        
        # 如果成功率低于 50%，降级为 draft
        if skill["success_rate"] < 0.5 and total > 10:
            skill["status"] = "draft"
        
        db.execute("UPDATE skills SET ... WHERE skill_id = %s", skill_id)
```

#### 3.3 乘法效应

| 功能 | 原来 | 现在 | 效果 |
|------|------|------|------|
| Skill 创建 | 手动编写 | 从分析中自动生成 | 零成本获得 Skill |
| Skill 复用 | 独立存在 | 记录来源项目和数据 | 可追溯 |
| Skill 更新 | 不更新 | 根据反馈自动调整权重 | 越用越准 |
| 新项目 | 从零开始 | 自动推荐相关 Skill | 速度提升 3 倍 |
| 经验沉淀 | 靠人记忆 | 系统自动沉淀 | 100% 保留 |

---

### 乘法 4：报告 × 资产 × 新项目 = "复利效应"

#### 4.1 组织知识库表设计

```sql
CREATE TABLE knowledge_assets (
    -- ========== 基础字段 ==========
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(50) UNIQUE NOT NULL,  -- 格式: ka_{uuid}
    
    -- ========== 资产类型 ==========
    asset_type VARCHAR(100) NOT NULL,  -- report/skill/template/case_study/insight
    
    -- ========== 资产信息 ==========
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content JSONB,  -- 资产的完整内容
    
    -- ========== 来源追踪 ==========
    source_project_id UUID REFERENCES projects(id),
    source_project_name VARCHAR(200),
    source_type VARCHAR(100),  -- auto_generated/manual/imported
    
    -- ========== 分类与标签 ==========
    dimensions JSONB,  -- 维度标签
    keywords JSONB,    -- 关键词
    entities JSONB,    -- 相关实体
    
    -- ========== 适用性 ==========
    applicable_dimensions JSONB,  -- 适用的维度
    applicable_scenarios JSONB,   -- 适用场景
    similarity_threshold FLOAT DEFAULT 0.7,  -- 推荐阈值
    
    -- ========== 使用统计 ==========
    usage_count INTEGER DEFAULT 0,
    reference_count INTEGER DEFAULT 0,  -- 被引用次数
    
    -- ========== 质量评分 ==========
    quality_score FLOAT,
    usefulness_score FLOAT,  -- 用户评价的有用性
    
    -- ========== 向量化 ==========
    embedding_id VARCHAR(100),  -- 用于相似度匹配
    
    -- ========== 元数据 ==========
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_knowledge_assets_type ON knowledge_assets(asset_type);
CREATE INDEX idx_knowledge_assets_project ON knowledge_assets(source_project_id);
CREATE INDEX idx_knowledge_assets_dimensions ON knowledge_assets USING GIN(dimensions);
CREATE INDEX idx_knowledge_assets_usage ON knowledge_assets(usage_count DESC);
```

#### 4.2 报告结论自动回流机制

```python
class KnowledgeAssetManager:
    """知识资产管理器"""
    
    def extract_assets_from_report(self, report: Dict, project: Dict):
        """从报告中提取可复用的知识资产"""
        assets = []
        
        # 1️⃣ 提取核心结论作为 Case Study
        if report.get("conclusions"):
            for conclusion in report["conclusions"]:
                asset = {
                    "asset_id": f"ka_{uuid.uuid4().hex[:12]}",
                    "asset_type": "case_study",
                    "title": f"{project['name']} - {conclusion['title']}",
                    "description": conclusion["summary"],
                    "content": {
                        "full_text": conclusion["full_text"],
                        "evidence": conclusion.get("evidence", []),
                        "data_sources": conclusion.get("data_sources", []),
                        "methodology": conclusion.get("methodology")
                    },
                    "source_project_id": project["id"],
                    "source_project_name": project["name"],
                    "source_type": "auto_generated",
                    "dimensions": project.get("dimensions", []),
                    "keywords": conclusion.get("keywords", []),
                    "entities": conclusion.get("entities", [])
                }
                
                # 生成向量（用于相似度匹配）
                asset["embedding_id"] = self.generate_embedding(
                    asset["title"] + " " + asset["description"]
                )
                
                assets.append(asset)
        
        # 2️⃣ 提取分析方法作为 Template
        if report.get("analysis_method"):
            asset = {
                "asset_id": f"ka_{uuid.uuid4().hex[:12]}",
                "asset_type": "template",
                "title": f"{project['name']} - 分析模板",
                "description": "可复用的分析方法和框架",
                "content": {
                    "method": report["analysis_method"],
                    "steps": report.get("analysis_steps", []),
                    "metrics": report.get("metrics", [])
                },
                "source_project_id": project["id"],
                "source_project_name": project["name"],
                "dimensions": project.get("dimensions", [])
            }
            assets.append(asset)
        
        # 3️⃣ 提取洞察作为 Insight
        if report.get("insights"):
            for insight in report["insights"]:
                asset = {
                    "asset_id": f"ka_{uuid.uuid4().hex[:12]}",
                    "asset_type": "insight",
                    "title": insight["title"],
                    "description": insight["description"],
                    "content": insight,
                    "source_project_id": project["id"],
                    "source_project_name": project["name"],
                    "dimensions": project.get("dimensions", [])
                }
                assets.append(asset)
        
        # 4️⃣ 批量保存
        for asset in assets:
            db.insert("knowledge_assets", asset)
        
        return assets
    
    def recommend_assets_for_new_project(self, project: Dict) -> List[Dict]:
        """为新项目推荐相关知识资产"""
        recommendations = []
        
        # 1️⃣ 基于维度匹配
        dimension_matches = db.query("""
            SELECT *
            FROM knowledge_assets
            WHERE dimensions ?| %s  -- 维度数组有交集
            ORDER BY usage_count DESC, quality_score DESC
            LIMIT 10
        """, project["dimensions"])
        
        # 2️⃣ 基于语义相似度
        project_embedding = self.generate_embedding(
            project["name"] + " " + project["description"]
        )
        
        semantic_matches = self.chromadb.query(
            query_embeddings=[project_embedding],
            n_results=10,
            where={"asset_type": {"$in": ["case_study", "template", "insight"]}}
        )
        
        # 3️⃣ 合并并排序
        all_matches = dimension_matches + [
            db.query("SELECT * FROM knowledge_assets WHERE asset_id = %s", m["id"])
            for m in semantic_matches["ids"][0]
        ]
        
        # 去重并按相关性排序
        seen = set()
        for asset in all_matches:
            if asset["asset_id"] not in seen:
                recommendations.append({
                    "asset": asset,
                    "relevance_score": self.calculate_relevance(asset, project)
                })
                seen.add(asset["asset_id"])
        
        recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return recommendations[:10]
    
    def apply_asset_to_project(self, asset_id: str, project_id: str):
        """将知识资产应用到新项目"""
        asset = db.query("SELECT * FROM knowledge_assets WHERE asset_id = %s", asset_id)
        project = db.query("SELECT * FROM projects WHERE id = %s", project_id)
        
        if asset["asset_type"] == "skill":
            # 挂载 Skill
            db.execute("""
                INSERT INTO project_skills (project_id, skill_id)
                VALUES (%s, %s)
            """, project_id, asset["content"]["skill_id"])
        
        elif asset["asset_type"] == "template":
            # 应用模板
            project["analysis_template"] = asset["content"]
            db.execute("UPDATE projects SET analysis_template = %s WHERE id = %s",
                      asset["content"], project_id)
        
        elif asset["asset_type"] == "case_study":
            # 添加参考案例
            project_references = project.get("reference_cases", [])
            project_references.append({
                "asset_id": asset_id,
                "title": asset["title"],
                "source": asset["source_project_name"]
            })
            db.execute("UPDATE projects SET reference_cases = %s WHERE id = %s",
                      project_references, project_id)
        
        # 更新资产使用统计
        db.execute("""
            UPDATE knowledge_assets
            SET usage_count = usage_count + 1
            WHERE asset_id = %s
        """, asset_id)
```

#### 4.3 复利效应示意

```
项目 A（布依族村落）
    ↓ 生成
┌───────────────────────────────┐
│ 3 份报告                      │
│ 5 个 Skill                    │
│ 1 个分析模板                  │
│ 128 个关键词                  │
│ 15 个 Case Study              │
└───────────────────────────────┘
    ↓ 自动沉淀到
┌───────────────────────────────┐
│    组织知识库                 │
│ - 50 个 Case Study            │
│ - 20 个 Skill                 │
│ - 8 个模板                    │
└───────────────────────────────┘
    ↓ 新项目开始
项目 B（另一个村落）
    ↓ 自动推荐
┌───────────────────────────────┐
│ 推荐：                        │
│ ✓ "布依族村落"模板（匹配度 92%）│
│ ✓ "非遗传承风险评估" Skill    │
│ ✓ 3 个相似案例参考            │
└───────────────────────────────┘
    ↓ 效果
┌───────────────────────────────┐
│ 项目 B 的分析速度提升 3 倍    │
│ 直接复用 5 个 Skill           │
│ 报告质量提升 40%              │
└───────────────────────────────┘
    ↓ 项目 B 完成后
┌───────────────────────────────┐
│ 新发现反哺知识库：            │
│ - Skill 升级到 v2.0           │
│ - 新增 2 个 Case Study        │
│ - 模板优化                    │
└───────────────────────────────┘
    ↓
项目 C, D, E...（复利持续增长）
```

---

## 四、四库乘法关系

### 4.1 数据主权架构

```
┌─────────────────────────────────────────────────────────┐
│                     数据主权层                          │
│  PostgreSQL：所有结构化主数据的唯一写入口               │
│  ├─ chunks（完整信息）                                  │
│  ├─ entities（生命周期）                                │
│  ├─ skills（自动生长）                                  │
│  └─ knowledge_assets（知识资产）                        │
└─────────────────────────────────────────────────────────┘
                    ↓（事件驱动同步）
┌─────────────────────────────────────────────────────────┐
│                     索引层（只读）                       │
│  ├─ Neo4j：图查询（关系推理、路径发现）                │
│  ├─ ChromaDB：向量检索（语义搜索、相似推荐）            │
│  └─ Redis：缓存（热点数据、毫秒级响应）                │
└─────────────────────────────────────────────────────────┘
```

### 4.2 组合查询示例

```python
class UnifiedQueryService:
    """统一查询服务：组合四库的能力"""
    
    def search_with_context(self, query: str, project_id: str) -> Dict:
        """
        带上下文的智能搜索
        
        组合：Redis缓存 → ChromaDB向量检索 → PostgreSQL完整数据 → Neo4j关系网络
        """
        cache_key = f"search:{project_id}:{hashlib.md5(query.encode()).hexdigest()}"
        
        # 1️⃣ 检查 Redis 缓存
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 2️⃣ ChromaDB 向量检索（语义搜索）
        query_embedding = generate_embedding(query)
        similar_chunks = self.chromadb.query(
            query_embeddings=[query_embedding],
            n_results=20,
            where={"project_id": project_id}
        )
        
        chunk_ids = [m["id"] for m in similar_chunks["ids"][0]]
        
        # 3️⃣ PostgreSQL 查询完整 chunk 信息
        chunks = db.query("""
            SELECT 
                c.*,
                e.name as entity_name,
                e.sentiment_avg,
                e.mention_count
            FROM chunks c
            LEFT JOIN entities e ON e.entity_id = ANY(
                SELECT jsonb_array_elements_text(c.entities::jsonb)
            )
            WHERE c.chunk_id = ANY(%s)
            ORDER BY c.quality_score DESC
        """, chunk_ids)
        
        # 4️⃣ 提取所有相关实体
        entity_ids = set()
        for chunk in chunks:
            if chunk.get("entities"):
                entity_ids.update([e["id"] for e in chunk["entities"]])
        
        # 5️⃣ Neo4j 查询实体关系网络
        relations = self.neo4j_query("""
            MATCH (e1:Entity)-[r]->(e2:Entity)
            WHERE e1.id IN $entity_ids OR e2.id IN $entity_ids
            RETURN e1, r, e2
            LIMIT 50
        """, entity_ids=list(entity_ids))
        
        # 6️⃣ 合并结果
        result = {
            "chunks": chunks,
            "entities": self._enrich_entities(entity_ids),
            "relations": relations,
            "summary": self._generate_summary(chunks, relations)
        }
        
        # 7️⃣ 写入 Redis 缓存（5分钟）
        self.redis.setex(cache_key, 300, json.dumps(result))
        
        return result
    
    def _enrich_entities(self, entity_ids: List[str]) -> List[Dict]:
        """从 PostgreSQL 获取实体的完整信息"""
        return db.query("""
            SELECT 
                entity_id,
                name,
                type,
                mention_count,
                sentiment_avg,
                sentiment_trend,
                related_events,
                timeline
            FROM entities
            WHERE entity_id = ANY(%s)
            ORDER BY importance_score DESC
        """, list(entity_ids))
```

### 4.3 事件驱动同步

```python
class DataSyncOrchestrator:
    """数据同步编排器"""
    
    def on_chunk_created(self, chunk: Dict):
        """当 chunk 在 PostgreSQL 创建后，同步到其他库"""
        
        # 1️⃣ 同步到 ChromaDB（向量检索）
        if chunk.get("embedding_id"):
            embedding = generate_embedding(chunk["text"])
            self.chromadb.add(
                ids=[chunk["chunk_id"]],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[{
                    "project_id": chunk["project_id"],
                    "document_id": chunk["document_id"],
                    "speaker": chunk.get("speaker"),
                    "dimension": chunk.get("dimension_category"),
                    "sentiment": chunk.get("emotion_polarity")
                }]
            )
        
        # 2️⃣ 如果包含实体，触发实体更新
        if chunk.get("entities"):
            for entity in chunk["entities"]:
                self.entity_lifecycle_manager.on_entity_mentioned(
                    entity["id"], chunk
                )
    
    def on_entity_updated(self, entity: Dict):
        """当实体在 PostgreSQL 更新后，同步到 Neo4j"""
        
        # 同步到 Neo4j
        self.neo4j.run("""
            MERGE (e:Entity {id: $id})
            SET e.name = $name,
                e.type = $type,
                e.mention_count = $mention_count,
                e.sentiment_avg = $sentiment_avg,
                e.importance_score = $importance_score
        """, 
            id=entity["entity_id"],
            name=entity["name"],
            type=entity["type"],
            mention_count=entity["mention_count"],
            sentiment_avg=entity["sentiment_avg"],
            importance_score=entity["importance_score"]
        )
        
        # 同步关系
        if entity.get("related_entities"):
            for related in entity["related_entities"]:
                self.neo4j.run("""
                    MATCH (e1:Entity {id: $id1})
                    MATCH (e2:Entity {id: $id2})
                    MERGE (e1)-[r:RELATED_TO {type: $relation_type}]->(e2)
                """,
                    id1=entity["entity_id"],
                    id2=related["id"],
                    relation_type=related.get("relation", "co_occurrence")
                )
        
        # 清除 Redis 缓存
        self.redis.delete(f"entity:{entity['entity_id']}")
```

---

## 五、实施计划

### 阶段 1：数据模型改造（第 1-2 周）

#### 1.1 数据库表改造

**优先级 P0：**
- [ ] 改造 chunks 表（增加新字段）
- [ ] 改造 entities 表（增加生命周期字段）
- [ ] 创建 skills 表
- [ ] 创建 knowledge_assets 表

**SQL 脚本：**
```sql
-- 1. 备份现有数据
CREATE TABLE chunks_backup AS SELECT * FROM chunks;
CREATE TABLE entities_backup AS SELECT * FROM entities;

-- 2. 执行 ALTER TABLE 添加新字段
-- （见上文完整字段设计）

-- 3. 数据迁移脚本
-- 将旧数据的基础字段迁移到新表，新字段初始化为 NULL
```

#### 1.2 统一 ID 体系

**优先级 P0：**
- [ ] 定义 ID 格式规范
  - chunk_id: `chk_{12位uuid}`
  - entity_id: `ent_{12位uuid}`
  - skill_id: `sk_{12位uuid}`
  - knowledge_asset_id: `ka_{12位uuid}`

- [ ] 迁移脚本：将现有数据的 ID 转换为新格式

```python
# migration_script.py
def migrate_ids():
    # 1. 生成新 ID
    chunks = db.query("SELECT id FROM chunks")
    for chunk in chunks:
        new_id = f"chk_{uuid.uuid4().hex[:12]}"
        db.execute("UPDATE chunks SET chunk_id = %s WHERE id = %s", new_id, chunk["id"])
    
    # 2. 同理迁移 entities, skills 等
```

---

### 阶段 2：核心服务改造（第 3-4 周）

#### 2.1 Chunk 生成服务

**优先级 P0：**
- [ ] 实现 `create_enriched_chunk()` 函数
- [ ] 集成说话人识别
- [ ] 集成情感量化
- [ ] 集成关键词提取
- [ ] 集成实体识别
- [ ] 集成维度分类

**代码位置：**
`backend/services/chunk_enrichment_service.py`

#### 2.2 实体生命周期管理

**优先级 P0：**
- [ ] 实现 `EntityLifecycleManager` 类
- [ ] 实现 `on_entity_mentioned()` 方法
- [ ] 实现事件检测逻辑
- [ ] 实现情感轨迹计算

**代码位置：**
`backend/services/entity_lifecycle_service.py`

#### 2.3 Skill 自动生长引擎

**优先级 P1：**
- [ ] 实现 `SkillGrowthEngine` 类
- [ ] 实现判断规则提取
- [ ] 实现 Skill 草稿生成
- [ ] 实现反馈权重调整

**代码位置：**
`backend/services/skill_growth_service.py`

---

### 阶段 3：知识资产管理（第 5-6 周）

#### 3.1 知识资产提取

**优先级 P1：**
- [ ] 实现 `KnowledgeAssetManager` 类
- [ ] 实现从报告提取资产
- [ ] 实现资产向量化
- [ ] 实现资产推荐算法

**代码位置：**
`backend/services/knowledge_asset_service.py`

#### 3.2 新项目推荐

**优先级 P1：**
- [ ] 实现相似度匹配
- [ ] 实现资产应用逻辑
- [ ] 实现使用统计

---

### 阶段 4：四库同步机制（第 7-8 周）

#### 4.1 事件驱动架构

**优先级 P0：**
- [ ] 实现事件总线
- [ ] 实现 PostgreSQL → Neo4j 同步
- [ ] 实现 PostgreSQL → ChromaDB 同步
- [ ] 实现 PostgreSQL → Redis 同步

**代码位置：**
`backend/core/event_bus.py`
`backend/services/data_sync_service.py`

#### 4.2 组合查询服务

**优先级 P1：**
- [ ] 实现 `UnifiedQueryService` 类
- [ ] 实现四库组合查询
- [ ] 实现缓存策略

**代码位置：**
`backend/services/unified_query_service.py`

---

### 阶段 5：前端集成（第 9-10 周）

#### 5.1 Chunk 详情展示

**优先级 P1：**
- [ ] 显示说话人、情绪、维度
- [ ] 显示关联实体
- [ ] 显示质量评分

#### 5.2 实体详情页增强

**优先级 P1：**
- [ ] 显示提及次数统计
- [ ] 显示情感轨迹图表
- [ ] 显示时间线
- [ ] 显示关联事件

#### 5.3 Skill 管理界面

**优先级 P2：**
- [ ] Skill 草稿审核
- [ ] Skill 应用管理
- [ ] 反馈提交

#### 5.4 知识资产推荐

**优先级 P2：**
- [ ] 新项目创建时显示推荐
- [ ] 资产详情页
- [ ] 一键应用资产

---

## 六、验收标准

### 6.1 乘法 1：有身份的 chunk

**测试场景：**
1. 上传一段音频访谈
2. 系统自动切分为 chunk
3. 每个 chunk 应包含：
   - ✅ 说话人姓名
   - ✅ 情感极性值
   - ✅ 关键词列表
   - ✅ 识别的实体
   - ✅ 维度分类

**成功标准：**
- chunk 生成时间 < 原来的 50%
- 维度分类准确率 > 85%
- 实体识别准确率 > 90%

### 6.2 乘法 2：有生命的知识图谱

**测试场景：**
1. 在多个 chunk 中提及同一个人物
2. 查看该人物的实体详情页

**成功标准：**
- ✅ 显示正确的提及次数
- ✅ 情感轨迹图表可见
- ✅ 时间线包含所有关键事件
- ✅ 关联实体列表完整

### 6.3 乘法 3：可复用的 Skill

**测试场景：**
1. 完成项目 A 的分析
2. 生成报告
3. 系统自动生成 2-3 个 Skill 草稿
4. 创建项目 B，自动推荐相关 Skill

**成功标准：**
- ✅ Skill 自动生成率 > 80%（有分析就有 Skill）
- ✅ Skill 推荐准确率 > 70%
- ✅ 应用 Skill 后分析速度提升 > 2 倍

### 6.4 乘法 4：知识复利

**测试场景：**
1. 完成项目 A，生成报告
2. 创建项目 B，查看推荐
3. 应用推荐的资产

**成功标准：**
- ✅ 推荐资产数量 > 5 个
- ✅ 推荐相关度 > 70%
- ✅ 项目 B 的分析时间 < 项目 A 的 50%

---

## 七、预期效果

### 7.1 性能提升

| 指标 | 改造前 | 改造后 | 提升 |
|------|--------|--------|------|
| chunk 生成时间 | 10秒/chunk | 5秒/chunk | 50% |
| 数据处理时间 | 100% | 40% | 60% |
| 新项目启动时间 | 2天 | 4小时 | 75% |
| 分析报告生成 | 4小时 | 1小时 | 75% |

### 7.2 质量提升

| 指标 | 改造前 | 改造后 | 提升 |
|------|--------|--------|------|
| 数据完整性 | 60% | 95% | 58% |
| 维度分类准确率 | 70% | 90% | 29% |
| Skill 复用率 | 0% | 80% | ∞ |
| 知识沉淀率 | 20% | 100% | 400% |

### 7.3 用户体验提升

| 场景 | 改造前 | 改造后 |
|------|--------|--------|
| 搜索结果 | 只有文本 | 文本+情绪+说话人+关联实体 |
| 实体详情 | 只有名字 | 名字+提及统计+情感轨迹+时间线 |
| 新项目 | 从零开始 | 自动推荐模板+Skill+案例 |
| 报告生成 | 需要手动整理 | 自动引用数据+案例+洞察 |

---

## 八、风险与应对

### 8.1 数据迁移风险

**风险：**
- 现有数据量大，迁移可能失败
- 新旧数据格式不兼容

**应对：**
- 分批迁移，每次迁移 10% 数据
- 保留原表备份，可回滚
- 迁移完成后验证数据完整性

### 8.2 性能风险

**风险：**
- 一步生成 enriched chunk 可能很慢
- 四库同步可能造成延迟

**应对：**
- 使用异步处理，避免阻塞
- Redis 缓存热点数据
- Neo4j/ChromaDB 同步可以延迟（最终一致性）

### 8.3 准确性风险

**风险：**
- 自动生成的 Skill 可能不准确
- 维度分类可能出错

**应对：**
- Skill 生成后需要人工审核
- 提供置信度分数，用户可以调整
- 根据反馈持续优化

---

## 九、总结

### 核心改造点

1. **Chunk 从诞生起就携带完整信息** - 转录、切分、量化、实体识别一步完成
2. **实体携带生命周期信息** - 提及次数、情感轨迹、时间线自动更新
3. **Skill 从分析中自动生长** - 判断规则自动提取、根据反馈调整权重
4. **报告结论回流为知识资产** - 自动沉淀、跨项目复用、产生复利效应

### 预期收益

- **效率提升 3 倍** - 新项目不再从零开始
- **质量提升 50%** - 数据更完整、分析更准确
- **成本降低 60%** - 减少重复劳动
- **知识沉淀 100%** - 所有经验自动保留

### 下一步行动

1. ✅ 审核本方案
2. ⏳ 确认优先级和时间表
3. ⏳ 开始阶段 1：数据模型改造
4. ⏳ 逐步推进，每两周一个里程碑

---

**文档版本**: v1.0  
**生成时间**: 2024-09-13  
**状态**: 待审核
