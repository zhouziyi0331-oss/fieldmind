# 阶段 1: 关键词功能整合 - 详细设计方案

## 📊 现状分析

### 已发现的关键词相关功能

#### 1. `keyword_search.py` - 关键词智能检索
**位置**: `/api/keyword_search.py`  
**功能**: 在视频/音频/文档中搜索关键词，返回精确时间点  
**特点**: 专注于**检索定位**，找到关键词在媒体中的位置

#### 2. `documents.py` - 聚合关键词
**位置**: `/api/documents.py`  
**端点**: `GET /aggregate/keywords`  
**功能**: 聚合项目所有文档的关键词，按词频排序  
**特点**: 专注于**统计分析**，展示高频关键词

#### 3. `knowledge_graph.py` - 项目关键词
**位置**: `/api/knowledge_graph.py`  
**端点**: `GET /projects/{project_id}/keywords/`  
**功能**: 获取知识图谱中的关键词（可能是实体）  
**特点**: 专注于**知识图谱**，关键词作为图谱节点

---

## 🎯 整合策略

### 方案 A: 统一 API（推荐）✅

**理念**: 创建一个统一的关键词 API，整合所有功能

**优点**:
- ✅ 清晰的接口设计
- ✅ 前端调用统一
- ✅ 便于维护和扩展

**缺点**:
- ⚠️ 需要重构现有代码
- ⚠️ 可能影响现有调用

### 方案 B: 保持分散，明确分工（快速）

**理念**: 保持现有结构，但明确各 API 的职责

**优点**:
- ✅ 无需重构
- ✅ 快速完成
- ✅ 不影响现有功能

**缺点**:
- ❌ 功能分散
- ❌ 前端需要知道调用哪个 API

---

## 💡 推荐方案: 混合方案

**核心思想**: 创建统一的关键词 API，但保留并优化现有功能

### 设计原则

1. **保留现有功能**
   - `keyword_search.py` 保留（专注检索）
   - `documents.py` 的聚合端点保留（向后兼容）
   - `knowledge_graph.py` 的关键词保留（图谱专用）

2. **创建统一入口**
   - 新建 `keywords.py` 作为统一入口
   - 整合常用功能
   - 调用现有服务

3. **明确职责分工**
   - `keywords.py` - **主入口**，常用功能
   - `keyword_search.py` - **专业检索**，媒体定位
   - `knowledge_graph.py` - **图谱专用**，实体关键词

---

## 📐 详细设计

### 新建 `keywords.py` - 统一关键词 API

#### 端点设计

