## 📊 统计摘要

- 后端 API 模块: **54** 个
- 后端 API 端点: **384** 个
- 前端文件调用: **0** 个文件
- 前端 API 调用: **0** 次


## 🔌 后端 API 端点列表


### annotation.py (12 个端点)

- `POST /annotations`
- `GET /annotations`
- `GET /annotations/{annotation_id}`
- `PUT /annotations/{annotation_id}`
- `DELETE /annotations/{annotation_id}`
- `GET /annotations/target/{target_type}/{target_id}`
- `GET /statistics/{project_id}`
- `GET /summary/{project_id}`
- `GET /search/{project_id}`
- `GET /trend/{project_id}`
- `GET /quality-feedback/{project_id}`
- `GET /corrections/{project_id}`

### api_management.py (10 个端点)

- `GET /stats`
- `GET /metrics`
- `GET /logs`
- `POST /rate-limit/reset`
- `GET /config`
- `PUT /config`
- `GET /health`
- `GET /endpoints`
- `GET /errors`
- `GET /performance`

### audio.py (3 个端点)

- `POST /upload`
- `GET /status/{task_id}/`
- `GET /list`

### audit.py (5 个端点)

- `GET /logs`
- `GET /resource/{resource_type}/{resource_id}`
- `GET /user/{user_id}/activity`
- `GET /statistics`
- `DELETE /cleanup`

### auth.py (5 个端点)

- `POST /register`
- `POST /login`
- `POST /logout`
- `GET /me`
- `POST /refresh`

### background_learning.py (6 个端点)

- `POST /tasks`
- `POST /tasks/{task_id}/execute`
- `GET /tasks`
- `POST /schedules`
- `GET /insights`
- `PUT /insights/{insight_id}/review`

### business_analysis.py (3 个端点)

- `GET /projects/{project_id}/business-analysis/existing`
- `GET /projects/{project_id}/business-analysis/potential`
- `POST /projects/{project_id}/business-analysis/ai-evaluation`

### chunks_quantification.py (5 个端点)

- `GET /{chunk_id}/metrics/`
- `GET /document/{document_id}/metrics/`
- `GET /document/{document_id}/metrics/summary/`
- `GET /document/{document_id}/emotion-distribution/`
- `GET /search`

### collaboration.py (7 个端点)

- `GET /projects/{project_id}/members`
- `POST /projects/{project_id}/members`
- `DELETE /projects/{project_id}/members/{user_id}`
- `PUT /projects/{project_id}/members/{user_id}/role`
- `POST /projects/{project_id}/invites`
- `GET /projects/{project_id}/activity-log`
- `GET /projects/{project_id}/permissions/check`

### conversation.py (7 个端点)

- `POST /conversations`
- `GET /conversations/recent`
- `POST /conversations/search`
- `GET /conversations/entity/{entity_name}`
- `GET /conversations/summary/{project_id}`
- `PUT /conversations/{memory_id}/importance`
- `DELETE /conversations/cleanup`

### crawler.py (6 个端点)

- `POST /crawl`
- `POST /batch-crawl`
- `POST /news`
- `POST /government`
- `GET /status/{task_id}/`
- `GET /supported-crawlers`

### dashboard.py (13 个端点)

- `POST /snapshots`
- `GET /snapshots/{project_id}`
- `GET /snapshots/{project_id}/trend/{metric_name}`
- `POST /events`
- `GET /events/{project_id}`
- `GET /events/{project_id}/statistics`
- `GET /projects/{project_id}/metrics`
- `POST /projects/{project_id}/metrics/increment`
- `POST /projects/{project_id}/workload/calculate`
- `GET /projects/{project_id}/workload/history`
- `POST /value-exhibitions`
- `GET /value-exhibitions/{project_id}`
- `GET /dashboard/{project_id}`

### dashboard_optimized.py (5 个端点)

- `GET /projects/{project_id}/quality`
- `GET /projects/{project_id}/stats`
- `GET /projects/{project_id}/knowledge-graph`
- `POST /cache/invalidate`
- `GET /cache/stats`

### data_enrichment.py (2 个端点)

- `POST /projects/{project_id}/enrich`
- `GET /projects/{project_id}/enrichment-status`

### data_quality.py (5 个端点)

