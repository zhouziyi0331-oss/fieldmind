# FieldMind 前后端API完整映射文档

## 概览统计

| 功能模块 | 总端点数 | 已实现 | 缺失 | 优先级 |
|---------|---------|--------|------|--------|
| 认证系统 | 5 | 0 | 5 | 🔴 CRITICAL |
| 技能管理系统 | 7 | 0 | 7 | 🔴 CRITICAL |
| 业态分析 | 4 | 0 | 4 | 🔴 CRITICAL |
| 编年史/时间线 | 4 | 0 | 4 | 🟡 HIGH |
| 报告生成 | 4 | 2 | 2 | 🟡 HIGH |
| 文档管理 | 7 | 4 | 3 | 🟢 MEDIUM |
| 仪表盘 | 3 | 0 | 3 | 🟢 MEDIUM |
| 知识图谱 | 6 | 6 | 0 | ✅ 完成 |
| 搜索功能 | 3 | 3 | 0 | ✅ 完成 |
| 数据分析 | 5 | 2 | 3 | 🟢 MEDIUM |

**总计: 48个端点 | 已实现: 17 (35%) | 缺失: 31 (65%)**

---

## 1. 认证系统 (Authentication) - 🔴 完全缺失

### 1.1 用户注册
- **端点**: `POST /api/v1/auth/register`
- **前端页面**: `pages/Auth/RegisterPage.tsx`
- **前端Hook**: `useAuth.ts`
- **请求体**:
```json
{
  "email": "string",
  "password": "string",
  "username": "string",
  "role": "researcher|admin"
}
```
- **响应**:
```json
{
  "user": {
    "id": "string",
    "email": "string",
    "username": "string",
    "role": "string"
  },
  "token": "string",
  "refresh_token": "string"
}
```
- **状态**: ❌ 未实现
- **优先级**: 🔴 CRITICAL

### 1.2 用户登录
- **端点**: `POST /api/v1/auth/login`
- **前端页面**: `pages/Auth/LoginPage.tsx`
- **请求体**:
```json
{
  "email": "string",
  "password": "string"
}
```
- **响应**:
```json
{
  "user": {...},
  "token": "string",
  "refresh_token": "string"
}
```
- **状态**: ❌ 未实现
- **优先级**: 🔴 CRITICAL

### 1.3 登出
- **端点**: `POST /api/v1/auth/logout`
- **前端**: `Header.tsx` (logout button)
- **请求头**: `Authorization: Bearer <token>`
- **响应**: `{"message": "Logged out successfully"}`
- **状态**: ❌ 未实现

### 1.4 获取当前用户
- **端点**: `GET /api/v1/auth/me`
- **前端**: `useAuth.ts` hook
- **响应**: User对象
- **状态**: ❌ 未实现

### 1.5 刷新Token
- **端点**: `POST /api/v1/auth/refresh`
- **请求体**: `{"refresh_token": "string"}`
- **响应**: `{"token": "string"}`
- **状态**: ❌ 未实现

---

## 2. 技能管理系统 (Skill Management) - 🔴 完全缺失（最高优先级）

### 2.1 获取所有技能
- **端点**: `GET /api/v1/skills`
- **前端页面**: `pages/Skills/SkillListPage.tsx`
- **查询参数**: `?status=active|inactive&category=string`
- **响应**:
```json
{
  "skills": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "version": "string",
      "status": "active|inactive",
      "category": "crawler|nlp|analysis",
      "created_at": "datetime",
      "can_be_applied": boolean,
      "validation_result": {
        "valid": boolean,
        "errors": ["string"]
      }
    }
  ]
}
```
- **状态**: ❌ 未实现
- **优先级**: 🔴 CRITICAL

### 2.2 上传新技能
- **端点**: `POST /api/v1/skills/upload`
- **前端组件**: `components/SkillUploader.tsx` (拖拽上传)
- **请求**: `multipart/form-data`
  - `file`: 技能文件 (.py, .zip)
  - `metadata`: JSON字符串
- **验证约束**:
  - 检查技能代码语法
  - 验证依赖项可用性
  - 测试技能基本功能
  - 确保与系统兼容
- **响应**:
```json
{
  "skill_id": "string",
  "validation": {
    "syntax_check": boolean,
    "dependencies_ok": boolean,
    "test_passed": boolean,
    "can_activate": boolean,
    "errors": ["string"],
    "warnings": ["string"]
  }
}
```
- **状态**: ❌ 未实现
- **优先级**: 🔴 CRITICAL