```python
# ============================================
# 1. 关键词提取
# ============================================
POST /api/keywords/extract
{
  "document_id": 123,
  "method": "auto",  # auto | llm | tfidf | rules
  "options": {
    "top_n": 20,
    "min_frequency": 2,
    "categories": ["人物", "地点", "事件"]
  }
}

Response:
{
  "keywords": [
    {
      "text": "村委会",
      "category": "组织",
      "frequency": 15,
      "weight": 0.85,
      "positions": [120, 450, 890]
    }
  ]
}

# ============================================
# 2. 获取项目关键词（整合版）
# ============================================
GET /api/keywords/projects/{project_id}
?category=人物          # 可选：按类别筛选
&top_n=50              # 可选：返回数量
&sort=frequency        # 可选：排序方式

Response:
{
  "total": 150,
  "keywords": [
    {
      "text": "村委会",
      "category": "组织",
      "frequency": 45,
      "weight": 0.92,
      "first_seen": "2024-01-15",
      "last_seen": "2024-03-20",
      "documents": [1, 5, 8]  # 出现的文档ID
    }
  ]
}

# ============================================
# 3. 获取文档关键词
# ============================================
GET /api/keywords/documents/{document_id}
?include_positions=true  # 是否返回位置信息

Response:
{
  "document_id": 123,
  "document_name": "访谈记录1.md",
  "keywords": [
    {
      "text": "村民大会",
      "category": "事件",
      "frequency": 8,
      "positions": [120, 450],
      "contexts": [
        "...召开村民大会讨论...",
        "...参加村民大会的人..."
      ]
    }
  ]
}

# ============================================
# 4. 关键词搜索（整合检索功能）
# ============================================
POST /api/keywords/search
{
  "keywords": ["村委会", "选举"],
  "project_id": 123,
  "scope": {
    "documents": true,
    "videos": true,
    "audios": true
  },
  "match_mode": "all"  # all | any
}

Response:
{
  "results": {
    "documents": [
      {
        "id": 5,
        "name": "访谈1.md",
        "matches": [...]
      }
    ],
    "videos": [
      {
        "id": 2,
        "name": "实地考察.mp4",
        "timestamps": ["00:05:30", "00:12:45"]
      }
    ]
  }
}

# ============================================
# 5. 热门关键词（跨项目）
# ============================================
GET /api/keywords/trending
?time_range=7d          # 时间范围
&category=all           # 类别
&limit=20

Response:
{
  "trending": [
    {
      "text": "村委会",
      "frequency": 230,
      "growth": "+15%",  # 相比上周
      "projects": 5
    }
  ]
}

# ============================================
# 6. 关键词统计
# ============================================
GET /api/keywords/stats
?project_id=123

Response:
{
  "total_keywords": 380,
  "by_category": {
    "人物": 120,
    "地点": 85,
    "事件": 95,
    "组织": 80
  },
  "average_per_document": 25.3,
  "most_frequent": "村委会"
}

# ============================================
# 7. 关键词关系分析（新增）
# ============================================
GET /api/keywords/{keyword}/relations
?project_id=123

Response:
{
  "keyword": "村委会",
  "related": [
    {
      "text": "选举",
      "co_occurrence": 35,  # 共现次数
      "correlation": 0.78
    },
    {
      "text": "村民",
      "co_occurrence": 42,
      "correlation": 0.85
    }
  ]
}

# ============================================
# 8. 批量提取关键词（新增）
# ============================================
POST /api/keywords/batch-extract
{
  "document_ids": [1, 2, 3, 4, 5],
  "method": "auto"
}

Response:
{
  "status": "processing",
  "task_id": "task_123",
  "progress_url": "/api/keywords/tasks/task_123"
}
```

---

## 🗄️ 数据库设计

### 新表结构

```sql
-- 关键词表
CREATE TABLE keywords (
    id INTEGER PRIMARY KEY,
    text VARCHAR(200) NOT NULL,
    category VARCHAR(50),  -- 人物/地点/事件/组织/主题
    project_id INTEGER,
    frequency INTEGER DEFAULT 1,
    weight FLOAT DEFAULT 0.5,
    first_seen_at DATETIME,
    last_seen_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    
    UNIQUE(text, project_id)  -- 同一项目内关键词唯一
);

-- 文档-关键词关联表
CREATE TABLE document_keywords (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    keyword_id INTEGER NOT NULL,
    positions JSON,  -- [120, 450, 890] 关键词位置
    contexts JSON,   -- ["上下文1", "上下文2"]
    frequency INTEGER DEFAULT 1,
    weight FLOAT DEFAULT 0.5,
    created_at DATETIME,
    
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (keyword_id) REFERENCES keywords(id),
    UNIQUE(document_id, keyword_id)
);

-- 关键词关系表（新增）
CREATE TABLE keyword_relations (
    id INTEGER PRIMARY KEY,
    keyword1_id INTEGER NOT NULL,
    keyword2_id INTEGER NOT NULL,
    project_id INTEGER,
    co_occurrence INTEGER DEFAULT 1,  -- 共现次数
    correlation FLOAT,  -- 相关性
    created_at DATETIME,
    updated_at DATETIME,
    
    FOREIGN KEY (keyword1_id) REFERENCES keywords(id),
    FOREIGN KEY (keyword2_id) REFERENCES keywords(id),
    UNIQUE(keyword1_id, keyword2_id, project_id)
);
```

