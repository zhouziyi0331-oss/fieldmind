# FieldMind API 参考文档

**版本**: 1.0.0  
**基础URL**: `http://your-domain.com/api`  
**认证方式**: JWT Bearer Token

---

## 目录

- [认证](#认证)
- [项目管理](#项目管理)
- [文档管理](#文档管理)
- [智能分析](#智能分析)
- [对话系统](#对话系统)
- [提案生成](#提案生成)
- [监控和日志](#监控和日志)
- [错误码](#错误码)

---

## 认证

### 注册用户

```http
POST /api/auth/register
```

**请求体**:
```json
{
  "username": "researcher01",
  "email": "researcher@example.com",
  "password": "secure_password",
  "role": "researcher"
}
```

**响应**:
```json
{
  "id": 1,
  "username": "researcher01",
  "email": "researcher@example.com",
  "role": "researcher",
  "created_at": "2026-08-02T10:00:00Z"
}
```

### 用户登录

```http
POST /api/auth/login
```

**请求体**:
```json
{
  "username": "researcher01",
  "password": "secure_password"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 获取当前用户

```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "id": 1,
  "username": "researcher01",
  "email": "researcher@example.com",
  "role": "researcher",
  "permissions": [
    "project:create",
    "project:read",
    "document:upload",
    "analysis:create"
  ]
}
```

---

## 项目管理

### 创建项目

```http
POST /api/projects
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "name": "布依族山歌调研",
  "description": "贵州布依族山歌的田野调查",
  "project_type": "cultural_research"
}
```

**响应**:
```json
{
  "id": 1,
  "name": "布依族山歌调研",
  "description": "贵州布依族山歌的田野调查",
  "project_type": "cultural_research",
  "owner_id": 1,
  "created_at": "2026-08-02T10:00:00Z",
  "updated_at": "2026-08-02T10:00:00Z",
  "document_count": 0,
  "analysis_count": 0
}
```

### 获取项目列表

```http
GET /api/projects?page=1&page_size=20
Authorization: Bearer {access_token}
```

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大100）
- `search`: 搜索关键词
- `project_type`: 项目类型筛选

**响应**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "布依族山歌调研",
      "description": "贵州布依族山歌的田野调查",
      "document_count": 5,
      "analysis_count": 3,
      "created_at": "2026-08-02T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

### 获取项目详情

```http
GET /api/projects/{project_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "id": 1,
  "name": "布依族山歌调研",
  "description": "贵州布依族山歌的田野调查",
  "project_type": "cultural_research",
  "owner_id": 1,
  "created_at": "2026-08-02T10:00:00Z",
  "updated_at": "2026-08-02T10:00:00Z",
  "statistics": {
    "document_count": 5,
    "total_size_bytes": 15728640,
    "analysis_count": 3,
    "chunk_count": 125
  }
}
```

### 更新项目

```http
PUT /api/projects/{project_id}
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "name": "布依族山歌深度调研",
  "description": "更新后的描述"
}
```

### 删除项目

```http
DELETE /api/projects/{project_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "message": "项目已删除",
  "project_id": 1
}
```

---

## 文档管理

### 上传文档

```http
POST /api/projects/{project_id}/documents
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**表单数据**:
- `file`: 文件内容（必需）
- `description`: 文档描述（可选）

**响应**:
```json
{
  "id": 1,
  "project_id": 1,
  "filename": "布依族山歌调研报告.pdf",
  "file_size": 2097152,
  "file_type": "application/pdf",
  "description": "初步调研报告",
  "status": "processing",
  "uploaded_at": "2026-08-02T10:00:00Z"
}
```

### 获取文档列表

```http
GET /api/projects/{project_id}/documents
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "items": [
    {
      "id": 1,
      "filename": "布依族山歌调研报告.pdf",
      "file_size": 2097152,
      "status": "completed",
      "chunk_count": 25,
      "uploaded_at": "2026-08-02T10:00:00Z"
    }
  ],
  "total": 1
}
```

### 获取文档详情

```http
GET /api/documents/{document_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "id": 1,
  "project_id": 1,
  "filename": "布依族山歌调研报告.pdf",
  "file_size": 2097152,
  "file_type": "application/pdf",
  "description": "初步调研报告",
  "status": "completed",
  "chunk_count": 25,
  "processing_time_seconds": 45,
  "uploaded_at": "2026-08-02T10:00:00Z",
  "processed_at": "2026-08-02T10:00:45Z"
}
```

### 删除文档

```http
DELETE /api/documents/{document_id}
Authorization: Bearer {access_token}
```

---

## 智能分析

### 关键词检索

```http
POST /api/keyword-search
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "project_id": 1,
  "query": "山歌 布依族",
  "top_k": 10
}
```

**响应**:
```json
{
  "results": [
    {
      "chunk_id": 101,
      "document_id": 1,
      "document_name": "调研报告.pdf",
      "text": "布依族山歌是贵州布依族的传统音乐形式...",
      "score": 0.95,
      "position": {
        "start": 1250,
        "end": 1450
      }
    }
  ],
  "total": 10,
  "query_time_ms": 25.3
}
```

### 文创分析

```http
POST /api/creative-analysis
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "project_id": 1,
  "query": "如何基于布依族山歌开发文创产品？"
}
```

**响应**:
```json
{
  "id": 1,
  "project_id": 1,
  "analysis_type": "creative",
  "query": "如何基于布依族山歌开发文创产品？",
  "result": {
    "creative_possibilities": [
      {
        "title": "数字音乐专辑",
        "description": "制作布依族山歌精选专辑...",
        "feasibility_score": 0.85,
        "implementation_steps": [
          "收集整理山歌录音",
          "专业录音棚重制",
          "数字平台发行"
        ]
      }
    ]
  },
  "created_at": "2026-08-02T10:05:00Z",
  "processing_time_seconds": 120
}
```

### 业态分析

```http
POST /api/business-analysis
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "project_id": 1,
  "query": "适合发展哪些旅游业态？"
}
```

**响应**:
```json
{
  "id": 2,
  "project_id": 1,
  "analysis_type": "business",
  "result": {
    "existing_businesses": [
      {
        "name": "民宿",
        "description": "现有10家民宿",
        "annual_revenue": "50-100万"
      }
    ],
    "recommended_businesses": [
      {
        "name": "山歌体验馆",
        "description": "游客互动体验布依族山歌",
        "investment_scale": "30-50万",
        "revenue_potential": "年收入60-100万",
        "risk_level": "中"
      }
    ]
  },
  "created_at": "2026-08-02T10:10:00Z"
}
```

### 材料溯源

```http
GET /api/source-traceback/{analysis_id}
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "analysis_id": 1,
  "statements": [
    {
      "id": 1,
      "statement": "布依族山歌具有独特的音乐特征",
      "sources": [
        {
          "document_id": 1,
          "document_name": "调研报告.pdf",
          "chunk_text": "布依族山歌采用五声音阶...",
          "relevance_score": 0.92,
          "position": {
            "start": 1250,
            "end": 1450
          }
        }
      ]
    }
  ],
  "coverage_rate": 1.0,
  "average_sources_per_statement": 3.0
}
```

---

## 对话系统

### 创建对话

```http
POST /api/conversation-memory
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "project_id": 1,
  "question": "布依族山歌有哪些类型？"
}
```

**响应**:
```json
{
  "conversation_id": 1,
  "question": "布依族山歌有哪些类型？",
  "answer": "根据调研材料，布依族山歌主要分为以下几类：\n1. 情歌：表达爱情...\n2. 劳动歌：伴随劳动...\n3. 节庆歌：节日庆典...",
  "confidence": 0.85,
  "sources": [
    {
      "chunk_id": 101,
      "document_name": "调研报告.pdf",
      "text": "布依族山歌类型丰富...",
      "relevance_score": 0.92
    }
  ],
  "created_at": "2026-08-02T10:15:00Z"
}
```

### 获取对话历史

```http
GET /api/conversation-memory/history/{project_id}?limit=20
Authorization: Bearer {access_token}
```

**响应**:
```json
{
  "conversations": [
    {
      "id": 1,
      "question": "布依族山歌有哪些类型？",
      "answer": "...",
      "created_at": "2026-08-02T10:15:00Z"
    }
  ],
  "total": 1
}
```

---

## 提案生成

### 生成提案

```http
POST /api/proposal/generate
Authorization: Bearer {access_token}
```

**请求体**:
```json
{
  "project_id": 1,
  "proposal_type": "government",
  "include_budget": true,
  "include_risks": true
}
```

**提案类型**:
- `government`: 政府汇报型
- `academic`: 学术汇报型
- `business`: 商业计划型

**响应**:
```json
{
  "id": 1,
  "project_id": 1,
  "proposal_type": "government",
  "content": {
    "title": "布依族山歌文化保护与开发项目提案",
    "sections": [
      {
        "title": "项目背景",
        "content": "..."
      },
      {
        "title": "核心发现",
        "content": "..."
      }
    ]
  },
  "word_count": 3500,
  "created_at": "2026-08-02T10:20:00Z"
}
```

### 导出提案

```http
GET /api/proposal/{proposal_id}/export?format=html
Authorization: Bearer {access_token}
```

**查询参数**:
- `format`: 导出格式（`markdown` 或 `html`）

**响应**:
- Content-Type: `text/html` 或 `text/markdown`
- 文件内容

---

## 监控和日志

### Prometheus指标

```http
GET /metrics
```

**响应** (Prometheus格式):
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/projects",status="200"} 1523

# HELP http_request_duration_seconds HTTP request latency
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/projects",le="0.1"} 1200
```

### 健康检查

```http
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": 1722576000.123,
  "response_time_ms": 15.2,
  "services": {
    "api": "ok",
    "database": "ok",
    "redis": "ok",
    "neo4j": "not_configured"
  }
}
```

### 系统指标

```http
GET /monitoring/metrics
```

**响应**:
```json
{
  "timestamp": "2026-08-02T10:25:00Z",
  "system": {
    "cpu_percent": 35.2,
    "memory_percent": 62.8,
    "disk_percent": 45.1
  },
  "process": {
    "memory_mb": 512.5,
    "threads": 8
  }
}
```

### 最近日志

```http
GET /monitoring/logs/recent?lines=100
```

**响应**:
```json
{
  "logs": [
    "2026-08-02 10:25:00 | INFO | app.main:health_check:126 - Health check passed"
  ],
  "total_lines": 5000,
  "returned_lines": 100
}
```

---

## 错误码

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 验证失败 |
| 429 | 请求过多 |
| 500 | 服务器错误 |

### 错误响应格式

```json
{
  "detail": "错误描述信息",
  "error_code": "PROJECT_NOT_FOUND",
  "timestamp": "2026-08-02T10:30:00Z"
}
```

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| `AUTH_INVALID_CREDENTIALS` | 用户名或密码错误 |
| `AUTH_TOKEN_EXPIRED` | Token已过期 |
| `AUTH_INSUFFICIENT_PERMISSIONS` | 权限不足 |
| `PROJECT_NOT_FOUND` | 项目不存在 |
| `DOCUMENT_UPLOAD_FAILED` | 文档上传失败 |
| `DOCUMENT_PROCESSING_FAILED` | 文档处理失败 |
| `ANALYSIS_FAILED` | 分析执行失败 |
| `RATE_LIMIT_EXCEEDED` | 超过速率限制 |

---

## 速率限制

### 限制规则

- **认证端点**: 5次/分钟
- **普通API**: 60次/分钟
- **文件上传**: 10次/分钟
- **分析任务**: 5次/分钟

### 速率限制响应头

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1722576060
```

---

## SDK和示例

### Python示例

```python
import requests

# 登录获取token
response = requests.post(
    'http://localhost:8000/api/auth/login',
    json={
        'username': 'researcher01',
        'password': 'password123'
    }
)
token = response.json()['access_token']

# 创建项目
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:8000/api/projects',
    headers=headers,
    json={
        'name': '新项目',
        'description': '项目描述'
    }
)
project = response.json()
print(f"项目创建成功: {project['id']}")
```

### JavaScript示例

```javascript
// 登录
const loginResponse = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'researcher01',
    password: 'password123'
  })
});
const { access_token } = await loginResponse.json();

// 获取项目列表
const projectsResponse = await fetch('http://localhost:8000/api/projects', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const projects = await projectsResponse.json();
console.log('项目列表:', projects);
```

---

**文档版本**: 1.0.0  
**最后更新**: 2026-08-02  
**在线文档**: http://your-domain.com/docs
