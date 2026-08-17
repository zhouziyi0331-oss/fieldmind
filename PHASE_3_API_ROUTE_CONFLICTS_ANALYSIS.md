# 阶段3：API路由冲突分析与修复计划

## 🔍 冲突发现

### 1. Documents路由冲突 ❌

**后端注册**:
- `documents.py` → `/api/documents/*` (line 253)
- `v1/documents.py` → `/api/v1/documents/*` (line 271)

**前端调用**:
```typescript
// api.ts line 141-144
documents: {
  list: (projectId) => `/api/v1/projects/${projectId}/documents`  // ✅ 使用v1
  get: (documentId) => `/api/documents/${documentId}`             // ❌ 使用非v1
  upload: (projectId, file) => `/api/documents/upload`            // ❌ 使用非v1
  delete: (documentId) => `/api/documents/${documentId}`          // ❌ 使用非v1
}
```

**问题**: 前端混用两个版本的API

---

### 2. Workflows路由冲突 ❌❌❌

**后端注册**:
- `workflows.py` → `/api/workflows/*` (line 203, legacy系统)
- `workflows_v2.py` → `/api/v2/workflows/*` (line 207, 6-Agent架构)
- `v1/workflows.py` → `/api/v1/workflows/*` (line 275, 模板系统)

**前端调用**:
```typescript
// api.ts line 212-269
workflows: {
  execute: () => `/api/workflows/execute`              // ✅ 使用legacy
  executeV2: () => `/api/v2/workflows/execute`         // ✅ 使用v2
  getStatus: (id) => `/api/workflows/${id}`            // ✅ 使用legacy
  getV2Status: (id) => `/api/v2/workflows/status/${id}` // ✅ 使用v2
  list: () => `/api/workflows`                         // ✅ 使用legacy
}
```

**问题**: 3个版本共存，v1版本未使用但已注册

---

### 3. Knowledge Graph路由冲突 ❌❌❌

**后端注册**:
- `knowledge_graph.py` → `/api/knowledge-graph/*` (line 187, 链路十一)
- `knowledge_graph_v3.py` → `/api/knowledge-graph-v3/*` (line 219, 证据链)
- `v1/knowledge_graph_api.py` → `/api/knowledge-graph-v2/*` (line 192, NetworkX)

**前端调用**:
```typescript
// api.ts line 196-209
knowledgeGraph: {
  getGraph: (projectId) => `/api/knowledge-graph/projects/${projectId}/graph`     // ✅ v1版本
  getKeywords: (projectId) => `/api/knowledge-graph/projects/${projectId}/keywords` // ✅ v1版本
  getDocumentEntities: (documentId) => `/api/knowledge-graph/documents/${documentId}/entities` // ✅ v1版本
  buildGraphForDocument: (documentId) => `/api/knowledge-graph-v2/build/${documentId}` // ✅ v2版本
  getGraphStats: () => `/api/knowledge-graph-v2/stats` // ✅ v2版本
}
```

**问题**: 3个版本共存，v3版本未使用

---

### 4. SuperAgents路由重复 ❌

**后端注册**:
```python
# main.py line 278-283
app.include_router(super_agents.router, tags=["SuperAgents"])  # 第1次
logger.info("✅ SuperAgents API已加载")

app.include_router(super_agents.router, tags=["SuperAgents"])  # 第2次（完全重复！）
logger.info("✅ SuperAgents API已加载")
```

**问题**: 完全重复注册，浪费资源

---

## 📊 统计总结

| 类别 | 注册版本数 | 前端使用 | 状态 |
|------|-----------|---------|------|
| Documents | 2 | 混用 | ❌ 需统一 |
| Workflows | 3 | legacy + v2 | ⚠️ v1未使用 |
| Knowledge Graph | 3 | v1 + v2 | ⚠️ v3未使用 |
| SuperAgents | 重复2次 | 正常 | ❌ 需删除重复 |

---

## 🎯 修复策略

### 原则
1. **前端优先**: 根据前端实际调用决定保留哪个版本
2. **向后兼容**: 添加兼容路由，不破坏现有功能
3. **清晰标注**: 废弃的路由标记 `include_in_schema=False`
4. **统一版本**: 新功能统一使用 `/api/v1/*` 或 `/api/v2/*`

### 具体方案

#### 1️⃣ Documents路由统一
- **保留**: `/api/documents/*` (新版本，前端主要使用)
- **保留**: `/api/v1/documents/*` (v1版本，仅list接口使用)
- **添加兼容路由**: 在v1版本中添加兼容处理

#### 2️⃣ Workflows路由清理
- **保留**: `/api/workflows/*` (legacy系统)
- **保留**: `/api/v2/workflows/*` (6-Agent架构)
- **移除**: `/api/v1/workflows/*` (未使用，完全删除注册)

#### 3️⃣ Knowledge Graph路由清理
- **保留**: `/api/knowledge-graph/*` (v1，前端主要使用)
- **保留**: `/api/knowledge-graph-v2/*` (NetworkX增强版，前端部分使用)
- **标记废弃**: `/api/knowledge-graph-v3/*` (证据链系统，未使用但保留代码)

#### 4️⃣ SuperAgents重复删除
- **删除**: 第二次注册（line 281-283）

---

## 📝 修复检查清单

- [ ] 1. 删除 SuperAgents 重复注册
- [ ] 2. 移除 v1/workflows 路由注册
- [ ] 3. 标记 knowledge_graph_v3 为 `include_in_schema=False`
- [ ] 4. 验证前端API调用仍正常工作
- [ ] 5. 运行后端确认无路由冲突警告
- [ ] 6. 更新API文档说明版本策略

---

## 🔄 下一步

修复完成后：
- 检查 `/docs` API文档中的路由是否清晰
- 确认没有路由冲突警告
- 前端功能测试验证
