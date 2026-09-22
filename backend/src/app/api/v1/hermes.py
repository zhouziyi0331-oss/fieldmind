"""
Hermes学习引擎API端点

提供自学习引擎的完整功能：
1. 经验记录和查询
2. 技能管理
3. 知识蒸馏集成
4. 学习统计
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.deps import get_db
from app.services.hermes_learning_engine import (
    get_learning_engine,
    HermesLearningEngine,
    LearningType,
    FeedbackScore,
    LearningExperience,
    LearnedSkill
)

router = APIRouter()


# ==================== Pydantic 模型 ====================

class ExperienceRecordRequest(BaseModel):
    """记录经验请求"""
    project_id: int = Field(..., description="项目ID")
    learning_type: str = Field(..., description="学习类型")
    context: Dict[str, Any] = Field(..., description="任务上下文")
    action: Dict[str, Any] = Field(..., description="执行的动作")
    result: Dict[str, Any] = Field(..., description="执行结果")
    success: bool = Field(True, description="是否成功")
    execution_time: float = Field(0.0, description="执行时间(秒)")


class ExperienceResponse(BaseModel):
    """经验响应"""
    experience_id: str
    project_id: int
    learning_type: str
    success: bool
    execution_time: float
    created_at: str


class SkillResponse(BaseModel):
    """技能响应"""
    skill_id: str
    skill_name: str
    skill_type: str
    description: str
    success_rate: float
    usage_count: int
    confidence_score: float
    last_updated: str


class SyncDistillationRequest(BaseModel):
    """同步蒸馏请求"""
    project_id: int = Field(..., description="项目ID")


class HermesStatsResponse(BaseModel):
    """Hermes统计响应"""
    total_experiences: int
    total_skills: int
    success_rate: float
    learning_types: Dict[str, int]


class ActionSuggestionRequest(BaseModel):
    """动作建议请求"""
    context: Dict[str, Any] = Field(..., description="当前上下文")
    learning_type: str = Field(..., description="学习类型")


# ==================== 依赖项 ====================

def get_hermes_engine(db: Session = Depends(get_db)) -> HermesLearningEngine:
    """获取Hermes学习引擎实例"""
    engine = get_learning_engine()
    # 注入数据库会话以支持蒸馏集成
    if not engine.db:
        engine.db = db
    return engine


# ==================== 经验管理 ====================

@router.post("/experiences", response_model=ExperienceResponse, summary="记录学习经验")
async def record_experience(
    request: ExperienceRecordRequest,
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """
    记录一次执行经验

    支持的学习类型：
    - tool_usage: 工具使用学习
    - pattern: 模式识别
    - error: 错误纠正
    - workflow: 工作流优化
    - skill: 技能创建
    """
    try:
        learning_type = LearningType(request.learning_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的学习类型: {request.learning_type}"
        )

    experience_id = engine.record_experience(
        project_id=request.project_id,
        learning_type=learning_type,
        context=request.context,
        action=request.action,
        result=request.result,
        success=request.success,
        execution_time=request.execution_time
    )

    # 查找刚创建的经验
    experience = next(
        (exp for exp in engine.experiences if exp.experience_id == experience_id),
        None
    )

    if not experience:
        raise HTTPException(status_code=500, detail="经验记录失败")

    return ExperienceResponse(
        experience_id=experience.experience_id,
        project_id=experience.project_id,
        learning_type=experience.learning_type.value,
        success=experience.success,
        execution_time=experience.execution_time,
        created_at=experience.created_at.isoformat()
    )


@router.get("/experiences", response_model=List[ExperienceResponse], summary="获取经验列表")
async def get_experiences(
    project_id: Optional[int] = Query(None, description="筛选项目ID"),
    learning_type: Optional[str] = Query(None, description="筛选学习类型"),
    limit: int = Query(50, description="返回数量", ge=1, le=500),
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """获取学习经验列表"""
    experiences = engine.experiences

    # 筛选
    if project_id:
        experiences = [exp for exp in experiences if exp.project_id == project_id]

    if learning_type:
        try:
            lt = LearningType(learning_type)
            experiences = [exp for exp in experiences if exp.learning_type == lt]
        except ValueError:
            pass

    # 限制数量并倒序
    experiences = experiences[-limit:][::-1]

    return [
        ExperienceResponse(
            experience_id=exp.experience_id,
            project_id=exp.project_id,
            learning_type=exp.learning_type.value,
            success=exp.success,
            execution_time=exp.execution_time,
            created_at=exp.created_at.isoformat()
        )
        for exp in experiences
    ]


@router.post("/suggest-action", summary="建议下一步动作")
async def suggest_action(
    request: ActionSuggestionRequest,
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """基于历史经验建议下一步动作"""
    try:
        learning_type = LearningType(request.learning_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的学习类型: {request.learning_type}"
        )

    suggestion = engine.suggest_action(
        context=request.context,
        learning_type=learning_type
    )

    if suggestion is None:
        return {
            "has_suggestion": False,
            "message": "暂无相似经验"
        }

    return {
        "has_suggestion": True,
        "suggested_action": suggestion
    }


# ==================== 技能管理 ====================

@router.get("/skills", response_model=List[SkillResponse], summary="获取技能列表")
async def get_skills(
    skill_type: Optional[str] = Query(None, description="筛选技能类型"),
    min_confidence: float = Query(0.0, description="最小置信度", ge=0, le=1),
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """获取学习到的技能列表"""
    skills = list(engine.skills.values())

    # 筛选
    if skill_type:
        skills = [s for s in skills if s.skill_type == skill_type]

    skills = [s for s in skills if s.confidence_score >= min_confidence]

    # 按置信度排序
    skills.sort(key=lambda s: s.confidence_score, reverse=True)

    return [
        SkillResponse(
            skill_id=skill.skill_id,
            skill_name=skill.skill_name,
            skill_type=skill.skill_type,
            description=skill.description,
            success_rate=skill.success_rate,
            usage_count=skill.usage_count,
            confidence_score=skill.confidence_score,
            last_updated=skill.last_updated.isoformat()
        )
        for skill in skills
    ]


@router.get("/skills/{skill_id}", summary="获取技能详情")
async def get_skill_detail(
    skill_id: str = Path(..., description="技能ID"),
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """获取技能详细信息"""
    if skill_id not in engine.skills:
        raise HTTPException(status_code=404, detail="技能不存在")

    skill = engine.skills[skill_id]

    return {
        "skill_id": skill.skill_id,
        "skill_name": skill.skill_name,
        "skill_type": skill.skill_type,
        "description": skill.description,
        "trigger_conditions": skill.trigger_conditions,
        "action_sequence": skill.action_sequence,
        "success_rate": skill.success_rate,
        "avg_execution_time": skill.avg_execution_time,
        "usage_count": skill.usage_count,
        "learned_from": skill.learned_from,
        "confidence_score": skill.confidence_score,
        "last_updated": skill.last_updated.isoformat()
    }


# ==================== 知识蒸馏集成 ====================

@router.post("/sync-distillation", summary="同步知识蒸馏数据")
async def sync_distillation(
    request: SyncDistillationRequest,
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """
    从知识蒸馏系统同步技能到学习引擎

    将蒸馏生成的技能加载到Hermes引擎中
    """
    stats = engine.sync_with_distillation(request.project_id)

    return {
        "message": f"项目 {request.project_id} 知识蒸馏同步完成",
        "stats": stats
    }


@router.post("/load-distilled-skills", summary="加载蒸馏技能")
async def load_distilled_skills(
    project_id: Optional[int] = Query(None, description="项目ID，None则加载所有"),
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """从知识蒸馏系统加载生成的技能"""
    loaded_count = engine.load_distilled_skills(project_id)

    return {
        "message": f"已加载 {loaded_count} 个蒸馏技能",
        "loaded_count": loaded_count,
        "total_skills": len(engine.skills)
    }


# ==================== 统计分析 ====================

@router.get("/stats", response_model=HermesStatsResponse, summary="获取学习统计")
async def get_stats(
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """获取Hermes学习引擎统计信息"""
    stats = engine.get_stats()
    return HermesStatsResponse(**stats)


@router.get("/health", summary="健康检查")
async def health_check(
    engine: HermesLearningEngine = Depends(get_hermes_engine)
):
    """检查Hermes学习引擎状态"""
    return {
        "status": "healthy",
        "storage_path": str(engine.storage_path),
        "auto_learning_enabled": engine.enable_auto_learning,
        "experiences_loaded": len(engine.experiences),
        "skills_loaded": len(engine.skills),
        "db_connected": engine.db is not None
    }
