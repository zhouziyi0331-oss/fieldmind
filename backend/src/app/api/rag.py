"""
RAG API路由

提供完整的RAG功能API：
- 知识图谱查询
- 向量搜索
- 混合检索
- RAG问答
- 会话管理
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.vector_store import VectorStore, EmbeddingModel
from app.services.hybrid_retriever import HybridRetriever, GraphQueryEngine
from app.services.rag_generator import RAGGenerator
from app.services.llm_enhancer import LLMEnhancer

router = APIRouter(prefix="/api/rag", tags=["RAG System"])


# ==================== Request/Response Models ====================

class BuildGraphRequest(BaseModel):
    """构建知识图谱请求"""
    package_id: int


class RAGQueryRequest(BaseModel):
    """RAG查询请求"""
    query: str
    session_id: Optional[str] = None
    retrieval_config: Optional[Dict] = None


class VectorSearchRequest(BaseModel):
    """向量搜索请求"""
    query: str
    top_k: int = 10
    threshold: float = 0.7
    filters: Optional[Dict] = None


class GraphQueryRequest(BaseModel):
    """图谱查询请求"""
    entity_name: str
    max_depth: int = 2


class AddDocumentsRequest(BaseModel):
    """添加文档请求"""
    documents: List[Dict[str, Any]]
    chunk_size: int = 512
    chunk_overlap: int = 50


# ==================== 知识图谱API ====================

@router.post("/graph/build")
async def build_knowledge_graph(
    request: BuildGraphRequest,
    db: Session = Depends(get_db)
):
    """
    从SBPACK构建知识图谱

    自动提取实体、关系、时序事件
    """
    try:
        # TODO: 从环境变量获取API key
        llm_enhancer = LLMEnhancer(api_key=None, model="gpt-4")

        builder = KnowledgeGraphBuilder(db, llm_enhancer)
        result = await builder.build_from_sbpack(request.package_id)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build graph: {str(e)}")


@router.get("/graph/entity/{entity_name}")
async def get_entity(entity_name: str, db: Session = Depends(get_db)):
    """获取实体详情"""
    graph_query = GraphQueryEngine(db)
    entity = graph_query.find_entity(entity_name)

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return {
        "entity_id": entity.entity_id,
        "name": entity.name,
        "type": entity.entity_type,
        "description": entity.description,
        "attributes": entity.attributes,
        "aliases": entity.aliases,
        "confidence_score": entity.confidence_score,
        "observation_count": entity.observation_count,
        "relation_count": entity.relation_count
    }


@router.post("/graph/traverse")
async def traverse_graph(request: GraphQueryRequest, db: Session = Depends(get_db)):
    """
    图遍历

    从指定实体开始遍历关系网络
    """
    try:
        graph_query = GraphQueryEngine(db)
        result = await graph_query.traverse(
            start_entities=[request.entity_name],
            max_depth=request.max_depth
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/stats")
async def get_graph_statistics(db: Session = Depends(get_db)):
    """获取知识图谱统计信息"""
    from app.models.knowledge_graph import Entity, Relation
    from sqlalchemy import func

    entity_count = db.query(func.count(Entity.id)).scalar()
    relation_count = db.query(func.count(Relation.id)).scalar()

    # 实体类型分布
    entity_types = db.query(
        Entity.entity_type,
        func.count(Entity.id)
    ).group_by(Entity.entity_type).all()

    # 关系类型分布
    relation_types = db.query(
        Relation.relation_type,
        func.count(Relation.id)
    ).group_by(Relation.relation_type).all()

    return {
        "total_entities": entity_count,
        "total_relations": relation_count,
        "entity_types": {et[0]: et[1] for et in entity_types},
        "relation_types": {rt[0]: rt[1] for rt in relation_types}
    }


# ==================== 向量存储API ====================

@router.post("/vectors/add")
async def add_documents_to_vector_store(
    request: AddDocumentsRequest,
    db: Session = Depends(get_db)
):
    """
    添加文档到向量存储

    自动分块和向量化
    """
    try:
        embedding_model = EmbeddingModel()
        vector_store = VectorStore(db, embedding_model)

        chunks_added = await vector_store.add_documents(
            request.documents,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        return {
            "success": True,
            "chunks_added": chunks_added
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vectors/search")
async def vector_search(request: VectorSearchRequest, db: Session = Depends(get_db)):
    """
    向量语义搜索

    基于pgvector的高性能检索
    """
    try:
        embedding_model = EmbeddingModel()
        vector_store = VectorStore(db, embedding_model)

        results = await vector_store.similarity_search(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            filters=request.filters
        )

        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vectors/stats")
async def get_vector_statistics(db: Session = Depends(get_db)):
    """获取向量存储统计信息"""
    embedding_model = EmbeddingModel()
    vector_store = VectorStore(db, embedding_model)

    stats = vector_store.get_statistics()

    return stats


# ==================== RAG查询API ====================

@router.post("/query")
async def rag_query(request: RAGQueryRequest, db: Session = Depends(get_db)):
    """
    RAG查询

    完整的检索-生成流程，返回有根据的答案
    """
    try:
        # 初始化组件
        embedding_model = EmbeddingModel()
        vector_store = VectorStore(db, embedding_model)
        graph_query = GraphQueryEngine(db)
        llm_enhancer = LLMEnhancer(api_key=None, model="gpt-4")

        retriever = HybridRetriever(db, vector_store, graph_query, llm_enhancer)

        # TODO: 从环境变量获取OpenAI client
        from openai import OpenAI
        llm_client = OpenAI(api_key=None)

        generator = RAGGenerator(db, retriever, llm_client)

        # 生成答案
        result = await generator.generate_answer(
            query=request.query,
            session_id=request.session_id,
            retrieval_config=request.retrieval_config
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def rag_query_stream(request: RAGQueryRequest, db: Session = Depends(get_db)):
    """
    RAG流式查询

    逐步返回答案内容
    """
    try:
        # 初始化组件
        embedding_model = EmbeddingModel()
        vector_store = VectorStore(db, embedding_model)
        graph_query = GraphQueryEngine(db)
        llm_enhancer = LLMEnhancer(api_key=None, model="gpt-4")

        retriever = HybridRetriever(db, vector_store, graph_query, llm_enhancer)

        from openai import OpenAI
        llm_client = OpenAI(api_key=None)

        generator = RAGGenerator(db, retriever, llm_client)

        # 流式生成
        async def generate():
            async for chunk in generator.stream_answer(
                query=request.query,
                session_id=request.session_id,
                retrieval_config=request.retrieval_config
            ):
                import json
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 会话管理API ====================

@router.post("/sessions")
async def create_session(
    session_name: Optional[str] = None,
    user_id: int = 1,  # TODO: 从认证获取
    db: Session = Depends(get_db)
):
    """创建RAG会话"""
    from app.models.knowledge_graph import RAGSession
    import uuid

    session = RAGSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        session_name=session_name or "新会话",
        context_window=[],
        retrieval_config={}
    )

    db.add(session)
    db.commit()

    return {
        "session_id": session.session_id,
        "session_name": session.session_name,
        "created_at": session.created_at.isoformat()
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """获取会话详情"""
    from app.models.knowledge_graph import RAGSession

    session = db.query(RAGSession).filter(
        RAGSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session.session_id,
        "session_name": session.session_name,
        "query_count": session.query_count,
        "context_window": session.context_window,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat() if session.last_activity else None
    }


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 20, db: Session = Depends(get_db)):
    """获取会话历史"""
    from app.models.knowledge_graph import RAGQuery

    # 查找会话
    from app.models.knowledge_graph import RAGSession
    session = db.query(RAGSession).filter(
        RAGSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 查询历史
    queries = db.query(RAGQuery).filter(
        RAGQuery.session_id == session.id
    ).order_by(RAGQuery.created_at.desc()).limit(limit).all()

    return {
        "session_id": session_id,
        "history": [
            {
                "query_id": q.query_id,
                "query": q.query_text,
                "answer": q.generated_answer,
                "sources": q.answer_sources,
                "created_at": q.created_at.isoformat(),
                "metrics": {
                    "relevance_score": q.relevance_score,
                    "groundedness_score": q.groundedness_score,
                    "total_time_ms": q.total_time_ms
                }
            }
            for q in queries
        ]
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    from app.models.knowledge_graph import RAGSession

    session = db.query(RAGSession).filter(
        RAGSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"success": True, "message": "Session deleted"}


# ==================== 检索测试API ====================

@router.post("/test/retrieve")
async def test_retrieval(
    query: str,
    strategy: str = 'hybrid',
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """
    测试检索功能

    用于调试和比较不同检索策略
    """
    try:
        embedding_model = EmbeddingModel()
        vector_store = VectorStore(db, embedding_model)
        graph_query = GraphQueryEngine(db)
        llm_enhancer = LLMEnhancer(api_key=None, model="gpt-4")

        retriever = HybridRetriever(db, vector_store, graph_query, llm_enhancer)

        results = await retriever.retrieve(
            query=query,
            strategy=strategy,
            top_k=top_k
        )

        return {
            "query": query,
            "strategy": strategy,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
