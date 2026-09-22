"""
RAG适配器模块

适配各种RAG提供者到统一接口
"""
from app.core.rag.adapters.base_rag_adapter import (
    BaseRAGAdapter,
    create_base_rag_adapter
)

from app.core.rag.adapters.lightrag_adapter import (
    LightRAGAdapter,
    create_lightrag_adapter
)

from app.core.rag.adapters.graphrag_adapter import (
    GraphRAGAdapter,
    create_graphrag_adapter
)

__all__ = [
    'BaseRAGAdapter',
    'create_base_rag_adapter',
    'LightRAGAdapter',
    'create_lightrag_adapter',
    'GraphRAGAdapter',
    'create_graphrag_adapter'
]
