# FieldMind 编年史和关键词功能集成分析报告

## 🔴 核心问题：功能孤立，未融入主流水线

### 当前架构状态

```
文档上传流程（主流水线）
├─ document_processing_pipeline_complete.py
│  ├─ 1. 文档切分 (chunker)
│  ├─ 2. 向量化 (vectorizer)
│  ├─ 3. ChromaDB存储
│  ├─ 4. 数据治理 (DataCurationPipeline)
│  ├─ 5. 结构化洞察 (StructuredInsight)
│  ├─ 6. 事实陈述填充 (fact_statements)
│  ├─ 7. 数据联邦登记 (federation)
│  └─ 8. 外部增强插件
│     ├─ ✅ 知识图谱 (knowledge_graph)
│     ├─ ✅ Cognee
│     ├─ ✅ LightRAG
│     ├─ ✅ Mem0
│     ├─ ✅ Graphiti
│     ├─ ✅ GraphRAG
│     ├─ ✅ Khoj
│     ├─ ✅ Quivr
│     └─ ✅ 中文NLP (chinese_nlp)

❌ 编年史功能（完全独立）
├─ chronicle_service.py (独立服务)
├─ chronicle.py (独立API)
└─ timeline_events 表 (无数据源)

❌ 关键词功能（分散在各处）
├─ chinese_nlp_service 提取关键词 → 无统一存储
├─ 结构化洞察提取主题 → 存入 structured_insights
└─ 没有统一的关键词服务和API
```

---

## 🔍 深度分析

### 1. 编年史功能问题

#### 1.1 数据源断裂
```python
# chronicle_service.py 期望的工作流程：
TimelineEvent (数据库表) 
  ↓
analyze_event_relations() → 分析因果关系
  ↓
generate_narrative_summary() → 生成叙事
  ↓
编年史页面展示

# 实际情况：
timeline_events 表 ❌ 空表，没有数据
  ↓
因为：文档处理流水线从不创建 TimelineEvent 记录
  ↓
结果：API 可以运行，但永远返回空数据
```

#### 1.2 时间信息提取缺失
```python
# 文档处理流水线应该做但没做的事：
1. 提取时间信息（年月日、事件时间）
2. 识别事件描述
3. 创建 TimelineEvent 记录
4. 关联到文档和项目

# 现有的时间处理：
- structured_insights 表有 start_time/end_time 字段 ✅
- 但只用于音频 segment 的时间戳
- 没有从文本内容中提取事件时间
```

#### 1.3 集成点缺失
```python
# document_processing_pipeline_complete.py
# 第810行：外部增强插件调用
enrichment_results = self._run_external_enrichment(...)

# ❌ 这里没有调用编年史服务！
# 应该添加：
# - 时间事件提取
# - TimelineEvent 创建
# - 编年史智能分析（可选，需要LLM）
```

---

### 2. 关键词功能问题

#### 2.1 分散的关键词提取
```python
# 位置1：chinese_nlp_service (第456-487行)
chinese_keywords = []
jieba_result = analysis.get("jieba", {})
chinese_keywords.extend(...)
# 结果：写入 plugin_enrichment，不便查询

# 位置2：数据治理 (data_curation)
topics = curation_pipeline.process(chunk_text)['topics']
# 结果：写入 structured_insights.topics

# 位置3：知识图谱
entities = kg_service.extract_entities_and_relations(...)
# 结果：写入 project_documents.entities

# ❌ 问题：没有统一的关键词表和服务
```

#### 2.2 缺少关键词API
```python
# 前端需要的功能：
- GET /api/keywords/projects/{project_id} → 项目所有关键词
- GET /api/keywords/documents/{doc_id} → 文档关键词
- GET /api/keywords/search?q=土地 → 关键词搜索

# 现状：
❌ 没有 keywords API
❌ 没有 KeywordService
❌ 关键词分散在多个表的JSON字段中
```

---

## ✅ 解决方案

### 方案A：深度集成（推荐）