---

## 🔧 服务层设计

### `keyword_service.py`

```python
class KeywordService:
    """统一的关键词服务"""
    
    def extract_keywords(self, text, method="auto", options=None):
        """提取关键词（多种方法）"""
        if method == "auto":
            # 自动选择最佳方法
            return self._auto_extract(text, options)
        elif method == "llm":
            return self._llm_extract(text, options)
        elif method == "tfidf":
            return self._tfidf_extract(text, options)
        elif method == "rules":
            return self._rule_extract(text, options)
    
    def _llm_extract(self, text, options):
        """使用 LLM 提取关键词"""
        # 调用 P3 LLM 服务
        from app.services.multi_provider_llm_manager import get_llm_manager
        
        llm_manager = get_llm_manager()
        # 构建提示词
        prompt = f"""
        从以下田野调查文本中提取关键词，按以下类别分类：
        - 人物
        - 地点
        - 事件
        - 组织
        - 主题
        
        文本：
        {text[:2000]}  # 限制长度
        """
        
        # 调用 LLM
        result = llm_manager.chat(prompt, task_complexity="simple")
        return self._parse_llm_result(result)
    
    def _tfidf_extract(self, text, options):
        """使用 TF-IDF 提取"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        # TF-IDF 实现
        pass
    
    def aggregate_keywords(self, project_id, top_n=50):
        """聚合项目关键词"""
        # 查询数据库
        # 统计词频
        # 返回结果
        pass
    
    def find_keyword_relations(self, project_id):
        """分析关键词关系"""
        # 计算共现
        # 计算相关性
        pass
```

---

## 🎨 前端集成

### 创建统一的 Hooks

```typescript
// hooks/useKeywords.ts

export const useExtractKeywords = () => {
  return useMutation({
    mutationFn: async (data: {
      document_id: number;
      method?: string;
    }) => {
      return api.post('/api/keywords/extract', data);
    }
  });
};

export const useProjectKeywords = (projectId: number) => {
  return useQuery({
    queryKey: ['keywords', 'project', projectId],
    queryFn: () => api.get(`/api/keywords/projects/${projectId}`)
  });
};

export const useKeywordSearch = () => {
  return useMutation({
    mutationFn: async (data: {
      keywords: string[];
      project_id: number;
    }) => {
      return api.post('/api/keywords/search', data);
    }
  });
};
```

---

## 📝 实施步骤

### Step 1: 创建数据库模型（15分钟）
1. 创建 `models/keyword.py`
2. 定义 Keyword, DocumentKeyword, KeywordRelation 表
3. 运行迁移

### Step 2: 创建服务层（30分钟）
1. 创建 `services/keyword_service.py`
2. 实现多种提取方法
3. 实现聚合和统计功能

### Step 3: 创建 API（30分钟）
1. 创建 `api/keywords.py`
2. 实现所有端点
3. 注册到 main.py

### Step 4: 前端集成（15分钟）
1. 创建 hooks
2. 更新现有页面调用

---

## ❓ 讨论问题

在开始实施前，请确认：

1. **关键词分类**: 您希望使用哪些类别？
   - 建议：人物、地点、事件、组织、主题
   - 或者其他分类方式？

2. **提取方法优先级**: 默认使用哪种方法？
   - LLM（准确但慢，需要 API Key）
   - TF-IDF（快速但可能不够准确）
   - 混合（先 TF-IDF 后 LLM 验证）

3. **保留现有端点**: 是否保留向后兼容？
   - 保留 `/aggregate/keywords`？
   - 保留 `keyword_search.py`？

4. **前端页面**: 是否需要新的关键词管理页面？
   - 或者在现有页面集成？

---

**请告诉我您的想法，我们开始实施！**
