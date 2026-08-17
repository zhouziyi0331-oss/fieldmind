# P1-3: 未使用模块验证报告

## 分析说明

对初步分析报告中的112个"未使用模块"进行二次验证，排除误报。

## 分类结果

- **在main.py中注册**: 27个 (实际被使用)
- **入口点模块**: 2个 (实际被使用)
- **动态导入**: 0个 (实际被使用)
- **真正未使用**: 83个 ⚠️

---

## 1. 在main.py中注册的路由

这些模块通过`include_router`在main.py中注册，实际被使用。

- `api/reports_real.py` ✓
- `api/v1/super_agents.py` ✓
- `api/workflows_v2.py` ✓
- `api/document_processing_v2.py` ✓
- `api/documents.py` ✓
- `api/file_manager.py` ✓
- `api/photos.py` ✓
- `api/batch_processing.py` ✓
- `api/v1/projects.py` ✓
- `api/citations.py` ✓
- `api/aggregate.py` ✓
- `api/knowledge_graph_v3.py` ✓
- `api/dynamic_discovery_api.py` ✓
- `api/dashboard.py` ✓
- `api/analytics.py` ✓
- `api/hierarchical_retrieval.py` ✓
- `api/chat_rag.py` ✓
- `api/federation_api.py` ✓
- `api/v1/project_documents.py` ✓
- `api/skill_config.py` ✓
- `api/v1/reports.py` ✓
- `api/v1/crawler.py` ✓
- `api/v1/documents.py` ✓
- `core/cache.py` ✓
- `api/v1/knowledge_graph_api.py` ✓
- `api/v1/project_chat.py` ✓
- `api/document_processing.py` ✓

## 2. 入口点模块

这些是应用的入口点，被直接执行而非import。

- `main_v2.py` ✓
- `main_simple.py` ✓

## 3. 动态导入的模块

## 4. 真正未使用的模块 ⚠️

共 83 个模块从未被导入或使用，可以考虑删除。

- `tools/entity/unified_entity_engine.py` (43194 bytes)
- `tools/entity/unified_entity_extractor.py` (29729 bytes)
- `tools/coordinator/document_processing_pipeline_complete.py` (28899 bytes)
- `tools/coordinator/document_processing_pipeline.py` (26995 bytes)
- `agents/v2/quality_control_agent.py` (26549 bytes)
- `workflows/gap_analysis.py` (26537 bytes)
- `tools/coordinator/workflow_chain.py` (24968 bytes)
- `services/skills/xiangtu_china.py` (19921 bytes)
- `core/data_flow_orchestrator.py` (18444 bytes)
- `workflows/orchestrator.py` (17007 bytes)
- `tools/report/batch_services_07_15.py` (16578 bytes)
- `services/skills/sacred_memory.py` (16462 bytes)
- `core/error_handlers.py` (15229 bytes)
- `tools/knowledge/knowledge_graph_v2.py` (15131 bytes)
- `tools/report/dynamic_report_generator.py` (15042 bytes)
- `services/skills/business_feasibility.py` (14862 bytes)
- `tools/standalone/skill_sandbox.py` (14385 bytes)
- `tools/knowledge/relation_discovery.py` (14067 bytes)
- `tools/chunking/document_chunker_v2.py` (14052 bytes)
- `tools/ingestion/document_parser.py` (13005 bytes)
- `tasks/report_tasks.py` (12891 bytes)
- `tools/knowledge/knowledge_graph_builder_optimized.py` (12659 bytes)
- `tools/knowledge/document_network_builder.py` (12508 bytes)
- `tools/report/adaptive_analyzer.py` (12211 bytes)
- `services/workflows/autonomous_crew.py` (11903 bytes)
- `agents/entity_relation_agent.py` (11880 bytes)
- `tools/knowledge/knowledge_graph_builder.py` (11666 bytes)
- `tools/knowledge/correlation_recommender.py` (11559 bytes)
- `tools/synthesis/anti_hallucination_report.py` (11522 bytes)
- `tools/knowledge/knowledge_graph_service.py` (11488 bytes)
- `tools/knowledge/knowledge_graph_improved.py` (11056 bytes)
- `tools/synthesis/fact_statement_populator.py` (11016 bytes)
- `services/workflows/research_report_crew_v2.py` (10870 bytes)
- `services/skills/livelihood_ecology.py` (10831 bytes)
- `tools/synthesis/evidence_extractor.py` (10742 bytes)
- `tasks/rag_tasks.py` (10193 bytes)
- `core/alerts.py` (10193 bytes)
- `agents/crew_config.py` (9870 bytes)
- `tools/vectorization/structured_extractor.py` (9815 bytes)
- `tools/knowledge/neo4j_adapter.py` (9808 bytes)
- `services/skills/heritage_dadi.py` (9781 bytes)
- `tools/vectorization/cross_document_entity_resolver.py` (9607 bytes)
- `tasks/crawler_tasks.py` (9593 bytes)
- `services/skills/multi_village_sop.py` (9586 bytes)
- `tools/report/business_analysis_orchestrator.py` (9425 bytes)
- `services/agents/relation_agent.py` (9374 bytes)
- `services/skills/literature_market_research.py` (9338 bytes)
- `services/workflows/rag_query_crew.py` (9334 bytes)
- `tools/report/competitor_analysis_service.py` (9183 bytes)
- `tools/coordinator/document_processing_pipeline_v2.py` (9146 bytes)
- `tools/ingestion/multimodal_processor.py` (9067 bytes)
- `tools/synthesis/facts_anchor.py` (8955 bytes)
- `services/skills/community_governance.py` (8748 bytes)
- `tools/knowledge/document_relation_discovery.py` (8739 bytes)
- `tools/chunking/semantic_chunker.py` (8709 bytes)
- `tools/ingestion/document_converter_v2.py` (8679 bytes)
- `tools/vectorization/entity_extraction.py` (8527 bytes)
- `services/workflows/research_report_crew.py` (8354 bytes)
- `tools/vectorization/entity_extractor.py` (8345 bytes)
- `tools/ingestion/table_processor.py` (8332 bytes)
- `agents/field_dimension_agent.py` (8189 bytes)
- `api/v1/api_docs_enhanced.py` (8136 bytes)
- `tools/ingestion/data_quality_checker.py` (7982 bytes)
- `services/agents/entity_agent.py` (7907 bytes)
- `tools/report/market_demand_service.py` (7807 bytes)
- `tools/ingestion/data_curation.py` (7369 bytes)
- `tools/coordinator/batch_processor.py` (6892 bytes)
- `services/workflows/document_processing_crew.py` (6852 bytes)
- `middleware/enhanced_monitoring.py` (6773 bytes)
- `tasks/graph_tasks.py` (6768 bytes)
- `tasks/audio_tasks.py` (6475 bytes)
- `agents/v2/tool_registry.py` (6409 bytes)
- `tools/standalone/ragflow_service.py` (6335 bytes)
- `core/funasr_service.py` (5633 bytes)
- `tools/chunking/audio_chunker.py` (5388 bytes)
- `api/permissions.py` (5375 bytes)
- `tools/vectorization/llm_enhanced_extractor.py` (5308 bytes)
- `tools/report/pricing_strategy_service.py` (4530 bytes)
- `tools/coordinator/auto_processing_trigger.py` (3637 bytes)
- `core/unified_transcription.py` (3406 bytes)
- `middleware/project_isolation.py` (2480 bytes)
- `core/permissions.py` (2185 bytes)
- `middleware/performance.py` (1633 bytes)

**总计**: 83 个文件，950,028 bytes (927.8 KB)

