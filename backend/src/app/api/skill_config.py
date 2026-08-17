"""
Skill配置管理API

动态控制哪些Skill被启用，影响文档处理流程
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundException, ValidationException, DatabaseException
from app.models.project import Project

router = APIRouter(prefix="/skills", tags=["skills"])
logger = logging.getLogger(__name__)


class SkillConfigRequest(BaseModel):
    """Skill配置请求"""
    project_id: int
    enabled_skills: List[str]  # 启用的skill列表，如 ["rural_sop", "fei_xiaotong"]


class SkillConfigResponse(BaseModel):
    """Skill配置响应"""
    project_id: int
    enabled_skills: List[str]
    available_skills: List[dict]


# 可用的Skill定义
AVAILABLE_SKILLS = [
    {
        "id": "rural_sop",
        "name": "乡村运营SOP",
        "description": "六维度乡村运营分析框架",
        "dimensions": [
            "社区基础调研",
            "文化资产盘点",
            "利益相关方分析",
            "业态可行性评估",
            "风险识别",
            "行动路径规划"
        ],
        "default_enabled": True
    },
    {
        "id": "fei_xiaotong",
        "name": "费孝通·乡土中国",
        "description": "社会学经典理论框架",
        "dimensions": [
            "差序格局",
            "礼治秩序",
            "熟人社会",
            "现代化冲击"
        ],
        "default_enabled": True
    },
    {
        "id": "cultural_heritage",
        "name": "文化遗产保护",
        "description": "非物质文化遗产识别与保护",
        "dimensions": [
            "传统技艺",
            "民俗活动",
            "口述历史",
            "传承人群"
        ],
        "default_enabled": False
    },
    {
        "id": "economic_model",
        "name": "经济业态分析",
        "description": "产业结构与经济模式分析",
        "dimensions": [
            "产业类型",
            "收入来源",
            "市场定位",
            "可持续性"
        ],
        "default_enabled": False
    },
    {
        "id": "community_governance",
        "name": "社区治理分析",
        "description": "村庄治理结构、权力关系与决策机制",
        "dimensions": [
            "权力结构",
            "决策机制",
            "矛盾调解",
            "资源分配"
        ],
        "default_enabled": False
    },
    {
        "id": "livelihood_ecology",
        "name": "生计生态分析",
        "description": "生计方式、收入来源与生态环境关系",
        "dimensions": [
            "收入来源",
            "农业实践",
            "生态影响",
            "资源依赖"
        ],
        "default_enabled": False
    }
]


@router.get("/available")
def get_available_skills() -> Dict[str, Any]:
    """
    获取所有可用的Skill列表
    """
    return {
        "skills": AVAILABLE_SKILLS,
        "total": len(AVAILABLE_SKILLS)
    }


@router.get("/config/{project_id}", response_model=SkillConfigResponse)
def get_skill_config(
    project_id: int,
    db: Session = Depends(get_db)
) -> SkillConfigResponse:
    """
    获取项目的Skill配置
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise ResourceNotFoundException("Project", project_id)

        # 从项目的extra_data中读取Skill配置
        enabled_skills = []

        if project.settings and project.settings.get('enabled_skills'):
            enabled_skills = project.settings['enabled_skills']
        else:
            # 默认启用default_enabled=True的Skill
            enabled_skills = [
                skill['id'] for skill in AVAILABLE_SKILLS
                if skill.get('default_enabled', False)
            ]

        return SkillConfigResponse(
            project_id=project_id,
            enabled_skills=enabled_skills,
            available_skills=AVAILABLE_SKILLS
        )

    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get skill config: {e}")
        raise DatabaseException(message=str(e), operation="skill_config", cause=e)


@router.post("/config")
def update_skill_config(
    request: SkillConfigRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    更新项目的Skill配置

    启用/禁用Skill后，需要重新处理文档才能生效
    """
    try:
        project = db.query(Project).filter(Project.id == request.project_id).first()

        if not project:
            raise ResourceNotFoundException("Project", project_id)

        # 验证Skill ID
        valid_skill_ids = [skill['id'] for skill in AVAILABLE_SKILLS]
        invalid_skills = [s for s in request.enabled_skills if s not in valid_skill_ids]

        if invalid_skills:
            raise ValidationException(
                message=f"无效的技能ID: {', '.join(invalid_skills)}",
                field="enabled_skills"
            )

        # 更新项目配置
        if not project.settings:
            project.settings = {}

        project.settings['enabled_skills'] = request.enabled_skills

        # 标记需要更新（使用flag标记）
        db.add(project)
        db.commit()

        logger.info(f"Updated skill config for project {request.project_id}: {request.enabled_skills}")

        return {
            "success": True,
            "project_id": request.project_id,
            "enabled_skills": request.enabled_skills,
            "message": "Skill配置已更新。重新处理文档后生效。"
        }

    except (ResourceNotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to update skill config: {e}")
        raise DatabaseException(message=str(e), operation="skill_config", cause=e)


@router.post("/toggle/{project_id}/{skill_id}")
def toggle_skill(
    project_id: int,
    skill_id: str,
    enabled: bool,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    快速开关单个Skill
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise ResourceNotFoundException("Project", project_id)

        # 验证Skill ID
        valid_skill_ids = [skill['id'] for skill in AVAILABLE_SKILLS]
        if skill_id not in valid_skill_ids:
            raise ValidationException(message=f"无效的技能ID: {skill_id}", field="skill_id")

        # 获取当前配置
        if not project.settings:
            project.settings = {}

        enabled_skills = project.settings.get('enabled_skills', [
            s['id'] for s in AVAILABLE_SKILLS if s.get('default_enabled', False)
        ])

        # 切换状态
        if enabled:
            if skill_id not in enabled_skills:
                enabled_skills.append(skill_id)
        else:
            if skill_id in enabled_skills:
                enabled_skills.remove(skill_id)

        project.settings['enabled_skills'] = enabled_skills

        db.add(project)
        db.commit()

        logger.info(f"Toggled skill {skill_id} to {enabled} for project {project_id}")

        return {
            "success": True,
            "project_id": project_id,
            "skill_id": skill_id,
            "enabled": enabled,
            "current_skills": enabled_skills
        }

    except (ResourceNotFoundException, ValidationException):
        raise
    except Exception as e:
        logger.error(f"Failed to toggle skill: {e}")
        raise DatabaseException(message=str(e), operation="skill_config", cause=e)
