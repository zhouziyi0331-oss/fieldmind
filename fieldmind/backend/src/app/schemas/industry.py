"""业态分析相关的Pydantic schemas"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any


class IndustryCategoryBase(BaseModel):
    """业态类别基础信息"""
    category_id: str
    name: str
    description: Optional[str] = None


class IndustryCategoryResponse(IndustryCategoryBase):
    """业态类别响应"""
    id: str
    document_count: int
    entity_count: int
    created_at: datetime
    updated_at: datetime
    last_analyzed: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IndustryCategoryListResponse(BaseModel):
    """业态类别列表响应"""
    categories: List[IndustryCategoryResponse]
    total: int


class IndustryOverview(BaseModel):
    """业态概览"""
    summary: str
    key_findings: List[str]
    document_count: int


class IndustryDetailedAnalysis(BaseModel):
    """业态详细分析"""
    current_status: str
    trends: List[str]
    challenges: List[str]
    opportunities: List[str]


class RelatedEntity(BaseModel):
    """相关实体"""
    type: str  # person, place, organization
    name: str
    count: int


class TimelineItem(BaseModel):
    """时间线项"""
    date: datetime
    event: str


class RelatedDocument(BaseModel):
    """相关文档"""
    id: str
    title: str
    relevance_score: float


class IndustryDetailResponse(BaseModel):
    """业态详细信息响应"""
    category: str
    overview: IndustryOverview
    detailed_analysis: IndustryDetailedAnalysis
    related_entities: List[RelatedEntity]
    timeline: List[TimelineItem]
    documents: List[RelatedDocument]


class IndustryStatistics(BaseModel):
    """业态统计"""
    total_documents: int
    entity_distribution: Dict[str, int]
    temporal_distribution: Dict[str, int]
    keyword_frequency: Dict[str, int]


class IndustryTrendsResponse(BaseModel):
    """业态趋势响应"""
    time_series: List[Dict[str, Any]]
    trend_direction: str  # increasing, decreasing, stable
    key_observations: List[str]
