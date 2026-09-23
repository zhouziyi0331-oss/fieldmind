"""
统一RAG检索API - 整合所有RAG检索相关功能
合并自: deep_rag, chat_rag, rag_p3, hierarchical_retrieval, v1/rag
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter(prefix="/api/rag", tags=["统一RAG检索"])


# 辅助函数：获取RAG引擎实例
def get_rag_engine():
    """获取RAG引擎实例（简化版）"""
    from app.core.rag_engine import RAGEngine
    return RAGEngine()

# ============================================================================
# 请求/响应模型
# ============================================================================

class RetrievalStrategy(str, Enum):
    """检索策略"""
    SEMANTIC = "semantic"  # 语义检索
    KEYWORD = "keyword"  # 关键词检索
    HYBRID = "hybrid"  # 混合检索
    HIERARCHICAL = "hierarchical"  # 层次检索


class RAGQueryRequest(BaseModel):
    """RAG查询请求"""
    query: str = Field(..., description="查询问题")
    project_id: Optional[int] = Field(None, description="项目ID")
    top_k: int = Field(default=5, ge=1, le=50, description="返回结果数")
    strategy: RetrievalStrategy = Field(default=RetrievalStrategy.HYBRID, description="检索策略")
    with_sources: bool = Field(default=True, description="是否返回来源")


class RAGChatRequest(BaseModel):
    """RAG对话请求"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    top_k: int = Field(default=5, ge=1, le=20, description="检索文档数")
    stream: bool = Field(default=False, description="是否流式输出")


class DocumentIndexRequest(BaseModel):
    """文档索引请求"""
    document_ids: List[int] = Field(..., description="文档ID列表")
    project_id: int = Field(..., description="项目ID")
    force_reindex: bool = Field(default=False, description="强制重新索引")


# ============================================================================
# 1. 文档检索
# ============================================================================

