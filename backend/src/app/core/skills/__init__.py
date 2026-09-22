"""
技能系统核心模块

统一的技能管理、执行、推荐系统
"""
from app.core.skills.skill_registry import (
    SkillRegistry,
    Skill,
    SkillType,
    SkillStatus,
    create_skill_registry
)

from app.core.skills.skill_executor import (
    SkillExecutor,
    ExecutionResult,
    SandboxConfig,
    get_skill_executor
)

from app.core.skills.skill_recommender import (
    SkillRecommender,
    SkillRecommendation,
    create_skill_recommender
)

__all__ = [
    # 注册中心
    'SkillRegistry',
    'Skill',
    'SkillType',
    'SkillStatus',
    'create_skill_registry',

    # 执行器
    'SkillExecutor',
    'ExecutionResult',
    'SandboxConfig',
    'get_skill_executor',

    # 推荐器
    'SkillRecommender',
    'SkillRecommendation',
    'create_skill_recommender'
]
