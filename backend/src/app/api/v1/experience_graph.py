"""
经验知识图谱API端点

提供经验知识的组织和查询接口（基于现有自学习系统数据）
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.core.deps import get_db, get_current_user
from app.models.user import User


router = APIRouter()


# ==================== Pydantic 模型 ====================

class ExperienceGraphRequest(BaseModel):
    """构建经验图谱请求"""
    project_id: int = Field(..., description="项目ID")
    include_patterns: bool = Field(True, description="包含模式")
    include_skills: bool = Field(True, description="包含技能")
    include_insights: bool = Field(True, description="包含洞察")
    min_confidence: float = Field(0.5, description="最小置信度", ge=0, le=1)


class ExperienceNodeResponse(BaseModel):
    """经验节点响应"""
    id: str
    type: str
    name: str
    description: str
    confidence: float
    content: Dict[str, Any]
    tags: List[str]
    created_at: str


class ExperienceRelationResponse(BaseModel):
    """经验关系响应"""
    source_id: str
    target_id: str
    relation_type: str
    strength: float


class ExperienceGraphResponse(BaseModel):
    """经验图谱响应"""
    project_id: int
    nodes: List[ExperienceNodeResponse]
    relations: List[ExperienceRelationResponse]
    statistics: Dict[str, int]


class ExperienceQueryRequest(BaseModel):
    """经验查询请求"""
    query_text: str = Field(..., description="查询文本")
    node_types: Optional[List[str]] = Field(None, description="节点类型过滤")
    min_confidence: float = Field(0.5, description="最小置信度", ge=0, le=1)
    limit: int = Field(10, description="返回数量", ge=1, le=100)


# ==================== 经验图谱构建 ====================

@router.post("/build", response_model=ExperienceGraphResponse, summary="构建经验图谱")
async def build_experience_graph(
    request: ExperienceGraphRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    从自学习系统数据构建经验知识图谱

    聚合以下数据源：
    - 识别出的模式（阶段14）
    - 生成的技能（阶段15）
    - 学习洞察（阶段18）
    - 反馈经验（阶段17）
    """
    nodes = []
    relations = []
    stats = {"patterns": 0, "skills": 0, "insights": 0, "experiences": 0}

    # 1. 导入模式节点
    if request.include_patterns:
        from app.models.pattern_library import PatternLibrary

        patterns = db.query(PatternLibrary).filter(
            PatternLibrary.project_id == request.project_id,
            PatternLibrary.confidence_score >= request.min_confidence
        ).limit(50).all()

        for pattern in patterns:
            nodes.append(ExperienceNodeResponse(
                id=f"pattern_{pattern.id}",
                type="模式",
                name=pattern.pattern_name,
                description=pattern.pattern_description,
                confidence=pattern.confidence_score,
                content={
                    "pattern_type": pattern.pattern_type.value,
                    "success_count": pattern.success_count,
                    "usage_count": pattern.usage_count
                },
                tags=[pattern.pattern_type.value],
                created_at=pattern.created_at.isoformat()
            ))
            stats["patterns"] += 1

    # 2. 导入技能节点
    if request.include_skills:
        from app.models.generated_skill import GeneratedSkill

        skills = db.query(GeneratedSkill).filter(
            GeneratedSkill.project_id == request.project_id,
            GeneratedSkill.confidence_score >= request.min_confidence,
            GeneratedSkill.is_active == True
        ).limit(50).all()

        for skill in skills:
            nodes.append(ExperienceNodeResponse(
                id=f"skill_{skill.id}",
                type="技能",
                name=skill.skill_name,
                description=skill.skill_description,
                confidence=skill.confidence_score,
                content={
                    "category": skill.skill_category,
                    "success_rate": skill.success_count / (skill.success_count + skill.failure_count) if (skill.success_count + skill.failure_count) > 0 else 0,
                    "quality_score": skill.quality_score
                },
                tags=[skill.skill_category] if skill.skill_category else [],
                created_at=skill.created_at.isoformat()
            ))
            stats["skills"] += 1

            # 创建技能与源模式的关系
            if skill.source_pattern_id:
                relations.append(ExperienceRelationResponse(
                    source_id=f"skill_{skill.id}",
                    target_id=f"pattern_{skill.source_pattern_id}",
                    relation_type="派生自",
                    strength=0.9
                ))

    # 3. 导入洞察节点
    if request.include_insights:
        from app.models.background_learning import LearningInsight

        insights = db.query(LearningInsight).filter(
            LearningInsight.project_id == request.project_id,
            LearningInsight.confidence_score >= request.min_confidence
        ).limit(50).all()

        for insight in insights:
            nodes.append(ExperienceNodeResponse(
                id=f"insight_{insight.id}",
                type="洞察",
                name=insight.insight_title,
                description=insight.insight_description,
                confidence=insight.confidence_score,
                content={
                    "insight_type": insight.insight_type,
                    "importance": insight.importance_score,
                    "actionability": insight.actionability_score
                },
                tags=[insight.insight_type],
                created_at=insight.discovered_at.isoformat()
            ))
            stats["insights"] += 1

    return ExperienceGraphResponse(
        project_id=request.project_id,
        nodes=nodes,
        relations=relations,
        statistics=stats
    )


