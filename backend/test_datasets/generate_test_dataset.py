"""
RAG评测示例测试集

包含50个精心设计的测试用例，覆盖不同难度和类别
"""

# 这是用于生成测试数据集的脚本
SAMPLE_TEST_CASES = [
    # 1. 事实查询类 (Factual)
    {
        "id": "fact_001",
        "question": "FieldMind系统支持哪些文件格式的上传？",
        "expected_answer": "FieldMind支持PDF、Word文档(doc/docx)、纯文本(txt)、Markdown(md)等常见文档格式的上传。",
        "relevant_doc_ids": ["doc_system_features", "doc_file_upload"],
        "aspects": ["PDF支持", "Word支持", "文本格式", "Markdown支持"],
        "category": "factual",
        "difficulty": "easy"
    },
    {
        "id": "fact_002",
        "question": "如何创建一个新项目？",
        "expected_answer": "登录后点击'新建项目'按钮，输入项目名称和描述，选择项目类型，然后点击'创建'即可。",
        "relevant_doc_ids": ["doc_project_management", "doc_getting_started"],
        "aspects": ["登录", "新建按钮", "项目信息", "创建操作"],
        "category": "factual",
        "difficulty": "easy"
    },
    {
        "id": "fact_003",
        "question": "系统的最大文件上传限制是多少？",
        "expected_answer": "单个文件最大支持100MB，每个项目总容量限制为10GB。",
        "relevant_doc_ids": ["doc_file_limits", "doc_system_config"],
        "aspects": ["单文件限制", "100MB", "项目容量", "10GB"],
        "category": "factual",
        "difficulty": "easy"
    },
    {
        "id": "fact_004",
        "question": "FieldMind使用的是哪个AI模型？",
        "expected_answer": "FieldMind使用OpenAI的GPT-4模型作为对话引擎，同时支持配置其他模型如Claude和Llama。",
        "relevant_doc_ids": ["doc_ai_models", "doc_technical_specs"],
        "aspects": ["GPT-4", "OpenAI", "多模型支持", "配置选项"],
        "category": "factual",
        "difficulty": "medium"
    },
    {
        "id": "fact_005",
        "question": "系统如何保证数据安全？",
        "expected_answer": "采用AES-256加密存储、SSL/TLS传输加密、JWT认证、RBAC权限控制、定期备份等多重安全机制。",
        "relevant_doc_ids": ["doc_security", "doc_data_protection"],
        "aspects": ["加密存储", "传输加密", "认证机制", "权限控制", "备份"],
        "category": "factual",
        "difficulty": "medium"
    },

    # 2. 操作指导类 (How-to)
    {
        "id": "howto_001",
        "question": "如何删除已上传的文档？",
        "expected_answer": "进入项目后，在文档列表中找到目标文档，点击右侧的'删除'按钮，确认后即可删除。",
        "relevant_doc_ids": ["doc_document_management", "doc_operations"],
        "aspects": ["进入项目", "文档列表", "删除按钮", "确认操作"],
        "category": "howto",
        "difficulty": "easy"
    },
    {
        "id": "howto_002",
        "question": "怎样邀请团队成员加入项目？",
        "expected_answer": "在项目设置中选择'成员管理'，点击'邀请成员'，输入邮箱地址，选择权限角色，发送邀请即可。",
        "relevant_doc_ids": ["doc_team_collaboration", "doc_project_settings"],
        "aspects": ["项目设置", "成员管理", "邀请功能", "权限设置"],
        "category": "howto",
        "difficulty": "medium"
    },
    {
        "id": "howto_003",
        "question": "如何导出对话记录？",
        "expected_answer": "在对话界面点击右上角的菜单，选择'导出对话'，可以选择导出为PDF或Markdown格式。",
        "relevant_doc_ids": ["doc_chat_features", "doc_export"],
        "aspects": ["对话界面", "导出功能", "格式选择", "PDF和Markdown"],
        "category": "howto",
        "difficulty": "easy"
    },
    {
        "id": "howto_004",
        "question": "如何配置自定义的AI提示词模板？",
        "expected_answer": "进入系统设置-AI配置，点击'提示词模板'，可以新建或编辑模板，设置系统提示词和用户提示词格式。",
        "relevant_doc_ids": ["doc_ai_customization", "doc_prompt_engineering"],
        "aspects": ["系统设置", "AI配置", "模板管理", "提示词编辑"],
        "category": "howto",
        "difficulty": "hard"
    },
    {
        "id": "howto_005",
        "question": "如何设置文档的访问权限？",
        "expected_answer": "选中文档后点击'权限设置'，可以设置为私有、项目成员可见或公开，并可针对特定用户设置读写权限。",
        "relevant_doc_ids": ["doc_permissions", "doc_access_control"],
        "aspects": ["权限设置", "访问级别", "用户权限", "读写控制"],
        "category": "howto",
        "difficulty": "medium"
    },

    # 3. 故障排查类 (Troubleshooting)
    {
        "id": "trouble_001",
        "question": "上传文档失败显示'文件格式不支持'怎么办？",
        "expected_answer": "检查文件扩展名是否正确，确保文件未损坏，如果是特殊格式请先转换为PDF或Word格式后再上传。",
        "relevant_doc_ids": ["doc_troubleshooting", "doc_file_upload"],
        "aspects": ["格式检查", "文件完整性", "格式转换", "支持的格式"],
        "category": "troubleshooting",
        "difficulty": "medium"
    },
    {
        "id": "trouble_002",
        "question": "AI回答速度很慢是什么原因？",
        "expected_answer": "可能是网络延迟、文档数量过多、或当前并发用户较多。建议减少检索文档数量、优化查询关键词、或稍后重试。",
        "relevant_doc_ids": ["doc_performance", "doc_troubleshooting"],
        "aspects": ["网络因素", "文档数量", "并发负载", "优化建议"],
        "category": "troubleshooting",
        "difficulty": "medium"
    },
    {
        "id": "trouble_003",
        "question": "为什么AI回答的内容与文档不符？",
        "expected_answer": "可能是检索召回的文档不相关，或者提问方式不够精确。建议重新组织问题、使用更具体的关键词、或手动选择参考文档。",
        "relevant_doc_ids": ["doc_rag_quality", "doc_best_practices"],
        "aspects": ["检索问题", "问题优化", "关键词", "文档选择"],
        "category": "troubleshooting",
        "difficulty": "hard"
    },
    {
        "id": "trouble_004",
        "question": "登录后显示'Token过期'怎么解决？",
        "expected_answer": "Token默认30分钟过期，需要重新登录。可以在设置中开启'保持登录'功能延长有效期。",
        "relevant_doc_ids": ["doc_authentication", "doc_security"],
        "aspects": ["Token机制", "过期时间", "重新登录", "保持登录"],
        "category": "troubleshooting",
        "difficulty": "easy"
    },
    {
        "id": "trouble_005",
        "question": "文档向量化一直在处理中是什么情况？",
        "expected_answer": "可能是文档过大或队列繁忙。一般10MB以内的文档在5分钟内完成，超时请刷新页面或联系管理员查看后台日志。",
        "relevant_doc_ids": ["doc_document_processing", "doc_troubleshooting"],
        "aspects": ["处理时间", "文档大小", "队列状态", "超时处理"],
        "category": "troubleshooting",
        "difficulty": "medium"
    },

    # 4. 概念理解类 (Conceptual)
    {
        "id": "concept_001",
        "question": "什么是RAG检索增强生成？",
        "expected_answer": "RAG是一种AI技术，将文档检索与大语言模型结合，先从知识库检索相关内容，再生成准确答案，提高回答的可信度和时效性。",
        "relevant_doc_ids": ["doc_rag_introduction", "doc_technical_concepts"],
        "aspects": ["检索", "生成", "知识库", "准确性"],
        "category": "conceptual",
        "difficulty": "medium"
    },
    {
        "id": "concept_002",
        "question": "向量数据库是如何工作的？",
        "expected_answer": "向量数据库将文本转换为高维向量存储，通过计算向量相似度实现语义搜索，相比关键词匹配能更好理解语义相关性。",
        "relevant_doc_ids": ["doc_vector_database", "doc_embeddings"],
        "aspects": ["向量化", "相似度计算", "语义搜索", "关键词对比"],
        "category": "conceptual",
        "difficulty": "hard"
    },
    {
        "id": "concept_003",
        "question": "文档分块的作用是什么？",
        "expected_answer": "将长文档分成小块便于检索和处理，提高检索精准度，同时避免超出模型上下文窗口限制。",
        "relevant_doc_ids": ["doc_chunking", "doc_document_processing"],
        "aspects": ["检索精准", "处理效率", "上下文限制", "块大小"],
        "category": "conceptual",
        "difficulty": "medium"
    },
    {
        "id": "concept_004",
        "question": "系统中的权限角色有什么区别？",
        "expected_answer": "管理员可以管理项目和成员、编辑者可以上传修改文档、查看者只能查看和对话，不同角色权限逐级递减。",
        "relevant_doc_ids": ["doc_rbac", "doc_roles"],
        "aspects": ["管理员", "编辑者", "查看者", "权限层级"],
        "category": "conceptual",
        "difficulty": "easy"
    },
    {
        "id": "concept_005",
        "question": "什么是上下文窗口？",
        "expected_answer": "上下文窗口是AI模型一次能处理的文本量限制，GPT-4约为8K-32K tokens，超出需要分段处理或总结。",
        "relevant_doc_ids": ["doc_llm_concepts", "doc_technical_limits"],
        "aspects": ["处理限制", "Token数量", "分段处理", "模型差异"],
        "category": "conceptual",
        "difficulty": "hard"
    },

    # 5. 对比分析类 (Comparison)
    {
        "id": "compare_001",
        "question": "FieldMind和传统搜索引擎有什么不同？",
        "expected_answer": "传统搜索返回链接列表需要人工筛选，FieldMind通过RAG直接生成答案并提供来源引用，更智能高效。",
        "relevant_doc_ids": ["doc_features", "doc_advantages"],
        "aspects": ["搜索方式", "结果形式", "智能程度", "效率对比"],
        "category": "comparison",
        "difficulty": "medium"
    },
    {
        "id": "compare_002",
        "question": "免费版和专业版的主要区别是什么？",
        "expected_answer": "免费版限制5个项目、单项目10个文档、无API访问；专业版无限项目、单项目1000文档、提供API和优先支持。",
        "relevant_doc_ids": ["doc_pricing", "doc_plans"],
        "aspects": ["项目限制", "文档数量", "API访问", "支持服务"],
        "category": "comparison",
        "difficulty": "easy"
    },
    {
        "id": "compare_003",
        "question": "GPT-4和GPT-3.5在系统中的表现差异？",
        "expected_answer": "GPT-4理解能力更强、准确率更高、支持更长上下文，但响应速度略慢、成本更高；GPT-3.5速度快、成本低但准确性稍差。",
        "relevant_doc_ids": ["doc_model_comparison", "doc_performance"],
        "aspects": ["理解能力", "准确率", "响应速度", "成本"],
        "category": "comparison",
        "difficulty": "hard"
    },
    {
        "id": "compare_004",
        "question": "本地部署和云服务版本有什么区别？",
        "expected_answer": "本地部署数据完全私有、可定制化强，但需要自行维护；云服务即开即用、自动更新，但数据存储在云端。",
        "relevant_doc_ids": ["doc_deployment", "doc_cloud_vs_onprem"],
        "aspects": ["数据隐私", "定制能力", "维护成本", "使用便捷性"],
        "category": "comparison",
        "difficulty": "medium"
    },
    {
        "id": "compare_005",
        "question": "文档分块的Token模式和段落模式哪个更好？",
        "expected_answer": "Token模式保证固定长度、处理均匀，段落模式保持语义完整、更符合阅读习惯，建议结合文档类型选择。",
        "relevant_doc_ids": ["doc_chunking_strategies", "doc_best_practices"],
        "aspects": ["长度控制", "语义完整", "处理效率", "适用场景"],
        "category": "comparison",
        "difficulty": "hard"
    },

    # 6. 最佳实践类 (Best Practices)
    {
        "id": "practice_001",
        "question": "如何提高AI回答的准确性？",
        "expected_answer": "上传高质量文档、使用清晰具体的提问、合理设置检索数量、定期更新知识库内容。",
        "relevant_doc_ids": ["doc_best_practices", "doc_optimization"],
        "aspects": ["文档质量", "提问技巧", "检索配置", "内容更新"],
        "category": "best_practice",
        "difficulty": "medium"
    },
    {
        "id": "practice_002",
        "question": "如何组织项目文档结构？",
        "expected_answer": "按主题分类创建文件夹、使用统一命名规范、添加描述性元数据、定期清理过期文档。",
        "relevant_doc_ids": ["doc_document_organization", "doc_best_practices"],
        "aspects": ["分类方法", "命名规范", "元数据", "维护策略"],
        "category": "best_practice",
        "difficulty": "medium"
    },
    {
        "id": "practice_003",
        "question": "大型文档上传前需要注意什么？",
        "expected_answer": "检查文件完整性、移除敏感信息、压缩图片减小体积、考虑拆分超大文档、选择非高峰时段上传。",
        "relevant_doc_ids": ["doc_file_upload_tips", "doc_best_practices"],
        "aspects": ["文件检查", "信息安全", "体积优化", "拆分策略", "时间选择"],
        "category": "best_practice",
        "difficulty": "hard"
    },
    {
        "id": "practice_004",
        "question": "如何设计有效的提示词？",
        "expected_answer": "明确角色定位、提供清晰指令、给出具体示例、限定输出格式、设置必要约束条件。",
        "relevant_doc_ids": ["doc_prompt_engineering", "doc_ai_usage"],
        "aspects": ["角色设定", "指令清晰", "示例引导", "格式控制", "约束条件"],
        "category": "best_practice",
        "difficulty": "hard"
    },
    {
        "id": "practice_005",
        "question": "团队协作时如何避免冲突？",
        "expected_answer": "明确成员角色和权限、建立文档命名规范、使用版本控制功能、定期同步更新信息。",
        "relevant_doc_ids": ["doc_team_collaboration", "doc_conflict_resolution"],
        "aspects": ["角色权限", "命名规范", "版本控制", "信息同步"],
        "category": "best_practice",
        "difficulty": "medium"
    },

    # 7. 集成API类 (API)
    {
        "id": "api_001",
        "question": "如何获取API访问令牌？",
        "expected_answer": "在个人设置-API密钥页面点击'生成新密钥'，保存好密钥后在请求头中使用Bearer认证。",
        "relevant_doc_ids": ["doc_api_authentication", "doc_api_getting_started"],
        "aspects": ["设置页面", "密钥生成", "密钥保存", "Bearer认证"],
        "category": "api",
        "difficulty": "medium"
    },
    {
        "id": "api_002",
        "question": "API的速率限制是多少？",
        "expected_answer": "免费用户每分钟60次请求，专业版每分钟300次，企业版可定制。超限返回429状态码。",
        "relevant_doc_ids": ["doc_api_limits", "doc_rate_limiting"],
        "aspects": ["免费限制", "专业版", "企业定制", "错误处理"],
        "category": "api",
        "difficulty": "easy"
    },
    {
        "id": "api_003",
        "question": "如何通过API上传文档？",
        "expected_answer": "使用POST /api/v1/documents端点，multipart/form-data格式上传文件，需要在header中提供token和project_id。",
        "relevant_doc_ids": ["doc_api_reference", "doc_file_upload_api"],
        "aspects": ["POST方法", "端点路径", "数据格式", "必需参数"],
        "category": "api",
        "difficulty": "medium"
    },
    {
        "id": "api_004",
        "question": "API响应的错误码分别代表什么？",
        "expected_answer": "400参数错误、401未认证、403权限不足、404资源不存在、429请求过多、500服务器错误。",
        "relevant_doc_ids": ["doc_api_errors", "doc_http_status"],
        "aspects": ["客户端错误", "认证错误", "权限错误", "资源错误", "服务器错误"],
        "category": "api",
        "difficulty": "medium"
    },
    {
        "id": "api_005",
        "question": "如何使用Webhook接收文档处理完成通知？",
        "expected_answer": "在项目设置中配置Webhook URL，文档处理完成后系统会POST通知到该地址，包含文档ID和处理状态。",
        "relevant_doc_ids": ["doc_webhooks", "doc_notifications"],
        "aspects": ["配置方法", "通知触发", "POST请求", "通知内容"],
        "category": "api",
        "difficulty": "hard"
    },

    # 8. 高级功能类 (Advanced)
    {
        "id": "advanced_001",
        "question": "如何配置自定义的向量模型？",
        "expected_answer": "在系统设置-高级配置中选择'自定义嵌入模型'，可以配置HuggingFace模型或本地部署的模型API端点。",
        "relevant_doc_ids": ["doc_advanced_config", "doc_custom_embeddings"],
        "aspects": ["高级配置", "模型选择", "HuggingFace", "API配置"],
        "category": "advanced",
        "difficulty": "hard"
    },
    {
        "id": "advanced_002",
        "question": "如何实现跨项目的文档搜索？",
        "expected_answer": "使用全局搜索功能或API的multi_project参数，需要有相应项目的访问权限，结果会标注来源项目。",
        "relevant_doc_ids": ["doc_search_features", "doc_multi_project"],
        "aspects": ["全局搜索", "API参数", "权限要求", "结果标注"],
        "category": "advanced",
        "difficulty": "hard"
    },
    {
        "id": "advanced_003",
        "question": "如何集成企业SSO单点登录？",
        "expected_answer": "企业版支持SAML 2.0和OAuth 2.0协议，需要配置IdP元数据URL、证书，并在企业管理后台启用SSO。",
        "relevant_doc_ids": ["doc_sso_integration", "doc_enterprise_features"],
        "aspects": ["协议支持", "配置步骤", "证书管理", "企业版"],
        "category": "advanced",
        "difficulty": "hard"
    },
    {
        "id": "advanced_004",
        "question": "如何实现对话上下文的持久化存储？",
        "expected_answer": "系统自动保存对话历史，可通过API导出为JSON格式，或在设置中配置自动备份到云存储服务。",
        "relevant_doc_ids": ["doc_conversation_storage", "doc_backup"],
        "aspects": ["自动保存", "导出功能", "JSON格式", "云备份"],
        "category": "advanced",
        "difficulty": "medium"
    },
    {
        "id": "advanced_005",
        "question": "如何优化大规模文档的检索性能？",
        "expected_answer": "使用向量索引优化、启用缓存机制、配置文档预加载、调整检索参数、考虑使用专用向量数据库如Milvus。",
        "relevant_doc_ids": ["doc_performance_tuning", "doc_scaling"],
        "aspects": ["索引优化", "缓存机制", "预加载", "参数调整", "数据库选择"],
        "category": "advanced",
        "difficulty": "hard"
    },

    # 9. 边界情况类 (Edge Cases)
    {
        "id": "edge_001",
        "question": "上传空文档会发生什么？",
        "expected_answer": "系统会检测空文档并拒绝上传，返回'文档内容为空'的错误提示，不会创建文档记录。",
        "relevant_doc_ids": ["doc_validation", "doc_error_handling"],
        "aspects": ["内容检测", "上传拒绝", "错误提示", "记录创建"],
        "category": "edge_case",
        "difficulty": "easy"
    },
    {
        "id": "edge_002",
        "question": "对话历史超过上下文窗口限制怎么办？",
        "expected_answer": "系统会自动总结早期对话内容，保留最近的完整对话和历史摘要，确保上下文连贯性。",
        "relevant_doc_ids": ["doc_context_management", "doc_conversation_flow"],
        "aspects": ["自动总结", "内容保留", "摘要机制", "连贯性"],
        "category": "edge_case",
        "difficulty": "hard"
    },
    {
        "id": "edge_003",
        "question": "同时上传多个重名文档会怎样？",
        "expected_answer": "系统会自动在文件名后添加序号(如doc.pdf、doc(1).pdf)，每个文档保持独立ID，不会覆盖。",
        "relevant_doc_ids": ["doc_file_naming", "doc_conflict_handling"],
        "aspects": ["重名处理", "序号添加", "独立ID", "覆盖避免"],
        "category": "edge_case",
        "difficulty": "medium"
    },
    {
        "id": "edge_004",
        "question": "网络中断时已上传一半的文档怎么办？",
        "expected_answer": "支持断点续传功能，重新上传时会从中断点继续，超过24小时未完成的上传会自动清理。",
        "relevant_doc_ids": ["doc_upload_resilience", "doc_network_handling"],
        "aspects": ["断点续传", "中断恢复", "超时清理", "24小时"],
        "category": "edge_case",
        "difficulty": "medium"
    },
    {
        "id": "edge_005",
        "question": "AI回答中包含多种语言如何处理？",
        "expected_answer": "系统支持多语言文档和查询，AI会根据问题语言回答，混合语言文档会标注语言类型并保持原语言引用。",
        "relevant_doc_ids": ["doc_multilingual", "doc_language_handling"],
        "aspects": ["多语言支持", "语言识别", "混合处理", "引用保持"],
        "category": "edge_case",
        "difficulty": "hard"
    },

    # 10. 性能优化类 (Performance)
    {
        "id": "perf_001",
        "question": "如何加快文档搜索速度？",
        "expected_answer": "减少检索数量(top_k参数)、使用元数据过滤缩小范围、启用查询缓存、定期清理无用文档。",
        "relevant_doc_ids": ["doc_performance", "doc_search_optimization"],
        "aspects": ["参数调整", "元数据过滤", "缓存启用", "文档清理"],
        "category": "performance",
        "difficulty": "medium"
    },
    {
        "id": "perf_002",
        "question": "批量上传文档有什么优化建议？",
        "expected_answer": "使用API批量接口、设置合理的并发数(建议5-10)、非高峰期处理、考虑压缩包方式上传。",
        "relevant_doc_ids": ["doc_batch_upload", "doc_optimization"],
        "aspects": ["批量接口", "并发控制", "时间选择", "压缩上传"],
        "category": "performance",
        "difficulty": "hard"
    },
    {
        "id": "perf_003",
        "question": "缓存命中率低怎么优化？",
        "expected_answer": "分析常见查询模式、预热热门文档、调整缓存TTL时间、增加缓存容量、使用Redis持久化。",
        "relevant_doc_ids": ["doc_cache_optimization", "doc_redis_config"],
        "aspects": ["查询分析", "预热策略", "TTL调整", "容量扩展", "持久化"],
        "category": "performance",
        "difficulty": "hard"
    },
    {
        "id": "perf_004",
        "question": "数据库查询慢有哪些优化方法？",
        "expected_answer": "添加索引、优化查询语句、启用连接池、读写分离、定期清理历史数据、考虑分库分表。",
        "relevant_doc_ids": ["doc_database_optimization", "doc_scaling"],
        "aspects": ["索引优化", "SQL优化", "连接池", "读写分离", "数据清理", "分库分表"],
        "category": "performance",
        "difficulty": "hard"
    },
    {
        "id": "perf_005",
        "question": "并发用户数增加时如何保证响应速度？",
        "expected_answer": "增加worker进程数、启用负载均衡、使用CDN加速静态资源、实施请求队列、考虑水平扩展。",
        "relevant_doc_ids": ["doc_concurrency", "doc_scaling_strategy"],
        "aspects": ["进程扩展", "负载均衡", "CDN", "请求队列", "水平扩展"],
        "category": "performance",
        "difficulty": "hard"
    }
]


