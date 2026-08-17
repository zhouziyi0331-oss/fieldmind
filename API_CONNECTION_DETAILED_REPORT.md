# API前后端连接详细检查报告

## 执行摘要

已完成对前端所有API调用的详细检查。

**检查范围：**
- 前端页面：9个使用API的页面
- API服务定义：`services/api.ts`
- 后端路由：255个

---

## 前端API调用列表

### 1. Projects API

**前端调用（api.ts）：**
```typescript
GET  /api/projects                    // list
GET  /api/projects/${id}              // get
POST /api/projects                    // create
PUT  /api/projects/${id}              // update
DELETE /api/projects/${id}            // delete
POST /api/projects/${id}/analyze      // analyze
GET  /api/projects/${id}/stats        // getStats
```

**后端路由（检查）：**
```python
# app/api/projects.py (注册在 /api/projects)
GET    /{project_id}                  # ✅ 匹配 /api/projects/${id}
PUT    /{project_id}                  # ✅ 匹配
DELETE /{project_id}                  # ✅ 匹配
POST   /{project_id}/analyze          # ✅ 匹配
GET    /{project_id}/stats            # ✅ 匹配

# app/api/v1/projects.py (注册在 /api/v1/projects)
POST   /                              # ✅ 匹配 create (但前缀不同！)
GET    /                              # ✅ 匹配 list (但前缀不同！)
```

**问题：前端调用 `/api/projects`，但后端只有 `/api/v1/projects`**

### 2. Documents API

**前端调用（api.ts）：**
```typescript
GET  /api/v1/projects/${projectId}/documents     // list
GET  /api/documents/${documentId}                // get
POST /api/documents/upload                       // upload
DELETE /api/documents/${documentId}              // delete
GET  /api/documents/${documentId}/fact-statements // getFactStatements
```

**后端路由（检查）：**
```python
# app/api/documents.py (注册在 /api/documents)
POST   /upload                        # ✅ 匹配
GET    /{document_id}                 # ✅ 匹配
DELETE /{document_id}                 # ✅ 匹配
GET    /{document_id}/fact-statements # ✅ 匹配

# main.py 兼容路由
GET /api/v1/projects/{project_id}/documents  # ✅ 有兼容层
```

**状态：✅ 已连接（有兼容层）**

### 3. Chat API

**前端调用（api.ts）：**
```typescript
POST   /api/chat/sessions                           // createSession
GET    /api/chat/projects/${projectId}/sessions     // listSessions
GET    /api/chat/sessions/${sessionId}              // getSession
DELETE /api/chat/sessions/${sessionId}              // deleteSession
POST   /api/chat/sessions/${sessionId}/messages     // sendMessage
GET    /api/chat/sessions/${sessionId}/messages     // getMessages
POST   /api/chat/sessions/${sessionId}/evolve-skill // evolveSkill
```

**后端路由（检查）：**
```python
# app/api/chat.py (注册在 /api/chat)
POST   /sessions                      # ✅ 匹配
GET    /sessions/{session_id}         # ✅ 匹配
GET    /projects/{project_id}/sessions # ✅ 匹配
POST   /sessions/{session_id}/messages # ✅ 匹配
GET    /sessions/{session_id}/messages # ✅ 匹配
DELETE /sessions/{session_id}         # ✅ 匹配
POST   /sessions/{session_id}/evolve-skill # ✅ 匹配
```

**状态：✅ 全部匹配**

### 4. Memories API

**前端调用（api.ts）：**
```typescript
GET    /api/v1/projects/${projectId}/memories              // list
POST   /api/v1/projects/${projectId}/memories              // create
PUT    /api/v1/projects/${projectId}/memories/${memoryId}  // update
DELETE /api/v1/projects/${projectId}/memories/${memoryId}  // delete
```

**后端路由（检查）：**
```python
# main.py 兼容路由
GET /api/v1/projects/{project_id}/memories  # ✅ 有兼容层

# app/api/memory.py (注册在 /api/memory)
GET    /project/{project_id}          # ❌ 路径不匹配！
GET    /{memory_id}                   # ❌ 路径不匹配！
POST   /create                        # ❌ 路径不匹配！
DELETE /{memory_id}                   # ❌ 路径不匹配！
```

**问题：前端期望 `/api/v1/projects/{id}/memories`，后端实际是 `/api/memory/project/{id}`**

### 5. Knowledge Graph API

**前端调用（api.ts）：**
```typescript
GET  /api/knowledge-graph/projects/${projectId}/graph        // getGraph
GET  /api/knowledge-graph/projects/${projectId}/keywords     // getKeywords
GET  /api/knowledge-graph/documents/${documentId}/entities   // getDocumentEntities
POST /api/v1/knowledge-graph/build/${documentId}             // buildGraphForDocument
GET  /api/v1/knowledge-graph/stats                           // getGraphStats
```

