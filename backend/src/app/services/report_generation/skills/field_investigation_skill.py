"""
田野调查报告生成 Skill
基于大地遗产"内容运营"方法论

核心理念：
- 从"资源管理"到"内容运营"的转变
- 三大挖掘方向：大考古、泛艺术、新乡土
- 三大转化模式：与旅游要素融合、与公共文化产品融合、打造内容IP

改造说明：
- Skill只定义方法论框架和分析维度
- 实际报告内容由LLM深度分析田野原文生成
- 无硬编码模板，报告完全数据驱动
"""

from typing import Dict, Any
import logging

from .llm_analysis_helper import LLMAnalysisHelper

logger = logging.getLogger(__name__)


class FieldInvestigationSkill:
    """
    田野调查报告生成 Skill

    基于大地遗产方法论，将文化遗产资源转化为可体验的内容和产品
    使用LLM深度分析真实田野数据，而非模板化生成
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """初始化Skill：定义方法论框架"""

        # 大地遗产方法论：三大内容挖掘方向
        self.excavation_framework = {
            "大考古": {
                "核心理念": "让考古发现从学术殿堂走向大众生活",
                "挖掘重点": [
                    "考古遗址背后的历史叙事",
                    "文物器物的故事性表达",
                    "考古发现与当代生活的关联"
                ],
                "分析维度": [
                    "这些考古/历史元素承载了什么样的文化记忆？",
                    "如何用故事化的方式讲述考古发现？",
                    "考古资源如何与当代审美和生活方式结合？"
                ]
            },
            "泛艺术": {
                "核心理念": "挖掘建筑、民俗、手工艺的艺术性和美学价值",
                "挖掘重点": [
                    "建筑空间的美学表达",
                    "民俗仪式的艺术呈现",
                    "传统技艺的当代演绎"
                ],
                "分析维度": [
                    "这些艺术/技艺元素体现了什么样的美学观念？",
                    "如何从艺术鉴赏的角度解读这些文化形式？",
                    "传统艺术形式如何进行现代化转译？"
                ]
            },
            "新乡土": {
                "核心理念": "发现乡土文化的当代价值和生活美学",
                "挖掘重点": [
                    "乡土生活方式的美学价值",
                    "社群关系与地方认同",
                    "乡土文化的现代性转化"
                ],
                "分析维度": [
                    "这些乡土元素反映了什么样的生活智慧和价值观？",
                    "地方社群如何通过文化实践建构身份认同？",
                    "乡土文化如何回应城市人对美好生活的向往？"
                ]
            }
        }

        # 大地遗产方法论：三大转化模式
        self.transformation_framework = {
            "旅游要素融合": {
                "核心理念": "将文化内容融入吃住行游购娱六大旅游要素",
                "转化路径": [
                    "文化主题餐饮（吃）",
                    "文化主题住宿（住）",
                    "文化主题交通/导览（行）",
                    "文化体验项目（游）",
                    "文化创意商品（购）",
                    "文化娱乐活动（娱）"
                ],
                "设计要点": [
                    "如何将文化元素转化为可感知的旅游体验？",
                    "体验设计如何平衡文化深度与游客接受度？",
                    "如何构建可持续的商业模式？"
                ]
            },
            "公共文化产品融合": {
                "核心理念": "与博物馆、图书馆、文化馆等公共文化空间结合",
                "转化路径": [
                    "文化主题展览",
                    "文化沙龙/讲座",
                    "研学课程",
                    "文化节庆活动"
                ],
                "设计要点": [
                    "如何通过公共文化产品扩大文化影响力？",
                    "如何设计兼具教育性和体验性的文化活动？",
                    "如何建立文化资源与公共机构的合作机制？"
                ]
            },
            "内容IP打造": {
                "核心理念": "提炼文化符号，打造可持续运营的内容IP",
                "转化路径": [
                    "节庆IP（传统节日的现代化表达）",
                    "人物IP（历史人物/民间传说的IP化）",
                    "故事IP（地方故事的内容生产）",
                    "物产IP（特色物产的品牌化）"
                ],
                "设计要点": [
                    "如何提炼具有传播力的文化符号？",
                    "如何构建IP的内容生产和运营体系？",
                    "如何实现IP的跨媒介、跨场景应用？"
                ]
            }
        }

        # 初始化LLM分析助手
        self.llm_helper = LLMAnalysisHelper()

    def generate_report(self, report_material: Dict[str, Any]) -> str:
        """
        生成完整的田野调查报告

        Args:
            report_material: 报告素材（包含citation_pool, keywords, entities等）

        Returns:
            完整的报告内容（目标：10,000字）
        """
        logger.info("开始生成田野调查报告（基于大地遗产方法论）")

        # 提取数据上下文
        data_context = self._extract_data_context(report_material)

        # 报告结构
        report_content = ""

        # 1. 方法论框架介绍（~500字）
        report_content += self._generate_framework_intro()

        # 2. 田野资源概览（LLM分析，~1500字）
        report_content += self._analyze_field_resources_with_llm(data_context)

        # 3. 三大挖掘方向的深度分析（每个方向~2000字，共~6000字）
        for direction_name, direction_info in self.excavation_framework.items():
            report_content += self._analyze_excavation_direction_with_llm(
                direction_name, direction_info, data_context
            )

        # 4. 三大转化模式的方案设计（LLM分析，~2000字）
        report_content += self._design_transformation_strategies_with_llm(data_context)

        logger.info(f"田野调查报告生成完成，总字数：{len(report_content)}")

        return report_content

    def _extract_data_context(self, report_material: Dict[str, Any]) -> str:
        """
        从report_material中提取数据上下文
        用于提供给LLM进行分析
        """
        context_parts = []

        # 1. 项目统计信息
        stats = report_material.get("project_statistics", {})
        if stats:
            context_parts.append(f"### 项目统计\n")
            context_parts.append(f"- 文档数量: {stats.get('total_chunks', 0)} 段")
            context_parts.append(f"- 总字数: {stats.get('total_words', 0):,} 字")
            context_parts.append(f"- 关键词数量: {len(report_material.get('main_keywords', []))}\n")

        # 2. 主要关键词
        keywords = report_material.get("main_keywords", [])
        if keywords:
            context_parts.append(f"### 主要关键词（前20个）\n")
            for kw in keywords[:20]:
                keyword_text = kw.get("keyword", "")
                pagerank = kw.get("pagerank", 0)
                context_parts.append(f"- {keyword_text} (权重: {pagerank:.3f})")
            context_parts.append("")

        # 3. 核心实体
        entities = report_material.get("core_entities", {})
        if entities:
            context_parts.append(f"### 核心实体\n")
            for entity_type, entity_list in entities.items():
                if entity_list:
                    entity_names = [e.get("entity", "") if isinstance(e, dict) else str(e)
                                   for e in entity_list[:10]]
                    context_parts.append(f"- {entity_type}: {', '.join(entity_names)}")
            context_parts.append("")

        # 4. 田野原文摘录（最重要的部分，选择最相关的15-20段）
        citations = report_material.get("citation_pool", [])
        if citations:
            context_parts.append(f"### 田野原文摘录（共{len(citations)}段，以下为代表性内容）\n")
            for i, citation in enumerate(citations[:20], 1):
                content = citation.get("content", "")
                if content:
                    # 限制每段长度，保持上下文在合理范围
                    excerpt = content[:400] + ("..." if len(content) > 400 else "")
                    context_parts.append(f"**摘录 {i}:**\n{excerpt}\n")

        # 5. 时间线信息
        timeline = report_material.get("timeline", [])
        if timeline:
            context_parts.append(f"### 时间线\n")
            for event in timeline[:10]:
                date = event.get("date", "")
                event_desc = event.get("event", "")
                context_parts.append(f"- {date}: {event_desc}")
            context_parts.append("")

        # 6. 实体关系
        relations = report_material.get("entity_relations", [])
        if relations:
            context_parts.append(f"### 实体关系\n")
            for rel in relations[:15]:
                source = rel.get("source", "")
                target = rel.get("target", "")
                rel_type = rel.get("relation", "")
                context_parts.append(f"- {source} --[{rel_type}]--> {target}")
            context_parts.append("")

        return "\n".join(context_parts)

    def _generate_framework_intro(self) -> str:
        """生成方法论框架介绍（固定内容）"""
        intro = """# 田野调查报告：基于大地遗产内容运营方法论

