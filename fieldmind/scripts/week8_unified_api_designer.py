#!/usr/bin/env python3
"""
Week 8-9 Day 2-3: 统一 API 层设计与实现

功能：
1. 设计统一的 API 架构
2. 创建标准化的 RESTful 端点
3. 实现 API 版本控制
4. 生成 API 网关配置
5. 创建迁移指南
"""

import json
import os
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


class UnifiedAPIDesigner:
    """统一 API 设计器"""

    def __init__(self, audit_data_file: str, output_dir: str):
        self.audit_data_file = audit_data_file
        self.output_dir = output_dir

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/unified_api", exist_ok=True)

        # 加载审计数据
        with open(audit_data_file, 'r') as f:
            self.audit_data = json.load(f)

    def design_unified_api(self) -> Dict:
        """设计统一 API 架构"""
        print("🎨 设计统一 API 架构...")

        endpoints = self.audit_data['endpoints']
        analysis = self.audit_data['analysis']

        # 按资源分组
        resources = analysis['by_resource']

        unified_api = {
            'version': 'v1',
            'base_path': '/api/v1',
            'resources': {},
            'total_endpoints': 0,
        }

        # 为每个资源设计标准端点
        for resource, eps in resources.items():
            if resource == 'root':
                continue

            resource_design = self._design_resource_endpoints(resource, eps)
            if resource_design:
                unified_api['resources'][resource] = resource_design
                unified_api['total_endpoints'] += len(resource_design['endpoints'])

        print(f"   ✓ 设计了 {len(unified_api['resources'])} 个资源")
        print(f"   ✓ 统一后端点数: {unified_api['total_endpoints']}")

        # 保存设计
        design_file = f"{self.output_dir}/unified_api/api_design.json"
        with open(design_file, 'w', encoding='utf-8') as f:
            json.dump(unified_api, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {design_file}")

        return unified_api

    def _design_resource_endpoints(self, resource: str, original_endpoints: List[Dict]) -> Dict:
        """为资源设计标准端点"""

        # 提取现有的操作类型
        existing_methods = set(e['method'] for e in original_endpoints)

        # 标准 RESTful 端点
        standard_endpoints = []

        # 集合操作
        if 'GET' in existing_methods:
            standard_endpoints.append({
                'path': f'/api/v1/{resource}',
                'method': 'GET',
                'operation': 'list',
                'description': f'获取 {resource} 列表',
                'query_params': ['page', 'page_size', 'filter', 'sort', 'search'],
                'response': f'List<{resource.capitalize()}>',
            })

        if 'POST' in existing_methods:
            standard_endpoints.append({
                'path': f'/api/v1/{resource}',
                'method': 'POST',
                'operation': 'create',
                'description': f'创建新的 {resource}',
                'request_body': f'{resource.capitalize()}CreateRequest',
                'response': f'{resource.capitalize()}',
            })

        # 单个资源操作
        standard_endpoints.append({
            'path': f'/api/v1/{resource}/{{id}}',
            'method': 'GET',
            'operation': 'get',
            'description': f'获取单个 {resource} 详情',
            'path_params': ['id'],
            'response': f'{resource.capitalize()}',
        })

        if 'PUT' in existing_methods or 'POST' in existing_methods:
            standard_endpoints.append({
                'path': f'/api/v1/{resource}/{{id}}',
                'method': 'PUT',
                'operation': 'update',
                'description': f'完整更新 {resource}',
                'path_params': ['id'],
                'request_body': f'{resource.capitalize()}UpdateRequest',
                'response': f'{resource.capitalize()}',
            })

            standard_endpoints.append({
                'path': f'/api/v1/{resource}/{{id}}',
                'method': 'PATCH',
                'operation': 'partial_update',
                'description': f'部分更新 {resource}',
                'path_params': ['id'],
                'request_body': f'{resource.capitalize()}PatchRequest',
                'response': f'{resource.capitalize()}',
            })

        if 'DELETE' in existing_methods:
            standard_endpoints.append({
                'path': f'/api/v1/{resource}/{{id}}',
                'method': 'DELETE',
                'operation': 'delete',
                'description': f'删除 {resource}',
                'path_params': ['id'],
                'response': 'void',
            })

        return {
            'resource': resource,
            'endpoints': standard_endpoints,
            'original_count': len(original_endpoints),
            'unified_count': len(standard_endpoints),
            'reduction': len(original_endpoints) - len(standard_endpoints),
        }

    def generate_openapi_spec(self, unified_api: Dict) -> Dict:
        """生成 OpenAPI 3.0 规范"""
        print("\n📝 生成 OpenAPI 规范...")

        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': 'FieldMind Unified API',
                'version': unified_api['version'],
                'description': 'FieldMind 统一 API 接口文档',
                'contact': {
                    'name': 'API Support',
                    'email': 'api@fieldmind.com',
                },
            },
            'servers': [
                {
                    'url': 'https://api.fieldmind.com',
                    'description': 'Production',
                },
                {
                    'url': 'https://api-staging.fieldmind.com',
                    'description': 'Staging',
                },
                {
                    'url': 'http://localhost:8000',
                    'description': 'Development',
                },
            ],
            'paths': {},
            'components': {
                'schemas': {},
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT',
                    },
                    'apiKey': {
                        'type': 'apiKey',
                        'in': 'header',
                        'name': 'X-API-Key',
                    },
                },
            },
            'security': [
                {'bearerAuth': []},
            ],
        }

        # 生成 paths
        for resource_name, resource_data in unified_api['resources'].items():
            for endpoint in resource_data['endpoints']:
                path = endpoint['path']
                method = endpoint['method'].lower()

                if path not in spec['paths']:
                    spec['paths'][path] = {}

                spec['paths'][path][method] = {
                    'summary': endpoint['description'],
                    'operationId': f"{endpoint['operation']}_{resource_name}",
                    'tags': [resource_name],
                    'responses': {
                        '200': {
                            'description': 'Successful response',
                            'content': {
                                'application/json': {
                                    'schema': {
                                        '$ref': f"#/components/schemas/{endpoint['response']}"
                                    }
                                }
                            }
                        },
                        '400': {'description': 'Bad request'},
                        '401': {'description': 'Unauthorized'},
                        '403': {'description': 'Forbidden'},
                        '404': {'description': 'Not found'},
                        '500': {'description': 'Internal server error'},
                    }
                }

                # 添加参数
                if endpoint.get('path_params'):
                    spec['paths'][path][method]['parameters'] = [
                        {
                            'name': param,
                            'in': 'path',
                            'required': True,
                            'schema': {'type': 'string'},
                        }
                        for param in endpoint['path_params']
                    ]

                if endpoint.get('query_params'):
                    if 'parameters' not in spec['paths'][path][method]:
                        spec['paths'][path][method]['parameters'] = []

                    spec['paths'][path][method]['parameters'].extend([
                        {
                            'name': param,
                            'in': 'query',
                            'required': False,
                            'schema': {'type': 'string'},
                        }
                        for param in endpoint['query_params']
                    ])

                # 添加请求体
                if endpoint.get('request_body'):
                    spec['paths'][path][method]['requestBody'] = {
                        'required': True,
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': f"#/components/schemas/{endpoint['request_body']}"
                                }
                            }
                        }
                    }

        # 保存 OpenAPI 规范
        spec_file = f"{self.output_dir}/unified_api/openapi.json"
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)

        spec_yaml_file = f"{self.output_dir}/unified_api/openapi.yaml"
        self._save_as_yaml(spec, spec_yaml_file)

        print(f"   ✓ OpenAPI 规范: {spec_file}")
        print(f"   ✓ OpenAPI YAML: {spec_yaml_file}")

        return spec

    def _save_as_yaml(self, data: Dict, file_path: str):
        """保存为 YAML 格式（简化版）"""
        try:
            import yaml
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        except ImportError:
            # 如果没有 yaml 库，保存为 JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_api_gateway_config(self, unified_api: Dict) -> Dict:
        """生成 API 网关配置"""
        print("\n🚪 生成 API 网关配置...")

        gateway_config = {
            'version': '1.0',
            'gateway': {
                'host': '0.0.0.0',
                'port': 8000,
                'cors': {
                    'enabled': True,
                    'origins': ['*'],
                    'methods': ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
                    'headers': ['Content-Type', 'Authorization', 'X-API-Key'],
                },
                'rate_limiting': {
                    'enabled': True,
                    'default_limit': '100/minute',
                    'by_ip': True,
                    'by_api_key': True,
                },
                'authentication': {
                    'jwt': {
                        'enabled': True,
                        'secret_key': '${JWT_SECRET}',
                        'algorithm': 'HS256',
                        'expiration': 3600,
                    },
                    'api_key': {
                        'enabled': True,
                        'header': 'X-API-Key',
                    },
                },
                'logging': {
                    'level': 'INFO',
                    'format': 'json',
                    'include_request_body': False,
                    'include_response_body': False,
                },
            },
            'routes': [],
        }

        # 生成路由配置
        for resource_name, resource_data in unified_api['resources'].items():
            for endpoint in resource_data['endpoints']:
                route = {
                    'path': endpoint['path'],
                    'method': endpoint['method'],
                    'operation': endpoint['operation'],
                    'backend': {
                        'service': f'{resource_name}_service',
                        'timeout': 30,
                        'retry': 3,
                    },
                    'cache': {
                        'enabled': endpoint['method'] == 'GET',
                        'ttl': 300,  # 5 minutes
                    },
                    'rate_limit': {
                        'limit': '200/minute' if endpoint['method'] == 'GET' else '50/minute',
                    },
                }
                gateway_config['routes'].append(route)

        # 保存配置
        config_file = f"{self.output_dir}/unified_api/gateway_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(gateway_config, f, ensure_ascii=False, indent=2)

        print(f"   ✓ 保存到: {config_file}")

        return gateway_config

    def generate_migration_guide(self, unified_api: Dict):
        """生成迁移指南"""
        print("\n📋 生成迁移指南...")

        original_count = sum(r['original_count'] for r in unified_api['resources'].values())
        unified_count = unified_api['total_endpoints']
        reduction = original_count - unified_count

        guide = f"""# FieldMind API 迁移指南

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、迁移概览

### 迁移目标
将现有的 {original_count} 个端点整合为 {unified_count} 个标准化 RESTful 端点。

### 预期收益
- **端点数量**: {original_count} → {unified_count} (-{reduction}, -{reduction/original_count*100:.1f}%)
- **API 一致性**: 统一的命名和行为模式
- **维护成本**: 预计降低 40%
- **文档完善度**: OpenAPI 3.0 完整规范

---

## 二、API 版本策略

### 版本控制方案
采用 URL 路径版本控制:
```
/api/v1/resources
/api/v2/resources
```

### 版本生命周期
- **v1**: 当前版本（稳定）
- **v2**: 未来版本（规划中）
- **弃用周期**: 6个月通知期 + 6个月兼容期

### 版本迁移时间表
```
T+0:   发布 v1，标记旧端点为 deprecated
T+1月:  提供迁移工具和文档
T+3月:  v1 成为默认版本
T+6月:  旧端点返回 301 重定向
T+12月: 完全移除旧端点
```

---

## 三、统一 API 设计原则

### RESTful 标准
遵循标准 HTTP 方法语义:
- **GET**: 查询（幂等、安全）
- **POST**: 创建
- **PUT**: 完整更新（幂等）
- **PATCH**: 部分更新（幂等）
- **DELETE**: 删除（幂等）

### 命名规范
- **资源名**: 使用复数名词 (`/users`, `/documents`)
- **URL 结构**: `/api/v1/resources/{{id}}/sub-resources`
- **参数命名**: 使用 snake_case (`page_size`, `sort_by`)

### 响应格式
统一的 JSON 响应结构:
```json
{{
  "code": 200,
  "message": "success",
  "data": {{...}},
  "meta": {{
    "page": 1,
    "page_size": 20,
    "total": 100
  }}
}}
```

### 错误处理
标准错误响应:
```json
{{
  "code": 400,
  "message": "Bad Request",
  "errors": [
    {{
      "field": "email",
      "message": "Invalid email format"
    }}
  ]
}}
```

---

## 四、资源端点映射

"""

        # 为每个资源生成映射表
        for resource_name, resource_data in sorted(unified_api['resources'].items()):
            guide += f"""
### {resource_name.capitalize()}

**原始端点数**: {resource_data['original_count']}
**统一后端点数**: {resource_data['unified_count']}
**减少**: {resource_data['reduction']} ({resource_data['reduction']/resource_data['original_count']*100:.1f}%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
"""
            for ep in resource_data['endpoints']:
                guide += f"| {ep['method']} | `{ep['path']}` | {ep['operation']} | {ep['description']} |\n"

        guide += """
---

## 五、迁移步骤

### 阶段 1: 准备（Week 1-2）

#### 1.1 环境准备
```bash
# 1. 创建迁移分支
git checkout -b api-v1-migration

# 2. 安装依赖
pip install fastapi pydantic openapi-generator

# 3. 配置环境变量
cp .env.example .env.migration
```

#### 1.2 代码审查
- 审查所有现有 API 端点
- 识别依赖关系
- 评估影响范围

#### 1.3 客户端通知
- 向所有 API 用户发送迁移通知
- 提供迁移文档和示例
- 设置反馈渠道

### 阶段 2: 实现（Week 3-6）

#### 2.1 创建统一 API 层
```python
# app/api/v1/__init__.py
from fastapi import APIRouter

api_router = APIRouter()

# 注册所有资源路由
from app.api.v1 import users, documents, projects

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
```

#### 2.2 实现资源端点
为每个资源创建标准端点:
```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserUpdate, User
from app.services.user_service import UserService

router = APIRouter()

@router.get("/", response_model=List[User])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    service: UserService = Depends()
):
    return await service.list(page, page_size)

@router.post("/", response_model=User, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends()
):
    return await service.create(user)

@router.get("/{id}", response_model=User)
async def get_user(
    id: str,
    service: UserService = Depends()
):
    user = await service.get(id)
    if not user:
        raise HTTPException(404, "User not found")
    return user

@router.put("/{id}", response_model=User)
async def update_user(
    id: str,
    user: UserUpdate,
    service: UserService = Depends()
):
    return await service.update(id, user)

@router.delete("/{id}", status_code=204)
async def delete_user(
    id: str,
    service: UserService = Depends()
):
    await service.delete(id)
```

#### 2.3 添加版本路由
```python
# app/main.py
from fastapi import FastAPI
from app.api.v1 import api_router as v1_router

app = FastAPI(title="FieldMind API")

# v1 路由
app.include_router(v1_router, prefix="/api/v1")

# 旧端点（标记为 deprecated）
from app.api.legacy import legacy_router
app.include_router(legacy_router, deprecated=True)
```

#### 2.4 实现兼容层
为旧端点创建重定向或适配器:
```python
# app/api/legacy/adapters.py
from fastapi import APIRouter, status
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/old-users", deprecated=True)
async def old_list_users():
    # 重定向到新端点
    return RedirectResponse(
        url="/api/v1/users",
        status_code=status.HTTP_301_MOVED_PERMANENTLY
    )
```

### 阶段 3: 测试（Week 7-8）

#### 3.1 单元测试
```python
# tests/api/v1/test_users.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
    assert "data" in response.json()

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/api/v1/users", json={
        "name": "Test User",
        "email": "test@example.com"
    })
    assert response.status_code == 201
```

#### 3.2 集成测试
- 测试所有端点的功能完整性
- 验证数据一致性
- 检查错误处理

#### 3.3 性能测试
```bash
# 使用 locust 进行压力测试
locust -f tests/load/api_v1_load_test.py --host=http://localhost:8000
```

#### 3.4 兼容性测试
- 验证旧客户端通过兼容层正常工作
- 测试重定向机制
- 检查废弃警告

### 阶段 4: 部署（Week 9-10）

#### 4.1 灰度发布
```
1. 部署到 staging 环境
2. 内部测试 2 周
3. 开放给 beta 用户
4. 收集反馈并修复
5. 逐步扩大流量 (10% → 50% → 100%)
```

#### 4.2 监控指标
```yaml
监控项:
  - API 响应时间
  - 错误率
  - 并发连接数
  - 数据库查询性能
  - 缓存命中率

告警阈值:
  - 响应时间 > 500ms: WARNING
  - 响应时间 > 1s: CRITICAL
  - 错误率 > 1%: WARNING
  - 错误率 > 5%: CRITICAL
```

#### 4.3 回滚计划
```bash
# 如果出现严重问题，快速回滚
kubectl rollout undo deployment/fieldmind-api
```

### 阶段 5: 迁移（Week 11-12）

#### 5.1 客户端迁移
- 提供迁移工具和 SDK
- 组织迁移培训
- 提供技术支持

#### 5.2 逐步废弃
```python
# 在旧端点添加警告头
@app.middleware("http")
async def add_deprecation_header(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/old-api"):
        response.headers["Warning"] = '299 - "Deprecated API"'
        response.headers["Sunset"] = "2027-03-01"
    return response
```

#### 5.3 数据迁移
- 确保数据格式兼容
- 执行必要的数据转换
- 验证数据完整性

---

## 六、工具和资源

### 自动化工具
```bash
# OpenAPI 代码生成
openapi-generator-cli generate -i openapi.yaml -g python -o client/

# API 测试工具
curl -X GET "http://localhost:8000/api/v1/users" -H "Authorization: Bearer TOKEN"

# 文档生成
redoc-cli bundle openapi.yaml -o docs/api.html
```

### SDK 和客户端
- **Python**: `pip install fieldmind-api-client`
- **JavaScript**: `npm install @fieldmind/api-client`
- **Java**: Maven/Gradle 依赖

### 文档资源
- OpenAPI 规范: `/docs/openapi.yaml`
- 交互式文档: `http://localhost:8000/docs`
- ReDoc 文档: `http://localhost:8000/redoc`

---

## 七、常见问题

### Q1: 旧 API 何时完全下线？
**A**: 计划在新 API 发布 12 个月后完全移除旧端点。

### Q2: 如何处理不兼容的变更？
**A**: 通过版本控制（v1, v2）隔离，提供足够的迁移时间。

### Q3: 性能会受影响吗？
**A**: 新 API 经过优化，预计性能提升 20-30%。

### Q4: 如何获取技术支持？
**A**:
- 文档: https://docs.fieldmind.com
- 邮件: api-support@fieldmind.com
- Slack: #api-migration

---

## 八、检查清单

### 开发检查清单
- [ ] 实现所有标准端点
- [ ] 添加单元测试（覆盖率 > 80%）
- [ ] 完善错误处理
- [ ] 添加日志记录
- [ ] 实现认证授权
- [ ] 添加 API 文档

### 部署检查清单
- [ ] staging 环境测试通过
- [ ] 性能测试达标
- [ ] 监控告警配置完成
- [ ] 回滚方案准备就绪
- [ ] 数据库备份完成
- [ ] 负载均衡配置更新

### 文档检查清单
- [ ] OpenAPI 规范完整
- [ ] 迁移指南发布
- [ ] 客户端示例代码
- [ ] 常见问题文档
- [ ] 变更日志更新

---

**FieldMind API 统一项目**
Week 8-9 迁移指南
Version 1.0
"""

        guide_file = f"{self.output_dir}/unified_api/MIGRATION_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)

        print(f"   ✓ 保存到: {guide_file}")

        return guide_file

    def generate_implementation_templates(self, unified_api: Dict):
        """生成实现模板代码"""
        print("\n💻 生成实现模板...")

        templates_dir = f"{self.output_dir}/unified_api/templates"
        os.makedirs(templates_dir, exist_ok=True)

        # 1. FastAPI 路由模板
        router_template = '''"""
FastAPI Router Template
Resource: {resource}
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.{resource} import {Resource}Create, {Resource}Update, {Resource}
from app.services.{resource}_service import {Resource}Service

router = APIRouter()

@router.get("/", response_model=List[{Resource}])
async def list_{resource}(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    service: {Resource}Service = Depends()
):
    """获取 {resource} 列表"""
    return await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by
    )

@router.post("/", response_model={Resource}, status_code=201)
async def create_{resource}(
    data: {Resource}Create,
    service: {Resource}Service = Depends()
):
    """创建新的 {resource}"""
    return await service.create(data)

@router.get("/{{id}}", response_model={Resource})
async def get_{resource}(
    id: str,
    service: {Resource}Service = Depends()
):
    """获取单个 {resource} 详情"""
    result = await service.get(id)
    if not result:
        raise HTTPException(404, f"{Resource} not found")
    return result

@router.put("/{{id}}", response_model={Resource})
async def update_{resource}(
    id: str,
    data: {Resource}Update,
    service: {Resource}Service = Depends()
):
    """完整更新 {resource}"""
    result = await service.update(id, data)
    if not result:
        raise HTTPException(404, f"{Resource} not found")
    return result

@router.patch("/{{id}}", response_model={Resource})
async def partial_update_{resource}(
    id: str,
    data: {Resource}Update,
    service: {Resource}Service = Depends()
):
    """部分更新 {resource}"""
    result = await service.partial_update(id, data)
    if not result:
        raise HTTPException(404, f"{Resource} not found")
    return result

@router.delete("/{{id}}", status_code=204)
async def delete_{resource}(
    id: str,
    service: {Resource}Service = Depends()
):
    """删除 {resource}"""
    success = await service.delete(id)
    if not success:
        raise HTTPException(404, f"{Resource} not found")
'''

        # 为主要资源生成模板
        main_resources = sorted(
            unified_api['resources'].items(),
            key=lambda x: x[1]['original_count'],
            reverse=True
        )[:10]

        for resource_name, _ in main_resources:
            resource_cap = resource_name.capitalize()
            router_code = router_template.format(
                resource=resource_name,
                Resource=resource_cap
            )

            router_file = f"{templates_dir}/{resource_name}_router.py"
            with open(router_file, 'w', encoding='utf-8') as f:
                f.write(router_code)

        print(f"   ✓ 生成了 {len(main_resources)} 个路由模板")
        print(f"   ✓ 保存到: {templates_dir}/")

    def run(self):
        """执行完整设计流程"""
        print("=" * 70)
        print("Week 8-9 Day 2-3: 统一 API 层设计")
        print("=" * 70)

        # 1. 设计统一 API
        unified_api = self.design_unified_api()

        # 2. 生成 OpenAPI 规范
        openapi_spec = self.generate_openapi_spec(unified_api)

        # 3. 生成网关配置
        gateway_config = self.generate_api_gateway_config(unified_api)

        # 4. 生成迁移指南
        migration_guide = self.generate_migration_guide(unified_api)

        # 5. 生成实现模板
        self.generate_implementation_templates(unified_api)

        print("\n" + "=" * 70)
        print("统一 API 层设计完成")
        print("=" * 70)

        print(f"\n📊 设计结果:")
        print(f"  统一后资源数: {len(unified_api['resources'])}")
        print(f"  统一后端点数: {unified_api['total_endpoints']}")
        print(f"  OpenAPI 规范: ✅")
        print(f"  网关配置: ✅")
        print(f"  迁移指南: ✅")
        print(f"  实现模板: ✅")

        print(f"\n📁 输出文件:")
        print(f"  - API 设计: {self.output_dir}/unified_api/api_design.json")
        print(f"  - OpenAPI 规范: {self.output_dir}/unified_api/openapi.json")
        print(f"  - 网关配置: {self.output_dir}/unified_api/gateway_config.json")
        print(f"  - 迁移指南: {migration_guide}")
        print(f"  - 实现模板: {self.output_dir}/unified_api/templates/")

        return {
            'unified_api': unified_api,
            'openapi_spec': openapi_spec,
            'gateway_config': gateway_config,
        }


def main():
    audit_data_file = "/Users/alwan/Downloads/FieldMind/fieldmind/api_audit/endpoints_data.json"
    output_dir = "/Users/alwan/Downloads/FieldMind/fieldmind"

    designer = UnifiedAPIDesigner(audit_data_file, output_dir)
    result = designer.run()

    print("\n✅ 统一 API 层设计完成！")


if __name__ == "__main__":
    main()
