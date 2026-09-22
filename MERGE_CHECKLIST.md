# FieldMind 文件合并清单

## fieldmind子目录独有API需要合并到主程序

### 1. document_normalization.py ✅ 需要合并
- **路由**: `/api/v1/files/{file_id}/normalize`
- **功能**: 文档规范化处理，脏数据报告
- **依赖服务**: `app.services.document_normalization.*`
- **状态**: 主程序**无此功能**

### 2. knowledge_pipeline.py ✅ 需要合并
- **路由**: `/knowledge-pipeline`
- **功能**: 知识流水线编排，端到端处理
- **依赖服务**: `app.services.knowledge_pipeline.orchestrator`
- **状态**: 主程序**无此路由**

### 3. knowledge_query.py ✅ 需要合并
- **路由**: 待确认
- **功能**: 知识查询接口
- **状态**: 需要详细检查

### 4. monitoring_api.py ✅ 需要合并
- **路由**: `/api/v1/monitoring`
- **功能**: 系统监控接口
- **状态**: 主程序**无此路由**

### 5. reader.py ✅ 需要合并
- **路由**: `/reader/timeline/{document_id}`
- **功能**: 文档阅读器，时间线视图
- **状态**: 主程序**无此路由**

### 6. export_summaries.py ⚠️ 待检查
- **功能**: 导出摘要
- **状态**: 需要检查主程序是否有替代实现

### 7. file_summaries.py ⚠️ 待检查
- **功能**: 文件摘要接口
- **状态**: 需要检查主程序是否有替代实现

## 主程序独有API（P3功能扩展）

### 已确认的新增P3功能
1. **agents_p3.py** - P3 Agent功能
2. **chronicle.py** - Chronicle编年史功能
3. **collaboration_p3.py** - P3协作功能
4. **keywords.py** - 关键词提取
5. **knowledge_graph_p3.py** - P3知识图谱
6. **llm_p3.py** - P3 LLM功能
7. **llm_providers.py** - LLM提供商管理
8. **llm_stats.py** - LLM统计
9. **notifications_p3.py** - P3通知
10. **rag_p3.py** - P3 RAG功能

## 服务层差异（36个文件）

需要执行：
```bash
diff -rq backend/src/app/services/ fieldmind/backend/src/app/services/ | grep "Only in fieldmind"
```

## 合并执行步骤

### 第1步：合并确认需要的API（5个）
```bash
cp fieldmind/backend/src/app/api/document_normalization.py backend/src/app/api/
cp fieldmind/backend/src/app/api/knowledge_pipeline.py backend/src/app/api/
cp fieldmind/backend/src/app/api/knowledge_query.py backend/src/app/api/
cp fieldmind/backend/src/app/api/monitoring_api.py backend/src/app/api/
cp fieldmind/backend/src/app/api/reader.py backend/src/app/api/
```

### 第2步：合并依赖的服务层
检查并复制：
- `app/services/document_normalization/`
- `app/services/knowledge_pipeline/`
- `app/services/monitoring/`

### 第3步：更新主路由注册
在 `backend/src/app/main.py` 中注册新路由

### 第4步：验证依赖
检查所有import是否可用

### 第5步：测试API可用性
```bash
curl http://localhost:8000/api/v1/monitoring/status
curl http://localhost:8000/reader/timeline/1
curl http://localhost:8000/knowledge-pipeline/status
```

## 风险评估

- **低风险**: API文件复制（不影响现有功能）
- **中风险**: 服务层合并（可能有依赖冲突）
- **高风险**: 数据库模型差异（需要检查models/）

## 回滚方案

如果合并后出现问题：
```bash
cd /Users/alwan
tar -xzf FieldMind_backup_*.tar.gz
```
