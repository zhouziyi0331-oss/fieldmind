"""
商业分析报告生成 Skill
基于「乡遗商途」商业可行性验证框架

核心理念：
- 从文化资源到商业机会的系统化验证
- 七章结构：田野扫描 → 价值判断 → 机会识别 → 概念方案 → 可行性验证 → 风险对策 → 行动路径

改造说明：
- Skill只定义「乡遗商途」方法论框架
- 实际商业分析由LLM深度分析田野数据生成
- 无硬编码模板，分析完全数据驱动
"""

from typing import Dict, Any
import logging

from .llm_analysis_helper import LLMAnalysisHelper

logger = logging.getLogger(__name__)


class BusinessSOPSkill:
    """
    商业分析报告生成 Skill

    基于「乡遗商途」框架，进行乡村文化遗产商业可行性验证
    使用LLM深度分析真实田野数据，而非模板化生成
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """初始化Skill：定义方法论框架"""

        # 「乡遗商途」七章验证框架
        self.sop_framework = {
            "第一章_田野扫描": {
                "核心任务": "梳理资源本底与在地语境",
                "分析维度": [
                    "物质遗存盘点（建筑、遗址、器物等）",
                    "非物质遗存盘点（技艺、民俗、仪式等）",
                    "自然与人文环境（地理位置、交通可达性、社区结构）",
                    "历史文化脉络（时间深度、文化厚度）"
                ],
                "输出要求": "系统性的资源清单和语境描述"
            },
            "第二章_价值判断": {
                "核心任务": "评估文化遗产的商业转化潜力",
                "评估维度": {
                    "故事性": "是否有动人的历史叙事和文化内涵",
                    "体验性": "是否可以转化为可参与、可感知的体验",
                    "稀缺性": "在区域/全国是否具有独特性和不可替代性",
                    "延展性": "是否可以延伸出系列化产品和IP"
                },
                "判断标准": "高/中/低商业化适宜性"
            },
            "第三章_机会识别": {
                "核心任务": "从文化资源转化为商业机会",
                "九大机会类别": {
                    "文化空间运营": "老建筑改造为复合型文化空间（古宅书店、祠堂咖啡馆等）",
                    "深度研学产品": "依托在地文化遗产开发研学课程",
                    "在地风物开发": "将地方物产与文化IP结合",
                    "节庆活动策划": "重构或活化传统节庆",
                    "数字内容生产": "文化遗产的数字化表达（纪录片、短视频等）",
                    "场景化餐饮": "文化与餐饮的深度融合（家宴体验、田野餐桌等）",
                    "主题民宿集群": "以文化主题统领住宿业态",
                    "文创产品体系": "超越冰箱贴的文化消费级产品",
                    "社群与会员运营": "构建文化遗产爱好者社群"
                },
                "机会评估": "文化价值彰显度 × 商业变现可行性",
                "优先级矩阵": {
                    "旗舰型项目": "高文化价值 × 高商业可行性（优先推进）",
                    "品牌型项目": "高文化价值 × 低商业可行性（长期价值）",
                    "现金牛型项目": "低文化价值 × 高商业可行性（快速见效）",
                    "基础配套型": "低文化价值 × 低商业可行性（按需配置）"
                }
            },
            "第四章_概念方案": {
                "核心任务": "从机会到产品原型",
                "设计要素": [
                    "产品/业态名称与定位",
                    "价值主张（为什么用户会选择）",
                    "体验流程设计（用户旅程地图）",
                    "文化解码方式（如何让文化可感知）",
                    "收入模式设计",
                    "MVP（最小可行产品）方案"
                ]
            },
            "第五章_可行性验证": {
                "核心任务": "财务、市场、运营三重验证",
                "验证维度": {
                    "财务验证": "投资额、收入预测（三种情境）、成本结构、ROI、回本周期",
                    "市场验证": "目标客群、市场规模、竞品分析、需求验证",
                    "运营验证": "人才需求、运营模式、供应链、标准化流程"
                }
            },
            "第六章_风险对策": {
                "核心任务": "识别风险并制定应对策略",
                "六大风险类别": {
                    "政策风险": "文保政策、土地政策、审批流程",
                    "市场风险": "需求不足、竞品增多、消费趋势变化",
                    "运营风险": "人才招聘、服务质量、安全事故",
                    "文化风险": "过度商业化、文化失真、社区冲突",
                    "资金风险": "投资回收慢、后续资金不足",
                    "自然风险": "极端天气、地质灾害、生态变化"
                },
                "风险等级": "高/中/低",
                "应对策略": "针对性的缓解措施"
            },
            "第七章_行动路径": {
                "核心任务": "制定分阶段行动计划",
                "时间维度": {
                    "短期（1个月内）": "田野补充调研、MVP测试、利益相关方建立联系",
                    "中期（1-6个月）": "确定合作模式、核心产品详细设计、首期建设",
                    "长期（6个月以上）": "品牌体系建立、社群运营、规模化复制"
                }
            }
        }

        # 初始化LLM分析助手
        self.llm_helper = LLMAnalysisHelper()

    def generate_report(self, report_material: Dict[str, Any]) -> str:
        """
        生成完整的商业分析报告

        Args:
            report_material: 报告素材（包含citation_pool, keywords, entities等）

        Returns:
            完整的报告内容（目标：5,000字，与commercial_feasibility_skill合并后达到10,000字）
        """
        logger.info("开始生成商业分析报告（基于乡遗商途方法论）")

        # 提取数据上下文
        data_context = self._extract_data_context(report_material)

        # 报告结构
        report_content = ""

        # 1. 方法论框架介绍（~400字）
        report_content += self._generate_framework_intro()

        # 2. 第一章：田野扫描（LLM分析，~800字）
        report_content += self._analyze_field_scan_with_llm(data_context)

        # 3. 第二章：价值判断（LLM分析，~800字）
        report_content += self._analyze_value_assessment_with_llm(data_context)

        # 4. 第三章：机会识别（LLM分析，~1200字）
        report_content += self._analyze_opportunity_identification_with_llm(data_context)

        # 5. 第四章：概念方案（LLM分析，~1000字）
        report_content += self._design_product_concepts_with_llm(data_context)

        # 6. 第五章：可行性验证（LLM分析，~600字）
        report_content += self._validate_feasibility_with_llm(data_context)

        # 7. 第六章：风险对策（LLM分析，~600字）
        report_content += self._analyze_risks_with_llm(data_context)

        # 8. 第七章：行动路径（LLM分析，~600字）
        report_content += self._generate_action_plan_with_llm(data_context)

        logger.info(f"商业分析报告生成完成，总字数：{len(report_content)}")

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

        # 4. 田野原文摘录（最重要的部分）
        citations = report_material.get("citation_pool", [])
        if citations:
            context_parts.append(f"### 田野原文摘录（共{len(citations)}段，以下为代表性内容）\n")
            for i, citation in enumerate(citations[:20], 1):
                content = citation.get("content", "")
                if content:
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

        # 6. 关键词社区
        communities = report_material.get("keyword_communities", [])
        if communities:
            context_parts.append(f"### 主题社区\n")
            for i, comm in enumerate(communities[:5], 1):
                keywords_in_comm = comm.get("keywords", [])[:8]
                kw_list = [kw.get("keyword", kw) if isinstance(kw, dict) else str(kw)
                          for kw in keywords_in_comm]
                context_parts.append(f"社区 {i}: {', '.join(kw_list)}")
            context_parts.append("")

        return "\n".join(context_parts)

    def _generate_framework_intro(self) -> str:
        """生成方法论框架介绍（固定内容）"""
        intro = """# 商业分析报告：基于「乡遗商途」方法论

