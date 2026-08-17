================================================================================
代码质量检查报告
================================================================================

## 1. 编码问题 (11 个文件)

- code_quality_check.py
  问题: 包含乱码字符

- repos/crawl4ai/deploy/docker/tests/test_security_ssrf_crawl.py
  问题: 非UTF-8编码: utf-7

- repos/crawl4ai/docs/md_v2/assets/highlight.min.js
  问题: 非UTF-8编码: utf-7

- repos/LightRAG/lightrag/api/static/swagger-ui/swagger-ui-bundle.js
  问题: 包含乱码字符

- repos/LightRAG/lightrag/sidecar/backfill.py
  问题: 包含乱码字符

- repos/LightRAG/tests/kg/test_bounded_pipeline_history.py
  问题: 包含乱码字符

- repos/LightRAG/tests/sidecar/test_backfill.py
  问题: 包含乱码字符

- repos/LightRAG/tests/chunker/test_sidecar_backfill_integration.py
  问题: 包含乱码字符

- repos/khoj/src/khoj/processor/content/org_mode/orgnode.py
  问题: 非UTF-8编码: utf-7

- repos/ragflow/common/data_source/confluence_connector.py
  问题: 非UTF-8编码: utf-7

- external-tools/ragflow/common/data_source/confluence_connector.py
  问题: 非UTF-8编码: utf-7

## 2. 重复文件 (2403 组)