@router.post("/query", response_model=List[ExperienceNodeResponse], summary="查询经验知识")
async def query_experience_knowledge(
    project_id: int = Query(..., description="项目ID"),
    request: ExperienceQueryRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询经验知识

    支持基于文本的语义搜索
    """
    results = []

    # 简单的关键词匹配（实际应该使用向量搜索）
    query_lower = request.query_text.lower()

    # 搜索模式
    if not request.node_types or "模式" in request.node_types:
        from app.models.pattern_library import PatternLibrary

        patterns = db.query(PatternLibrary).filter(
            PatternLibrary.project_id == project_id,
            PatternLibrary.confidence_score >= request.min_confidence
        ).all()

        for pattern in patterns:
            if query_lower in pattern.pattern_name.lower() or query_lower in pattern.pattern_description.lower():
                results.append(ExperienceNodeResponse(
                    id=f"pattern_{pattern.id}",
                    type="模式",
                    name=pattern.pattern_name,
                    description=pattern.pattern_description,
                    confidence=pattern.confidence_score,
                    content={"pattern_type": pattern.pattern_type.value},
                    tags=[pattern.pattern_type.value],
                    created_at=pattern.created_at.isoformat()
                ))

    # 搜索技能
    if not request.node_types or "技能" in request.node_types:
        from app.models.generated_skill import GeneratedSkill

        skills = db.query(GeneratedSkill).filter(
            GeneratedSkill.project_id == project_id,
            GeneratedSkill.confidence_score >= request.min_confidence
        ).all()

        for skill in skills:
            if query_lower in skill.skill_name.lower() or query_lower in skill.skill_description.lower():
                results.append(ExperienceNodeResponse(
                    id=f"skill_{skill.id}",
                    type="技能",
                    name=skill.skill_name,
                    description=skill.skill_description,
                    confidence=skill.confidence_score,
                    content={"category": skill.skill_category},
                    tags=[skill.skill_category] if skill.skill_category else [],
                    created_at=skill.created_at.isoformat()
                ))

    # 搜索洞察
    if not request.node_types or "洞察" in request.node_types:
        from app.models.background_learning import LearningInsight

        insights = db.query(LearningInsight).filter(
            LearningInsight.project_id == project_id,
            LearningInsight.confidence_score >= request.min_confidence
        ).all()

        for insight in insights:
            if query_lower in insight.insight_title.lower() or query_lower in insight.insight_description.lower():
                results.append(ExperienceNodeResponse(
                    id=f"insight_{insight.id}",
                    type="洞察",
                    name=insight.insight_title,
                    description=insight.insight_description,
                    confidence=insight.confidence_score,
                    content={"insight_type": insight.insight_type},
                    tags=[insight.insight_type],
                    created_at=insight.discovered_at.isoformat()
                ))

    # 按置信度排序并限制数量
    results.sort(key=lambda x: x.confidence, reverse=True)
    return results[:request.limit]


@router.get("/statistics/{project_id}", summary="获取经验图谱统计")
async def get_experience_graph_statistics(
    project_id: int = Path(..., description="项目ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取经验图谱统计信息
    """
    from app.models.pattern_library import PatternLibrary
    from app.models.generated_skill import GeneratedSkill
    from app.models.background_learning import LearningInsight
    from app.models.feedback_loop import FeedbackLoop

    stats = {
        "total_patterns": db.query(PatternLibrary).filter(
            PatternLibrary.project_id == project_id
        ).count(),
        "total_skills": db.query(GeneratedSkill).filter(
            GeneratedSkill.project_id == project_id
        ).count(),
        "active_skills": db.query(GeneratedSkill).filter(
            GeneratedSkill.project_id == project_id,
            GeneratedSkill.is_active == True
        ).count(),
        "total_insights": db.query(LearningInsight).filter(
            LearningInsight.project_id == project_id
        ).count(),
        "completed_loops": db.query(FeedbackLoop).filter(
            FeedbackLoop.project_id == project_id,
            FeedbackLoop.loop_completed == True
        ).count(),
        "avg_pattern_confidence": db.query(func.avg(PatternLibrary.confidence_score)).filter(
            PatternLibrary.project_id == project_id
        ).scalar() or 0,
        "avg_skill_quality": db.query(func.avg(GeneratedSkill.quality_score)).filter(
            GeneratedSkill.project_id == project_id
        ).scalar() or 0
    }

    return stats
