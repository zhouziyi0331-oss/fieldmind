"""
Citations API - 文献引用管理
提供学术文献的CRUD、批量导入、引用统计等功能
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.citation import Citation, DocumentCitation
from app.contracts import success_response, error_response, ErrorCodes
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DatabaseException
)

router = APIRouter(tags=["citations"])
logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class CitationCreate(BaseModel):
    """创建引用请求"""
    title: str
    authors: List[str] = []
    year: Optional[str] = None
    publication: Optional[str] = None
    publisher: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    notes: Optional[str] = None
    citation_type: str  # 学术论文/书籍/报告/网页/其他
    tags: List[str] = []
    project_id: int
    bibtex: Optional[str] = None
    extra_metadata: dict = {}


class CitationUpdate(BaseModel):
    """更新引用请求"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    year: Optional[str] = None
    publication: Optional[str] = None
    publisher: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    url: Optional[str] = None
    abstract: Optional[str] = None
    notes: Optional[str] = None
    citation_type: Optional[str] = None
    tags: Optional[List[str]] = None
    bibtex: Optional[str] = None
    extra_metadata: Optional[dict] = None


class CitationResponse(BaseModel):
    """引用响应"""
    id: int
    title: str
    authors: List[str]
    year: Optional[str]
    publication: Optional[str]
    publisher: Optional[str]
    doi: Optional[str]
    isbn: Optional[str]
    url: Optional[str]
    abstract: Optional[str]
    notes: Optional[str]
    citation_type: str
    tags: List[str]
    project_id: int
    cited_count: int
    added_at: datetime
    updated_at: datetime
    bibtex: Optional[str]

    class Config:
        from_attributes = True


class CitationListResponse(BaseModel):
    """引用列表响应"""
    citations: List[CitationResponse]
    total: int
    page: int
    page_size: int


class CitationStatsResponse(BaseModel):
    """引用统计响应"""
    total_citations: int
    by_type: dict  # {citation_type: count}
    by_year: dict  # {year: count}
    top_tags: List[dict]  # [{tag: str, count: int}]
    recent_additions: int  # 最近7天添加的数量


# ==================== API接口 ====================

@router.post("/citations", response_model=CitationResponse)
async def create_citation(
    request: CitationCreate,
    db: Session = Depends(get_db)
):
    """创建新引用"""
    try:
        # 检查DOI是否已存在
        if request.doi:
            existing = db.query(Citation).filter(Citation.doi == request.doi).first()
            if existing:
                raise ValidationException(
                    message=f"DOI {request.doi} 已存在",
                    field="doi"
                )

        citation = Citation(
            title=request.title,
            authors=request.authors,
            year=request.year,
            publication=request.publication,
            publisher=request.publisher,
            doi=request.doi,
            isbn=request.isbn,
            url=request.url,
            abstract=request.abstract,
            notes=request.notes,
            citation_type=request.citation_type,
            tags=request.tags,
            project_id=request.project_id,
            bibtex=request.bibtex,
            extra_metadata=request.extra_metadata
        )

        db.add(citation)
        db.commit()
        db.refresh(citation)

        logger.info(f"✅ 创建引用: {citation.title}")
        return citation

    except ValidationException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 创建引用失败: {e}")
        raise DatabaseException(
            message="创建引用失败",
            cause=e
        )