- `GET /data-quality/{project_id}/overview`
- `GET /data-quality/document/{document_id}`
- `POST /data-quality/document/{document_id}/retry`
- `GET /data-quality/{project_id}/gaps`
- `GET /data-quality/{project_id}/dashboard`

### documents.py (10 个端点)

- `POST /upload`
- `GET /{document_id}`
- `GET /projects/{project_id}/documents/simple`
- `PATCH /{document_id}`
- `DELETE /{document_id}`
- `GET /{document_id}/download`
- `GET /{document_id}/content/`
- `POST /classify`
- `POST /upload-batch`
- `GET /upload-progress/{project_id}`

### enhanced_chat.py (8 个端点)

- `POST /chat/enhanced`
- `POST /chat/enhanced/stream`
- `POST /chat/sessions`
- `GET /chat/sessions/{project_id}/`
- `GET /chat/sessions/{session_id}/messages/`
- `POST /memory/search`
- `GET /memory/statistics`
- `DELETE /chat/sessions/{session_id}/`

### execution_tracking.py (6 个端点)

- `POST /executions`
- `PUT /executions/{execution_id}/progress`
- `PUT /executions/{execution_id}/complete`
- `PUT /executions/{execution_id}/feedback`
- `GET /executions`
- `GET /patterns`

### experience_graph.py (3 个端点)

- `POST /build`
- `POST /query`
- `GET /statistics/{project_id}`

### feedback_loops.py (8 个端点)

- `POST /loops`
- `POST /loops/{loop_id}/feedback`
- `POST /loops/{loop_id}/learn`
- `POST /loops/{loop_id}/improve`
- `POST /loops/{loop_id}/complete`
- `GET /loops`
- `GET /tasks`
- `GET /metrics/{project_id}`

### feeding.py (11 个端点)

- `POST /sessions`
- `GET /sessions`
- `POST /sessions/{session_id}/apply`
- `PUT /sessions/{session_id}/importance`
- `DELETE /sessions/{session_id}`
- `GET /summary/{project_id}`
- `GET /valuable/{project_id}`
- `GET /search`
- `GET /trend/{project_id}`
- `GET /corrections/{project_id}`
- `GET /preferences/{project_id}`

### governance_validation.py (5 个端点)

- `GET /validation/dimension-distribution`
- `GET /validation/chunk-continuity`
- `GET /validation/missing-analysis`
- `GET /validation/document-coverage/{document_id}/`
- `GET /validation/full-report`

### industry.py (4 个端点)

- `GET /categories`
- `GET /{category}/details`
- `GET /{category}/statistics`
- `GET /{category}/trends`

### knowledge_graph.py (3 个端点)

- `GET /knowledge-graph/{project_id}`
- `GET /knowledge-graph/{project_id}/node/{node_id}`
- `POST /knowledge-graph/{project_id}/rebuild`

### knowledge_graph_api.py (6 个端点)

- `GET /stats`
- `GET /data`
- `POST /query/related`
- `POST /build/{document_id}/`
- `POST /rebuild`
- `GET /export/html`

### knowledge_graph_enhanced.py (9 个端点)

- `POST /construct`
- `POST /query/node`
- `POST /reasoning`
- `POST /skills/link`
- `POST /skills/query`
- `POST /timeline`
- `POST /export`
- `POST /cypher/query`
- `GET /stats`

### knowledge_network.py (2 个端点)

- `GET /projects/{project_id}/knowledge-network`
- `GET /projects/{project_id}/knowledge-network/nodes/{node_id}`

### learning.py (9 个端点)

- `POST /logs`
- `GET /logs`
- `POST /logs/{log_id}/apply`
- `PUT /logs/{log_id}/status`
- `DELETE /logs/{log_id}`
- `GET /summary/{project_id}`
- `GET /top/{project_id}`
- `GET /search`
- `GET /trend/{project_id}`

### learning_old.py (6 个端点)

- `POST /experience`
- `POST /suggest`
- `GET /stats`
- `POST /skill`
- `GET /skills`
- `GET /health`

### lineage.py (10 个端点)

- `POST /lineage`
- `GET /lineage/upstream/{target_type}/{target_id}`
- `GET /lineage/downstream/{source_type}/{source_id}`
- `GET /lineage/graph/{node_type}/{node_id}`
- `GET /lineage/impact/{source_type}/{source_id}`
- `POST /versions`
- `GET /versions/{data_type}/{data_id}`
- `POST /source-files`
- `GET /source-files/{project_id}`
- `GET /stats/{project_id}`