重复组 d41d8cd9:
  - repos/cognee/cognee/tasks/graph/cascade_extract/__init__.py
  - repos/cognee/cognee/tasks/graph/cascade_extract/utils/__init__.py
  - repos/cognee/cognee/tests/__init__.py
  - repos/cognee/cognee/tests/unit/truth_subspace/__init__.py
  - repos/cognee/cognee/tests/unit/tasks/graph/__init__.py
  - repos/cognee/cognee/tests/unit/api/v1/__init__.py
  - repos/cognee/cognee/tests/unit/api/v1/ui/__init__.py
  - repos/cognee/cognee/tests/unit/api/v1/config/__init__.py
  - repos/cognee/cognee/tests/unit/api/v1/recall/__init__.py
  - repos/cognee/cognee/tests/unit/api/v1/forget/__init__.py
  - repos/cognee/cognee/tests/unit/api/v1/improve/__init__.py
  - repos/cognee/cognee/tests/unit/infrastructure/databases/vector/__init__.py
  - repos/cognee/cognee/tests/unit/modules/tools/__init__.py
  - repos/cognee/cognee/tests/unit/modules/agents/__init__.py
  - repos/cognee/cognee/tests/unit/modules/observability/__init__.py
  - repos/cognee/cognee/tests/unit/modules/session_distillation/__init__.py
  - repos/cognee/cognee/tests/api/__init__.py
  - repos/cognee/cognee/tests/performance/utils/__init__.py
  - repos/cognee/cognee/tests/e2e/__init__.py
  - repos/cognee/cognee/tests/e2e/turso/__init__.py
  - repos/cognee/cognee/tests/e2e/postgres/__init__.py
  - repos/cognee/cognee/eval_framework/__init__.py
  - repos/cognee/cognee/eval_framework/reporting/__init__.py
  - repos/cognee/cognee/eval_framework/analysis/__init__.py
  - repos/cognee/cognee/eval_framework/answer_generation/__init__.py
  - repos/cognee/cognee/eval_framework/corpus_builder/__init__.py
  - repos/cognee/cognee/eval_framework/corpus_builder/task_getters/__init__.py
  - repos/cognee/cognee/eval_framework/sweeps/__init__.py
  - repos/cognee/cognee/eval_framework/evaluation/__init__.py
  - repos/cognee/cognee/eval_framework/evaluation/metrics/__init__.py
  - repos/cognee/cognee/eval_framework/benchmark_adapters/__init__.py
  - repos/cognee/cognee/eval_framework/beam/__init__.py
  - repos/cognee/cognee/eval_framework/beam/preprocessing/__init__.py
  - repos/cognee/cognee/eval_framework/beam/eval/__init__.py
  - repos/cognee/cognee/eval_framework/beam/eval/metrics/__init__.py
  - repos/cognee/cognee/api/__init__.py
  - repos/cognee/cognee/api/v1/memify/__init__.py
  - repos/cognee/cognee/api/v1/ontologies/routers/__init__.py
  - repos/cognee/cognee/api/v1/delete/delete.py
  - repos/cognee/cognee/api/v1/activity/__init__.py
  - repos/cognee/cognee/api/v1/sessions/routers/__init__.py
  - repos/cognee/cognee/api/v1/proposals/__init__.py
  - repos/cognee/cognee/infrastructure/__init__.py
  - repos/cognee/cognee/infrastructure/databases/__init__.py
  - repos/cognee/cognee/infrastructure/databases/relational/sqlalchemy/__init__.py
  - repos/cognee/cognee/infrastructure/databases/graph/kuzu/subprocess/__init__.py
  - repos/cognee/cognee/infrastructure/databases/graph/postgres/__init__.py
  - repos/cognee/cognee/infrastructure/databases/graph/neo4j_driver/__init__.py
  - repos/cognee/cognee/infrastructure/databases/vector/turso/__init__.py
  - repos/cognee/cognee/infrastructure/databases/vector/models/__init__.py
  - repos/cognee/cognee/infrastructure/databases/vector/lancedb/__init__.py
  - repos/cognee/cognee/infrastructure/databases/vector/lancedb/subprocess/__init__.py
  - repos/cognee/cognee/infrastructure/databases/hybrid/neptune_analytics/__init__.py
  - repos/cognee/cognee/infrastructure/databases/hybrid/postgres/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/baml/baml_src/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_native/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/gemini/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/generic_llm_api/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/azure_openai/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/anthropic/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/ollama/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/mistral/__init__.py
  - repos/cognee/cognee/infrastructure/llm/structured_output_framework/litellm_instructor/llm/openai/__init__.py
  - repos/cognee/cognee/infrastructure/context/__init__.py
  - repos/cognee/cognee/infrastructure/files/utils/__init__.py
  - repos/cognee/cognee/infrastructure/data/__init__.py
  - repos/cognee/cognee/infrastructure/data/utils/__init__.py
  - repos/cognee/cognee/infrastructure/data/chunking/__init__.py
  - repos/cognee/cognee/infrastructure/loaders/utils/__init__.py
  - repos/cognee/cognee/infrastructure/entities/__init__.py
  - repos/cognee/cognee/modules/__init__.py
  - repos/cognee/cognee/modules/truth_subspace/__init__.py
  - repos/cognee/cognee/modules/visualization/__init__.py
  - repos/cognee/cognee/modules/graph/cognee_graph/__init__.py
  - repos/cognee/cognee/modules/ontology/__init__.py
  - repos/cognee/cognee/modules/ontology/rdf_xml/__init__.py
  - repos/cognee/cognee/modules/cognify/__init__.py
  - repos/cognee/cognee/modules/recall/__init__.py
  - repos/cognee/cognee/modules/recall/types/__init__.py
  - repos/cognee/cognee/modules/recall/methods/__init__.py
  - repos/cognee/cognee/modules/retrieval/__init__.py
  - repos/cognee/cognee/modules/retrieval/context_providers/__init__.py
  - repos/cognee/cognee/modules/retrieval/utils/__init__.py
  - repos/cognee/cognee/modules/retrieval/entity_extractors/__init__.py
  - repos/cognee/cognee/modules/retrieval/hybrid/__init__.py
  - repos/cognee/cognee/modules/data/__init__.py
  - repos/cognee/cognee/modules/data/processing/__init__.py
  - repos/cognee/evals/old/hotpot_qa_24_2025/src/modal_apps/__init__.py
  - repos/cognee/evals/old/hotpot_qa_24_2025/src/qa/__init__.py
  - repos/cognee/distributed/__init__.py
  - repos/cognee/distributed/tasks/__init__.py
  - repos/cognee/cognee-mcp/src/codingagents/__init__.py
  - repos/crawl4ai/crawl4ai/crawlers/__init__.py
  - repos/crawl4ai/crawl4ai/crawlers/amazon_product/__init__.py
  - repos/crawl4ai/crawl4ai/crawlers/google_search/__init__.py
  - repos/crawl4ai/crawl4ai/legacy/__init__.py
  - repos/crawl4ai/tests/__init__.py
  - repos/crawl4ai/tests/deep_crawling/__init__.py
  - repos/LightRAG/lightrag/tools/__init__.py
  - repos/LightRAG/lightrag/llm/__init__.py
  - repos/LightRAG/tests/pipeline/__init__.py
  - repos/LightRAG/tests/tools/__init__.py
  - repos/LightRAG/tests/llm/__init__.py
  - repos/LightRAG/tests/llm/nvidia_impl/__init__.py
  - repos/LightRAG/tests/llm/voyageai_impl/__init__.py
  - repos/LightRAG/tests/llm/bedrock_impl/__init__.py
  - repos/LightRAG/tests/llm/gemini_impl/__init__.py
  - repos/LightRAG/tests/llm/ollama_impl/__init__.py
  - repos/LightRAG/tests/llm/zhipu_impl/__init__.py
  - repos/LightRAG/tests/llm/anthropic_impl/__init__.py
  - repos/LightRAG/tests/llm/openai_impl/__init__.py
  - repos/LightRAG/tests/workspace/__init__.py
  - repos/LightRAG/tests/utils/__init__.py
  - repos/LightRAG/tests/parser/__init__.py
  - repos/LightRAG/tests/parser/external/__init__.py
  - repos/LightRAG/tests/parser/external/docling/__init__.py
  - repos/LightRAG/tests/parser/external/mineru/__init__.py
  - repos/LightRAG/tests/parser/docx/__init__.py
  - repos/LightRAG/tests/kg/__init__.py
  - repos/LightRAG/tests/kg/faiss_impl/__init__.py
  - repos/LightRAG/tests/kg/redis_impl/__init__.py
  - repos/LightRAG/tests/kg/qdrant_impl/__init__.py
  - repos/LightRAG/tests/kg/postgres_impl/__init__.py
  - repos/LightRAG/tests/kg/milvus_impl/__init__.py
  - repos/LightRAG/tests/kg/json_impl/__init__.py
  - repos/LightRAG/tests/kg/mongo_impl/__init__.py
  - repos/LightRAG/tests/kg/memgraph_impl/__init__.py
  - repos/LightRAG/tests/kg/neo4j_impl/__init__.py
  - repos/LightRAG/tests/kg/opensearch_impl/__init__.py
  - repos/LightRAG/tests/kg/nano_impl/__init__.py
  - repos/LightRAG/tests/kg/networkx_impl/__init__.py
  - repos/LightRAG/tests/api/__init__.py
  - repos/LightRAG/tests/api/config/__init__.py
  - repos/LightRAG/tests/api/auth/__init__.py
  - repos/LightRAG/tests/api/routes/__init__.py
  - repos/LightRAG/tests/evaluation/__init__.py
  - repos/LightRAG/tests/sidecar/__init__.py
  - repos/LightRAG/tests/chunker/__init__.py
  - repos/LightRAG/tests/extraction/__init__.py
  - repos/firecrawl/apps/test-suite/jest.setup.js
  - repos/khoj/tests/__init__.py
  - repos/khoj/src/khoj/__init__.py
  - repos/khoj/src/khoj/routers/__init__.py
  - repos/khoj/src/khoj/database/__init__.py
  - repos/khoj/src/khoj/database/migrations/__init__.py
  - repos/khoj/src/khoj/database/management/__init__.py
  - repos/khoj/src/khoj/database/management/commands/__init__.py
  - repos/khoj/src/khoj/app/__init__.py
  - repos/khoj/src/khoj/search_type/__init__.py
  - repos/khoj/src/khoj/processor/__init__.py
  - repos/khoj/src/khoj/processor/tools/__init__.py
  - repos/khoj/src/khoj/processor/content/__init__.py
  - repos/khoj/src/khoj/processor/content/org_mode/__init__.py
  - repos/khoj/src/khoj/processor/content/plaintext/__init__.py
  - repos/khoj/src/khoj/processor/content/images/__init__.py
  - repos/khoj/src/khoj/processor/content/markdown/__init__.py
  - repos/khoj/src/khoj/processor/content/pdf/__init__.py
  - repos/khoj/src/khoj/processor/content/github/__init__.py
  - repos/khoj/src/khoj/processor/content/docx/__init__.py
  - repos/khoj/src/khoj/processor/speech/__init__.py
  - repos/khoj/src/khoj/processor/conversation/__init__.py
  - repos/khoj/src/khoj/processor/conversation/google/__init__.py
  - repos/khoj/src/khoj/processor/conversation/anthropic/__init__.py
  - repos/khoj/src/khoj/processor/conversation/openai/__init__.py
  - repos/khoj/src/khoj/utils/__init__.py
  - repos/khoj/src/khoj/search_filter/__init__.py
  - repos/markitdown/packages/markitdown/src/markitdown/converter_utils/__init__.py
  - repos/markitdown/packages/markitdown/src/markitdown/converter_utils/docx/__init__.py
  - repos/markitdown/packages/markitdown/src/markitdown/converter_utils/docx/math/__init__.py
  - repos/markitdown/packages/markitdown-ocr/tests/__init__.py
  - repos/pyhanlp/tests/demos/__init__.py
  - repos/graphiti/server/graph_service/__init__.py
  - repos/graphiti/server/graph_service/routers/__init__.py
  - repos/graphiti/graphiti_core/migrations/__init__.py
  - repos/graphiti/graphiti_core/driver/neo4j/__init__.py
  - repos/graphiti/graphiti_core/driver/kuzu/__init__.py
  - repos/graphiti/graphiti_core/driver/neptune/__init__.py
  - repos/graphiti/graphiti_core/utils/__init__.py
  - repos/graphiti/graphiti_core/models/__init__.py
  - repos/graphiti/graphiti_core/models/nodes/__init__.py
  - repos/graphiti/graphiti_core/models/edges/__init__.py
  - repos/graphiti/graphiti_core/search/__init__.py
  - repos/graphiti/mcp_server/tests/__init__.py
  - repos/graphiti/mcp_server/src/__init__.py
  - repos/graphiti/mcp_server/src/config/__init__.py
  - repos/graphiti/mcp_server/src/utils/__init__.py
  - repos/graphiti/mcp_server/src/models/__init__.py
  - repos/graphiti/mcp_server/src/services/__init__.py
  - repos/quivr/core/tests/__init__.py
  - repos/quivr/core/tests/processor/__init__.py
  - repos/quivr/core/tests/processor/odt/__init__.py
  - repos/quivr/core/tests/processor/pdf/__init__.py
  - repos/quivr/core/tests/processor/community/__init__.py
  - repos/quivr/core/tests/processor/docx/__init__.py
  - repos/quivr/core/tests/processor/epub/__init__.py
  - repos/quivr/core/quivr_core/llm_tools/__init__.py
  - repos/quivr/core/quivr_core/processor/__init__.py
  - repos/quivr/core/quivr_core/processor/implementations/__init__.py
  - repos/quivr/core/quivr_core/rag/__init__.py
  - repos/quivr/core/quivr_core/rag/entities/__init__.py
  - repos/quivr/core/quivr_core/storage/__init__.py
  - repos/mem0/tests/__init__.py
  - repos/mem0/tests/utils/__init__.py
  - repos/mem0/server/routers/__init__.py
  - repos/mem0/cli/python/tests/__init__.py
  - repos/mem0/examples/notebooks/helper/__init__.py
  - repos/mem0/mem0/vector_stores/__init__.py
  - repos/mem0/mem0/embeddings/__init__.py
  - repos/mem0/mem0/memory/__init__.py
  - repos/mem0/mem0/proxy/__init__.py
  - repos/mem0/mem0/configs/__init__.py
  - repos/mem0/mem0/configs/vector_stores/__init__.py
  - repos/mem0/mem0/configs/embeddings/__init__.py
  - repos/mem0/mem0/configs/rerankers/__init__.py
  - repos/mem0/mem0/configs/llms/__init__.py
  - repos/mem0/mem0/llms/__init__.py
  - repos/mem0/mem0/client/__init__.py
  - repos/ragflow/memory/__init__.py
  - repos/ragflow/memory/utils/__init__.py
  - repos/ragflow/memory/services/__init__.py
  - repos/ragflow/deepdoc/server/endpoints/__init__.py
  - repos/ragflow/deepdoc/server/adapters/__init__.py
  - repos/ragflow/test/__init__.py
  - repos/ragflow/test/unit_test/data_source/__init__.py
  - repos/ragflow/test/unit_test/rag/llm/__init__.py
  - repos/ragflow/test/unit_test/rag/app/__init__.py
  - repos/ragflow/test/playwright/__init__.py
  - repos/ragflow/test/playwright/e2e/__init__.py
  - repos/ragflow/test/playwright/helpers/__init__.py
  - repos/ragflow/web/src/pages/agent/hooks/use-iteration.ts
  - repos/ragflow/rag/graphrag/__init__.py
  - repos/ragflow/rag/graphrag/general/__init__.py
  - repos/ragflow/common/data_source/cross_connector_utils/__init__.py
  - repos/ragflow/common/data_source/google_util/__init__.py
  - repos/ragflow/common/data_source/jira/__init__.py
  - repos/ragflow/common/data_source/github/__init__.py
  - repos/ragflow/common/data_source/bitbucket/__init__.py
  - repos/ragflow/common/data_source/google_drive/__init__.py
  - repos/ragflow/common/doc_store/__init__.py
  - repos/ragflow/sdk/python/test/test_http_api/test_file_management_within_dataset/test_stop_parse_documents.py
  - repos/ragflow/api/db/joint_services/__init__.py
  - repos/ragflow/api/apps/services/__init__.py
  - repos/ragflow/api/channels/__init__.py
  - repos/ragflow/api/channels/core/__init__.py
  - repos/browser-use/examples/__init__.py
  - repos/browser-use/examples/models/langchain/__init__.py
  - repos/browser-use/browser_use/filesystem/__init__.py
  - repos/browser-use/browser_use/browser/watchdogs/__init__.py
  - repos/browser-use/browser_use/tokens/__init__.py
  - external-tools/markitdown/packages/markitdown/src/markitdown/converter_utils/__init__.py
  - external-tools/markitdown/packages/markitdown/src/markitdown/converter_utils/docx/__init__.py
  - external-tools/markitdown/packages/markitdown/src/markitdown/converter_utils/docx/math/__init__.py
  - external-tools/markitdown/packages/markitdown-ocr/tests/__init__.py
  - external-tools/ragflow/memory/__init__.py
  - external-tools/ragflow/memory/utils/__init__.py
  - external-tools/ragflow/memory/services/__init__.py
  - external-tools/ragflow/deepdoc/server/endpoints/__init__.py
  - external-tools/ragflow/deepdoc/server/adapters/__init__.py
  - external-tools/ragflow/test/__init__.py
  - external-tools/ragflow/test/unit_test/data_source/__init__.py
  - external-tools/ragflow/test/unit_test/rag/llm/__init__.py
  - external-tools/ragflow/test/unit_test/rag/app/__init__.py
  - external-tools/ragflow/test/playwright/__init__.py
  - external-tools/ragflow/test/playwright/e2e/__init__.py
  - external-tools/ragflow/test/playwright/helpers/__init__.py
  - external-tools/ragflow/web/src/pages/agent/hooks/use-iteration.ts
  - external-tools/ragflow/rag/graphrag/__init__.py
  - external-tools/ragflow/rag/graphrag/general/__init__.py
  - external-tools/ragflow/common/data_source/cross_connector_utils/__init__.py
  - external-tools/ragflow/common/data_source/google_util/__init__.py
  - external-tools/ragflow/common/data_source/jira/__init__.py
  - external-tools/ragflow/common/data_source/github/__init__.py
  - external-tools/ragflow/common/data_source/bitbucket/__init__.py
  - external-tools/ragflow/common/data_source/google_drive/__init__.py
  - external-tools/ragflow/common/doc_store/__init__.py
  - external-tools/ragflow/sdk/python/test/test_http_api/test_file_management_within_dataset/test_stop_parse_documents.py
  - external-tools/ragflow/api/db/joint_services/__init__.py
  - external-tools/ragflow/api/apps/services/__init__.py
  - external-tools/ragflow/api/channels/__init__.py
  - external-tools/ragflow/api/channels/core/__init__.py
  - fieldmind-backend/app/middleware/__init__.py

