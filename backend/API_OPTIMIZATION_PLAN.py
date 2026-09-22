#!/usr/bin/env python3
"""
FieldMind API优化方案
问题1: 26个未注册的API模块需要注册
问题2: 894个端点过多，需要合并优化
"""

# ============================================================================
# 问题1: 未注册API模块分析
# ============================================================================

UNREGISTERED_APIS = {
    "核心功能（必须注册）": [
        "memory",           # 记忆管理 - 对话系统核心
        "timeline",         # 时间线 - 知识图谱重要功能
        "tables",           # 表格处理 - 文档处理必需
        "proposal",         # 方案生成 - 业务功能
        "photos",           # 图片管理 - 多媒体支持
        "super_agents",     # 超级Agent - AI核心
        "agent_pipeline",   # Agent流水线 - 自动化
    ],

    "增强功能（建议注册）": [
        "topic_analysis",           # 主题分析
        "chunks_quantification",    # 块量化分析
        "kg_visualization",         # 知识图谱可视化
        "dashboard_optimized",      # 优化版Dashboard
        "file_summaries",           # 文件摘要
        "export_summaries",         # 导出摘要
        "query_api",               # 查询API
        "sop",                     # 标准作业程序
    ],

    "辅助功能（可选注册）": [
        "monitoring",              # 监控（已有monitoring_api）
        "websocket",               # WebSocket（已有websocket_events）
        "governance_validation",   # 治理验证
        "live_extraction_enhanced", # 实时提取增强版
        "api_docs_enhanced",       # API文档增强
        "file_management",         # 文件管理
        "tasks",                   # 任务管理
    ],

    "废弃功能（不需要注册）": [
        "learning_old",            # 旧版学习（已有新版）
        "workflows_old",           # 旧版工作流（已有新版）
    ],
}

# ============================================================================
# 问题2: API合并优化方案
# ============================================================================

API_CONSOLIDATION_PLAN = {
    "1. 知识图谱模块合并": {
        "现状": [
            "knowledge_graph.py (9端点)",
            "knowledge_graph_v3.py (6端点)",
            "knowledge_graph_p3.py (16端点)",
            "knowledge_graph_enhanced.py (9端点)",
            "knowledge_graph_api.py (6端点)",
            "experience_graph.py (3端点)",
            "kg_visualization.py (6端点)",
        ],
        "合并为": "unified_knowledge_graph.py",
        "端点数": "20-25个（减少50%）",
        "保留功能": [
            "构建图谱",
            "查询实体/关系",
            "可视化",
            "统计分析",
            "经验图谱",
            "交互式操作"
        ]
    },

    "2. 文档处理模块合并": {
        "现状": [
            "documents.py (18端点)",
            "document_processing.py (5端点)",
            "document_processing_v2.py (7端点)",
            "document_normalization.py (6端点)",
        ],
        "合并为": "unified_documents.py",
        "端点数": "15-20个（减少40%）",
        "保留功能": [
            "上传文档",
            "处理文档",
            "规范化",
            "查询文档",
            "批量操作"
        ]
    },

    "3. RAG检索模块合并": {
        "现状": [
            "deep_rag.py (10端点)",
            "chat_rag.py (3端点)",
            "rag_p3.py (5端点)",
            "hierarchical_retrieval.py (3端点)",
        ],
        "合并为": "unified_rag.py",
        "端点数": "8-12个（减少50%）",
        "保留功能": [
            "检索",
            "对话",
            "重排序",
            "层次检索",
            "统计"
        ]
    },

    "4. Agent系统合并": {
        "现状": [
            "agents_p3.py (15端点)",
            "super_agents.py (7端点)",
            "agent_pipeline.py (6端点)",
        ],
        "合并为": "unified_agents.py",
        "端点数": "12-15个（减少40%）",
        "保留功能": [
            "创建Agent",
            "执行任务",
            "管理生命周期",
            "流水线编排",
            "超级Agent"
        ]
    },

    "5. Dashboard分析合并": {
        "现状": [
            "dashboard.py (3端点)",
            "dashboard_v1.py (13端点)",
            "dashboard_optimized.py (5端点)",
            "analytics.py (5端点)",
        ],
        "合并为": "unified_dashboard.py",
        "端点数": "10-12个（减少50%）"
    },

    "6. 工作流模块合并": {
        "现状": [
            "workflows.py (9端点)",
            "workflows_v1.py (12端点)",
            "workflows_old.py (4端点)",
            "project_workflow.py (2端点)",
        ],
        "合并为": "unified_workflows.py",
        "端点数": "15-18个（减少40%）"
    },

    "7. 报告生成合并": {
        "现状": [
            "reports_real.py",
            "reports_refactored.py",
            "report_generation.py (6端点)",
            "reports.py (5端点)",
            "report_relations.py (12端点)",
        ],
        "合并为": "unified_reports.py",
        "端点数": "12-15个（减少50%）"
    },

    "8. 学习系统合并": {
        "现状": [
            "background_learning.py (6端点)",
            "learning.py (9端点)",
            "learning_old.py (6端点)",
            "hermes.py (9端点)",
        ],
        "合并为": "unified_learning.py",
        "端点数": "12-15个（减少50%）"
    },

    "9. 协作系统合并": {
        "现状": [
            "collaboration.py (7端点)",
            "collaboration_p3.py (5端点)",
        ],
        "合并为": "unified_collaboration.py",
        "端点数": "8-10个（减少30%）"
    },

    "10. 关键词系统合并": {
        "现状": [
            "keywords.py (11端点)",
            "keyword_search.py (3端点)",
            "keyword_network.py (7端点)",
        ],
        "合并为": "unified_keywords.py",
        "端点数": "10-12个（减少40%）"
    }
}

