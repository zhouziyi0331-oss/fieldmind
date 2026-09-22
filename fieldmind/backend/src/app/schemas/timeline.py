"""时间线相关的Pydantic schemas"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class LocationData(BaseModel):
    """地理位置数据"""
    lat: float
    lng: float
    name: Optional[str] = None


class TimelineEventBase(BaseModel):
    """时间线事件基础信息"""
    date: datetime
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = None


class TimelineEventCreate(TimelineEventBase):
    """创建时间线事件"""
    entities: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None
    location: Optional[LocationData] = None
    source: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = None


class TimelineEventUpdate(BaseModel):
    """更新时间线事件"""
    date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    entities: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None
    location: Optional[LocationData] = None
    tags: Optional[List[str]] = None


class TimelineEventResponse(TimelineEventBase):
    """时间线事件响应"""
    id: str
    entities: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None
    location: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    confidence: Optional[float] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimelineEventListResponse(BaseModel):
    """时间线事件列表响应"""
    events: List[TimelineEventResponse]
    total: int


class TimelineOrganizeRequest(BaseModel):
    """时间线组织请求"""
    document_ids: List[str]
    auto_extract_dates: bool = True
    grouping: str = Field("day", pattern="^(day|month|year)$")


class TimelineOrganizeResponse(BaseModel):
    """时间线组织响应"""
    events_created: int
    events_updated: int
    timeline_structure: Dict[str, Any]