重复组 1eb34d03:
  - repos/cognee/cognee/infrastructure/databases/graph/supported_databases.py
  - repos/cognee/cognee/infrastructure/databases/vector/supported_databases.py

重复组 da71947e:
  - repos/cognee/evals/old/hotpot_qa_24_2025/src/helpers/convert_metrics.py
  - repos/cognee/evals/old/comparative_eval/helpers/convert_metrics.py

重复组 6965f0a0:
  - repos/cognee/evals/old/hotpot_qa_24_2025/src/helpers/modal_evaluate_answers.py
  - repos/cognee/evals/old/comparative_eval/helpers/modal_evaluate_answers.py

重复组 2f3be58a:
  - repos/cognee/evals/old/hotpot_qa_24_2025/src/helpers/calculate_aggregate_metrics.py
  - repos/cognee/evals/old/comparative_eval/helpers/calculate_aggregate_metrics.py

重复组 4d5dcbb8:
  - repos/cognee/examples/configurations/database_examples/neo4j_graph_database_configuration.py
  - repos/cognee/examples/database_examples/neo4j_example.py

重复组 2437efc6:
  - repos/cognee/examples/configurations/database_examples/ladybug_graph_database_configuration.py
  - repos/cognee/examples/database_examples/ladybug_example.py

重复组 0352474b:
  - repos/cognee/cognee-mcp/apps-src/src/vite-env.d.ts
  - repos/firecrawl/apps/ui/ingestion-ui/src/vite-env.d.ts
  - repos/neo4j-knowledge-graph-builder/frontend/src/vite-env.d.ts
  - repos/mem0/examples/vercel-ai-sdk-chat-app/src/vite-env.d.ts
  - repos/mem0/examples/multimodal-demo/src/vite-env.d.ts