### pattern_recognition.py (5 个端点)

- `POST /detect`
- `POST /match`
- `GET /patterns`
- `PUT /patterns/{pattern_id}/validate`
- `PUT /patterns/{pattern_id}/activate`

### permissions.py (17 个端点)

- `POST /roles`
- `GET /roles`
- `GET /roles/{role_id}`
- `PUT /roles/{role_id}`
- `DELETE /roles/{role_id}`
- `POST /permissions`
- `GET /permissions`
- `POST /roles/{role_id}/permissions`
- `POST /projects/{project_id}/members`
- `GET /projects/{project_id}/members`
- `PUT /projects/{project_id}/members/{user_id}`
- `DELETE /projects/{project_id}/members/{user_id}`
- `POST /resources/{resource_type}/{resource_id}/owner`
- `GET /resources/{resource_type}/{resource_id}/owner`
- `GET /users/{user_id}/permissions`
- `GET /users/me/permissions`
- `POST /check`

### project_chat.py (2 个端点)

- `POST /{project_id}/chat-sessions/{session_id}/messages`
- `GET /{project_id}/chat-sessions/{session_id}/messages`

### project_documents.py (8 个端点)

- `POST /{project_id}/documents/upload`
- `GET /{project_id}/documents/{document_id}`
- `GET /{project_id}/documents/{document_id}/tags/`
- `POST /{project_id}/documents/{document_id}/tags/`
- `DELETE /{project_id}/documents/{document_id}/tags/{tag_id}`
- `POST /{project_id}/documents/{document_id}/process/`
- `DELETE /{project_id}/documents/{document_id}`
- `GET /{project_id}/documents/{document_id}/content/`

### project_workflow.py (2 个端点)

- `POST /projects/{project_id}/analyze/`
- `GET /projects/{project_id}/workflow-status/`

### projects.py (18 个端点)

- `POST /`
- `GET /`
- `GET /{project_id}/`
- `PUT /{project_id}`
- `DELETE /{project_id}`
- `POST /{project_id}/archive`
- `POST /{project_id}/restore`
- `GET /{project_id}/documents`
- `GET /{project_id}/documents/{document_id}`
- `POST /{project_id}/contexts`
- `GET /{project_id}/contexts`
- `GET /{project_id}/contexts/{context_id}`
- `POST /{project_id}/chat-sessions`
- `GET /{project_id}/chat-sessions`
- `GET /{project_id}/chat-sessions/{session_id}`
- `GET /{project_id}/dashboard`
- `GET /{project_id}/memories`
- `GET /{project_id}/sessions/`

### query_api.py (6 个端点)

- `POST /`
- `GET /views`
- `GET /view/{view_id}`
- `GET /metrics`
- `POST /cache/clear`
- `POST /metrics/reset`

### rag.py (3 个端点)

- `POST /retrieve`
- `GET /stats`
- `POST /test`

### reports.py (5 个端点)

- `POST /generate`
- `GET /{report_id}`
- `GET /{report_id}/download/`
- `DELETE /{report_id}`
- `POST /summary-document`

### search.py (1 个端点)

- `GET /entity/{entity_name}/graph`

### skill_generation.py (6 个端点)

- `POST /generate`
- `POST /skills/{skill_id}/test`
- `POST /skills/{skill_id}/validate`
- `POST /skills/{skill_id}/deploy`
- `GET /skills`
- `GET /skills/{skill_id}`

### skill_optimization.py (8 个端点)

- `POST /performance`
- `GET /performance/{skill_id}/summary`
- `GET /recommendations`
- `POST /optimizations`
- `GET /optimizations`
- `POST /optimizations/{optimization_id}/validate`
- `POST /optimizations/{optimization_id}/apply`
- `POST /optimizations/{optimization_id}/revert`

### skills.py (6 个端点)

- `POST /upload`
- `PUT /{skill_id}/activate`
- `PUT /{skill_id}/deactivate`
- `DELETE /{skill_id}`
- `POST /{skill_id}/test`
- `GET /available-for-task`

### sop.py (11 个端点)

