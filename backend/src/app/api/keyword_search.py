"""
关键词智能检索 API
核心功能：在视频/音频/文档中搜索关键词，返回精确时间点
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.keyword_search_service import KeywordSearchService
from app.core.exceptions import DatabaseException


router = APIRouter(tags=["关键词检索"])


class KeywordSearchRequest(BaseModel):
    keyword: str
    include_videos: bool = True
    include_audios: bool = True
    include_documents: bool = True


class VideoTimestamp(BaseModel):
    video_id: int
    filename: str
    timestamp: str  # HH:MM:SS
    timestamp_seconds: float
    context: str
    match_position: int


class AudioTimestamp(BaseModel):
    audio_id: int
    filename: str
    timestamp: str
    timestamp_seconds: float
    context: str
    match_position: int


class DocumentMatch(BaseModel):
    doc_id: int
    filename: str
    matches: List[dict]


class KeywordSearchResponse(BaseModel):
    keyword: str
    total_mentions: int
    documents: List[DocumentMatch]
    video_timestamps: List[VideoTimestamp]
    audio_timestamps: List[AudioTimestamp]
    timeline: List[dict]
    related_keywords: List[str]


@router.post("/projects/{project_id}/search", response_model=KeywordSearchResponse)
async def search_by_keyword(
    project_id: int,
    request: KeywordSearchRequest,
    db: Session = Depends(get_db)
):
    """
    关键词智能检索

    **核心功能**：
    - 在所有项目材料中搜索关键词
    - 视频/音频返回精确时间点（如：00:03:25）
    - 文档返回匹配位置和上下文
    - 生成关键词时间线
    - 推荐相关关键词

    **示例**：
    ```
    输入：关键词 = "布依族"
    输出：
    - 视频1：在 00:03:25 提到"布依族的山歌..."
    - 视频1：在 00:12:40 提到"布依族的传统..."
    - 音频2：在 00:05:15 提到"布依族节日..."
    - 文档3：在第2段提到"布依族文化..."
    ```
    """
    try:
        service = KeywordSearchService(db)
        results = await service.search_keyword(
            project_id=project_id,
            keyword=request.keyword,
            include_videos=request.include_videos,
            include_audios=request.include_audios,
            include_documents=request.include_documents
        )
        return results
    except Exception as e:
        raise DatabaseException(
            message="关键词搜索失败",
            operation="search_keyword",
            details={"error": str(e)}
        )


@router.get("/projects/{project_id}/keywords/top")
async def get_top_keywords(
    project_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    获取项目的 Top N 关键词
    """
    service = KeywordSearchService(db)
    keywords = await service.get_top_keywords(project_id, limit)
    return {"project_id": project_id, "keywords": keywords}


@router.get("/projects/{project_id}/keywords/timeline")
async def get_keyword_timeline(
    project_id: int,
    keyword: str,
    db: Session = Depends(get_db)
):
    """
    获取关键词的时间线
    """
    service = KeywordSearchService(db)
    timeline = await service.get_keyword_timeline(project_id, keyword)
    return {"keyword": keyword, "timeline": timeline}
