================================================================================
路由重复问题修复报告
================================================================================

## 修复内容

### 1. 移除的重复路由注册
- /api/auth (旧版) - 保留 /api/v1/auth
- /api/projects (旧版) - 保留 /api/v1/projects

### 2. 标记为弃用的文件
- app/api/auth.py - 使用 v1/auth.py
- app/api/projects.py - 使用 v1/projects.py

### 3. 剩余的重复路由说明

以下路由在不同模块中有重复，但功能不同，需要保留：

- POST /build - timeline (时间线构建) vs knowledge_graph (图谱构建)
  解决方案: 通过不同的prefix区分 (/api/timeline/build vs /api/knowledge-graph/build)

- GET /stats - 多个模块都有统计接口
  解决方案: 通过prefix区分 (如 /api/timeline/stats, /api/memory/stats/{project_id})

- POST /upload - documents vs skills vs audio
  解决方案: 通过prefix区分 (如 /api/v1/documents/upload, /api/v1/audio/upload)

这些路由在不同的prefix下注册，实际不会冲突。

## 验证结果

修复后的路由结构：
- 认证: /api/v1/auth/* (唯一)
- 项目: /api/v1/projects/* (唯一)
- 其他功能路由通过prefix区分，无冲突

================================================================================