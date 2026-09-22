# FieldMind 田野调查报告生成系统 - 完整现状分析

**分析时间**: 2026-09-16  
**目标**: 从数据清洗到生成三个专业报告的完整工作流

---

## 🎯 目标工作流

```
原始数据导入
    ↓
数据清洗与标准化
    ↓
关键词提取
    ↓
时间线生成
    ↓
编年史构建
    ↓
知识图谱构建
    ↓
三个专业报告生成：
  ├─ 1. 基础分析报告（根据原始资料）
  ├─ 2. 学术分析报告（费孝通《乡土中国》视角）
  └─ 3. 商业分析报告（商业价值分析）
```

---

## ✅ 现有功能清单

### 1. 数据清洗 ✅ 完整

**后端 API**: `/api/documents.py`

**已有端点**:
- `POST /upload` - 文档上传
- `GET /projects/{project_id}/documents/` - 获取文档列表
- `DELETE /{document_id}/` - 删除文档
- `GET /knowledge-base/status` - 知识库状态
- `GET /aggregate/keywords` - 聚合关键词
- `GET /skill/analysis/{document_id}/` - 技能分析

**前端页面**: `Documents.tsx` ✅

**数据库模型**: `models/document.py` ✅

**状态**: ✅ **功能完整**

---

### 2. 关键词提取 ⚠️ 部分存在

**后端文件**: 
- `app/api/keyword_search.py` ✅ 找到
- ❌ 没有独立的 `keywords.py` API

**已有功能**:
- `GET /aggregate/keywords` - 在 documents API 中
- `GET /projects/{project_id}/keywords/` - 在 knowledge_graph API 中

**前端**: Documents.tsx 中有关键词功能 ✅

**状态**: ⚠️ **功能分散，需要整合**

---

### 3. 时间线生成 ✅ 完整

**后端 API**: `/api/timeline.py` ✅

**已有端点**:
- `POST /build` - 构建时间线
- `GET /events` - 获取事件
- `GET /stats` - 统计信息
- `GET /projects/{project_id}/events/` - 项目事件
- `GET /projects/{project_id}/events/grouped/` - 分组事件

**前端页面**: `Timeline.tsx` ✅

**数据库模型**: `models/timeline.py` ✅
- TimelineEvent 表
- 包含：date, title, description, category, entities, location 等

**状态**: ✅ **功能完整**

---

### 4. 编年史构建 ❌ 缺失

**检查结果**: ❌ 未找到编年史相关文件

**分析**:
- 时间线有了（TimelineEvent）
- 但没有"编年史"的专门整合和呈现功能

**缺失内容**:
- ❌ 编年史 API 端点
- ❌ 编年史前端页面
- ❌ 编年史数据模型（可能可以基于 Timeline）
- ❌ 按时间顺序的叙事性整合

**状态**: ❌ **功能缺失，需要创建**

---

### 5. 知识图谱构建 ✅ 完整

**后端 API**: `/api/knowledge_graph.py` ✅

**已有端点**:
- `POST /build` - 构建知识图谱
- `GET /visualize` - 可视化
- `GET /stats` - 统计信息
- `DELETE /entities/{entity_id}/` - 删除实体
- `GET /projects/{project_id}/graph/` - 项目图谱
- `GET /projects/{project_id}/keywords/` - 项目关键词
- `GET /documents/{document_id}/entities/` - 文档实体

**前端页面**: `KnowledgeGraph.tsx` ✅

**数据库模型**: `models/knowledge_graph.py` ✅

**状态**: ✅ **功能完整**

---

### 6. 报告生成 ⚠️ 部分完整

**后端 API**: `/api/reports_real.py` ✅

**已有报告生成函数**:
- `generate_level1_report()` - 基础报告
- `generate_level2_report()` - 中级报告
- `generate_level3_report()` - 高级报告

**费孝通分析**: ✅ **已存在**
- `FeiDimensionAnalyzer` 类
- 包含差序格局、礼治秩序等维度分析

**商业分析**: ✅ **已存在**
- 在报告中包含商业相关分析

**前端页面**: `Reports.tsx` ✅

**问题分析**:
- ✅ 有三个 level 的报告（level1/2/3）
- ⚠️ 但不明确对应：基础/学术/商业
- ⚠️ 需要确认三个报告的具体内容是否符合要求

**状态**: ⚠️ **功能存在，但需要确认映射关系**

---

## 🔍 关键问题诊断

### 问题 1: 编年史功能缺失 ❌

**现状**:
- 有时间线（Timeline）
- 但没有编年史（Chronicle）

**区别**:
- **时间线**: 事件列表，时间点
- **编年史**: 按时间顺序的**叙事性文档**，像故事一样连贯

**需要**:
- 创建编年史 API
- 创建编年史前端页面
- 将时间线事件整合成连贯的叙事

---

### 问题 2: 关键词提取功能分散 ⚠️

**现状**:
- 关键词提取功能存在
- 但分散在多个 API 中

**位置**:
- `documents.py` - `/aggregate/keywords`
- `knowledge_graph.py` - `/projects/{project_id}/keywords/`
- `keyword_search.py` - 独立文件

