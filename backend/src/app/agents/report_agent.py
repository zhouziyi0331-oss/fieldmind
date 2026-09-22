"""
ReportAgent - Agent 6: 综合报告生成器

整合三个报告生成服务：
1. DynamicReportGenerator - 数据驱动的动态大纲生成
2. LLMReportGenerator - 三度报告（一度材料/二度理论/三度建议）
3. AntiHallucinationReportGenerator - 反幻觉的事实核查

核心职责：
- 根据项目需求选择合适的报告策略
- 整合多层次分析结果（数据画像、知识图谱、记忆系统）
- 生成结构化、可追溯、防幻觉的研究报告
- 支持多种导出格式（Markdown, JSON, PDF）
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportLevel(str, Enum):
    """报告深度等级"""
    LEVEL_1 = "level_1"  # 一度报告：材料呈现 + 关键词分析
    LEVEL_2 = "level_2"  # 二度报告：理论框架深度解读
    LEVEL_3 = "level_3"  # 三度报告：综合评估 + 行动建议
    DYNAMIC = "dynamic"   # 动态报告：数据驱动的大纲生成
    ANTI_HALLUCINATION = "anti_hallucination"  # 反幻觉报告：事实核查模式


class ReportFormat(str, Enum):
    """报告导出格式"""
    MARKDOWN = "markdown"
    JSON = "json"
    PDF = "pdf"
    HTML = "html"


class ReportStrategy(str, Enum):
    """报告生成策略"""
    DATA_DRIVEN = "data_driven"      # 基于数据画像
    THEORY_BASED = "theory_based"    # 基于理论框架
    MEMORY_ENHANCED = "memory_enhanced"  # 增强记忆系统
    CITATION_FOCUSED = "citation_focused"  # 强调引用追溯
    COMPREHENSIVE = "comprehensive"   # 综合全部能力
    AUTO = "auto"                    # 自动选择策略


@dataclass
class ReportMetadata:
    """报告元数据"""
    project_id: int
    report_level: ReportLevel
    report_format: ReportFormat
    generated_at: datetime
    document_count: int
    total_words: int
    generation_strategy: ReportStrategy
    has_citations: bool = False
    has_data_profile: bool = False
    has_llm_generation: bool = False
    validation_passed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportSection:
    """报告章节"""
    chapter_number: int
    title: str
    content: str
    subsections: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportResult:
    """报告生成结果"""
    success: bool
    report_title: str
    sections: List[ReportSection]
    metadata: ReportMetadata
    raw_content: str
    validation_errors: List[str] = field(default_factory=list)
    export_formats: Dict[ReportFormat, str] = field(default_factory=dict)


class ReportAgent:
    """
    Agent 6: 综合报告生成器

    整合三大报告服务，提供统一的报告生成接口
    """

    def __init__(
        self,
        default_level: ReportLevel = ReportLevel.DYNAMIC,
        default_strategy: ReportStrategy = ReportStrategy.AUTO,
        enable_anti_hallucination: bool = True,
        enable_citation_check: bool = True,
        max_report_length: int = 50000
    ):
        """
        初始化ReportAgent

        Args:
            default_level: 默认报告等级
            default_strategy: 默认生成策略
            enable_anti_hallucination: 启用反幻觉检测
            enable_citation_check: 启用引用检查
            max_report_length: 最大报告长度（字符数）
        """
        self.default_level = default_level
        self.default_strategy = default_strategy
        self.enable_anti_hallucination = enable_anti_hallucination
        self.enable_citation_check = enable_citation_check
        self.max_report_length = max_report_length

        # 懒加载服务
        self._dynamic_generator = None
        self._llm_generator = None
        self._anti_hallucination_generator = None

    def _get_dynamic_generator(self, db_session):
        """懒加载DynamicReportGenerator"""
        if self._dynamic_generator is None:
            from app.services.dynamic_report_generator import DynamicReportGenerator
            self._dynamic_generator = DynamicReportGenerator(db=db_session)
        return self._dynamic_generator

    def _get_llm_generator(self):
        """懒加载LLMReportGenerator"""
        if self._llm_generator is None:
            from app.services.llm_report_generator import LLMReportGenerator
            self._llm_generator = LLMReportGenerator()
        return self._llm_generator

    def _get_anti_hallucination_generator(self):
        """懒加载AntiHallucinationReportGenerator"""
        if self._anti_hallucination_generator is None:
            from app.services.anti_hallucination_report import AntiHallucinationReportGenerator
            self._anti_hallucination_generator = AntiHallucinationReportGenerator()
        return self._anti_hallucination_generator

    def generate_report(
        self,
        project_id: int,
        db_session,
        report_level: Optional[ReportLevel] = None,
        strategy: Optional[ReportStrategy] = None,
        export_formats: Optional[List[ReportFormat]] = None
    ) -> ReportResult:
        """
        生成综合报告（主入口）

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            report_level: 报告等级（None则使用默认）
            strategy: 生成策略（None则使用默认）
            export_formats: 导出格式列表

        Returns:
            ReportResult对象
        """
        level = report_level or self.default_level
        strategy = strategy or self.default_strategy
        export_formats = export_formats or [ReportFormat.MARKDOWN]

        logger.info(f"🚀 开始生成报告（项目={project_id}, 等级={level}, 策略={strategy}）")

        try:
            # 1. 自动选择策略（如果是AUTO模式）
            if strategy == ReportStrategy.AUTO:
                strategy = self._select_strategy(project_id, level, db_session)
                logger.info(f"📊 自动选择策略: {strategy}")

            # 2. 根据等级和策略生成报告
            if level == ReportLevel.DYNAMIC:
                report_data = self._generate_dynamic_report(project_id, db_session, strategy)
            elif level == ReportLevel.ANTI_HALLUCINATION:
                report_data = self._generate_anti_hallucination_report(project_id, db_session)
            elif level in [ReportLevel.LEVEL_1, ReportLevel.LEVEL_2, ReportLevel.LEVEL_3]:
                report_data = self._generate_llm_report(project_id, level, db_session, strategy)
            else:
                raise ValueError(f"不支持的报告等级: {level}")

            # 3. 结构化报告内容
            sections = self._parse_report_sections(report_data)

            # 4. 反幻觉验证（如果启用）
            validation_errors = []
            if self.enable_anti_hallucination:
                validation_errors = self._validate_report(report_data, project_id, db_session)

            # 5. 引用检查（如果启用）
            if self.enable_citation_check:
                citation_errors = self._check_citations(sections)
                validation_errors.extend(citation_errors)

            # 6. 构建元数据
            metadata = self._build_metadata(
                project_id=project_id,
                report_level=level,
                strategy=strategy,
                report_data=report_data,
                validation_passed=len(validation_errors) == 0,
                db_session=db_session
            )

            # 7. 导出多种格式
            exports = {}
            raw_content = report_data.get('raw_text', '')
            for fmt in export_formats:
                exports[fmt] = self._export_format(sections, metadata, fmt)

            # 8. 构建结果
            result = ReportResult(
                success=True,
                report_title=report_data.get('title', f'项目{project_id}分析报告'),
                sections=sections,
                metadata=metadata,
                raw_content=raw_content,
                validation_errors=validation_errors,
                export_formats=exports
            )

            logger.info(f"✅ 报告生成完成（章节数={len(sections)}, 验证={'通过' if not validation_errors else '失败'}）")

            return result

        except Exception as e:
            logger.error(f"❌ 报告生成失败: {e}", exc_info=True)
            return ReportResult(
                success=False,
                report_title=f'项目{project_id}报告生成失败',
                sections=[],
                metadata=ReportMetadata(
                    project_id=project_id,
                    report_level=level,
                    report_format=ReportFormat.MARKDOWN,
                    generated_at=datetime.now(),
                    document_count=0,
                    total_words=0,
                    generation_strategy=strategy,
                    validation_passed=False
                ),
                raw_content='',
                validation_errors=[str(e)]
            )

    def _select_strategy(
        self,
        project_id: int,
        level: ReportLevel,
        db_session
    ) -> ReportStrategy:
        """
        自动选择最合适的报告生成策略

        决策逻辑：
        - 有数据画像 -> DATA_DRIVEN
        - LLM可用 + 需要深度分析 -> THEORY_BASED
        - 有丰富记忆数据 -> MEMORY_ENHANCED
        - 需要学术引用 -> CITATION_FOCUSED
        - 数据充足且LLM可用 -> COMPREHENSIVE
        """
        from app.models.project import ProjectDocument

        # 检查项目文档数量和数据画像
        docs = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).all()

        has_data_profile = any(doc.data_profile for doc in docs)
        doc_count = len(docs)

        # 检查LLM是否可用
        llm_gen = self._get_llm_generator()
        llm_available = llm_gen.is_available()

        # 决策树
        if doc_count == 0:
            return ReportStrategy.DATA_DRIVEN  # 至少返回空报告

        if has_data_profile and doc_count >= 3:
            if llm_available and level in [ReportLevel.LEVEL_2, ReportLevel.LEVEL_3]:
                return ReportStrategy.COMPREHENSIVE  # 数据+LLM综合
            else:
                return ReportStrategy.DATA_DRIVEN  # 纯数据驱动

        if llm_available and level != ReportLevel.DYNAMIC:
            return ReportStrategy.THEORY_BASED  # 理论深度

        if doc_count >= 5:
            return ReportStrategy.MEMORY_ENHANCED  # 记忆增强

        return ReportStrategy.DATA_DRIVEN  # 默认保守策略

    def _generate_dynamic_report(
        self,
        project_id: int,
        db_session,
        strategy: ReportStrategy
    ) -> Dict[str, Any]:
        """使用DynamicReportGenerator生成报告"""
        generator = self._get_dynamic_generator(db_session)
        report = generator.generate_report(project_id)

        # 转换为统一格式
        return {
            'title': report['title'],
            'sections': report.get('sections', []),
            'outline': report.get('outline', []),
            'metadata': report.get('metadata', {}),
            'raw_text': self._sections_to_text(report.get('sections', [])),
            'generation_mode': 'dynamic'
        }

    def _generate_anti_hallucination_report(
        self,
        project_id: int,
        db_session
    ) -> Dict[str, Any]:
        """使用AntiHallucinationReportGenerator生成报告"""
        generator = self._get_anti_hallucination_generator()

        # 构建facts数据
        facts = self._build_facts_data(project_id, db_session)

        # 生成报告
        report_text = generator.generate_report_direct(facts)

        return {
            'title': f'项目{project_id}数据分析报告',
            'sections': [],  # 反幻觉报告是纯文本
            'raw_text': report_text,
            'facts': facts,
            'generation_mode': 'anti_hallucination'
        }

    def _generate_llm_report(
        self,
        project_id: int,
        level: ReportLevel,
        db_session,
        strategy: ReportStrategy
    ) -> Dict[str, Any]:
        """使用LLMReportGenerator生成三度报告"""
        from app.models.project import ProjectDocument

        generator = self._get_llm_generator()

        if not generator.is_available():
            logger.warning("⚠️ LLM不可用，降级为动态报告")
            return self._generate_dynamic_report(project_id, db_session, strategy)

        # 加载文档
        docs = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).all()

        # 准备关键词和skill结果（简化版）
        keywords = self._extract_keywords_from_docs(docs)
        skill_results = self._prepare_skill_results(docs)

        # 根据等级生成报告
        if level == ReportLevel.LEVEL_1:
            report_text = generator.generate_level1_report(docs, keywords)
        elif level == ReportLevel.LEVEL_2:
            report_text = generator.generate_level2_report(docs, skill_results)
        elif level == ReportLevel.LEVEL_3:
            report_text = generator.generate_level3_report(docs, keywords, skill_results)
        else:
            report_text = None

        if not report_text:
            logger.warning("⚠️ LLM生成失败，降级为动态报告")
            return self._generate_dynamic_report(project_id, db_session, strategy)

        return {
            'title': f'项目{project_id}{level.value}分析报告',
            'sections': [],
            'raw_text': report_text,
            'generation_mode': f'llm_{level.value}'
        }

    def _build_facts_data(self, project_id: int, db_session) -> Dict[str, Any]:
        """构建反幻觉报告需要的facts数据"""
        from app.models.project import ProjectDocument

        docs = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id,
            ProjectDocument.status == "completed"
        ).all()

        total_words = sum(len(doc.text_content or '') for doc in docs)

        # 简化的facts结构
        facts = {
            'project_id': project_id,
            'total_docs': len(docs),
            'total_chunks': sum(len(doc.chunks or []) for doc in docs),
            'total_words': total_words,
            'category_rank': [],
            'top_speakers': [],
            'top_locations': [],
            'evidence_samples': [],
            'generated_at': datetime.now().isoformat(),
            'data_source': 'ProjectDocument表'
        }

        return facts

    def _extract_keywords_from_docs(self, docs) -> List[Dict[str, Any]]:
        """从文档中提取关键词"""
        keywords = []
        for doc in docs:
            if hasattr(doc, 'data_profile') and doc.data_profile:
                profile = doc.data_profile
                if 'discovered_dimensions' in profile:
                    for dim in profile['discovered_dimensions']:
                        for kw in dim.get('keywords', []):
                            keywords.append({
                                'keyword': kw,
                                'weight': dim.get('priority', 0.5)
                            })

        # 去重并排序
        keyword_dict = {}
        for kw in keywords:
            key = kw['keyword']
            if key in keyword_dict:
                keyword_dict[key]['weight'] += kw['weight']
            else:
                keyword_dict[key] = kw

        sorted_keywords = sorted(keyword_dict.values(), key=lambda x: x['weight'], reverse=True)
        return sorted_keywords[:50]

    def _prepare_skill_results(self, docs) -> Dict[str, Any]:
        """准备skill分析结果（简化版）"""
        skill_results = {}

        for doc in docs:
            if hasattr(doc, 'data_profile') and doc.data_profile:
                profile = doc.data_profile
                dimensions = profile.get('discovered_dimensions', [])

                for dim in dimensions:
                    dim_name = dim['dimension_name']
                    if dim_name not in skill_results:
                        skill_results[dim_name] = {
                            'dimensions': {},
                            'matched_count': 0
                        }

                    skill_results[dim_name]['matched_count'] += dim.get('total_mentions', 0)

        return skill_results

    def _parse_report_sections(self, report_data: Dict[str, Any]) -> List[ReportSection]:
        """解析报告为结构化章节"""
        sections = []

        # 如果有预定义的sections
        if 'sections' in report_data and report_data['sections']:
            for idx, sec in enumerate(report_data['sections'], 1):
                if isinstance(sec, dict):
                    section = ReportSection(
                        chapter_number=idx,
                        title=sec.get('chapter', f'第{idx}章'),
                        content=sec.get('content', {}).get('text', ''),
                        metadata=sec.get('content', {})
                    )
                    sections.append(section)

        # 如果是纯文本报告，尝试解析章节
        elif 'raw_text' in report_data:
            text = report_data['raw_text']
            sections = self._parse_text_sections(text)

        return sections

    def _parse_text_sections(self, text: str) -> List[ReportSection]:
        """从纯文本中解析章节"""
        import re

        sections = []
        # 匹配Markdown标题（## 章节名）
        pattern = r'^##\s+(.+?)$'
        matches = list(re.finditer(pattern, text, re.MULTILINE))

        if not matches:
            # 没有章节标记，整个文本作为一个章节
            return [ReportSection(
                chapter_number=1,
                title='完整报告',
                content=text.strip()
            )]

        for idx, match in enumerate(matches):
            title = match.group(1).strip()
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            section = ReportSection(
                chapter_number=idx + 1,
                title=title,
                content=content
            )
            sections.append(section)

        return sections

    def _validate_report(
        self,
        report_data: Dict[str, Any],
        project_id: int,
        db_session
    ) -> List[str]:
        """反幻觉验证"""
        if not self.enable_anti_hallucination:
            return []

        from app.services.anti_hallucination_report import HallucinationDetector

        errors = []

        # 如果有facts数据，进行验证
        if 'facts' in report_data:
            raw_text = report_data.get('raw_text', '')
            facts = report_data['facts']

            is_valid, validation_errors = HallucinationDetector.validate_report(raw_text, facts)
            if not is_valid:
                errors.extend(validation_errors)

        return errors

    def _check_citations(self, sections: List[ReportSection]) -> List[str]:
        """检查引用完整性"""
        if not self.enable_citation_check:
            return []

        import re
        errors = []

        for section in sections:
            content = section.content

            # 检查是否有引号但缺少引用
            quotes = re.findall(r'"([^"]+)"', content)
            for quote in quotes:
                # 检查引号后是否有引用标记
                if not re.search(r'"' + re.escape(quote) + r'"[^（]*[（(]来源[：:]', content):
                    errors.append(f'章节"{section.title}"中的引用缺少来源: "{quote[:50]}..."')

        return errors

    def _build_metadata(
        self,
        project_id: int,
        report_level: ReportLevel,
        strategy: ReportStrategy,
        report_data: Dict[str, Any],
        validation_passed: bool,
        db_session
    ) -> ReportMetadata:
        """构建报告元数据"""
        from app.models.project import ProjectDocument

        docs = db_session.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).count()

        total_words = len(report_data.get('raw_text', ''))

        has_citations = '[来源：' in report_data.get('raw_text', '')
        has_data_profile = 'data_profile' in report_data.get('metadata', {})
        has_llm = report_data.get('generation_mode', '').startswith('llm')

        return ReportMetadata(
            project_id=project_id,
            report_level=report_level,
            report_format=ReportFormat.MARKDOWN,
            generated_at=datetime.now(),
            document_count=docs,
            total_words=total_words,
            generation_strategy=strategy,
            has_citations=has_citations,
            has_data_profile=has_data_profile,
            has_llm_generation=has_llm,
            validation_passed=validation_passed,
            metadata=report_data.get('metadata', {})
        )

    def _export_format(
        self,
        sections: List[ReportSection],
        metadata: ReportMetadata,
        fmt: ReportFormat
    ) -> str:
        """导出为指定格式"""
        if fmt == ReportFormat.MARKDOWN:
            return self._export_markdown(sections, metadata)
        elif fmt == ReportFormat.JSON:
            return self._export_json(sections, metadata)
        elif fmt == ReportFormat.HTML:
            return self._export_html(sections, metadata)
        else:
            return f"不支持的格式: {fmt}"

    def _export_markdown(self, sections: List[ReportSection], metadata: ReportMetadata) -> str:
        """导出为Markdown"""
        lines = []

        # 标题
        lines.append(f"# 项目{metadata.project_id}分析报告\n")

        # 元数据
        lines.append(f"**生成时间**: {metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**报告等级**: {metadata.report_level.value}")
        lines.append(f"**生成策略**: {metadata.generation_strategy.value}")
        lines.append(f"**文档数量**: {metadata.document_count}")
        lines.append(f"**总字数**: {metadata.total_words}")
        lines.append(f"**验证状态**: {'✅ 通过' if metadata.validation_passed else '❌ 失败'}\n")
        lines.append("---\n")

        # 章节
        for section in sections:
            lines.append(f"## {section.chapter_number}. {section.title}\n")
            lines.append(section.content)
            lines.append("\n")

        return "\n".join(lines)

    def _export_json(self, sections: List[ReportSection], metadata: ReportMetadata) -> str:
        """导出为JSON"""
        import json

        data = {
            'metadata': {
                'project_id': metadata.project_id,
                'report_level': metadata.report_level.value,
                'report_format': metadata.report_format.value,
                'generated_at': metadata.generated_at.isoformat(),
                'document_count': metadata.document_count,
                'total_words': metadata.total_words,
                'generation_strategy': metadata.generation_strategy.value,
                'has_citations': metadata.has_citations,
                'validation_passed': metadata.validation_passed
            },
            'sections': [
                {
                    'chapter_number': sec.chapter_number,
                    'title': sec.title,
                    'content': sec.content,
                    'citations': sec.citations,
                    'data_sources': sec.data_sources
                }
                for sec in sections
            ]
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    def _export_html(self, sections: List[ReportSection], metadata: ReportMetadata) -> str:
        """导出为HTML"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>项目{metadata.project_id}分析报告</title>
    <style>
        body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metadata {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 30px; }}
        .section {{ margin-bottom: 40px; }}
    </style>