def generate_test_dataset():
    """生成测试数据集JSON文件"""
    import json
    from datetime import datetime

    dataset = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "description": "FieldMind RAG系统标准测试集 - 50个测试用例覆盖10个类别",
        "categories": {
            "factual": "事实查询类",
            "howto": "操作指导类",
            "troubleshooting": "故障排查类",
            "conceptual": "概念理解类",
            "comparison": "对比分析类",
            "best_practice": "最佳实践类",
            "api": "集成API类",
            "advanced": "高级功能类",
            "edge_case": "边界情况类",
            "performance": "性能优化类"
        },
        "difficulties": {
            "easy": "简单 - 单一事实查询",
            "medium": "中等 - 需要理解和综合",
            "hard": "困难 - 复杂概念或多步骤"
        },
        "statistics": {
            "total": len(SAMPLE_TEST_CASES),
            "by_category": {},
            "by_difficulty": {}
        },
        "test_cases": SAMPLE_TEST_CASES
    }

    # 统计
    for tc in SAMPLE_TEST_CASES:
        cat = tc["category"]
        diff = tc["difficulty"]
        dataset["statistics"]["by_category"][cat] = dataset["statistics"]["by_category"].get(cat, 0) + 1
        dataset["statistics"]["by_difficulty"][diff] = dataset["statistics"]["by_difficulty"].get(diff, 0) + 1

    return dataset


if __name__ == "__main__":
    dataset = generate_test_dataset()

    # 保存到文件
    output_path = "test_datasets/fieldmind_rag_test_v1.json"
    import os
    os.makedirs("test_datasets", exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"✅ 测试数据集已生成: {output_path}")
    print(f"📊 总用例数: {dataset['statistics']['total']}")
    print(f"📂 类别分布: {dataset['statistics']['by_category']}")
    print(f"⚡ 难度分布: {dataset['statistics']['by_difficulty']}")
