"""
统一文档处理工具包

提供统一的文档处理流水线，整合多个版本的功能
"""

from .unified_document_pipeline import (
    UnifiedDocumentPipeline,
    create_document_pipeline,
    process_single_document,
    DocumentProcessingError,
    ExtractionError,
    ChunkingError,
    VectorizationError,
    StorageError
)

from .unified_document_converter import (
    UnifiedDocumentConverter,
    ConversionStrategy,
    ConversionQuality,
    ConversionResult,
    ConversionError,
    create_converter,
    convert_document,
    batch_convert_documents
)

from .unified_document_chunker import (
    UnifiedDocumentChunker,
    ChunkStrategy,
    ChunkQuality,
    ChunkResult,
    create_chunker,
    chunk_document,
    batch_chunk_documents
)

__all__ = [
    # Pipeline
    'UnifiedDocumentPipeline',
    'create_document_pipeline',
    'process_single_document',
    'DocumentProcessingError',
    'ExtractionError',
    'ChunkingError',
    'VectorizationError',
    'StorageError',
    # Converter
    'UnifiedDocumentConverter',
    'ConversionStrategy',
    'ConversionQuality',
    'ConversionResult',
    'ConversionError',
    'create_converter',
    'convert_document',
    'batch_convert_documents',
    # Chunker
    'UnifiedDocumentChunker',
    'ChunkStrategy',
    'ChunkQuality',
    'ChunkResult',
    'create_chunker',
    'chunk_document',
    'batch_chunk_documents',
]
