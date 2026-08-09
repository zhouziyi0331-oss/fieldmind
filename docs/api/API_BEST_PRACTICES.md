# API最佳实践指南

**版本**: 1.0  
**更新时间**: 2026-08-01

---

## 目录

1. [认证流程](#认证流程)
2. [请求规范](#请求规范)
3. [响应规范](#响应规范)
4. [错误处理](#错误处理)
5. [速率限制](#速率限制)
6. [安全最佳实践](#安全最佳实践)
7. [性能优化](#性能优化)
8. [版本控制](#版本控制)

---

## 认证流程

### JWT认证架构

```
┌─────────────┐                                    ┌─────────────┐
│   客户端     │                                    │   API服务器  │
└──────┬──────┘                                    └──────┬──────┘
       │                                                  │
       │  1. POST /api/v1/auth/register                  │
       │     {username, email, password}                  │
       ├─────────────────────────────────────────────────>│
       │                                                  │
       │  2. 返回用户信息（未登录）                        │
       │<─────────────────────────────────────────────────┤
       │                                                  │
       │  3. POST /api/v1/auth/login                     │
       │     {username, password}                         │
       ├─────────────────────────────────────────────────>│
       │                                                  │──┐
       │                                                  │  │ 验证凭据
       │                                                  │<─┘
       │                                                  │──┐
       │                                                  │  │ 生成JWT tokens
       │                                                  │<─┘
       │  4. 返回 access_token + refresh_token            │
       │<─────────────────────────────────────────────────┤
       │                                                  │
       │  5. API请求 + Authorization: Bearer <token>     │
       ├─────────────────────────────────────────────────>│
       │                                                  │──┐
       │                                                  │  │ 验证token
       │                                                  │<─┘
       │  6. 返回数据                                     │
       │<─────────────────────────────────────────────────┤
       │                                                  │
       │  (access_token过期)                              │
       │                                                  │
       │  7. POST /api/v1/auth/refresh                   │
       │     {refresh_token}                              │
       ├─────────────────────────────────────────────────>│
       │                                                  │──┐
       │                                                  │  │ 验证refresh token
       │                                                  │<─┘
       │  8. 返回新的 access_token                        │
       │<─────────────────────────────────────────────────┤
```

### Token生命周期

| Token类型 | 有效期 | 用途 | 存储位置 |
|-----------|--------|------|----------|
| **Access Token** | 30分钟 | API访问 | 内存/SessionStorage |
| **Refresh Token** | 7天 | 刷新access token | HttpOnly Cookie |

### 认证最佳实践

#### 1. Token存储

```javascript
// ✅ 推荐：使用HttpOnly Cookie存储refresh token
// 服务器端设置
response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=True,  // 仅HTTPS
    samesite="strict",
    max_age=7*24*3600
)

// 客户端：access token存储在内存或sessionStorage
sessionStorage.setItem('access_token', accessToken);

// ❌ 不推荐：将token存储在localStorage
localStorage.setItem('token', token);  // 易受XSS攻击
```

#### 2. Token刷新策略

```javascript
// 自动刷新策略
async function apiCall(url, options) {
    let response = await fetch(url, {
        ...options,
        headers: {
            'Authorization': `Bearer ${getAccessToken()}`,
            ...options.headers
        }
    });

    // 如果401，尝试刷新token
    if (response.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            // 重试原请求
            response = await fetch(url, {
                ...options,
                headers: {
                    'Authorization': `Bearer ${getAccessToken()}`,
                    ...options.headers
                }
            });
        } else {
            // 刷新失败，跳转登录
            redirectToLogin();
        }
    }

    return response;
}
```

#### 3. 登出流程

```javascript
// 完整的登出流程
async function logout() {
    try {
        // 1. 调用服务器登出接口（可选）
        await fetch('/api/v1/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`
            }
        });
    } finally {
        // 2. 清除客户端token
        sessionStorage.removeItem('access_token');
        
        // 3. 清除refresh token cookie（服务器端）
        // 通过调用专门的清除cookie接口
        
        // 4. 跳转登录页
        window.location.href = '/login';
    }
}
```

---

## 请求规范

### HTTP方法使用

| 方法 | 用途 | 幂等性 | 示例 |
|------|------|--------|------|
| **GET** | 查询资源 | ✅ | GET /api/v1/projects |
| **POST** | 创建资源 | ❌ | POST /api/v1/projects |
| **PUT** | 完整更新 | ✅ | PUT /api/v1/projects/123 |
| **PATCH** | 部分更新 | ❌ | PATCH /api/v1/projects/123 |
| **DELETE** | 删除资源 | ✅ | DELETE /api/v1/projects/123 |

### 请求头规范

```http
# 必需的请求头
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

# 推荐的请求头
Accept: application/json
Accept-Language: zh-CN,en;q=0.9
User-Agent: MyApp/1.0.0

# 可选的追踪头
X-Request-ID: uuid-generated-by-client
X-Correlation-ID: trace-id-for-distributed-tracing
```

### URL参数规范

```bash
# ✅ 推荐：使用清晰的查询参数
GET /api/v1/projects?skip=0&limit=10&sort=-created_at&status=active

# 查询参数命名规范
skip=0           # 分页偏移（从0开始）
limit=10         # 每页数量（默认10，最大100）
sort=-created_at # 排序（-表示降序）
search=keyword   # 全文搜索
filter=active    # 状态过滤

# ❌ 避免：使用非标准参数名
GET /api/v1/projects?page=1&size=10&order=desc
```

### 请求体规范

```json
// ✅ 推荐：使用驼峰命名（camelCase）或下划线（snake_case）
{
  "project_name": "十八洞村研究",
  "description": "研究描述",
  "metadata": {
    "location": "湖南湘西",
    "year": 2024
  }
}

// ❌ 避免：混合命名风格
{
  "projectName": "十八洞村研究",
  "Description": "研究描述",
  "meta_data": {}
}
```

---

## 响应规范

### 成功响应

```json
// 单个资源
{
  "id": "proj_123456",
  "name": "十八洞村研究",
  "created_at": "2026-08-01T06:00:00Z",
  "updated_at": "2026-08-01T06:00:00Z"
}

// 资源列表（分页）
{
  "items": [
    {"id": "proj_123456", "name": "项目1"},
    {"id": "proj_123457", "name": "项目2"}
  ],
  "total": 25,
  "skip": 0,
  "limit": 10
}

// 操作结果
{
  "success": true,
  "message": "操作成功",
  "data": {
    "task_id": "task_789012"
  }
}
```

### HTTP状态码使用

| 状态码 | 含义 | 使用场景 |
|--------|------|----------|
| **200 OK** | 成功 | GET/PUT/PATCH成功 |
| **201 Created** | 已创建 | POST创建资源成功 |
| **204 No Content** | 无内容 | DELETE成功 |
| **400 Bad Request** | 请求错误 | 参数验证失败 |
| **401 Unauthorized** | 未授权 | token无效或过期 |
| **403 Forbidden** | 禁止访问 | 权限不足 |
| **404 Not Found** | 未找到 | 资源不存在 |
| **409 Conflict** | 冲突 | 资源已存在 |
| **422 Unprocessable** | 无法处理 | 业务逻辑错误 |
| **429 Too Many Requests** | 请求过多 | 速率限制 |
| **500 Internal Error** | 服务器错误 | 系统异常 |

---

## 错误处理

### 统一错误格式

```json
{
  "detail": {
    "error_code": 3001,
    "message": "文档上传失败",
    "details": {
      "field": "file",
      "reason": "文件格式不支持",
      "supported_formats": ["mp4", "mp3", "txt", "pdf"]
    }
  }
}
```

### 客户端错误处理

```javascript
async function handleApiCall(url, options) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const error = await response.json();
            
            // 根据错误码处理
            switch (error.detail.error_code) {
                case 2001: // Token过期
                    await refreshToken();
                    return handleApiCall(url, options); // 重试
                    
                case 2003: // 权限不足
                    showPermissionDenied();
                    break;
                    
                case 1006: // 速率限制
                    const retryAfter = error.detail.details.retry_after;
                    await sleep(retryAfter * 1000);
                    return handleApiCall(url, options); // 重试
                    
                default:
                    showError(error.detail.message);
            }
            
            throw error;
        }
        
        return await response.json();
        
    } catch (err) {
        // 网络错误
        if (err.name === 'TypeError') {
            showError('网络连接失败，请检查网络');
        }
        throw err;
    }
}
```

### 错误日志记录

```python
from app.core.logging_config import get_logger, log_error

