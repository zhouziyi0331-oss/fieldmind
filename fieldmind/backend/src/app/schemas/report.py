"""报告相关的Pydantic schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.report import ReportStatus, ReportType


class TimeRange(BaseModel):
    """时间范围"""
    start: datetime
    end: datetime


class ReportInclude(BaseModel):
    """报告包含选项"""
    charts: bool = True
    maps: bool = True
    tables: bool = True
    wordcloud: bool = True


class DataSources(BaseModel):
    """数据源"""
    document_ids: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class ReportGenerateRequest(BaseModel):
    """生成报告请求"""
    title: str = Field(..., min_length=1, max_length=500)
    report_type: ReportType = ReportType.RESEARCH
    time_range: Optional[TimeRange] = None
    include: ReportInclude = ReportInclude()
    data_sources: DataSources = DataSources()
    format: str = Field("docx", pattern="^(docx|pdf|html)$")


class ReportContent(BaseModel):
    """报告内容"""
    summary: str
    sections: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    statistics: Dict[str, Any]


class ReportResponse(BaseModel):
    """报告响应"""
    id: str
    task_id: Optional[str] = None
    title: str
    report_type: ReportType
    status: ReportStatus
    progress: int
    content: Optional[ReportContent] = None
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    file_size: Optional[str] = None
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SummaryDocumentRequest(BaseModel):
    """总结文档请求"""
    document_ids: List[str]
    summary_type: str = Field("comprehensive", pattern="^(comprehensive|executive|technical)$")
    max_length: Optional[int] = Field(None, gt=0)
    include_citations: bool = True


class SummaryDocumentResponse(BaseModel):
    """总结文档响应"""
    summary: str
    sections: List[Dict[str, Any]]
    citations: Optional[List[Dict[str, str]]] = None
    word_count: int
