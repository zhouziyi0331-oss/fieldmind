"""
时间线 API - 链路十一：从文档自动提取时间事件并构建编年史
从文档中提取时间事件并构建时间线
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import re
from datetime import datetime
from collections import defaultdict

from app.core.database import get_db
from app.models.project import ProjectDocument, Project
from app.models.timeline import TimelineEvent
from app.tools.entity import create_engine

router = APIRouter(tags=["timeline"])
logger = logging.getLogger(__name__)


# ==================== 新增Schema ====================

class BuildTimelineRequest(BaseModel):
    """构建时间线请求"""
    project_id: int
    document_ids: Optional[List[int]] = None  # 空表示处理所有文档
    force_rebuild: bool = False


class TimelineExtractor:
    """时间线事件提取器"""

    def __init__(self):
        # 日期模式
        self.date_patterns = [
            # 中文日期格式
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', 'yyyy-mm-dd'),
            (r'(\d{4})年(\d{1,2})月', 'yyyy-mm'),
            (r'(\d{4})年', 'yyyy'),
            # 英文日期格式
            (r'(\d{4})-(\d{2})-(\d{2})', 'yyyy-mm-dd'),
            (r'(\d{4})/(\d{2})/(\d{2})', 'yyyy-mm-dd'),
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'mm-dd-yyyy'),
        ]

    def extract_events(self, text: str, doc_id: int, doc_name: str) -> List[Dict[str, Any]]:
        """从文本中提取时间事件"""
        events = []
        sentences = re.split(r'[。！？\n.!?]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            # 提取日期
            date_info = self._extract_date(sentence)
            if date_info:
                events.append({
                    'date': date_info['date'],
                    'date_string': date_info['date_string'],
                    'description': sentence[:200],  # 限制长度
                    'document_id': doc_id,
                    'document_name': doc_name,
                    'timestamp': date_info['timestamp'],
                })

        return events

    def _extract_date(self, text: str) -> Dict[str, Any] | None:
        """从文本中提取日期"""
        for pattern, format_type in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    if format_type == 'yyyy-mm-dd':
                        if '-' in match.group():
                            year, month, day = match.groups()
                        else:
                            year, month, day = match.groups()
                        date_obj = datetime(int(year), int(month), int(day))
                        date_string = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                    elif format_type == 'yyyy-mm':
                        year, month = match.groups()
                        date_obj = datetime(int(year), int(month), 1)
                        date_string = f"{year}-{month.zfill(2)}"

                    elif format_type == 'yyyy':
                        year = match.group(1)
                        date_obj = datetime(int(year), 1, 1)
                        date_string = year

                    elif format_type == 'mm-dd-yyyy':
                        month, day, year = match.groups()
                        date_obj = datetime(int(year), int(month), int(day))
                        date_string = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                    else:
                        continue

                    return {
                        'date': date_string,
                        'date_string': match.group(),
                        'timestamp': int(date_obj.timestamp()),
                    }

                except (ValueError, IndexError):
                    continue

        return None


# 全局提取器实例
extractor = TimelineExtractor()


# ==================== 新API：构建时间线到数据库 ====================

@router.post("/build")
async def build_timeline(
    request: BuildTimelineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    从文档构建时间线并保存到数据库（链路十一核心功能）

    - 自动提取文档中的时间表达式
    - 创建TimelineEvent记录
    - 关联到文档和项目
    """
    try:
        entity_service = create_engine()

        # 验证项目存在
        project = db.query(Project).filter(Project.id == request.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取待处理文档
        query = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == request.project_id,
            ProjectDocument.status == "completed",
            ProjectDocument.text_content.isnot(None)
        )

        if request.document_ids:
            query = query.filter(ProjectDocument.id.in_(request.document_ids))

        documents = query.all()

        if not documents:
            return {
                "status": "completed",
                "message": "没有可处理的文档",
                "stats": {"documents_processed": 0, "events_created": 0}
            }

        logger.info(f"🕐 开始为项目 {request.project_id} 构建时间线，处理 {len(documents)} 个文档")

        # 如果强制重建，删除已有事件
        if request.force_rebuild:
            doc_ids = [doc.id for doc in documents]
            deleted = db.query(TimelineEvent).filter(
                TimelineEvent.document_ids.overlap(doc_ids)
            ).delete(synchronize_session=False)
            db.commit()
            logger.info(f"⚠️ 强制重建：删除了 {deleted} 个已有事件")

        total_events = 0

        for doc in documents:
            # 提取时间表达式
            time_expressions = entity_service.extract_time_expressions(doc.text_content)

            for time_expr in time_expressions:
                # 检查是否已存在相同事件
                existing = db.query(TimelineEvent).filter(
                    TimelineEvent.date == time_expr['parsed'],
                    TimelineEvent.document_ids.contains([doc.id])
                ).first()

                if not existing:
                    # 创建新事件
                    event = TimelineEvent(
                        date=time_expr['parsed'],
                        title=f"{doc.filename} - {time_expr['raw']}",
                        description=f"从文档中提取的时间点：{time_expr['raw']}",
                        category="document_extraction",
                        document_ids=[doc.id],
                        source=doc.filename,
                        confidence=time_expr['confidence'],
                        tags=["auto-extracted", f"project-{request.project_id}"]
                    )
                    db.add(event)
                    total_events += 1

        db.commit()
        logger.info(f"✅ 时间线构建完成：创建 {total_events} 个事件")

        return {
            "status": "completed",
            "message": f"时间线构建完成：{total_events} 个事件",
            "stats": {
                "documents_processed": len(documents),
                "events_created": total_events
            }
        }

    except Exception as e:
        logger.error(f"构建时间线失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


@router.get("/events")
async def get_timeline_events(
    project_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取时间线事件（从数据库读取）

    - project_id: 项目ID（必填）
    - start_date: 开始日期 YYYY-MM-DD
    - end_date: 结束日期 YYYY-MM-DD
    - category: 事件分类
    - limit: 返回数量
    """
    # 获取项目文档ID
    doc_ids = [doc.id for doc in db.query(ProjectDocument.id).filter(
        ProjectDocument.project_id == project_id
    ).all()]

    if not doc_ids:
        return {"events": [], "total": 0}

    # 查询事件（使用contains而不是overlap，因为PostgreSQL的overlap仅用于数组类型）
    # 使用any_来检查JSON数组中是否包含任何doc_id
    from sqlalchemy import or_, cast, Integer
    from sqlalchemy.dialects.postgresql import ARRAY

    query = db.query(TimelineEvent).filter(
        TimelineEvent.document_ids.isnot(None)
    )

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(TimelineEvent.date >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(TimelineEvent.date <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    if category:
        query = query.filter(TimelineEvent.category == category)

    # 按日期倒序
    query = query.order_by(TimelineEvent.date.desc())

    total = query.count()
    all_events = query.limit(limit * 3).all()  # 获取更多以便过滤

    # 过滤：只返回与项目相关的事件
    relevant_events = []
    for event in all_events:
        if event.document_ids and any(doc_id in doc_ids for doc_id in event.document_ids):
            relevant_events.append(event)
            if len(relevant_events) >= limit:
                break

    return {
        "events": [
            {
                "id": event.id,
                "date": event.date.isoformat(),
                "title": event.title,
                "description": event.description,
                "category": event.category,
                "document_ids": event.document_ids,
                "source": event.source,
                "confidence": event.confidence,
                "tags": event.tags,
                "created_at": event.created_at.isoformat()
            }
            for event in relevant_events
        ],
        "total": len(relevant_events)
    }


@router.get("/stats")
async def get_timeline_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取时间线统计信息
    """
    # 获取项目文档ID
    doc_ids = [doc.id for doc in db.query(ProjectDocument.id).filter(
        ProjectDocument.project_id == project_id
    ).all()]

    if not doc_ids:
        return {
            "total_events": 0,
            "date_range": None,
            "categories": {}
        }

    # 查询所有事件（过滤在Python层完成）
    events = db.query(TimelineEvent).filter(
        TimelineEvent.document_ids.isnot(None)
    ).all()

    # 过滤：只保留与项目相关的事件
    relevant_events = [
        event for event in events
        if event.document_ids and any(doc_id in doc_ids for doc_id in event.document_ids)
    ]

    if not relevant_events:
        return {
            "total_events": 0,
            "date_range": None,
            "categories": {}
        }

    # 统计分类
    categories = {}
    for event in relevant_events:
        cat = event.category or "uncategorized"
        categories[cat] = categories.get(cat, 0) + 1

    # 日期范围
    dates = [event.date for event in relevant_events if event.date]
    date_range = None
    if dates:
        date_range = {
            "start": min(dates).isoformat(),
            "end": max(dates).isoformat()
        }

    return {
        "total_events": len(relevant_events),
        "date_range": date_range,
        "categories": categories
    }


# ==================== 旧API：兼容保留（不持久化） ====================

# 全局提取器实例
extractor = TimelineExtractor()


@router.get("/projects/{project_id}/events")
async def get_project_timeline(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取项目的时间线事件"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取项目的所有文档
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.status == "completed"
    ).all()

    if not documents:
        return {
            "events": [],
            "statistics": {
                "total_events": 0,
                "date_range": None,
            },
            "message": "项目暂无已处理的文档"
        }

    # 提取所有事件
    all_events = []
    for doc in documents:
        if doc.text_content:
            events = extractor.extract_events(
                doc.text_content,
                doc.id,
                doc.filename
            )
            all_events.extend(events)

    # 按时间排序
    all_events.sort(key=lambda x: x['timestamp'])

    # 统计信息
    statistics = {
        "total_events": len(all_events),
        "date_range": {
            "start": all_events[0]['date'] if all_events else None,
            "end": all_events[-1]['date'] if all_events else None,
        } if all_events else None,
    }

    # 按年份分组
    events_by_year = defaultdict(list)
    for event in all_events:
        year = event['date'].split('-')[0]
        events_by_year[year].append(event)

    return {
        "events": all_events,
        "events_by_year": dict(events_by_year),
        "statistics": statistics,
    }


@router.get("/projects/{project_id}/events/grouped")
async def get_grouped_timeline(
    project_id: int,
    group_by: str = "year",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取分组的时间线数据"""
    # 获取原始事件
    timeline_data = await get_project_timeline(project_id, db)
    events = timeline_data['events']

    if not events:
        return {"groups": [], "statistics": timeline_data['statistics']}

    # 按指定方式分组
    grouped = defaultdict(list)

    for event in events:
        if group_by == "year":
            key = event['date'].split('-')[0]
        elif group_by == "month":
            parts = event['date'].split('-')
            key = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else parts[0]
        elif group_by == "document":
            key = event['document_name']
        else:
            key = event['date']

        grouped[key].append(event)

    # 转换为列表格式
    groups = [
        {
            "key": key,
            "events": events_list,
            "count": len(events_list)
        }
        for key, events_list in sorted(grouped.items())
    ]

    return {
        "groups": groups,
        "statistics": timeline_data['statistics'],
    }
