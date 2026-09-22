"""
LLM报告生成服务

使用Claude或GPT-4生成万字级深度报告
"""
import os
import logging
from typing import List, Dict, Optional
import anthropic
import openai

logger = logging.getLogger(__name__)


class LLMReportGenerator:
    """LLM报告生成器"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')

        # 优先使用Claude
        if self.anthropic_key:
            self.client = anthropic.Anthropic(api_key=self.anthropic_key)
            self.provider = 'anthropic'
            logger.info("✅ 使用Claude API生成报告")
        elif self.openai_key:
            openai.api_key = self.openai_key
            self.provider = 'openai'
            logger.info("✅ 使用OpenAI API生成报告")
        else:
            self.client = None
            self.provider = None
            logger.warning("⚠️ 未配置LLM API Key，将使用模板生成")

    def is_available(self) -> bool:
        """检查LLM是否可用"""
        return self.provider is not None

    def generate_level1_report(self, documents: List, keywords: List[Dict]) -> str:
        """
        生成一度报告（10000+字）

        策略：完整材料呈现 + 关键词深度分析 + 主题挖掘
        """
        if not self.is_available():
            return None

        # 准备材料内容
        materials = []
        for i, doc in enumerate(documents, 1):
            if doc.text_content:
                materials.append(f"【材料{i}：{doc.filename}】\n{doc.text_content}")

        materials_text = "\n\n".join(materials)

        # 准备关键词
        keywords_text = "\n".join([
            f"{i+1}. {kw['keyword']} (权重:{kw.get('weight', 0):.2f})"
            for i, kw in enumerate(keywords[:30])
        ])

        # 构建Prompt
        prompt = f"""你是一位资深的田野调查研究者。请基于以下材料生成一份10000字以上的"一度报告"。

【材料内容】
{materials_text}

【提取的关键词（Top 30）】
{keywords_text}

【报告要求】
1. **字数要求**：10000字以上（必须达到）
2. **报告性质**：一度报告，基于材料的直接分析，不引入理论框架
3. **内容结构**：
   - 第一部分：材料来源与基本情况（1000字）
   - 第二部分：核心关键词深度分析（2000字，每个Top关键词100-200字分析）
   - 第三部分：田野材料完整呈现（3000字，完整展示所有材料）
   - 第四部分：材料结构与内容梳理（2000字，逐段分析）
   - 第五部分：主题深度挖掘（1500字，识别潜在主题）
   - 第六部分：研究发现总结（1000字）
   - 第七部分：研究局限与展望（500字）

【写作要求】
- 忠实呈现材料原貌，大量引用原文
- 每个关键词都要结合材料进行深度解读
- 识别材料中的细节、隐含意义和潜在关联
- 使用学术化但易读的语言
- 必须达到10000字

请开始生成报告："""

        try:
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=16000,  # 足够生成万字报告
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                report = response.content[0].text

            elif self.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,
                    temperature=0.7
                )
                report = response.choices[0].message.content

            logger.info(f"✅ LLM生成一度报告完成，长度：{len(report)}字符")
            return report

        except Exception as e:
            logger.error(f"❌ LLM生成报告失败: {e}")
            return None

    def generate_level2_report(self, documents: List, skill_results: Dict) -> str:
        """
        生成二度报告（10000+字）

        策略：费孝通框架深度解读 + 材料对话 + 理论启示
        """
        if not self.is_available():
            return None

        # 准备材料
        materials = []
        for i, doc in enumerate(documents, 1):
            if doc.text_content:
                materials.append(f"【材料{i}：{doc.filename}】\n{doc.text_content}")

        materials_text = "\n\n".join(materials)

        # 准备Skill分析结果
        skill_text = ""
        for skill_name, skill_data in skill_results.items():
            skill_text += f"\n【{skill_name}分析结果】\n"
            for dim_name, dim_data in skill_data.get('dimensions', {}).items():
                contexts = dim_data.get('contexts', [])
                if contexts:
                    skill_text += f"\n维度：{dim_name}\n"
                    skill_text += f"匹配数量：{len(contexts)}\n"
                    for ctx in contexts[:3]:
                        skill_text += f"- {ctx}\n"

        prompt = f"""你是一位精通费孝通《乡土中国》理论的社会学研究者。请基于以下材料生成一份10000字以上的"二度报告"。

【材料内容】
{materials_text}

【Skill框架分析结果】
{skill_text}

