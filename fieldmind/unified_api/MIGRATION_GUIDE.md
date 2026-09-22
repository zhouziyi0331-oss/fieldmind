# FieldMind API 迁移指南

生成时间: 2026-09-13 15:46:20

---

## 一、迁移概览

### 迁移目标
将现有的 1182 个端点整合为 1577 个标准化 RESTful 端点。

### 预期收益
- **端点数量**: 1182 → 1577 (--395, --33.4%)
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
- **URL 结构**: `/api/v1/resources/{id}/sub-resources`
- **参数命名**: 使用 snake_case (`page_size`, `sort_by`)

### 响应格式
统一的 JSON 响应结构:
```json
{
  "code": 200,
  "message": "success",
  "data": {...},
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

### 错误处理
标准错误响应:
```json
{
  "code": 400,
  "message": "Bad Request",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

---

## 四、资源端点映射


### Active_tasks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/active_tasks` | list | 获取 active_tasks 列表 |
| GET | `/api/v1/active_tasks/{id}` | get | 获取单个 active_tasks 详情 |

### Active_version

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/active_version` | list | 获取 active_version 列表 |
| GET | `/api/v1/active_version/{id}` | get | 获取单个 active_version 详情 |

### Activity_log

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/activity_log` | list | 获取 activity_log 列表 |
| GET | `/api/v1/activity_log/{id}` | get | 获取单个 activity_log 详情 |

### Adapter_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/adapter_status` | list | 获取 adapter_status 列表 |
| GET | `/api/v1/adapter_status/{id}` | get | 获取单个 adapter_status 详情 |

### Admin

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/admin` | list | 获取 admin 列表 |
| GET | `/api/v1/admin/{id}` | get | 获取单个 admin 详情 |

### Agent

**原始端点数**: 4
**统一后端点数**: 2
**减少**: 2 (50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/agent` | list | 获取 agent 列表 |
| GET | `/api/v1/agent/{id}` | get | 获取单个 agent 详情 |

### Agent_coordinator

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/agent_coordinator` | list | 获取 agent_coordinator 列表 |
| GET | `/api/v1/agent_coordinator/{id}` | get | 获取单个 agent_coordinator 详情 |

### Agent_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/agent_info` | list | 获取 agent_info 列表 |
| GET | `/api/v1/agent_info/{id}` | get | 获取单个 agent_info 详情 |

### Agent_integration

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/agent_integration` | list | 获取 agent_integration 列表 |
| GET | `/api/v1/agent_integration/{id}` | get | 获取单个 agent_integration 详情 |

### Agent_metadata

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/agent_metadata` | list | 获取 agent_metadata 列表 |
| GET | `/api/v1/agent_metadata/{id}` | get | 获取单个 agent_metadata 详情 |

### Agent_registry

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/agent_registry` | list | 获取 agent_registry 列表 |
| GET | `/api/v1/agent_registry/{id}` | get | 获取单个 agent_registry 详情 |

### Aggregate

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/aggregate` | list | 获取 aggregate 列表 |
| GET | `/api/v1/aggregate/{id}` | get | 获取单个 aggregate 详情 |

### Aggregated_keywords

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/aggregated_keywords` | list | 获取 aggregated_keywords 列表 |
| GET | `/api/v1/aggregated_keywords/{id}` | get | 获取单个 aggregated_keywords 详情 |

### Aggregated_skills

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/aggregated_skills` | list | 获取 aggregated_skills 列表 |
| GET | `/api/v1/aggregated_skills/{id}` | get | 获取单个 aggregated_skills 详情 |

### Ai_call_manager

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/ai_call_manager` | list | 获取 ai_call_manager 列表 |
| GET | `/api/v1/ai_call_manager/{id}` | get | 获取单个 ai_call_manager 详情 |

### Ai_evaluation

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/ai_evaluation` | list | 获取 ai_evaluation 列表 |
| GET | `/api/v1/ai_evaluation/{id}` | get | 获取单个 ai_evaluation 详情 |

### All

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all` | list | 获取 all 列表 |
| GET | `/api/v1/all/{id}` | get | 获取单个 all 详情 |

### All_discovered_entities

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_discovered_entities` | list | 获取 all_discovered_entities 列表 |
| GET | `/api/v1/all_discovered_entities/{id}` | get | 获取单个 all_discovered_entities 详情 |

### All_discovered_topics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_discovered_topics` | list | 获取 all_discovered_topics 列表 |
| GET | `/api/v1/all_discovered_topics/{id}` | get | 获取单个 all_discovered_topics 详情 |

### All_loaded

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_loaded` | list | 获取 all_loaded 列表 |
| GET | `/api/v1/all_loaded/{id}` | get | 获取单个 all_loaded 详情 |

### All_memories

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_memories` | list | 获取 all_memories 列表 |
| GET | `/api/v1/all_memories/{id}` | get | 获取单个 all_memories 详情 |

### All_metadata

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_metadata` | list | 获取 all_metadata 列表 |
| GET | `/api/v1/all_metadata/{id}` | get | 获取单个 all_metadata 详情 |

### All_permissions

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_permissions` | list | 获取 all_permissions 列表 |
| GET | `/api/v1/all_permissions/{id}` | get | 获取单个 all_permissions 详情 |

### All_plugins

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_plugins` | list | 获取 all_plugins 列表 |
| GET | `/api/v1/all_plugins/{id}` | get | 获取单个 all_plugins 详情 |

### All_services_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_services_status` | list | 获取 all_services_status 列表 |
| GET | `/api/v1/all_services_status/{id}` | get | 获取单个 all_services_status 详情 |

### All_stages

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_stages` | list | 获取 all_stages 列表 |
| GET | `/api/v1/all_stages/{id}` | get | 获取单个 all_stages 详情 |

### All_tag_names

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_tag_names` | list | 获取 all_tag_names 列表 |
| GET | `/api/v1/all_tag_names/{id}` | get | 获取单个 all_tag_names 详情 |

### All_tasks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_tasks` | list | 获取 all_tasks 列表 |
| GET | `/api/v1/all_tasks/{id}` | get | 获取单个 all_tasks 详情 |

### All_templates

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/all_templates` | list | 获取 all_templates 列表 |
| GET | `/api/v1/all_templates/{id}` | get | 获取单个 all_templates 详情 |

### Analyses

**原始端点数**: 3
**统一后端点数**: 6
**减少**: -3 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/analyses` | list | 获取 analyses 列表 |
| POST | `/api/v1/analyses` | create | 创建新的 analyses |
| GET | `/api/v1/analyses/{id}` | get | 获取单个 analyses 详情 |
| PUT | `/api/v1/analyses/{id}` | update | 完整更新 analyses |
| PATCH | `/api/v1/analyses/{id}` | partial_update | 部分更新 analyses |
| DELETE | `/api/v1/analyses/{id}` | delete | 删除 analyses |

### Analysis

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/analysis` | list | 获取 analysis 列表 |
| GET | `/api/v1/analysis/{id}` | get | 获取单个 analysis 详情 |
| DELETE | `/api/v1/analysis/{id}` | delete | 删除 analysis |

### Analysis_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/analysis_service` | list | 获取 analysis_service 列表 |
| GET | `/api/v1/analysis_service/{id}` | get | 获取单个 analysis_service 详情 |

### Analysis_with_sources

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/analysis_with_sources` | list | 获取 analysis_with_sources 列表 |
| GET | `/api/v1/analysis_with_sources/{id}` | get | 获取单个 analysis_with_sources 详情 |

### Analyzer

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/analyzer` | list | 获取 analyzer 列表 |
| GET | `/api/v1/analyzer/{id}` | get | 获取单个 analyzer 详情 |

### Annotation

**原始端点数**: 3
**统一后端点数**: 3
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/annotation` | list | 获取 annotation 列表 |
| GET | `/api/v1/annotation/{id}` | get | 获取单个 annotation 详情 |
| DELETE | `/api/v1/annotation/{id}` | delete | 删除 annotation |

### Annotation_by_id

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/annotation_by_id` | list | 获取 annotation_by_id 列表 |
| GET | `/api/v1/annotation_by_id/{id}` | get | 获取单个 annotation_by_id 详情 |

### Annotation_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/annotation_service` | list | 获取 annotation_service 列表 |
| GET | `/api/v1/annotation_service/{id}` | get | 获取单个 annotation_service 详情 |

### Annotation_statistics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/annotation_statistics` | list | 获取 annotation_statistics 列表 |
| GET | `/api/v1/annotation_statistics/{id}` | get | 获取单个 annotation_statistics 详情 |

### Annotation_trend

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/annotation_trend` | list | 获取 annotation_trend 列表 |
| GET | `/api/v1/annotation_trend/{id}` | get | 获取单个 annotation_trend 详情 |

### Annotations

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/annotations` | list | 获取 annotations 列表 |
| GET | `/api/v1/annotations/{id}` | get | 获取单个 annotations 详情 |

### Annotations_for_target

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/annotations_for_target` | list | 获取 annotations_for_target 列表 |
| GET | `/api/v1/annotations_for_target/{id}` | get | 获取单个 annotations_for_target 详情 |

### Api

**原始端点数**: 21
**统一后端点数**: 5
**减少**: 16 (76.2%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/api` | list | 获取 api 列表 |
| POST | `/api/v1/api` | create | 创建新的 api |
| GET | `/api/v1/api/{id}` | get | 获取单个 api 详情 |
| PUT | `/api/v1/api/{id}` | update | 完整更新 api |
| PATCH | `/api/v1/api/{id}` | partial_update | 部分更新 api |

### Api_gateway

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/api_gateway` | list | 获取 api_gateway 列表 |
| GET | `/api/v1/api_gateway/{id}` | get | 获取单个 api_gateway 详情 |

### Api_metrics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/api_metrics` | list | 获取 api_metrics 列表 |
| GET | `/api/v1/api_metrics/{id}` | get | 获取单个 api_metrics 详情 |

### Api_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/api_stats` | list | 获取 api_stats 列表 |
| GET | `/api/v1/api_stats/{id}` | get | 获取单个 api_stats 详情 |

### App

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/app` | list | 获取 app 列表 |
| GET | `/api/v1/app/{id}` | get | 获取单个 app 详情 |

### Audio

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audio` | list | 获取 audio 列表 |
| GET | `/api/v1/audio/{id}` | get | 获取单个 audio 详情 |

### Audio-segment

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audio-segment` | list | 获取 audio-segment 列表 |
| GET | `/api/v1/audio-segment/{id}` | get | 获取单个 audio-segment 详情 |

### Audio_chunker

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audio_chunker` | list | 获取 audio_chunker 列表 |
| GET | `/api/v1/audio_chunker/{id}` | get | 获取单个 audio_chunker 详情 |

### Audio_duration

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audio_duration` | list | 获取 audio_duration 列表 |
| GET | `/api/v1/audio_duration/{id}` | get | 获取单个 audio_duration 详情 |

### Audio_info

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audio_info` | list | 获取 audio_info 列表 |
| GET | `/api/v1/audio_info/{id}` | get | 获取单个 audio_info 详情 |

### Audio_processing_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audio_processing_status` | list | 获取 audio_processing_status 列表 |
| GET | `/api/v1/audio_processing_status/{id}` | get | 获取单个 audio_processing_status 详情 |

### Audio_segment

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audio_segment` | list | 获取 audio_segment 列表 |
| GET | `/api/v1/audio_segment/{id}` | get | 获取单个 audio_segment 详情 |

### Audit_logs

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audit_logs` | list | 获取 audit_logs 列表 |
| GET | `/api/v1/audit_logs/{id}` | get | 获取单个 audit_logs 详情 |

### Audit_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/audit_statistics` | list | 获取 audit_statistics 列表 |
| GET | `/api/v1/audit_statistics/{id}` | get | 获取单个 audit_statistics 详情 |

### Auto-analyze

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/auto-analyze` | create | 创建新的 auto-analyze |
| GET | `/api/v1/auto-analyze/{id}` | get | 获取单个 auto-analyze 详情 |
| PUT | `/api/v1/auto-analyze/{id}` | update | 完整更新 auto-analyze |
| PATCH | `/api/v1/auto-analyze/{id}` | partial_update | 部分更新 auto-analyze |

### Auto-promote

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/auto-promote` | create | 创建新的 auto-promote |
| GET | `/api/v1/auto-promote/{id}` | get | 获取单个 auto-promote 详情 |
| PUT | `/api/v1/auto-promote/{id}` | update | 完整更新 auto-promote |
| PATCH | `/api/v1/auto-promote/{id}` | partial_update | 部分更新 auto-promote |

### Available

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available` | list | 获取 available 列表 |
| GET | `/api/v1/available/{id}` | get | 获取单个 available 详情 |

### Available-documents

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available-documents` | list | 获取 available-documents 列表 |
| GET | `/api/v1/available-documents/{id}` | get | 获取单个 available-documents 详情 |

### Available_crawlers

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available_crawlers` | list | 获取 available_crawlers 列表 |
| GET | `/api/v1/available_crawlers/{id}` | get | 获取单个 available_crawlers 详情 |

### Available_documents

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available_documents` | list | 获取 available_documents 列表 |
| GET | `/api/v1/available_documents/{id}` | get | 获取单个 available_documents 详情 |

### Available_query_types

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available_query_types` | list | 获取 available_query_types 列表 |
| GET | `/api/v1/available_query_types/{id}` | get | 获取单个 available_query_types 详情 |

### Available_skills

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available_skills` | list | 获取 available_skills 列表 |
| GET | `/api/v1/available_skills/{id}` | get | 获取单个 available_skills 详情 |

### Available_skills_for_task

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available_skills_for_task` | list | 获取 available_skills_for_task 列表 |
| GET | `/api/v1/available_skills_for_task/{id}` | get | 获取单个 available_skills_for_task 详情 |

### Available_strategies

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/available_strategies` | list | 获取 available_strategies 列表 |
| GET | `/api/v1/available_strategies/{id}` | get | 获取单个 available_strategies 详情 |

### Background_learner

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/background_learner` | list | 获取 background_learner 列表 |
| GET | `/api/v1/background_learner/{id}` | get | 获取单个 background_learner 详情 |

### Batch

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/batch/{id}` | get | 获取单个 batch 详情 |
| DELETE | `/api/v1/batch/{id}` | delete | 删除 batch |

### Batch-crawl

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/batch-crawl` | create | 创建新的 batch-crawl |
| GET | `/api/v1/batch-crawl/{id}` | get | 获取单个 batch-crawl 详情 |
| PUT | `/api/v1/batch-crawl/{id}` | update | 完整更新 batch-crawl |
| PATCH | `/api/v1/batch-crawl/{id}` | partial_update | 部分更新 batch-crawl |

### Batch_status

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/batch_status` | list | 获取 batch_status 列表 |
| GET | `/api/v1/batch_status/{id}` | get | 获取单个 batch_status 详情 |

### Best_tool

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/best_tool` | list | 获取 best_tool 列表 |
| GET | `/api/v1/best_tool/{id}` | get | 获取单个 best_tool 详情 |

### Broadcast

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/broadcast` | create | 创建新的 broadcast |
| GET | `/api/v1/broadcast/{id}` | get | 获取单个 broadcast 详情 |
| PUT | `/api/v1/broadcast/{id}` | update | 完整更新 broadcast |
| PATCH | `/api/v1/broadcast/{id}` | partial_update | 部分更新 broadcast |

### Build

**原始端点数**: 3
**统一后端点数**: 4
**减少**: -1 (-33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/build` | create | 创建新的 build |
| GET | `/api/v1/build/{id}` | get | 获取单个 build 详情 |
| PUT | `/api/v1/build/{id}` | update | 完整更新 build |
| PATCH | `/api/v1/build/{id}` | partial_update | 部分更新 build |

### Build-prompt

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/build-prompt` | create | 创建新的 build-prompt |
| GET | `/api/v1/build-prompt/{id}` | get | 获取单个 build-prompt 详情 |
| PUT | `/api/v1/build-prompt/{id}` | update | 完整更新 build-prompt |
| PATCH | `/api/v1/build-prompt/{id}` | partial_update | 部分更新 build-prompt |

### Business_analysis_skill

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/business_analysis_skill` | list | 获取 business_analysis_skill 列表 |
| GET | `/api/v1/business_analysis_skill/{id}` | get | 获取单个 business_analysis_skill 详情 |

### By_entity

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/by_entity/{id}` | get | 获取单个 by_entity 详情 |
| DELETE | `/api/v1/by_entity/{id}` | delete | 删除 by_entity |

### By_ids

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/by_ids` | list | 获取 by_ids 列表 |
| GET | `/api/v1/by_ids/{id}` | get | 获取单个 by_ids 详情 |
| DELETE | `/api/v1/by_ids/{id}` | delete | 删除 by_ids |

### Cache

**原始端点数**: 3
**统一后端点数**: 5
**减少**: -2 (-66.7%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cache` | list | 获取 cache 列表 |
| POST | `/api/v1/cache` | create | 创建新的 cache |
| GET | `/api/v1/cache/{id}` | get | 获取单个 cache 详情 |
| PUT | `/api/v1/cache/{id}` | update | 完整更新 cache |
| PATCH | `/api/v1/cache/{id}` | partial_update | 部分更新 cache |

### Cache_backend

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cache_backend` | list | 获取 cache_backend 列表 |
| GET | `/api/v1/cache_backend/{id}` | get | 获取单个 cache_backend 详情 |

### Cache_manager

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cache_manager` | list | 获取 cache_manager 列表 |
| GET | `/api/v1/cache_manager/{id}` | get | 获取单个 cache_manager 详情 |

### Cache_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cache_stats` | list | 获取 cache_stats 列表 |
| GET | `/api/v1/cache_stats/{id}` | get | 获取单个 cache_stats 详情 |

### Cached

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cached` | list | 获取 cached 列表 |
| GET | `/api/v1/cached/{id}` | get | 获取单个 cached 详情 |

### Calculated_values

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/calculated_values` | list | 获取 calculated_values 列表 |
| GET | `/api/v1/calculated_values/{id}` | get | 获取单个 calculated_values 详情 |

### Cancel

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/cancel` | create | 创建新的 cancel |
| GET | `/api/v1/cancel/{id}` | get | 获取单个 cancel 详情 |
| PUT | `/api/v1/cancel/{id}` | update | 完整更新 cancel |
| PATCH | `/api/v1/cancel/{id}` | partial_update | 部分更新 cancel |

### Capabilities

**原始端点数**: 4
**统一后端点数**: 2
**减少**: 2 (50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/capabilities` | list | 获取 capabilities 列表 |
| GET | `/api/v1/capabilities/{id}` | get | 获取单个 capabilities 详情 |

### Capabilities_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/capabilities_info` | list | 获取 capabilities_info 列表 |
| GET | `/api/v1/capabilities_info/{id}` | get | 获取单个 capabilities_info 详情 |

### Capability_index

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/capability_index` | list | 获取 capability_index 列表 |
| GET | `/api/v1/capability_index/{id}` | get | 获取单个 capability_index 详情 |

### Categories

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/categories` | list | 获取 categories 列表 |
| GET | `/api/v1/categories/{id}` | get | 获取单个 categories 详情 |

### Category_display_name

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/category_display_name` | list | 获取 category_display_name 列表 |
| GET | `/api/v1/category_display_name/{id}` | get | 获取单个 category_display_name 详情 |

### Category_evidences

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/category_evidences` | list | 获取 category_evidences 列表 |
| GET | `/api/v1/category_evidences/{id}` | get | 获取单个 category_evidences 详情 |

### Category_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/category_stats` | list | 获取 category_stats 列表 |
| GET | `/api/v1/category_stats/{id}` | get | 获取单个 category_stats 详情 |

### Chat

**原始端点数**: 9
**统一后端点数**: 6
**减少**: 3 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chat` | list | 获取 chat 列表 |
| POST | `/api/v1/chat` | create | 创建新的 chat |
| GET | `/api/v1/chat/{id}` | get | 获取单个 chat 详情 |
| PUT | `/api/v1/chat/{id}` | update | 完整更新 chat |
| PATCH | `/api/v1/chat/{id}` | partial_update | 部分更新 chat |
| DELETE | `/api/v1/chat/{id}` | delete | 删除 chat |

### Chat_messages

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chat_messages` | list | 获取 chat_messages 列表 |
| GET | `/api/v1/chat_messages/{id}` | get | 获取单个 chat_messages 详情 |

### Chat_session

**原始端点数**: 3
**统一后端点数**: 3
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chat_session` | list | 获取 chat_session 列表 |
| GET | `/api/v1/chat_session/{id}` | get | 获取单个 chat_session 详情 |
| DELETE | `/api/v1/chat_session/{id}` | delete | 删除 chat_session |

### Check

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/check` | list | 获取 check 列表 |
| GET | `/api/v1/check/{id}` | get | 获取单个 check 详情 |

### Chinese_nlp_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chinese_nlp_service` | list | 获取 chinese_nlp_service 列表 |
| GET | `/api/v1/chinese_nlp_service/{id}` | get | 获取单个 chinese_nlp_service 详情 |

### Chunk

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk` | list | 获取 chunk 列表 |
| GET | `/api/v1/chunk/{id}` | get | 获取单个 chunk 详情 |

### Chunk_context

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_context` | list | 获取 chunk_context 列表 |
| GET | `/api/v1/chunk_context/{id}` | get | 获取单个 chunk_context 详情 |

### Chunk_detail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_detail` | list | 获取 chunk_detail 列表 |
| GET | `/api/v1/chunk_detail/{id}` | get | 获取单个 chunk_detail 详情 |

### Chunk_keywords

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_keywords` | list | 获取 chunk_keywords 列表 |
| GET | `/api/v1/chunk_keywords/{id}` | get | 获取单个 chunk_keywords 详情 |

### Chunk_lineage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_lineage` | list | 获取 chunk_lineage 列表 |
| GET | `/api/v1/chunk_lineage/{id}` | get | 获取单个 chunk_lineage 详情 |

### Chunk_metrics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_metrics` | list | 获取 chunk_metrics 列表 |
| GET | `/api/v1/chunk_metrics/{id}` | get | 获取单个 chunk_metrics 详情 |

### Chunk_metrics_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_metrics_summary` | list | 获取 chunk_metrics_summary 列表 |
| GET | `/api/v1/chunk_metrics_summary/{id}` | get | 获取单个 chunk_metrics_summary 详情 |

### Chunk_preview

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_preview` | list | 获取 chunk_preview 列表 |
| GET | `/api/v1/chunk_preview/{id}` | get | 获取单个 chunk_preview 详情 |

### Chunk_quantification

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_quantification` | list | 获取 chunk_quantification 列表 |
| GET | `/api/v1/chunk_quantification/{id}` | get | 获取单个 chunk_quantification 详情 |

### Chunk_statistics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_statistics` | list | 获取 chunk_statistics 列表 |
| GET | `/api/v1/chunk_statistics/{id}` | get | 获取单个 chunk_statistics 详情 |

### Chunk_with_citation

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunk_with_citation` | list | 获取 chunk_with_citation 列表 |
| GET | `/api/v1/chunk_with_citation/{id}` | get | 获取单个 chunk_with_citation 详情 |

### Chunking_agent

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunking_agent` | list | 获取 chunking_agent 列表 |
| GET | `/api/v1/chunking_agent/{id}` | get | 获取单个 chunking_agent 详情 |

### Chunks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunks` | list | 获取 chunks 列表 |
| GET | `/api/v1/chunks/{id}` | get | 获取单个 chunks 详情 |

### Chunks_preview

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/chunks_preview` | list | 获取 chunks_preview 列表 |
| GET | `/api/v1/chunks_preview/{id}` | get | 获取单个 chunks_preview 详情 |

### Circuit_breaker

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/circuit_breaker` | list | 获取 circuit_breaker 列表 |
| GET | `/api/v1/circuit_breaker/{id}` | get | 获取单个 circuit_breaker 详情 |

### Circuit_breaker_status

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/circuit_breaker_status` | list | 获取 circuit_breaker_status 列表 |
| GET | `/api/v1/circuit_breaker_status/{id}` | get | 获取单个 circuit_breaker_status 详情 |

### Citation

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/citation` | list | 获取 citation 列表 |
| GET | `/api/v1/citation/{id}` | get | 获取单个 citation 详情 |
| DELETE | `/api/v1/citation/{id}` | delete | 删除 citation |

### Citation_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/citation_stats` | list | 获取 citation_stats 列表 |
| GET | `/api/v1/citation_stats/{id}` | get | 获取单个 citation_stats 详情 |

### Citations

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/citations` | create | 创建新的 citations |
| GET | `/api/v1/citations/{id}` | get | 获取单个 citations 详情 |
| PUT | `/api/v1/citations/{id}` | update | 完整更新 citations |
| PATCH | `/api/v1/citations/{id}` | partial_update | 部分更新 citations |
| DELETE | `/api/v1/citations/{id}` | delete | 删除 citations |

### Cleanup

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/cleanup` | create | 创建新的 cleanup |
| GET | `/api/v1/cleanup/{id}` | get | 获取单个 cleanup 详情 |
| PUT | `/api/v1/cleanup/{id}` | update | 完整更新 cleanup |
| PATCH | `/api/v1/cleanup/{id}` | partial_update | 部分更新 cleanup |
| DELETE | `/api/v1/cleanup/{id}` | delete | 删除 cleanup |

### Client_info

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/client_info` | list | 获取 client_info 列表 |
| GET | `/api/v1/client_info/{id}` | get | 获取单个 client_info 详情 |

### Clients

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/clients` | list | 获取 clients 列表 |
| GET | `/api/v1/clients/{id}` | get | 获取单个 clients 详情 |

### Cluster

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/cluster` | create | 创建新的 cluster |
| GET | `/api/v1/cluster/{id}` | get | 获取单个 cluster 详情 |
| PUT | `/api/v1/cluster/{id}` | update | 完整更新 cluster |
| PATCH | `/api/v1/cluster/{id}` | partial_update | 部分更新 cluster |

### Cluster_chunks

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cluster_chunks` | list | 获取 cluster_chunks 列表 |
| GET | `/api/v1/cluster_chunks/{id}` | get | 获取单个 cluster_chunks 详情 |

### Cluster_results

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cluster_results` | list | 获取 cluster_results 列表 |
| GET | `/api/v1/cluster_results/{id}` | get | 获取单个 cluster_results 详情 |

### Cluster_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cluster_summary` | list | 获取 cluster_summary 列表 |
| GET | `/api/v1/cluster_summary/{id}` | get | 获取单个 cluster_summary 详情 |

### Clusters

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/clusters` | list | 获取 clusters 列表 |
| GET | `/api/v1/clusters/{id}` | get | 获取单个 clusters 详情 |

### Cognee_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cognee_service` | list | 获取 cognee_service 列表 |
| GET | `/api/v1/cognee_service/{id}` | get | 获取单个 cognee_service 详情 |

### Collection

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/collection/{id}` | get | 获取单个 collection 详情 |
| DELETE | `/api/v1/collection/{id}` | delete | 删除 collection |

### Collection_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/collection_info` | list | 获取 collection_info 列表 |
| GET | `/api/v1/collection_info/{id}` | get | 获取单个 collection_info 详情 |

### Compare-strategies

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/compare-strategies` | create | 创建新的 compare-strategies |
| GET | `/api/v1/compare-strategies/{id}` | get | 获取单个 compare-strategies 详情 |
| PUT | `/api/v1/compare-strategies/{id}` | update | 完整更新 compare-strategies |
| PATCH | `/api/v1/compare-strategies/{id}` | partial_update | 部分更新 compare-strategies |

### Comparison_results

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/comparison_results` | list | 获取 comparison_results 列表 |
| GET | `/api/v1/comparison_results/{id}` | get | 获取单个 comparison_results 详情 |

### Comparisons

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/comparisons` | list | 获取 comparisons 列表 |
| GET | `/api/v1/comparisons/{id}` | get | 获取单个 comparisons 详情 |

### Compliance_report

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/compliance_report` | list | 获取 compliance_report 列表 |
| GET | `/api/v1/compliance_report/{id}` | get | 获取单个 compliance_report 详情 |

### Config

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/config` | create | 创建新的 config |
| GET | `/api/v1/config/{id}` | get | 获取单个 config 详情 |
| PUT | `/api/v1/config/{id}` | update | 完整更新 config |
| PATCH | `/api/v1/config/{id}` | partial_update | 部分更新 config |

### Configuration

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/configuration` | list | 获取 configuration 列表 |
| GET | `/api/v1/configuration/{id}` | get | 获取单个 configuration 详情 |

### Connection_count

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/connection_count` | list | 获取 connection_count 列表 |
| GET | `/api/v1/connection_count/{id}` | get | 获取单个 connection_count 详情 |

### Connection_manager

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/connection_manager` | list | 获取 connection_manager 列表 |
| GET | `/api/v1/connection_manager/{id}` | get | 获取单个 connection_manager 详情 |

### Content

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/content` | list | 获取 content 列表 |
| GET | `/api/v1/content/{id}` | get | 获取单个 content 详情 |

### Content_at_time

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/content_at_time` | list | 获取 content_at_time 列表 |
| GET | `/api/v1/content_at_time/{id}` | get | 获取单个 content_at_time 详情 |

### Context_for_entity

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/context_for_entity` | list | 获取 context_for_entity 列表 |
| GET | `/api/v1/context_for_entity/{id}` | get | 获取单个 context_for_entity 详情 |

### Context_for_position

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/context_for_position` | list | 获取 context_for_position 列表 |
| GET | `/api/v1/context_for_position/{id}` | get | 获取单个 context_for_position 详情 |

### Context_for_prompt

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/context_for_prompt` | list | 获取 context_for_prompt 列表 |
| GET | `/api/v1/context_for_prompt/{id}` | get | 获取单个 context_for_prompt 详情 |

### Conversation

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/conversation` | list | 获取 conversation 列表 |
| GET | `/api/v1/conversation/{id}` | get | 获取单个 conversation 详情 |
| DELETE | `/api/v1/conversation/{id}` | delete | 删除 conversation |

### Conversation_context

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/conversation_context` | list | 获取 conversation_context 列表 |
| GET | `/api/v1/conversation_context/{id}` | get | 获取单个 conversation_context 详情 |

### Conversation_history

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/conversation_history` | list | 获取 conversation_history 列表 |
| GET | `/api/v1/conversation_history/{id}` | get | 获取单个 conversation_history 详情 |

### Conversation_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/conversation_service` | list | 获取 conversation_service 列表 |
| GET | `/api/v1/conversation_service/{id}` | get | 获取单个 conversation_service 详情 |

### Conversation_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/conversation_statistics` | list | 获取 conversation_statistics 列表 |
| GET | `/api/v1/conversation_statistics/{id}` | get | 获取单个 conversation_statistics 详情 |

### Conversation_summary

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/conversation_summary` | list | 获取 conversation_summary 列表 |
| GET | `/api/v1/conversation_summary/{id}` | get | 获取单个 conversation_summary 详情 |

### Conversations_by_category

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/conversations_by_category` | list | 获取 conversations_by_category 列表 |
| GET | `/api/v1/conversations_by_category/{id}` | get | 获取单个 conversations_by_category 详情 |

### Coordinator

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/coordinator` | list | 获取 coordinator 列表 |
| GET | `/api/v1/coordinator/{id}` | get | 获取单个 coordinator 详情 |

### Coordinator_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/coordinator_status` | list | 获取 coordinator_status 列表 |
| GET | `/api/v1/coordinator_status/{id}` | get | 获取单个 coordinator_status 详情 |

### Corrections

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/corrections` | list | 获取 corrections 列表 |
| GET | `/api/v1/corrections/{id}` | get | 获取单个 corrections 详情 |

### Crawl

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/crawl` | create | 创建新的 crawl |
| GET | `/api/v1/crawl/{id}` | get | 获取单个 crawl 详情 |
| PUT | `/api/v1/crawl/{id}` | update | 完整更新 crawl |
| PATCH | `/api/v1/crawl/{id}` | partial_update | 部分更新 crawl |

### Crawl_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/crawl_status` | list | 获取 crawl_status 列表 |
| GET | `/api/v1/crawl_status/{id}` | get | 获取单个 crawl_status 详情 |

### Crawler

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/crawler` | create | 创建新的 crawler |
| GET | `/api/v1/crawler/{id}` | get | 获取单个 crawler 详情 |
| PUT | `/api/v1/crawler/{id}` | update | 完整更新 crawler |
| PATCH | `/api/v1/crawler/{id}` | partial_update | 部分更新 crawler |

### Crawler_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/crawler_service` | list | 获取 crawler_service 列表 |
| GET | `/api/v1/crawler_service/{id}` | get | 获取单个 crawler_service 详情 |

### Cultural_elements

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/cultural_elements` | list | 获取 cultural_elements 列表 |
| GET | `/api/v1/cultural_elements/{id}` | get | 获取单个 cultural_elements 详情 |

### Current_active_user

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/current_active_user` | list | 获取 current_active_user 列表 |
| GET | `/api/v1/current_active_user/{id}` | get | 获取单个 current_active_user 详情 |

### Current_admin_user

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/current_admin_user` | list | 获取 current_admin_user 列表 |
| GET | `/api/v1/current_admin_user/{id}` | get | 获取单个 current_admin_user 详情 |

### Current_user

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/current_user` | list | 获取 current_user 列表 |
| GET | `/api/v1/current_user/{id}` | get | 获取单个 current_user 详情 |

### Current_user_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/current_user_info` | list | 获取 current_user_info 列表 |
| GET | `/api/v1/current_user_info/{id}` | get | 获取单个 current_user_info 详情 |

### Cypher

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/cypher` | create | 创建新的 cypher |
| GET | `/api/v1/cypher/{id}` | get | 获取单个 cypher 详情 |
| PUT | `/api/v1/cypher/{id}` | update | 完整更新 cypher |
| PATCH | `/api/v1/cypher/{id}` | partial_update | 部分更新 cypher |

### Dashboard

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dashboard` | list | 获取 dashboard 列表 |
| GET | `/api/v1/dashboard/{id}` | get | 获取单个 dashboard 详情 |

### Dashboard_aggregate

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dashboard_aggregate` | list | 获取 dashboard_aggregate 列表 |
| GET | `/api/v1/dashboard_aggregate/{id}` | get | 获取单个 dashboard_aggregate 详情 |

### Dashboard_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dashboard_stats` | list | 获取 dashboard_stats 列表 |
| GET | `/api/v1/dashboard_stats/{id}` | get | 获取单个 dashboard_stats 详情 |

### Dashboard_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dashboard_summary` | list | 获取 dashboard_summary 列表 |
| GET | `/api/v1/dashboard_summary/{id}` | get | 获取单个 dashboard_summary 详情 |

### Data

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/data` | list | 获取 data 列表 |
| GET | `/api/v1/data/{id}` | get | 获取单个 data 详情 |

### Data_quality_metrics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/data_quality_metrics` | list | 获取 data_quality_metrics 列表 |
| GET | `/api/v1/data_quality_metrics/{id}` | get | 获取单个 data_quality_metrics 详情 |

### Data_versions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/data_versions` | list | 获取 data_versions 列表 |
| GET | `/api/v1/data_versions/{id}` | get | 获取单个 data_versions 详情 |

### Db

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/db` | list | 获取 db 列表 |
| GET | `/api/v1/db/{id}` | get | 获取单个 db 详情 |

### Db_context

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/db_context` | list | 获取 db_context 列表 |
| GET | `/api/v1/db_context/{id}` | get | 获取单个 db_context 详情 |

### Db_session

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/db_session` | list | 获取 db_session 列表 |
| GET | `/api/v1/db_session/{id}` | get | 获取单个 db_session 详情 |

### Deep_rag_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/deep_rag_service` | list | 获取 deep_rag_service 列表 |
| GET | `/api/v1/deep_rag_service/{id}` | get | 获取单个 deep_rag_service 详情 |

### Deep_thinking_engine

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/deep_thinking_engine` | list | 获取 deep_thinking_engine 列表 |
| GET | `/api/v1/deep_thinking_engine/{id}` | get | 获取单个 deep_thinking_engine 详情 |

### Deprecation_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/deprecation_info` | list | 获取 deprecation_info 列表 |
| GET | `/api/v1/deprecation_info/{id}` | get | 获取单个 deprecation_info 详情 |

### Depth

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/depth` | list | 获取 depth 列表 |
| GET | `/api/v1/depth/{id}` | get | 获取单个 depth 详情 |

### Dialect_statistics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dialect_statistics` | list | 获取 dialect_statistics 列表 |
| GET | `/api/v1/dialect_statistics/{id}` | get | 获取单个 dialect_statistics 详情 |

### Dimension_distribution

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dimension_distribution` | list | 获取 dimension_distribution 列表 |
| GET | `/api/v1/dimension_distribution/{id}` | get | 获取单个 dimension_distribution 详情 |

### Dimension_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/dimension_info` | list | 获取 dimension_info 列表 |
| GET | `/api/v1/dimension_info/{id}` | get | 获取单个 dimension_info 详情 |

### Document

**原始端点数**: 14
**统一后端点数**: 6
**减少**: 8 (57.1%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document` | list | 获取 document 列表 |
| POST | `/api/v1/document` | create | 创建新的 document |
| GET | `/api/v1/document/{id}` | get | 获取单个 document 详情 |
| PUT | `/api/v1/document/{id}` | update | 完整更新 document |
| PATCH | `/api/v1/document/{id}` | partial_update | 部分更新 document |
| DELETE | `/api/v1/document/{id}` | delete | 删除 document |

### Document-stats

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/document-stats` | create | 创建新的 document-stats |
| GET | `/api/v1/document-stats/{id}` | get | 获取单个 document-stats 详情 |
| PUT | `/api/v1/document-stats/{id}` | update | 完整更新 document-stats |
| PATCH | `/api/v1/document-stats/{id}` | partial_update | 部分更新 document-stats |

### Document_audio

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_audio` | list | 获取 document_audio 列表 |
| GET | `/api/v1/document_audio/{id}` | get | 获取单个 document_audio 详情 |

### Document_chunks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_chunks` | list | 获取 document_chunks 列表 |
| GET | `/api/v1/document_chunks/{id}` | get | 获取单个 document_chunks 详情 |

### Document_chunks_lineage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_chunks_lineage` | list | 获取 document_chunks_lineage 列表 |
| GET | `/api/v1/document_chunks_lineage/{id}` | get | 获取单个 document_chunks_lineage 详情 |

### Document_chunks_metrics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_chunks_metrics` | list | 获取 document_chunks_metrics 列表 |
| GET | `/api/v1/document_chunks_metrics/{id}` | get | 获取单个 document_chunks_metrics 详情 |

### Document_content

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_content` | list | 获取 document_content 列表 |
| GET | `/api/v1/document_content/{id}` | get | 获取单个 document_content 详情 |

### Document_coverage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_coverage` | list | 获取 document_coverage 列表 |
| GET | `/api/v1/document_coverage/{id}` | get | 获取单个 document_coverage 详情 |

### Document_detail

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_detail` | list | 获取 document_detail 列表 |
| GET | `/api/v1/document_detail/{id}` | get | 获取单个 document_detail 详情 |

### Document_discovery

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_discovery` | list | 获取 document_discovery 列表 |
| GET | `/api/v1/document_discovery/{id}` | get | 获取单个 document_discovery 详情 |

### Document_entities

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_entities` | list | 获取 document_entities 列表 |
| GET | `/api/v1/document_entities/{id}` | get | 获取单个 document_entities 详情 |

### Document_fact_statements

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_fact_statements` | list | 获取 document_fact_statements 列表 |
| GET | `/api/v1/document_fact_statements/{id}` | get | 获取单个 document_fact_statements 详情 |

### Document_metrics_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_metrics_summary` | list | 获取 document_metrics_summary 列表 |
| GET | `/api/v1/document_metrics_summary/{id}` | get | 获取单个 document_metrics_summary 详情 |

### Document_quality_detail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_quality_detail` | list | 获取 document_quality_detail 列表 |
| GET | `/api/v1/document_quality_detail/{id}` | get | 获取单个 document_quality_detail 详情 |

### Document_single_skill_result

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_single_skill_result` | list | 获取 document_single_skill_result 列表 |
| GET | `/api/v1/document_single_skill_result/{id}` | get | 获取单个 document_single_skill_result 详情 |

### Document_skill_results

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_skill_results` | list | 获取 document_skill_results 列表 |
| GET | `/api/v1/document_skill_results/{id}` | get | 获取单个 document_skill_results 详情 |

### Document_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_status` | list | 获取 document_status 列表 |
| GET | `/api/v1/document_status/{id}` | get | 获取单个 document_status 详情 |

### Document_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_summary` | list | 获取 document_summary 列表 |
| GET | `/api/v1/document_summary/{id}` | get | 获取单个 document_summary 详情 |

### Document_tag

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_tag/{id}` | get | 获取单个 document_tag 详情 |
| DELETE | `/api/v1/document_tag/{id}` | delete | 删除 document_tag |

### Document_vectors

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/document_vectors/{id}` | get | 获取单个 document_vectors 详情 |
| DELETE | `/api/v1/document_vectors/{id}` | delete | 删除 document_vectors |

### Documents

**原始端点数**: 14
**统一后端点数**: 5
**减少**: 9 (64.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/documents` | list | 获取 documents 列表 |
| POST | `/api/v1/documents` | create | 创建新的 documents |
| GET | `/api/v1/documents/{id}` | get | 获取单个 documents 详情 |
| PUT | `/api/v1/documents/{id}` | update | 完整更新 documents |
| PATCH | `/api/v1/documents/{id}` | partial_update | 部分更新 documents |

### Documents_batch

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/documents_batch/{id}` | get | 获取单个 documents_batch 详情 |
| DELETE | `/api/v1/documents_batch/{id}` | delete | 删除 documents_batch |

### Documents_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/documents_status` | list | 获取 documents_status 列表 |
| GET | `/api/v1/documents_status/{id}` | get | 获取单个 documents_status 详情 |

### Download

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/download` | list | 获取 download 列表 |
| GET | `/api/v1/download/{id}` | get | 获取单个 download 详情 |

### Download_url

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/download_url` | list | 获取 download_url 列表 |
| GET | `/api/v1/download_url/{id}` | get | 获取单个 download_url 详情 |

### Downstream

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/downstream` | list | 获取 downstream 列表 |
| GET | `/api/v1/downstream/{id}` | get | 获取单个 downstream 详情 |

### Downstream_lineage

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/downstream_lineage` | list | 获取 downstream_lineage 列表 |
| GET | `/api/v1/downstream_lineage/{id}` | get | 获取单个 downstream_lineage 详情 |

### Due_schedules

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/due_schedules` | list | 获取 due_schedules 列表 |
| GET | `/api/v1/due_schedules/{id}` | get | 获取单个 due_schedules 详情 |

### Element

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/element` | list | 获取 element 列表 |
| GET | `/api/v1/element/{id}` | get | 获取单个 element 详情 |

### Embedding_dimension

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/embedding_dimension` | list | 获取 embedding_dimension 列表 |
| GET | `/api/v1/embedding_dimension/{id}` | get | 获取单个 embedding_dimension 详情 |

### Embedding_model

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/embedding_model` | list | 获取 embedding_model 列表 |
| GET | `/api/v1/embedding_model/{id}` | get | 获取单个 embedding_model 详情 |

### Emotion_distribution

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/emotion_distribution` | list | 获取 emotion_distribution 列表 |
| GET | `/api/v1/emotion_distribution/{id}` | get | 获取单个 emotion_distribution 详情 |

### Empty_comparison

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/empty_comparison` | list | 获取 empty_comparison 列表 |
| GET | `/api/v1/empty_comparison/{id}` | get | 获取单个 empty_comparison 详情 |

### Empty_features

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/empty_features` | list | 获取 empty_features 列表 |
| GET | `/api/v1/empty_features/{id}` | get | 获取单个 empty_features 详情 |

### Engine

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/engine` | list | 获取 engine 列表 |
| GET | `/api/v1/engine/{id}` | get | 获取单个 engine 详情 |

### Engine_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/engine_status` | list | 获取 engine_status 列表 |
| GET | `/api/v1/engine_status/{id}` | get | 获取单个 engine_status 详情 |

### Enhanced_metadata

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/enhanced_metadata` | list | 获取 enhanced_metadata 列表 |
| GET | `/api/v1/enhanced_metadata/{id}` | get | 获取单个 enhanced_metadata 详情 |

### Enrichment_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/enrichment_status` | list | 获取 enrichment_status 列表 |
| GET | `/api/v1/enrichment_status/{id}` | get | 获取单个 enrichment_status 详情 |

### Enterprise_hermes

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/enterprise_hermes` | list | 获取 enterprise_hermes 列表 |
| GET | `/api/v1/enterprise_hermes/{id}` | get | 获取单个 enterprise_hermes 详情 |

### Entities

**原始端点数**: 5
**统一后端点数**: 3
**减少**: 2 (40.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entities` | list | 获取 entities 列表 |
| GET | `/api/v1/entities/{id}` | get | 获取单个 entities 详情 |
| DELETE | `/api/v1/entities/{id}` | delete | 删除 entities |

### Entity

**原始端点数**: 3
**统一后端点数**: 3
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity` | list | 获取 entity 列表 |
| GET | `/api/v1/entity/{id}` | get | 获取单个 entity 详情 |
| DELETE | `/api/v1/entity/{id}` | delete | 删除 entity |

### Entity_categorizer

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_categorizer` | list | 获取 entity_categorizer 列表 |
| GET | `/api/v1/entity_categorizer/{id}` | get | 获取单个 entity_categorizer 详情 |

### Entity_conversations

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_conversations` | list | 获取 entity_conversations 列表 |
| GET | `/api/v1/entity_conversations/{id}` | get | 获取单个 entity_conversations 详情 |

### Entity_detail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_detail` | list | 获取 entity_detail 列表 |
| GET | `/api/v1/entity_detail/{id}` | get | 获取单个 entity_detail 详情 |

### Entity_evidences

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_evidences` | list | 获取 entity_evidences 列表 |
| GET | `/api/v1/entity_evidences/{id}` | get | 获取单个 entity_evidences 详情 |

### Entity_extraction_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_extraction_service` | list | 获取 entity_extraction_service 列表 |
| GET | `/api/v1/entity_extraction_service/{id}` | get | 获取单个 entity_extraction_service 详情 |

### Entity_full_profile

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_full_profile` | list | 获取 entity_full_profile 列表 |
| GET | `/api/v1/entity_full_profile/{id}` | get | 获取单个 entity_full_profile 详情 |

### Entity_graph

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_graph` | list | 获取 entity_graph 列表 |
| GET | `/api/v1/entity_graph/{id}` | get | 获取单个 entity_graph 详情 |

### Entity_neighbors

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_neighbors` | list | 获取 entity_neighbors 列表 |
| GET | `/api/v1/entity_neighbors/{id}` | get | 获取单个 entity_neighbors 详情 |

### Entity_profile

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_profile` | list | 获取 entity_profile 列表 |
| GET | `/api/v1/entity_profile/{id}` | get | 获取单个 entity_profile 详情 |

### Entity_relations

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_relations` | list | 获取 entity_relations 列表 |
| GET | `/api/v1/entity_relations/{id}` | get | 获取单个 entity_relations 详情 |

### Entity_timeline

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/entity_timeline` | list | 获取 entity_timeline 列表 |
| GET | `/api/v1/entity_timeline/{id}` | get | 获取单个 entity_timeline 详情 |

### Episodes_by_time_range

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/episodes_by_time_range` | list | 获取 episodes_by_time_range 列表 |
| GET | `/api/v1/episodes_by_time_range/{id}` | get | 获取单个 episodes_by_time_range 详情 |

### Error_message

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/error_message` | list | 获取 error_message 列表 |
| GET | `/api/v1/error_message/{id}` | get | 获取单个 error_message 详情 |

### Error_status_code

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/error_status_code` | list | 获取 error_status_code 列表 |
| GET | `/api/v1/error_status_code/{id}` | get | 获取单个 error_status_code 详情 |

### Event_emitter

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/event_emitter` | list | 获取 event_emitter 列表 |
| GET | `/api/v1/event_emitter/{id}` | get | 获取单个 event_emitter 详情 |

### Event_full_profile

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/event_full_profile` | list | 获取 event_full_profile 列表 |
| GET | `/api/v1/event_full_profile/{id}` | get | 获取单个 event_full_profile 详情 |

### Event_history

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/event_history` | list | 获取 event_history 列表 |
| GET | `/api/v1/event_history/{id}` | get | 获取单个 event_history 详情 |

### Event_profile

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/event_profile` | list | 获取 event_profile 列表 |
| GET | `/api/v1/event_profile/{id}` | get | 获取单个 event_profile 详情 |

### Event_statistics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/event_statistics` | list | 获取 event_statistics 列表 |
| GET | `/api/v1/event_statistics/{id}` | get | 获取单个 event_statistics 详情 |

### Event_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/event_stats` | list | 获取 event_stats 列表 |
| GET | `/api/v1/event_stats/{id}` | get | 获取单个 event_stats 详情 |

### Events

**原始端点数**: 6
**统一后端点数**: 5
**减少**: 1 (16.7%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/events` | list | 获取 events 列表 |
| POST | `/api/v1/events` | create | 创建新的 events |
| GET | `/api/v1/events/{id}` | get | 获取单个 events 详情 |
| PUT | `/api/v1/events/{id}` | update | 完整更新 events |
| PATCH | `/api/v1/events/{id}` | partial_update | 部分更新 events |

### Evidence

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/evidence/{id}` | get | 获取单个 evidence 详情 |
| DELETE | `/api/v1/evidence/{id}` | delete | 删除 evidence |

### Evidence_extractor

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/evidence_extractor` | list | 获取 evidence_extractor 列表 |
| GET | `/api/v1/evidence_extractor/{id}` | get | 获取单个 evidence_extractor 详情 |

### Evidences

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/evidences/{id}` | get | 获取单个 evidences 详情 |
| DELETE | `/api/v1/evidences/{id}` | delete | 删除 evidences |

### Executed_migrations

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/executed_migrations` | list | 获取 executed_migrations 列表 |
| GET | `/api/v1/executed_migrations/{id}` | get | 获取单个 executed_migrations 详情 |

### Execution

**原始端点数**: 5
**统一后端点数**: 2
**减少**: 3 (60.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/execution` | list | 获取 execution 列表 |
| GET | `/api/v1/execution/{id}` | get | 获取单个 execution 详情 |

### Execution_history

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/execution_history` | list | 获取 execution_history 列表 |
| GET | `/api/v1/execution_history/{id}` | get | 获取单个 execution_history 详情 |

### Execution_progress

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/execution_progress` | list | 获取 execution_progress 列表 |
| GET | `/api/v1/execution_progress/{id}` | get | 获取单个 execution_progress 详情 |

### Execution_records

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/execution_records` | list | 获取 execution_records 列表 |
| GET | `/api/v1/execution_records/{id}` | get | 获取单个 execution_records 详情 |

### Execution_statistics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/execution_statistics` | list | 获取 execution_statistics 列表 |
| GET | `/api/v1/execution_statistics/{id}` | get | 获取单个 execution_statistics 详情 |

### Execution_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/execution_status` | list | 获取 execution_status 列表 |
| GET | `/api/v1/execution_status/{id}` | get | 获取单个 execution_status 详情 |

### Executions

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/executions` | list | 获取 executions 列表 |
| GET | `/api/v1/executions/{id}` | get | 获取单个 executions 详情 |

### Executor_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/executor_status` | list | 获取 executor_status 列表 |
| GET | `/api/v1/executor_status/{id}` | get | 获取单个 executor_status 详情 |

### Existing_businesses

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/existing_businesses` | list | 获取 existing_businesses 列表 |
| GET | `/api/v1/existing_businesses/{id}` | get | 获取单个 existing_businesses 详情 |

### Existing_formats

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/existing_formats` | list | 获取 existing_formats 列表 |
| GET | `/api/v1/existing_formats/{id}` | get | 获取单个 existing_formats 详情 |

### Experience_graph_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/experience_graph_statistics` | list | 获取 experience_graph_statistics 列表 |
| GET | `/api/v1/experience_graph_statistics/{id}` | get | 获取单个 experience_graph_statistics 详情 |

### Export

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/export` | list | 获取 export 列表 |
| POST | `/api/v1/export` | create | 创建新的 export |
| GET | `/api/v1/export/{id}` | get | 获取单个 export 详情 |
| PUT | `/api/v1/export/{id}` | update | 完整更新 export |
| PATCH | `/api/v1/export/{id}` | partial_update | 部分更新 export |

### External_knowledge_integration

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/external_knowledge_integration` | list | 获取 external_knowledge_integration 列表 |
| GET | `/api/v1/external_knowledge_integration/{id}` | get | 获取单个 external_knowledge_integration 详情 |

### External_knowledge_summary

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/external_knowledge_summary` | list | 获取 external_knowledge_summary 列表 |
| GET | `/api/v1/external_knowledge_summary/{id}` | get | 获取单个 external_knowledge_summary 详情 |

### Extract-evidences

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/extract-evidences` | create | 创建新的 extract-evidences |
| GET | `/api/v1/extract-evidences/{id}` | get | 获取单个 extract-evidences 详情 |
| PUT | `/api/v1/extract-evidences/{id}` | update | 完整更新 extract-evidences |
| PATCH | `/api/v1/extract-evidences/{id}` | partial_update | 部分更新 extract-evidences |

### Extract-keywords

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/extract-keywords` | create | 创建新的 extract-keywords |
| GET | `/api/v1/extract-keywords/{id}` | get | 获取单个 extract-keywords 详情 |
| PUT | `/api/v1/extract-keywords/{id}` | update | 完整更新 extract-keywords |
| PATCH | `/api/v1/extract-keywords/{id}` | partial_update | 部分更新 extract-keywords |

### Fact-statements

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/fact-statements` | list | 获取 fact-statements 列表 |
| GET | `/api/v1/fact-statements/{id}` | get | 获取单个 fact-statements 详情 |

### Fact_db_session

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/fact_db_session` | list | 获取 fact_db_session 列表 |
| GET | `/api/v1/fact_db_session/{id}` | get | 获取单个 fact_db_session 详情 |

### Failure_statistics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/failure_statistics` | list | 获取 failure_statistics 列表 |
| GET | `/api/v1/failure_statistics/{id}` | get | 获取单个 failure_statistics 详情 |

### Feedback_loops

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/feedback_loops` | list | 获取 feedback_loops 列表 |
| GET | `/api/v1/feedback_loops/{id}` | get | 获取单个 feedback_loops 详情 |

### Feeding

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/feeding/{id}` | get | 获取单个 feeding 详情 |
| DELETE | `/api/v1/feeding/{id}` | delete | 删除 feeding |

### Feeding_by_type

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/feeding_by_type` | list | 获取 feeding_by_type 列表 |
| GET | `/api/v1/feeding_by_type/{id}` | get | 获取单个 feeding_by_type 详情 |

### Feeding_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/feeding_service` | list | 获取 feeding_service 列表 |
| GET | `/api/v1/feeding_service/{id}` | get | 获取单个 feeding_service 详情 |

### Feeding_sessions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/feeding_sessions` | list | 获取 feeding_sessions 列表 |
| GET | `/api/v1/feeding_sessions/{id}` | get | 获取单个 feeding_sessions 详情 |

### Feeding_summary

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/feeding_summary` | list | 获取 feeding_summary 列表 |
| GET | `/api/v1/feeding_summary/{id}` | get | 获取单个 feeding_summary 详情 |

### Feeding_trend

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/feeding_trend` | list | 获取 feeding_trend 列表 |
| GET | `/api/v1/feeding_trend/{id}` | get | 获取单个 feeding_trend 详情 |

### File

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/file/{id}` | get | 获取单个 file 详情 |
| DELETE | `/api/v1/file/{id}` | delete | 删除 file |

### File_hash

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/file_hash` | list | 获取 file_hash 列表 |
| GET | `/api/v1/file_hash/{id}` | get | 获取单个 file_hash 详情 |

### File_transcript

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/file_transcript` | list | 获取 file_transcript 列表 |
| GET | `/api/v1/file_transcript/{id}` | get | 获取单个 file_transcript 详情 |

### File_tree

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/file_tree` | list | 获取 file_tree 列表 |
| GET | `/api/v1/file_tree/{id}` | get | 获取单个 file_tree 详情 |

### Files

**原始端点数**: 3
**统一后端点数**: 5
**减少**: -2 (-66.7%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/files` | list | 获取 files 列表 |
| GET | `/api/v1/files/{id}` | get | 获取单个 files 详情 |
| PUT | `/api/v1/files/{id}` | update | 完整更新 files |
| PATCH | `/api/v1/files/{id}` | partial_update | 部分更新 files |
| DELETE | `/api/v1/files/{id}` | delete | 删除 files |

### Flag_embedding_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/flag_embedding_service` | list | 获取 flag_embedding_service 列表 |
| GET | `/api/v1/flag_embedding_service/{id}` | get | 获取单个 flag_embedding_service 详情 |

### Folder

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/folder/{id}` | get | 获取单个 folder 详情 |
| DELETE | `/api/v1/folder/{id}` | delete | 删除 folder |

### Folder-contents

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/folder-contents` | list | 获取 folder-contents 列表 |
| GET | `/api/v1/folder-contents/{id}` | get | 获取单个 folder-contents 详情 |

### Folder_contents

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/folder_contents` | list | 获取 folder_contents 列表 |
| GET | `/api/v1/folder_contents/{id}` | get | 获取单个 folder_contents 详情 |

### Folders

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/folders` | create | 创建新的 folders |
| GET | `/api/v1/folders/{id}` | get | 获取单个 folders 详情 |
| PUT | `/api/v1/folders/{id}` | update | 完整更新 folders |
| PATCH | `/api/v1/folders/{id}` | partial_update | 部分更新 folders |
| DELETE | `/api/v1/folders/{id}` | delete | 删除 folders |

### Fts_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/fts_stats` | list | 获取 fts_stats 列表 |
| GET | `/api/v1/fts_stats/{id}` | get | 获取单个 fts_stats 详情 |

### Full_lineage_graph

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/full_lineage_graph` | list | 获取 full_lineage_graph 列表 |
| GET | `/api/v1/full_lineage_graph/{id}` | get | 获取单个 full_lineage_graph 详情 |

### Full_text

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/full_text` | list | 获取 full_text 列表 |
| GET | `/api/v1/full_text/{id}` | get | 获取单个 full_text 详情 |

### Full_validation_report

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/full_validation_report` | list | 获取 full_validation_report 列表 |
| GET | `/api/v1/full_validation_report/{id}` | get | 获取单个 full_validation_report 详情 |

### Gateway_config

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/gateway_config` | list | 获取 gateway_config 列表 |
| GET | `/api/v1/gateway_config/{id}` | get | 获取单个 gateway_config 详情 |

### Gateway_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/gateway_stats` | list | 获取 gateway_stats 列表 |
| GET | `/api/v1/gateway_stats/{id}` | get | 获取单个 gateway_stats 详情 |

### Generated_skills

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/generated_skills` | list | 获取 generated_skills 列表 |
| GET | `/api/v1/generated_skills/{id}` | get | 获取单个 generated_skills 详情 |

### Governance_dashboard

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/governance_dashboard` | list | 获取 governance_dashboard 列表 |
| GET | `/api/v1/governance_dashboard/{id}` | get | 获取单个 governance_dashboard 详情 |

### Governed_hermes

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/governed_hermes` | list | 获取 governed_hermes 列表 |
| GET | `/api/v1/governed_hermes/{id}` | get | 获取单个 governed_hermes 详情 |

### Government

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/government` | create | 创建新的 government |
| GET | `/api/v1/government/{id}` | get | 获取单个 government 详情 |
| PUT | `/api/v1/government/{id}` | update | 完整更新 government |
| PATCH | `/api/v1/government/{id}` | partial_update | 部分更新 government |

### Graph_construction_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_construction_service` | list | 获取 graph_construction_service 列表 |
| GET | `/api/v1/graph_construction_service/{id}` | get | 获取单个 graph_construction_service 详情 |

### Graph_data

**原始端点数**: 4
**统一后端点数**: 2
**减少**: 2 (50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_data` | list | 获取 graph_data 列表 |
| GET | `/api/v1/graph_data/{id}` | get | 获取单个 graph_data 详情 |

### Graph_database_integration

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_database_integration` | list | 获取 graph_database_integration 列表 |
| GET | `/api/v1/graph_database_integration/{id}` | get | 获取单个 graph_database_integration 详情 |

### Graph_reasoning_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_reasoning_service` | list | 获取 graph_reasoning_service 列表 |
| GET | `/api/v1/graph_reasoning_service/{id}` | get | 获取单个 graph_reasoning_service 详情 |

### Graph_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_statistics` | list | 获取 graph_statistics 列表 |
| GET | `/api/v1/graph_statistics/{id}` | get | 获取单个 graph_statistics 详情 |

### Graph_statistics_compat

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_statistics_compat` | list | 获取 graph_statistics_compat 列表 |
| GET | `/api/v1/graph_statistics_compat/{id}` | get | 获取单个 graph_statistics_compat 详情 |

### Graph_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_stats` | list | 获取 graph_stats 列表 |
| GET | `/api/v1/graph_stats/{id}` | get | 获取单个 graph_stats 详情 |

### Graph_visualization

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_visualization` | list | 获取 graph_visualization 列表 |
| GET | `/api/v1/graph_visualization/{id}` | get | 获取单个 graph_visualization 详情 |

### Graph_visualization_data

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graph_visualization_data` | list | 获取 graph_visualization_data 列表 |
| GET | `/api/v1/graph_visualization_data/{id}` | get | 获取单个 graph_visualization_data 详情 |

### Graphiti_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graphiti_service` | list | 获取 graphiti_service 列表 |
| GET | `/api/v1/graphiti_service/{id}` | get | 获取单个 graphiti_service 详情 |

### Graphrag_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/graphrag_service` | list | 获取 graphrag_service 列表 |
| GET | `/api/v1/graphrag_service/{id}` | get | 获取单个 graphrag_service 详情 |

### Grouped_timeline

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/grouped_timeline` | list | 获取 grouped_timeline 列表 |
| GET | `/api/v1/grouped_timeline/{id}` | get | 获取单个 grouped_timeline 详情 |

### Hanlp_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/hanlp_service` | list | 获取 hanlp_service 列表 |
| GET | `/api/v1/hanlp_service/{id}` | get | 获取单个 hanlp_service 详情 |

### Health

**原始端点数**: 18
**统一后端点数**: 2
**减少**: 16 (88.9%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/health` | list | 获取 health 列表 |
| GET | `/api/v1/health/{id}` | get | 获取单个 health 详情 |

### Health_checker

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/health_checker` | list | 获取 health_checker 列表 |
| GET | `/api/v1/health_checker/{id}` | get | 获取单个 health_checker 详情 |

### Hierarchical_retriever

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/hierarchical_retriever` | list | 获取 hierarchical_retriever 列表 |
| GET | `/api/v1/hierarchical_retriever/{id}` | get | 获取单个 hierarchical_retriever 详情 |

### Hierarchy_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/hierarchy_stats` | list | 获取 hierarchy_stats 列表 |
| GET | `/api/v1/hierarchy_stats/{id}` | get | 获取单个 hierarchy_stats 详情 |

### High_priority_gaps

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/high_priority_gaps` | list | 获取 high_priority_gaps 列表 |
| GET | `/api/v1/high_priority_gaps/{id}` | get | 获取单个 high_priority_gaps 详情 |

### High_quality_skills

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/high_quality_skills` | list | 获取 high_quality_skills 列表 |
| GET | `/api/v1/high_quality_skills/{id}` | get | 获取单个 high_quality_skills 详情 |

### History

**原始端点数**: 4
**统一后端点数**: 2
**减少**: 2 (50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/history` | list | 获取 history 列表 |
| GET | `/api/v1/history/{id}` | get | 获取单个 history 详情 |

### Hot_connections

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/hot_connections` | list | 获取 hot_connections 列表 |
| GET | `/api/v1/hot_connections/{id}` | get | 获取单个 hot_connections 详情 |

### Hybrid_knowledge_graph_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/hybrid_knowledge_graph_service` | list | 获取 hybrid_knowledge_graph_service 列表 |
| GET | `/api/v1/hybrid_knowledge_graph_service/{id}` | get | 获取单个 hybrid_knowledge_graph_service 详情 |

### Hybrid_search_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/hybrid_search_service` | list | 获取 hybrid_search_service 列表 |
| GET | `/api/v1/hybrid_search_service/{id}` | get | 获取单个 hybrid_search_service 详情 |

### Impact_analysis

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/impact_analysis` | list | 获取 impact_analysis 列表 |
| GET | `/api/v1/impact_analysis/{id}` | get | 获取单个 impact_analysis 详情 |

### Improvement_tasks

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/improvement_tasks` | list | 获取 improvement_tasks 列表 |
| GET | `/api/v1/improvement_tasks/{id}` | get | 获取单个 improvement_tasks 详情 |

### Index_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/index_status` | list | 获取 index_status 列表 |
| GET | `/api/v1/index_status/{id}` | get | 获取单个 index_status 详情 |

### Industry_categories

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/industry_categories` | list | 获取 industry_categories 列表 |
| GET | `/api/v1/industry_categories/{id}` | get | 获取单个 industry_categories 详情 |

### Industry_details

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/industry_details` | list | 获取 industry_details 列表 |
| GET | `/api/v1/industry_details/{id}` | get | 获取单个 industry_details 详情 |

### Industry_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/industry_statistics` | list | 获取 industry_statistics 列表 |
| GET | `/api/v1/industry_statistics/{id}` | get | 获取单个 industry_statistics 详情 |

### Industry_trends

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/industry_trends` | list | 获取 industry_trends 列表 |
| GET | `/api/v1/industry_trends/{id}` | get | 获取单个 industry_trends 详情 |

### Info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/info` | list | 获取 info 列表 |
| GET | `/api/v1/info/{id}` | get | 获取单个 info 详情 |

### Ingestion_agent

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/ingestion_agent` | list | 获取 ingestion_agent 列表 |
| GET | `/api/v1/ingestion_agent/{id}` | get | 获取单个 ingestion_agent 详情 |

### Input_schema

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/input_schema` | list | 获取 input_schema 列表 |
| GET | `/api/v1/input_schema/{id}` | get | 获取单个 input_schema 详情 |

### Insights

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/insights` | list | 获取 insights 列表 |
| GET | `/api/v1/insights/{id}` | get | 获取单个 insights 详情 |

### Internvl_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/internvl_service` | list | 获取 internvl_service 列表 |
| GET | `/api/v1/internvl_service/{id}` | get | 获取单个 internvl_service 详情 |

### Issue-types

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/issue-types` | list | 获取 issue-types 列表 |
| GET | `/api/v1/issue-types/{id}` | get | 获取单个 issue-types 详情 |

### Issue_types

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/issue_types` | list | 获取 issue_types 列表 |
| GET | `/api/v1/issue_types/{id}` | get | 获取单个 issue_types 详情 |

### Keyword_timeline

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/keyword_timeline` | list | 获取 keyword_timeline 列表 |
| GET | `/api/v1/keyword_timeline/{id}` | get | 获取单个 keyword_timeline 详情 |

### Keywords

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/keywords` | list | 获取 keywords 列表 |
| GET | `/api/v1/keywords/{id}` | get | 获取单个 keywords 详情 |

### Kg

**原始端点数**: 3
**统一后端点数**: 5
**减少**: -2 (-66.7%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/kg` | list | 获取 kg 列表 |
| POST | `/api/v1/kg` | create | 创建新的 kg |
| GET | `/api/v1/kg/{id}` | get | 获取单个 kg 详情 |
| PUT | `/api/v1/kg/{id}` | update | 完整更新 kg |
| PATCH | `/api/v1/kg/{id}` | partial_update | 部分更新 kg |

### Kg_builder

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/kg_builder` | list | 获取 kg_builder 列表 |
| GET | `/api/v1/kg_builder/{id}` | get | 获取单个 kg_builder 详情 |

### Khoj_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/khoj_service` | list | 获取 khoj_service 列表 |
| GET | `/api/v1/khoj_service/{id}` | get | 获取单个 khoj_service 详情 |

### Knowledge-base

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge-base` | list | 获取 knowledge-base 列表 |
| GET | `/api/v1/knowledge-base/{id}` | get | 获取单个 knowledge-base 详情 |

### Knowledge-graph

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/knowledge-graph` | create | 创建新的 knowledge-graph |
| GET | `/api/v1/knowledge-graph/{id}` | get | 获取单个 knowledge-graph 详情 |
| PUT | `/api/v1/knowledge-graph/{id}` | update | 完整更新 knowledge-graph |
| PATCH | `/api/v1/knowledge-graph/{id}` | partial_update | 部分更新 knowledge-graph |

### Knowledge_base_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge_base_status` | list | 获取 knowledge_base_status 列表 |
| GET | `/api/v1/knowledge_base_status/{id}` | get | 获取单个 knowledge_base_status 详情 |

### Knowledge_graph

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge_graph` | list | 获取 knowledge_graph 列表 |
| GET | `/api/v1/knowledge_graph/{id}` | get | 获取单个 knowledge_graph 详情 |

### Knowledge_graph_builder

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge_graph_builder` | list | 获取 knowledge_graph_builder 列表 |
| GET | `/api/v1/knowledge_graph_builder/{id}` | get | 获取单个 knowledge_graph_builder 详情 |

### Knowledge_graph_cached

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge_graph_cached` | list | 获取 knowledge_graph_cached 列表 |
| GET | `/api/v1/knowledge_graph_cached/{id}` | get | 获取单个 knowledge_graph_cached 详情 |

### Knowledge_graph_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge_graph_service` | list | 获取 knowledge_graph_service 列表 |
| GET | `/api/v1/knowledge_graph_service/{id}` | get | 获取单个 knowledge_graph_service 详情 |

### Knowledge_graph_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge_graph_stats` | list | 获取 knowledge_graph_stats 列表 |
| GET | `/api/v1/knowledge_graph_stats/{id}` | get | 获取单个 knowledge_graph_stats 详情 |

### Knowledge_network

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/knowledge_network` | list | 获取 knowledge_network 列表 |
| GET | `/api/v1/knowledge_network/{id}` | get | 获取单个 knowledge_network 详情 |

### Lance_store

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/lance_store` | list | 获取 lance_store 列表 |
| GET | `/api/v1/lance_store/{id}` | get | 获取单个 lance_store 详情 |

### Latest_snapshots

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/latest_snapshots` | list | 获取 latest_snapshots 列表 |
| GET | `/api/v1/latest_snapshots/{id}` | get | 获取单个 latest_snapshots 详情 |

### Latest_version

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/latest_version` | list | 获取 latest_version 列表 |
| GET | `/api/v1/latest_version/{id}` | get | 获取单个 latest_version 详情 |

### Learning

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning/{id}` | get | 获取单个 learning 详情 |
| DELETE | `/api/v1/learning/{id}` | delete | 删除 learning |

### Learning_engine

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_engine` | list | 获取 learning_engine 列表 |
| GET | `/api/v1/learning_engine/{id}` | get | 获取单个 learning_engine 详情 |

### Learning_insights

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_insights` | list | 获取 learning_insights 列表 |
| GET | `/api/v1/learning_insights/{id}` | get | 获取单个 learning_insights 详情 |

### Learning_logs

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_logs` | list | 获取 learning_logs 列表 |
| GET | `/api/v1/learning_logs/{id}` | get | 获取单个 learning_logs 详情 |

### Learning_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_service` | list | 获取 learning_service 列表 |
| GET | `/api/v1/learning_service/{id}` | get | 获取单个 learning_service 详情 |

### Learning_stats

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_stats` | list | 获取 learning_stats 列表 |
| GET | `/api/v1/learning_stats/{id}` | get | 获取单个 learning_stats 详情 |

### Learning_summary

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_summary` | list | 获取 learning_summary 列表 |
| GET | `/api/v1/learning_summary/{id}` | get | 获取单个 learning_summary 详情 |

### Learning_tasks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_tasks` | list | 获取 learning_tasks 列表 |
| GET | `/api/v1/learning_tasks/{id}` | get | 获取单个 learning_tasks 详情 |

### Learning_trend

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/learning_trend` | list | 获取 learning_trend 列表 |
| GET | `/api/v1/learning_trend/{id}` | get | 获取单个 learning_trend 详情 |

### Lightrag_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/lightrag_service` | list | 获取 lightrag_service 列表 |
| GET | `/api/v1/lightrag_service/{id}` | get | 获取单个 lightrag_service 详情 |

### Lineage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/lineage` | list | 获取 lineage 列表 |
| GET | `/api/v1/lineage/{id}` | get | 获取单个 lineage 详情 |

### Lineage_graph

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/lineage_graph` | list | 获取 lineage_graph 列表 |
| GET | `/api/v1/lineage_graph/{id}` | get | 获取单个 lineage_graph 详情 |

### Lineage_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/lineage_service` | list | 获取 lineage_service 列表 |
| GET | `/api/v1/lineage_service/{id}` | get | 获取单个 lineage_service 详情 |

### List

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/list` | list | 获取 list 列表 |
| GET | `/api/v1/list/{id}` | get | 获取单个 list 详情 |

### Llm_extractor

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/llm_extractor` | list | 获取 llm_extractor 列表 |
| GET | `/api/v1/llm_extractor/{id}` | get | 获取单个 llm_extractor 详情 |

### Loaded_plugin

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/loaded_plugin` | list | 获取 loaded_plugin 列表 |
| GET | `/api/v1/loaded_plugin/{id}` | get | 获取单个 loaded_plugin 详情 |

### Logger

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/logger` | list | 获取 logger 列表 |
| GET | `/api/v1/logger/{id}` | get | 获取单个 logger 详情 |

### Logout

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/logout` | create | 创建新的 logout |
| GET | `/api/v1/logout/{id}` | get | 获取单个 logout 详情 |
| PUT | `/api/v1/logout/{id}` | update | 完整更新 logout |
| PATCH | `/api/v1/logout/{id}` | partial_update | 部分更新 logout |

### Logs

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/logs` | list | 获取 logs 列表 |
| GET | `/api/v1/logs/{id}` | get | 获取单个 logs 详情 |

### Loop_manager

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/loop_manager` | list | 获取 loop_manager 列表 |
| GET | `/api/v1/loop_manager/{id}` | get | 获取单个 loop_manager 详情 |

### Loop_metrics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/loop_metrics` | list | 获取 loop_metrics 列表 |
| GET | `/api/v1/loop_metrics/{id}` | get | 获取单个 loop_metrics 详情 |

### Matrix

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/matrix` | list | 获取 matrix 列表 |
| GET | `/api/v1/matrix/{id}` | get | 获取单个 matrix 详情 |

### Memory

**原始端点数**: 6
**统一后端点数**: 6
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/memory` | list | 获取 memory 列表 |
| POST | `/api/v1/memory` | create | 创建新的 memory |
| GET | `/api/v1/memory/{id}` | get | 获取单个 memory 详情 |
| PUT | `/api/v1/memory/{id}` | update | 完整更新 memory |
| PATCH | `/api/v1/memory/{id}` | partial_update | 部分更新 memory |
| DELETE | `/api/v1/memory/{id}` | delete | 删除 memory |

### Memory_aggregator

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/memory_aggregator` | list | 获取 memory_aggregator 列表 |
| GET | `/api/v1/memory_aggregator/{id}` | get | 获取单个 memory_aggregator 详情 |

### Memory_detail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/memory_detail` | list | 获取 memory_detail 列表 |
| GET | `/api/v1/memory_detail/{id}` | get | 获取单个 memory_detail 详情 |

### Memory_injector

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/memory_injector` | list | 获取 memory_injector 列表 |
| GET | `/api/v1/memory_injector/{id}` | get | 获取单个 memory_injector 详情 |

### Memory_statistics

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/memory_statistics` | list | 获取 memory_statistics 列表 |
| GET | `/api/v1/memory_statistics/{id}` | get | 获取单个 memory_statistics 详情 |

### Memory_stats

**原始端点数**: 4
**统一后端点数**: 2
**减少**: 2 (50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/memory_stats` | list | 获取 memory_stats 列表 |
| GET | `/api/v1/memory_stats/{id}` | get | 获取单个 memory_stats 详情 |

### Memory_usage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/memory_usage` | list | 获取 memory_usage 列表 |
| GET | `/api/v1/memory_usage/{id}` | get | 获取单个 memory_usage 详情 |

### Metadata

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metadata` | list | 获取 metadata 列表 |
| GET | `/api/v1/metadata/{id}` | get | 获取单个 metadata 详情 |

### Metadata-stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metadata-stats` | list | 获取 metadata-stats 列表 |
| GET | `/api/v1/metadata-stats/{id}` | get | 获取单个 metadata-stats 详情 |

### Metadata_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metadata_stats` | list | 获取 metadata_stats 列表 |
| GET | `/api/v1/metadata_stats/{id}` | get | 获取单个 metadata_stats 详情 |

### Metric_trend

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metric_trend` | list | 获取 metric_trend 列表 |
| GET | `/api/v1/metric_trend/{id}` | get | 获取单个 metric_trend 详情 |

### Metrics

**原始端点数**: 9
**统一后端点数**: 5
**减少**: 4 (44.4%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metrics` | list | 获取 metrics 列表 |
| POST | `/api/v1/metrics` | create | 创建新的 metrics |
| GET | `/api/v1/metrics/{id}` | get | 获取单个 metrics 详情 |
| PUT | `/api/v1/metrics/{id}` | update | 完整更新 metrics |
| PATCH | `/api/v1/metrics/{id}` | partial_update | 部分更新 metrics |

### Metrics_app

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metrics_app` | list | 获取 metrics_app 列表 |
| GET | `/api/v1/metrics_app/{id}` | get | 获取单个 metrics_app 详情 |

### Metrics_events

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metrics_events` | list | 获取 metrics_events 列表 |
| GET | `/api/v1/metrics_events/{id}` | get | 获取单个 metrics_events 详情 |

### Metrics_handler

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metrics_handler` | list | 获取 metrics_handler 列表 |
| GET | `/api/v1/metrics_handler/{id}` | get | 获取单个 metrics_handler 详情 |

### Metrics_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metrics_service` | list | 获取 metrics_service 列表 |
| GET | `/api/v1/metrics_service/{id}` | get | 获取单个 metrics_service 详情 |

### Metrics_snapshots

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/metrics_snapshots` | list | 获取 metrics_snapshots 列表 |
| GET | `/api/v1/metrics_snapshots/{id}` | get | 获取单个 metrics_snapshots 详情 |

### Mime_type

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/mime_type` | list | 获取 mime_type 列表 |
| GET | `/api/v1/mime_type/{id}` | get | 获取单个 mime_type 详情 |

### Missing_agents

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/missing_agents` | list | 获取 missing_agents 列表 |
| GET | `/api/v1/missing_agents/{id}` | get | 获取单个 missing_agents 详情 |

### Most_valuable_feedings

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/most_valuable_feedings` | list | 获取 most_valuable_feedings 列表 |
| GET | `/api/v1/most_valuable_feedings/{id}` | get | 获取单个 most_valuable_feedings 详情 |

### My_permissions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/my_permissions` | list | 获取 my_permissions 列表 |
| GET | `/api/v1/my_permissions/{id}` | get | 获取单个 my_permissions 详情 |

### Neighbors

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/neighbors` | list | 获取 neighbors 列表 |
| GET | `/api/v1/neighbors/{id}` | get | 获取单个 neighbors 详情 |

### Networkx

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/networkx` | create | 创建新的 networkx |
| GET | `/api/v1/networkx/{id}` | get | 获取单个 networkx 详情 |
| PUT | `/api/v1/networkx/{id}` | update | 完整更新 networkx |
| PATCH | `/api/v1/networkx/{id}` | partial_update | 部分更新 networkx |

### News

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/news` | create | 创建新的 news |
| GET | `/api/v1/news/{id}` | get | 获取单个 news 详情 |
| PUT | `/api/v1/news/{id}` | update | 完整更新 news |
| PATCH | `/api/v1/news/{id}` | partial_update | 部分更新 news |

### Nlp

**原始端点数**: 5
**统一后端点数**: 4
**减少**: 1 (20.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/nlp` | create | 创建新的 nlp |
| GET | `/api/v1/nlp/{id}` | get | 获取单个 nlp 详情 |
| PUT | `/api/v1/nlp/{id}` | update | 完整更新 nlp |
| PATCH | `/api/v1/nlp/{id}` | partial_update | 部分更新 nlp |

### Node_detail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/node_detail` | list | 获取 node_detail 列表 |
| GET | `/api/v1/node_detail/{id}` | get | 获取单个 node_detail 详情 |

### Node_details

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/node_details` | list | 获取 node_details 列表 |
| GET | `/api/v1/node_details/{id}` | get | 获取单个 node_details 详情 |

### Node_neighborhood

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/node_neighborhood` | list | 获取 node_neighborhood 列表 |
| GET | `/api/v1/node_neighborhood/{id}` | get | 获取单个 node_neighborhood 详情 |

### Object_full_data

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/object_full_data` | list | 获取 object_full_data 列表 |
| GET | `/api/v1/object_full_data/{id}` | get | 获取单个 object_full_data 详情 |

### Object_lineage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/object_lineage` | list | 获取 object_lineage 列表 |
| GET | `/api/v1/object_lineage/{id}` | get | 获取单个 object_lineage 详情 |

### Object_relations

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/object_relations` | list | 获取 object_relations 列表 |
| GET | `/api/v1/object_relations/{id}` | get | 获取单个 object_relations 详情 |

### Objects

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/objects` | list | 获取 objects 列表 |
| GET | `/api/v1/objects/{id}` | get | 获取单个 objects 详情 |

### Ocr_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/ocr_service` | list | 获取 ocr_service 列表 |
| GET | `/api/v1/ocr_service/{id}` | get | 获取单个 ocr_service 详情 |

### Ocr_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/ocr_statistics` | list | 获取 ocr_statistics 列表 |
| GET | `/api/v1/ocr_statistics/{id}` | get | 获取单个 ocr_statistics 详情 |

### Old_conversations

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/old_conversations/{id}` | get | 获取单个 old_conversations 详情 |
| DELETE | `/api/v1/old_conversations/{id}` | delete | 删除 old_conversations |

### Oldest_entries

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/oldest_entries` | list | 获取 oldest_entries 列表 |
| GET | `/api/v1/oldest_entries/{id}` | get | 获取单个 oldest_entries 详情 |

### Optimizations

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/optimizations` | list | 获取 optimizations 列表 |
| GET | `/api/v1/optimizations/{id}` | get | 获取单个 optimizations 详情 |

### Optimized_pipeline

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/optimized_pipeline` | list | 获取 optimized_pipeline 列表 |
| GET | `/api/v1/optimized_pipeline/{id}` | get | 获取单个 optimized_pipeline 详情 |

### Optimizer

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/optimizer` | list | 获取 optimizer 列表 |
| GET | `/api/v1/optimizer/{id}` | get | 获取单个 optimizer 详情 |

### Or_compute

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/or_compute` | list | 获取 or_compute 列表 |
| GET | `/api/v1/or_compute/{id}` | get | 获取单个 or_compute 详情 |

### Or_create_brain

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/or_create_brain` | list | 获取 or_create_brain 列表 |
| GET | `/api/v1/or_create_brain/{id}` | get | 获取单个 or_create_brain 详情 |

### Output_schema

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/output_schema` | list | 获取 output_schema 列表 |
| GET | `/api/v1/output_schema/{id}` | get | 获取单个 output_schema 详情 |

### Overview

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/overview` | list | 获取 overview 列表 |
| GET | `/api/v1/overview/{id}` | get | 获取单个 overview 详情 |

### Packet

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/packet` | list | 获取 packet 列表 |
| GET | `/api/v1/packet/{id}` | get | 获取单个 packet 详情 |

### Packet_lineage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/packet_lineage` | list | 获取 packet_lineage 列表 |
| GET | `/api/v1/packet_lineage/{id}` | get | 获取单个 packet_lineage 详情 |

### Packet_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/packet_status` | list | 获取 packet_status 列表 |
| GET | `/api/v1/packet_status/{id}` | get | 获取单个 packet_status 详情 |

### Packet_versions

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/packet_versions` | list | 获取 packet_versions 列表 |
| GET | `/api/v1/packet_versions/{id}` | get | 获取单个 packet_versions 详情 |

### Paddlenlp_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/paddlenlp_service` | list | 获取 paddlenlp_service 列表 |
| GET | `/api/v1/paddlenlp_service/{id}` | get | 获取单个 paddlenlp_service 详情 |

### Page_count

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/page_count` | list | 获取 page_count 列表 |
| GET | `/api/v1/page_count/{id}` | get | 获取单个 page_count 详情 |

### Parallel_processor

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/parallel_processor` | list | 获取 parallel_processor 列表 |
| GET | `/api/v1/parallel_processor/{id}` | get | 获取单个 parallel_processor 详情 |

### Parent_chain

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/parent_chain` | list | 获取 parent_chain 列表 |
| GET | `/api/v1/parent_chain/{id}` | get | 获取单个 parent_chain 详情 |

### Parser

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/parser` | list | 获取 parser 列表 |
| GET | `/api/v1/parser/{id}` | get | 获取单个 parser 详情 |

### Partial_agents

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/partial_agents` | list | 获取 partial_agents 列表 |
| GET | `/api/v1/partial_agents/{id}` | get | 获取单个 partial_agents 详情 |

### Password_hash

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/password_hash` | list | 获取 password_hash 列表 |
| GET | `/api/v1/password_hash/{id}` | get | 获取单个 password_hash 详情 |

### Pattern

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/pattern/{id}` | get | 获取单个 pattern 详情 |
| DELETE | `/api/v1/pattern/{id}` | delete | 删除 pattern |

### Pattern_detector

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/pattern_detector` | list | 获取 pattern_detector 列表 |
| GET | `/api/v1/pattern_detector/{id}` | get | 获取单个 pattern_detector 详情 |

### Patterns

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/patterns` | list | 获取 patterns 列表 |
| GET | `/api/v1/patterns/{id}` | get | 获取单个 patterns 详情 |

### Pending_migrations

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/pending_migrations` | list | 获取 pending_migrations 列表 |
| GET | `/api/v1/pending_migrations/{id}` | get | 获取单个 pending_migrations 详情 |

### Performance_metrics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/performance_metrics` | list | 获取 performance_metrics 列表 |
| GET | `/api/v1/performance_metrics/{id}` | get | 获取单个 performance_metrics 详情 |

### Performance_summary

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/performance_summary` | list | 获取 performance_summary 列表 |
| GET | `/api/v1/performance_summary/{id}` | get | 获取单个 performance_summary 详情 |

### Permission_matrix

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/permission_matrix` | list | 获取 permission_matrix 列表 |
| GET | `/api/v1/permission_matrix/{id}` | get | 获取单个 permission_matrix 详情 |

### Permission_service

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/permission_service` | list | 获取 permission_service 列表 |
| GET | `/api/v1/permission_service/{id}` | get | 获取单个 permission_service 详情 |

### Personalized_suggestions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/personalized_suggestions` | list | 获取 personalized_suggestions 列表 |
| GET | `/api/v1/personalized_suggestions/{id}` | get | 获取单个 personalized_suggestions 详情 |

### Photo

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/photo/{id}` | get | 获取单个 photo 详情 |
| DELETE | `/api/v1/photo/{id}` | delete | 删除 photo |

### Photo_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/photo_stats` | list | 获取 photo_stats 列表 |
| GET | `/api/v1/photo_stats/{id}` | get | 获取单个 photo_stats 详情 |

### Photos

**原始端点数**: 7
**统一后端点数**: 6
**减少**: 1 (14.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/photos` | list | 获取 photos 列表 |
| POST | `/api/v1/photos` | create | 创建新的 photos |
| GET | `/api/v1/photos/{id}` | get | 获取单个 photos 详情 |
| PUT | `/api/v1/photos/{id}` | update | 完整更新 photos |
| PATCH | `/api/v1/photos/{id}` | partial_update | 部分更新 photos |
| DELETE | `/api/v1/photos/{id}` | delete | 删除 photos |

### Pipeline_status

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/pipeline_status` | list | 获取 pipeline_status 列表 |
| GET | `/api/v1/pipeline_status/{id}` | get | 获取单个 pipeline_status 详情 |

### Plotly

**原始端点数**: 3
**统一后端点数**: 4
**减少**: -1 (-33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/plotly` | create | 创建新的 plotly |
| GET | `/api/v1/plotly/{id}` | get | 获取单个 plotly 详情 |
| PUT | `/api/v1/plotly/{id}` | update | 完整更新 plotly |
| PATCH | `/api/v1/plotly/{id}` | partial_update | 部分更新 plotly |

### Plugin

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin` | list | 获取 plugin 列表 |
| GET | `/api/v1/plugin/{id}` | get | 获取单个 plugin 详情 |

### Plugin_by_capability

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_by_capability` | list | 获取 plugin_by_capability 列表 |
| GET | `/api/v1/plugin_by_capability/{id}` | get | 获取单个 plugin_by_capability 详情 |

### Plugin_by_extension

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_by_extension` | list | 获取 plugin_by_extension 列表 |
| GET | `/api/v1/plugin_by_extension/{id}` | get | 获取单个 plugin_by_extension 详情 |

### Plugin_by_file

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_by_file` | list | 获取 plugin_by_file 列表 |
| GET | `/api/v1/plugin_by_file/{id}` | get | 获取单个 plugin_by_file 详情 |

### Plugin_for_capability

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_for_capability` | list | 获取 plugin_for_capability 列表 |
| GET | `/api/v1/plugin_for_capability/{id}` | get | 获取单个 plugin_for_capability 详情 |

### Plugin_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_info` | list | 获取 plugin_info 列表 |
| GET | `/api/v1/plugin_info/{id}` | get | 获取单个 plugin_info 详情 |

### Plugin_loader

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_loader` | list | 获取 plugin_loader 列表 |
| GET | `/api/v1/plugin_loader/{id}` | get | 获取单个 plugin_loader 详情 |

### Plugin_manager

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_manager` | list | 获取 plugin_manager 列表 |
| GET | `/api/v1/plugin_manager/{id}` | get | 获取单个 plugin_manager 详情 |

### Plugin_registry

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_registry` | list | 获取 plugin_registry 列表 |
| GET | `/api/v1/plugin_registry/{id}` | get | 获取单个 plugin_registry 详情 |

### Plugin_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugin_status` | list | 获取 plugin_status 列表 |
| GET | `/api/v1/plugin_status/{id}` | get | 获取单个 plugin_status 详情 |

### Plugins_by_capability

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugins_by_capability` | list | 获取 plugins_by_capability 列表 |
| GET | `/api/v1/plugins_by_capability/{id}` | get | 获取单个 plugins_by_capability 详情 |

### Plugins_by_type

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/plugins_by_type` | list | 获取 plugins_by_type 列表 |
| GET | `/api/v1/plugins_by_type/{id}` | get | 获取单个 plugins_by_type 详情 |

### Popular_skills

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/popular_skills` | list | 获取 popular_skills 列表 |
| GET | `/api/v1/popular_skills/{id}` | get | 获取单个 popular_skills 详情 |

### Potential_businesses

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/potential_businesses` | list | 获取 potential_businesses 列表 |
| GET | `/api/v1/potential_businesses/{id}` | get | 获取单个 potential_businesses 详情 |

### Presigned_url

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/presigned_url` | list | 获取 presigned_url 列表 |
| GET | `/api/v1/presigned_url/{id}` | get | 获取单个 presigned_url 详情 |

### Process

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/process` | create | 创建新的 process |
| GET | `/api/v1/process/{id}` | get | 获取单个 process 详情 |
| PUT | `/api/v1/process/{id}` | update | 完整更新 process |
| PATCH | `/api/v1/process/{id}` | partial_update | 部分更新 process |

### Process-audio

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/process-audio` | create | 创建新的 process-audio |
| GET | `/api/v1/process-audio/{id}` | get | 获取单个 process-audio 详情 |
| PUT | `/api/v1/process-audio/{id}` | update | 完整更新 process-audio |
| PATCH | `/api/v1/process-audio/{id}` | partial_update | 部分更新 process-audio |

### Process-project

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/process-project` | create | 创建新的 process-project |
| GET | `/api/v1/process-project/{id}` | get | 获取单个 process-project 详情 |
| PUT | `/api/v1/process-project/{id}` | update | 完整更新 process-project |
| PATCH | `/api/v1/process-project/{id}` | partial_update | 部分更新 process-project |

### Process_chunks

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/process_chunks` | create | 创建新的 process_chunks |
| GET | `/api/v1/process_chunks/{id}` | get | 获取单个 process_chunks 详情 |
| PUT | `/api/v1/process_chunks/{id}` | update | 完整更新 process_chunks |
| PATCH | `/api/v1/process_chunks/{id}` | partial_update | 部分更新 process_chunks |

### Processing_status

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/processing_status` | list | 获取 processing_status 列表 |
| GET | `/api/v1/processing_status/{id}` | get | 获取单个 processing_status 详情 |

### Progress

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/progress` | list | 获取 progress 列表 |
| GET | `/api/v1/progress/{id}` | get | 获取单个 progress 详情 |

### Project

**原始端点数**: 9
**统一后端点数**: 5
**减少**: 4 (44.4%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project` | list | 获取 project 列表 |
| GET | `/api/v1/project/{id}` | get | 获取单个 project 详情 |
| PUT | `/api/v1/project/{id}` | update | 完整更新 project |
| PATCH | `/api/v1/project/{id}` | partial_update | 部分更新 project |
| DELETE | `/api/v1/project/{id}` | delete | 删除 project |

### Project_chunks_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_chunks_statistics` | list | 获取 project_chunks_statistics 列表 |
| GET | `/api/v1/project_chunks_statistics/{id}` | get | 获取单个 project_chunks_statistics 详情 |

### Project_clusters

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_clusters` | list | 获取 project_clusters 列表 |
| GET | `/api/v1/project_clusters/{id}` | get | 获取单个 project_clusters 详情 |

### Project_context

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_context` | list | 获取 project_context 列表 |
| GET | `/api/v1/project_context/{id}` | get | 获取单个 project_context 详情 |

### Project_contexts_compat

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_contexts_compat` | list | 获取 project_contexts_compat 列表 |
| GET | `/api/v1/project_contexts_compat/{id}` | get | 获取单个 project_contexts_compat 详情 |

### Project_dashboard

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_dashboard` | list | 获取 project_dashboard 列表 |
| GET | `/api/v1/project_dashboard/{id}` | get | 获取单个 project_dashboard 详情 |

### Project_data_gaps

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_data_gaps` | list | 获取 project_data_gaps 列表 |
| GET | `/api/v1/project_data_gaps/{id}` | get | 获取单个 project_data_gaps 详情 |

### Project_discovery_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_discovery_summary` | list | 获取 project_discovery_summary 列表 |
| GET | `/api/v1/project_discovery_summary/{id}` | get | 获取单个 project_discovery_summary 详情 |

### Project_document

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_document` | list | 获取 project_document 列表 |
| GET | `/api/v1/project_document/{id}` | get | 获取单个 project_document 详情 |

### Project_documents

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_documents` | list | 获取 project_documents 列表 |
| GET | `/api/v1/project_documents/{id}` | get | 获取单个 project_documents 详情 |

### Project_documents_compat

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_documents_compat` | list | 获取 project_documents_compat 列表 |
| GET | `/api/v1/project_documents_compat/{id}` | get | 获取单个 project_documents_compat 详情 |

### Project_keywords

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_keywords` | list | 获取 project_keywords 列表 |
| GET | `/api/v1/project_keywords/{id}` | get | 获取单个 project_keywords 详情 |

### Project_knowledge_graph

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_knowledge_graph` | list | 获取 project_knowledge_graph 列表 |
| GET | `/api/v1/project_knowledge_graph/{id}` | get | 获取单个 project_knowledge_graph 详情 |

### Project_lineage_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_lineage_stats` | list | 获取 project_lineage_stats 列表 |
| GET | `/api/v1/project_lineage_stats/{id}` | get | 获取单个 project_lineage_stats 详情 |

### Project_list

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_list` | list | 获取 project_list 列表 |
| GET | `/api/v1/project_list/{id}` | get | 获取单个 project_list 详情 |

### Project_members

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_members` | list | 获取 project_members 列表 |
| GET | `/api/v1/project_members/{id}` | get | 获取单个 project_members 详情 |

### Project_memories

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_memories` | list | 获取 project_memories 列表 |
| GET | `/api/v1/project_memories/{id}` | get | 获取单个 project_memories 详情 |
| DELETE | `/api/v1/project_memories/{id}` | delete | 删除 project_memories |

### Project_merged

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_merged` | list | 获取 project_merged 列表 |
| GET | `/api/v1/project_merged/{id}` | get | 获取单个 project_merged 详情 |

### Project_metrics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_metrics` | list | 获取 project_metrics 列表 |
| GET | `/api/v1/project_metrics/{id}` | get | 获取单个 project_metrics 详情 |

### Project_packets

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_packets` | list | 获取 project_packets 列表 |
| GET | `/api/v1/project_packets/{id}` | get | 获取单个 project_packets 详情 |

### Project_progress

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_progress` | list | 获取 project_progress 列表 |
| GET | `/api/v1/project_progress/{id}` | get | 获取单个 project_progress 详情 |

### Project_quality_overview

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_quality_overview` | list | 获取 project_quality_overview 列表 |
| GET | `/api/v1/project_quality_overview/{id}` | get | 获取单个 project_quality_overview 详情 |

### Project_skill_settings

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_skill_settings` | list | 获取 project_skill_settings 列表 |
| GET | `/api/v1/project_skill_settings/{id}` | get | 获取单个 project_skill_settings 详情 |

### Project_skills_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_skills_statistics` | list | 获取 project_skills_statistics 列表 |
| GET | `/api/v1/project_skills_statistics/{id}` | get | 获取单个 project_skills_statistics 详情 |

### Project_source_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_source_statistics` | list | 获取 project_source_statistics 列表 |
| GET | `/api/v1/project_source_statistics/{id}` | get | 获取单个 project_source_statistics 详情 |

### Project_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_stats` | list | 获取 project_stats 列表 |
| GET | `/api/v1/project_stats/{id}` | get | 获取单个 project_stats 详情 |

### Project_stats_compat

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_stats_compat` | list | 获取 project_stats_compat 列表 |
| GET | `/api/v1/project_stats_compat/{id}` | get | 获取单个 project_stats_compat 详情 |

### Project_status

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_status` | list | 获取 project_status 列表 |
| GET | `/api/v1/project_status/{id}` | get | 获取单个 project_status 详情 |

### Project_timeline

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_timeline` | list | 获取 project_timeline 列表 |
| GET | `/api/v1/project_timeline/{id}` | get | 获取单个 project_timeline 详情 |

### Project_top_keywords

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/project_top_keywords` | list | 获取 project_top_keywords 列表 |
| GET | `/api/v1/project_top_keywords/{id}` | get | 获取单个 project_top_keywords 详情 |

### Projects

**原始端点数**: 59
**统一后端点数**: 6
**减少**: 53 (89.8%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/projects` | list | 获取 projects 列表 |
| POST | `/api/v1/projects` | create | 创建新的 projects |
| GET | `/api/v1/projects/{id}` | get | 获取单个 projects 详情 |
| PUT | `/api/v1/projects/{id}` | update | 完整更新 projects |
| PATCH | `/api/v1/projects/{id}` | partial_update | 部分更新 projects |
| DELETE | `/api/v1/projects/{id}` | delete | 删除 projects |

### Promote

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/promote` | create | 创建新的 promote |
| GET | `/api/v1/promote/{id}` | get | 获取单个 promote 详情 |
| PUT | `/api/v1/promote/{id}` | update | 完整更新 promote |
| PATCH | `/api/v1/promote/{id}` | partial_update | 部分更新 promote |

### Proposal_templates

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/proposal_templates` | list | 获取 proposal_templates 列表 |
| GET | `/api/v1/proposal_templates/{id}` | get | 获取单个 proposal_templates 详情 |

### Protected

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/protected` | list | 获取 protected 列表 |
| GET | `/api/v1/protected/{id}` | get | 获取单个 protected 详情 |

### Provider_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/provider_info` | list | 获取 provider_info 列表 |
| GET | `/api/v1/provider_info/{id}` | get | 获取单个 provider_info 详情 |

### Provider_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/provider_status` | list | 获取 provider_status 列表 |
| GET | `/api/v1/provider_status/{id}` | get | 获取单个 provider_status 详情 |

### Pyecharts

**原始端点数**: 2
**统一后端点数**: 4
**减少**: -2 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/pyecharts` | create | 创建新的 pyecharts |
| GET | `/api/v1/pyecharts/{id}` | get | 获取单个 pyecharts 详情 |
| PUT | `/api/v1/pyecharts/{id}` | update | 完整更新 pyecharts |
| PATCH | `/api/v1/pyecharts/{id}` | partial_update | 部分更新 pyecharts |

### Quality-check

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/quality-check` | create | 创建新的 quality-check |
| GET | `/api/v1/quality-check/{id}` | get | 获取单个 quality-check 详情 |
| PUT | `/api/v1/quality-check/{id}` | update | 完整更新 quality-check |
| PATCH | `/api/v1/quality-check/{id}` | partial_update | 部分更新 quality-check |

### Quality-levels

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quality-levels` | list | 获取 quality-levels 列表 |
| GET | `/api/v1/quality-levels/{id}` | get | 获取单个 quality-levels 详情 |

### Quality_control_agent

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quality_control_agent` | list | 获取 quality_control_agent 列表 |
| GET | `/api/v1/quality_control_agent/{id}` | get | 获取单个 quality_control_agent 详情 |

### Quality_dashboard

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quality_dashboard` | list | 获取 quality_dashboard 列表 |
| GET | `/api/v1/quality_dashboard/{id}` | get | 获取单个 quality_dashboard 详情 |

### Quality_feedback

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quality_feedback` | list | 获取 quality_feedback 列表 |
| GET | `/api/v1/quality_feedback/{id}` | get | 获取单个 quality_feedback 详情 |

### Quality_levels

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quality_levels` | list | 获取 quality_levels 列表 |
| GET | `/api/v1/quality_levels/{id}` | get | 获取单个 quality_levels 详情 |

### Quality_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quality_statistics` | list | 获取 quality_statistics 列表 |
| GET | `/api/v1/quality_statistics/{id}` | get | 获取单个 quality_statistics 详情 |

### Quantification_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quantification_stats` | list | 获取 quantification_stats 列表 |
| GET | `/api/v1/quantification_stats/{id}` | get | 获取单个 quantification_stats 详情 |

### Query

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/query` | create | 创建新的 query |
| GET | `/api/v1/query/{id}` | get | 获取单个 query 详情 |
| PUT | `/api/v1/query/{id}` | update | 完整更新 query |
| PATCH | `/api/v1/query/{id}` | partial_update | 部分更新 query |

### Query_types

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/query_types` | list | 获取 query_types 列表 |
| GET | `/api/v1/query_types/{id}` | get | 获取单个 query_types 详情 |

### Queue_length

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/queue_length` | list | 获取 queue_length 列表 |
| GET | `/api/v1/queue_length/{id}` | get | 获取单个 queue_length 详情 |

### Quick

**原始端点数**: 5
**统一后端点数**: 4
**减少**: 1 (20.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/quick` | create | 创建新的 quick |
| GET | `/api/v1/quick/{id}` | get | 获取单个 quick 详情 |
| PUT | `/api/v1/quick/{id}` | update | 完整更新 quick |
| PATCH | `/api/v1/quick/{id}` | partial_update | 部分更新 quick |

### Quick-stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quick-stats` | list | 获取 quick-stats 列表 |
| GET | `/api/v1/quick-stats/{id}` | get | 获取单个 quick-stats 详情 |

### Quick_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quick_stats` | list | 获取 quick_stats 列表 |
| GET | `/api/v1/quick_stats/{id}` | get | 获取单个 quick_stats 详情 |

### Quivr_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/quivr_service` | list | 获取 quivr_service 列表 |
| GET | `/api/v1/quivr_service/{id}` | get | 获取单个 quivr_service 详情 |

### Rag

**原始端点数**: 2
**统一后端点数**: 4
**减少**: -2 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/rag` | create | 创建新的 rag |
| GET | `/api/v1/rag/{id}` | get | 获取单个 rag 详情 |
| PUT | `/api/v1/rag/{id}` | update | 完整更新 rag |
| PATCH | `/api/v1/rag/{id}` | partial_update | 部分更新 rag |

### Rag_router

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/rag_router` | list | 获取 rag_router 列表 |
| GET | `/api/v1/rag_router/{id}` | get | 获取单个 rag_router 详情 |

### Rag_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/rag_service` | list | 获取 rag_service 列表 |
| GET | `/api/v1/rag_service/{id}` | get | 获取单个 rag_service 详情 |

### Rank-fuse

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/rank-fuse` | create | 创建新的 rank-fuse |
| GET | `/api/v1/rank-fuse/{id}` | get | 获取单个 rank-fuse 详情 |
| PUT | `/api/v1/rank-fuse/{id}` | update | 完整更新 rank-fuse |
| PATCH | `/api/v1/rank-fuse/{id}` | partial_update | 部分更新 rank-fuse |

### Ready_tasks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/ready_tasks` | list | 获取 ready_tasks 列表 |
| GET | `/api/v1/ready_tasks/{id}` | get | 获取单个 ready_tasks 详情 |

### Rebuild

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/rebuild` | create | 创建新的 rebuild |
| GET | `/api/v1/rebuild/{id}` | get | 获取单个 rebuild 详情 |
| PUT | `/api/v1/rebuild/{id}` | update | 完整更新 rebuild |
| PATCH | `/api/v1/rebuild/{id}` | partial_update | 部分更新 rebuild |

### Recent

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recent` | list | 获取 recent 列表 |
| GET | `/api/v1/recent/{id}` | get | 获取单个 recent 详情 |

### Recent_conversations

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recent_conversations` | list | 获取 recent_conversations 列表 |
| GET | `/api/v1/recent_conversations/{id}` | get | 获取单个 recent_conversations 详情 |

### Recent_corrections

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recent_corrections` | list | 获取 recent_corrections 列表 |
| GET | `/api/v1/recent_corrections/{id}` | get | 获取单个 recent_corrections 详情 |

### Recent_errors

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recent_errors` | list | 获取 recent_errors 列表 |
| GET | `/api/v1/recent_errors/{id}` | get | 获取单个 recent_errors 详情 |

### Recent_logs

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recent_logs` | list | 获取 recent_logs 列表 |
| GET | `/api/v1/recent_logs/{id}` | get | 获取单个 recent_logs 详情 |

### Recommendations

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recommendations` | list | 获取 recommendations 列表 |
| GET | `/api/v1/recommendations/{id}` | get | 获取单个 recommendations 详情 |

### Recommended_strategy

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recommended_strategy` | list | 获取 recommended_strategy 列表 |
| GET | `/api/v1/recommended_strategy/{id}` | get | 获取单个 recommended_strategy 详情 |

### Recommender_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/recommender_status` | list | 获取 recommender_status 列表 |
| GET | `/api/v1/recommender_status/{id}` | get | 获取单个 recommender_status 详情 |

### Registered_handlers

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/registered_handlers` | list | 获取 registered_handlers 列表 |
| GET | `/api/v1/registered_handlers/{id}` | get | 获取单个 registered_handlers 详情 |

### Registry_status

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/registry_status` | list | 获取 registry_status 列表 |
| GET | `/api/v1/registry_status/{id}` | get | 获取单个 registry_status 详情 |

### Related_nodes

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/related_nodes` | list | 获取 related_nodes 列表 |
| GET | `/api/v1/related_nodes/{id}` | get | 获取单个 related_nodes 详情 |

### Relations

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/relations` | list | 获取 relations 列表 |
| POST | `/api/v1/relations` | create | 创建新的 relations |
| GET | `/api/v1/relations/{id}` | get | 获取单个 relations 详情 |
| PUT | `/api/v1/relations/{id}` | update | 完整更新 relations |
| PATCH | `/api/v1/relations/{id}` | partial_update | 部分更新 relations |

### Remaining

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/remaining` | list | 获取 remaining 列表 |
| GET | `/api/v1/remaining/{id}` | get | 获取单个 remaining 详情 |

### Report

**原始端点数**: 3
**统一后端点数**: 3
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/report` | list | 获取 report 列表 |
| GET | `/api/v1/report/{id}` | get | 获取单个 report 详情 |
| DELETE | `/api/v1/report/{id}` | delete | 删除 report |

### Reprocess

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/reprocess` | create | 创建新的 reprocess |
| GET | `/api/v1/reprocess/{id}` | get | 获取单个 reprocess 详情 |
| PUT | `/api/v1/reprocess/{id}` | update | 完整更新 reprocess |
| PATCH | `/api/v1/reprocess/{id}` | partial_update | 部分更新 reprocess |

### Reprocess-failed

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/reprocess-failed` | create | 创建新的 reprocess-failed |
| GET | `/api/v1/reprocess-failed/{id}` | get | 获取单个 reprocess-failed 详情 |
| PUT | `/api/v1/reprocess-failed/{id}` | update | 完整更新 reprocess-failed |
| PATCH | `/api/v1/reprocess-failed/{id}` | partial_update | 部分更新 reprocess-failed |

### Request_logs

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/request_logs` | list | 获取 request_logs 列表 |
| GET | `/api/v1/request_logs/{id}` | get | 获取单个 request_logs 详情 |

### Reranker_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/reranker_service` | list | 获取 reranker_service 列表 |
| GET | `/api/v1/reranker_service/{id}` | get | 获取单个 reranker_service 详情 |

### Resource

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/resource` | list | 获取 resource 列表 |
| GET | `/api/v1/resource/{id}` | get | 获取单个 resource 详情 |

### Resource_history

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/resource_history` | list | 获取 resource_history 列表 |
| GET | `/api/v1/resource_history/{id}` | get | 获取单个 resource_history 详情 |

### Resource_owner

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/resource_owner` | list | 获取 resource_owner 列表 |
| GET | `/api/v1/resource_owner/{id}` | get | 获取单个 resource_owner 详情 |

### Resources

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/resources` | list | 获取 resources 列表 |
| GET | `/api/v1/resources/{id}` | get | 获取单个 resources 详情 |

### Retrieve

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/retrieve` | create | 创建新的 retrieve |
| GET | `/api/v1/retrieve/{id}` | get | 获取单个 retrieve 详情 |
| PUT | `/api/v1/retrieve/{id}` | update | 完整更新 retrieve |
| PATCH | `/api/v1/retrieve/{id}` | partial_update | 部分更新 retrieve |

### Role

**原始端点数**: 4
**统一后端点数**: 3
**减少**: 1 (25.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/role` | list | 获取 role 列表 |
| GET | `/api/v1/role/{id}` | get | 获取单个 role 详情 |
| DELETE | `/api/v1/role/{id}` | delete | 删除 role |

### Role_permission_detail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/role_permission_detail` | list | 获取 role_permission_detail 列表 |
| GET | `/api/v1/role_permission_detail/{id}` | get | 获取单个 role_permission_detail 详情 |

### Role_permissions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/role_permissions` | list | 获取 role_permissions 列表 |
| GET | `/api/v1/role_permissions/{id}` | get | 获取单个 role_permissions 详情 |

### Rollback_history

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/rollback_history` | list | 获取 rollback_history 列表 |
| GET | `/api/v1/rollback_history/{id}` | get | 获取单个 rollback_history 详情 |

### Room_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/room_info` | list | 获取 room_info 列表 |
| GET | `/api/v1/room_info/{id}` | get | 获取单个 room_info 详情 |

### Room_info_endpoint

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/room_info_endpoint` | list | 获取 room_info_endpoint 列表 |
| GET | `/api/v1/room_info_endpoint/{id}` | get | 获取单个 room_info_endpoint 详情 |

### Rooms

**原始端点数**: 4
**统一后端点数**: 5
**减少**: -1 (-25.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/rooms` | list | 获取 rooms 列表 |
| POST | `/api/v1/rooms` | create | 创建新的 rooms |
| GET | `/api/v1/rooms/{id}` | get | 获取单个 rooms 详情 |
| PUT | `/api/v1/rooms/{id}` | update | 完整更新 rooms |
| PATCH | `/api/v1/rooms/{id}` | partial_update | 部分更新 rooms |

### Router

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/router` | list | 获取 router 列表 |
| GET | `/api/v1/router/{id}` | get | 获取单个 router 详情 |

### Router_manager

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/router_manager` | list | 获取 router_manager 列表 |
| GET | `/api/v1/router_manager/{id}` | get | 获取单个 router_manager 详情 |

### Router_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/router_status` | list | 获取 router_status 列表 |
| GET | `/api/v1/router_status/{id}` | get | 获取单个 router_status 详情 |

### Routes_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/routes_info` | list | 获取 routes_info 列表 |
| GET | `/api/v1/routes_info/{id}` | get | 获取单个 routes_info 详情 |

### Routing_strategy

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/routing_strategy` | list | 获取 routing_strategy 列表 |
| GET | `/api/v1/routing_strategy/{id}` | get | 获取单个 routing_strategy 详情 |

### Running_tasks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/running_tasks` | list | 获取 running_tasks 列表 |
| GET | `/api/v1/running_tasks/{id}` | get | 获取单个 running_tasks 详情 |

### Sample_data

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/sample_data` | list | 获取 sample_data 列表 |
| GET | `/api/v1/sample_data/{id}` | get | 获取单个 sample_data 详情 |

### Scheduled_task

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/scheduled_task` | list | 获取 scheduled_task 列表 |
| GET | `/api/v1/scheduled_task/{id}` | get | 获取单个 scheduled_task 详情 |
| DELETE | `/api/v1/scheduled_task/{id}` | delete | 删除 scheduled_task |

### Scheduled_tasks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/scheduled_tasks` | list | 获取 scheduled_tasks 列表 |
| GET | `/api/v1/scheduled_tasks/{id}` | get | 获取单个 scheduled_tasks 详情 |

### Search

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/search` | list | 获取 search 列表 |
| GET | `/api/v1/search/{id}` | get | 获取单个 search 详情 |

### Search-with-citation

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/search-with-citation` | create | 创建新的 search-with-citation |
| GET | `/api/v1/search-with-citation/{id}` | get | 获取单个 search-with-citation 详情 |
| PUT | `/api/v1/search-with-citation/{id}` | update | 完整更新 search-with-citation |
| PATCH | `/api/v1/search-with-citation/{id}` | partial_update | 部分更新 search-with-citation |

### Sentence_embedding_dimension

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/sentence_embedding_dimension` | list | 获取 sentence_embedding_dimension 列表 |
| GET | `/api/v1/sentence_embedding_dimension/{id}` | get | 获取单个 sentence_embedding_dimension 详情 |

### Service_status

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/service_status` | list | 获取 service_status 列表 |
| GET | `/api/v1/service_status/{id}` | get | 获取单个 service_status 详情 |

### Services

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/services` | list | 获取 services 列表 |
| GET | `/api/v1/services/{id}` | get | 获取单个 services 详情 |

### Session

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/session/{id}` | get | 获取单个 session 详情 |
| DELETE | `/api/v1/session/{id}` | delete | 删除 session |

### Session_history

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/session_history` | list | 获取 session_history 列表 |
| GET | `/api/v1/session_history/{id}` | get | 获取单个 session_history 详情 |

### Session_messages

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/session_messages` | list | 获取 session_messages 列表 |
| GET | `/api/v1/session_messages/{id}` | get | 获取单个 session_messages 详情 |

### Sessions

**原始端点数**: 4
**统一后端点数**: 6
**减少**: -2 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/sessions` | list | 获取 sessions 列表 |
| POST | `/api/v1/sessions` | create | 创建新的 sessions |
| GET | `/api/v1/sessions/{id}` | get | 获取单个 sessions 详情 |
| PUT | `/api/v1/sessions/{id}` | update | 完整更新 sessions |
| PATCH | `/api/v1/sessions/{id}` | partial_update | 部分更新 sessions |
| DELETE | `/api/v1/sessions/{id}` | delete | 删除 sessions |

### Settings

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/settings` | list | 获取 settings 列表 |
| GET | `/api/v1/settings/{id}` | get | 获取单个 settings 详情 |

### Significant_comparisons

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/significant_comparisons` | list | 获取 significant_comparisons 列表 |
| GET | `/api/v1/significant_comparisons/{id}` | get | 获取单个 significant_comparisons 详情 |

### Similar_experiences

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/similar_experiences` | list | 获取 similar_experiences 列表 |
| GET | `/api/v1/similar_experiences/{id}` | get | 获取单个 similar_experiences 详情 |

### Single_analysis

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/single_analysis` | list | 获取 single_analysis 列表 |
| GET | `/api/v1/single_analysis/{id}` | get | 获取单个 single_analysis 详情 |

### Skill

**原始端点数**: 7
**统一后端点数**: 3
**减少**: 4 (57.1%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill` | list | 获取 skill 列表 |
| GET | `/api/v1/skill/{id}` | get | 获取单个 skill 详情 |
| DELETE | `/api/v1/skill/{id}` | delete | 删除 skill |

### Skill_analysis

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_analysis` | list | 获取 skill_analysis 列表 |
| GET | `/api/v1/skill_analysis/{id}` | get | 获取单个 skill_analysis 详情 |

### Skill_config

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_config` | list | 获取 skill_config 列表 |
| GET | `/api/v1/skill_config/{id}` | get | 获取单个 skill_config 详情 |

### Skill_detail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_detail` | list | 获取 skill_detail 列表 |
| GET | `/api/v1/skill_detail/{id}` | get | 获取单个 skill_detail 详情 |

### Skill_evolution_integration

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_evolution_integration` | list | 获取 skill_evolution_integration 列表 |
| GET | `/api/v1/skill_evolution_integration/{id}` | get | 获取单个 skill_evolution_integration 详情 |

### Skill_evolution_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_evolution_service` | list | 获取 skill_evolution_service 列表 |
| GET | `/api/v1/skill_evolution_service/{id}` | get | 获取单个 skill_evolution_service 详情 |

### Skill_evolution_summary

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_evolution_summary` | list | 获取 skill_evolution_summary 列表 |
| GET | `/api/v1/skill_evolution_summary/{id}` | get | 获取单个 skill_evolution_summary 详情 |

### Skill_executor

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_executor` | list | 获取 skill_executor 列表 |
| GET | `/api/v1/skill_executor/{id}` | get | 获取单个 skill_executor 详情 |

### Skill_generator

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_generator` | list | 获取 skill_generator 列表 |
| GET | `/api/v1/skill_generator/{id}` | get | 获取单个 skill_generator 详情 |

### Skill_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_info` | list | 获取 skill_info 列表 |
| GET | `/api/v1/skill_info/{id}` | get | 获取单个 skill_info 详情 |

### Skill_knowledge_base

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_knowledge_base` | list | 获取 skill_knowledge_base 列表 |
| GET | `/api/v1/skill_knowledge_base/{id}` | get | 获取单个 skill_knowledge_base 详情 |

### Skill_loader

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_loader` | list | 获取 skill_loader 列表 |
| GET | `/api/v1/skill_loader/{id}` | get | 获取单个 skill_loader 详情 |

### Skill_metadata

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_metadata` | list | 获取 skill_metadata 列表 |
| GET | `/api/v1/skill_metadata/{id}` | get | 获取单个 skill_metadata 详情 |

### Skill_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_service` | list | 获取 skill_service 列表 |
| GET | `/api/v1/skill_service/{id}` | get | 获取单个 skill_service 详情 |

### Skill_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_statistics` | list | 获取 skill_statistics 列表 |
| GET | `/api/v1/skill_statistics/{id}` | get | 获取单个 skill_statistics 详情 |

### Skill_usage_statistics

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_usage_statistics` | list | 获取 skill_usage_statistics 列表 |
| GET | `/api/v1/skill_usage_statistics/{id}` | get | 获取单个 skill_usage_statistics 详情 |

### Skill_versions

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skill_versions` | list | 获取 skill_versions 列表 |
| GET | `/api/v1/skill_versions/{id}` | get | 获取单个 skill_versions 详情 |

### Skills

**原始端点数**: 3
**统一后端点数**: 5
**减少**: -2 (-66.7%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skills` | list | 获取 skills 列表 |
| POST | `/api/v1/skills` | create | 创建新的 skills |
| GET | `/api/v1/skills/{id}` | get | 获取单个 skills 详情 |
| PUT | `/api/v1/skills/{id}` | update | 完整更新 skills |
| PATCH | `/api/v1/skills/{id}` | partial_update | 部分更新 skills |

### Skills_integration_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/skills_integration_service` | list | 获取 skills_integration_service 列表 |
| GET | `/api/v1/skills_integration_service/{id}` | get | 获取单个 skills_integration_service 详情 |

### Sop

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/sop` | list | 获取 sop 列表 |
| GET | `/api/v1/sop/{id}` | get | 获取单个 sop 详情 |

### Sop_by_name

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/sop_by_name` | list | 获取 sop_by_name 列表 |
| GET | `/api/v1/sop_by_name/{id}` | get | 获取单个 sop_by_name 详情 |

### Source_files

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/source_files` | list | 获取 source_files 列表 |
| GET | `/api/v1/source_files/{id}` | get | 获取单个 source_files 详情 |

### Sources

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/sources` | list | 获取 sources 列表 |
| POST | `/api/v1/sources` | create | 创建新的 sources |
| GET | `/api/v1/sources/{id}` | get | 获取单个 sources 详情 |
| PUT | `/api/v1/sources/{id}` | update | 完整更新 sources |
| PATCH | `/api/v1/sources/{id}` | partial_update | 部分更新 sources |

### Sqlite_database_path

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/sqlite_database_path` | list | 获取 sqlite_database_path 列表 |
| GET | `/api/v1/sqlite_database_path/{id}` | get | 获取单个 sqlite_database_path 详情 |

### Stage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/stage` | list | 获取 stage 列表 |
| GET | `/api/v1/stage/{id}` | get | 获取单个 stage 详情 |

### Stage_audit_trail

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/stage_audit_trail` | list | 获取 stage_audit_trail 列表 |
| GET | `/api/v1/stage_audit_trail/{id}` | get | 获取单个 stage_audit_trail 详情 |

### Stage_status

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/stage_status` | list | 获取 stage_status 列表 |
| GET | `/api/v1/stage_status/{id}` | get | 获取单个 stage_status 详情 |

### Stages

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/stages` | list | 获取 stages 列表 |
| GET | `/api/v1/stages/{id}` | get | 获取单个 stages 详情 |

### Statement_sources

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/statement_sources` | list | 获取 statement_sources 列表 |
| GET | `/api/v1/statement_sources/{id}` | get | 获取单个 statement_sources 详情 |

### Statements

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/statements` | list | 获取 statements 列表 |
| GET | `/api/v1/statements/{id}` | get | 获取单个 statements 详情 |

### Statistics

**原始端点数**: 20
**统一后端点数**: 5
**减少**: 15 (75.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/statistics` | list | 获取 statistics 列表 |
| POST | `/api/v1/statistics` | create | 创建新的 statistics |
| GET | `/api/v1/statistics/{id}` | get | 获取单个 statistics 详情 |
| PUT | `/api/v1/statistics/{id}` | update | 完整更新 statistics |
| PATCH | `/api/v1/statistics/{id}` | partial_update | 部分更新 statistics |

### Stats

**原始端点数**: 30
**统一后端点数**: 2
**减少**: 28 (93.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/stats` | list | 获取 stats 列表 |
| GET | `/api/v1/stats/{id}` | get | 获取单个 stats 详情 |

### Status

**原始端点数**: 10
**统一后端点数**: 2
**减少**: 8 (80.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/status` | list | 获取 status 列表 |
| GET | `/api/v1/status/{id}` | get | 获取单个 status 详情 |

### Storage

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/storage` | list | 获取 storage 列表 |
| GET | `/api/v1/storage/{id}` | get | 获取单个 storage 详情 |

### Strategies

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/strategies` | list | 获取 strategies 列表 |
| GET | `/api/v1/strategies/{id}` | get | 获取单个 strategies 详情 |

### Subgraph

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/subgraph` | list | 获取 subgraph 列表 |
| GET | `/api/v1/subgraph/{id}` | get | 获取单个 subgraph 详情 |

### Success_patterns

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/success_patterns` | list | 获取 success_patterns 列表 |
| GET | `/api/v1/success_patterns/{id}` | get | 获取单个 success_patterns 详情 |

### Summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/summary` | list | 获取 summary 列表 |
| GET | `/api/v1/summary/{id}` | get | 获取单个 summary 详情 |

### Supported-crawlers

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported-crawlers` | list | 获取 supported-crawlers 列表 |
| GET | `/api/v1/supported-crawlers/{id}` | get | 获取单个 supported-crawlers 详情 |

### Supported-languages

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported-languages` | list | 获取 supported-languages 列表 |
| GET | `/api/v1/supported-languages/{id}` | get | 获取单个 supported-languages 详情 |

### Supported_crawlers

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported_crawlers` | list | 获取 supported_crawlers 列表 |
| GET | `/api/v1/supported_crawlers/{id}` | get | 获取单个 supported_crawlers 详情 |

### Supported_extensions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported_extensions` | list | 获取 supported_extensions 列表 |
| GET | `/api/v1/supported_extensions/{id}` | get | 获取单个 supported_extensions 详情 |

### Supported_formats

**原始端点数**: 4
**统一后端点数**: 2
**减少**: 2 (50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported_formats` | list | 获取 supported_formats 列表 |
| GET | `/api/v1/supported_formats/{id}` | get | 获取单个 supported_formats 详情 |

### Supported_languages

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported_languages` | list | 获取 supported_languages 列表 |
| GET | `/api/v1/supported_languages/{id}` | get | 获取单个 supported_languages 详情 |

### Supported_plugins

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported_plugins` | list | 获取 supported_plugins 列表 |
| GET | `/api/v1/supported_plugins/{id}` | get | 获取单个 supported_plugins 详情 |

### Supported_strategies

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/supported_strategies` | list | 获取 supported_strategies 列表 |
| GET | `/api/v1/supported_strategies/{id}` | get | 获取单个 supported_strategies 详情 |

### System_status

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/system_status` | list | 获取 system_status 列表 |
| GET | `/api/v1/system_status/{id}` | get | 获取单个 system_status 详情 |

### Table

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/table` | list | 获取 table 列表 |
| GET | `/api/v1/table/{id}` | get | 获取单个 table 详情 |
| DELETE | `/api/v1/table/{id}` | delete | 删除 table |

### Tag

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tag/{id}` | get | 获取单个 tag 详情 |
| DELETE | `/api/v1/tag/{id}` | delete | 删除 tag |

### Tag_by_id

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tag_by_id` | list | 获取 tag_by_id 列表 |
| GET | `/api/v1/tag_by_id/{id}` | get | 获取单个 tag_by_id 详情 |

### Tag_statistics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tag_statistics` | list | 获取 tag_statistics 列表 |
| GET | `/api/v1/tag_statistics/{id}` | get | 获取单个 tag_statistics 详情 |

### Tag_trend

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tag_trend` | list | 获取 tag_trend 列表 |
| GET | `/api/v1/tag_trend/{id}` | get | 获取单个 tag_trend 详情 |

### Tagging_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tagging_service` | list | 获取 tagging_service 列表 |
| GET | `/api/v1/tagging_service/{id}` | get | 获取单个 tagging_service 详情 |

### Tags

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tags` | list | 获取 tags 列表 |
| GET | `/api/v1/tags/{id}` | get | 获取单个 tags 详情 |

### Tags_for_target

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tags_for_target` | list | 获取 tags_for_target 列表 |
| GET | `/api/v1/tags_for_target/{id}` | get | 获取单个 tags_for_target 详情 |

### Target_annotations

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/target_annotations` | list | 获取 target_annotations 列表 |
| GET | `/api/v1/target_annotations/{id}` | get | 获取单个 target_annotations 详情 |

### Target_tags

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/target_tags` | list | 获取 target_tags 列表 |
| GET | `/api/v1/target_tags/{id}` | get | 获取单个 target_tags 详情 |

### Targets_by_tag

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/targets_by_tag` | list | 获取 targets_by_tag 列表 |
| GET | `/api/v1/targets_by_tag/{id}` | get | 获取单个 targets_by_tag 详情 |

### Task

**原始端点数**: 2
**统一后端点数**: 3
**减少**: -1 (-50.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task` | list | 获取 task 列表 |
| GET | `/api/v1/task/{id}` | get | 获取单个 task 详情 |
| DELETE | `/api/v1/task/{id}` | delete | 删除 task |

### Task_by_id

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_by_id` | list | 获取 task_by_id 列表 |
| GET | `/api/v1/task_by_id/{id}` | get | 获取单个 task_by_id 详情 |

### Task_execution

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_execution` | list | 获取 task_execution 列表 |
| GET | `/api/v1/task_execution/{id}` | get | 获取单个 task_execution 详情 |

### Task_history

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_history` | list | 获取 task_history 列表 |
| GET | `/api/v1/task_history/{id}` | get | 获取单个 task_history 详情 |

### Task_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_info` | list | 获取 task_info 列表 |
| GET | `/api/v1/task_info/{id}` | get | 获取单个 task_info 详情 |

### Task_metrics

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_metrics` | list | 获取 task_metrics 列表 |
| GET | `/api/v1/task_metrics/{id}` | get | 获取单个 task_metrics 详情 |

### Task_progress

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_progress` | list | 获取 task_progress 列表 |
| GET | `/api/v1/task_progress/{id}` | get | 获取单个 task_progress 详情 |

### Task_result

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_result` | list | 获取 task_result 列表 |
| GET | `/api/v1/task_result/{id}` | get | 获取单个 task_result 详情 |

### Task_status

**原始端点数**: 5
**统一后端点数**: 2
**减少**: 3 (60.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/task_status` | list | 获取 task_status 列表 |
| GET | `/api/v1/task_status/{id}` | get | 获取单个 task_status 详情 |

### Tasks

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tasks` | list | 获取 tasks 列表 |
| GET | `/api/v1/tasks/{id}` | get | 获取单个 tasks 详情 |

### Templates

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/templates` | list | 获取 templates 列表 |
| GET | `/api/v1/templates/{id}` | get | 获取单个 templates 详情 |

### Temporal_extractor

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/temporal_extractor` | list | 获取 temporal_extractor 列表 |
| GET | `/api/v1/temporal_extractor/{id}` | get | 获取单个 temporal_extractor 详情 |

### Test

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/test` | list | 获取 test 列表 |
| POST | `/api/v1/test` | create | 创建新的 test |
| GET | `/api/v1/test/{id}` | get | 获取单个 test 详情 |
| PUT | `/api/v1/test/{id}` | update | 完整更新 test |
| PATCH | `/api/v1/test/{id}` | partial_update | 部分更新 test |

### Thinking_levels

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/thinking_levels` | list | 获取 thinking_levels 列表 |
| GET | `/api/v1/thinking_levels/{id}` | get | 获取单个 thinking_levels 详情 |

### Thinking_pattern_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/thinking_pattern_service` | list | 获取 thinking_pattern_service 列表 |
| GET | `/api/v1/thinking_pattern_service/{id}` | get | 获取单个 thinking_pattern_service 详情 |

### Thinking_patterns

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/thinking_patterns` | list | 获取 thinking_patterns 列表 |
| GET | `/api/v1/thinking_patterns/{id}` | get | 获取单个 thinking_patterns 详情 |

### Timeline

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/timeline` | list | 获取 timeline 列表 |
| GET | `/api/v1/timeline/{id}` | get | 获取单个 timeline 详情 |

### Timeline_distribution

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/timeline_distribution` | list | 获取 timeline_distribution 列表 |
| GET | `/api/v1/timeline_distribution/{id}` | get | 获取单个 timeline_distribution 详情 |

### Timeline_events

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/timeline_events` | list | 获取 timeline_events 列表 |
| GET | `/api/v1/timeline_events/{id}` | get | 获取单个 timeline_events 详情 |

### Timeline_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/timeline_service` | list | 获取 timeline_service 列表 |
| GET | `/api/v1/timeline_service/{id}` | get | 获取单个 timeline_service 详情 |

### Timeline_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/timeline_stats` | list | 获取 timeline_stats 列表 |
| GET | `/api/v1/timeline_stats/{id}` | get | 获取单个 timeline_stats 详情 |

### Toggle

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/toggle` | create | 创建新的 toggle |
| GET | `/api/v1/toggle/{id}` | get | 获取单个 toggle 详情 |
| PUT | `/api/v1/toggle/{id}` | update | 完整更新 toggle |
| PATCH | `/api/v1/toggle/{id}` | partial_update | 部分更新 toggle |

### Tool

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/tool` | list | 获取 tool 列表 |
| GET | `/api/v1/tool/{id}` | get | 获取单个 tool 详情 |

### Top_entities

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/top_entities` | list | 获取 top_entities 列表 |
| GET | `/api/v1/top_entities/{id}` | get | 获取单个 top_entities 详情 |

### Top_entries

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/top_entries` | list | 获取 top_entries 列表 |
| GET | `/api/v1/top_entries/{id}` | get | 获取单个 top_entries 详情 |

### Top_interests

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/top_interests` | list | 获取 top_interests 列表 |
| GET | `/api/v1/top_interests/{id}` | get | 获取单个 top_interests 详情 |

### Top_keywords

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/top_keywords` | list | 获取 top_keywords 列表 |
| GET | `/api/v1/top_keywords/{id}` | get | 获取单个 top_keywords 详情 |

### Top_learnings

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/top_learnings` | list | 获取 top_learnings 列表 |
| GET | `/api/v1/top_learnings/{id}` | get | 获取单个 top_learnings 详情 |

### Topic_distribution

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/topic_distribution` | list | 获取 topic_distribution 列表 |
| GET | `/api/v1/topic_distribution/{id}` | get | 获取单个 topic_distribution 详情 |

### Unified_rag_engine

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/unified_rag_engine` | list | 获取 unified_rag_engine 列表 |
| GET | `/api/v1/unified_rag_engine/{id}` | get | 获取单个 unified_rag_engine 详情 |

### Upload

**原始端点数**: 3
**统一后端点数**: 4
**减少**: -1 (-33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/upload` | create | 创建新的 upload |
| GET | `/api/v1/upload/{id}` | get | 获取单个 upload 详情 |
| PUT | `/api/v1/upload/{id}` | update | 完整更新 upload |
| PATCH | `/api/v1/upload/{id}` | partial_update | 部分更新 upload |

### Upload_progress

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/upload_progress` | list | 获取 upload_progress 列表 |
| GET | `/api/v1/upload_progress/{id}` | get | 获取单个 upload_progress 详情 |

### Upstream_lineage

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/upstream_lineage` | list | 获取 upstream_lineage 列表 |
| GET | `/api/v1/upstream_lineage/{id}` | get | 获取单个 upstream_lineage 详情 |

### Uptime

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/uptime` | list | 获取 uptime 列表 |
| GET | `/api/v1/uptime/{id}` | get | 获取单个 uptime 详情 |

### User

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user` | list | 获取 user 列表 |
| GET | `/api/v1/user/{id}` | get | 获取单个 user 详情 |

### User_activity

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_activity` | list | 获取 user_activity 列表 |
| GET | `/api/v1/user_activity/{id}` | get | 获取单个 user_activity 详情 |

### User_annotation_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_annotation_summary` | list | 获取 user_annotation_summary 列表 |
| GET | `/api/v1/user_annotation_summary/{id}` | get | 获取单个 user_annotation_summary 详情 |

### User_dimensions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_dimensions` | list | 获取 user_dimensions 列表 |
| GET | `/api/v1/user_dimensions/{id}` | get | 获取单个 user_dimensions 详情 |

### User_memories

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_memories` | list | 获取 user_memories 列表 |
| GET | `/api/v1/user_memories/{id}` | get | 获取单个 user_memories 详情 |

### User_permissions

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_permissions` | list | 获取 user_permissions 列表 |
| GET | `/api/v1/user_permissions/{id}` | get | 获取单个 user_permissions 详情 |

### User_preferences

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_preferences` | list | 获取 user_preferences 列表 |
| GET | `/api/v1/user_preferences/{id}` | get | 获取单个 user_preferences 详情 |

### User_summary

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_summary` | list | 获取 user_summary 列表 |
| GET | `/api/v1/user_summary/{id}` | get | 获取单个 user_summary 详情 |

### User_tag_summary

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/user_tag_summary` | list | 获取 user_tag_summary 列表 |
| GET | `/api/v1/user_tag_summary/{id}` | get | 获取单个 user_tag_summary 详情 |

### Validation

**原始端点数**: 5
**统一后端点数**: 2
**减少**: 3 (60.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/validation` | list | 获取 validation 列表 |
| GET | `/api/v1/validation/{id}` | get | 获取单个 validation 详情 |

### Valuable_feedings

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/valuable_feedings` | list | 获取 valuable_feedings 列表 |
| GET | `/api/v1/valuable_feedings/{id}` | get | 获取单个 valuable_feedings 详情 |

### Vector

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/vector/{id}` | get | 获取单个 vector 详情 |
| DELETE | `/api/v1/vector/{id}` | delete | 删除 vector |

### Vector_count

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/vector_count` | list | 获取 vector_count 列表 |
| GET | `/api/v1/vector_count/{id}` | get | 获取单个 vector_count 详情 |

### Vector_generator

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/vector_generator` | list | 获取 vector_generator 列表 |
| GET | `/api/v1/vector_generator/{id}` | get | 获取单个 vector_generator 详情 |

### Vector_store

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/vector_store` | list | 获取 vector_store 列表 |
| GET | `/api/v1/vector_store/{id}` | get | 获取单个 vector_store 详情 |

### Vectorization_service

**原始端点数**: 3
**统一后端点数**: 2
**减少**: 1 (33.3%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/vectorization_service` | list | 获取 vectorization_service 列表 |
| GET | `/api/v1/vectorization_service/{id}` | get | 获取单个 vectorization_service 详情 |

### Version

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/version` | list | 获取 version 列表 |
| GET | `/api/v1/version/{id}` | get | 获取单个 version 详情 |

### Version_by_number

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/version_by_number` | list | 获取 version_by_number 列表 |
| GET | `/api/v1/version_by_number/{id}` | get | 获取单个 version_by_number 详情 |

### Version_history

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/version_history` | list | 获取 version_history 列表 |
| GET | `/api/v1/version_history/{id}` | get | 获取单个 version_history 详情 |

### Video_info

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/video_info` | list | 获取 video_info 列表 |
| GET | `/api/v1/video_info/{id}` | get | 获取单个 video_info 详情 |

### View

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/view` | list | 获取 view 列表 |
| GET | `/api/v1/view/{id}` | get | 获取单个 view 详情 |

### View_definition

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/view_definition` | list | 获取 view_definition 列表 |
| GET | `/api/v1/view_definition/{id}` | get | 获取单个 view_definition 详情 |

### Visualization

**原始端点数**: 1
**统一后端点数**: 4
**减少**: -3 (-300.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| POST | `/api/v1/visualization` | create | 创建新的 visualization |
| GET | `/api/v1/visualization/{id}` | get | 获取单个 visualization 详情 |
| PUT | `/api/v1/visualization/{id}` | update | 完整更新 visualization |
| PATCH | `/api/v1/visualization/{id}` | partial_update | 部分更新 visualization |

### Visualization_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/visualization_service` | list | 获取 visualization_service 列表 |
| GET | `/api/v1/visualization_service/{id}` | get | 获取单个 visualization_service 详情 |

### Visualize

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/visualize` | list | 获取 visualize 列表 |
| GET | `/api/v1/visualize/{id}` | get | 获取单个 visualize 详情 |

### Word_count_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/word_count_stats` | list | 获取 word_count_stats 列表 |
| GET | `/api/v1/word_count_stats/{id}` | get | 获取单个 word_count_stats 详情 |

### Wordcloud

**原始端点数**: 2
**统一后端点数**: 5
**减少**: -3 (-150.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/wordcloud` | list | 获取 wordcloud 列表 |
| POST | `/api/v1/wordcloud` | create | 创建新的 wordcloud |
| GET | `/api/v1/wordcloud/{id}` | get | 获取单个 wordcloud 详情 |
| PUT | `/api/v1/wordcloud/{id}` | update | 完整更新 wordcloud |
| PATCH | `/api/v1/wordcloud/{id}` | partial_update | 部分更新 wordcloud |

### Wordcloud_data

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/wordcloud_data` | list | 获取 wordcloud_data 列表 |
| GET | `/api/v1/wordcloud_data/{id}` | get | 获取单个 wordcloud_data 详情 |

### Workbench_services

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workbench_services` | list | 获取 workbench_services 列表 |
| GET | `/api/v1/workbench_services/{id}` | get | 获取单个 workbench_services 详情 |

### Worker_stats

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/worker_stats` | list | 获取 worker_stats 列表 |
| GET | `/api/v1/worker_stats/{id}` | get | 获取单个 worker_stats 详情 |

### Workflow

**原始端点数**: 4
**统一后端点数**: 3
**减少**: 1 (25.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow` | list | 获取 workflow 列表 |
| GET | `/api/v1/workflow/{id}` | get | 获取单个 workflow 详情 |
| DELETE | `/api/v1/workflow/{id}` | delete | 删除 workflow |

### Workflow_execution

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_execution` | list | 获取 workflow_execution 列表 |
| GET | `/api/v1/workflow_execution/{id}` | get | 获取单个 workflow_execution 详情 |

### Workflow_executions

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_executions` | list | 获取 workflow_executions 列表 |
| GET | `/api/v1/workflow_executions/{id}` | get | 获取单个 workflow_executions 详情 |

### Workflow_manager

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_manager` | list | 获取 workflow_manager 列表 |
| GET | `/api/v1/workflow_manager/{id}` | get | 获取单个 workflow_manager 详情 |

### Workflow_progress

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_progress` | list | 获取 workflow_progress 列表 |
| GET | `/api/v1/workflow_progress/{id}` | get | 获取单个 workflow_progress 详情 |

### Workflow_service

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_service` | list | 获取 workflow_service 列表 |
| GET | `/api/v1/workflow_service/{id}` | get | 获取单个 workflow_service 详情 |

### Workflow_stats

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_stats` | list | 获取 workflow_stats 列表 |
| GET | `/api/v1/workflow_stats/{id}` | get | 获取单个 workflow_stats 详情 |

### Workflow_status

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_status` | list | 获取 workflow_status 列表 |
| GET | `/api/v1/workflow_status/{id}` | get | 获取单个 workflow_status 详情 |

### Workflow_steps

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflow_steps` | list | 获取 workflow_steps 列表 |
| GET | `/api/v1/workflow_steps/{id}` | get | 获取单个 workflow_steps 详情 |

### Workflows

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workflows` | list | 获取 workflows 列表 |
| GET | `/api/v1/workflows/{id}` | get | 获取单个 workflows 详情 |

### Workload_history

**原始端点数**: 2
**统一后端点数**: 2
**减少**: 0 (0.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/workload_history` | list | 获取 workload_history 列表 |
| GET | `/api/v1/workload_history/{id}` | get | 获取单个 workload_history 详情 |

### Zero_cost_solutions

**原始端点数**: 1
**统一后端点数**: 2
**减少**: -1 (-100.0%)

#### 标准端点

| 方法 | 路径 | 操作 | 说明 |
|------|------|------|------|
| GET | `/api/v1/zero_cost_solutions` | list | 获取 zero_cost_solutions 列表 |
| GET | `/api/v1/zero_cost_solutions/{id}` | get | 获取单个 zero_cost_solutions 详情 |

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
