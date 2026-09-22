"""定时任务相关的Schema"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
try:
    from croniter import croniter
except ImportError:
    croniter = None


def validate_cron_expression(value: str) -> None:
    """校验 cron 表达式；可选依赖缺失时做保守的 5/6 段形状校验。"""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("cron表达式不能为空")
    if croniter is not None:
        croniter(value)
        return

    fields = value.split()
    if len(fields) not in {5, 6} or any(not field or len(field) > 100 for field in fields):
        raise ValueError("croniter未安装时仅能校验5段或6段cron表达式，请安装croniter获得完整校验")


class ScheduledTaskCreate(BaseModel):
    """创建定时任务请求"""
    project_id: Optional[int] = Field(None, description="项目ID，某些任务类型可为空")
    name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: str = Field(..., description="任务类型: crawler, report, quality_check, export, cleanup")
    cron_expression: str = Field(..., description="Cron表达式")
    is_active: bool = Field(True, description="是否激活")
    config: Dict[str, Any] = Field(..., description="任务配置")

    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v):
        valid_types = ['crawler', 'report', 'quality_check', 'export', 'cleanup']
        if v not in valid_types:
            raise ValueError(f'task_type必须是以下之一: {", ".join(valid_types)}')
        return v

    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v):
        try:
            validate_cron_expression(v)
        except Exception as e:
            raise ValueError(f'无效的cron表达式: {str(e)}')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": 1,
                "name": "每日爬取新闻",
                "description": "每天早上8点爬取最新新闻",
                "task_type": "crawler",
                "cron_expression": "0 8 * * *",
                "is_active": True,
                "config": {
                    "urls": ["https://example.com/news"],
                    "max_depth": 2
                }
            }
        }
    )


class ScheduledTaskUpdate(BaseModel):
    """更新定时任务请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None

    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v):
        if v is not None:
            try:
                validate_cron_expression(v)
            except Exception as e:
                raise ValueError(f'无效的cron表达式: {str(e)}')
        return v


class ScheduledTaskResponse(BaseModel):
    """定时任务响应"""
    id: int
    task_id: str
    project_id: Optional[int]
    name: str
    description: Optional[str]
    task_type: str
    cron_expression: str
    is_active: bool
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_by: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskExecutionResponse(BaseModel):
    """定时任务执行记录响应"""
    id: int
    task_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    duration_seconds: float

    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskListResponse(BaseModel):
    """定时任务列表响应"""
    tasks: List[ScheduledTaskResponse]
    total: int
    limit: int
    offset: int


class ExecutionListResponse(BaseModel):
    """执行记录列表响应"""
    executions: List[ScheduledTaskExecutionResponse]
    total: int
    limit: int
    offset: int


class TaskRunRequest(BaseModel):
    """手动运行任务请求"""
    task_id: str = Field(..., description="任务ID")


class TaskRunResponse(BaseModel):
    """手动运行任务响应"""
    execution_id: int
    task_id: str
    message: str
    started_at: datetime