logger = get_logger(__name__)

try:
    result = process_document(doc_id)
except ValueError as e:
    # 客户端错误 - 记录WARNING
    logger.warning(
        f"文档处理参数错误: {doc_id}",
        extra={"document_id": doc_id, "error": str(e)}
    )
    raise BadRequestException(
        ErrorCode.DOCUMENT_INVALID_FORMAT,
        details={"document_id": doc_id}
    )
    
except Exception as e:
    # 服务器错误 - 记录ERROR
    log_error(
        logger,
        f"文档处理失败: {doc_id}",
        exc_info=e,
        extra_data={"document_id": doc_id}
    )
    raise InternalServerException()
```

---

## 速率限制

### 速率限制策略

| 端点类型 | 限制 | 说明 |
|----------|------|------|
| **默认** | 100次/分钟 | 大部分GET请求 |
| **文档上传** | 10次/分钟 | POST /documents/upload |
| **报告生成** | 5次/分钟 | POST /reports/generate |
| **聊天消息** | 30次/分钟 | POST /chat/chat |

### 速率限制响应头

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1690876800
```

### 处理速率限制

```javascript
async function apiCallWithRetry(url, options, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url, options);
            
            if (response.status === 429) {
                const retryAfter = response.headers.get('Retry-After') || 60;
                console.log(`速率限制，${retryAfter}秒后重试...`);
                await sleep(retryAfter * 1000);
                continue;
            }
            
            return response;
            
        } catch (err) {
            if (i === maxRetries - 1) throw err;
            await sleep(1000 * Math.pow(2, i)); // 指数退避
        }
    }
}
```

