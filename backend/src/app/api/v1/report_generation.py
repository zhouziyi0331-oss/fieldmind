"""
报告生成API端点

提供三层递进报告生成的REST API
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.services.report_generation.three_layer_report_service import ThreeLayerReportService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Models ====================

class ReportGenerationRequest(BaseModel):
    """报告生成请求"""
    report_level: int = Field(
        default=1,
        ge=1,
        le=3,
        description="报告层级：1=田野调查报告, 2=学术分析报告, 3=商业分析报告"
    )
    min_word_count: int = Field(
        default=10000,
        description="最少字数要求"
    )
    include_validation: bool = Field(
        default=True,
        description="是否包含引用验证"
    )
    export_formats: List[str] = Field(
        default=["markdown"],
        description="导出格式列表（markdown/html/json）"
    )


class ThreeLayerReportRequest(BaseModel):
    """三层完整报告生成请求"""
    min_word_count: int = Field(
        default=10000,
        description="每层报告的最少字数"
    )
    include_validation: bool = Field(
        default=True,
        description="是否包含引用验证"
    )


class ReportExportRequest(BaseModel):
    """报告导出请求"""
    format_type: str = Field(
        default="markdown",
        description="导出格式：markdown/html/json"
    )


# ==================== API Endpoints ====================

@router.post("/projects/{project_id}/reports/generate")
async def generate_project_report(
    project_id: int,
    request: ReportGenerationRequest,
    db: Session = Depends(get_db)
):
    """
    生成指定层级的项目报告

    报告层级说明：
    - Level 1: 田野调查报告（数据驱动，客观呈现，10,000字+）
      - 编年史时间线
      - 关键词社区分析
      - 核心实体展开
      - 所有观点有原文引用

    - Level 2: 学术专家分析报告（费孝通视角，10,000字+）
      - 差序格局分析
      - 礼治秩序探讨
      - 熟人社会结构
      - 现代化冲击研究

    - Level 3: 商业市场分析报告（商业决策导向，10,000字+）
      - SOP六维度评估
      - SWOT分析
      - 战略建议
      - 行动计划
    """
    try:
        logger.info(f"收到报告生成请求：项目={project_id}, Level={request.report_level}")

        # 创建报告服务
        service = ThreeLayerReportService(db)

        # 生成报告
        options = {
            'min_word_count': request.min_word_count,
            'include_validation': request.include_validation,
            'export_formats': request.export_formats
        }

        report = service.generate_report(
            project_id=project_id,
            report_level=request.report_level,
            options=options
        )

        return {
            'success': True,
            'data': report,
            'message': f"Level {request.report_level}报告生成成功"
        }

    except Exception as e:
        logger.error(f"报告生成失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@router.post("/projects/{project_id}/reports/generate-three-layers")
async def generate_three_layer_reports(
    project_id: int,
    request: ThreeLayerReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    生成完整的三层报告（异步任务）

    生成顺序：
    1. Level 1: 田野调查报告（基础层）
    2. Level 2: 学术分析报告（基于Level 1）
    3. Level 3: 商业分析报告（基于Level 1和2）

    注意：三层报告生成需要较长时间（约5-10分钟），建议使用异步任务
    """
    try:
        logger.info(f"收到三层报告生成请求：项目={project_id}")

        # 创建报告服务
        service = ThreeLayerReportService(db)

        # 生成三层报告
        options = {
            'min_word_count': request.min_word_count,
            'include_validation': request.include_validation
        }

        result = service.generate_three_layer_reports(
            project_id=project_id,
            options=options
        )

        return {
            'success': True,
            'data': result,
            'message': '三层报告生成完成'
        }

    except Exception as e:
        logger.error(f"三层报告生成失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"三层报告生成失败: {str(e)}")


@router.post("/reports/export")
async def export_report(
    request: ReportExportRequest,
    report_data: dict
):
    """
    导出报告为指定格式

    支持的格式：
    - markdown: Markdown格式（默认）
    - html: HTML格式（带样式）
    - json: JSON格式（原始数据）
    """
    try:
        from app.services.report_generation.three_layer_report_service import ThreeLayerReportService

        # 创建临时服务实例（不需要db）
        service = ThreeLayerReportService(db=None)

        # 导出报告
        exported_content = service.export_report(
            report=report_data,
            format_type=request.format_type
        )

        return {
            'success': True,
            'data': {
                'format': request.format_type,
                'content': exported_content
            },
            'message': f'报告已导出为{request.format_type}格式'
        }

    except Exception as e:
        logger.error(f"报告导出失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"报告导出失败: {str(e)}")


@router.get("/projects/{project_id}/reports/material-preview")
async def preview_report_material(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    预览报告素材

    在生成报告之前，查看项目的数据是否充足：
    - 文档数量
    - 关键词网络
    - 实体数量
    - 时间线
    - 引用池大小
    """
    try:
        from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder

        builder = DataDrivenReportBuilder(db)
        material = builder.extract_report_material(project_id)

        return {
            'success': True,
            'data': {
                'project_id': project_id,
                'material_stats': {
                    'total_documents': material.total_documents,
                    'total_chunks': material.total_chunks,
                    'total_words': material.total_words,
                    'main_keywords_count': len(material.main_keywords),
                    'keyword_communities_count': len(material.keyword_communities),
                    'entities_by_type': {
                        entity_type: len(entities)
                        for entity_type, entities in material.core_entities.items()
                    },
                    'timeline_events': len(material.timeline),
                    'citation_pool_size': len(material.citation_pool),
                    'temporal_span': material.temporal_span
                },
                'readiness': {
                    'has_enough_documents': material.total_documents >= 5,
                    'has_keywords': len(material.main_keywords) > 0,
                    'has_entities': sum(len(v) for v in material.core_entities.values()) > 0,
                    'has_timeline': len(material.timeline) > 0,
                    'has_citations': len(material.citation_pool) > 0
                }
            },
            'message': '素材预览成功'
        }

    except Exception as e:
        logger.error(f"素材预览失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"素材预览失败: {str(e)}")


@router.get("/projects/{project_id}/reports/outline-preview")
async def preview_report_outline(
    project_id: int,
    report_level: int = 1,
    db: Session = Depends(get_db)
):
    """
    预览报告大纲

    在生成完整报告之前，查看动态生成的报告大纲
    """
    try:
        from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder

        builder = DataDrivenReportBuilder(db)

        # 提取素材
        material = builder.extract_report_material(project_id)

        # 生成大纲
        outline = builder.generate_dynamic_outline(material, report_level)

        return {
            'success': True,
            'data': {
                'project_id': project_id,
                'report_level': report_level,
                'outline': outline,
                'estimated_sections': len(outline),
                'estimated_min_words': sum(s['min_words'] for s in outline)
            },
            'message': '大纲预览成功'
        }

    except Exception as e:
        logger.error(f"大纲预览失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"大纲预览失败: {str(e)}")


@router.get("/reports/info")
async def get_report_system_info():
    """
    获取报告系统信息

    返回：
    - 支持的报告类型
    - 生成方法说明
    - API使用指南
    """
    return {
        'success': True,
        'data': {
            'system_name': 'FieldMind 三层递进报告生成系统',
            'version': '1.0.0',
            'report_levels': [
                {
                    'level': 1,
                    'name': '田野调查报告',
                    'description': '数据驱动，客观呈现田野材料',
                    'features': [
                        '编年史时间线',
                        '关键词社区分析（Louvain算法）',
                        '核心实体网络（人物/地点/事件/组织）',
                        '所有观点有原文引用（反幻觉）'
                    ],
                    'min_word_count': 10000,
                    'typical_sections': 6-8
                },
                {
                    'level': 2,
                    'name': '学术专家分析报告',
                    'description': '费孝通《乡土中国》理论视角深度分析',
                    'features': [
                        '差序格局分析',
                        '礼治秩序探讨',
                        '熟人社会结构研究',
                        '现代化冲击评估',
                        '理论与材料深度对话'
                    ],
                    'min_word_count': 10000,
                    'typical_sections': 6,
                    'requires': 'Level 1报告或田野材料'
                },
                {
                    'level': 3,
                    'name': '商业市场分析报告',
                    'description': '商业决策导向，提供战略建议',
                    'features': [
                        '乡村运营SOP六维度评估',
                        'SWOT综合分析',
                        '战略建议（短期/中期/长期）',
                        '风险预警与应对',
                        '行动计划'
                    ],
                    'min_word_count': 10000,
                    'typical_sections': 6,
                    'requires': 'Level 1和Level 2报告'
                }
            ],
            'generation_method': {
                'approach': 'data_driven',
                'description': '数据驱动+动态大纲+LLM深度分析',
                'anti_hallucination': [
                    '强制原文引用',
                    '引用完整性验证',
                    '数字来源追踪',
                    '引用覆盖率统计'
                ]
            },
            'api_usage': {
                'single_report': 'POST /api/v1/projects/{project_id}/reports/generate',
                'three_layers': 'POST /api/v1/projects/{project_id}/reports/generate-three-layers',
                'preview_material': 'GET /api/v1/projects/{project_id}/reports/material-preview',
                'preview_outline': 'GET /api/v1/projects/{project_id}/reports/outline-preview'
            }
        },
        'message': '报告系统信息'
    }
