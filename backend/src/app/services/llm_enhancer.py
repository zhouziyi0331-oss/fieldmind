"""
LLM增强提取服务

使用LLM提升知识点和技能提取的质量
可选启用，提供更准确的语义理解和结构化提取
"""
from typing import Dict, Any, List, Optional
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMEnhancer:
    """
    LLM增强器

    功能：
    1. 增强知识点提取质量
    2. 增强技能RIA++结构生成
    3. 改进证据提取和验证
    4. 生成更好的压力测试
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = model
        self.enabled = api_key is not None

    def enhance_knowledge_extraction(
        self,
        raw_text: str,
        initial_candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        使用LLM增强知识点提取

        参数:
            raw_text: 原始文本
            initial_candidates: 初始提取的候选知识点

        返回:
            增强后的知识点列表
        """
        if not self.enabled:
            logger.warning("LLM增强未启用，返回原始候选")
            return initial_candidates

        enhanced = []

        for candidate in initial_candidates:
            try:
                # 使用LLM增强单个知识点
                enhanced_item = self._enhance_single_knowledge(candidate, raw_text)
                enhanced.append(enhanced_item)
            except Exception as e:
                logger.error(f"LLM增强知识点失败: {str(e)}")
                enhanced.append(candidate)  # 失败时使用原始候选

        return enhanced

    def _enhance_single_knowledge(
        self,
        candidate: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """使用LLM增强单个知识点"""
        prompt = f"""你是一个知识点提取专家。请分析以下候选知识点，并按照SBPACK 2.0标准完善它。

原始文本上下文：
{context[:1000]}

候选知识点：
类型: {candidate.get('knowledge_type', '')}
标题: {candidate.get('title', '')}
内容: {candidate.get('raw_content', '')}

请提供以下字段的完善内容（JSON格式）：
1. statement - 清晰的陈述
2. explanation - 详细解释
3. whyMatters - 为什么重要
4. scope - 适用范围
5. conditions - 前置条件（如果有）
6. boundaries - 边界限制
7. counterexamples - 反例（如果有）

只返回JSON，不要其他内容。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的知识工程师，擅长结构化知识提取。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        enhanced_data = json.loads(response.choices[0].message.content)

        # 合并增强数据
        candidate.update(enhanced_data)

        return candidate

    def enhance_skill_extraction(
        self,
        raw_text: str,
        initial_candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        使用LLM增强技能提取

        参数:
            raw_text: 原始文本
            initial_candidates: 初始提取的候选技能

        返回:
            增强后的技能列表
        """
        if not self.enabled:
            return initial_candidates

        enhanced = []

        for candidate in initial_candidates:
            try:
                enhanced_item = self._enhance_single_skill(candidate, raw_text)
                enhanced.append(enhanced_item)
            except Exception as e:
                logger.error(f"LLM增强技能失败: {str(e)}")
                enhanced.append(candidate)

        return enhanced

    def _enhance_single_skill(
        self,
        candidate: Dict[str, Any],
        context: str
    ) -> Dict[str, Any]:
        """使用LLM增强单个技能"""
        prompt = f"""你是一个技能提取专家，熟悉仓颉v2.0.0方法论。请分析以下候选技能，并按照RIA++结构完善它。

原始文本上下文：
{context[:1000]}

候选技能：
类型: {candidate.get('type', '')}
标题: {candidate.get('title', '')}
内容: {candidate.get('raw_content', '')}

请提供RIA++结构的完整内容（JSON格式）：
1. rationale - 为什么需要这个技能
2. interpretation - 核心逻辑和机制
3. applicationOriginal - 原始应用场景
4. applicationFuture - 未来可扩展应用
5. execution - 具体执行步骤（数组）
6. boundaries - 不适用的场景和边界

只返回JSON，不要其他内容。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个专业的技能工程师，擅长可执行技能的结构化提取。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        enhanced_data = json.loads(response.choices[0].message.content)

        # 合并增强数据
        candidate.update(enhanced_data)

        return candidate

    def generate_pressure_tests(
        self,
        skill: Dict[str, Any],
        sibling_skills: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """
        使用LLM生成高质量压力测试

        参数:
            skill: 技能数据
            sibling_skills: 兄弟技能列表

        返回:
            压力测试集
        """
        if not self.enabled:
            return {
                "should_trigger": [],
                "should_not_trigger": [],
                "boundary_cases": []
            }

        # 构建兄弟技能描述
        siblings_desc = "\n".join([
            f"- {s.get('title', '')}: {s.get('description', '')[:100]}"
            for s in sibling_skills[:3]
        ])

        prompt = f"""你是一个技能测试专家。请为以下技能生成压力测试用例。

技能信息：
名称: {skill.get('title', '')}
描述: {skill.get('raw_content', '')[:500]}

相似技能（容易混淆）：
{siblings_desc}

请生成3类测试用例（JSON格式）：
1. should_trigger - 应该触发此技能的场景（3-5个具体场景）
2. should_not_trigger - 不应该触发此技能的场景（3-5个具体场景）
3. boundary_cases - 边界模糊的场景（2-3个，包括与相似技能的区分）

每个测试用例应该：
- 具体明确
- 可实际验证
- 包含足够的上下文信息

只返回JSON，不要其他内容。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个测试工程师，擅长设计全面的测试用例。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )

        tests = json.loads(response.choices[0].message.content)

        return tests

    def verify_evidence(
        self,
        statement: str,
        evidence_text: str
    ) -> Dict[str, Any]:
        """
        使用LLM验证证据是否充分支持陈述

        参数:
            statement: 知识点或技能陈述
            evidence_text: 证据文本

        返回:
            验证结果
        """
        if not self.enabled:
            return {
                "supported": True,
                "confidence": 0.5,
                "reasoning": "LLM未启用，无法验证"
            }

        prompt = f"""你是一个证据分析专家。请判断以下证据是否充分支持陈述。

陈述：
{statement}

证据：
{evidence_text}

请分析并返回JSON格式：
1. supported - 是否支持（true/false）
2. confidence - 置信度（0-1）
3. reasoning - 分析理由
4. gaps - 如果不充分，缺少什么（可选）

只返回JSON，不要其他内容。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个逻辑分析专家，擅长评估证据的充分性。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        return result

    def improve_description(self, description: str, max_length: int = 300) -> str:
        """
        改进技能description，确保简洁清晰且不超过长度限制

        参数:
            description: 原始描述
            max_length: 最大长度

        返回:
            改进后的描述
        """
        if not self.enabled or len(description) <= max_length:
            return description[:max_length]

        prompt = f"""请将以下技能描述优化为简洁清晰的版本，不超过{max_length}个字符。

