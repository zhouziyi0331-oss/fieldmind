# FieldMind 前后端完整对接行动计划

## 📋 发现的问题

### 1. API 端点不匹配 ❌
**后端实际路由**:
```
/api/v1/auth/*          - 认证
/api/v1/projects/*      - 项目 (project_workflow)
/api/chat              - Chat对话
/api/dashboard         - Dashboard
/api/v1/dashboard/*    - Dashboard v1
/api/knowledge-graph   - 知识图谱
/api/knowledge-graph-v3/* - 知识图谱v3
/api/timeline          - 时间线
/api/workflows         - 工作流
/api/memory            - 记忆
/api/batch/*           - 批量处理
... 等等
```

**前端当前调用**:
```typescript
/api/projects          ❌ 错误
/api/documents         ❌ 错误
/api/auth/login        ❌ 错误 (应该是 /api/v1/auth/login)
```

### 2. 桌面程序位置
找到了：`/Users/alwan/Desktop/FieldMind.app`

### 3. 缺少大量页面
需要补充 20-30 个页面

---

## 🎯 立即行动

### 第一步：修复 API 服务层（立即执行）
更新所有 API 端点以匹配后端实际路由

### 第二步：补充所有缺失页面（2-3小时）
创建 20-30 个详细功能页面

### 第三步：复制到桌面程序位置
将所有文件复制到正确位置

---

让我立即开始！
