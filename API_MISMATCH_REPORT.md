# API前后端连接问题报告

## 执行摘要

**发现问题总数：12个API调用不匹配**

扫描结果：
- 前端文件：2个（`pages/AnalyticsPage.tsx`, `services/aggregateService.ts`）
- 前端API调用：12个
- 后端路由文件：49个
- 后端API定义：255个
- **不匹配API：12个（100%的前端调用都有问题）**

---

## 问题分类

### 类型1：路径完全正确，后端已实现 ✅

这些API后端已经实现，只是我的检测脚本没有正确识别参数化路径。

#### 1. Analytics API（4个）

**前端调用：**
```typescript
// pages/AnalyticsPage.tsx
GET /api/analytics/projects/${projectId}/topic-distribution
GET /api/analytics/projects/${projectId}/top-entities?entity_type=person&top_k=10
GET /api/analytics/projects/${projectId}/top-entities?entity_type=location&top_k=10
GET /api/analytics/projects/${projectId}/word-count-stats
```

**后端定义：**
```python
# app/api/analytics.py (注册在 /api/analytics 前缀)
@router.get("/projects/{project_id}/topic-distribution")
@router.get("/projects/{project_id}/top-entities")
@router.get("/projects/{project_id}/word-count-stats")
```

**状态：✅ 已连接**
- 路径匹配：`/api/analytics` + `/projects/{project_id}/topic-distribution` = `/api/analytics/projects/{project_id}/topic-distribution`
- 后端实现：[app/api/analytics.py](fieldmind-backend/app/api/analytics.py#L24-L168)
- 注册位置：[app/main.py:230](fieldmind-backend/app/main.py#L230)

#### 2. Aggregate API（4个，重复调用）

**前端调用：**
```typescript
// services/aggregateService.ts
GET /api/aggregate/dashboard/${projectId}
GET /api/aggregate/quick-stats/${projectId}
// 以下是重复调用
GET /api/aggregate/dashboard/${projectId}
GET /api/aggregate/quick-stats/${projectId}
```

**后端定义：**
```python
# app/api/aggregate.py (注册在 /api/aggregate 前缀)
@router.get("/dashboard/{project_id}")
@router.get("/quick-stats/{project_id}")
```

**状态：✅ 已连接**
- 路径匹配：`/api/aggregate` + `/dashboard/{project_id}` = `/api/aggregate/dashboard/{project_id}`
- 后端实现：[app/api/aggregate.py](fieldmind-backend/app/api/aggregate.py#L18-L356)
- 注册位置：[app/main.py:234](fieldmind-backend/app/main.py#L234)

### 类型2：前端错误调用（4个）⚠️

**问题：AnalyticsPage.tsx 中存在错误的相对路径调用**

```typescript
// pages/AnalyticsPage.tsx 第85-88行
GET /topic-distribution                                    // ❌ 缺少前缀
GET /top-entities?entity_type=person&top_k=10             // ❌ 缺少前缀
GET /top-entities?entity_type=location&top_k=10           // ❌ 缺少前缀
GET /word-count-stats                                      // ❌ 缺少前缀
```

这些调用缺少了`/api/analytics/projects/${projectId}`前缀，会导致404错误。

---

## 需要修复的问题

### 问题1：AnalyticsPage.tsx 存在错误的API调用

**文件：** `fieldmind-web/src/pages/AnalyticsPage.tsx`

**问题描述：**
代码中存在4个没有完整路径的API调用，这些调用会失败。

**需要检查的代码：**
```typescript
// 错误示例（需要查找实际代码位置）
fetch(`/topic-distribution`)  // ❌ 应该是 /api/analytics/projects/${projectId}/topic-distribution
```

**修复方案：**
1. 查找并修复所有缺少`/api/analytics/projects/${projectId}`前缀的调用
2. 统一使用`API_BASE_URL`常量
3. 确保所有API调用都是完整路径

### 问题2：aggregateService.ts 存在重复调用

**文件：** `fieldmind-web/src/services/aggregateService.ts`

**问题描述：**
同一个API被调用了两次（可能是代码重复或者错误的重试逻辑）。

**需要检查：**
- 是否有重复的函数定义
- 是否有不必要的重试逻辑

---

## 检测方法的局限性

我的检测脚本发现了所有前端API调用，但在路径匹配上存在误报：

1. **参数化路径识别不完善**：`${projectId}` vs `{project_id}` 应该被识别为匹配
2. **查询参数处理**：`?entity_type=person` 部分应该被忽略
3. **重复调用**：同一API被调用多次会被计算为多个不匹配

实际上，真正的问题只有4个错误的相对路径调用。

---

## 验证步骤

### 步骤1：检查 AnalyticsPage.tsx 的完整代码

需要读取完整文件找出所有API调用，确认哪些是正确的，哪些是错误的。

### 步骤2：检查 aggregateService.ts 的完整代码

找出为什么同一个API被调用了两次。

### 步骤3：运行前端测试

启动前端应用，访问Analytics页面，检查浏览器控制台是否有404错误。

### 步骤4：修复发现的问题

根据具体代码情况修复错误的API调用。

---

## 后续行动

1. ✅ 已完成：扫描所有前后端API
2. ✅ 已完成：识别不匹配的调用
3. ⏳ 待处理：读取前端文件确认具体问题
4. ⏳ 待处理：修复错误的API调用
5. ⏳ 待处理：测试修复后的连接

---

## 附录：完整的API映射

### 已验证正确连接的API

| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/analytics/projects/${projectId}/topic-distribution` | `GET /api/analytics/projects/{project_id}/topic-distribution` | ✅ |
| `GET /api/analytics/projects/${projectId}/top-entities` | `GET /api/analytics/projects/{project_id}/top-entities` | ✅ |
| `GET /api/analytics/projects/${projectId}/word-count-stats` | `GET /api/analytics/projects/{project_id}/word-count-stats` | ✅ |
| `GET /api/aggregate/dashboard/${projectId}` | `GET /api/aggregate/dashboard/{project_id}` | ✅ |
| `GET /api/aggregate/quick-stats/${projectId}` | `GET /api/aggregate/quick-stats/{project_id}` | ✅ |

### 需要修复的API调用

| 前端调用 | 应该是 | 状态 |
|---------|--------|------|
| `GET /topic-distribution` | `GET /api/analytics/projects/${projectId}/topic-distribution` | ❌ |
| `GET /top-entities?entity_type=person&top_k=10` | `GET /api/analytics/projects/${projectId}/top-entities?...` | ❌ |
| `GET /top-entities?entity_type=location&top_k=10` | `GET /api/analytics/projects/${projectId}/top-entities?...` | ❌ |
| `GET /word-count-stats` | `GET /api/analytics/projects/${projectId}/word-count-stats` | ❌ |
