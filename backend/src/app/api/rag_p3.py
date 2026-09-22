"""
RAG (Retrieval-Augmented Generation) API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.rag import (
    RAGService,
    VectorStore,
    EmbeddingService,
    ChunkingService
)

router = APIRouter(prefix="/rag", tags=["rag"])

# 全局 RAG 服务实例
_vector_store = VectorStore(embedding_dim=768)
_embedding_service = EmbeddingService()
_rag_service = RAGService(_vector_store, _embedding_service)


# Request/Response Models
class IndexDocumentRequest(BaseModel):
    doc_id: str = Field(..., description="文档 ID")
    content: str = Field(..., description="文档内容")
    metadata: dict = Field(default_factory=dict, description="元数据")
    chunk: bool = Field(False, description="是否分块")
    chunk_method: str = Field("tokens", description="分块方法 (tokens/paragraphs/sentences)")


class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    top_k: int = Field(5, ge=1, le=50, description="返回数量")
    filter_metadata: Optional[dict] = Field(None, description="元数据过滤")


class GenerateRequest(BaseModel):
    query: str = Field(..., description="查询问题")
    top_k: int = Field(3, ge=1, le=10, description="检索文档数")
    llm_provider: str = Field("openai", description="LLM 提供商")
    model: str = Field("gpt-3.5-turbo", description="模型名称")


@router.post("/index")
async def index_document(
    request: IndexDocumentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    索引文档

    支持自动分块处理长文档
    """
    try:
        if request.chunk:
            # 分块处理
            if request.chunk_method == "tokens":
                chunks = ChunkingService.chunk_by_tokens(request.content)
            elif request.chunk_method == "paragraphs":
                chunks = ChunkingService.chunk_by_paragraphs(request.content)
            elif request.chunk_method == "sentences":
                chunks = ChunkingService.chunk_by_sentences(request.content)
            else:
                raise ValueError(f"Unknown chunk method: {request.chunk_method}")

            # 索引每个块
            documents = []
            for i, chunk in enumerate(chunks):
                doc = await _rag_service.index_document(
                    doc_id=f"{request.doc_id}_chunk_{i}",
                    content=chunk,
                    metadata={
                        **request.metadata,
                        "parent_doc_id": request.doc_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc.to_dict())

            return {
                "status": "success",
                "documents": documents,
                "chunks": len(chunks)
            }
        else:
            # 不分块，直接索引
            document = await _rag_service.index_document(
                doc_id=request.doc_id,
                content=request.content,
                metadata=request.metadata
            )

            return {
                "status": "success",
                "document": document.to_dict()
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/search")
async def search_documents(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    搜索相关文档

    使用向量相似度搜索
    """
    try:
        results = await _rag_service.search(
            query=request.query,
            top_k=request.top_k,
            filter_metadata=request.filter_metadata
        )

        return {
            "query": request.query,
            "results": [result.to_dict() for result in results],
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate")
async def generate_with_rag(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    检索增强生成

    结合检索和 LLM 生成回答
    """
    try:
        result = await _rag_service.generate_with_context(
            query=request.query,
            top_k=request.top_k,
            llm_provider=request.llm_provider,
            model=request.model
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除文档"""
    success = await _rag_service.delete_document(doc_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )

    return {"message": "Document deleted successfully"}


@router.get("/statistics")
async def get_statistics(current_user: User = Depends(get_current_user)):
    """获取 RAG 统计信息"""
    return _rag_service.get_statistics()
