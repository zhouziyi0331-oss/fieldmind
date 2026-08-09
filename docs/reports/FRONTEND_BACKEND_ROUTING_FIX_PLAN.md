# 前后端路由不匹配修复方案

## 问题诊断

前端调用的API端点与后端注册的路由存在严重不匹配，导致很多功能"点了没反应"。

## 路径冲突列表

### 1. 项目管理（Projects）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/projects/` | `/api/v1/projects/` | ✗ 不匹配 |
| `POST /api/projects/` | `/api/v1/projects/` | ✗ 不匹配 |
| `GET /api/projects/{id}` | `/api/v1/projects/{id}` | ✗ 不匹配 |
| `DELETE /api/projects/{id}` | `/api/v1/projects/{id}` | ✗ 不匹配 |

### 2. 文档管理（Documents）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/projects/{id}/documents` | 不存在 | ✗ 缺失 |
| `POST /api/documents/upload` | `/api/documents/upload` | ✓ 匹配 |
| `POST /api/documents/{id}/process` | `/api/documents/{id}/process` | ✓ 匹配 |
| `DELETE /api/documents/{id}` | `/api/documents/{id}` | ✓ 匹配 |

### 3. 上下文（Contexts）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/projects/{id}/contexts` | 不存在 | ✗ 缺失 |
| `POST /api/contexts/` | 不存在 | ✗ 缺失 |

### 4. 聊天（Chat）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/chat/sessions` | `/api/chat/*` | ✓ 存在 |
| `POST /api/chat/sessions` | `/api/chat/*` | ✓ 存在 |
| `POST /api/chat/message` | `/api/chat/message` | ✓ 匹配 |
| `POST /api/chat/enhanced` | `/api/chat/enhanced` | ✓ 匹配 |

### 5. 时间线（Timeline）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `POST /api/timeline/generate` | `/api/timeline/generate` | ✓ 匹配 |
| `GET /api/timeline/` | `/api/timeline/` | ✓ 匹配 |

### 6. 知识图谱（Knowledge Graph）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `POST /api/graph/build` | 不存在，应该是 `/api/knowledge-graph/*` | ✗ 路径错误 |
| `GET /api/graph/statistics` | 不存在 | ✗ 路径错误 |

### 7. 技能/报告（Skills）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/v1/skills` | `/api/v1/skills` | ✓ 匹配 |
| `POST /api/v1/skills/{id}/execute` | `/api/v1/skills/{id}/execute` | ✓ 匹配 |

### 8. 工作流（Workflows）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/v1/workflows` | `/api/v1/workflows` | ✓ 匹配 |
| `POST /api/v1/workflows` | `/api/v1/workflows` | ✓ 匹配 |
| `POST /api/v1/workflows/{id}/execute` | `/api/v1/workflows/{id}/execute` | ✓ 匹配 |

### 9. 产业分析（Industry）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/v1/industry/categories` | `/api/v1/industry/categories` | ✓ 匹配 |
| `GET /api/v1/industry/{category}/details` | `/api/v1/industry/{category}/details` | ✓ 匹配 |

### 10. 统计数据（Dashboard Stats）
| 前端调用 | 后端路由 | 状态 |
|---------|---------|------|
| `GET /api/projects/{id}/stats` | 不存在 | ✗ 缺失 |

## 修复策略

### 方案A：修改后端（推荐）✓
在后端添加路由别名/兼容层，保持向后兼容：

```python
# 在 app/main.py 中添加

# 项目管理兼容路由（无版本号）
app.include_router(v1_projects.router, prefix="/api/projects", tags=["项目管理(兼容)"], include_in_schema=False)

# 项目文档兼容路由
@app.get("/api/projects/{project_id}/documents")
async def get_project_documents_compat(project_id: int, db: Session = Depends(get_db)):
    # 调用实际实现
    pass

# 项目上下文兼容路由
@app.get("/api/projects/{project_id}/contexts")
async def get_project_contexts_compat(project_id: int, db: Session = Depends(get_db)):
    # 调用实际实现
    pass

# 项目统计兼容路由
@app.get("/api/projects/{project_id}/stats")
async def get_project_stats_compat(project_id: int, db: Session = Depends(get_db)):
    # 调用实际实现
    pass

# 知识图谱兼容路由
app.include_router(kg_new.router, prefix="/api/graph", tags=["知识图谱(兼容)"], include_in_schema=False)
```

### 方案B：修改前端
修改 APIService.swift 中的所有URL，统一使用 `/api/v1/` 前缀。

**缺点**：需要修改几十处URL，容易遗漏。

## 推荐执行顺序

1. **立即修复**（阻塞功能）：
   - ✗ `/api/projects/*` → 添加无版本号别名
   - ✗ `/api/projects/{id}/documents` → 添加兼容路由
   - ✗ `/api/projects/{id}/contexts` → 添加兼容路由
   - ✗ `/api/projects/{id}/stats` → 添加兼容路由
   - ✗ `/api/graph/*` → 添加别名指向 `/api/knowledge-graph`

2. **后续优化**：
   - 统一API版本策略（全部用v1或全部不用）
   - 清理重复路由
   - 添加API文档和测试

## 实现细节

见下一步代码修复文件。
