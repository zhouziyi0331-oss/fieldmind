"""
三层递进报告生成服务

整合所有组件，提供完整的报告生成流程：
1. 提取素材（DataDrivenReportBuilder）
2. 生成大纲（动态）
3. 填充内容（ReportContentEngine）
4. 验证引用（CitationValidator）
5. 导出报告（多种格式）
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .data_driven_report_builder import DataDrivenReportBuilder, ReportMaterial
from .report_content_engine import ReportContentEngine
from .citation_validator import CitationValidator

logger = logging.getLogger(__name__)


class ThreeLayerReportService:
    """
    三层递进报告生成服务

    报告层级：
    - Level 1: 田野调查报告（数据驱动，客观呈现）10,000字+
    - Level 2: 学术专家分析报告（费孝通视角）10,000字+
    - Level 3: 商业市场分析报告（商业决策）10,000字+
    """
    def __init__(self, db: Session, llm_adapter=None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化报告生成服务

        Args:
            db: 数据库会话
            llm_adapter: LLM适配器（用于深度分析）
        """
        self.db = db
        self.builder = DataDrivenReportBuilder(db)
        self.content_engine = ReportContentEngine(llm_adapter)
        self.validator = CitationValidator()

    def generate_report(
        self,
        project_id: int,
        report_level: int = 1,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成指定层级的报告

        Args:
            project_id: 项目ID
            report_level: 报告层级（1/2/3）
            options: 生成选项
                - include_validation: 是否包含引用验证（默认True）
                - min_word_count: 最少字数（默认10000）
                - export_formats: 导出格式列表（默认['markdown']）
                - use_workflow: 是否使用工作流引擎（默认False）

        Returns:
            {
                'report_id': 报告ID,
                'level': 报告层级,
                'title': 报告标题,
                'generated_at': 生成时间,
                'sections': [章节列表],
                'total_word_count': 总字数,
                'total_citations': 总引用数,
                'validation': {验证结果},
                'metadata': {元数据}
            }
        """
        options = options or {}
        use_workflow = options.get('use_workflow', False)

        # 如果启用工作流模式，使用工作流引擎
        if use_workflow:
            return self._generate_report_with_workflow(project_id, report_level, options)

        # 否则使用传统顺序执行模式
        return self._generate_report_sequential(project_id, report_level, options)

    def _generate_report_with_workflow(
        self,
        project_id: int,
        report_level: int,
        options: Dict
    ) -> Dict[str, Any]:
        """
        使用工作流引擎生成报告（支持进度追踪和并行执行）
        """
        from app.services.workflow_templates import run_report_generation_workflow

        logger.info(f"🚀 使用工作流引擎生成Level {report_level}报告（项目={project_id}）...")

        try:
            execution_result = run_report_generation_workflow(
                project_id=project_id,
                report_level=report_level,
                options=options
            )

            logger.info(f"✅ 工作流执行完成: {execution_result['workflow_id']}")
            logger.info(f"   状态: {execution_result['status']}")
            logger.info(f"   任务数: {len(execution_result['tasks'])}")

            # 从工作流结果中提取报告数据
            assemble_result = execution_result['results'].get('assemble_report', {})

            return {
                'report_id': assemble_result.get('report_id'),
                'level': report_level,
                'workflow_id': execution_result['workflow_id'],
                'content_length': assemble_result.get('content_length', 0),
                'section_count': assemble_result.get('section_count', 0),
                'generated_at': execution_result['created_at'],
                'metadata': {
                    'project_id': project_id,
                    'generation_method': 'workflow',
                    'workflow_status': execution_result['status'],
                    'report_type': self._get_report_type_name(report_level)
                }
            }

        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
            raise

    def _generate_report_sequential(
        self,
        project_id: int,
        report_level: int,
        options: Dict
    ) -> Dict[str, Any]:
        """
        传统顺序执行模式生成报告
        """
        logger.info(f"🚀 开始生成Level {report_level}报告（项目={project_id}）...")

        include_validation = options.get('include_validation', True)
        min_word_count = options.get('min_word_count', 10000)

        # 步骤1：提取报告素材
        logger.info("📊 步骤1：提取报告素材...")
        material = self.builder.extract_report_material(project_id)

        # 步骤2：生成动态大纲
        logger.info("📝 步骤2：生成动态大纲...")
        outline = self.builder.generate_dynamic_outline(material, report_level)

        # 步骤3：填充章节内容
        logger.info("✍️  步骤3：填充章节内容...")
        sections = []
        total_word_count = 0

        for section_outline in outline:
            section = self.content_engine.fill_section(
                section_outline,
                material,
                report_level
            )
            sections.append(section)
            total_word_count += section['word_count']

        # 步骤4：验证引用完整性
        validation = None
        if include_validation:
            logger.info("🔍 步骤4：验证引用完整性...")
            validation = self.validator.validate_full_report(sections)

            if not validation['is_valid']:
                logger.warning(f"⚠️  发现{len(validation['sections_with_issues'])}个章节存在引用问题")

        # 步骤5：检查字数要求
        if total_word_count < min_word_count:
            logger.warning(f"⚠️  报告字数({total_word_count})未达到最低要求({min_word_count})")

        # 生成报告标题
        title = self._generate_report_title(material, report_level)

        # 构建完整报告
        report = {
            'report_id': f"report_{project_id}_L{report_level}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'level': report_level,
            'title': title,
            'generated_at': datetime.now().isoformat(),
            'sections': sections,
            'total_word_count': total_word_count,
            'total_citations': sum(len(s['citations']) for s in sections),
            'validation': validation,
            'metadata': {
                'project_id': project_id,
                'material_stats': {
                    'documents': material.total_documents,
                    'chunks': material.total_chunks,
                    'main_keywords': len(material.main_keywords),
                    'entities': sum(len(v) for v in material.core_entities.values()),
                    'timeline_events': len(material.timeline)
                },
                'generation_method': 'data_driven',
                'report_type': self._get_report_type_name(report_level)
            }
        }

        logger.info(f"✅ 报告生成完成：{total_word_count}字，{len(sections)}章节，"
                   f"{report['total_citations']}条引用")

        return report

    def generate_three_layer_reports(
        self,
        project_id: int,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成完整的三层报告

        Args:
            project_id: 项目ID
            options: 生成选项

        Returns:
            {
                'level1_report': Level1报告,
                'level2_report': Level2报告,
                'level3_report': Level3报告,
                'summary': {三层报告汇总}
            }
        """
        logger.info(f"🎯 开始生成三层完整报告（项目={project_id}）...")

        # 生成Level 1报告
        logger.info("\n" + "="*70)
        logger.info("生成Level 1：田野调查报告")
        logger.info("="*70)
        level1_report = self.generate_report(project_id, 1, options)

        # 生成Level 2报告（基于Level 1）
        logger.info("\n" + "="*70)
        logger.info("生成Level 2：学术专家分析报告")
        logger.info("="*70)
        level2_report = self.generate_report(project_id, 2, options)

        # 生成Level 3报告（基于Level 1和2）
        logger.info("\n" + "="*70)
        logger.info("生成Level 3：商业市场分析报告")
        logger.info("="*70)
        level3_report = self.generate_report(project_id, 3, options)

        # 汇总统计
        summary = {
            'total_word_count': (
                level1_report['total_word_count'] +
                level2_report['total_word_count'] +
                level3_report['total_word_count']
            ),
            'total_citations': (
                level1_report['total_citations'] +
                level2_report['total_citations'] +
                level3_report['total_citations']
            ),
            'total_sections': (
                len(level1_report['sections']) +
                len(level2_report['sections']) +
                len(level3_report['sections'])
            ),
            'generated_at': datetime.now().isoformat()
        }

        logger.info(f"\n✅ 三层报告全部生成完成！")
        logger.info(f"   总字数：{summary['total_word_count']:,} 字")
        logger.info(f"   总引用：{summary['total_citations']} 条")
        logger.info(f"   总章节：{summary['total_sections']} 个")

        return {
            'level1_report': level1_report,
            'level2_report': level2_report,
            'level3_report': level3_report,
            'summary': summary
        }

    def export_report(
        self,
        report: Dict[str, Any],
        format_type: str = 'markdown'
    ) -> str:
        """
        导出报告为指定格式

        Args:
            report: 生成的报告
            format_type: 格式类型（markdown/html/json）

        Returns:
            格式化的报告内容
        """
        if format_type == 'markdown':
            return self._export_markdown(report)
        elif format_type == 'html':
            return self._export_html(report)
        elif format_type == 'json':
            import json
            return json.dumps(report, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")

    def _export_markdown(self, report: Dict[str, Any]) -> str:
        """导出为Markdown格式"""
        md = f"# {report['title']}\n\n"

        # 元数据
        md += "---\n\n"
        md += f"**报告层级**：Level {report['level']} - {report['metadata']['report_type']}\n\n"
        md += f"**生成时间**：{report['generated_at'][:19]}\n\n"
        md += f"**项目ID**：{report['metadata']['project_id']}\n\n"
        md += f"**总字数**：{report['total_word_count']:,} 字\n\n"
        md += f"**引用数**：{report['total_citations']} 条\n\n"
        md += "---\n\n"

        # 目录
        md += "## 目录\n\n"
        for idx, section in enumerate(report['sections'], 1):
            md += f"{idx}. [{section['chapter']}](#{self._anchor(section['chapter'])})\n"
        md += "\n---\n\n"

        # 章节内容
        for section in report['sections']:
            md += f"# {section['chapter']}\n\n"
            md += section['content']
            md += "\n\n"

        # 引用完整性报告
        if report.get('validation'):
            md += "\n---\n\n"
            md += "# 附录：引用完整性验证\n\n"
            validation_report = self.validator.generate_validation_report(report['validation'])
            md += validation_report

        # 页脚
        md += "\n---\n\n"
        md += "*本报告由 FieldMind 智能报告系统自动生成*\n\n"
        md += f"*生成方法：{report['metadata']['generation_method']}*\n\n"
        md += f"*数据来源：{report['metadata']['material_stats']['documents']}份文档，"
        md += f"{report['metadata']['material_stats']['chunks']}个文本片段*\n"

        return md

    def _export_html(self, report: Dict[str, Any]) -> str:
        """导出为HTML格式"""
        import markdown

        # 先导出为Markdown
        md_content = self._export_markdown(report)

        # 转换为HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'toc', 'footnotes']
        )

        # 添加CSS样式
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report['title']}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            line-height: 1.8;
            max-width: 1000px;
            margin: 0 auto;
            padding: 40px 20px;
            color: #333;
            background: #f5f5f5;
        }}
        .content {{
            background: white;
            padding: 60px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 15px;
            margin-top: 40px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 20px 0;
            color: #666;
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .footnote {{
            font-size: 0.9em;
            color: #666;
            border-top: 1px solid #ddd;
            margin-top: 40px;
            padding-top: 20px;
        }}
        .metadata {{
            background: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }}
        .validation {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="content">
        {html_content}
    </div>
</body>
</html>"""

        return html

    def _generate_report_title(
        self,
        material: ReportMaterial,
        report_level: int
    ) -> str:
        """生成报告标题"""
        # 基于主关键词生成标题
        if material.main_keywords:
            top_keyword = material.main_keywords[0]['keyword']
        else:
            top_keyword = "项目"

        level_names = {
            1: "田野调查报告",
            2: "学术专家分析报告",
            3: "商业市场分析报告"
        }

        # 如果有时间跨度，加入时间
        if material.temporal_span.get('has_temporal'):
            earliest = material.temporal_span['earliest'][:4]  # 年份
            latest = material.temporal_span['latest'][:4]
            time_range = f"{earliest}-{latest}年" if earliest != latest else f"{earliest}年"
            return f"{time_range}{top_keyword}{level_names[report_level]}"
        else:
            return f"{top_keyword}{level_names[report_level]}"

    def _get_report_type_name(self, report_level: int) -> str:
        """获取报告类型名称"""
        names = {
            1: "田野调查报告",
            2: "学术专家分析报告（费孝通视角）",
            3: "商业市场分析报告"
        }
        return names.get(report_level, f"Level {report_level}报告")

    @staticmethod
    def _anchor(text: str) -> str:
        """生成Markdown锚点"""
        # 简化版：去除特殊字符
        import re
        anchor = re.sub(r'[^\w\s-]', '', text)
        anchor = re.sub(r'\s+', '-', anchor)
        return anchor.lower()