重复组 52598e32:
  - repos/crawl4ai/tests/adaptive/test_llm_embedding.py
  - repos/crawl4ai/docs/examples/adaptive_crawling/llm_config_example.py

重复组 069a4b60:
  - repos/crawl4ai/docs/md_v2/assets/toc.js
  - repos/crawl4ai/docs/md_v2/assets/test/toc.js

## 3. 格式问题 (4387 个文件)

- code_quality_check.py
  行 119: 行过长 (121 > 120)

- test_workflow.py
  行 307: 行过长 (129 > 120)

- test_audio_processing.py
  行 119: 行过长 (125 > 120)

- test_real_audio.py
  行 114: 行过长 (139 > 120)

- repos/PDF-Guru/frontend/wailsjs/go/models.ts
  行 2: 行尾空格
  行 4: 混合tab和空格
  行 5: 混合tab和空格

- repos/PDF-Guru/frontend/wailsjs/go/main/App.d.ts
  行 5: 行过长 (151 > 100)
  行 7: 行过长 (163 > 100)
  行 9: 行过长 (246 > 100)

- repos/PDF-Guru/frontend/wailsjs/go/main/App.js
  行 6: 行过长 (112 > 100)
  行 10: 行过长 (118 > 100)
  行 13: 行过长 (135 > 100)

