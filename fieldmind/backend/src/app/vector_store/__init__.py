"""
向量存储模块

提供统一的向量存储抽象接口和多种后端实现
"""

from .base import (
    VectorStore,
    Document,
    SearchResult,
    DistanceMetric,
    IndexType,
)

__all__ = [
    "VectorStore",
    "Document",
    "SearchResult",
    "DistanceMetric",
    "IndexType",
]

__version__ = "0.1.0"