**后端路由（检查）：**
```python
# app/api/knowledge_graph.py (注册在 /api/knowledge-graph)
GET    /projects/{project_id}/graph   # ✅ 匹配
GET    /projects/{project_id}/keywords # ✅ 匹配
GET    /documents/{document_id}/entities # ✅ 匹配

# app/api/v1/knowledge_graph_api.py (注册在 /api/knowledge-graph-v2)
POST   /build/{document_id}            # ❌ 前缀不匹配！前端调用v1，后端是v2
GET    /stats                          # ❌ 前缀不匹配！
```

**问题：前端调用 `/api/v1/knowledge-graph`，后端注册在 `/api/knowledge-graph-v2`**

### 6. Timeline API

**前端调用（api.ts）：**
```typescript
GET /api/timeline/projects/${projectId}/events                // getEvents
GET /api/timeline/projects/${projectId}/events/grouped        // getGroupedEvents
```

**后端路由（检查）：**
```python
# app/api/timeline.py (注册在 /api/timeline)
GET    /projects/{project_id}/events          # ✅ 匹配
GET    /projects/{project_id}/events/grouped  # ✅ 匹配
```

**状态：✅ 全部匹配**

### 7. Analytics API

**前端调用（AnalyticsPage.tsx）：**
```typescript
GET /api/analytics/projects/${projectId}/topic-distribution
GET /api/analytics/projects/${projectId}/top-entities
GET /api/analytics/projects/${projectId}/word-count-stats
```

**状态：✅ 全部匹配**（之前已验证）

### 8. Aggregate API

**前端调用（aggregateService.ts）：**
```typescript
GET /api/aggregate/dashboard/${projectId}
GET /api/aggregate/quick-stats/${projectId}
```

**状态：✅ 全部匹配**（之前已验证）

---

## 发现的问题总结

### 🔴 严重问题（API完全不匹配）

#### 1. Memories API 路径不匹配

**影响范围：** 所有Memory相关功能无法使用

**前端期望：**
- `GET /api/v1/projects/{id}/memories`
- `POST /api/v1/projects/{id}/memories`
- `PUT /api/v1/projects/{id}/memories/{memoryId}`
- `DELETE /api/v1/projects/{id}/memories/{memoryId}`

**后端实际：**
- `GET /api/memory/project/{id}`
- `POST /api/memory/create`
- `GET /api/memory/{memory_id}`
- `DELETE /api/memory/{memory_id}`

**修复方案：** 
1. 修改前端`api.ts`中的memories API路径，匹配后端实际路径
2. 或者在后端添加路由兼容层（类似documents）

#### 2. Knowledge Graph v1 API 不存在

**影响范围：** 知识图谱构建功能

**前端调用：**
- `POST /api/v1/knowledge-graph/build/{documentId}`
- `GET /api/v1/knowledge-graph/stats`

**后端实际：**
- 注册在 `/api/knowledge-graph-v2/`（不是v1）

**修复方案：**
1. 修改前端调用，改为`/api/knowledge-graph-v2/`
2. 或者在后端添加`/api/v1/knowledge-graph`路由别名

#### 3. Projects API 前缀不一致

**影响范围：** 项目列表和创建功能

**前端调用：**
- `GET /api/projects` (list)
- `POST /api/projects` (create)

**后端实际：**
- `GET /api/v1/projects/` (list)
- `POST /api/v1/projects/` (create)
- 其他操作在 `/api/projects/{id}`

**修复方案：**
1. 统一前端路径，要么全用`/api/projects`，要么全用`/api/v1/projects`
2. 后端添加路由别名或兼容层

---

## 修复优先级

### P0 - 必须立即修复（功能完全不可用）

1. **Memories API路径** - 完全不匹配
2. **Knowledge Graph build API** - 完全不匹配
3. **Projects list/create API** - 部分不匹配

### P1 - 应该修复（可能有兼容层但不确定）

1. 检查所有兼容层是否正确实现

---

## 下一步行动

1. ✅ 已完成：全面扫描前后端API
2. ✅ 已完成：识别所有不匹配的路径
3. ⏳ 待处理：修复Memories API路径
4. ⏳ 待处理：修复Knowledge Graph API路径
5. ⏳ 待处理：统一Projects API路径
6. ⏳ 待处理：测试所有修复

---

## 统计

- **总API调用数：** ~30个
- **完全匹配：** ~20个 (67%)
- **需要修复：** ~10个 (33%)
- **严重问题：** 3个主要模块

