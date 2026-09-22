"""
乡土中国田野调查与发展指导 Skill

基于费孝通《乡土中国》的认知框架，深入理解乡村社会的内在逻辑
核心理念：
- 乡土本色：离不了泥土的生产与生活方式
- 差序格局：以己为中心的人际关系网络
- 礼治秩序：依赖教化与道德约束的社会秩序
- 家族血缘：血缘与地缘深度交融的社区形态
"""

import logging
from typing import Dict, List, Any
from dataclasses import dataclass

from .llm_analysis_helper import LLMAnalysisHelper

logger = logging.getLogger(__name__)


@dataclass
class XiangtuDimension:
    """乡土社会维度分析结果"""
    dimension: str  # 社会结构/文化传统/物质遗产/经济生活
    key_findings: List[str]  # 核心发现
    xiangtu_logic: str  # 乡土逻辑解读
    development_potential: str  # 发展潜力


@dataclass
class XiangtuOpportunity:
    """基于乡土资源的商业机会"""
    resource_type: str  # 熟人网络/礼治秩序/血缘认同等
    transformation_path: str  # 转化路径
    practical_approach: str  # 实践路径
    risk_mitigation: str  # 风险防范


class XiangtuChinaSkill:
    """
    乡土中国田野调查与发展指导 Skill

    核心思路：
    1. 定义费孝通理论框架的核心维度
    2. 从田野数据中提取相关证据
    3. 调用LLM用理论框架深度分析数据
    4. 生成有洞察力的万字报告
    """
    def __init__(self, use_workflow_engine: bool = True):

        # 费孝通理论框架
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.theoretical_lens = {
            "乡土本色": {
                "核心概念": "从基层上看去，中国社会是乡土性的",
                "关键特征": ["离不了泥土", "不流动性", "熟人社会"],
                "实践提问": ["土地关系如何", "人口流动性如何", "熟人还是陌生人"]
            },
            "差序格局": {
                "核心概念": "以己为中心如石子投水的波纹向外推展",
                "关键特征": ["亲疏远近", "弹性边界", "私人道德"],
                "实践提问": ["权力结构如何", "谁有影响力", "人际网络如何影响决策"]
            },
            "礼治秩序": {
                "核心概念": "依赖礼治而非法治，重教化靠道德约束",
                "关键特征": ["无讼传统", "长老权威", "乡规民约"],
                "实践提问": ["纠纷如何解决", "村规民约内容", "长老角色"]
            },
            "家族血缘": {
                "核心概念": "家族是基本单位，血缘维系社会网络",
                "关键特征": ["宗族结构", "聚族而居", "安土重迁"],
                "实践提问": ["宗族结构如何", "家族作用", "姓氏构成"]
            },
            "长老统治": {
                "核心概念": "年长者在文化传承和秩序维护中拥有权威",
                "关键特征": ["经验权威", "文化传承", "代际关系"],
                "实践提问": ["长老在村务中的角色", "年轻人与老年人关系"]
            }
        }

        # 初始化LLM辅助类
        self.llm_helper = LLMAnalysisHelper()

    def generate_report(self, report_material: Dict[str, Any]) -> str:
        """
        生成乡土中国视角的田野调查报告

        核心流程：
        1. 提取田野数据上下文
        2. 对每个理论维度进行LLM深度分析
        3. 组装成完整报告
        """
        logger.info("开始生成乡土中国分析报告")

        # 提取田野数据
        data_context = self._extract_data_context(report_material)

        # 生成报告
        content = "# 乡土中国视角：田野调查深度分析报告\n\n"

        # 第一部分：理论框架介绍
        content += self._generate_framework_intro()

        # 第二部分：按五个维度进行LLM深度分析
        for dimension_name, dimension_info in self.theoretical_lens.items():
            logger.info(f"正在分析维度：{dimension_name}")
            content += self._analyze_dimension_with_llm(
                dimension_name,
                dimension_info,
                data_context
            )

        # 第三部分：综合诊断与发展建议
        content += self._generate_synthesis_with_llm(data_context)

        logger.info(f"✅ 报告生成完成，共{len(content)}字")
        return content

    def _extract_data_context(self, report_material: Dict[str, Any]) -> str:
        """
        从report_material中提取田野数据上下文

        将关键词、实体、引文、时间线组织成LLM可读的格式
        """
        lines = []

        # 1. 关键词
        main_keywords = report_material.get('main_keywords', [])
        if main_keywords:
            lines.append("### 主要关键词")
            for kw in main_keywords[:20]:
                kw_text = kw.get('keyword', '') if isinstance(kw, dict) else str(kw)
                lines.append(f"- {kw_text}")
            lines.append("")

        # 2. 核心实体
        core_entities = report_material.get('core_entities', {})
        if core_entities:
            lines.append("### 核心实体")
            if isinstance(core_entities, dict):
                for entity_type, entity_list in core_entities.items():
                    entities_text = []
                    for entity_obj in entity_list[:10]:
                        entity = entity_obj.get('entity', '') if isinstance(entity_obj, dict) else str(entity_obj)
                        entities_text.append(entity)
                    if entities_text:
                        lines.append(f"- **{entity_type}**: {', '.join(entities_text)}")
            lines.append("")

        # 3. 引文池（最重要的原始材料）
        citation_pool = report_material.get('citation_pool', [])
        if citation_pool:
            lines.append("### 田野原文摘录（前30条）")
            for i, citation in enumerate(citation_pool[:30], 1):
                text = citation.get('content', '') or citation.get('text', '')
                source = citation.get('source_document', '未知来源')
                if text:
                    lines.append(f"{i}. 【{source}】{text[:200]}")
            lines.append("")

        # 4. 时间线
        timeline = report_material.get('timeline', [])
        if timeline:
            lines.append("### 时间线")
            for event in timeline[:10]:
                event_text = event.get('event', '') if isinstance(event, dict) else str(event)
                lines.append(f"- {event_text}")
            lines.append("")

        return "\n".join(lines)

    def _generate_framework_intro(self) -> str:
        """生成理论框架介绍"""
        return """
## 一、理论框架：费孝通《乡土中国》

费孝通先生的《乡土中国》是理解中国传统社会结构的经典著作。本报告将运用其五个核心理论维度，对田野调查材料进行深度解读：

1. **乡土本色**：中国社会的乡土性基础
2. **差序格局**：以己为中心的同心圆关系结构
3. **礼治秩序**：基于传统习俗的社会控制机制
4. **家族血缘**：血缘维系的社会网络
5. **长老统治**：年长者的经验权威

---

## 二、田野数据的理论解读

"""

    def _analyze_dimension_with_llm(
        self,
        dimension_name: str,
        dimension_info: Dict[str, Any],
        data_context: str
    ) -> str:
        """
        使用LLM对单个维度进行深度分析
        """
        analysis_focus = f"""
请从「{dimension_name}」的视角深度分析这个村落的田野数据。

理论框架：
- 核心概念：{dimension_info['核心概念']}
- 关键特征：{', '.join(dimension_info['关键特征'])}
- 实践提问：{', '.join(dimension_info['实践提问'])}

分析要求：
1. 仔细阅读田野原文摘录，找出与「{dimension_name}」相关的具体证据
2. 用费孝通的理论框架解读这些证据
3. 揭示背后的社会逻辑和文化机制
4. 评估这一维度在当代的延续、变迁或消失
5. 输出应为学术性但接地气的深度分析，1000-1500字

输出格式：
### {dimension_name}

#### 1. 田野证据
（从原文中提取的具体例证）

#### 2. 理论解读
（用费孝通理论分析这些证据）

#### 3. 当代变迁
（这一维度在现代化进程中的变化）

#### 4. 发展意涵
（对乡村发展的启示）
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="费孝通《乡土中国》",
            framework_dimensions={dimension_name: dimension_info},
            data_context=data_context,
            analysis_focus=analysis_focus,
            max_tokens=2000
        )

        return llm_analysis + "\n\n---\n\n"

    def _generate_synthesis_with_llm(self, data_context: str) -> str:
        """
        使用LLM生成综合诊断与发展建议
        """
        synthesis_prompt = """
基于前面五个维度的分析，请进行综合诊断：

1. **乡土社会健康度诊断**：这个村落的传统社会结构保存如何？哪些在延续，哪些在瓦解？
2. **现代化冲击评估**：外出务工、城市化、市场经济对传统结构的影响
3. **发展路径建议**：基于乡土社会特征，什么样的发展路径更适合这个村落？
4. **风险提示**：哪些传统资源容易被破坏？如何避免？

要求：
- 基于前面的田野数据和理论分析
- 提出有洞察力的诊断
- 给出可操作的建议
- 1500-2000字
"""

        synthesis = self.llm_helper.analyze_with_framework(
            framework_name="费孝通《乡土中国》",
            framework_dimensions=self.theoretical_lens,
            data_context=data_context,
            analysis_focus=synthesis_prompt,
            max_tokens=2500
        )

        return f"""
## 三、综合诊断与发展建议

{synthesis}

---

## 报告说明

本报告基于费孝通《乡土中国》的理论框架，对田野调查数据进行了深度解读。所有分析结论均基于实际调查材料，力求理论与实证相结合，为乡村发展提供社会学视角的洞察。
"""