### 2.3 激活技能
- **端点**: `PUT /api/v1/skills/{skill_id}/activate`
- **前端**: `SkillCard.tsx` (activate button)
- **前置条件**: 技能必须通过验证
- **响应**: `{"status": "active", "message": "Skill activated"}`
- **状态**: ❌ 未实现

### 2.4 停用技能
- **端点**: `PUT /api/v1/skills/{skill_id}/deactivate`
- **前端**: `SkillCard.tsx` (deactivate button)
- **响应**: `{"status": "inactive"}`
- **状态**: ❌ 未实现

### 2.5 删除技能
- **端点**: `DELETE /api/v1/skills/{skill_id}`
- **前端**: `SkillCard.tsx` (delete button with confirmation)
- **响应**: `{"message": "Skill deleted"}`
- **状态**: ❌ 未实现

### 2.6 测试技能
- **端点**: `POST /api/v1/skills/{skill_id}/test`
- **前端**: `SkillDetailPage.tsx` (test button)
- **请求体**:
```json
{
  "test_input": "string",
  "test_params": {}
}
```
- **响应**:
```json
{
  "success": boolean,
  "output": "string",
  "execution_time": float,
  "errors": ["string"]
}
```
- **状态**: ❌ 未实现

### 2.7 获取可用于任务的技能
- **端点**: `GET /api/v1/skills/available-for-task`
- **查询参数**: `?task_type=crawler|nlp|analysis`
- **前端**: 工作流配置页面
- **响应**: 过滤后的技能列表
- **状态**: ❌ 未实现

---

## 3. 业态分析 (Industry Analysis) - 🔴 完全缺失

### 3.1 获取业态类别列表
- **端点**: `GET /api/v1/industry/categories`
- **前端页面**: `pages/Industry/IndustryOverviewPage.tsx`
- **响应**:
```json
{
  "categories": [
    {
      "id": "traditional-agriculture",
      "name": "传统农业",
      "description": "string",
      "document_count": int,
      "last_updated": "datetime"
    }
  ]
}
```
- **状态**: ❌ 未实现
- **优先级**: 🔴 CRITICAL

### 3.2 获取业态详细分析
- **端点**: `GET /api/v1/industry/{category}/details`
- **前端页面**: `pages/Industry/IndustryDetailPage.tsx`
- **示例**: `/api/v1/industry/traditional-agriculture/details`
- **响应**:
```json
{
  "category": "传统农业",
  "overview": {
    "summary": "string",
    "key_findings": ["string"],
    "document_count": int
  },
  "detailed_analysis": {
    "current_status": "string",
    "trends": ["string"],
    "challenges": ["string"],
    "opportunities": ["string"]
  },
  "related_entities": [
    {"type": "person|place|organization", "name": "string", "count": int}
  ],
  "timeline": [
    {"date": "datetime", "event": "string"}
  ],
  "documents": [
    {"id": "string", "title": "string", "relevance_score": float}
  ]
}
```
- **状态**: ❌ 未实现
- **优先级**: 🔴 CRITICAL

### 3.3 获取业态统计数据
- **端点**: `GET /api/v1/industry/{category}/statistics`
- **前端**: `IndustryDetailPage.tsx` (statistics section)
- **响应**:
```json
{
  "total_documents": int,
  "entity_distribution": {...},
  "temporal_distribution": {...},
  "keyword_frequency": {...}
}
```
- **状态**: ❌ 未实现

### 3.4 获取业态趋势分析
- **端点**: `GET /api/v1/industry/{category}/trends`
- **前端**: `IndustryDetailPage.tsx` (trends chart)
- **查询参数**: `?time_range=1y|3y|5y`
- **响应**: 时间序列数据
- **状态**: ❌ 未实现

---

## 4. 编年史/时间线 (Chronicle/Timeline) - 🟡 完全缺失

### 4.1 获取时间线事件
- **端点**: `GET /api/v1/timeline/events`
- **前端页面**: `pages/Timeline/TimelinePage.tsx`
- **查询参数**: 
  - `?start_date=YYYY-MM-DD`
  - `&end_date=YYYY-MM-DD`
  - `&category=string`
  - `&sort=asc|desc`
