"""
Hermes Learning API - 学习能力 API 端点
提供自学习引擎的 HTTP 接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user
from app.services.hermes_learning_engine import (
    get_learning_engine,
    LearningType,
    FeedbackScore
)
from app.schemas.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learning", tags=["Learning"])


# ==================== Pydantic 模型 ====================

class RecordExperienceRequest(BaseModel):
    """记录经验请求"""
    project_id: int
    learning_type: str = Field(..., description="learning type: tool_usage, pattern, error, workflow, skill")
    context: Dict[str, Any] = Field(..., description="执行上下文")
    action: Dict[str, Any] = Field(..., description="执行的动作")
    result: Dict[str, Any] = Field(..., description="执行结果")
    success: bool = Field(default=True, description="是否成功")
    execution_time: float = Field(default=0.0, description="执行时间（秒）")


class RecordExperienceResponse(BaseModel):
    """记录经验响应"""
    experience_id: str
    message: str = "Experience recorded successfully"


class SuggestActionRequest(BaseModel):
    """建议动作请求"""
    project_id: int
    context: Dict[str, Any] = Field(..., description="当前上下文")
    learning_type: str = Field(default="tool_usage", description="learning type")


class SuggestActionResponse(BaseModel):
    """建议动作响应"""
    suggested_action: Optional[Dict[str, Any]]
    confidence: float = Field(default=0.0, description="建议的置信度")
    based_on_experiences: int = Field(default=0, description="基于多少条历史经验")


class LearningStatsResponse(BaseModel):
    """学习统计响应"""
    total_experiences: int
    total_skills: int
    success_rate: float
    learning_types: Dict[str, int]
    recent_learning_trend: Optional[Dict[str, Any]] = None


class RegisterSkillRequest(BaseModel):
    """注册技能请求"""
    skill_name: str
    skill_type: str = Field(..., description="skill type: tool_chain, workflow, pattern")
    description: str
    trigger_conditions: List[Dict[str, Any]]
    action_sequence: List[Dict[str, Any]]
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)


class RegisterSkillResponse(BaseModel):
    """注册技能响应"""
    skill_id: str
    message: str = "Skill registered successfully"


class GetSkillsResponse(BaseModel):
    """获取技能列表响应"""
    skills: List[Dict[str, Any]]
    total: int


# ==================== API 端点 ====================

@router.post("/experience", response_model=RecordExperienceResponse)
async def record_experience(
    request: RecordExperienceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    记录一次执行经验

    用于记录 Agent 执行、工具调用、工作流运行等经验，供未来学习使用
    """
    try:
        engine = get_learning_engine()

        # 验证 learning_type
        learning_type_map = {
            "tool_usage": LearningType.TOOL_USAGE,
            "pattern": LearningType.PATTERN_RECOGNITION,
            "error": LearningType.ERROR_CORRECTION,
            "workflow": LearningType.WORKFLOW_OPTIMIZATION,
            "skill": LearningType.SKILL_CREATION
        }

        if request.learning_type not in learning_type_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid learning_type. Must be one of: {list(learning_type_map.keys())}"
            )

        learning_type = learning_type_map[request.learning_type]

        # 记录经验
        experience_id = engine.record_experience(
            project_id=request.project_id,
            learning_type=learning_type,
            context=request.context,
            action=request.action,
            result=request.result,
            success=request.success,
            execution_time=request.execution_time
        )

        logger.info(f"✅ User {current_user.id} recorded experience {experience_id}")

        return RecordExperienceResponse(
            experience_id=experience_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to record experience: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record experience: {str(e)}"
        )


@router.post("/suggest", response_model=SuggestActionResponse)
async def suggest_action(
    request: SuggestActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    基于历史经验建议下一步动作

    根据当前上下文和历史学习经验，推荐最优的执行动作
    """
    try:
        engine = get_learning_engine()

        # 验证 learning_type
        learning_type_map = {
            "tool_usage": LearningType.TOOL_USAGE,
            "pattern": LearningType.PATTERN_RECOGNITION,
            "workflow": LearningType.WORKFLOW_OPTIMIZATION
        }

        learning_type = learning_type_map.get(
            request.learning_type,
            LearningType.TOOL_USAGE
        )

        # 获取建议
        suggested_action = engine.suggest_action(
            context=request.context,
            learning_type=learning_type
        )

        # 获取相似经验数量
        similar_experiences = engine.get_similar_experiences(
            context=request.context,
            learning_type=learning_type,
            limit=10
        )

        confidence = 0.0
        if suggested_action and similar_experiences:
            # 简单的置信度计算：基于历史成功率
            successful = sum(1 for exp in similar_experiences if exp.success)
            confidence = successful / len(similar_experiences)

        return SuggestActionResponse(
            suggested_action=suggested_action,
            confidence=confidence,
            based_on_experiences=len(similar_experiences)
        )

    except Exception as e:
        logger.error(f"❌ Failed to suggest action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest action: {str(e)}"
        )


@router.get("/stats", response_model=LearningStatsResponse)
async def get_learning_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取学习统计信息

    包括：总经验数、总技能数、成功率、学习类型分布等
    """
    try:
        engine = get_learning_engine()
        stats = engine.get_stats()

        return LearningStatsResponse(**stats)

    except Exception as e:
        logger.error(f"❌ Failed to get learning stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get learning stats: {str(e)}"
        )


@router.post("/skill", response_model=RegisterSkillResponse)
async def register_skill(
    request: RegisterSkillRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    注册一个学习到的技能

    将学习到的模式、工具链、工作流注册为可复用的技能
    """
    try:
        engine = get_learning_engine()

        from app.services.hermes_learning_engine import LearnedSkill
        import uuid

        skill_id = f"skill_{uuid.uuid4().hex[:8]}"

        skill = LearnedSkill(
            skill_id=skill_id,
            skill_name=request.skill_name,
            skill_type=request.skill_type,
            description=request.description,
            trigger_conditions=request.trigger_conditions,
            action_sequence=request.action_sequence,
            confidence_score=request.confidence_score
        )

        registered_id = engine.register_skill(skill)

        logger.info(f"✅ User {current_user.id} registered skill {registered_id}")

        return RegisterSkillResponse(
            skill_id=registered_id
        )

    except Exception as e:
        logger.error(f"❌ Failed to register skill: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register skill: {str(e)}"
        )


@router.get("/skills", response_model=GetSkillsResponse)
async def get_skills(
    skill_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取已学习的技能列表

    可选过滤：skill_type (tool_chain, workflow, pattern)
    """
    try:
        engine = get_learning_engine()

        skills = []
        for skill_id, skill in engine.skills.items():
            if skill_type and skill.skill_type != skill_type:
                continue

            skills.append({
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "skill_type": skill.skill_type,
                "description": skill.description,
                "success_rate": skill.success_rate,
                "usage_count": skill.usage_count,
                "confidence_score": skill.confidence_score,
                "last_updated": skill.last_updated.isoformat()
            })

        return GetSkillsResponse(
            skills=skills,
            total=len(skills)
        )

    except Exception as e:
        logger.error(f"❌ Failed to get skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get skills: {str(e)}"
        )


@router.get("/health")
async def learning_health_check():
    """
    学习引擎健康检查
    """
    try:
        engine = get_learning_engine()
        stats = engine.get_stats()

        return success_response(
            data={
                "status": "healthy",
                "learning_enabled": True,
                "total_experiences": stats["total_experiences"],
                "total_skills": stats["total_skills"]
            }
        )
    except Exception as e:
        return success_response(
            data={
                "status": "degraded",
                "learning_enabled": False,
                "error": str(e)
            }
        )
