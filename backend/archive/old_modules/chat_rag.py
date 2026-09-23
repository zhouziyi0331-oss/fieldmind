"""
RAG对话API - 真正的向量检索对话

严禁使用模拟数据，必须读写 ChromaDB 和 PostgreSQL
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.rag_engine import rag_engine
from app.models.project import ProjectDocument
from app.schemas.response import success_response, error_response

router = APIRouter(tags=["chat-rag"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """聊天请求"""
    question: str
    project_id: Optional[int] = None
    top_k: int = 5  # 召回前K个相关文本块
    selected_document_ids: Optional[List[int]] = None  # 指定检索范围的文档ID列表


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    retrieved_chunks: List[dict]
    has_relevant_data: bool
    message: Optional[str] = None


@router.post("/query", response_model=ChatResponse)
def rag_query(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    基于RAG的对话查询

    流程：
    1. 检查是否有已处理的文档
    2. 使用RAG引擎从ChromaDB检索相关文本块
    3. 如果没有相关数据，直接返回提示
    4. 如果有相关数据，拼接成上下文返回（LLM生成需要API Key）
    """
    try:
        logger.info(f"收到RAG查询: {request.question[:50]}...")

        # 1. 检查是否有已向量化的文档
        query = db.query(ProjectDocument).filter(
            ProjectDocument.status == 'completed'
        )

        if request.project_id:
            query = query.filter(ProjectDocument.project_id == request.project_id)

        # 如果指定了文档ID，仅检索这些文档
        if request.selected_document_ids:
            query = query.filter(ProjectDocument.id.in_(request.selected_document_ids))
            logger.info(f"限定检索范围：文档ID {request.selected_document_ids}")

        # 统计有向量化数据的文档
        vectorized_docs = []
        all_docs = query.all()

        for doc in all_docs:
            if doc.extra_data and doc.extra_data.get('pipeline_completed'):
                vectorized_docs.append(doc)

        if not vectorized_docs:
            if request.selected_document_ids:
                logger.warning(f"指定的文档{request.selected_document_ids}未向量化")
                return ChatResponse(
                    answer="",
                    retrieved_chunks=[],
                    has_relevant_data=False,
                    message="您选择的文档尚未完成向量化处理，请等待处理完成或选择其他文档。"
                )
            else:
                logger.warning("没有已向量化的文档")
                return ChatResponse(
                    answer="",
                    retrieved_chunks=[],
                    has_relevant_data=False,
                    message="当前知识库中暂无相关材料，请先上传并处理相关文档。"
                )

        logger.info(f"找到 {len(vectorized_docs)} 个已向量化的文档")

        # 2. 使用RAG引擎检索
        if not rag_engine or not rag_engine.collection:
            logger.error("RAG引擎未初始化")
            return ChatResponse(
                answer="",
                retrieved_chunks=[],
                has_relevant_data=False,
                message="向量检索服务未初始化，请检查ChromaDB配置。"
            )

        try:
            # 构建where条件（文档ID过滤）
            where_filter = None
            if request.selected_document_ids:
                # ChromaDB的where语法：metadata字段过滤
                where_filter = {
                    "document_id": {
                        "$in": [int(doc_id) for doc_id in request.selected_document_ids]
                    }
                }
                logger.info(f"应用文档ID过滤: {where_filter}")

            # 从ChromaDB检索相关文档
            results = rag_engine.collection.query(
                query_texts=[request.question],
                n_results=request.top_k,
                where=where_filter,  # 关键：添加metadata过滤
                include=["documents", "metadatas", "distances"]
            )

            logger.info(f"ChromaDB返回 {len(results['documents'][0]) if results['documents'] else 0} 个结果")

            # 解析检索结果
            retrieved_chunks = []
            if results['documents'] and len(results['documents'][0]) > 0:
                for i, doc_text in enumerate(results['documents'][0]):
                    chunk = {
                        'text': doc_text,
                        'distance': float(results['distances'][0][i]) if results.get('distances') else None,
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {}
                    }
                    retrieved_chunks.append(chunk)

            if not retrieved_chunks:
                logger.warning("向量检索未找到相关内容")
                return ChatResponse(
                    answer="",
                    retrieved_chunks=[],
                    has_relevant_data=False,
                    message="未找到与问题相关的材料内容。"
                )

            logger.info(f"✅ 检索到 {len(retrieved_chunks)} 个相关文本块")

            # 3. 拼接检索到的文本作为上下文
            context_text = "\n\n".join([
                f"【相关材料 {i+1}】\n{chunk['text'][:500]}"
                for i, chunk in enumerate(retrieved_chunks[:3])
            ])

            # 4. 生成回答提示（没有LLM API Key时返回检索结果）
            answer = f"""基于以下材料回答您的问题：

问题：{request.question}

相关材料：
{context_text}

---
注意：当前系统未配置LLM API Key（ANTHROPIC_API_KEY或OPENAI_API_KEY），无法自动生成回答。
上述是从知识库中检索到的相关材料片段，请根据这些材料自行归纳答案。

如需AI自动生成回答，请在 .env 文件中配置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY。
"""

            return ChatResponse(
                answer=answer,
                retrieved_chunks=retrieved_chunks,
                has_relevant_data=True,
                message=None
            )

        except Exception as e:
            logger.error(f"ChromaDB检索失败: {e}", exc_info=True)
            return ChatResponse(
                answer="",
                retrieved_chunks=[],
                has_relevant_data=False,
                message=f"向量检索失败: {str(e)}"
            )

    except Exception as e:
        logger.error(f"RAG查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-documents/{project_id}/")
def get_available_documents(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目中可用于RAG检索的文档列表

    返回已完成向量化的文档
    """
    try:
        docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == 'completed'
        ).all()

        available_docs = []
        for doc in docs:
            if doc.extra_data and doc.extra_data.get('pipeline_completed'):
                available_docs.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "word_count": doc.word_count,
                    "chunks_count": doc.extra_data.get('chunks_count', 0)
                })

        return success_response(
            data={
                "project_id": project_id,
                "available_documents": available_docs,
                "total": len(available_docs)
            }
        )

    except Exception as e:
        logger.error(f"获取可用文档失败: {e}")
        return error_response(
            code="GET_DOCUMENTS_FAILED",
            message=str(e)
        )


@router.get("/status")
def rag_status(db: Session = Depends(get_db)):
    """
    检查RAG系统状态
    """
    try:
        # 检查向量化文档数量
        vectorized_count = 0
        docs = db.query(ProjectDocument).filter(
            ProjectDocument.status == 'completed'
        ).all()

        for doc in docs:
            if doc.extra_data and doc.extra_data.get('pipeline_completed'):
                vectorized_count += 1

        # 检查ChromaDB
        chroma_status = "ok" if (rag_engine and rag_engine.collection) else "not_initialized"

        # 检查ChromaDB中的向量数量
        vector_count = 0
        if rag_engine and rag_engine.collection:
            try:
                vector_count = rag_engine.collection.count()
            except Exception as e:
                logger.warning(f"获取向量数量失败: {e}")

        return success_response(
            data={
                "status": "ready" if (vectorized_count > 0 and chroma_status == "ok") else "not_ready",
                "vectorized_documents": vectorized_count,
                "chromadb_status": chroma_status,
                "vector_count": vector_count
            },
            message="RAG系统已就绪，可以进行对话" if vectorized_count > 0 else "请先上传并处理文档"
        )

    except Exception as e:
        logger.error(f"获取RAG状态失败: {e}")
        return error_response(
            code="GET_STATUS_FAILED",
            message=str(e)
        )
