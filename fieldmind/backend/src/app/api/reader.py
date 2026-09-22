"""
阅读器 API 路由
Reader API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.knowledge import ReaderView, WikiPage

router = APIRouter(prefix="/reader", tags=["Reader"])


@router.get("/timeline/{document_id}")
async def get_timeline(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取时间轴视图
    """
    stmt = select(ReaderView).where(
        ReaderView.document_id == document_id,
        ReaderView.view_type == "timeline"
    )
    result = await db.execute(stmt)
    view = result.scalar_one_or_none()

    if not view:
        raise HTTPException(status_code=404, detail="Timeline view not found")

    return {
        "document_id": document_id,
        "view_type": "timeline",
        "content": view.content,
        "metadata": view.metadata or {}
    }


@router.get("/topics/{document_id}")
async def get_topics(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取主题聚类视图
    """
    stmt = select(ReaderView).where(
        ReaderView.document_id == document_id,
        ReaderView.view_type == "topics"
    )
    result = await db.execute(stmt)
    view = result.scalar_one_or_none()

    if not view:
        raise HTTPException(status_code=404, detail="Topics view not found")

    return {
        "document_id": document_id,
        "view_type": "topics",
        "content": view.content,
        "metadata": view.metadata or {}
    }


@router.get("/network/{document_id}")
async def get_network(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取人物网络图
    """
    stmt = select(ReaderView).where(
        ReaderView.document_id == document_id,
        ReaderView.view_type == "network"
    )
    result = await db.execute(stmt)
    view = result.scalar_one_or_none()

    if not view:
        raise HTTPException(status_code=404, detail="Network view not found")

    return {
        "document_id": document_id,
        "view_type": "network",
        "content": view.content,
        "metadata": view.metadata or {}
    }


@router.get("/wiki/{document_id}")
async def list_wiki_pages(
    document_id: str,
    category: Optional[str] = Query(None, description="分类过滤"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出 Wiki 页面
    """
    stmt = select(WikiPage).where(WikiPage.document_id == document_id)

    if category:
        stmt = stmt.where(WikiPage.category == category)

    stmt = stmt.order_by(WikiPage.title)
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    pages = result.scalars().all()

    return [
        {
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "tags": p.tags or [],
            "related_pages": p.related_pages or [],
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat()
        }
        for p in pages
    ]


@router.get("/wiki/{document_id}/{page_id}")
async def get_wiki_page(
    document_id: str,
    page_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取 Wiki 页面内容（Markdown）
    """
    stmt = select(WikiPage).where(
        WikiPage.document_id == document_id,
        WikiPage.id == page_id
    )
    result = await db.execute(stmt)
    page = result.scalar_one_or_none()

    if not page:
        raise HTTPException(status_code=404, detail="Wiki page not found")

    return {
        "id": page.id,
        "title": page.title,
        "content": page.content,
        "category": page.category,
        "tags": page.tags or [],
        "related_pages": page.related_pages or [],
        "version": page.version,
        "created_at": page.created_at.isoformat(),
        "updated_at": page.updated_at.isoformat()
    }


@router.get("/wiki/{document_id}/search")
async def search_wiki(
    document_id: str,
    query: str = Query(..., min_length=1, description="搜索查询"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    搜索 Wiki 页面
    """
    from sqlalchemy import or_

    stmt = select(WikiPage).where(
        WikiPage.document_id == document_id,
        or_(
            WikiPage.title.ilike(f"%{query}%"),
            WikiPage.content.ilike(f"%{query}%")
        )
    ).limit(limit)

    result = await db.execute(stmt)
    pages = result.scalars().all()

    return [
        {
            "id": p.id,
            "title": p.title,
            "category": p.category,
            "snippet": p.content[:200] + "..." if len(p.content) > 200 else p.content
        }
        for p in pages
    ]