原始描述：
{description}

要求：
1. 保留核心信息
2. 明确触发条件
3. 简洁清晰
4. 不超过{max_length}个字符

只返回优化后的描述，不要其他内容。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个技术写作专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        improved = response.choices[0].message.content.strip()

        return improved[:max_length]

    def extract_relations(
        self,
        knowledge_items: List[Dict[str, Any]],
        skill_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        使用LLM自动提取知识-技能关系

        参数:
            knowledge_items: 知识点列表
            skill_items: 技能列表

        返回:
            关系列表
        """
        if not self.enabled:
            return []

        # 限制输入大小
        knowledge_sample = knowledge_items[:20]
        skill_sample = skill_items[:20]

        # 构建简化描述
        knowledge_desc = "\n".join([
            f"K{i}: {k.get('title', '')} - {k.get('statement', '')[:100]}"
            for i, k in enumerate(knowledge_sample)
        ])

        skill_desc = "\n".join([
            f"S{i}: {s.get('title', '')} - {s.get('description', '')[:100]}"
            for i, s in enumerate(skill_sample)
        ])

        prompt = f"""你是一个知识关系分析专家。请分析以下知识点和技能之间的关系。

知识点：
{knowledge_desc}

技能：
{skill_desc}

请识别有意义的关系，返回JSON数组，每个关系包含：
1. knowledge_index - 知识点索引（K后的数字）
2. skill_index - 技能索引（S后的数字）
3. relation_type - 关系类型（uses, explains, depends_on, supports）
4. strength - 关系强度（strong, moderate, weak）
5. reasoning - 关系理由

只返回JSON数组，不要其他内容。"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个知识图谱专家。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        relations = result.get("relations", [])

        # 转换为实际的ID
        enhanced_relations = []
        for rel in relations:
            k_idx = rel.get("knowledge_index")
            s_idx = rel.get("skill_index")

            if k_idx < len(knowledge_sample) and s_idx < len(skill_sample):
                enhanced_relations.append({
                    "knowledge_id": knowledge_sample[k_idx].get("knowledge_id"),
                    "skill_id": skill_sample[s_idx].get("skill_id"),
                    "relation_type": rel.get("relation_type", "uses"),
                    "strength": rel.get("strength", "moderate"),
                    "evidence": rel.get("reasoning", "")
                })

        return enhanced_relations