- `POST /`
- `GET /`
- `GET /{sop_id}`
- `GET /by-name/{name}`
- `PATCH /{sop_id}`
- `POST /{sop_id}/activate`
- `POST /{sop_id}/archive`
- `POST /execute`
- `GET /executions/`
- `GET /executions/{execution_id}`
- `POST /executions/{execution_id}/cancel`

### super_agents.py (7 个端点)

- `POST /knowledge/analyze`
- `POST /search/query`
- `POST /summary/generate`
- `POST /transcript/process`
- `POST /orchestrate`
- `GET /status/{execution_id}`
- `GET /health`

### tagging.py (12 个端点)

- `POST /tags`
- `POST /tags/bulk`
- `GET /tags`
- `DELETE /tags/{tag_id}`
- `DELETE /tags/target/{target_type}/{target_id}`
- `GET /tags/target/{target_type}/{target_id}`
- `GET /tag-names/{project_id}`
- `GET /targets-by-tag/{project_id}/{tag_name}`
- `GET /statistics/{project_id}`
- `GET /summary/{project_id}`
- `GET /search/{project_id}`
- `GET /trend/{project_id}`

### tasks.py (9 个端点)

- `POST /documents/{document_id}/process`
- `GET /{task_id}/status`
- `POST /{task_id}/cancel`
- `GET /active`
- `GET /scheduled`
- `GET /workers`
- `GET /metrics`
- `GET /queues/{queue_name}/length`
- `DELETE /queues/{queue_name}`

### topic_analysis.py (7 个端点)

- `POST /extract-keywords`
- `GET /keywords/chunk/{chunk_id}/`
- `GET /keywords/project/{project_id}/`
- `POST /cluster`
- `GET /clusters/{project_id}/`
- `GET /clusters/{project_id}/{cluster_id}/chunks/`
- `POST /auto-analyze/{project_id}/`

### traceability.py (5 个端点)

- `POST /traceability/trace`
- `GET /traceability/chunk/{chunk_id}/context`
- `GET /traceability/chunk/{chunk_id}/highlight`
- `GET /traceability/document/{document_id}/chunks`
- `POST /traceability/batch-trace`

### unified_plugins.py (8 个端点)

- `GET /list`
- `GET /extensions`
- `GET /plugin/{plugin_name}`
- `POST /process/upload`
- `POST /process/path`
- `POST /process/batch`
- `GET /test/{plugin_name}`
- `POST /recommend`

### user_analysis.py (9 个端点)

- `POST /dimensions`
- `GET /dimensions`
- `GET /dimensions/top/{project_id}`
- `POST /patterns`
- `GET /patterns`
- `PUT /patterns/{pattern_id}/confidence`
- `GET /focus/{project_id}`
- `GET /suggestions/{project_id}`
- `GET /baseline/{project_id}`

### workbench.py (19 个端点)

- `GET /health`
- `GET /services`
- `POST /nlp/tokenize`
- `POST /nlp/keywords`
- `POST /nlp/entities`
- `POST /nlp/summarize`
- `POST /nlp/sentiment`
- `POST /rag/query`
- `POST /rag/index`
- `POST /kg/build`
- `POST /kg/query`
- `GET /kg/entity/{entity_id}/neighbors`
- `POST /document/process`
- `GET /document/formats`
- `POST /crawler/crawl`
- `POST /memory/store`
- `GET /memory/search`
- `POST /visualization/mindmap`
- `GET /overview`

### workflows.py (12 个端点)

- `POST /executions`
- `POST /executions/{execution_id}/start`
- `POST /executions/{execution_id}/execute`
- `POST /executions/{execution_id}/cancel`
- `GET /executions/{execution_id}`
- `GET /executions`
- `GET /executions/{execution_id}/steps`
- `GET /executions/{execution_id}/progress`
- `POST /templates`
- `GET /templates`
- `POST /steps/{step_id}/retry`
- `GET /handlers`

### workflows_old.py (4 个端点)

- `GET /{workflow_id}`
- `POST /{workflow_id}/execute`
- `DELETE /{workflow_id}`
- `GET /{workflow_id}/executions`


## 🌐 前端 API 调用列表



## ✅ 连接状态

- 后端 API 已部署: ✅
- 前端已配置 API 客户端: ✅
- API 基础 URL: `http://localhost:8000`
- 认证方式: JWT Bearer Token
- CORS 配置: 已启用
