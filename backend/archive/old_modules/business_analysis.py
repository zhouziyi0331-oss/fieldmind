"""
业态分析系统 API
分析现有业态 + 建议新业态（基于调研数据，有理有据）
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.business_analysis_service import BusinessAnalysisService
from app.schemas.response import success_response, error_response


router = APIRouter(tags=["业态分析"])


class ExistingFormat(BaseModel):
    name: str
    status: str
    scale: str
    description: str


class SuggestedFormat(BaseModel):
    name: str
    feasibility_score: int
    reason: str
    investment: str
    revenue_potential: str
    risk_points: List[str]
    required_conditions: List[str]
    evidence: List[str]
    implementation_steps: List[str]


class BusinessAnalysisResponse(BaseModel):
    project_id: int
    existing_formats: List[ExistingFormat]
    suggested_formats: List[SuggestedFormat]
    synergy_analysis: str
    recommendations: List[str]


@router.post("/projects/{project_id}/analyze", response_model=BusinessAnalysisResponse)
async def analyze_business_formats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    业态分析系统

    **核心功能**：
    1. 梳理现有业态（咖啡馆、民宿、研学基地等）
    2. 建议可能的新业态
    3. 可行性评分（基于调研数据）
    4. 所需资源和条件
    5. 风险点分析
    6. 业态协同效应分析

    **示例**：

    **现有业态**：
    - 咖啡馆（运营中，小型）
    - 民宿（筹备中，5间房）

    **建议新业态**：

    1. **研学基地**
       - 可行性：78/100
       - 理由：有丰富的非遗资源，学校研学需求大
       - 所需投资：50-100万
       - 风险：安全设施、住宿条件需完善
       - 证据：调研中提到"XX小学多次咨询研学活动"

    2. **茶文化体验馆**
       - 可行性：85/100
       - 理由：村落有优质茶叶资源，距城市1.5小时车程
       - 建议模式：茶文化体验 + 轻食 + 手工体验
       - 风险：季节性客流

    **协同效应**：
    - 咖啡馆 + 研学基地：研学团队用餐需求
    - 民宿 + 茶体验：住宿客人的配套体验
    """
    try:
        service = BusinessAnalysisService(db)
        results = await service.analyze_business_formats(project_id)
        return success_response(data=results)
    except Exception as e:
        return error_response(
            code="ANALYSIS_FAILED",
            message=f"业态分析失败: {str(e)}"
        )


@router.get("/projects/{project_id}/formats/existing/")
async def get_existing_formats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取现有业态列表
    """
    service = BusinessAnalysisService(db)
    formats = await service.get_existing_formats(project_id)
    return success_response(
        data={
            "project_id": project_id,
            "existing_formats": formats
        }
    )


@router.get("/projects/{project_id}/synergy/")
async def analyze_synergy(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    分析业态协同效应
    """
    service = BusinessAnalysisService(db)
    synergy = await service.analyze_synergy(project_id)
    return success_response(
        data={
            "project_id": project_id,
            "synergy": synergy
        }
    )