## 方法论说明

本报告采用"大地遗产"内容运营方法论，将文化遗产资源从传统的保护管理视角，转向内容挖掘与产品转化视角。

**核心理念：** 从"资源管理"到"内容运营"

**三大挖掘方向：**
1. **大考古** - 让考古发现从学术殿堂走向大众生活
2. **泛艺术** - 挖掘建筑、民俗、手工艺的艺术性和美学价值
3. **新乡土** - 发现乡土文化的当代价值和生活美学

**三大转化模式：**
1. **旅游要素融合** - 将文化内容融入吃住行游购娱
2. **公共文化产品融合** - 与博物馆、图书馆、文化馆等结合
3. **内容IP打造** - 提炼文化符号，构建可持续运营的IP

以下报告基于田野调查的真实资料，运用上述方法论框架进行深度分析。

---

"""
        return intro

    def _analyze_field_resources_with_llm(self, data_context: str) -> str:
        """
        使用LLM分析田野资源概览
        """
        logger.info("正在用LLM分析田野资源概览...")

        analysis_prompt = """请基于提供的田野资料，完成以下任务：

1. **资源整体扫描**：概述田野调查收集到的文化遗产资源的整体特征，包括类型、分布、密度等
2. **核心资源识别**：从田野原文中识别出最具代表性和挖掘潜力的文化资源（至少5-8个）
3. **资源价值评估**：分析这些资源的历史价值、文化价值、美学价值和当代价值
4. **资源关联网络**：揭示不同文化资源之间的关联关系，构建资源网络图景

