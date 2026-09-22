"""
材料溯源API - 分析结果的来源追踪
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.source_traceback_service import SourceTracebackService
from app.models.analysis import AnalysisResult
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/source-traceback", tags=["材料溯源"])


# Pydantic模型
class SaveAnalysisRequest(BaseModel):
    project_id: int
    analysis_type: str
    title: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]


class VerifySourceRequest(BaseModel):
    status: str  # 'verified', 'questioned', 'incorrect'
    notes: Optional[str] = None


@router.post("/analyses")
async def save_analysis(
    request: SaveAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    保存分析结果并自动追溯来源

    这是核心功能：将分析结果保存时，自动为每个陈述查找原始材料来源
    """
    service = SourceTracebackService(db)

    try:
        analysis = service.save_analysis_with_sources(
            project_id=request.project_id,
            analysis_type=request.analysis_type,
            title=request.title,
            parameters=request.parameters,
            result=request.result
        )

        return success_response(
            data={
                "id": analysis.id,
                "analysis_type": analysis.analysis_type
            },
            message="分析结果已保存并完成溯源"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/analyses/{analysis_id}/")
async def get_analysis_with_sources(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    获取分析结果（包含完整的溯源信息）

    返回:
    - 分析结果
    - 每个陈述的来源列表
    - 每个来源的原始材料片段
    - 用户验证状态
    """
    service = SourceTracebackService(db)

    result = service.get_analysis_with_sources(analysis_id)

    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")

    return result


@router.get("/projects/{project_id}/analyses/")
async def list_project_analyses(
    project_id: int,
    analysis_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取项目的所有分析结果列表

    支持按分析类型过滤
    """
    query = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    )

    if analysis_type:
        query = query.filter(AnalysisResult.analysis_type == analysis_type)

    total = query.count()

    analyses = query.order_by(
        AnalysisResult.created_at.desc()
    ).limit(limit).offset(offset).all()

    return success_response(
        data={
            "total": total,
            "limit": limit,
            "offset": offset,
            "analyses": [
                {
                    "id": a.id,
                    "analysis_type": a.analysis_type,
                    "title": a.title,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "view_count": a.view_count,
                    "rating": a.rating
                }
                for a in analyses
            ]
        }
    )


@router.get("/statements/{statement_id}/sources/")
async def get_statement_sources(
    statement_id: int,
    db: Session = Depends(get_db)
):
    """
    获取特定陈述的所有来源

    用于"点击查看来源"功能
    """
    service = SourceTracebackService(db)

    sources = service.get_statement_sources(statement_id)

    return success_response(
        data={
            "statement_id": statement_id,
            "sources": sources
        }
    )


@router.post("/sources/{source_id}/verify/")
async def verify_source(
    source_id: int,
    request: VerifySourceRequest,
    db: Session = Depends(get_db)
):
    """
    用户验证来源的正确性

    支持三种状态:
    - verified (绿色): 已核实，来源正确
    - questioned (黄色): 存疑，需要进一步确认
    - incorrect (红色): 错误，来源不正确
    """
    # TODO: 从认证中获取user_id
    user_id = "temp_user_id"

    service = SourceTracebackService(db)

    try:
        verification = service.verify_source(
            source_id=source_id,
            user_id=user_id,
            status=request.status,
            notes=request.notes
        )

        return success_response(
            data={
                "id": verification.id,
                "status": verification.status
            },
            message="验证成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/chunks/{chunk_id}/detail/")
async def get_chunk_detail(
    chunk_id: int,
    db: Session = Depends(get_db)
):
    """
    获取chunk的详细信息（用于溯源预览）

    返回:
    - chunk文本
    - 所属文档信息
    - 位置信息
    - 上下文（前后chunk）
    """
    from app.services.vectorization_service_complete import DocumentChunk
    from app.models.project import ProjectDocument

    try:
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.id == chunk_id
        ).first()

        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk不存在")

        # 获取文档信息
        document = None
        if chunk.document_id:
            document = db.query(ProjectDocument).filter(
                ProjectDocument.id == chunk.document_id
            ).first()

        # 获取前后chunk（上下文）
        prev_chunk = None
        next_chunk = None

        if chunk.prev_chunk_id:
            prev_chunk = db.query(DocumentChunk).filter(
                DocumentChunk.chunk_id == chunk.prev_chunk_id
            ).first()

        if chunk.next_chunk_id:
            next_chunk = db.query(DocumentChunk).filter(
                DocumentChunk.chunk_id == chunk.next_chunk_id
            ).first()

        return {
            "chunk": {
                "id": int(chunk.id) if chunk.id else 0,
                "text": str(chunk.text) if chunk.text else "",
                "chunk_index": int(chunk.chunk_index) if chunk.chunk_index is not None else 0,
                "total_chunks": int(chunk.total_chunks) if chunk.total_chunks else 0,
                "position": {
                    "start": int(chunk.start_pos) if chunk.start_pos else 0,
                    "end": int(chunk.end_pos) if chunk.end_pos else 0
                }
            },
            "document": {
                "id": int(document.id) if document else 0,
                "filename": str(document.filename) if document else "",
                "file_type": str(document.file_type) if document else ""
            } if document else None,
            "context": {
                "prev": {
                    "id": int(prev_chunk.id),
                    "text": str(prev_chunk.text[:100]) + "..." if len(prev_chunk.text) > 100 else str(prev_chunk.text)
                } if prev_chunk and prev_chunk.text else None,
                "next": {
                    "id": int(next_chunk.id),
                    "text": str(next_chunk.text[:100]) + "..." if len(next_chunk.text) > 100 else str(next_chunk.text)
                } if next_chunk and next_chunk.text else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取chunk详情失败: {str(e)}")


@router.delete("/analyses/{analysis_id}/")
async def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    删除分析结果

    级联删除所有关联的陈述、来源和验证记录
    """
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.id == analysis_id
    ).first()

    if not analysis:
        raise HTTPException(status_code=404, detail="分析结果不存在")

    db.delete(analysis)
    db.commit()

    return success_response(message="分析结果已删除")


@router.get("/projects/{project_id}/statistics/")
async def get_project_source_statistics(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的溯源统计信息

    返回:
    - 总分析数
    - 总陈述数
    - 已验证/存疑/错误的来源数
    - 溯源覆盖率
    """
    from app.models.analysis import AnalysisStatement, StatementSource, SourceVerification

    # 总分析数
    total_analyses = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project_id
    ).count()

    # 总陈述数
    total_statements = db.query(AnalysisStatement).join(
        AnalysisResult
    ).filter(
        AnalysisResult.project_id == project_id
    ).count()

    # 有来源的陈述数
    statements_with_sources = db.query(AnalysisStatement.id).join(
        AnalysisResult
    ).join(
        StatementSource
    ).filter(
        AnalysisResult.project_id == project_id
    ).distinct().count()

    # 验证统计
    verified_count = db.query(SourceVerification).join(
        StatementSource
    ).join(
        AnalysisStatement
    ).join(
        AnalysisResult
    ).filter(
        AnalysisResult.project_id == project_id,
        SourceVerification.status == 'verified'
    ).count()

    questioned_count = db.query(SourceVerification).join(
        StatementSource
    ).join(
        AnalysisStatement
    ).join(
        AnalysisResult
    ).filter(
        AnalysisResult.project_id == project_id,
        SourceVerification.status == 'questioned'
    ).count()

    incorrect_count = db.query(SourceVerification).join(
        StatementSource
    ).join(
        AnalysisStatement
    ).join(
        AnalysisResult
    ).filter(
        AnalysisResult.project_id == project_id,
        SourceVerification.status == 'incorrect'
    ).count()

    return {
        "project_id": project_id,
        "total_analyses": total_analyses,
        "total_statements": total_statements,
        "statements_with_sources": statements_with_sources,
        "source_coverage_rate": statements_with_sources / total_statements if total_statements > 0 else 0,
        "verifications": {
            "verified": verified_count,
            "questioned": questioned_count,
            "incorrect": incorrect_count,
            "total": verified_count + questioned_count + incorrect_count
        }
    }