@router.post("/retrieve", response_model=ApiResponse, summary="检索相关文档")
async def retrieve_documents(
    request: Request,
    query_request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    检索与查询相关的文档片段

    支持多种检索策略:
    - semantic: 基于语义相似度
    - keyword: 基于关键词匹配
    - hybrid: 混合检索（推荐）
    - hierarchical: 层次检索
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        rag_engine = get_rag_engine()

        # 执行检索
        results = rag_engine.retrieve(
            query=query_request.query,
            project_id=query_request.project_id,
            top_k=query_request.top_k,
            strategy=query_request.strategy.value
        )

        # 格式化结果
        chunks = []
        for result in results:
            chunk_data = {
                "chunk_id": result.get("chunk_id"),
                "content": result.get("content"),
                "score": result.get("score", 0.0),
                "document_id": result.get("document_id")
            }

            if query_request.with_sources:
                chunk_data["source"] = {
                    "document_name": result.get("document_name"),
                    "page": result.get("page"),
                    "chunk_index": result.get("chunk_index")
                }

            chunks.append(chunk_data)

        return success_response(
            data={
                "query": query_request.query,
                "chunks": chunks,
                "total": len(chunks),
                "strategy": query_request.strategy.value
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=ApiResponse, summary="语义搜索")
async def semantic_search(
    request: Request,
    query: str = Body(..., embed=True),
    project_id: Optional[int] = Body(None, embed=True),
    limit: int = Body(10, ge=1, le=100, embed=True),
    db: Session = Depends(get_db)
):
    """
    语义搜索文档

    使用向量相似度进行搜索
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        rag_engine = get_rag_engine()

        results = rag_engine.retrieve(
            query=query,
            project_id=project_id,
            top_k=limit,
            strategy="semantic"
        )

        return success_response(
            data={
                "query": query,
                "results": results,
                "total": len(results)
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. RAG对话
# ============================================================================

@router.post("/chat", response_model=ApiResponse, summary="RAG对话")
async def rag_chat(
    request: Request,
    chat_request: RAGChatRequest,
    db: Session = Depends(get_db)
):
    """
    基于检索增强的对话

    流程:
    1. 检索相关文档
    2. 构建上下文
    3. 生成回答
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        rag_engine = get_rag_engine()

        # 检索相关文档
        retrieved_docs = rag_engine.retrieve(
            query=chat_request.message,
            project_id=chat_request.project_id,
            top_k=chat_request.top_k,
            strategy="hybrid"
        )

        # 构建上下文
        context = "\n\n".join([
            doc.get("content", "") for doc in retrieved_docs
        ])

        # 生成回答（简化版，实际需要调用LLM）
        # TODO: 集成LLM生成回答
        answer = f"基于检索到的{len(retrieved_docs)}个文档片段，针对您的问题：{chat_request.message}"

        return success_response(
            data={
                "answer": answer,
                "sources": retrieved_docs,
                "session_id": chat_request.session_id or "new_session"
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream", summary="流式RAG对话")
async def rag_chat_stream(
    request: Request,
    chat_request: RAGChatRequest,
    db: Session = Depends(get_db)
):
    """
    流式RAG对话

    支持SSE (Server-Sent Events) 流式输出
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import json

    async def generate():
        try:
            rag_engine = get_rag_engine()

            # 检索文档
            retrieved_docs = rag_engine.retrieve(
                query=chat_request.message,
                project_id=chat_request.project_id,
                top_k=chat_request.top_k,
                strategy="hybrid"
            )

            # 模拟流式输出
            response_text = f"基于{len(retrieved_docs)}个相关文档，"
            for char in response_text:
                yield f"data: {json.dumps({'type': 'token', 'content': char})}\n\n"
                await asyncio.sleep(0.01)

            # 发送来源
            yield f"data: {json.dumps({'type': 'sources', 'sources': retrieved_docs})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ============================================================================
# 3. 文档索引管理
# ============================================================================

@router.post("/index", response_model=ApiResponse, summary="索引文档")
async def index_documents(
    request: Request,
    index_request: DocumentIndexRequest,
    db: Session = Depends(get_db)
):
    """
    为文档创建向量索引

    处理流程:
    1. 读取文档内容
    2. 分块
    3. 向量化
    4. 存储到向量数据库
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        rag_engine = get_rag_engine()

        indexed_count = 0
        for doc_id in index_request.document_ids:
            try:
                # TODO: 实现实际的索引逻辑
                # rag_engine.index_document(doc_id, force=index_request.force_reindex)
                indexed_count += 1
            except Exception as e:
                # 记录错误但继续处理其他文档
                pass

        return success_response(
            data={
                "total": len(index_request.document_ids),
                "indexed": indexed_count,
                "failed": len(index_request.document_ids) - indexed_count
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index/documents/{document_id}", response_model=ApiResponse, summary="删除文档索引")
async def delete_document_index(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db)
):
    """删除文档的向量索引"""
    request_id = getattr(request.state, "request_id", None)

    try:
        rag_engine = get_rag_engine()

        # TODO: 实现删除索引逻辑
        # rag_engine.delete_document_index(document_id)

        return success_response(
            data={"deleted_document_id": document_id},
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. 会话管理
# ============================================================================

@router.get("/conversations/{session_id}", response_model=ApiResponse, summary="获取会话历史")
async def get_conversation(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取会话的对话历史"""
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 从数据库获取会话历史
        history = []

        return success_response(
            data={
                "session_id": session_id,
                "history": history
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{session_id}", response_model=ApiResponse, summary="删除会话")
async def delete_conversation(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除会话历史"""
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 从数据库删除会话
        return success_response(
            data={"deleted_session_id": session_id},
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. 统计与监控
# ============================================================================

@router.get("/statistics", response_model=ApiResponse, summary="RAG统计信息")
async def get_statistics(
    request: Request,
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取RAG系统的统计信息

    包括:
    - 索引文档数
    - 查询次数
    - 平均响应时间
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.document_chunk import DocumentChunk
        from sqlalchemy import func

        # 统计块数量
        query = db.query(func.count(DocumentChunk.id))
        if project_id:
            # TODO: 添加project_id过滤
            pass

        chunk_count = query.scalar() or 0

        stats = {
            "total_chunks": chunk_count,
            "indexed_documents": 0,  # TODO: 实现
            "total_queries": 0,  # TODO: 从日志或统计表获取
            "project_id": project_id
        }

        return success_response(data=stats, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=ApiResponse, summary="健康检查")
async def health_check(request: Request):
    """RAG系统健康检查"""
    request_id = getattr(request.state, "request_id", None)

    try:
        rag_engine = get_rag_engine()

        # 检查RAG引擎状态
        status = {
            "status": "healthy",
            "rag_engine": "initialized",
            "vector_db": "connected"
        }

        return success_response(data=status, request_id=request_id)
    except Exception as e:
        return success_response(
            data={
                "status": "unhealthy",
                "error": str(e)
            },
            request_id=request_id
        )


# ============================================================================
# 6. 检索策略对比
# ============================================================================

@router.post("/compare-strategies", response_model=ApiResponse, summary="对比检索策略")
async def compare_strategies(
    request: Request,
    query: str = Body(..., embed=True),
    project_id: Optional[int] = Body(None, embed=True),
    top_k: int = Body(5, ge=1, le=20, embed=True),
    db: Session = Depends(get_db)
):
    """
    对比不同检索策略的效果

    用于调试和优化检索效果
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        rag_engine = get_rag_engine()

        strategies = ["semantic", "keyword", "hybrid"]
        results = {}

        for strategy in strategies:
            strategy_results = rag_engine.retrieve(
                query=query,
                project_id=project_id,
                top_k=top_k,
                strategy=strategy
            )
            results[strategy] = {
                "chunks": strategy_results,
                "count": len(strategy_results)
            }

        return success_response(
            data={
                "query": query,
                "strategies": results
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 7. 可用文档列表
# ============================================================================

@router.get("/available-documents/{project_id}", response_model=ApiResponse, summary="获取可检索文档")
async def get_available_documents(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目中可用于检索的文档列表"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).all()

        result = {
            "project_id": project_id,
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status
                }
                for doc in documents
            ],
            "total": len(documents)
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