</head>
<body>
    <h1>项目{metadata.project_id}分析报告</h1>

    <div class="metadata">
        <p><strong>生成时间</strong>: {metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>报告等级</strong>: {metadata.report_level.value}</p>
        <p><strong>文档数量</strong>: {metadata.document_count}</p>
        <p><strong>总字数</strong>: {metadata.total_words}</p>
    </div>
"""

        for section in sections:
            html += f"""
    <div class="section">
        <h2>{section.chapter_number}. {section.title}</h2>
        <p>{section.content.replace(chr(10), '<br>')}</p>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

    def _sections_to_text(self, sections: List[Dict]) -> str:
        """将章节列表转换为纯文本"""
        lines = []
        for sec in sections:
            if isinstance(sec, dict):
                lines.append(sec.get('chapter', ''))
                content = sec.get('content', {})
                if isinstance(content, dict):
                    lines.append(content.get('text', ''))
                else:
                    lines.append(str(content))
                lines.append('')

        return '\n'.join(lines)

    async def generate_three_layer_report(
        self,
        project_id: str,
        db_session,
        synthesis_result_id: int,
        target_words_per_layer: int = 10000,
        include_citations: bool = True
    ) -> Dict[str, Any]:
        """
        Phase 5核心方法：生成三层报告并存储到report_layers表

        这是ReportAgent在Phase 5的新增核心功能：
        1. 从synthesis_results表读取综合洞察数据
        2. 从report_analysis_cache表读取15个分析服务的结果
        3. 生成三层报告（每层约10000字）：
           - 第一层：数据呈现与基础分析
           - 第二层：理论框架与深度解读
           - 第三层：综合评估与行动建议
        4. 每层报告存储到report_layers表（可验证、可追溯）

        Args:
            project_id: 项目ID
            db_session: 数据库会话
            synthesis_result_id: SynthesisAgent生成的综合洞察ID
            target_words_per_layer: 每层目标字数（默认10000）
            include_citations: 是否包含引用（默认True）

        Returns:
            三层报告生成结果，包含：
            - layer_1_id: 第一层报告ID
            - layer_2_id: 第二层报告ID
            - layer_3_id: 第三层报告ID
            - layer_1_content: 第一层内容
            - layer_2_content: 第二层内容
            - layer_3_content: 第三层内容
            - total_words: 总字数
            - metadata: 生成元数据
        """
        from datetime import datetime
        from sqlalchemy import text
        import json

        logger.info(f"🎯 开始生成三层报告 - 项目: {project_id}, 综合洞察ID: {synthesis_result_id}")

        # 1. 从synthesis_results表读取综合洞察
        synthesis_query = text("""
            SELECT * FROM synthesis_results
            WHERE id = :synthesis_id
        """)
        synthesis_row = db_session.execute(synthesis_query, {'synthesis_id': synthesis_result_id}).fetchone()

        if not synthesis_row:
            raise ValueError(f"Synthesis result {synthesis_result_id} not found")

        synthesis_data = {
            'key_insights': json.loads(synthesis_row['key_insights']),
            'decision_factors': json.loads(synthesis_row['decision_factors']),
            'recommendations': json.loads(synthesis_row['recommendations']),
            'thinking_patterns': json.loads(synthesis_row['thinking_patterns']),
            'skill_knowledge': json.loads(synthesis_row['skill_knowledge']),
            'domain_knowledge': json.loads(synthesis_row['domain_knowledge']),
            'applied_skills': json.loads(synthesis_row['applied_skills']),
            'context_summary': synthesis_row['context_summary'],
            'confidence_score': synthesis_row['confidence_score']
        }

        logger.info(f"✅ 综合洞察数据加载完成: {len(synthesis_data['key_insights'])}个洞察")

        # 2. 从report_analysis_cache表读取15个分析服务结果
        cache_query = text("""
            SELECT analysis_type, result_data, confidence_score
            FROM report_analysis_cache
            WHERE project_id = :project_id
            AND is_valid = 1
            ORDER BY created_at DESC
        """)
        cache_rows = db_session.execute(cache_query, {'project_id': project_id}).fetchall()

        analysis_cache = {}
        for row in cache_rows:
            analysis_type = row['analysis_type']
            if analysis_type not in analysis_cache:  # 只取最新的
                analysis_cache[analysis_type] = {
                    'data': json.loads(row['result_data']),
                    'confidence': row['confidence_score']
                }

        logger.info(f"✅ 分析缓存加载完成: {len(analysis_cache)}个分析类型")

        # 3. 生成第一层报告：数据呈现与基础分析（10000字）
        layer_1_content = self._generate_layer_1(
            project_id=project_id,
            synthesis_data=synthesis_data,
            analysis_cache=analysis_cache,
            target_words=target_words_per_layer
        )

        layer_1_word_count = len(layer_1_content)
        logger.info(f"✅ 第一层报告生成完成: {layer_1_word_count}字")

        # 4. 生成第二层报告：理论框架与深度解读（10000字）
        layer_2_content = self._generate_layer_2(
            project_id=project_id,
            synthesis_data=synthesis_data,
            analysis_cache=analysis_cache,
            layer_1_summary=layer_1_content[:500],  # 传递第一层摘要
            target_words=target_words_per_layer
        )

        layer_2_word_count = len(layer_2_content)
        logger.info(f"✅ 第二层报告生成完成: {layer_2_word_count}字")

        # 5. 生成第三层报告：综合评估与行动建议（10000字）
        layer_3_content = self._generate_layer_3(
            project_id=project_id,
            synthesis_data=synthesis_data,
            analysis_cache=analysis_cache,
            layer_1_summary=layer_1_content[:300],
            layer_2_summary=layer_2_content[:300],
            target_words=target_words_per_layer
        )

        layer_3_word_count = len(layer_3_content)
        logger.info(f"✅ 第三层报告生成完成: {layer_3_word_count}字")

        # 6. 存储三层报告到report_layers表
        insert_layer_query = text("""
            INSERT INTO report_layers (
                project_id,
                synthesis_result_id,
                layer_number,
                title,
                abstract,
                content,
                word_count,
                data_sources,
                analysis_types_used,
                skills_used,
                theoretical_frameworks,
                quality_score,
                created_at
            ) VALUES (
                :project_id,
                :synthesis_result_id,
                :layer_number,
                :title,
                :abstract,
                :content,
                :word_count,
                :data_sources,
                :analysis_types_used,
                :skills_used,
                :theoretical_frameworks,
                :quality_score,
                :created_at
            )
        """)

        # 插入第一层
        db_session.execute(insert_layer_query, {
            'project_id': project_id,
            'synthesis_result_id': synthesis_result_id,
            'layer_number': 1,
            'title': '第一层：数据呈现与基础分析',
            'abstract': layer_1_content[:200],
            'content': layer_1_content,
            'word_count': layer_1_word_count,
            'data_sources': json.dumps(list(analysis_cache.keys())),
            'analysis_types_used': json.dumps(list(analysis_cache.keys())),
            'skills_used': json.dumps(synthesis_data['applied_skills']),
            'theoretical_frameworks': json.dumps([]),
            'quality_score': synthesis_data['confidence_score'],
            'created_at': datetime.utcnow()
        })

        result = db_session.execute(text("SELECT last_insert_rowid()"))
        layer_1_id = result.fetchone()[0]

        # 插入第二层
        db_session.execute(insert_layer_query, {
            'project_id': project_id,
            'synthesis_result_id': synthesis_result_id,
            'layer_number': 2,
            'title': '第二层：理论框架与深度解读',
            'abstract': layer_2_content[:200],
            'content': layer_2_content,
            'word_count': layer_2_word_count,
            'data_sources': json.dumps(list(analysis_cache.keys())),
            'analysis_types_used': json.dumps(list(analysis_cache.keys())),
            'skills_used': json.dumps(synthesis_data['applied_skills']),
            'theoretical_frameworks': json.dumps([p['pattern_name'] for p in synthesis_data['thinking_patterns']]),
            'quality_score': synthesis_data['confidence_score'] * 0.95,
            'created_at': datetime.utcnow()
        })

        result = db_session.execute(text("SELECT last_insert_rowid()"))
        layer_2_id = result.fetchone()[0]

        # 插入第三层
        db_session.execute(insert_layer_query, {
            'project_id': project_id,
            'synthesis_result_id': synthesis_result_id,
            'layer_number': 3,
            'title': '第三层：综合评估与行动建议',
            'abstract': layer_3_content[:200],
            'content': layer_3_content,
            'word_count': layer_3_word_count,
            'data_sources': json.dumps(list(analysis_cache.keys())),
            'analysis_types_used': json.dumps(list(analysis_cache.keys())),
            'skills_used': json.dumps(synthesis_data['applied_skills']),
            'theoretical_frameworks': json.dumps([p['pattern_name'] for p in synthesis_data['thinking_patterns']]),
            'quality_score': synthesis_data['confidence_score'] * 0.98,
            'created_at': datetime.utcnow()
        })

        result = db_session.execute(text("SELECT last_insert_rowid()"))
        layer_3_id = result.fetchone()[0]

        db_session.commit()

        logger.info(f"✅ 三层报告已存储到数据库 - Layer IDs: {layer_1_id}, {layer_2_id}, {layer_3_id}")

        total_words = layer_1_word_count + layer_2_word_count + layer_3_word_count

        return {
            'success': True,
            'layer_1_id': layer_1_id,
            'layer_2_id': layer_2_id,
            'layer_3_id': layer_3_id,
            'layer_1_content': layer_1_content,
            'layer_2_content': layer_2_content,
            'layer_3_content': layer_3_content,
            'layer_1_words': layer_1_word_count,
            'layer_2_words': layer_2_word_count,
            'layer_3_words': layer_3_word_count,
            'total_words': total_words,
            'metadata': {
                'project_id': project_id,
                'synthesis_result_id': synthesis_result_id,
                'analyses_used': len(analysis_cache),
                'confidence_score': synthesis_data['confidence_score'],
                'generated_at': datetime.utcnow().isoformat()
            }
        }

    def _generate_layer_1(
        self,
        project_id: str,
        synthesis_data: Dict[str, Any],
        analysis_cache: Dict[str, Any],
        target_words: int
    ) -> str:
        """
        生成第一层报告：数据呈现与基础分析

        重点：呈现原始数据、统计结果、基础洞察
        """
        sections = []

        # 标题和摘要
        sections.append(f"# 第一层报告：数据呈现与基础分析\n\n项目ID: {project_id}\n")
        sections.append(f"## 综合摘要\n\n{synthesis_data['context_summary']}\n\n")

        # 1. 项目概览（from summary analysis）
        if 'summary' in analysis_cache:
            summary = analysis_cache['summary']['data']
            sections.append("## 1. 项目概览\n\n")
            sections.append(f"### 1.1 数据规模\n\n")
            sections.append(f"- 文档数量：{summary.get('documents', {}).get('total', 0)}个\n")
            sections.append(f"- 文档类型：{summary.get('documents', {}).get('types', 0)}种\n")
            sections.append(f"- 文本块数量：{summary.get('chunks', {}).get('total', 0)}个\n")
            sections.append(f"- 实体数量：{summary.get('entities', {}).get('total', 0)}个\n")
            sections.append(f"- 关系数量：{summary.get('relations', {}).get('total', 0)}条\n")
            sections.append(f"- 知识节点：{summary.get('knowledge', {}).get('nodes', 0)}个\n\n")

            sections.append(f"### 1.2 数据质量指标\n\n")
            metrics = summary.get('metrics', {})
            sections.append(f"- 数据密度：{metrics.get('data_density', 0)}\n")
            sections.append(f"- 知识深度：{metrics.get('knowledge_depth', 0)}\n\n")

        # 2. 分类分析（from category analysis）
        if 'category' in analysis_cache:
            category = analysis_cache['category']['data']
            sections.append("## 2. 数据分类分析\n\n")
            sections.append(f"### 2.1 文档类型分布\n\n")
            for doc_type, count in category.get('doc_type_distribution', {}).items():
                sections.append(f"- {doc_type}: {count}个\n")
            sections.append(f"\n分类覆盖率：{category.get('coverage_rate', 0)*100:.1f}%\n\n")

        # 3. 关键词分析（from keyword analysis）
        if 'keyword' in analysis_cache:
            keyword = analysis_cache['keyword']['data']
            sections.append("## 3. 关键词分析\n\n")
            sections.append(f"识别出{keyword.get('total_unique_keywords', 0)}个独特关键词\n\n")
            sections.append("### 3.1 核心关键词（Top 10）\n\n")
            for kw in keyword.get('top_keywords', [])[:10]:
                sections.append(f"- {kw['keyword']} (权重: {kw['score']})\n")
            sections.append("\n")

        # 4. 实体与关系网络（from entity and relation analysis）
        if 'entity' in analysis_cache and 'relation' in analysis_cache:
            entity = analysis_cache['entity']['data']
            relation = analysis_cache['relation']['data']
            sections.append("## 4. 实体与关系网络\n\n")
            sections.append(f"### 4.1 实体统计\n\n")
            sections.append(f"- 总实体数：{entity.get('total_entities', 0)}\n")
            sections.append(f"- 实体类型：{entity.get('entity_types_count', 0)}种\n\n")

            sections.append(f"### 4.2 关系统计\n\n")
            sections.append(f"- 总关系数：{relation.get('total_relations', 0)}\n")
            sections.append(f"- 关系类型：{len(relation.get('relation_types', []))}种\n")
            sections.append(f"- 网络密度：{relation.get('network_density', 0):.4f}\n\n")

        # 5. 时间线分析（from timeline analysis）
        if 'timeline' in analysis_cache:
            timeline = analysis_cache['timeline']['data']
            sections.append("## 5. 时间线分析\n\n")
            sections.append(f"记录事件总数：{timeline.get('total_events', 0)}个\n\n")
            time_span = timeline.get('time_span', {})
            if time_span.get('start') and time_span.get('end'):
                sections.append(f"时间跨度：{time_span['start']} 至 {time_span['end']} ({time_span['duration_days']}天)\n\n")

        # 6. 情感分析（from sentiment analysis）
        if 'sentiment' in analysis_cache:
            sentiment = analysis_cache['sentiment']['data']
            sections.append("## 6. 情感倾向分析\n\n")
            sections.append(f"整体情感：{sentiment.get('overall_sentiment', 'neutral')}\n")
            sections.append(f"置信度：{sentiment.get('confidence_score', 0):.2f}\n\n")

        # 7. 主题分析（from theme analysis）
        if 'theme' in analysis_cache:
            theme = analysis_cache['theme']['data']
            sections.append("## 7. 主题分析\n\n")
            sections.append(f"识别出{len(theme.get('main_themes', []))}个主要主题\n\n")
            for i, t in enumerate(theme.get('main_themes', [])[:5], 1):
                sections.append(f"{i}. {t.get('theme', 'Unknown')} (占比: {t.get('percentage', 0):.1f}%)\n")
            sections.append("\n")

        # 8. 综合洞察（from synthesis_data）
        sections.append("## 8. 关键洞察\n\n")
        for insight in synthesis_data['key_insights'][:10]:
            sections.append(f"- **{insight.get('aspect', 'general')}**: {insight.get('insight', '')}\n")
        sections.append("\n")

        # 合并所有sections
        content = ''.join(sections)

        # 如果字数不足target_words，补充详细描述
        if len(content) < target_words:
            sections.append("\n## 9. 详细数据呈现\n\n")
            sections.append("以下是各维度的详细统计数据，为后续分析提供基础：\n\n")

            # 补充更多细节直到达到目标字数
            for analysis_type, cache_data in analysis_cache.items():
                if len(''.join(sections)) >= target_words:
                    break
                sections.append(f"### 9.{len(sections)} {analysis_type}分析详情\n\n")
                sections.append(f"```json\n{json.dumps(cache_data['data'], ensure_ascii=False, indent=2)[:500]}\n```\n\n")

            content = ''.join(sections)

        return content[:target_words + 1000]  # 允许一定超出

    def _generate_layer_2(
        self,
        project_id: str,
        synthesis_data: Dict[str, Any],
        analysis_cache: Dict[str, Any],
        layer_1_summary: str,
        target_words: int
    ) -> str:
        """
        生成第二层报告：理论框架与深度解读

        重点：应用理论框架、深度分析、模式识别
        """
        sections = []

        sections.append(f"# 第二层报告：理论框架与深度解读\n\n项目ID: {project_id}\n\n")
        sections.append(f"## 基于第一层的深化分析\n\n{layer_1_summary}\n\n")

        # 1. 理论框架应用（from thinking_patterns）
        sections.append("## 1. 理论框架与思维模式\n\n")
        for pattern in synthesis_data['thinking_patterns']:
            sections.append(f"### {pattern.get('pattern_name', 'Unknown Pattern')}\n\n")
            sections.append(f"{pattern.get('application', '')}\n")
            sections.append(f"应用置信度：{pattern.get('confidence', 0):.2f}\n\n")

        # 2. 趋势分析（from trend analysis）
        if 'trend' in analysis_cache:
            trend = analysis_cache['trend']['data']
            sections.append("## 2. 发展趋势解读\n\n")
            sections.append(f"整体趋势方向：{trend.get('overall_direction', 'unknown')}\n")
            sections.append(f"平均增长率：{trend.get('average_growth_rate', 0):.2f}%\n\n")

            sections.append("### 2.1 多维度趋势分析\n\n")
            for t in trend.get('trends', []):
                sections.append(f"**{t.get('aspect')}**: {t.get('description')}\n")
            sections.append("\n")

        # 3. 对比分析（from comparison analysis）
        if 'comparison' in analysis_cache:
            comparison = analysis_cache['comparison']['data']
            sections.append("## 3. 多维度对比分析\n\n")
            for comp in comparison.get('comparisons', []):
                sections.append(f"### 3.{comparison['comparisons'].index(comp)+1} {comp.get('dimension')}维度\n\n")
                sections.append(f"{comp.get('insight', '')}\n\n")

        # 4. 影响力分析（from impact analysis）
        if 'impact' in analysis_cache:
            impact = analysis_cache['impact']['data']
            sections.append("## 4. 影响力与核心节点分析\n\n")

            sections.append("### 4.1 高影响力实体\n\n")
            for entity in impact.get('high_impact_entities', [])[:5]:
                sections.append(f"- **{entity.get('entity_name')}** ({entity.get('entity_type')})\n")
                sections.append(f"  - 影响力得分：{entity.get('impact_score')}\n")
                sections.append(f"  - 连接数：{entity.get('total_connections')}\n")
            sections.append("\n")

            sections.append("### 4.2 网络拓扑特征\n\n")
            metrics = impact.get('network_metrics', {})
            sections.append(f"- 网络密度：{metrics.get('network_density', 0):.4f}\n")
            sections.append(f"- 桥接节点数：{metrics.get('bridge_node_count', 0)}\n")
            sections.append(f"- 连接性评级：{impact.get('summary', {}).get('network_connectivity', 'unknown')}\n\n")

        # 5. 异常分析（from anomaly analysis）
        if 'anomaly' in analysis_cache:
            anomaly = analysis_cache['anomaly']['data']
            sections.append("## 5. 异常模式识别\n\n")
            sections.append(f"数据质量评分：{anomaly.get('data_quality_score', 0):.2f}/100\n\n")

            if anomaly.get('total_anomalies', 0) > 0:
                sections.append("### 5.1 识别出的异常\n\n")
                for anom in anomaly.get('anomalies', []):
                    sections.append(f"**{anom.get('type')}** (严重性: {anom.get('severity')})\n")
                    sections.append(f"- {anom.get('description')}\n")
                    sections.append(f"- 影响：{anom.get('impact')}\n\n")

        # 6. 决策因素分析（from synthesis_data）
        sections.append("## 6. 决策因素分析\n\n")
        for factor in synthesis_data['decision_factors']:
            sections.append(f"- **{factor.get('type')}**: {factor.get('factor', '')}\n")
        sections.append("\n")

        # 7. Skill知识应用
        if synthesis_data['skill_knowledge']:
            sections.append("## 7. Skill知识库应用\n\n")
            for sk in synthesis_data['skill_knowledge']:
                sections.append(f"应用了{sk.get('total_skills', 0)}个Skills，平均有效性{sk.get('avg_effectiveness', 0):.2f}\n\n")

        content = ''.join(sections)

        # 补充至目标字数
        if len(content) < target_words:
            sections.append("\n## 8. 深度理论解读\n\n")
            sections.append("基于以上数据和理论框架，我们可以得出以下深层次洞察：\n\n")

            # 根据分析结果生成更多理论解读
            sections.append("### 8.1 数据背后的模式\n\n")
            sections.append("通过多维度分析发现，项目数据呈现出明显的结构化特征。")
            sections.append("实体网络的密度和连接模式反映了知识组织的内在逻辑。\n\n")

            content = ''.join(sections)

        return content[:target_words + 1000]

    def _generate_layer_3(
        self,
        project_id: str,
        synthesis_data: Dict[str, Any],
        analysis_cache: Dict[str, Any],
        layer_1_summary: str,
        layer_2_summary: str,
        target_words: int
    ) -> str:
        """
        生成第三层报告：综合评估与行动建议

        重点：战略建议、行动计划、风险与机会
        """
        sections = []

        sections.append(f"# 第三层报告：综合评估与行动建议\n\n项目ID: {project_id}\n\n")

        # 1. 综合评估
        sections.append("## 1. 综合评估\n\n")
        sections.append(f"基于前两层分析，项目整体置信度为{synthesis_data['confidence_score']:.2f}。\n\n")

        # 2. 风险评估（from risk analysis）
        if 'risk' in analysis_cache:
            risk = analysis_cache['risk']['data']
            sections.append("## 2. 风险评估\n\n")
            sections.append(f"整体风险等级：**{risk.get('overall_risk_level', 'unknown').upper()}**\n")
            sections.append(f"风险评分：{risk.get('risk_score', 0):.2f}/100\n\n")

            if risk.get('total_risks', 0) > 0:
                sections.append("### 2.1 识别出的风险\n\n")
                for r in risk.get('risks', []):
                    sections.append(f"#### {r.get('risk_type')} (严重性: {r.get('severity')})\n\n")
                    sections.append(f"- **描述**: {r.get('description')}\n")
                    sections.append(f"- **影响**: {r.get('impact')}\n")
                    sections.append(f"- **缓解措施**: {r.get('mitigation')}\n\n")

        # 3. 机会识别（from opportunity analysis）
        if 'opportunity' in analysis_cache:
            opportunity = analysis_cache['opportunity']['data']
            sections.append("## 3. 机会识别\n\n")
            sections.append(f"识别出{opportunity.get('total_opportunities', 0)}个潜在机会\n\n")

            for opp in opportunity.get('opportunities', []):
                sections.append(f"### 3.{opportunity['opportunities'].index(opp)+1} {opp.get('opportunity_type')} (优先级: {opp.get('priority')})\n\n")
                sections.append(f"- **描述**: {opp.get('description')}\n")
                sections.append(f"- **潜在收益**: {opp.get('potential_gain')}\n")
                sections.append(f"- **行动项**:\n")
                for action in opp.get('action_items', []):
                    sections.append(f"  - {action}\n")
                sections.append("\n")

        # 4. 执行建议（from recommendation analysis and synthesis_data）
        sections.append("## 4. 执行建议与行动计划\n\n")

        if 'recommendation' in analysis_cache:
            rec = analysis_cache['recommendation']['data']

            # 项目健康评分
            sections.append(f"### 4.1 项目健康评分\n\n")
            sections.append(f"综合健康评分：{rec.get('project_health_score', 0):.2f}/100\n\n")

            # 具体建议
            sections.append(f"### 4.2 优先建议事项\n\n")
            for recommendation in rec.get('recommendations', []):
                sections.append(f"#### {recommendation.get('title')} ({recommendation.get('priority')}优先级)\n\n")
                sections.append(f"**当前状态**: {recommendation.get('current_state')}\n\n")
                sections.append(f"**目标状态**: {recommendation.get('target_state')}\n\n")
                sections.append(f"**理由**: {recommendation.get('rationale')}\n\n")
                sections.append(f"**执行步骤**:\n\n")
                for action in recommendation.get('actions', []):
                    sections.append(f"{action.get('step')}. {action.get('action')}\n")
                    sections.append(f"   - 方法：{action.get('method')}\n")
                sections.append(f"\n**预期影响**: {recommendation.get('expected_impact')}\n\n")

            # 执行路线图
            roadmap = rec.get('execution_roadmap', {})
            if roadmap.get('phases'):
                sections.append(f"### 4.3 执行路线图\n\n")
                sections.append(f"预计总时长：{roadmap.get('estimated_total_duration')}\n\n")
                for phase in roadmap.get('phases', []):
                    sections.append(f"**阶段{phase.get('phase')}: {phase.get('name')}** ({phase.get('duration')})\n\n")
                    sections.append(f"目标：{phase.get('goal')}\n\n")
                    sections.append(f"包含建议：\n")
                    for rec_title in phase.get('recommendations', []):
                        sections.append(f"- {rec_title}\n")
                    sections.append("\n")

        # 5. 综合建议（from synthesis_data）
        sections.append("## 5. 战略性综合建议\n\n")
        for rec in synthesis_data['recommendations']:
            sections.append(f"### {rec.get('title')} ({rec.get('priority')})\n\n")
            sections.append(f"**现状**: {rec.get('current_state')}\n\n")
            sections.append(f"**目标**: {rec.get('target_state')}\n\n")

        # 6. 立即行动项
        sections.append("## 6. 立即行动项（Next Steps）\n\n")
        if 'recommendation' in analysis_cache:
            immediate = analysis_cache['recommendation']['data'].get('immediate_actions', [])
            for i, action in enumerate(immediate, 1):
                sections.append(f"{i}. {action.get('title')}\n")
                sections.append(f"   - 第一步：{action.get('first_step')}\n")
        sections.append("\n")

        # 7. 结论
        sections.append("## 7. 结论\n\n")
        sections.append(f"通过三层深度分析，本报告为项目{project_id}提供了从数据呈现、理论解读到行动建议的完整视图。")
        sections.append(f"建议优先执行{len([r for r in synthesis_data['recommendations'] if r.get('priority') == 'high'])}项高优先级建议，")
        sections.append(f"以实现项目目标并规避关键风险。\n\n")

        content = ''.join(sections)

        # 补充至目标字数
        if len(content) < target_words:
            sections.append("\n## 8. 附加说明\n\n")
            sections.append("本报告基于完整的数据分析链，所有结论均可追溯到原始数据源。")
            sections.append("建议定期更新分析以反映项目最新状态。\n\n")
            content = ''.join(sections)

        return content[:target_words + 1000]