## 方法论说明

本报告采用「乡遗商途」商业可行性验证框架，系统性地将乡村文化遗产资源转化为可持续运营的商业机会。

**核心理念：** 从资源盘点到商业落地的全链条验证

**七章验证流程：**
1. **田野扫描** - 梳理资源本底与在地语境
2. **价值判断** - 评估文化遗产的商业转化潜力（故事性、体验性、稀缺性、延展性）
3. **机会识别** - 匹配九大商业机会类别，构建优先级矩阵
4. **概念方案** - 从机会到产品原型，设计MVP
5. **可行性验证** - 财务、市场、运营三重验证
6. **风险对策** - 识别六大风险类别并制定应对策略
7. **行动路径** - 分阶段行动计划（短期/中期/长期）

以下报告基于田野调查的真实资料，运用上述框架进行深度商业可行性分析。

---

"""
        return intro

    def _analyze_field_scan_with_llm(self, data_context: str) -> str:
        """第一章：田野扫描"""
        logger.info("正在用LLM分析田野扫描...")

        chapter_info = self.sop_framework["第一章_田野扫描"]

        analysis_prompt = f"""请完成「乡遗商途」第一章：田野扫描

**核心任务：** {chapter_info['核心任务']}

**分析维度：**
{chr(10).join(f'- {dim}' for dim in chapter_info['分析维度'])}