- **响应**:
```json
{
  "events": [
    {
      "id": "string",
      "date": "datetime",
      "title": "string",
      "description": "string",
      "category": "string",
      "entities": ["string"],
      "documents": ["doc_id"],
      "location": {"lat": float, "lng": float}
    }
  ],
  "total": int
}
```
- **状态**: ❌ 未实现
- **优先级**: 🟡 HIGH

### 4.2 创建时间线事件
- **端点**: `POST /api/v1/timeline/events`
- **前端**: `TimelinePage.tsx` (add event button)
- **请求体**: Event对象
- **状态**: ❌ 未实现

### 4.3 获取单个事件详情
- **端点**: `GET /api/v1/timeline/events/{event_id}`
- **前端**: `TimelineEventDetailModal.tsx`
- **响应**: 完整的Event对象
- **状态**: ❌ 未实现

### 4.4 按时间组织数据
- **端点**: `PUT /api/v1/timeline/organize`
- **前端**: `TimelinePage.tsx` (organize button)
- **请求体**:
```json
{
  "document_ids": ["string"],
  "auto_extract_dates": boolean,
  "grouping": "day|month|year"
}
```
- **响应**: 组织后的时间线结构
- **状态**: ❌ 未实现

---

## 5. 报告生成 (Report Generation) - 🟡 部分实现

### 5.1 生成报告
- **端点**: `POST /api/v1/reports/generate`
- **前端页面**: `pages/Reports/ReportGeneratorPage.tsx`
- **请求体**:
```json
{
  "title": "string",
  "report_type": "research|summary|analysis",
  "time_range": {
    "start": "datetime",
    "end": "datetime"
  },
  "include": {
    "charts": boolean,
    "maps": boolean,
    "tables": boolean,
    "wordcloud": boolean
  },
  "data_sources": {
    "document_ids": ["string"],
    "categories": ["string"]
  },
  "format": "docx|pdf|html"
}
```
- **响应**:
```json
{
  "task_id": "string",
  "status": "processing"
}
```
- **状态**: ⚠️ 部分实现 (后端任务存在，但前端集成不完整)
- **优先级**: 🟡 HIGH

### 5.2 获取报告状态和内容
- **端点**: `GET /api/v1/reports/{report_id}`
- **前端**: `ReportListPage.tsx`, `ReportDetailPage.tsx`
- **响应**:
```json
{
  "id": "string",
  "title": "string",
  "status": "processing|completed|failed",
  "progress": 0-100,
  "content": {
    "summary": "string",
    "sections": [...],
    "charts": [...],
    "statistics": {...}
  },
  "download_url": "string",
  "created_at": "datetime"
}
```
- **状态**: ⚠️ 部分实现

### 5.3 下载报告
- **端点**: `GET /api/v1/reports/{report_id}/download`
- **前端**: `ReportDetailPage.tsx` (download button)
- **查询参数**: `?format=docx|pdf|html`
- **响应**: 文件下载
- **状态**: ❌ 未实现
- **优先级**: 🟡 HIGH

### 5.4 生成总结文档
- **端点**: `POST /api/v1/reports/summary-document`
- **前端页面**: `pages/Reports/SummaryGeneratorPage.tsx`
- **请求体**:
```json
{
  "document_ids": ["string"],
  "summary_type": "comprehensive|executive|technical",
  "max_length": int,
  "include_citations": boolean
}
```
- **响应**: 完整的总结文档
- **状态**: ❌ 未实现
- **优先级**: 🟡 HIGH

---

## 6. 文档管理 (Document Management) - 🟢 部分实现

### 6.1 获取文档列表
- **端点**: `GET /api/v1/documents`
- **前端页面**: `pages/Documents/DocumentList.tsx`
- **查询参数**: `?page=1&limit=20&sort=created_at&order=desc&tag=string`
- **响应**: 文档列表 + 分页信息
- **状态**: ✅ 已实现

### 6.2 上传文档
- **端点**: `POST /api/v1/documents/upload`
- **前端**: `DocumentList.tsx` (upload button)
- **请求**: `multipart/form-data`
- **状态**: ✅ 已实现

### 6.3 批量上传（拖拽）
- **端点**: `POST /api/v1/documents/batch-upload`
- **前端**: `DocumentList.tsx` (drag-drop zone)
- **请求**: 多个文件
- **响应**: 批量上传任务ID
- **状态**: ❌ 未实现
- **优先级**: 🟢 MEDIUM

