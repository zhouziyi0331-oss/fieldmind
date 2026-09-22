"""
RAG模块

统一的RAG系统，整合多个RAG提供者
"""
from app.core.rag.base_interface import (
    BaseRAGInterface,
    RAGQuery,
    RAGResult,
    RAGResponse,
    RAGMode,
    QueryType,
    RAGProviderConfig,
    RAGException,
    RAGProviderNotFoundError,
    RAGQueryError,
    RAGIngestionError
)

from app.core.rag.router import (
    RAGRouter,
    RoutingStrategy,
    get_rag_router
)

from app.core.rag.unified_engine import (
    UnifiedRAGEngine,
    get_unified_rag_engine
)

__all__ = [
    # 基础接口
    'BaseRAGInterface',
    'RAGQuery',
    'RAGResult',
    'RAGResponse',
    'RAGMode',
    'QueryType',
    'RAGProviderConfig',

    # 异常
    'RAGException',
    'RAGProviderNotFoundError',
    'RAGQueryError',
    'RAGIngestionError',

    # 路由器
    'RAGRouter',
    'RoutingStrategy',
    'get_rag_router',

    # 统一引擎
    'UnifiedRAGEngine',
    'get_unified_rag_engine'
]