**分析要求：**
1. 从田野原文中系统性地盘点物质和非物质文化遗产
2. 分析在地的自然环境、交通可达性、社区结构
3. 梳理历史文化脉络，判断文化厚度
4. 形成清晰的资源清单
5. 用800-1000字完成分析，必须引用具体的田野原文

**输出格式：**
- 物质遗存盘点（引用原文）
- 非物质遗存盘点（引用原文）
- 在地语境分析
- 文化脉络梳理
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="乡遗商途 - 田野扫描",
            framework_dimensions={"第一章": chapter_info},
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=1500
        )

        return f"## 第一章：田野扫描 - 资源本底与在地语境\n\n{llm_analysis}\n\n---\n\n"

    def _analyze_value_assessment_with_llm(self, data_context: str) -> str:
        """第二章：价值判断"""
        logger.info("正在用LLM分析价值判断...")

        chapter_info = self.sop_framework["第二章_价值判断"]

        analysis_prompt = f"""请完成「乡遗商途」第二章：价值判断

**核心任务：** {chapter_info['核心任务']}

**评估维度：**
{chr(10).join(f'- **{k}**: {v}' for k, v in chapter_info['评估维度'].items())}

**分析要求：**
1. 从田野资料中识别出5-8个最具潜力的文化资源
2. 对每个资源进行四维度评估（故事性、体验性、稀缺性、延展性）
3. 给出商业化适宜性判断（高/中/低）
4. 必须引用田野原文作为评估依据
5. 用800-1000字完成分析

**输出格式：**
- 高商业化适宜性资源（列举3-5个，每个详细分析四维度）
- 中商业化适宜性资源（列举2-3个，指出提升路径）
- 整体潜力评估
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="乡遗商途 - 价值判断",
            framework_dimensions={"第二章": chapter_info},
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=1500
        )

        return f"## 第二章：价值判断 - 商业转化潜力评估\n\n{llm_analysis}\n\n---\n\n"

    def _analyze_opportunity_identification_with_llm(self, data_context: str) -> str:
        """第三章：机会识别"""
        logger.info("正在用LLM分析机会识别...")

        chapter_info = self.sop_framework["第三章_机会识别"]

        analysis_prompt = f"""请完成「乡遗商途」第三章：机会识别

**核心任务：** {chapter_info['核心任务']}

**九大机会类别：**
{chr(10).join(f'- **{k}**: {v}' for k, v in chapter_info['九大机会类别'].items())}

**优先级矩阵：**
{chr(10).join(f'- **{k}**: {v}' for k, v in chapter_info['优先级矩阵'].items())}

**分析要求：**
1. 为前面识别的高潜力文化资源匹配合适的商业机会类别
2. 每个资源可匹配1-2个机会类别
3. 对每个商业机会进行评估：文化价值彰显度 × 商业变现可行性
4. 按优先级矩阵分类（旗舰型/品牌型/现金牛型）
5. 重点阐述2-3个旗舰型项目
6. 用1200-1500字完成分析

**输出格式：**
- 旗舰型项目（优先推进）：详细描述2-3个
- 现金牛型项目（快速见效）：列举1-2个
- 品牌型项目（长期价值）：列举1-2个
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="乡遗商途 - 机会识别",
            framework_dimensions={"第三章": chapter_info},
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=2500
        )

        return f"## 第三章：机会识别 - 从文化资源到商业机会\n\n{llm_analysis}\n\n---\n\n"

    def _design_product_concepts_with_llm(self, data_context: str) -> str:
        """第四章：概念方案"""
        logger.info("正在用LLM设计产品概念...")

        chapter_info = self.sop_framework["第四章_概念方案"]

        analysis_prompt = f"""请完成「乡遗商途」第四章：概念方案

**核心任务：** {chapter_info['核心任务']}

**设计要素：**
{chr(10).join(f'- {elem}' for elem in chapter_info['设计要素'])}

**分析要求：**
1. 选择前面识别的1-2个旗舰型项目进行详细产品设计
2. 每个产品包含：名称、价值主张、体验流程、文化解码、收入模式、MVP方案
3. 体验流程要具体（5-7个步骤）
4. 文化解码要说明如何让文化可感知
5. MVP方案要具有可操作性
6. 用1000-1200字完成设计

**输出格式：**
- 产品1：[名称]
  - 价值主张
  - 体验流程（详细步骤）
  - 文化解码方式
  - 收入模式
  - MVP设计
- 产品2：[名称]（同样结构）
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="乡遗商途 - 概念方案",
            framework_dimensions={"第四章": chapter_info},
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=2000
        )

        return f"## 第四章：概念方案 - 从机会到产品原型\n\n{llm_analysis}\n\n---\n\n"

    def _validate_feasibility_with_llm(self, data_context: str) -> str:
        """第五章：可行性验证"""
        logger.info("正在用LLM验证可行性...")

        chapter_info = self.sop_framework["第五章_可行性验证"]

        analysis_prompt = f"""请完成「乡遗商途」第五章：可行性验证