请用1200-1500字完成上述分析，务必引用具体的田野原文片段作为分析依据。"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="田野资源分析",
            framework_dimensions={"分析任务": analysis_prompt},
            data_context=data_context,
            analysis_focus="对田野资料进行资源概览分析",
            max_tokens=2500
        )

        return f"## 一、田野资源概览\n\n{llm_analysis}\n\n---\n\n"

    def _analyze_excavation_direction_with_llm(
        self,
        direction_name: str,
        direction_info: Dict[str, Any],
        data_context: str
    ) -> str:
        """
        使用LLM深度分析单个挖掘方向
        """
        logger.info(f"正在用LLM分析挖掘方向：{direction_name}...")

        # 构建分析提示
        analysis_dimensions = f"""
**{direction_name}的核心理念：** {direction_info['核心理念']}

**挖掘重点：**
{chr(10).join(f'- {point}' for point in direction_info['挖掘重点'])}

**请回答以下问题：**
{chr(10).join(f'{i+1}. {question}' for i, question in enumerate(direction_info['分析维度']))}

**分析要求：**
1. 从田野原文中提取具体的文化元素和案例
2. 运用{direction_name}的视角进行深度解读
3. 提出具体的内容挖掘方向和故事线索
4. 分析这些内容如何与当代审美和生活方式结合
5. 用1800-2200字完成分析，必须引用田野原文
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name=f"大地遗产方法论 - {direction_name}",
            framework_dimensions={direction_name: direction_info},
            data_context=data_context,
            analysis_focus=analysis_dimensions,
            max_tokens=3500
        )

        return f"## 二、内容挖掘：{direction_name}\n\n{llm_analysis}\n\n---\n\n"

    def _design_transformation_strategies_with_llm(self, data_context: str) -> str:
        """
        使用LLM设计内容转化策略
        """
        logger.info("正在用LLM设计内容转化策略...")

        # 构建转化框架说明
        framework_desc = []
        for mode_name, mode_info in self.transformation_framework.items():
            framework_desc.append(f"**{mode_name}：** {mode_info['核心理念']}")
            framework_desc.append(f"转化路径：{', '.join(mode_info['转化路径'][:4])}")

        analysis_prompt = f"""基于前面分析的文化内容，请设计具体的转化策略：

{chr(10).join(framework_desc)}

**设计任务：**
1. 为每种转化模式提出2-3个具体的产品/业态方案
2. 每个方案需要包括：
   - 文化元素来源（引用田野原文中的具体内容）
   - 产品/业态形态（详细描述）
   - 体验设计（用户如何参与和体验）
   - 商业模式（如何实现可持续运营）
3. 分析不同转化模式之间的协同效应
4. 提出内容运营的整体策略建议

请用1800-2200字完成上述设计，确保方案具有可操作性和创新性。"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="内容转化策略设计",
            framework_dimensions=self.transformation_framework,
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=3500
        )

        return f"## 三、内容转化策略\n\n{llm_analysis}\n\n---\n\n"


# 工具函数：供外部调用
def create_field_investigation_skill() -> FieldInvestigationSkill:
    """创建田野调查 Skill 实例"""
    return FieldInvestigationSkill()


def apply_field_investigation_skill(
    report_material: Dict[str, Any],
    chapter_title: str = None
) -> str:
    """
    应用田野调查 Skill 生成报告内容

    Args:
        report_material: 报告素材
        chapter_title: 章节标题（保留参数以兼容旧接口，但不再使用）

    Returns:
        报告内容
    """
    skill = create_field_investigation_skill()
    return skill.generate_report(report_material)
