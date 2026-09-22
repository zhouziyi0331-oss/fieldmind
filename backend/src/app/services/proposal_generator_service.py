"""
提案生成服务 - Action Proposal Generator
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


class ProposalGeneratorService:
    """提案生成服务 - 将分析结果转化为行动方案"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def generate_proposal(
        self,
        project_id: int,
        proposal_type: str = 'government',
        include_budget: bool = True,
        include_risk: bool = True
    ) -> Dict[str, Any]:
        """
        生成提案文档

        Args:
            project_id: 项目ID
            proposal_type: 提案类型 (government/academic/business)
            include_budget: 是否包含预算框架
            include_risk: 是否包含风险评估

        Returns:
            完整的提案文档
        """
        logger.info(f"开始生成提案，项目ID: {project_id}, 类型: {proposal_type}")

        # 1. 收集项目数据
        project_data = self._collect_project_data(project_id)

        # 2. 生成提案框架
        proposal = self._build_proposal_framework(
            project_data,
            proposal_type,
            include_budget,
            include_risk
        )

        # 3. 填充内容
        proposal = self._fill_proposal_content(proposal, project_data)

        # 4. 生成Markdown文档
        markdown = self._generate_markdown(proposal)

        proposal['markdown'] = markdown
        proposal['generated_at'] = datetime.utcnow().isoformat()

        logger.info(f"提案生成完成，字数: {len(markdown)}")

        return proposal

    def _collect_project_data(self, project_id: int) -> Dict[str, Any]:
        """收集项目的所有相关数据"""
        from app.models.project import Project, ProjectDocument
        from app.services.vectorization_service_complete import DocumentChunk

        # 获取项目基本信息
        project = self.db.query(Project).filter(
            Project.id == project_id
        ).first()

        if not project:
            raise ValueError(f"项目 {project_id} 不存在")

        # 获取文档统计
        doc_count = self.db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).count()

        # 获取chunks统计
        chunk_count = self.db.query(DocumentChunk).filter(
            DocumentChunk.project_id == project_id
        ).count()

        # 获取所有分析结果
        analyses = self.db.query(AnalysisResult).filter(
            AnalysisResult.project_id == project_id
        ).order_by(AnalysisResult.created_at.desc()).all()

        # 按类型分组分析
        keyword_analyses = [a for a in analyses if a.analysis_type == 'keyword_search']
        creative_analyses = [a for a in analyses if a.analysis_type == 'creative']
        business_analyses = [a for a in analyses if a.analysis_type == 'business']

        return {
            'project': {
                'id': project.id,
                'name': project.name,
                'description': project.description
            },
            'statistics': {
                'documents': doc_count,
                'chunks': chunk_count,
                'analyses': len(analyses)
            },
            'analyses': {
                'keyword': keyword_analyses,
                'creative': creative_analyses,
                'business': business_analyses
            }
        }

    def _build_proposal_framework(
        self,
        project_data: Dict[str, Any],
        proposal_type: str,
        include_budget: bool,
        include_risk: bool
    ) -> Dict[str, Any]:
        """构建提案框架"""

        framework = {
            'title': f"{project_data['project']['name']} - 行动提案",
            'type': proposal_type,
            'sections': []
        }

        # 根据提案类型确定章节结构
        if proposal_type == 'government':
            # 政府汇报型：简洁有力
            framework['sections'] = [
                {'id': 'background', 'title': '一、项目背景', 'content': []},
                {'id': 'findings', 'title': '二、调研核心发现', 'content': []},
                {'id': 'opportunities', 'title': '三、机会研判', 'content': []},
                {'id': 'actions', 'title': '四、行动路径', 'content': []},
                {'id': 'budget', 'title': '五、预算框架', 'content': []} if include_budget else None,
                {'id': 'risks', 'title': '六、风险评估', 'content': []} if include_risk else None,
                {'id': 'next_steps', 'title': '七、下一步计划', 'content': []}
            ]

        elif proposal_type == 'academic':
            # 学术汇报型：详细数据
            framework['sections'] = [
                {'id': 'abstract', 'title': '摘要', 'content': []},
                {'id': 'background', 'title': '一、研究背景', 'content': []},
                {'id': 'methodology', 'title': '二、调研方法', 'content': []},
                {'id': 'findings', 'title': '三、核心发现', 'content': []},
                {'id': 'analysis', 'title': '四、深度分析', 'content': []},
                {'id': 'recommendations', 'title': '五、建议', 'content': []},
                {'id': 'conclusion', 'title': '六、结论', 'content': []}
            ]

        elif proposal_type == 'business':
            # 商业计划型：强调ROI
            framework['sections'] = [
                {'id': 'executive_summary', 'title': 'Executive Summary', 'content': []},
                {'id': 'market_analysis', 'title': '一、市场分析', 'content': []},
                {'id': 'opportunities', 'title': '二、商业机会', 'content': []},
                {'id': 'strategy', 'title': '三、实施策略', 'content': []},
                {'id': 'financial', 'title': '四、财务预测', 'content': []},
                {'id': 'roi', 'title': '五、投资回报分析', 'content': []},
                {'id': 'risks', 'title': '六、风险与应对', 'content': []},
                {'id': 'milestones', 'title': '七、关键里程碑', 'content': []}
            ]

        # 过滤掉None
        framework['sections'] = [s for s in framework['sections'] if s is not None]

        return framework

    def _fill_proposal_content(
        self,
        proposal: Dict[str, Any],
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """填充提案内容"""

        for section in proposal['sections']:
            section_id = section['id']

            if section_id == 'background':
                section['content'] = self._generate_background(project_data)

            elif section_id == 'findings':
                section['content'] = self._generate_findings(project_data)

            elif section_id == 'opportunities':
                section['content'] = self._generate_opportunities(project_data)

            elif section_id == 'actions':
                section['content'] = self._generate_actions(project_data)

            elif section_id == 'budget':
                section['content'] = self._generate_budget(project_data)

            elif section_id == 'risks':
                section['content'] = self._generate_risks(project_data)

            elif section_id == 'next_steps':
                section['content'] = self._generate_next_steps(project_data)

            elif section_id == 'methodology':
                section['content'] = self._generate_methodology(project_data)

            elif section_id == 'market_analysis':
                section['content'] = self._generate_market_analysis(project_data)

            elif section_id == 'roi':
                section['content'] = self._generate_roi(project_data)

        return proposal

    def _generate_background(self, data: Dict[str, Any]) -> List[str]:
        """生成项目背景"""
        project = data['project']
        stats = data['statistics']

        return [
            f"本次调研针对{project['name']}进行深入分析。",
            f"调研团队共收集{stats['documents']}份材料，"
            f"提取{stats['chunks']}个关键信息点，"
            f"完成{stats['analyses']}项专项分析。",
            f"项目概述：{project.get('description', '详见附件')}"
        ]

    def _generate_findings(self, data: Dict[str, Any]) -> List[str]:
        """生成核心发现（增强版）"""
        findings = []

        # 从关键词分析提取发现
        keyword_analyses = data['analyses']['keyword']
        if keyword_analyses:
            findings.append("### 🔍 关键信息点分析")
            findings.append("")

            # 统计关键词频率
            keyword_freq = {}
            for analysis in keyword_analyses:
                result = analysis.result
                keyword = result.get('keyword', '')
                doc_count = len(result.get('documents', []))
                if keyword:
                    keyword_freq[keyword] = doc_count

            # 按频率排序
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)

            findings.append("**高频关键词统计**：")
            for keyword, count in sorted_keywords[:5]:
                findings.append(f"- 「{keyword}」出现 {count} 次，是重点关注领域")
            findings.append("")

        # 从文创分析提取发现
        creative_analyses = data['analyses']['creative']
        if creative_analyses:
            findings.append("### 💡 文创潜力发现")
            findings.append("")

            all_ideas = []
            for analysis in creative_analyses:
                result = analysis.result
                possibilities = result.get('creative_possibilities', [])
                all_ideas.extend(possibilities)

            if all_ideas:
                findings.append(f"**综合评估**：识别出 {len(all_ideas)} 个文创机会点")
                findings.append("")
                findings.append("**优质创意TOP3**：")
                for idx, idea in enumerate(all_ideas[:3], 1):
                    idea_text = idea.get('idea', '')
                    feasibility = idea.get('feasibility_score', 75)
                    findings.append(f"{idx}. **{idea_text}**")
                    findings.append(f"   - 可行性评分：{feasibility}/100")
                    if 'description' in idea:
                        findings.append(f"   - 说明：{idea['description']}")
                findings.append("")

        # 从业态分析提取发现
        business_analyses = data['analyses']['business']
        if business_analyses:
            findings.append("### 💼 业态适配性分析")
            findings.append("")

            for analysis in business_analyses:
                result = analysis.result
                formats = result.get('suggested_formats', [])

                if formats:
                    findings.append(f"**推荐业态清单**：共 {len(formats)} 种")
                    findings.append("")

                    for idx, fmt in enumerate(formats[:5], 1):
                        name = fmt.get('format_name', '')
                        description = fmt.get('description', '适合当地发展')
                        findings.append(f"{idx}. **{name}**")
                        findings.append(f"   - {description}")
                    findings.append("")

        if not findings:
            findings.append("基于收集的材料，我们进行了全面分析。详细发现见各专项报告。")

        return findings

    def _generate_opportunities(self, data: Dict[str, Any]) -> List[str]:
        """生成机会研判（增强版）"""
        opportunities = []

        creative_analyses = data['analyses']['creative']

        if creative_analyses:
            opportunities.append("### 🎯 机会一：文创开发")
            opportunities.append("")

            # 收集所有创意
            all_ideas = []
            for analysis in creative_analyses:
                result = analysis.result
                possibilities = result.get('creative_possibilities', [])
                all_ideas.extend(possibilities)

            # 按可行性评分排序
            sorted_ideas = sorted(
                all_ideas,
                key=lambda x: x.get('feasibility_score', 0),
                reverse=True
            )

            for idx, idea in enumerate(sorted_ideas[:3], 1):
                idea_text = idea.get('idea', '')
                description = idea.get('description', '')
                feasibility = idea.get('feasibility_score', 75)

                opportunities.append(f"**{idx}. {idea_text}**")
                opportunities.append(f"- 可行性：{feasibility}/100")
                if description:
                    opportunities.append(f"- 方案：{description}")
                opportunities.append(f"- 预期效果：提升文化影响力，带动相关产业发展")
                opportunities.append("")

        business_analyses = data['analyses']['business']

        if business_analyses:
            opportunities.append("### 🏪 机会二：业态升级")
            opportunities.append("")

            for analysis in business_analyses[:1]:
                result = analysis.result
                formats = result.get('suggested_formats', [])

                for idx, fmt in enumerate(formats[:3], 1):
                    name = fmt.get('format_name', '')
                    description = fmt.get('description', '')

                    opportunities.append(f"**{idx}. {name}**")
                    if description:
                        opportunities.append(f"- 说明：{description}")
                    opportunities.append(f"- 市场前景：结合当地特色，具有良好发展潜力")
                    opportunities.append("")

        opportunities.append("### 🌟 机会三：品牌打造")
        opportunities.append("")
        opportunities.append("**战略定位**：")
        opportunities.append("- 基于调研发现的独特文化资源")
        opportunities.append("- 系统性打造地方文化品牌")
        opportunities.append("- 形成可持续的文化IP")
        opportunities.append("")
        opportunities.append("**预期价值**：")
        opportunities.append("- 提升地方知名度和美誉度")
        opportunities.append("- 带动文旅产业发展")
        opportunities.append("- 促进文化传承与创新")

        return opportunities

    def _generate_actions(self, data: Dict[str, Any]) -> List[str]:
        """生成行动路径"""
        return [
            "### 短期行动（1-3个月）",
            "1. 完成资源盘点和基础设施评估",
            "2. 启动第一批试点项目",
            "3. 建立项目管理和监测机制",
            "",
            "### 中期行动（3-6个月）",
            "1. 扩大试点范围，总结经验",
            "2. 完善运营体系和标准",
            "3. 开展品牌宣传和推广",
            "",
            "### 长期行动（6-12个月）",
            "1. 形成可持续运营模式",
            "2. 复制推广成功经验",
            "3. 建立长效发展机制"
        ]

    def _generate_budget(self, data: Dict[str, Any]) -> List[str]:
        """生成预算框架"""
        return [
            "### 预算概算",
            "",
            "| 项目 | 预算（万元） | 说明 |",
            "|------|-------------|------|",
            "| 基础设施改造 | 50-100 | 根据实际需求调整 |",
            "| 项目启动资金 | 30-50 | 包含前期投入 |",
            "| 运营推广费用 | 20-30 | 年度预算 |",
            "| 人员培训 | 10-20 | 包含专业培训 |",
            "| 应急储备金 | 10 | 风险应对 |",
            "| **合计** | **120-210** | 分阶段投入 |",
            "",
            "注：具体预算需根据实际情况进一步细化。"
        ]

    def _generate_risks(self, data: Dict[str, Any]) -> List[str]:
        """生成风险评估"""
        return [
            "### 主要风险",
            "",
            "**1. 政策风险**",
            "- 风险描述：相关政策可能调整",
            "- 应对措施：密切关注政策动态，保持灵活性",
            "",
            "**2. 市场风险**",
            "- 风险描述：市场接受度不确定",
            "- 应对措施：小规模试点，快速迭代调整",
            "",
            "**3. 执行风险**",
            "- 风险描述：团队能力和资源不足",
            "- 应对措施：引入专业团队，建立培训机制",
            "",
            "**4. 财务风险**",
            "- 风险描述：资金链压力",
            "- 应对措施：分阶段投入，确保现金流安全"
        ]

    def _generate_next_steps(self, data: Dict[str, Any]) -> List[str]:
        """生成下一步计划"""
        return [
            "### 近期工作安排",
            "",
            "**第一周**",
            "- 召开项目启动会",
            "- 成立项目工作组",
            "- 明确分工和责任",
            "",
            "**第二周**",
            "- 开展详细调研",
            "- 完成方案细化",
            "- 启动前期准备",
            "",
            "**第三-四周**",
            "- 正式启动试点",
            "- 建立监测机制",
            "- 开展培训工作",
            "",
            "### 关键里程碑",
            "- 1个月：完成试点启动",
            "- 3个月：形成初步成果",
            "- 6个月：完成中期评估",
            "- 12个月：实现全面推广"
        ]

    def _generate_methodology(self, data: Dict[str, Any]) -> List[str]:
        """生成调研方法"""
        stats = data['statistics']

        return [
            "### 调研方法",
            "",
            f"本次调研采用多元化方法，共收集{stats['documents']}份材料：",
            "",
            "**1. 文献研究**",
            "- 收集政策文件、行业报告、学术论文",
            "- 建立文献知识库，进行系统分析",
            "",
            "**2. 田野调查**",
            "- 实地访谈、参与观察",
            "- 收集第一手资料",
            "",
            "**3. 数据分析**",
            f"- 提取{stats['chunks']}个关键信息点",
            f"- 完成{stats['analyses']}项专项分析",
            "- 运用AI辅助分析工具"
        ]

    def _generate_market_analysis(self, data: Dict[str, Any]) -> List[str]:
        """生成市场分析"""
        return [
            "### 市场现状",
            "根据调研数据和行业分析，当前市场呈现以下特点：",
            "",
            "**市场规模**",
            "- 目标市场规模持续增长",
            "- 消费需求日益多元化",
            "",
            "**竞争格局**",
            "- 市场处于发展初期",
            "- 竞争者较少，机会窗口明显",
            "",
            "**目标客群**",
            "- 主要面向都市休闲人群",
            "- 文化体验需求旺盛"
        ]

    def _generate_roi(self, data: Dict[str, Any]) -> List[str]:
        """生成ROI分析"""
        return [
            "### 投资回报分析",
            "",
            "**收入预测**",
            "",
            "| 年度 | 预计收入（万元） | 说明 |",
            "|------|-----------------|------|",
            "| 第1年 | 50-80 | 试点阶段 |",
            "| 第2年 | 100-150 | 扩展阶段 |",
            "| 第3年 | 200-300 | 成熟阶段 |",
            "",
            "**回报周期**",
            "- 预计投资回收期：2-3年",
            "- 内部收益率（IRR）：预计15-20%",
            "- 净现值（NPV）：正值，项目可行",
            "",
            "注：以上为初步测算，实际需根据详细商业计划调整。"
        ]

    def _generate_markdown(self, proposal: Dict[str, Any]) -> str:
        """生成Markdown文档（增强版）"""
        lines = []

        # 标题
        lines.append(f"# {proposal['title']}")
        lines.append("")
        lines.append(f"*生成时间：{datetime.utcnow().strftime('%Y年%m月%d日')}*")
        lines.append(f"*提案类型：{self._get_type_name(proposal['type'])}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 各章节
        for section in proposal['sections']:
            lines.append(section['title'])
            lines.append("")

            for item in section['content']:
                lines.append(item)

            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _get_type_name(self, type_code: str) -> str:
        """获取提案类型中文名"""
        type_names = {
            'government': '政府汇报型',
            'academic': '学术汇报型',
            'business': '商业计划型'
        }
        return type_names.get(type_code, '通用型')

    def generate_html(self, proposal: Dict[str, Any]) -> str:
        """生成HTML文档（带样式）"""
        html_parts = []

        # HTML头部
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="zh-CN">')
        html_parts.append('<head>')
        html_parts.append('    <meta charset="UTF-8">')
        html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html_parts.append(f'    <title>{proposal["title"]}</title>')
        html_parts.append(self._get_html_styles())
        html_parts.append('</head>')
        html_parts.append('<body>')
        html_parts.append('    <div class="container">')

        # 标题页
        html_parts.append('        <div class="title-page">')
        html_parts.append(f'            <h1>{proposal["title"]}</h1>')
        html_parts.append(f'            <p class="subtitle">提案类型：{self._get_type_name(proposal["type"])}</p>')
        html_parts.append(f'            <p class="date">生成时间：{datetime.utcnow().strftime("%Y年%m月%d日")}</p>')
        html_parts.append('        </div>')

        # 各章节内容
        for section in proposal['sections']:
            html_parts.append('        <div class="section">')
            html_parts.append(f'            <h2>{section["title"]}</h2>')

            for item in section['content']:
                # 转换Markdown格式到HTML
                html_item = self._markdown_to_html(item)
                html_parts.append(f'            {html_item}')

            html_parts.append('        </div>')

        # 页脚
        html_parts.append('        <div class="footer">')
        html_parts.append('            <p>由 FieldMind 自动生成</p>')
        html_parts.append('        </div>')

        html_parts.append('    </div>')
        html_parts.append('</body>')
        html_parts.append('</html>')

        return '\n'.join(html_parts)

    def _get_html_styles(self) -> str:
        """获取HTML样式"""
        return '''
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .title-page {
            text-align: center;
            padding: 60px 0;
            border-bottom: 3px solid #2563eb;
            margin-bottom: 40px;
        }
        .title-page h1 {
            font-size: 36px;
            color: #1e293b;
            margin-bottom: 20px;
        }
        .subtitle {
            font-size: 18px;
            color: #64748b;
            margin-bottom: 10px;
        }
        .date {
            font-size: 14px;
            color: #94a3b8;
        }
        .section {
            margin-bottom: 40px;
        }
        .section h2 {
            font-size: 24px;
            color: #1e293b;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        .section h3 {
            font-size: 20px;
            color: #334155;
            margin: 20px 0 10px;
        }
        .section p {
            margin-bottom: 12px;
            text-align: justify;
        }
        .section ul, .section ol {
            margin-left: 20px;
            margin-bottom: 12px;
        }
        .section li {
            margin-bottom: 8px;
        }
        .section table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .section table th,
        .section table td {
            border: 1px solid #e2e8f0;
            padding: 12px;
            text-align: left;
        }
        .section table th {
            background: #f8fafc;
            font-weight: 600;
        }
        .footer {
            text-align: center;
            padding: 20px 0;
            margin-top: 40px;
            border-top: 1px solid #e2e8f0;
            color: #94a3b8;
            font-size: 14px;
        }
        strong {
            color: #1e293b;
            font-weight: 600;
        }
        @media print {
            body {
                background: white;
                padding: 0;
            }
            .container {
                box-shadow: none;
                padding: 20px;
            }
        }
    </style>
        '''

    def _markdown_to_html(self, text: str) -> str:
        """简单的Markdown到HTML转换"""
        if not text.strip():
            return '<br>'

        # 处理标题
        if text.startswith('###'):
            return f'<h3>{text.replace("###", "").strip()}</h3>'
        elif text.startswith('##'):
            return f'<h2>{text.replace("##", "").strip()}</h2>'

        # 处理列表
        if text.strip().startswith('- '):
            return f'<li>{text.strip()[2:]}</li>'
        if text.strip().startswith('* '):
            return f'<li>{text.strip()[2:]}</li>'

        # 处理表格行
        if '|' in text:
            cells = [cell.strip() for cell in text.split('|') if cell.strip()]
            if cells:
                if text.strip().startswith('|'):
                    # 表格头或数据行
                    cell_html = ''.join([f'<td>{cell}</td>' for cell in cells])
                    return f'<tr>{cell_html}</tr>'

        # 处理粗体
        text = text.replace('**', '<strong>').replace('**', '</strong>')

        # 普通段落
        return f'<p>{text}</p>'
