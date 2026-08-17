"""
Skills API路由 - 学术方法论框架管理
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from app.core.database import get_db
from app.models.project import ProjectDocument, Project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/list")
async def list_available_skills() -> Dict[str, Any]:
    """
    获取所有可用的Skills列表

    返回6个学术方法论框架的基本信息
    """
    return {
        "skills": [
            {
                "id": "heritage_dadi",
                "name": "大地遗产方法论",
                "description": "文化遗产识别与价值评估（自然遗产、文化遗产、非物质遗产、物质遗产）",
                "dimensions": 4,
                "author": "FieldMind团队",
                "keywords": ["文化遗产", "价值评估", "传统文化", "非遗"],
                "enabled": True
            },
            {
                "id": "business_feasibility",
                "name": "商业可行性验证",
                "description": "乡村文化遗产商业可行性评估（市场需求、资源可用性、技术可行性、财务可行性、社会接受度、政策支持）",
                "dimensions": 6,
                "author": "FieldMind团队",
                "keywords": ["商业模式", "可行性分析", "市场调研", "财务规划"],
                "enabled": True
            },
            {
                "id": "multi_village_sop",
                "name": "多村联动SOP",
                "description": "多村落田野调查标准流程（准备阶段、进入阶段、田野工作、记录管理、社区互动、深度分析）",
                "dimensions": 6,
                "author": "FieldMind团队",
                "keywords": ["田野调查", "多村联动", "标准流程", "社区参与"],
                "enabled": True
            },
            {
                "id": "literature_market_research",
                "name": "文献市场研究",
                "description": "文献和市场调研方法论（文献研究、市场研究、产业分析、政策研究）",
                "dimensions": 4,
                "author": "FieldMind团队",
                "keywords": ["文献综述", "市场调研", "产业研究", "政策分析"],
                "enabled": True
            },
            {
                "id": "xiangtu_china",
                "name": "乡土中国理论分析",
                "description": "费孝通《乡土中国》8维度社会学框架（差序格局、熟人社会、礼治秩序、长老统治、血缘地缘、土地情结、家族观念、传统与变迁）",
                "dimensions": 8,
                "author": "费孝通",
                "keywords": ["差序格局", "熟人社会", "礼治秩序", "乡土社会"],
                "enabled": True
            },
            {
                "id": "sacred_memory",
                "name": "神圣记忆理论分析",
                "description": "景军《神圣记忆》6维度社会记忆框架（历史记忆、创伤记忆、仪式记忆、谱系记忆、文化象征记忆、身份认同记忆）",
                "dimensions": 6,
                "author": "景军",
                "keywords": ["集体记忆", "社会记忆", "文化传承", "身份认同"],
                "enabled": True
            }
        ],
        "total": 6,
        "categories": [
            {
                "name": "遗产保护",
                "skills": ["heritage_dadi"]
            },
            {
                "name": "商业化路径",
                "skills": ["business_feasibility"]
            },
            {
                "name": "田野调查",
                "skills": ["multi_village_sop"]
            },
            {
                "name": "案头研究",
                "skills": ["literature_market_research"]
            },
            {
                "name": "社会学理论",
                "skills": ["xiangtu_china", "sacred_memory"]
            }
        ]
    }


@router.get("/document/{document_id}/results")
async def get_document_skill_results(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取文档的Skills分析结果

    Args:
        document_id: 文档ID

    Returns:
        {
            "document_id": 123,
            "skills_completed": true,
            "summary": {...},
            "results": {...}
        }
    """
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查是否有Skills分析结果
    skills_analysis = None
    if doc.extra_data and 'skills_analysis' in doc.extra_data:
        skills_analysis = doc.extra_data['skills_analysis']

    skills_completed = doc.extra_data.get('skills_completed', False) if doc.extra_data else False

    return {
        "document_id": document_id,
        "document_name": doc.file_name,
        "skills_completed": skills_completed,
        "skills_analysis": skills_analysis,
        "has_results": skills_analysis is not None
    }


