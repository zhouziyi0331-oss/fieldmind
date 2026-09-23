"""
技能树和进度追踪API

提供技能树构建、可视化、进度追踪的完整API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.services.skill_tree_builder import SkillTreeBuilder
from app.services.skill_progress_tracker import SkillProgressTracker
from app.models.skill_system import SkillNode, SkillProgress

router = APIRouter(prefix="/api/skills", tags=["Skill Tree & Progress"])


# ==================== Request/Response Models ====================

class BuildTreeRequest(BaseModel):
    """构建技能树请求"""
    package_id: int


class StartLearningRequest(BaseModel):
    """开始学习请求"""
    skill_id: int


class PracticeRequest(BaseModel):
    """练习记录请求"""
    skill_id: int
    success: bool
    time_spent_minutes: int
    xp_earned: Optional[int] = None
    notes: Optional[str] = None


# ==================== 技能树API ====================

@router.post("/tree/build")
async def build_skill_tree(request: BuildTreeRequest, db: Session = Depends(get_db)):
    """
    从SBPACK构建技能树

    自动分析技能关系，构建层级结构，生成可视化数据
    """
    try:
        builder = SkillTreeBuilder(db)
        tree_data = builder.build_from_sbpack(request.package_id)

        return {
            "success": True,
            "tree": tree_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tree/{package_id}")
async def get_skill_tree(package_id: int, db: Session = Depends(get_db)):
    """
    获取已构建的技能树

    返回可视化所需的节点和边数据
    """
    try:
        # 获取该package的所有技能节点
        from app.models.skill_system import SkillNode, SkillRelation
        from app.models.sbpack import SkillItem

        # 查找该package的技能
        skill_items = db.query(SkillItem).filter(
            SkillItem.package_id == package_id
        ).all()

        skill_item_ids = [s.id for s in skill_items]

        # 获取对应的技能节点
        nodes = db.query(SkillNode).filter(
            SkillNode.sbpack_skill_id.in_(skill_item_ids)
        ).all()

        if not nodes:
            return {
                "success": False,
                "message": "Skill tree not built yet. Please build it first.",
                "nodes": [],
                "edges": []
            }

        # 获取关系
        node_ids = [n.id for n in nodes]
        relations = db.query(SkillRelation).filter(
            SkillRelation.source_id.in_(node_ids),
            SkillRelation.target_id.in_(node_ids)
        ).all()

        # 构建可视化数据
        builder = SkillTreeBuilder(db)
        viz_data = builder._generate_visualization_data(nodes, relations)

        return {
            "success": True,
            **viz_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{skill_id}")
async def get_skill_detail(skill_id: str, db: Session = Depends(get_db)):
    """获取技能节点详细信息"""
    node = db.query(SkillNode).filter(SkillNode.skill_id == skill_id).first()

    if not node:
        raise HTTPException(status_code=404, detail="Skill not found")

    return {
        "id": node.skill_id,
        "name": node.name,
        "display_name": node.display_name,
        "description": node.description,
        "category": node.category,
        "difficulty": node.difficulty,
        "estimated_hours": node.estimated_hours,
        "status": node.status,
        "level": node.level,
        "xp": node.xp,
        "prerequisites": node.prerequisites,
        "rationale": node.rationale,
        "interpretation": node.interpretation,
        "application_original": node.application_original,
        "application_future": node.application_future,
        "execution_steps": node.execution_steps,
        "boundaries": node.boundaries,
        "learning_resources": node.learning_resources,
        "practice_exercises": node.practice_exercises
    }


# ==================== 进度追踪API ====================

@router.post("/progress/start")
async def start_learning(
    request: StartLearningRequest,
    user_id: int = 1,  # TODO: 从认证获取
    db: Session = Depends(get_db)
):
    """
    开始学习一个技能

    检查前置条件，创建进度记录
    """
    try:
        # 查找技能节点
        node = db.query(SkillNode).filter(SkillNode.skill_id == request.skill_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Skill not found")

        tracker = SkillProgressTracker(db)
        result = tracker.start_learning(user_id, node.id)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress/practice")
async def record_practice(
    request: PracticeRequest,
    user_id: int = 1,  # TODO: 从认证获取
    db: Session = Depends(get_db)
):
    """
    记录一次技能练习

    更新XP、等级、进度，检查成就和解锁
    """
    try:
        # 查找技能节点
        node = db.query(SkillNode).filter(SkillNode.skill_id == request.skill_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="Skill not found")

        tracker = SkillProgressTracker(db)
        result = tracker.record_practice(user_id, node.id, {
            "success": request.success,
            "time_spent_minutes": request.time_spent_minutes,
            "xp_earned": request.xp_earned,
            "notes": request.notes
        })

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/user/{user_id}")
async def get_user_progress(user_id: int, db: Session = Depends(get_db)):
    """
    获取用户的所有技能进度

    返回学习中、已完成、已精通的技能列表
    """
    progresses = db.query(SkillProgress).filter(
        SkillProgress.user_id == user_id
    ).all()

    tracker = SkillProgressTracker(db)

    return {
        "user_id": user_id,
        "total_skills": len(progresses),
        "learning": [
            tracker._progress_to_dict(p) for p in progresses if p.status == 'learning'
        ],
        "completed": [
            tracker._progress_to_dict(p) for p in progresses if p.status == 'completed'
        ],
        "mastered": [
            tracker._progress_to_dict(p) for p in progresses if p.status == 'mastered'
        ]
    }


@router.get("/progress/skill/{skill_id}/user/{user_id}")
async def get_skill_progress(skill_id: str, user_id: int, db: Session = Depends(get_db)):
    """获取用户在特定技能上的进度"""
    node = db.query(SkillNode).filter(SkillNode.skill_id == skill_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Skill not found")

    tracker = SkillProgressTracker(db)
    progress = tracker.get_user_progress(user_id, node.id)

    if not progress:
        return {
            "found": False,
            "message": "No progress record found"
        }

    return {
        "found": True,
        "progress": tracker._progress_to_dict(progress)
    }


@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: int, db: Session = Depends(get_db)):
    """
    获取推荐学习的技能

    基于用户已完成的技能、兴趣和难度匹配
    """
    try:
        tracker = SkillProgressTracker(db)
        recommendations = tracker.get_recommendations(user_id)

        return {
            "user_id": user_id,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计API ====================

@router.get("/stats/user/{user_id}")
async def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """
    获取用户的技能学习统计

    总XP、等级分布、学习时长等
    """
    progresses = db.query(SkillProgress).filter(
        SkillProgress.user_id == user_id
    ).all()

    total_xp = sum(p.current_xp for p in progresses)
    total_time = sum(p.time_spent_minutes for p in progresses)
    total_practices = sum(p.practice_count for p in progresses)

    # 技能数量统计
    skill_counts = {
        "learning": len([p for p in progresses if p.status == 'learning']),
        "completed": len([p for p in progresses if p.status == 'completed']),
        "mastered": len([p for p in progresses if p.status == 'mastered'])
    }

    # 类别统计
    category_stats = {}
    for progress in progresses:
        node = db.query(SkillNode).filter(SkillNode.id == progress.skill_id).first()
        if node and node.category:
            if node.category not in category_stats:
                category_stats[node.category] = 0
            category_stats[node.category] += 1

    return {
        "user_id": user_id,
        "total_xp": total_xp,
        "total_time_hours": round(total_time / 60, 1),
        "total_practices": total_practices,
        "skill_counts": skill_counts,
        "category_stats": category_stats
    }