- repos/PDF-Guru/frontend/wailsjs/runtime/runtime.d.ts
  行 40: 行过长 (115 > 100)
  行 45: 行过长 (120 > 100)
  行 100: 行过长 (113 > 100)

- repos/PDF-Guru/thirdparty/encrypt.py
  行 11: 行过长 (126 > 120)
  行 64: 行过长 (140 > 120)
  行 74: 行过长 (153 > 120)

- repos/PDF-Guru/thirdparty/mask.py
  行 88: 行过长 (170 > 120)

- repos/PDF-Guru/thirdparty/merge.py
  行 13: 行过长 (124 > 120)

- repos/PDF-Guru/thirdparty/metadata.py
  行 35: 行过长 (135 > 120)

- repos/PDF-Guru/thirdparty/watermark.py
  行 48: 行尾空格
  行 131: 行过长 (136 > 120)
  行 137: 行过长 (131 > 120)

- repos/PDF-Guru/thirdparty/cmd_parser.py
  行 11: 行过长 (149 > 120)
  行 38: 行过长 (190 > 120)
  行 40: 行过长 (125 > 120)

- repos/PDF-Guru/thirdparty/convert.py
  行 12: 行过长 (124 > 120)
  行 140: 行尾空格
  行 182: 行过长 (127 > 120)