### 6.4 获取文档详情
- **端点**: `GET /api/v1/documents/{doc_id}`
- **前端页面**: `pages/Documents/DocumentDetail.tsx`
- **响应**: 完整文档对象 + metadata + 实体 + 关系
- **状态**: ✅ 已实现

### 6.5 更新文档
- **端点**: `PUT /api/v1/documents/{doc_id}`
- **前端页面**: `pages/Documents/DocumentEditor.tsx`
- **请求体**: 更新的字段
- **状态**: ✅ 已实现

### 6.6 删除文档
- **端点**: `DELETE /api/v1/documents/{doc_id}`
- **前端**: `DocumentCard.tsx` (delete button)
- **状态**: ⚠️ 部分实现

### 6.7 管理文档标签
- **端点**: `POST /api/v1/documents/{doc_id}/tags`
- **前端**: `DocumentDetail.tsx` (tag manager)
- **请求体**: `{"tags": ["string"]}`
- **状态**: ❌ 未实现

---

## 7. 仪表盘 (Dashboard) - 🟢 缺失

### 7.1 获取统计数据
- **端点**: `GET /api/v1/dashboard/stats`
- **前端页面**: `pages/Dashboard/index.tsx`
- **响应**:
```json
{
  "total_documents": int,
  "total_entities": int,
  "total_relations": int,
  "active_tasks": int,
  "storage_used": "string"
}
```
- **状态**: ❌ 未实现
- **优先级**: 🟢 MEDIUM

### 7.2 获取趋势数据
- **端点**: `GET /api/v1/dashboard/trends`
- **查询参数**: `?period=7d|30d|90d`
- **响应**: 时间序列数据
- **状态**: ❌ 未实现

### 7.3 获取最近活动
- **端点**: `GET /api/v1/dashboard/activities`
- **查询参数**: `?limit=10`
- **响应**: 活动日志列表
- **状态**: ❌ 未实现

---

## 8. 知识图谱 (Knowledge Graph) - ✅ 已实现

### 8.1 获取图谱数据
- **端点**: `GET /api/v1/knowledge-graph/graph`
- **状态**: ✅ 已实现

### 8.2 获取实体列表
- **端点**: `GET /api/v1/knowledge-graph/entities`
- **状态**: ✅ 已实现

### 8.3 获取实体详情
- **端点**: `GET /api/v1/knowledge-graph/entities/{entity_id}`
- **状态**: ✅ 已实现

### 8.4 创建关系
- **端点**: `POST /api/v1/knowledge-graph/relations`
- **状态**: ✅ 已实现

### 8.5 查询子图
- **端点**: `POST /api/v1/knowledge-graph/query`
- **状态**: ✅ 已实现

### 8.6 图谱统计
- **端点**: `GET /api/v1/knowledge-graph/statistics`
- **状态**: ✅ 已实现

---

## 9. 搜索功能 (Search) - ✅ 已实现

### 9.1 全局搜索
- **端点**: `GET /api/v1/search`
- **状态**: ✅ 已实现

### 9.2 语义搜索
- **端点**: `POST /api/v1/search/semantic`
- **状态**: ✅ 已实现

### 9.3 图搜索
- **端点**: `POST /api/v1/search/graph`
- **状态**: ✅ 已实现

---

## 10. 数据分析 (Analytics) - 🟢 部分实现

### 10.1 主题分布
- **端点**: `GET /api/v1/analytics/topics`
- **前端页面**: `pages/Analytics/AnalyticsPage.tsx`
- **状态**: ⚠️ 部分实现

### 10.2 地理热力图数据
- **端点**: `GET /api/v1/analytics/geo-heatmap`
- **前端**: `AnalyticsPage.tsx` (map section)
- **响应**: GeoJSON格式数据
- **状态**: ❌ 未实现

### 10.3 时间序列分析
- **端点**: `GET /api/v1/analytics/timeseries`
- **查询参数**: `?metric=documents|entities&granularity=day|month`
- **状态**: ⚠️ 部分实现

### 10.4 实体网络分析
- **端点**: `GET /api/v1/analytics/entity-network`
- **响应**: 网络图数据
- **状态**: ❌ 未实现

### 10.5 关键词趋势
- **端点**: `GET /api/v1/analytics/keyword-trends`
- **查询参数**: `?keywords=["string"]&time_range=1y`
- **状态**: ❌ 未实现