@router.get("/citations", response_model=CitationListResponse)
async def list_citations(
    project_id: int = Query(..., description="项目ID"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    citation_type: Optional[str] = Query(None, description="文献类型筛选"),
    tags: Optional[str] = Query(None, description="标签筛选（逗号分隔）"),
    sort_by: str = Query("added_at", description="排序字段: added_at/title/cited_count/year"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取引用列表（带搜索、筛选、分页）"""
    try:
        query = db.query(Citation).filter(Citation.project_id == project_id)

        # 搜索
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Citation.title.ilike(search_pattern),
                    Citation.abstract.ilike(search_pattern),
                    func.json_array_length(Citation.authors) > 0  # 简化处理，实际应搜索JSON数组
                )
            )

        # 类型筛选
        if citation_type and citation_type != "全部类型":
            query = query.filter(Citation.citation_type == citation_type)

        # 标签筛选
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            for tag in tag_list:
                query = query.filter(Citation.tags.contains([tag]))

        # 总数
        total = query.count()

        # 排序
        if sort_by == "title":
            order_col = Citation.title
        elif sort_by == "cited_count":
            order_col = Citation.cited_count
        elif sort_by == "year":
            order_col = Citation.year
        else:
            order_col = Citation.added_at

        if sort_order == "asc":
            query = query.order_by(order_col.asc())
        else:
            query = query.order_by(order_col.desc())

        # 分页
        citations = query.offset((page - 1) * page_size).limit(page_size).all()

        return CitationListResponse(
            citations=citations,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"❌ 获取引用列表失败: {e}")
        raise DatabaseException(
            message="获取引用列表失败",
            cause=e
        )


@router.get("/citations/{citation_id}", response_model=CitationResponse)
async def get_citation(
    citation_id: int,
    db: Session = Depends(get_db)
):
    """获取单个引用详情"""
    citation = db.query(Citation).filter(Citation.id == citation_id).first()
    if not citation:
        raise ResourceNotFoundException("Citation", citation_id)
    return citation


@router.put("/citations/{citation_id}", response_model=CitationResponse)
async def update_citation(
    citation_id: int,
    request: CitationUpdate,
    db: Session = Depends(get_db)
):
    """更新引用"""
    try:
        citation = db.query(Citation).filter(Citation.id == citation_id).first()
        if not citation:
            raise ResourceNotFoundException("Citation", citation_id)

        # 更新字段
        update_data = request.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(citation, key, value)

        citation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(citation)

        logger.info(f"✅ 更新引用: {citation.title}")
        return citation

    except ResourceNotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 更新引用失败: {e}")
        raise DatabaseException(
            message="更新引用失败",
            cause=e
        )


@router.delete("/citations/{citation_id}/")
async def delete_citation(
    citation_id: int,
    db: Session = Depends(get_db)
):
    """删除引用"""
    try:
        citation = db.query(Citation).filter(Citation.id == citation_id).first()
        if not citation:
            raise ResourceNotFoundException("Citation", citation_id)

        db.delete(citation)
        db.commit()

        logger.info(f"✅ 删除引用: {citation.title}")
        return success_response(message="引用已删除")

    except ResourceNotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 删除引用失败: {e}")
        raise DatabaseException(
            message="删除引用失败",
            cause=e
        )


@router.get("/citations/stats/{project_id}", response_model=CitationStatsResponse)
async def get_citation_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取引用统计"""
    try:
        from datetime import timedelta

        # 总数
        total = db.query(func.count(Citation.id)).filter(Citation.project_id == project_id).scalar() or 0

        # 按类型统计
        by_type_data = db.query(
            Citation.citation_type,
            func.count(Citation.id)
        ).filter(
            Citation.project_id == project_id
        ).group_by(Citation.citation_type).all()
        by_type = {ctype: count for ctype, count in by_type_data}

        # 按年份统计
        by_year_data = db.query(
            Citation.year,
            func.count(Citation.id)
        ).filter(
            Citation.project_id == project_id,
            Citation.year.isnot(None)
        ).group_by(Citation.year).all()
        by_year = {year: count for year, count in by_year_data}

        # 标签统计（简化版）
        citations = db.query(Citation).filter(Citation.project_id == project_id).all()
        tag_counts = {}
        for citation in citations:
            for tag in citation.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        top_tags = [{"tag": tag, "count": count} for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]]

        # 最近7天添加
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent = db.query(func.count(Citation.id)).filter(
            Citation.project_id == project_id,
            Citation.added_at >= seven_days_ago
        ).scalar() or 0

        return CitationStatsResponse(
            total_citations=total,
            by_type=by_type,
            by_year=by_year,
            top_tags=top_tags,
            recent_additions=recent
        )

    except Exception as e:
        logger.error(f"❌ 获取引用统计失败: {e}")
        raise DatabaseException(
            message="获取引用统计失败",
            cause=e
        )


@router.post("/citations/batch")
async def batch_create_citations(
    citations: List[CitationCreate],
    db: Session = Depends(get_db)
):
    """批量创建引用（用于导入BibTeX等）"""
    try:
        created = []
        errors = []

        for idx, citation_data in enumerate(citations):
            try:
                citation = Citation(**citation_data.dict())
                db.add(citation)
                db.flush()
                created.append(citation.id)
            except Exception as e:
                errors.append({"index": idx, "error": str(e)})

        db.commit()

        logger.info(f"✅ 批量创建引用: 成功{len(created)}条, 失败{len(errors)}条")
        return success_response(
            data={
                "created_count": len(created),
                "created_ids": created,
                "errors": errors
            }
        )

    except Exception as e:
        db.rollback()
        logger.error(f"❌ 批量创建引用失败: {e}")
        raise DatabaseException(
            message="批量创建引用失败",
            cause=e
        )
