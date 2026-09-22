"""
提案生成 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.proposal_generator_service import ProposalGeneratorService
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/proposal", tags=["提案生成"])


class GenerateProposalRequest(BaseModel):
    proposal_type: str = 'government'  # government/academic/business
    include_budget: bool = True
    include_risk: bool = True


@router.post("/projects/{project_id}/generate/")
async def generate_proposal(
    project_id: int,
    request: GenerateProposalRequest,
    db: Session = Depends(get_db)
):
    """
    生成行动提案

    根据项目的分析结果，自动生成可以拿去汇报的提案文档。

    提案类型:
    - government: 政府汇报型（简洁有力）
    - academic: 学术汇报型（详细数据）
    - business: 商业计划型（强调ROI）
    """
    service = ProposalGeneratorService(db)

    try:
        proposal = service.generate_proposal(
            project_id=project_id,
            proposal_type=request.proposal_type,
            include_budget=request.include_budget,
            include_risk=request.include_risk
        )

        return success_response(data=proposal)

    except ValueError as e:
        return error_response(
            code="INVALID_PROJECT",
            message=str(e)
        )
    except Exception as e:
        return error_response(
            code="GENERATE_FAILED",
            message=str(e)
        )


@router.get("/projects/{project_id}/templates/")
async def get_proposal_templates(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取可用的提案模板列表

    根据项目类型推荐合适的提案模板
    """
    templates = [
        {
            'id': 'government',
            'name': '政府汇报型',
            'description': '简洁有力，适合向政府部门汇报',
            'sections': ['项目背景', '核心发现', '机会研判', '行动路径', '预算框架', '风险评估', '下一步计划']
        },
        {
            'id': 'academic',
            'name': '学术汇报型',
            'description': '详细严谨，适合学术研究报告',
            'sections': ['摘要', '研究背景', '调研方法', '核心发现', '深度分析', '建议', '结论']
        },
        {
            'id': 'business',
            'name': '商业计划型',
            'description': '强调ROI，适合投资方汇报',
            'sections': ['Executive Summary', '市场分析', '商业机会', '实施策略', '财务预测', 'ROI分析', '风险应对', '里程碑']
        }
    ]

    return success_response(
        data={
            'project_id': project_id,
            'templates': templates,
            'recommended': 'government'  # 默认推荐政府型
        }
    )


@router.post("/projects/{project_id}/export/")
async def export_proposal(
    project_id: int,
    request: GenerateProposalRequest,
    format: str = 'markdown',
    db: Session = Depends(get_db)
):
    """
    导出提案文档

    支持格式:
    - markdown: Markdown格式（可直接导入Gamma/Beautiful.ai）
    - html: HTML格式
    - pdf: PDF格式（需要额外配置）
    """
    service = ProposalGeneratorService(db)

    try:
        proposal = service.generate_proposal(
            project_id=project_id,
            proposal_type=request.proposal_type,
            include_budget=request.include_budget,
            include_risk=request.include_risk
        )

        if format == 'markdown':
            return success_response(
                data={
                    'format': 'markdown',
                    'content': proposal['markdown'],
                    'filename': f"{proposal['title']}.md"
                }
            )

        elif format == 'html':
            # 生成HTML（带样式）
            html_content = service.generate_html(proposal)
            return success_response(
                data={
                    'format': 'html',
                    'content': html_content,
                    'filename': f"{proposal['title']}.html"
                }
            )

        else:
            return error_response(
                code="INVALID_FORMAT",
                message=f"不支持的格式: {format}"
            )

    except ValueError as e:
        return error_response(
            code="INVALID_PROJECT",
            message=str(e)
        )
    except Exception as e:
        return error_response(
            code="EXPORT_FAILED",
            message=str(e)
        )
