"""
SOP API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.services.sop_service import SOPService
from app.models.sop import SOPCategory, SOPStatus

router = APIRouter(prefix="/sop", tags=["SOP"])


# ========== Pydantic 模型 ==========

class SOPCreate(BaseModel):
    """创建 SOP 请求"""
    name: str = Field(..., description="SOP 唯一名称")
    display_name: str = Field(..., description="显示名称")
    category: SOPCategory = Field(..., description="分类")
    workflow: dict = Field(..., description="工作流定义")
    description: Optional[str] = Field(None, description="描述")
    project_id: Optional[int] = Field(None, description="关联项目 ID")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签")


class SOPUpdate(BaseModel):
    """更新 SOP 请求"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    workflow: Optional[dict] = None
    tags: Optional[List[str]] = None
    status: Optional[SOPStatus] = None


class SOPResponse(BaseModel):
    """SOP 响应"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    category: SOPCategory
    status: SOPStatus
    version: str
    workflow: dict
    tags: List[str]
    project_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SOPExecutionRequest(BaseModel):
    """执行 SOP 请求"""
    sop_id: int = Field(..., description="SOP ID")
    input_data: dict = Field(..., description="输入数据")
    project_id: Optional[int] = Field(None, description="项目 ID")


class SOPExecutionResponse(BaseModel):
    """SOP 执行响应"""
    id: int
    sop_id: int
    project_id: Optional[int]
    status: str
    input_data: dict
    output_data: Optional[dict]
    error_message: Optional[str]
    current_step: int
    total_steps: int
    step_results: Optional[List[dict]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ========== API 端点 ==========

@router.post("/", response_model=SOPResponse, status_code=status.HTTP_201_CREATED)
async def create_sop(
    request: SOPCreate,
    db: Session = Depends(get_db)
):
    """
    创建新 SOP

    - **name**: SOP 唯一名称（英文）
    - **display_name**: 显示名称（中文）
    - **category**: 分类
    - **workflow**: 工作流定义（JSON）
    """
    service = SOPService(db)

    try:
        sop = service.create_sop(
            name=request.name,
            display_name=request.display_name,
            category=request.category,
            workflow=request.workflow,
            description=request.description,
            project_id=request.project_id,
            tags=request.tags
        )
        return sop
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建 SOP 失败: {str(e)}"
        )


@router.get("/", response_model=List[SOPResponse])
async def list_sops(
    category: Optional[SOPCategory] = None,
    status: Optional[SOPStatus] = None,
    project_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    列出 SOP

    - **category**: 筛选分类
    - **status**: 筛选状态
    - **project_id**: 筛选项目
    - **limit**: 数量限制
    """
    service = SOPService(db)
    sops = service.list_sops(
        category=category,
        status=status,
        project_id=project_id,
        limit=limit
    )
    return sops


@router.get("/{sop_id}", response_model=SOPResponse)
async def get_sop(
    sop_id: int,
    db: Session = Depends(get_db)
):
    """获取 SOP 详情"""
    service = SOPService(db)
    sop = service.get_sop(sop_id)

    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP {sop_id} 不存在"
        )

    return sop


@router.get("/by-name/{name}", response_model=SOPResponse)
async def get_sop_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """根据名称获取 SOP"""
    service = SOPService(db)
    sop = service.get_sop_by_name(name)

    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP '{name}' 不存在"
        )

    return sop


@router.patch("/{sop_id}", response_model=SOPResponse)
async def update_sop(
    sop_id: int,
    request: SOPUpdate,
    db: Session = Depends(get_db)
):
    """更新 SOP"""
    service = SOPService(db)

    update_data = request.dict(exclude_unset=True)
    sop = service.update_sop(sop_id, **update_data)

    if not sop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP {sop_id} 不存在"
        )

    return sop


@router.post("/{sop_id}/activate", response_model=dict)
async def activate_sop(
    sop_id: int,
    db: Session = Depends(get_db)
):
    """激活 SOP"""
    service = SOPService(db)

    if not service.activate_sop(sop_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP {sop_id} 不存在"
        )

    return {"message": "SOP 已激活", "sop_id": sop_id}


@router.post("/{sop_id}/archive", response_model=dict)
async def archive_sop(
    sop_id: int,
    db: Session = Depends(get_db)
):
    """归档 SOP"""
    service = SOPService(db)

    if not service.archive_sop(sop_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOP {sop_id} 不存在"
        )

    return {"message": "SOP 已归档", "sop_id": sop_id}


@router.post("/execute", response_model=SOPExecutionResponse)
async def execute_sop(
    request: SOPExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    执行 SOP

    - **sop_id**: SOP ID
    - **input_data**: 输入数据（JSON）
    - **project_id**: 项目 ID（可选）
    """
    service = SOPService(db)

    try:
        execution = await service.execute_sop(
            sop_id=request.sop_id,
            input_data=request.input_data,
            project_id=request.project_id
        )
        return execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行 SOP 失败: {str(e)}"
        )


@router.get("/executions/", response_model=List[SOPExecutionResponse])
async def list_executions(
    sop_id: Optional[int] = None,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    列出执行记录

    - **sop_id**: 筛选 SOP
    - **project_id**: 筛选项目
    - **status**: 筛选状态
    - **limit**: 数量限制
    """
    service = SOPService(db)
    executions = service.list_executions(
        sop_id=sop_id,
        project_id=project_id,
        status=status,
        limit=limit
    )
    return executions


@router.get("/executions/{execution_id}", response_model=SOPExecutionResponse)
async def get_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """获取执行记录详情"""
    service = SOPService(db)
    execution = service.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"执行记录 {execution_id} 不存在"
        )

    return execution


@router.post("/executions/{execution_id}/cancel", response_model=dict)
async def cancel_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """取消执行"""
    service = SOPService(db)

    if not service.cancel_execution(execution_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法取消执行记录 {execution_id}"
        )

    return {"message": "执行已取消", "execution_id": execution_id}
