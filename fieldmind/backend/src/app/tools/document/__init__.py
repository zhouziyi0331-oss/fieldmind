"""文档工具兼容入口，统一复用当前主文档服务。"""

from app.services.document_converter import DocumentConverter
from app.services.document_chunker import DocumentChunker

UnifiedDocumentConverter = DocumentConverter
UnifiedDocumentChunker = DocumentChunker

__all__ = [
    "DocumentConverter",
    "DocumentChunker",
    "UnifiedDocumentConverter",
    "UnifiedDocumentChunker",
]