**需要**:
- 整合到统一的关键词 API
- 或者明确各个端点的用途

---

### 问题 3: 报告映射不明确 ⚠️

**现状**:
- 有 level1/level2/level3 三个报告
- 但不清楚对应：基础/学术/商业

**需要确认**:
1. `level1_report` = 基础分析报告？
2. `level2_report` = 费孝通学术报告？
3. `level3_report` = 商业分析报告？

**或者需要**:
- 重新命名报告函数
- 明确三个报告的定位

---

## 📋 数据流检查

### 当前数据流

```
1. Documents API (上传) ✅
   ↓
2. Documents 数据清洗 ✅
   ↓
3. 关键词提取 ⚠️ (分散在多处)
   ↓
4. Timeline Build ✅
   ↓
5. Chronicle ❌ (缺失)
   ↓
6. Knowledge Graph Build ✅
   ↓
7. Reports Generate ⚠️ (需要确认映射)
```

### 缺失的连接

1. **文档 → 关键词**
   - ⚠️ 功能存在但分散
   - 需要统一调用路径

2. **时间线 → 编年史**
   - ❌ 完全缺失
   - 需要创建编年史生成逻辑

3. **所有数据 → 三个专业报告**
   - ⚠️ 逻辑存在但映射不清晰
   - 需要明确对应关系

---

## 🎯 待完成任务清单

### 🔴 优先级 1: 关键缺失功能

#### 任务 1.1: 创建编年史功能
- [ ] 后端 API: `app/api/chronicle.py`
  - `POST /api/chronicle/generate` - 从时间线生成编年史
  - `GET /api/chronicle/projects/{project_id}` - 获取项目编年史
  - `PUT /api/chronicle/{id}` - 编辑编年史
- [ ] 前端页面: `frontend/src/pages/Chronicle.tsx`
  - 显示编年史文档
  - 支持编辑和导出
- [ ] 服务层: `app/services/chronicle_generator.py`
  - 将时间线事件整合成叙事文档
  - 使用 LLM 生成连贯叙述

#### 任务 1.2: 明确三个报告的映射
- [ ] 确认现有 level1/2/3 报告的内容
- [ ] 重命名或重构为：
  - `generate_basic_analysis_report()` - 基础分析
  - `generate_academic_analysis_report()` - 费孝通视角
  - `generate_business_analysis_report()` - 商业价值
- [ ] 更新前端显示，明确三个报告的区别

---

### 🟡 优先级 2: 功能整合

#### 任务 2.1: 整合关键词提取
- [ ] 创建统一的关键词 API: `app/api/keywords.py`
  - `POST /api/keywords/extract` - 提取关键词
  - `GET /api/keywords/projects/{project_id}` - 项目关键词
  - `GET /api/keywords/trending` - 热门关键词
- [ ] 或者明确现有端点的使用场景

---

### 🟢 优先级 3: 优化增强

#### 任务 3.1: 完善数据流
- [ ] 创建自动化工作流
- [ ] 文档上传后自动：
  - 提取关键词
  - 构建时间线
  - 生成编年史
  - 构建知识图谱
- [ ] 一键生成三个报告

#### 任务 3.2: 前端整合
- [ ] 创建工作流总览页面
- [ ] 显示完整的数据处理流程
- [ ] 可视化各阶段状态

---

## 💡 建议的实现顺序

### 第一步: 确认报告映射（最快）⏱️ 30分钟
1. 阅读 `reports_real.py` 中的三个报告函数
2. 确认它们的实际内容
3. 确定是否需要重构

### 第二步: 创建编年史功能 ⏱️ 2-3小时
1. 后端 API（1小时）
2. 前端页面（1小时）
3. LLM 生成逻辑（1小时）

### 第三步: 整合关键词功能 ⏱️ 1-2小时
1. 统一 API 端点
2. 更新前端调用

### 第四步: 完善数据流 ⏱️ 2-3小时
1. 自动化工作流
2. 前端总览页面

---

## 📊 功能完整度评估

| 功能模块 | 后端API | 前端页面 | 数据模型 | 完整度 | 备注 |
|---------|--------|---------|---------|-------|------|
| 数据清洗 | ✅ | ✅ | ✅ | 100% | 完整 |
| 关键词提取 | ⚠️ | ✅ | ✅ | 70% | 功能分散 |
| 时间线生成 | ✅ | ✅ | ✅ | 100% | 完整 |
| 编年史构建 | ❌ | ❌ | ❌ | 0% | 完全缺失 |
| 知识图谱 | ✅ | ✅ | ✅ | 100% | 完整 |
| 报告生成 | ⚠️ | ✅ | ✅ | 80% | 需确认映射 |
| **总体完整度** | | | | **75%** | |

---

## 🎯 下一步行动

请告诉我您希望：

1. **立即确认报告映射** - 我帮您检查三个报告的实际内容
2. **创建编年史功能** - 从零开始实现编年史系统
3. **整合关键词功能** - 统一分散的关键词提取功能
4. **完善整体数据流** - 创建自动化工作流

请选择优先级，我们一个个解决！