**核心任务：** {chapter_info['核心任务']}

**验证维度：**
{chr(10).join(f'- **{k}**: {v}' for k, v in chapter_info['验证维度'].items())}

**分析要求：**
1. 对前面设计的1-2个核心产品进行三重验证
2. 财务验证：估算投资额、收入预测（乐观/中性/保守）、ROI、回本周期
3. 市场验证：目标客群、市场规模、竞品分析
4. 运营验证：人才需求、运营模式、标准化流程
5. 给出整体可行性结论
6. 用600-800字完成验证

**输出格式：**
- 产品1可行性验证
  - 财务验证
  - 市场验证
  - 运营验证
- 整体可行性结论
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="乡遗商途 - 可行性验证",
            framework_dimensions={"第五章": chapter_info},
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=1200
        )

        return f"## 第五章：可行性验证 - 财务、市场、运营三重验证\n\n{llm_analysis}\n\n---\n\n"

    def _analyze_risks_with_llm(self, data_context: str) -> str:
        """第六章：风险对策"""
        logger.info("正在用LLM分析风险...")

        chapter_info = self.sop_framework["第六章_风险对策"]

        analysis_prompt = f"""请完成「乡遗商途」第六章：风险对策

**核心任务：** {chapter_info['核心任务']}

**六大风险类别：**
{chr(10).join(f'- **{k}**: {v}' for k, v in chapter_info['六大风险类别'].items())}

**分析要求：**
1. 基于田野资料和产品设计，识别各类别的具体风险
2. 评估每类风险的等级（高/中/低）和影响
3. 提出针对性的应对策略
4. 用600-800字完成分析

**输出格式：**
- 高风险类别（详细分析）
- 中风险类别（列举并给出应对策略）
- 低风险类别（简要说明）
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="乡遗商途 - 风险对策",
            framework_dimensions={"第六章": chapter_info},
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=1200
        )

        return f"## 第六章：风险对策 - 识别风险与应对策略\n\n{llm_analysis}\n\n---\n\n"

    def _generate_action_plan_with_llm(self, data_context: str) -> str:
        """第七章：行动路径"""
        logger.info("正在用LLM生成行动路径...")

        chapter_info = self.sop_framework["第七章_行动路径"]

        analysis_prompt = f"""请完成「乡遗商途」第七章：行动路径

**核心任务：** {chapter_info['核心任务']}

**时间维度：**
{chr(10).join(f'- **{k}**: {v}' for k, v in chapter_info['时间维度'].items())}

**分析要求：**
1. 基于前面的分析，制定分阶段行动计划
2. 短期行动（1个月内）：3-5个具体行动
3. 中期行动（1-6个月）：3-4个核心任务
4. 长期行动（6个月以上）：2-3个战略目标
5. 行动要具体可执行
6. 用600-800字完成规划

**输出格式：**
- 短期行动（1个月内）
- 中期行动（1-6个月）
- 长期行动（6个月以上）
"""

        llm_analysis = self.llm_helper.analyze_with_framework(
            framework_name="乡遗商途 - 行动路径",
            framework_dimensions={"第七章": chapter_info},
            data_context=data_context,
            analysis_focus=analysis_prompt,
            max_tokens=1200
        )

        return f"## 第七章：行动路径 - 分阶段行动计划\n\n{llm_analysis}\n\n---\n\n"


# 工具函数：供外部调用
def create_business_sop_skill() -> BusinessSOPSkill:
    """创建商业分析 Skill 实例"""
    return BusinessSOPSkill()


def apply_business_sop_skill(
    report_material: Dict[str, Any],
    chapter_title: str = None
) -> str:
    """
    应用商业分析 Skill 生成报告内容

    Args:
        report_material: 报告素材
        chapter_title: 章节标题（保留参数以兼容旧接口，但不再使用）

    Returns:
        报告内容
    """
    skill = create_business_sop_skill()
    return skill.generate_report(report_material)