#### 第1步：创建时间事件提取服务
```python
# 新建：app/services/temporal_extractor.py
class TemporalEventExtractor:
    """从文本中提取时间事件"""
    
    def extract_events(self, text: str, metadata: Dict) -> List[Dict]:
        """
        提取时间事件
        
        1. 识别时间表达式（年月日）
        2. 识别事件描述（动词+宾语）
        3. 提取人物、地点
        4. 返回结构化事件列表
        """
        events = []
        
        # 使用正则+NLP提取时间
        time_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})年(\d{1,2})月',
            r'(\d{4})年',
        ]
        
        # 使用依存句法分析提取事件
        # ...
        
        return events
```

#### 第2步：集成到文档处理流水线
```python
# 修改：document_processing_pipeline_complete.py
# 在第797行之后添加：

# ===== 新增：时间事件提取和编年史集成 =====
try:
    from app.services.temporal_extractor import TemporalEventExtractor
    from app.models.timeline import TimelineEvent
    from app.services.chronicle_service import ChronicleService
    
    logger.info(f"⏰ 阶段5: 提取时间事件")
    
    extractor = TemporalEventExtractor()
    events = extractor.extract_events(
        text=text_content,
        metadata=metadata
    )
    
    # 保存到 timeline_events 表
    for event_data in events:
        timeline_event = TimelineEvent(
            project_id=project_id,
            document_id=document_id,
            title=event_data['title'],
            description=event_data['description'],
            date=event_data['date'],
            event_type=event_data['type'],
            source_chunk_id=event_data.get('chunk_id')
        )
        self.db.add(timeline_event)
    
    self.db.commit()
    logger.info(f"✅ 已提取 {len(events)} 个时间事件")
    
    # 可选：如果配置了LLM，立即进行智能分析
    if app_settings.ENABLE_CHRONICLE_ANALYSIS:
        chronicle_service = ChronicleService(self.db)
        for event in events:
            await chronicle_service.update_event_intelligence(event['id'])
            
except Exception as e:
    logger.warning(f"⚠️ 时间事件提取失败: {e}", exc_info=True)
# ===== 结束时间事件提取 =====
```

#### 第3步：创建统一关键词服务
```python
# 新建：app/services/keyword_service.py
class KeywordService:
    """统一关键词管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def extract_and_store_keywords(
        self,
        document_id: int,
        project_id: int,
        text: str
    ) -> List[str]:
        """
        提取并存储关键词
        
        融合多种来源：
        1. Jieba 关键词提取
        2. 数据治理的主题标签
        3. 知识图谱的实体
        4. TF-IDF 权重
        """
        keywords = []
        
        # 1. 从 chinese_nlp 提取
        from app.services.chinese_nlp_service import get_chinese_nlp_service
        nlp_service = get_chinese_nlp_service()
        analysis = nlp_service.analyse_text(text[:5000])
        jieba_keywords = analysis.get('jieba', {}).get('keywords', [])
        keywords.extend([k['keyword'] for k in jieba_keywords])
        
        # 2. 从数据治理提取主题
        from app.services.data_curation import DataCurationPipeline
        curation = DataCurationPipeline()
        topics = curation.process(text, {})['topics']
        keywords.extend(topics)
        
        # 3. 从知识图谱提取实体
        # ...
        
        # 4. 去重并计算权重
        keyword_scores = self._calculate_keyword_scores(keywords, text)
        
        # 5. 保存到数据库
        self._save_keywords(document_id, project_id, keyword_scores)
        
        return list(keyword_scores.keys())
    
    def get_project_keywords(
        self,
        project_id: int,
        limit: int = 100
    ) -> List[Dict]:
        """获取项目所有关键词（按权重排序）"""
        # 从 document_keywords 表查询
        pass
    
    def search_by_keyword(
        self,
        project_id: int,
        keyword: str
    ) -> List[Dict]:
        """根据关键词搜索文档"""
        pass
```

#### 第4步：创建关键词数据表
```sql
-- 新建表：document_keywords
CREATE TABLE document_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    keyword VARCHAR(200) NOT NULL,
    keyword_type VARCHAR(50),  -- 'topic', 'entity', 'jieba', 'tfidf'
    score FLOAT DEFAULT 0.0,   -- TF-IDF 或其他权重
    source VARCHAR(100),       -- 'chinese_nlp', 'data_curation', 'knowledge_graph'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES project_documents(id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_keywords_project ON document_keywords(project_id);
CREATE INDEX idx_keywords_document ON document_keywords(document_id);
CREATE INDEX idx_keywords_keyword ON document_keywords(keyword);
```