# ============================================================================
# 优化后的API架构
# ============================================================================

OPTIMIZED_API_STRUCTURE = {
    "核心模块 (10个)": [
        "unified_knowledge_graph.py",    # 知识图谱 (20端点)
        "unified_documents.py",          # 文档处理 (18端点)
        "unified_rag.py",                # RAG检索 (12端点)
        "unified_agents.py",             # Agent系统 (15端点)
        "unified_workflows.py",          # 工作流 (18端点)
        "unified_chat.py",               # 对话系统 (15端点)
        "unified_learning.py",           # 学习系统 (15端点)
        "unified_dashboard.py",          # 仪表盘 (12端点)
        "unified_reports.py",            # 报告生成 (15端点)
        "unified_collaboration.py",      # 协作系统 (10端点)
    ],

    "专业模块 (8个)": [
        "unified_keywords.py",           # 关键词 (12端点)
        "timeline.py",                   # 时间线 (5端点)
        "citations.py",                  # 引用 (7端点)
        "memory.py",                     # 记忆 (11端点)
        "tables.py",                     # 表格 (10端点)
        "photos.py",                     # 图片 (7端点)
        "ocr.py",                        # OCR (7端点)
        "audio.py",                      # 音频 (3端点)
    ],

    "管理模块 (6个)": [
        "auth.py",                       # 认证 (5端点)
        "projects.py",                   # 项目 (18端点)
        "permissions.py",                # 权限 (17端点)
        "audit.py",                      # 审计 (16端点)
        "monitoring.py",                 # 监控 (4端点)
        "health.py",                     # 健康检查 (5端点)
    ],

    "工具模块 (6个)": [
        "search.py",                     # 搜索 (1端点 + POST)
        "visualize.py",                  # 可视化 (10端点)
        "batch_operations.py",           # 批量操作 (6端点)
        "scheduler.py",                  # 调度器 (8端点)
        "export.py",                     # 导出 (合并export_summaries)
        "websocket.py",                  # WebSocket (11端点)
    ],
}

# ============================================================================
# 预期优化效果
# ============================================================================

OPTIMIZATION_RESULTS = {
    "优化前": {
        "API模块": 139,
        "API端点": 894,
        "平均每模块端点": 6.4,
    },

    "优化后": {
        "API模块": 30,
        "API端点": "400-450",
        "平均每模块端点": 13.5,
        "减少比例": "78% (模块), 50% (端点)",
    },

    "优势": [
        "✅ 结构更清晰，易于维护",
        "✅ 减少50%的API端点，降低复杂度",
        "✅ 统一的接口设计",
        "✅ 减少重复代码",
        "✅ 更好的版本管理",
        "✅ 文档更易维护",
        "✅ 前端调用更简单",
    ]
}

# ============================================================================
# 实施计划
# ============================================================================

IMPLEMENTATION_PLAN = {
    "阶段1: 注册未注册API (1天)": [
        "1. 注册7个核心功能API",
        "2. 注册8个增强功能API",
        "3. 更新路由配置",
        "4. 测试所有端点可访问",
    ],

    "阶段2: API合并 - 第一批 (3天)": [
        "1. 合并知识图谱模块",
        "2. 合并文档处理模块",
        "3. 合并RAG检索模块",
        "4. 保持向后兼容",
    ],

    "阶段3: API合并 - 第二批 (3天)": [
        "1. 合并Agent系统",
        "2. 合并工作流模块",
        "3. 合并Dashboard",
        "4. 合并报告生成",
    ],

    "阶段4: API合并 - 第三批 (2天)": [
        "1. 合并学习系统",
        "2. 合并协作系统",
        "3. 合并关键词系统",
        "4. 清理旧版本代码",
    ],

    "阶段5: 测试和文档 (2天)": [
        "1. 全面API测试",
        "2. 更新API文档",
        "3. 前端适配",
        "4. 性能测试",
    ],
}

if __name__ == "__main__":
    print("="*80)
    print("FieldMind API优化方案")
    print("="*80)

    print("\n问题1: 未注册API模块")
    print("-" * 80)
    for category, apis in UNREGISTERED_APIS.items():
        print(f"\n{category}:")
        for api in apis:
            print(f"  - {api}")

    print("\n\n问题2: API合并优化")
    print("-" * 80)
    for i, (name, plan) in enumerate(API_CONSOLIDATION_PLAN.items(), 1):
        print(f"\n{i}. {name}")
        print(f"   现状: {len(plan['现状'])}个模块")
        print(f"   合并为: {plan['合并为']}")
        print(f"   端点: {plan['端点数']}")

    print("\n\n优化效果预估")
    print("-" * 80)
    print(f"优化前: {OPTIMIZATION_RESULTS['优化前']['API模块']}个模块, "
          f"{OPTIMIZATION_RESULTS['优化前']['API端点']}个端点")
    print(f"优化后: {OPTIMIZATION_RESULTS['优化后']['API模块']}个模块, "
          f"{OPTIMIZATION_RESULTS['优化后']['API端点']}个端点")
    print(f"减少: {OPTIMIZATION_RESULTS['优化后']['减少比例']}")

    print("\n\n总耗时: 11天")
    print("="*80)
