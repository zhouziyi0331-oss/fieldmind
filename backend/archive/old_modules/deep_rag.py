"""
深度RAG对话API - Phase 3.6
Deep RAG Chat API Endpoints

提供统一的多源检索对话接口
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.services.deep_rag_service import get_deep_rag_service
from app.schemas.response import success_response, error_response

logger = logging.getLogger(__name__)
router = APIRouter()


# ========== Pydantic 请求模型 ==========

class DeepChatRequest(BaseModel):
    """深度对话请求"""
    query: str = Field(..., description="用户问题")
    session_id: str = Field(..., description="会话ID，用于多轮对话上下文")
    project_id: Optional[int] = Field(None, description="项目ID，限定检索范围")
    use_context: bool = Field(True, description="是否使用对话历史上下文")
    top_k: int = Field(5, ge=1, le=20, description="每个源返回的Top K结果")
    enabled_sources: Optional[List[str]] = Field(
        None,
        description="启用的检索源列表，如['vector', 'cognee', 'lightrag']，None则启用所有"
    )
    llm_provider: str = Field(
        'anthropic',
        description="LLM提供商: 'anthropic', 'openai', 'ollama'"
    )


class MultiSourceRetrieveRequest(BaseModel):
    """多源检索请求"""
    query: str = Field(..., description="检索查询")
    project_id: Optional[int] = Field(None, description="项目ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    top_k: int = Field(5, ge=1, le=20, description="每个源返回的Top K结果")
    enabled_sources: Optional[List[str]] = Field(None, description="启用的检索源列表")


class RankFuseRequest(BaseModel):
    """排序融合请求"""
    multi_source_results: Dict[str, Any] = Field(..., description="多源检索结果")
    fusion_method: str = Field('rrf', description="融合方法: 'rrf', 'weighted', 'simple'")
    top_k: int = Field(10, ge=1, le=50, description="返回Top K结果")


# ========== API 端点 ==========

@router.get("/health")
async def health_check():
    """
    健康检查

    返回服务状态和可用检索源列表
    """
    try:
        service = get_deep_rag_service()
        health = service.health_check()
        return success_response(
            data={
                "service": health['service'],
                "available_sources": health['available_sources'],
                "total_sources": health['total_sources'],
                "active_conversations": health['active_conversations'],
                "timestamp": datetime.utcnow().isoformat()
            },
            message="健康检查成功"
        )
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}")
        return error_response(
            code="HEALTH_CHECK_FAILED",
            message=str(e)
        )


@router.post("/chat")
async def deep_chat(request: DeepChatRequest):
    """
    深度RAG对话 - 主接口

    整合多源检索、上下文记忆、引用溯源的完整对话系统

    Returns:
        {
            "answer": "AI回答",
            "citations": [引用列表],
            "confidence": 0.85,
            "sources_used": ["vector", "cognee", "lightrag"],
            "context": "检索上下文",
            "metadata": {统计信息}
        }
    """
    try:
        service = get_deep_rag_service()

        result = await service.deep_chat(
            query=request.query,
            session_id=request.session_id,
            project_id=request.project_id,
            use_context=request.use_context,
            top_k=request.top_k,
            enabled_sources=request.enabled_sources,
            llm_provider=request.llm_provider
        )

        return success_response(
            data=result,
            message="深度对话成功"
        )

    except Exception as e:
        logger.error(f"❌ 深度对话失败: {e}")
        import traceback
        traceback.print_exc()
        return error_response(
            code="DEEP_CHAT_FAILED",
            message=str(e)
        )


@router.post("/retrieve")
async def multi_source_retrieve(request: MultiSourceRetrieveRequest):
    """
    多源并行检索

    不生成回答，仅返回检索结果和引用

    Returns:
        {
            "results": {source_name: results},
            "metadata": {统计信息},
            "citations": [引用列表]
        }
    """
    try:
        service = get_deep_rag_service()

        result = await service.multi_source_retrieve(
            query=request.query,
            project_id=request.project_id,
            session_id=request.session_id,
            top_k=request.top_k,
            enabled_sources=request.enabled_sources
        )

        return success_response(
            data=result,
            message="多源检索成功"
        )

    except Exception as e:
        logger.error(f"❌ 多源检索失败: {e}")
        import traceback
        traceback.print_exc()
        return error_response(
            code="RETRIEVE_FAILED",
            message=str(e)
        )


@router.post("/rank-fuse")
async def rank_and_fuse(request: RankFuseRequest):
    """
    融合排序多源检索结果

    使用RRF (Reciprocal Rank Fusion) 算法融合多个检索源的结果

    Returns:
        排序后的Top K结果列表
    """
    try:
        service = get_deep_rag_service()

        fused_results = service.rank_and_fuse(
            multi_source_results=request.multi_source_results,
            fusion_method=request.fusion_method,
            top_k=request.top_k
        )

        return success_response(
            data={
                "results": fused_results,
                "count": len(fused_results),
                "fusion_method": request.fusion_method
            },
            message="融合排序成功"
        )

    except Exception as e:
        logger.error(f"❌ 融合排序失败: {e}")
        return error_response(
            code="RANK_FUSE_FAILED",
            message=str(e)
        )


@router.get("/conversation/{session_id}/")
async def get_conversation_history(session_id: str):
    """
    获取对话历史

    Args:
        session_id: 会话ID

    Returns:
        对话历史消息列表
    """
    try:
        service = get_deep_rag_service()
        history = service.get_conversation_history(session_id)

        return success_response(
            data={
                "session_id": session_id,
                "messages": history,
                "count": len(history)
            },
            message="获取对话历史成功"
        )

    except Exception as e:
        logger.error(f"❌ 获取对话历史失败: {e}")
        return error_response(
            code="GET_HISTORY_FAILED",
            message=str(e)
        )


@router.delete("/conversation/{session_id}/")
async def clear_conversation(session_id: str):
    """
    清除对话历史

    Args:
        session_id: 会话ID

    Returns:
        删除确认
    """
    try:
        service = get_deep_rag_service()
        service.clear_conversation(session_id)

        return success_response(
            data=None,
            message=f"会话 {session_id} 的对话历史已清除"
        )

    except Exception as e:
        logger.error(f"❌ 清除对话历史失败: {e}")
        return error_response(
            code="CLEAR_CONVERSATION_FAILED",
            message=str(e)
        )


@router.get("/sources")
async def list_available_sources():
    """
    列出所有可用的检索源

    Returns:
        检索源列表及其状态
    """
    try:
        service = get_deep_rag_service()
        sources = service.retrieval_sources

        source_info = []
        for name, source in sources.items():
            source_info.append({
                "name": name,
                "type": type(source).__name__,
                "available": True
            })

        return success_response(
            data={
                "sources": source_info,
                "total": len(source_info)
            },
            message="列出检索源成功"
        )

    except Exception as e:
        logger.error(f"❌ 列出检索源失败: {e}")
        return error_response(
            code="LIST_SOURCES_FAILED",
            message=str(e)
        )


@router.post("/chat/batch")
async def batch_chat(
    queries: List[str] = Body(..., description="批量问题列表"),
    session_id: str = Body(..., description="会话ID"),
    project_id: Optional[int] = Body(None, description="项目ID"),
    llm_provider: str = Body('anthropic', description="LLM提供商")
):
    """
    批量对话

    一次性处理多个问题，适用于批量分析场景

    Returns:
        批量回答结果
    """
    try:
        service = get_deep_rag_service()
        results = []

        for idx, query in enumerate(queries):
            logger.info(f"📝 处理批量问题 {idx+1}/{len(queries)}: {query[:50]}...")

            result = await service.deep_chat(
                query=query,
                session_id=f"{session_id}_batch_{idx}",  # 独立会话
                project_id=project_id,
                use_context=False,  # 批量不使用上下文
                llm_provider=llm_provider
            )

            results.append({
                "query": query,
                "answer": result['answer'],
                "confidence": result['confidence'],
                "sources_used": result['sources_used']
            })

        return success_response(
            data={
                "results": results,
                "total": len(results)
            },
            message="批量对话成功"
        )

    except Exception as e:
        logger.error(f"❌ 批量对话失败: {e}")
        return error_response(
            code="BATCH_CHAT_FAILED",
            message=str(e)
        )


@router.post("/chat/stream")
async def stream_chat(request: DeepChatRequest):
    """
    流式对话（预留接口）

    TODO: 实现SSE流式返回，实时推送生成进度
    """
    raise HTTPException(
        status_code=501,
        detail="流式对话功能即将推出，请使用 POST /chat"
    )


@router.get("/statistics")
async def get_statistics():
    """
    获取服务统计信息

    Returns:
        使用统计数据
    """
    try:
        service = get_deep_rag_service()

        stats = {
            "active_conversations": len(service.conversation_history),
            "total_messages": sum(
                len(messages) for messages in service.conversation_history.values()
            ),
            "available_sources": len(service.retrieval_sources),
            "source_names": list(service.retrieval_sources.keys())
        }

        return success_response(
            data=stats,
            message="获取统计信息成功"
        )

    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")
        return error_response(
            code="GET_STATISTICS_FAILED",
            message=str(e)
        )
