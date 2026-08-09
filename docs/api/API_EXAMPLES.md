# API请求示例

## 认证

### 用户注册

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "full_name": "张三"
  }'
```

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "email": "user@example.com",
  "full_name": "张三",
  "role": "viewer",
  "is_active": true,
  "created_at": "2026-08-01T06:00:00Z"
}
```

### 用户登录

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePassword123!"
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## 项目管理

### 创建项目

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "湘西十八洞村研究",
    "description": "十八洞村精准扶贫案例研究",
    "metadata": {
      "location": "湖南湘西",
      "year": 2024
    }
  }'
```

**响应**:
```json
{
  "id": "proj_123456",
  "name": "湘西十八洞村研究",
  "description": "十八洞村精准扶贫案例研究",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "metadata": {
    "location": "湖南湘西",
    "year": 2024
  },
  "created_at": "2026-08-01T06:00:00Z",
  "updated_at": "2026-08-01T06:00:00Z"
}
```

### 获取项目列表

**请求**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应**:
```json
{
  "items": [
    {
      "id": "proj_123456",
      "name": "湘西十八洞村研究",
      "description": "十八洞村精准扶贫案例研究",
      "owner_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-08-01T06:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 10
}
```

---

## 文档管理

### 上传文档

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@interview.mp4" \
  -F "project_id=proj_123456" \
  -F "title=村民访谈录音"
```

**响应**:
```json
{
  "id": "doc_789012",
  "title": "村民访谈录音",
  "filename": "interview.mp4",
  "file_type": "video",
  "file_size": 52428800,
  "project_id": "proj_123456",
  "status": "uploaded",
  "created_at": "2026-08-01T06:00:00Z"
}
```

### 处理文档

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/process" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_789012"
  }'
```

**响应**:
```json
{
  "task_id": "task_345678",
  "status": "processing",
  "message": "文档处理任务已启动"
}
```

### 批量处理文档

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch-process" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc_789012", "doc_789013", "doc_789014"]
  }'
```

**响应**:
```json
{
  "task_ids": ["task_345678", "task_345679", "task_345680"],
  "total": 3,
  "message": "批量处理任务已启动"
}
```

---

## 报告生成

### 生成完整报告

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123456",
    "title": "十八洞村研究报告",
    "tiers": ["tier1", "tier2", "tier3"]
  }'
```

**响应**:
```json
{
  "report_id": "rpt_456789",
  "status": "generating",
  "message": "报告生成任务已启动",
  "estimated_time": 300
}
```

### 生成单层报告

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/reports/generate/tier1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123456"
  }'
```

**响应**:
```json
{
  "tier": "tier1",
  "content": "# 第一层分析：信息整理\n\n## 基础统计...",
  "word_count": 8500,
  "generated_at": "2026-08-01T06:00:00Z"
}
```

---

## 智能对话

### 发送消息

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/chat/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sess_901234",
    "message": "十八洞村的主要产业是什么？",
    "project_id": "proj_123456"
  }'
```

**响应**:
```json
{
  "session_id": "sess_901234",
  "message": "根据文档分析，十八洞村的主要产业包括：1. 苗绣产业...",
  "sources": [
    {
      "document_id": "doc_789012",
      "title": "村民访谈录音",
      "relevance": 0.89
    }
  ],
  "timestamp": "2026-08-01T06:00:00Z"
}
```

### 获取对话历史

**请求**:
```bash
curl -X GET "http://localhost:8000/api/v1/chat/sessions/sess_901234/history" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**响应**:
```json
{
  "session_id": "sess_901234",
  "messages": [
    {
      "role": "user",
      "content": "十八洞村的主要产业是什么？",
      "timestamp": "2026-08-01T06:00:00Z"
    },
    {
      "role": "assistant",
      "content": "根据文档分析，十八洞村的主要产业包括...",
      "timestamp": "2026-08-01T06:00:05Z"
    }
  ],
  "total": 2
}
```

---

## 知识图谱

### 构建知识图谱

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/graph/build" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123456"
  }'
```

**响应**:
```json
{
  "task_id": "graph_567890",
  "status": "building",
  "message": "知识图谱构建任务已启动"
}
```

### 查询图谱

**请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/graph/query" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_123456",
    "query": "MATCH (p:Person)-[r:WORKS_IN]->(o:Organization) RETURN p, r, o LIMIT 10"
  }'
```

**响应**:
```json
{
  "results": [
    {
      "person": {"name": "龙德成", "age": 45},
      "relationship": {"type": "WORKS_IN", "since": 2013},
      "organization": {"name": "十八洞村委会"}
    }
  ],
  "count": 10
}
```

---

## 错误响应示例

### 400 Bad Request

```json
{
  "detail": {
    "error_code": 1002,
    "message": "数据验证失败",
    "details": {
      "field": "email",
      "issue": "邮箱格式不正确"
    }
  }
}
```

### 401 Unauthorized

```json
{
  "detail": {
    "error_code": 2002,
    "message": "无效的令牌",
    "details": {}
  }
}
```

### 403 Forbidden

```json
{
  "detail": {
    "error_code": 4004,
    "message": "无权访问该项目",
    "details": {
      "project_id": "proj_123456",
      "required_role": "owner"
    }
  }
}
```

### 404 Not Found

```json
{
  "detail": {
    "error_code": 3000,
    "message": "文档不存在",
    "details": {
      "document_id": "doc_999999"
    }
  }
}
```

### 429 Too Many Requests

```json
{
  "detail": {
    "error_code": 1006,
    "message": "请求频率超限",
    "details": {
      "limit": "10/minute",
      "retry_after": 45
    }
  }
}
```

### 500 Internal Server Error

```json
{
  "detail": {
    "error_code": 1000,
    "message": "服务器内部错误",
    "details": {}
  }
}
```