@router.get("/document/{document_id}/skill/{skill_id}")
async def get_document_single_skill_result(
    document_id: int,
    skill_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取文档某个单独Skill的分析结果

    Args:
        document_id: 文档ID
        skill_id: Skill ID (如 'xiangtu_china')

    Returns:
        单个Skill的详细分析结果
    """
    doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 检查Skills分析结果
    if not doc.extra_data or 'skills_analysis' not in doc.extra_data:
        raise HTTPException(status_code=404, detail="该文档尚未完成Skills分析")

    skills_analysis = doc.extra_data['skills_analysis']

    if 'results' not in skills_analysis or skill_id not in skills_analysis['results']:
        raise HTTPException(status_code=404, detail=f"未找到Skill '{skill_id}' 的分析结果")

    skill_result = skills_analysis['results'][skill_id]

    return {
        "document_id": document_id,
        "skill_id": skill_id,
        "result": skill_result
    }


@router.get("/project/{project_id}/settings")
async def get_project_skill_settings(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取项目的Skills配置

    Args:
        project_id: 项目ID

    Returns:
        项目启用的Skills列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    enabled_skills = []
    if project.settings and 'enabled_skills' in project.settings:
        enabled_skills = project.settings['enabled_skills']
    else:
        # 默认全部启用
        enabled_skills = [
            'heritage_dadi',
            'business_feasibility',
            'multi_village_sop',
            'literature_market_research',
            'xiangtu_china',
            'sacred_memory'
        ]

    return {
        "project_id": project_id,
        "project_name": project.name,
        "enabled_skills": enabled_skills,
        "total_enabled": len(enabled_skills)
    }


@router.put("/project/{project_id}/settings")
async def update_project_skill_settings(
    project_id: int,
    settings: Dict[str, List[str]],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    更新项目的Skills配置

    Args:
        project_id: 项目ID
        settings: {"enabled_skills": ["xiangtu_china", "sacred_memory"]}

    Returns:
        更新后的配置
    """
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证skill_id
    valid_skills = [
        'heritage_dadi',
        'business_feasibility',
        'multi_village_sop',
        'literature_market_research',
        'xiangtu_china',
        'sacred_memory'
    ]

    enabled_skills = settings.get('enabled_skills', [])

    # 检查无效的skill_id
    invalid_skills = [s for s in enabled_skills if s not in valid_skills]
    if invalid_skills:
        raise HTTPException(
            status_code=400,
            detail=f"无效的Skill ID: {invalid_skills}"
        )

    # 更新项目设置
    if project.settings is None:
        project.settings = {}

    project.settings['enabled_skills'] = enabled_skills

    # 标记settings字段已修改（SQLAlchemy的JSON字段需要显式标记）
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(project, 'settings')

    db.commit()

    logger.info(f"项目 {project_id} Skills配置已更新: {enabled_skills}")

    return {
        "success": True,
        "project_id": project_id,
        "enabled_skills": enabled_skills,
        "message": f"已启用 {len(enabled_skills)} 个Skills"
    }


@router.get("/project/{project_id}/statistics")
async def get_project_skills_statistics(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取项目的Skills分析统计

    Args:
        project_id: 项目ID

    Returns:
        项目内所有文档的Skills分析汇总统计
    """
    # 获取项目所有已完成Skills分析的文档
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).all()

    total_docs = len(documents)
    analyzed_docs = 0
    skill_stats = {}

    for doc in documents:
        if not doc.extra_data or 'skills_analysis' not in doc.extra_data:
            continue

        analyzed_docs += 1
        skills_analysis = doc.extra_data['skills_analysis']

        if 'results' not in skills_analysis:
            continue

        for skill_id, skill_result in skills_analysis['results'].items():
            if skill_id not in skill_stats:
                skill_stats[skill_id] = {
                    'total_runs': 0,
                    'success_runs': 0,
                    'error_runs': 0
                }

            skill_stats[skill_id]['total_runs'] += 1

            if skill_result.get('success'):
                skill_stats[skill_id]['success_runs'] += 1
            else:
                skill_stats[skill_id]['error_runs'] += 1

    return {
        "project_id": project_id,
        "total_documents": total_docs,
        "analyzed_documents": analyzed_docs,
        "analysis_rate": round(analyzed_docs / total_docs * 100, 1) if total_docs > 0 else 0,
        "skill_statistics": skill_stats
    }
