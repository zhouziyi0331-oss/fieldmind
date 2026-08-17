"""
RAG API路由 - 三重检索融合
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.exceptions import AIServiceException, VectorStoreException

# from app.tasks.rag_tasks import triple_retrieval_query, generate_answer
# from app.celery_app import celery_app

router = APIRouter()


class RAGQueryRequest(BaseModel):
    """RAG查询请求"""
    question: str
    top_k: int = 5
    generate_answer: bool = True


class BatchRAGQueryRequest(BaseModel):
    """批量RAG查询请求"""
    questions: List[str]
    top_k: int = 5
    generate_answer: bool = True


@router.post("/query")
async def rag_query(request: RAGQueryRequest) -> Dict[str, Any]:
    """
    RAG查询 - 三重检索融合

    自动触发：
    1. 并行检索：向量检索 | 全文检索 | 图谱检索 | 关键词检索
    2. RRF 融合排序
    3. LLM 生成答案（可选）

    检索来源：
    - ChromaDB: 向量语义检索
    - Whoosh: 全文关键词检索
    - Neo4j: 知识图谱关系检索
    - PostgreSQL: 数据库关键词检索
    """
    try:
        # 执行三重检索
        retrieval_result = triple_retrieval_query(request.question, request.top_k)

        if not retrieval_result.get("success"):
            raise VectorStoreException(
                message=retrieval_result.get("error", "检索失败"),
                operation="triple_retrieval"
            )

        response = {
            "success": True,
            "question": request.question,
            "retrieval": retrieval_result,
        }

        # 生成答案
        if request.generate_answer:
            answer_result = generate_answer(
                request.question,
                retrieval_result["top_documents"]
            )
            response["answer"] = answer_result

        response["queried_at"] = datetime.utcnow().isoformat()

        return response

    except (VectorStoreException, AIServiceException):
        raise
    except Exception as e:
        raise AIServiceException(
            message="RAG查询失败",
            service="rag_query",
            details={"question": request.question, "error": str(e)}
        )


@router.post("/query-async")
async def rag_query_async(request: RAGQueryRequest) -> Dict[str, Any]:
    """
    异步RAG查询（适合长时间查询）
    """
    try:
        # 异步执行三重检索
        task = triple_retrieval_query.delay(request.question, request.top_k)

        return {
            "success": True,
            "message": "RAG查询任务已启动",
            "question": request.question,
            "task_id": task.id,
            "status_url": f"/api/v1/rag/status/{task.id}",
            "submitted_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise AIServiceException(
            message="任务提交失败",
            service="rag_query_async",
            details={"question": request.question, "error": str(e)}
        )


@router.post("/batch-query")
async def batch_rag_query(request: BatchRAGQueryRequest) -> Dict[str, Any]:
    """
    批量RAG查询
    """
    try:
        tasks = []

        for question in request.questions:
            task = triple_retrieval_query.delay(question, request.top_k)
            tasks.append({
                "question": question,
                "task_id": task.id,
            })

        return {
            "success": True,
            "message": f"已提交 {len(tasks)} 个查询任务",
            "total": len(tasks),
            "tasks": tasks,
            "submitted_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise AIServiceException(
            message="批量查询失败",
            service="batch_rag_query",
            details={"question_count": len(request.questions), "error": str(e)}
        )


@router.get("/status/{task_id}")
async def get_query_status(task_id: str) -> Dict[str, Any]:
    """
    查询RAG任务状态
    """
    try:
        task = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": task.state,
            "ready": task.ready(),
        }

        if task.ready():
            if task.successful():
                response["result"] = task.result
            else:
                response["error"] = str(task.info)

        return response

    except Exception as e:
        raise AIServiceException(
            message="状态查询失败",
            service="rag_status_check",
            details={"task_id": task_id, "error": str(e)}
        )


@router.get("/retrieval-stats")
async def get_retrieval_stats() -> Dict[str, Any]:
    """
    获取检索统计信息
    """
    try:
        # TODO: 实现实际的统计查询
        return {
            "vector_db": {
                "type": "ChromaDB",
                "collections": 1,
                "documents": 0,  # TODO: 实际查询
            },
            "fulltext_db": {
                "type": "Whoosh",
                "indexed_documents": 0,  # TODO: 实际查询
            },
            "graph_db": {
                "type": "Neo4j",
                "nodes": 0,  # TODO: 实际查询
                "relationships": 0,
            },
            "keyword_db": {
                "type": "PostgreSQL",
                "documents": 0,  # TODO: 实际查询
            }
        }

    except Exception as e:
        raise VectorStoreException(
            message="统计查询失败",
            operation="get_retrieval_stats",
            details={"error": str(e)}
        )