【理论框架】
费孝通《乡土中国》的核心概念：
1. 差序格局：以自我为中心的同心圆关系网络
2. 礼治秩序：基于传统习俗的社会控制
3. 熟人社会：建立在长期互动上的信任机制
4. 现代化冲击：传统社会的转型与变迁

【报告要求】
1. **字数要求**：10000字以上（必须达到）
2. **报告性质**：二度报告，运用费孝通理论框架深度解读材料
3. **内容结构**：
   - 理论框架说明（1000字）
   - 差序格局分析（2500字，理论阐释+材料证据+深度对话）
   - 礼治秩序分析（2500字）
   - 熟人社会分析（2500字）
   - 现代化冲击分析（2500字）
   - 综合讨论：延续与变迁（1500字）
   - 理论启示与研究建议（1000字）

【写作要求】
- 每个维度都要：理论阐释（500字）+ 材料证据（1000字）+ 理论对话（1000字）
- 大量引用费孝通原著的论述
- 将材料与理论深度对话，而非简单套用
- 揭示传统社会结构在当代的延续与变迁
- 必须达到10000字

请开始生成报告："""

        try:
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=16000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                report = response.content[0].text

            elif self.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,
                    temperature=0.7
                )
                report = response.choices[0].message.content

            logger.info(f"✅ LLM生成二度报告完成，长度：{len(report)}字符")
            return report

        except Exception as e:
            logger.error(f"❌ LLM生成报告失败: {e}")
            return None

    def generate_level3_report(self, documents: List, keywords: List[Dict], skill_results: Dict) -> str:
        """
        生成三度报告（10000+字）

        策略：SOP框架 + 费孝通理论 + 关键词趋势 + 行动建议
        """
        if not self.is_available():
            return None

        # 准备材料
        materials = []
        for i, doc in enumerate(documents, 1):
            if doc.text_content:
                materials.append(f"【材料{i}：{doc.filename}】\n{doc.text_content[:500]}...")  # 摘要即可

        materials_text = "\n\n".join(materials)

        # 准备关键词
        keywords_text = "\n".join([
            f"{i+1}. {kw['keyword']} (权重:{kw.get('weight', 0):.2f})"
            for i, kw in enumerate(keywords[:20])
        ])

        # 准备Skill结果摘要
        skill_summary = ""
        for skill_name, skill_data in skill_results.items():
            skill_summary += f"\n{skill_name}:\n"
            for dim_name, dim_data in skill_data.get('dimensions', {}).items():
                matched = dim_data.get('matched_count', 0)
                skill_summary += f"  - {dim_name}: {matched}处匹配\n"

        prompt = f"""你是一位兼具理论素养与实践经验的乡村发展顾问。请基于以下材料生成一份10000字以上的"三度报告"。

【材料摘要】
{materials_text}

【核心关键词】
{keywords_text}

【框架分析结果】
{skill_summary}

【报告要求】
1. **字数要求**：10000字以上（必须达到）
2. **报告性质**：三度报告，整合多维度分析，提供综合评估与行动建议
3. **内容结构**：
   - 执行摘要（800字）
   - 第一章：乡村运营SOP六维度评估（2500字）
     * 社区基础调研、文化资产、利益相关方、业态可行性、风险、行动路径
   - 第二章：社会结构分析（费孝通视角）（2000字）
   - 第三章：核心议题识别与趋势分析（2000字）
   - 第四章：SWOT分析（1500字）
     * 优势、劣势、机会、威胁
   - 第五章：综合评估与战略建议（2000字）
     * 短期行动计划（0-6个月）
     * 中期发展路径（6-18个月）
     * 长期愿景规划（18个月以上）
   - 第六章：风险预警与应对策略（700字）
   - 附录：关键指标与监测框架（500字）

【写作要求】
- 整合一度报告的材料分析和二度报告的理论洞察
- 提供可操作、可落地的具体建议
- 每个建议都要有材料依据和理论支撑
- 识别潜在风险并给出应对方案
- 必须达到10000字

请开始生成报告："""

        try:
            if self.provider == 'anthropic':
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=16000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                report = response.content[0].text

            elif self.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=16000,
                    temperature=0.7
                )
                report = response.choices[0].message.content

            logger.info(f"✅ LLM生成三度报告完成，长度：{len(report)}字符")
            return report

        except Exception as e:
            logger.error(f"❌ LLM生成报告失败: {e}")
            return None


# 全局实例
llm_report_generator = LLMReportGenerator()