- repos/PDF-Guru/thirdparty/cut.py
  行 38: 行过长 (148 > 120)
  行 60: 行过长 (158 > 120)
  行 74: 行过长 (163 > 120)

- repos/PDF-Guru/thirdparty/page_number.py
  行 96: 行过长 (269 > 120)
  行 113: 行过长 (153 > 120)
  行 115: 行过长 (154 > 120)

- repos/PDF-Guru/thirdparty/background.py
  行 41: 行尾空格
  行 79: 行尾空格

- repos/PDF-Guru/thirdparty/pdf.py
  行 44: 行过长 (144 > 120)
  行 56: 行过长 (201 > 120)
  行 58: 行过长 (183 > 120)

- repos/PDF-Guru/thirdparty/bookmark.py
  行 77: 行尾空格
  行 113: 行尾空格
  行 116: 行过长 (129 > 120)

## 4. 代码质量问题 (4119 个文件)

### 严重问题 (214 个文件):
- code_quality_check.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_shared_node_preservation.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_delete_dataset_neo4j.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_delete_permission.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_delete_two_users_same_dataset.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_feedback_weights_memify_pipeline.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_delete_all_with_mixed_permissions.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_delete_dataset_ladybug.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/test_delete_two_users_with_legacy_data.py
  ⚠️  可能包含硬编码密码/密钥

