"""编年史 API - 时间线智能关联和可视化"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.chronicle_service import ChronicleService
from app.core.responses import APIResponse

router = APIRouter(prefix="/api/chronicle", tags=["编年史"])


class UpdateIntelligenceRequest(BaseModel):
    """更新事件智能分析请求"""
    event_id: str = Field(..., description="事件ID")
    context_window_days: int = Field(90, ge=7, le=365, description="上下文窗口天数")


class BatchUpdateRequest(BaseModel):
    """批量更新智能分析请求"""
    project_id: int = Field(..., description="项目ID")
    year: Optional[int] = Field(None, description="指定年份（可选）")


@router.post("/events/{event_id}/analyze")
async def analyze_event(
    event_id: str,
    request: UpdateIntelligenceRequest,
    db: Session = Depends(get_db)
):
    """
    分析单个事件的智能关联

    - 识别因果关系（前置事件、后续事件）
    - 提取主题标签
    - 识别关键人物和地点
    - 生成叙事摘要
    """
    try:
        service = ChronicleService(db)
        event = await service.update_event_intelligence(
            event_id=event_id,
            context_window_days=request.context_window_days
        )

        return APIResponse(
            success=True,
            data={
                "id": event.id,
                "title": event.title,
                "date": event.date.isoformat(),
                "relations": event.relations,
                "theme_tags": event.theme_tags,
                "key_persons": event.key_persons,
                "key_locations": event.key_locations,
                "narrative_summary": event.narrative_summary
            },
            message="事件关联分析完成"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/batch-analyze")
async def batch_analyze(
    request: BatchUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量分析项目的所有事件（异步任务）

    - 可指定年份，只分析某一年的事件
    - 后台任务执行，立即返回
    """
    try:
        service = ChronicleService(db)

        # 添加后台任务
        background_tasks.add_task(
            service.batch_update_intelligence,
            project_id=request.project_id,
            year=request.year
        )

        return APIResponse(
            success=True,
            data={"status": "processing"},
            message="批量分析任务已启动，将在后台执行"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.get("/projects/{project_id}/years")
async def get_years(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的所有年份列表（用于编年史目录）

    返回示例：
    ```json
    {
        "years": [2020, 2021, 2022, 2023]
    }
    ```
    """
    try:
        service = ChronicleService(db)
        years = service.get_chronicle_years(project_id)

        return APIResponse(
            success=True,
            data={"years": years},
            message="获取年份列表成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/projects/{project_id}/years/{year}")
async def get_chronicle_by_year(
    project_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """
    获取某一年的编年史数据（用于前端时间轴展示）

    返回示例：
    ```json
    {
        "year": 2020,
        "events": [
            {
                "id": "uuid",
                "date": "2020-03-15",
                "title": "村委会选举",
                "narrative": "村委会完成换届选举，李明当选新一届村长...",
                "theme_tags": ["村委会选举", "民主治理"],
                "key_persons": ["李明", "王书记"],
                "key_locations": ["XX村", "村委会"],
                "relations": {
                    "causes": ["event_id1"],
                    "effects": ["event_id2"],
                    "related": []
                }
            }
        ],
        "theme_summary": {
            "村委会选举": 2,
            "土地改革": 5
        }
    }
    ```
    """
    try:
        service = ChronicleService(db)
        chronicle = service.get_chronicle_by_year(project_id, year)

        return APIResponse(
            success=True,
            data=chronicle,
            message=f"获取 {year} 年编年史成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/events/{event_id}/narrative")
async def get_event_narrative(
    event_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个事件的详细信息（包括叙事摘要和关联关系）

    用于前端点击事件时展开显示
    """
    try:
        from app.models.timeline import TimelineEvent

        event = db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail=f"事件 {event_id} 不存在")

        return APIResponse(
            success=True,
            data={
                "id": event.id,
                "date": event.date.isoformat(),
                "title": event.title,
                "description": event.description,
                "narrative_summary": event.narrative_summary,
                "category": event.category,
                "theme_tags": event.theme_tags or [],
                "key_persons": event.key_persons or [],
                "key_locations": event.key_locations or [],
                "relations": event.relations or {},
                "location": event.location,
                "document_ids": event.document_ids or [],
                "confidence": event.confidence
            },
            message="获取事件详情成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/projects/{project_id}/themes")
async def get_all_themes(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的所有主题标签及其事件数量

    返回示例：
    ```json
    {
        "themes": [
            {"name": "土地改革", "count": 15},
            {"name": "村委会选举", "count": 8},
            {"name": "基础设施", "count": 12}
        ]
    }
    ```

    用于前端主题筛选
    """
    try:
        from app.models.timeline import TimelineEvent
        from sqlalchemy import func

        # TODO: 添加 project_id 过滤
        # 目前获取所有事件的主题
        events = db.query(TimelineEvent).all()

        theme_count = {}
        for event in events:
            if event.theme_tags:
                for theme in event.theme_tags:
                    theme_count[theme] = theme_count.get(theme, 0) + 1

        themes = [
            {"name": name, "count": count}
            for name, count in sorted(theme_count.items(), key=lambda x: x[1], reverse=True)
        ]

        return APIResponse(
            success=True,
            data={"themes": themes},
            message="获取主题列表成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")