---

## 实现优先级路线图

### 🔴 Phase 1: Critical (立即实现 - 1周)
1. **认证系统** - 5个端点
   - 实现JWT认证
   - 用户注册/登录/登出
   - 权限中间件

2. **技能管理系统** - 7个端点
   - 技能上传和验证机制
   - 激活/停用功能
   - 约束系统确保技能可用

3. **业态分析** - 4个端点
   - 类别管理
   - 详细分析页面数据
   - 统计和趋势

### 🟡 Phase 2: High Priority (第2-3周)
4. **编年史/时间线** - 4个端点
   - 事件管理
   - 时间线可视化数据
   - 自动组织功能

5. **报告生成完善** - 2个端点
   - 下载功能
   - 总结文档生成

### 🟢 Phase 3: Medium Priority (第4周)
6. **文档管理增强** - 3个端点
   - 批量上传（拖拽）
   - 标签管理
   - 删除功能完善

7. **仪表盘** - 3个端点
8. **数据分析增强** - 3个端点

---

## 安全层设计

### 认证中间件
```python
# fieldmind-backend/app/middleware/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

async def verify_token(credentials: HTTPAuthorizationCredentials):
    # JWT验证逻辑
    pass

async def require_role(required_role: str):
    # 角色验证
    pass
```

### 权限装饰器
```python
@router.get("/api/v1/documents")
@require_auth
@require_role("researcher")
async def get_documents():
    pass
```

---

## 数据库模型扩展

### 需要新增的表
1. `users` - 用户表
2. `skills` - 技能表
3. `skill_validations` - 技能验证记录
4. `industry_categories` - 业态类别
5. `timeline_events` - 时间线事件
6. `reports` - 报告表
7. `activity_logs` - 活动日志

---

## 前端服务层完整实现

### authService.ts
```typescript
export const authService = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken })
}
```

### skillService.ts (新增)
```typescript
export const skillService = {
  getAll: (params) => api.get('/skills', { params }),
  upload: (file, metadata) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('metadata', JSON.stringify(metadata))
    return api.post('/skills/upload', formData)
  },
  activate: (id) => api.put(`/skills/${id}/activate`),
  deactivate: (id) => api.put(`/skills/${id}/deactivate`),
  delete: (id) => api.delete(`/skills/${id}`),
  test: (id, testData) => api.post(`/skills/${id}/test`, testData),
  getAvailableForTask: (taskType) => api.get('/skills/available-for-task', { params: { task_type: taskType } })
}
```

### industryService.ts (新增)
```typescript
export const industryService = {
  getCategories: () => api.get('/industry/categories'),
  getDetails: (category) => api.get(`/industry/${category}/details`),
  getStatistics: (category) => api.get(`/industry/${category}/statistics`),
  getTrends: (category, timeRange) => api.get(`/industry/${category}/trends`, { params: { time_range: timeRange } })
}
```

### timelineService.ts (新增)
```typescript
export const timelineService = {
  getEvents: (params) => api.get('/timeline/events', { params }),
  createEvent: (data) => api.post('/timeline/events', data),
  getEvent: (id) => api.get(`/timeline/events/${id}`),
  organize: (data) => api.put('/timeline/organize', data)
}
```

---

## WebSocket端点（实时功能）

### 任务进度推送
- **端点**: `ws://localhost:8000/ws/tasks/{task_id}`
- **前端**: 所有长时间运行的任务页面
- **消息格式**:
```json
{
  "type": "progress|completed|error",
  "progress": 0-100,
  "message": "string",
  "data": {}
}
```
- **状态**: ❌ 未实现

---

## 总结

**当前状态**:
- ✅ 知识图谱和搜索功能完整
- ⚠️ 文档管理和报告生成部分实现
- ❌ 认证、技能管理、业态分析、时间线完全缺失

**关键问题**:
1. 没有认证系统 - 安全隐患
2. 没有技能管理 - 无法实现动态技能加载
3. 没有业态分析 - 核心功能缺失
4. 没有时间线视图 - 数据组织功能缺失
5. 前后端API调用不完整

**下一步行动**:
1. 立即实现认证系统（JWT + 角色权限）
2. 实现完整的技能管理系统（上传、验证、激活）
3. 实现业态分析端点和前端页面
4. 实现编年史/时间线功能
5. 完善报告生成和下载
6. 测试所有前后端API调用