- repos/cognee/cognee/tests/unit/api/test_cloud_client_skills_upload.py
  ⚠️  可能包含硬编码密码/密钥

### 警告 (386 个文件):
- repos/PDF-Guru/frontend/src/components/data.tsx
  包含 2 个console.log调试语句
  使用了 4 次any类型

- repos/cognee/cognee-frontend/src/app/(app)/graph-models/[id]/GraphModelEditorPage.tsx
  包含 5 个console.log调试语句
  使用了 1 次any类型

- repos/cognee/cognee-frontend/src/app/api/schema/inventory/route.ts
  包含 6 个console.log调试语句

- repos/cognee/cognee-frontend/src/app/api/log/route.ts
  包含 1 个console.log调试语句

- repos/cognee/cognee-frontend/src/modules/datasets/getSchemaInventory.ts
  包含 3 个console.log调试语句

- repos/cognee/cognee-frontend/src/modules/instances/localFetch.ts
  包含 2 个console.log调试语句

- repos/crawl4ai/crawl4ai/js_snippet/remove_overlay_elements.js
  包含 1 个console.log调试语句

- repos/crawl4ai/docs/md_v2/ask_ai/ask-ai.js
  包含 7 个console.log调试语句

- repos/crawl4ai/docs/md_v2/marketplace/marketplace.js
  包含 1 个console.log调试语句

- repos/crawl4ai/docs/md_v2/marketplace/frontend/marketplace.js
  包含 1 个console.log调试语句

================================================================================
## 统计总结

- 编码问题: 11 个文件
- 重复文件: 2403 组
- 格式问题: 4387 个文件
- 代码质量: 4119 个文件
================================================================================