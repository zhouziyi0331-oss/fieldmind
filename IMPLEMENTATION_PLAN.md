# FieldMind 田野调查报告系统完善计划

**制定时间**: 2026-09-16  
**预计总时长**: 8-11 小时  
**目标**: 完善从数据清洗到三个专业报告生成的完整工作流

---

## 📋 实施计划总览

```
阶段 1: 整合关键词功能 (1-2h) ⭐ 当前阶段
    ↓
阶段 2: 创建编年史功能 (2-3h)
    ↓
阶段 3: 确认并完善报告映射 (30min)
    ↓
阶段 4: 补充功能/插件/页面/Skill (1-2h)
    ↓
阶段 5: 完善自动化数据流 (2-3h)
    ↓
最终测试与文档 (1h)
```

---

## 🔧 阶段 1: 整合关键词功能（1-2小时）⭐

### 目标
统一分散在多个 API 中的关键词提取功能，提供清晰的接口

### 现状分析

**当前分散的位置**:
1. `/api/documents.py` - `GET /aggregate/keywords`
2. `/api/knowledge_graph.py` - `GET /projects/{project_id}/keywords/`
3. `/api/keyword_search.py` - 独立搜索功能

### 任务清单

#### 1.1 创建统一的关键词 API ⏱️ 30分钟
**文件**: `backend/src/app/api/keywords.py`

**端点设计**:
```python
# 关键词提取
POST /api/keywords/extract
{
  "document_id": "xxx",
  "method": "auto" | "llm" | "tfidf"
}

# 获取项目关键词
GET /api/keywords/projects/{project_id}
Response: {
  "keywords": [
    {
      "text": "村委会",
      "category": "组织",
      "frequency": 15,
      "weight": 0.85
    }
  ]
}

# 获取文档关键词
GET /api/keywords/documents/{document_id}

# 关键词搜索
POST /api/keywords/search
{
  "keywords": ["村委会", "选举"],
  "project_id": 123
}

# 热门关键词
GET /api/keywords/trending

# 关键词统计
GET /api/keywords/stats
```

#### 1.2 创建关键词服务层 ⏱️ 30分钟
**文件**: `backend/src/app/services/keyword_service.py`

**功能**:
- TF-IDF 提取
- LLM 智能提取
- 规则提取
- 关键词聚合
- 关键词关系分析

#### 1.3 更新数据库模型 ⏱️ 15分钟
**文件**: `backend/src/app/models/keyword.py`

**表结构**:
```python
class Keyword(Base):
    __tablename__ = "keywords"
    
    id
    text           # 关键词文本
    category       # 类别（人物/地点/事件/主题）
    frequency      # 出现频率
    weight         # 权重
    project_id     # 所属项目
    first_seen_at  # 首次出现
    last_seen_at   # 最后出现
    
class DocumentKeyword(Base):
    __tablename__ = "document_keywords"
    
    document_id
    keyword_id
    positions      # JSON: 在文档中的位置
    context        # 上下文片段
```

#### 1.4 更新前端调用 ⏱️ 15分钟
- 统一前端调用新的关键词 API
- 更新 `Documents.tsx` 使用新接口
- 创建 API hooks

---

## 📖 阶段 2: 创建编年史功能（2-3小时）

### 目标
将时间线事件整合成连贯的叙事性文档

### 编年史 vs 时间线
- **时间线**: 离散的事件点 (Event A, Event B, Event C)
- **编年史**: 连贯的叙事文档 ("在某年某月，发生了A，这导致了B，最终C...")

### 任务清单

#### 2.1 创建编年史 API ⏱️ 45分钟
**文件**: `backend/src/app/api/chronicle.py`

**端点**:
```python
# 生成编年史
POST /api/chronicle/generate
{
  "project_id": 123,
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "style": "narrative" | "academic" | "report",
  "granularity": "daily" | "weekly" | "monthly"
}

# 获取编年史
GET /api/chronicle/projects/{project_id}

# 获取章节
GET /api/chronicle/{chronicle_id}/chapters

# 编辑编年史
PUT /api/chronicle/{chronicle_id}

# 导出
GET /api/chronicle/{chronicle_id}/export?format=pdf
```

#### 2.2 创建编年史服务 ⏱️ 60分钟
**文件**: `backend/src/app/services/chronicle_generator.py`

**核心逻辑**:
```python
class ChronicleGenerator:
    def generate_chronicle(events, style):
        # 1. 按时间分组事件
        # 2. 识别事件关联
        # 3. 使用 LLM 生成叙述
        # 4. 添加过渡段落
        
    def generate_narrative(event_group):
        # 使用 LLM 将事件组转为叙述
```

#### 2.3 数据库模型 ⏱️ 20分钟
**文件**: `backend/src/app/models/chronicle.py`

```python
class Chronicle(Base):
    id
    project_id
    title
    style              # narrative/academic/report
    start_date
    end_date
    content            # Markdown
    metadata           # JSON
    
class ChronicleChapter(Base):
    chronicle_id
    order
    title
    period_start
    period_end
    content
    event_ids          # 关联的事件
```

#### 2.4 前端页面 ⏱️ 45分钟
**文件**: `frontend/src/pages/Chronicle.tsx`

**功能**:
- 显示编年史文档
- 章节导航
- 编辑模式
- 导出 PDF/Word/Markdown

---

## 📊 阶段 3: 确认报告映射（30分钟）

### 目标
明确三个报告的定位

### 任务
1. 检查现有 level1/2/3 报告内容
2. 确认映射:
   - 报告 1: 基础分析报告
   - 报告 2: 学术报告（费孝通）
   - 报告 3: 商业分析报告
3. 如需要，重构函数

---

## 🔌 阶段 4: 补充功能模块（1-2小时）

### 4.1 补充 Skills
- 文档分析 Skill
- 关键词提取 Skill
- 编年史生成 Skill
- 报告生成 Skill

### 4.2 工作流总览页面
**文件**: `frontend/src/pages/WorkflowOverview.tsx`

显示完整处理流程和状态

### 4.3 一键生成功能
```python
POST /api/workflows/full-analysis
{
  "project_id": 123
}
```

---

## 🔄 阶段 5: 自动化数据流（2-3小时）

### 自动化流程
```
文档上传 → 清洗 → 关键词 → 时间线 → 编年史 → 知识图谱 → 报告
```

### 任务
- 后台任务队列
- 实时进度追踪
- 智能触发机制
- 批量处理

---

## 📈 进度跟踪

- [ ] 阶段 1: 整合关键词功能 (0%)
- [ ] 阶段 2: 创建编年史功能 (0%)
- [ ] 阶段 3: 确认报告映射 (0%)
- [ ] 阶段 4: 补充功能模块 (0%)
- [ ] 阶段 5: 自动化流程 (0%)
- [ ] 最终测试 (0%)

**预计总时长**: 8-11 小时

---

## 🎯 成功标准

**目标功能完整度**: 95%+

- [x] 数据清洗 - 100%
- [ ] 关键词提取 - 目标 100% (当前 70%)
- [x] 时间线生成 - 100%
- [ ] 编年史构建 - 目标 100% (当前 0%)
- [x] 知识图谱 - 100%
- [ ] 报告生成 - 目标 100% (当前 80%)
- [ ] 自动化流程 - 目标 100% (当前 0%)

---

**准备好开始了吗？我们从阶段 1: 关键词功能整合开始！**
