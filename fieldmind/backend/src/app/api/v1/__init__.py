"""API v1模块初始化"""
from . import (
    audio, documents, search, rag, workflows,
    auth, crawler, skills, industry, reports,
    projects, project_chat, project_documents, enhanced_chat,
    knowledge_graph_enhanced, knowledge_network, data_enrichment
    # business_analysis,  # 临时禁用 - 缺少 app.config.business_database 模块
)

__all__ = [
    "audio", "documents", "search", "rag", "workflows",
    "auth", "crawler", "skills", "industry", "reports",
    "projects", "project_chat", "project_documents", "enhanced_chat",
    "knowledge_graph_enhanced", "knowledge_network", "data_enrichment"
    # "business_analysis",  # 临时禁用
]