#### 第5步：创建关键词API
```python
# 新建：app/api/keywords.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/projects/{project_id}/keywords")
async def get_project_keywords(
    project_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取项目所有关键词"""
    service = KeywordService(db)
    keywords = service.get_project_keywords(project_id, limit)
    return APIResponse(success=True, data=keywords)

@router.get("/documents/{document_id}/keywords")
async def get_document_keywords(
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取文档关键词"""
    service = KeywordService(db)
    keywords = service.get_document_keywords(document_id)
    return APIResponse(success=True, data=keywords)

@router.get("/projects/{project_id}/search")
async def search_by_keyword(
    project_id: int,
    q: str,
    db: Session = Depends(get_db)
):
    """关键词搜索文档"""
    service = KeywordService(db)
    results = service.search_by_keyword(project_id, q)
    return APIResponse(success=True, data=results)
```

---

### 方案B：轻量集成（快速验证）

只做最小修改，验证功能可用性：

#### 1. 编年史：手动创建测试数据
```python
# 使用现有的 structured_insights 数据填充 timeline_events
# 从 structured_insights 提取时间和内容 → TimelineEvent
```

#### 2. 关键词：聚合现有数据
```python
# 创建视图聚合关键词
CREATE VIEW project_keywords_view AS
SELECT 
    project_id,
    keyword,
    COUNT(*) as frequency
FROM (
    -- 从 structured_insights 提取 topics
    SELECT project_id, topics as keyword FROM structured_insights
    UNION ALL
    -- 从 project_documents.entities 提取
    SELECT project_id, json_extract(entities, '$.name') FROM project_documents
)
GROUP BY project_id, keyword;
```

---

## 📋 实施计划

### 立即执行（30分钟）

**任务：验证现有数据状态**
- [ ] 检查 timeline_events 表是否有数据
- [ ] 检查 structured_insights 表的数据量和质量
- [ ] 检查 project_documents.entities 字段
- [ ] 确认哪些文档已经处理过

### 第1阶段：编年史深度集成（2-3小时）

- [ ] 创建 TemporalEventExtractor 服务
- [ ] 集成到 document_processing_pipeline_complete.py
- [ ] 测试时间事件提取
- [ ] 验证编年史API返回真实数据

### 第2阶段：关键词统一服务（1-2小时）

- [ ] 创建 document_keywords 表
- [ ] 创建 KeywordService
- [ ] 集成到文档处理流水线
- [ ] 创建关键词API

### 第3阶段：前端集成验证（1小时）

- [ ] 测试编年史页面展示
- [ ] 测试关键词搜索
- [ ] 验证数据流完整性

---

## 🎯 成功标准

### 编年史功能
✅ 上传文档后，timeline_events 表自动填充
✅ 编年史API返回结构化的年份目录和事件列表
✅ LLM分析（可选）能够识别因果关系和主题
✅ 前端编年史页面展示真实田野调查事件

### 关键词功能
✅ 上传文档后，document_keywords 表自动填充
✅ 关键词API返回项目/文档的关键词列表
✅ 关键词搜索能够找到相关文档
✅ 关键词权重准确反映重要性

---

## 🚨 风险提示

1. **性能影响**：在文档处理流水线中增加时间提取和关键词提取会增加处理时间（约10-20%）
2. **数据迁移**：需要为已处理的文档补充提取时间事件和关键词
3. **LLM成本**：编年史智能分析如果使用LLM会产生API费用
4. **时间解析准确性**：中文时间表达式复杂，需要充分测试

---

## 💡 建议

**推荐执行顺序：**
1. 先做"立即执行"，确认现状
2. 采用方案A第1-2步，实现编年史的基础数据提取
3. 采用方案A第3-5步，实现关键词统一服务
4. 全面测试，验证前端集成

**关键决策点：**
- 是否在文档上传时同步提取（影响上传速度）？
- 还是异步批处理（延迟但不阻塞）？
- LLM分析是否默认开启（影响成本）？
