# 路由前缀问题诊断和修复方案

## 问题概述

后端有249个API端点已注册，但其中239个路由的路径前缀不正确，导致前后端无法正常通信。

## 核心问题

**双重前缀冲突**: Router内部定义了prefix，main.py注册时又加了prefix，但FastAPI的处理方式导致某些router的内部prefix覆盖了main.py的prefix。

### 示例

```python
# app/api/auth.py
router = APIRouter(prefix="/auth", tags=["认证"])  # 内部已有prefix

# app/main.py
app.include_router(auth.router, prefix="/api", tags=["认证"])  # 又加了prefix

# 期望结果: /api/auth/register
# 实际结果: /auth/register  ❌ (内部prefix覆盖了外部prefix)
```

## 当前路由状态

### 正确的路由 (10个)
- ✅ `/api/knowledge-graph/*` - 6个端点
- ✅ `/api/aggregate/*` - 2个端点  
- ✅ `/api/v1/projects/{project_id}/documents` - 兼容层
- ✅ `/api/v1/projects/{project_id}/memories` - 兼容层

### 错误的路由 (239个)
- ❌ `/auth/*` → 应该是 `/api/v1/auth/*`
- ❌ `/projects/*` → 应该是 `/api/projects/*`
- ❌ `/chat/*` → 应该是 `/api/chat/*`
- ❌ `/chat-rag/*` → 应该是 `/api/chat-rag/*`
- ❌ `/reports/*` → 应该是 `/api/reports/*`
- ❌ `/dashboard/*` → 应该是 `/api/dashboard/*`
- ❌ `/batch/*` → 应该是 `/api/batch/*`
- ❌ 等等...

## 修复方案

有两种修复方式：

### 方案A: 移除router内部的prefix (推荐)

在各个router文件中移除prefix，让main.py统一管理：

```python
# app/api/auth.py (修改前)
router = APIRouter(prefix="/auth", tags=["认证"])

# app/api/auth.py (修改后)
router = APIRouter(tags=["认证"])

# main.py保持不变
app.include_router(auth.router, prefix="/api/v1", tags=["认证(v1)"])
# 结果: /api/v1/register, /api/v1/login 等
```

**优点**: 
- 统一管理，清晰明了
- 便于版本控制（v1/v2切换）
- 符合FastAPI最佳实践

**缺点**: 
- 需要修改多个文件

### 方案B: 移除main.py中的prefix

保留router内部prefix，main.py不加prefix：

```python
# app/api/auth.py 保持不变
router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# main.py (修改后)
app.include_router(auth.router, tags=["认证"])
# 结果: /api/v1/auth/register, /api/v1/auth/login 等
```

**优点**: 
- 每个router自包含，模块独立
- main.py更简洁

**缺点**: 
- 前缀分散在各个文件中，难以统一管理
- 版本升级时需要修改每个文件

## 推荐修复步骤

采用**方案A**，分3批修复：

### 第1批：核心router (优先修复)

这些是前端最常调用的API：

1. **auth.py** - 认证系统
   ```python
   # 修改前: router = APIRouter(prefix="/auth", tags=["认证"])
   # 修改后: router = APIRouter(tags=["认证"])
   ```

2. **projects.py** - 项目管理
   ```python
   # 修改前: router = APIRouter(prefix="/projects", tags=["projects"])
   # 修改后: router = APIRouter(tags=["projects"])
   ```

3. **chat.py** - 智能对话
   ```python
   # 修改前: router = APIRouter(prefix="/chat", tags=["chat"])
   # 修改后: router = APIRouter(tags=["chat"])
   ```

4. **documents.py** - 文档管理
   ```python
   # 修改前: router = APIRouter(prefix="/documents", tags=["documents"])
   # 修改后: router = APIRouter(tags=["documents"])
   ```

### 第2批：功能router

- chat_rag.py
- dashboard.py
- batch_processing.py
- reports_real.py
- skill_config.py
- timeline.py
- memory.py
- workflows.py

### 第3批：其他router

- keyword_search.py
- creative_analysis.py
- business_analysis.py
- document_processing.py
- source_traceback.py
- conversation_memory.py
- proposal.py
- knowledge_graph.py (已有/api前缀，但需要调整)
- knowledge_graph_v3.py
- document_processing_v2.py
- analytics.py
- hierarchical_retrieval.py
- dynamic_discovery_api.py

### 特殊处理

**aggregate.py**: 已经有完整的`/api/aggregate`前缀
```python
# 当前: router = APIRouter(prefix="/api/aggregate", tags=["aggregate"])
# 修改为: router = APIRouter(tags=["aggregate"])
# main.py: app.include_router(aggregate.router, prefix="/api/aggregate", tags=["数据聚合"])
```

**federation_api.py**: 没有prefix，依赖main.py的prefix (保持不变)
```python
# 当前: router = APIRouter()  # 正确✅
# main.py: app.include_router(federation_api.router, prefix="/api/federation", ...)
```

## 验证方法

修复后运行以下脚本验证：

```python
python3 -c "
import sys
sys.path.insert(0, '.')
from app.main import app

def extract_all_routes(app):
    all_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            all_routes.append(route.path)
        elif type(route).__name__ == '_IncludedRouter':
            if hasattr(route, 'original_router'):
                for sub_route in route.original_router.routes:
                    if hasattr(sub_route, 'path'):
                        prefix = getattr(route, 'prefix', '')
                        all_routes.append(prefix + sub_route.path)
    return all_routes

routes = extract_all_routes(app)
api_routes = [r for r in routes if r.startswith('/api')]
non_api_routes = [r for r in routes if not r.startswith('/api') and r not in ['/', '/health', '/openapi.json', '/docs', '/redoc', '/docs/oauth2-redirect']]

print(f'✅ /api开头的路由: {len(api_routes)}')
print(f'❌ 缺少/api前缀的路由: {len(non_api_routes)}')

if non_api_routes:
    print('\n需要修复的路由（前20个）:')
    for r in non_api_routes[:20]:
        print(f'  {r}')
"
```

**期望结果**: 
- ✅ /api开头的路由: 240+
- ❌ 缺少/api前缀的路由: 0

## 前端影响

修复后，前端需要确认以下路径可正常访问：

- `/api/v1/auth/*` - 认证
- `/api/projects/*` - 项目管理
- `/api/chat/*` - 对话
- `/api/documents/*` - 文档
- `/api/v1/projects/{id}/documents` - 项目文档（兼容层）
- `/api/v1/projects/{id}/memories` - 项目记忆（兼容层）

## 下一步

1. ✅ 已完成诊断
2. ⏳ 执行修复（从第1批核心router开始）
3. ⏳ 测试验证
4. ⏳ 前端联调