---

## 安全最佳实践

### 1. HTTPS使用

```bash
# ✅ 生产环境必须使用HTTPS
https://api.example.com/api/v1/projects

# ❌ 不要在生产环境使用HTTP
http://api.example.com/api/v1/projects
```

### 2. 敏感信息保护

```python
# ✅ 不要在响应中返回敏感信息
{
  "id": "user_123",
  "username": "user@example.com",
  "role": "admin"
  # password_hash 不应返回
}

# ✅ 不要在日志中记录敏感信息
logger.info("用户登录", extra={"user_id": user.id})
# 不要记录 password, token, api_key

# ✅ 不要在URL中传递敏感信息
POST /api/v1/auth/login
Body: {"username": "...", "password": "..."}

# ❌ 错误示例
GET /api/v1/auth/login?username=...&password=...
```

### 3. CORS配置

```python
# 生产环境：限制允许的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",
        "https://admin.example.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# 开发环境：允许所有域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. 输入验证

```python
from pydantic import BaseModel, Field, validator

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(None, max_length=1000)
    
    @validator('name')
    def name_must_not_contain_special_chars(cls, v):
        if not re.match(r'^[a-zA-Z0-9一-龥\s\-_]+$', v):
            raise ValueError('项目名称包含非法字符')
        return v
```

---

## 性能优化

### 1. 分页查询

```python
# ✅ 始终使用分页
@router.get("/projects")
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    projects = db.query(Project).offset(skip).limit(limit).all()
    total = db.query(Project).count()
    return {"items": projects, "total": total, "skip": skip, "limit": limit}
```

### 2. 字段选择

```bash
# ✅ 允许客户端选择需要的字段
GET /api/v1/projects/123?fields=id,name,created_at

# 减少数据传输量
```

### 3. 缓存策略

```python
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@router.get("/projects/{project_id}")
@cache(expire=300)  # 缓存5分钟
async def get_project(project_id: str):
    return db.query(Project).filter(Project.id == project_id).first()
```

### 4. 异步处理

```python
# ✅ 长时间操作使用异步任务
@router.post("/documents/process")
async def process_document(doc_id: str, background_tasks: BackgroundTasks):
    # 立即返回任务ID
    task_id = generate_task_id()
    
    # 后台处理
    background_tasks.add_task(process_document_task, doc_id, task_id)
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": "文档处理任务已启动"
    }
```

---

## 版本控制

### URL版本控制

```bash
# 当前版本
https://api.example.com/api/v1/projects

# 未来版本（保持向后兼容）
https://api.example.com/api/v2/projects
```

### 版本演进策略

1. **向后兼容的变更**（无需新版本）
   - 添加新端点
   - 添加可选参数
   - 添加新的响应字段

2. **破坏性变更**（需要新版本）
   - 删除端点
   - 删除参数或字段
   - 修改数据类型
   - 修改行为逻辑

### 弃用策略

```python
from fastapi import APIRouter, status
from warnings import warn

@router.get(
    "/old-endpoint",
    deprecated=True,
    description="⚠️ 已弃用：请使用 /api/v2/new-endpoint"
)
async def old_endpoint():
    warn("此端点将在v2版本中移除", DeprecationWarning)
    return {"message": "请迁移到新端点"}
```

---

## 快速检查清单

### API开发检查清单

- [ ] 使用正确的HTTP方法和状态码
- [ ] 实现统一的错误格式
- [ ] 添加输入验证
- [ ] 实现JWT认证
- [ ] 配置速率限制
- [ ] 添加请求日志
- [ ] 实现分页查询
- [ ] 使用HTTPS（生产环境）
- [ ] 配置CORS
- [ ] 编写API文档
- [ ] 添加请求示例
- [ ] 实现错误处理
- [ ] 添加单元测试
- [ ] 性能测试
- [ ] 安全审计

---

## 总结

遵循以上最佳实践可以帮助你构建：

✅ **安全的API** - JWT认证、HTTPS、输入验证  
✅ **可靠的API** - 统一错误处理、完善日志  
✅ **高性能的API** - 分页、缓存、异步处理  
✅ **易用的API** - 清晰的文档、一致的规范  
✅ **可维护的API** - 版本控制、向后兼容

---

**相关文档**:
- [API错误码参考](API_ERROR_CODES.md)
- [API请求示例](API_EXAMPLES.md)
- [日志系统指南](LOGGING_SYSTEM_GUIDE.md)
- [速率限制指南](API_RATE_LIMIT_GUIDE.md)
