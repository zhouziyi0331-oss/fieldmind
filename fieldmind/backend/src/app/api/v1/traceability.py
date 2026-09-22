"""
溯源回溯 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter()


@router.post("/traceability/trace", response_model=ApiResponse)
async def trace_conclusion(
    request: Request,
    project_id: int = Body(..., description="项目ID"),
    conclusion: str = Body(..., description="结论文本"),
    db: Session = Depends(get_db),
):
    """
    追溯结论的来源

    输入：结论文本
    输出：支撑该结论的原始材料（chunks + 文档）

    返回：
    - 匹配的 chunks 列表
    - 每个 chunk 的来源文档
    - 匹配度分数
    - 音频时间码（如果有）
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.traceability_service import traceability_service

        trace_result = traceability_service.trace_conclusion(
            db=db,
            conclusion_text=conclusion,
            project_id=project_id
        )

        return success_response(
            data=trace_result,
            request_id=request_id,
            message=f"找到 {len(trace_result['sources'])} 个来源"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traceability/chunk/{chunk_id}/context", response_model=ApiResponse)
async def get_chunk_context(
    request: Request,
    chunk_id: int,
    context_size: int = 1,
    db: Session = Depends(get_db),
):
    """
    获取 chunk 的上下文

    返回：
    - 当前 chunk
    - 前 N 个 chunks
    - 后 N 个 chunks
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.traceability_service import traceability_service

        context = traceability_service.get_chunk_context(
            db=db,
            chunk_id=chunk_id,
            context_size=context_size
        )

        if "error" in context:
            raise HTTPException(status_code=404, detail=context["error"])

        return success_response(
            data=context,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traceability/chunk/{chunk_id}/highlight", response_model=ApiResponse)
async def highlight_chunk_in_document(
    request: Request,
    chunk_id: int,
    db: Session = Depends(get_db),
):
    """
    在文档中高亮显示 chunk

    返回：
    - 文档全文
    - chunk 在文档中的位置（字符索引）
    - 高亮起止位置
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.traceability_service import traceability_service
        from app.models.chunk import Chunk

        # 获取 chunk 的 document_id
        chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk 不存在")

        highlight_result = traceability_service.highlight_in_document(
            db=db,
            document_id=chunk.document_id,
            chunk_id=chunk_id
        )

        if "error" in highlight_result:
            raise HTTPException(status_code=404, detail=highlight_result["error"])

        return success_response(
            data=highlight_result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traceability/document/{document_id}/chunks", response_model=ApiResponse)
async def get_document_chunks(
    request: Request,
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    获取文档的所有 chunks

    用于在前端展示完整的文档结构
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chunk import Chunk
        from app.models.project import ProjectDocument

        # 检查文档是否存在
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 获取所有 chunks
        chunks = db.query(Chunk).filter(
            Chunk.document_id == document_id
        ).order_by(Chunk.position).all()

        chunks_data = [
            {
                "id": chunk.id,
                "position": chunk.position,
                "content": chunk.content,
                "char_count": chunk.char_count,
                "sentiment_polarity": chunk.sentiment_polarity,
                "dimension_category": chunk.dimension_category
            }
            for chunk in chunks
        ]

        return success_response(
            data={
                "document_id": document_id,
                "document_name": doc.original_filename,
                "total_chunks": len(chunks),
                "chunks": chunks_data
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/traceability/batch-trace", response_model=ApiResponse)
async def batch_trace_conclusions(
    request: Request,
    project_id: int = Body(...),
    conclusions: list[str] = Body(..., description="多个结论文本"),
    db: Session = Depends(get_db),
):
    """
    批量追溯多个结论

    用于报告中一次追溯多个结论的来源
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.traceability_service import traceability_service

        results = []

        for conclusion in conclusions[:20]:  # 限制最多20个
            trace_result = traceability_service.trace_conclusion(
                db=db,
                conclusion_text=conclusion,
                project_id=project_id
            )
            results.append(trace_result)

        return success_response(
            data={
                "total": len(results),
                "traces": results
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
