"""
蒸馏功能API端点
Distillation API - 知识蒸馏与洞察提取
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.distillation_engine import DistillationEngine
from app.models.distillation import DistilledUnit

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Models ====================
class DistillationRequest(BaseModel):
    """蒸馏请求"""
    project_id: int
    force_refresh: bool = False


class DistilledUnitResponse(BaseModel):
    """蒸馏产物响应"""
    id: int
    project_id: int
    unit_type: str
    title: str
    content: str
    credibility: float
    confidence: float
    source_count: int
    created_at: str

    class Config:
        from_attributes = True


class DistillationResultResponse(BaseModel):
    """蒸馏结果响应"""
    project_id: int
    total_units: int
    breakdown: Dict[str, int]
    timestamp: str


class SourceResponse(BaseModel):
    """来源响应"""
    chunk_id: int
    content: str
    document: str


# ==================== API Endpoints ====================

@router.post("/api/projects/{project_id}/distill", response_model=DistillationResultResponse)
async def distill_project(
    project_id: int,
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    启动项目蒸馏

    从结构化数据中提炼6类知识单元：
    - insight: 核心洞察
    - quote: 经典原话
    - model: 思维模型
    - case: 案例与应用
    - action: 行动建议
    - method: 方法论沉淀
    """
    try:
        engine = DistillationEngine(db)

        # 检查是否已经蒸馏过
        existing_units = engine.get_distilled_units(project_id)

        if existing_units and not force_refresh:
            # 返回现有统计
            breakdown = {}
            for unit in existing_units:
                breakdown[unit.unit_type] = breakdown.get(unit.unit_type, 0) + 1

            return {
                "project_id": project_id,
                "total_units": len(existing_units),
                "breakdown": breakdown,
                "timestamp": existing_units[0].created_at.isoformat() if existing_units else ""
            }

        # 执行蒸馏
        result = engine.distill_project(project_id)

        return result

    except Exception as e:
        logger.error(f"蒸馏项目 {project_id} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"蒸馏失败: {str(e)}")


@router.get("/api/projects/{project_id}/distilled-units", response_model=List[DistilledUnitResponse])
async def get_distilled_units(
    project_id: int,
    unit_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取项目的蒸馏产物

    可选参数:
    - unit_type: 筛选类型 (insight/quote/model/case/action/method)
    """
    try:
        engine = DistillationEngine(db)
        units = engine.get_distilled_units(project_id, unit_type)

        return [
            {
                "id": unit.id,
                "project_id": unit.project_id,
                "unit_type": unit.unit_type,
                "title": unit.title,
                "content": unit.content,
                "credibility": unit.credibility,
                "confidence": unit.confidence,
                "source_count": len(unit.source_chunks.split(",")) if unit.source_chunks else 0,
                "created_at": unit.created_at.isoformat()
            }
            for unit in units
        ]

    except Exception as e:
        logger.error(f"获取蒸馏产物失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/api/distilled-units/{unit_id}", response_model=DistilledUnitResponse)
async def get_distilled_unit(
    unit_id: int,
    db: Session = Depends(get_db)
):
    """获取单个蒸馏产物详情"""
    try:
        unit = db.query(DistilledUnit).filter(DistilledUnit.id == unit_id).first()

        if not unit:
            raise HTTPException(status_code=404, detail="蒸馏产物不存在")

        return {
            "id": unit.id,
            "project_id": unit.project_id,
            "unit_type": unit.unit_type,
            "title": unit.title,
            "content": unit.content,
            "credibility": unit.credibility,
            "confidence": unit.confidence,
            "source_count": len(unit.source_chunks.split(",")) if unit.source_chunks else 0,
            "created_at": unit.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取蒸馏产物 {unit_id} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/api/distilled-units/{unit_id}/sources", response_model=List[SourceResponse])
async def get_unit_sources(
    unit_id: int,
    db: Session = Depends(get_db)
):
    """
    获取蒸馏产物的来源

    返回该产物所依据的原始chunk和文档信息
    """
    try:
        engine = DistillationEngine(db)
        sources = engine.get_unit_sources(unit_id)

        return sources

    except Exception as e:
        logger.error(f"获取蒸馏产物 {unit_id} 来源失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取来源失败: {str(e)}")


@router.delete("/api/distilled-units/{unit_id}")
async def delete_distilled_unit(
    unit_id: int,
    db: Session = Depends(get_db)
):
    """删除蒸馏产物"""
    try:
        unit = db.query(DistilledUnit).filter(DistilledUnit.id == unit_id).first()

        if not unit:
            raise HTTPException(status_code=404, detail="蒸馏产物不存在")

        db.delete(unit)
        db.commit()

        return {"message": "删除成功", "unit_id": unit_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除蒸馏产物 {unit_id} 失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/api/projects/{project_id}/distillation/stats")
async def get_distillation_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目蒸馏统计

    返回各类蒸馏产物的数量和平均评分
    """
    try:
        from sqlalchemy import func

        stats = db.query(
            DistilledUnit.unit_type,
            func.count(DistilledUnit.id).label('count'),
            func.avg(DistilledUnit.credibility).label('avg_credibility'),
            func.avg(DistilledUnit.confidence).label('avg_confidence')
        ).filter(
            DistilledUnit.project_id == project_id
        ).group_by(
            DistilledUnit.unit_type
        ).all()

        result = {
            "project_id": project_id,
            "total": sum(s.count for s in stats),
            "by_type": {
                s.unit_type: {
                    "count": s.count,
                    "avg_credibility": round(s.avg_credibility or 0, 2),
                    "avg_confidence": round(s.avg_confidence or 0, 2)
                }
                for s in stats
            }
        }

        return result

    except Exception as e:
        logger.error(f"获取蒸馏统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
