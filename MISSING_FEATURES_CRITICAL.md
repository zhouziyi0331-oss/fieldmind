# FieldMind 关键缺失功能清单

## 🔴 P0级别 - 核心流水线缺失（必须合并）

### 1. Knowledge Pipeline (知识流水线) - 完整9步处理
**位置**: `fieldmind/backend/src/app/services/knowledge_pipeline/`
**文件数**: 21个文件
**功能**: 端到端知识处理流水线
- Step 1: Text Cleaning (文本清洗)
- Step 2: Structure Analysis (结构分析)
- Step 3: Entity Extraction (实体提取)
- Step 4: Event Extraction (事件提取)
- Step 5: Relationship Discovery (关系发现)
- Step 6: Ontology Construction (本体构建)
- Step 7: Logical Inference (逻辑推理)
- Step 8: Knowledge Unitization (知识单元化)
- Step 9: Reader Generation (阅读器生成)

**API**: `/knowledge-pipeline`
**状态**: 主程序**完全缺失**

### 2. Document Normalization (文档规范化)
**位置**: `fieldmind/backend/src/app/services/document_normalization/`
**文件数**: 4个文件
- normalization_rules.py (48KB, 规范化规则)
- additional_rules.py (24KB, 附加规则)
- normalization_service.py (16KB)
- plugin_integration.py (9KB)

**API**: `/api/v1/files/{file_id}/normalize`
**状态**: 主程序**完全缺失**

### 3. Event Bus & Handlers (事件总线)
**位置**: `fieldmind/backend/src/app/services/event_handlers/`
**文件数**: 3个文件
- event_handler_registry.py (事件注册)
- event_monitoring_service.py (事件监控)
- normalization_handler.py (规范化处理器)

**状态**: 主程序**完全缺失**

## 🟡 P1级别 - 重要功能增强

### 4. Knowledge Graph Extensions (知识图谱扩展)
**位置**: `fieldmind/backend/src/app/services/knowledge_graph/`
- kg_analysis_service.py (分析服务)
- kg_query_service.py (查询服务)
- kg_visualization_api.py (可视化API)
- unified_query_interface.py (统一查询接口)

**状态**: 主程序knowledge_graph目录**缺失这4个文件**

### 5. Boundary Validators (边界校验器)
- boundary1_validator.py + v2
- boundary2_validator.py + v2
- data_contract_validator.py

**功能**: 数据质量和边界校验
**状态**: 主程序**缺失**

### 6. Performance & Monitoring
- performance_monitor.py (性能监控)
- monitoring_api.py (监控API)
- cache_optimization.py (缓存优化)

**API**: `/api/v1/monitoring`
**状态**: 主程序**缺失**

### 7. RAG Integration
- rag_integration_service.py
**状态**: 主程序有rag_p3.py但缺失此集成服务

### 8. Reader API
**位置**: `fieldmind/backend/src/app/api/reader.py`
**API**: `/reader/timeline/{document_id}`
**功能**: 文档阅读器时间线视图
**状态**: 主程序**缺失**

## 🟢 P2级别 - 优化功能

### 9. Chunk Enricher
- chunk_enricher.py (chunk增强)
**状态**: 主程序**缺失**

### 10. Export & Summary APIs
- export_summaries.py
- file_summaries.py
**状态**: 需检查主程序是否有等效实现

## 合并优先级

### 立即合并 (P0)
1. ✅ knowledge_pipeline/ (21个文件) - 核心流水线
2. ✅ document_normalization/ (4个文件) - 文档处理
3. ✅ event_handlers/ + event_bus.py - 事件系统
4. ✅ knowledge_pipeline.py API
5. ✅ document_normalization.py API

### 第二批 (P1)
6. ✅ knowledge_graph扩展 (4个文件)
7. ✅ monitoring相关 (3个文件)
8. ✅ boundary validators (5个文件)
9. ✅ reader.py API
10. ✅ rag_integration_service.py

### 第三批 (P2)
11. chunk_enricher.py
12. export_summaries.py
13. file_summaries.py

## 估计影响

- **新增服务文件**: ~40个
- **新增API路由**: 3个主要路由
- **新增代码量**: ~500KB
- **测试需求**: 9步流水线端到端测试

## 依赖检查清单

合并前必须检查：
- [ ] models/ 数据库模型是否一致
- [ ] 事件总线是否与现有架构冲突
- [ ] LLM调用接口是否统一
- [ ] Neo4j操作是否兼容
