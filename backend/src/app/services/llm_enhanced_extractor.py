"""
LLM增强的实体关系提取器
使用Claude/GPT提升知识图谱构建质量
"""

import logging
import json
from typing import List, Tuple, Dict, Any
import os

logger = logging.getLogger(__name__)


class LLMEnhancedExtractor:
    """使用LLM增强实体和关系提取"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.use_llm = bool(self.api_key)

        if not self.use_llm:
            logger.warning("⚠️ 未检测到LLM API密钥，使用基础规则提取")
        else:
            logger.info("✅ LLM增强提取器已启用")

    def extract_with_llm(self, text: str, max_length: int = 2000) -> Tuple[List[Dict], List[Dict]]:
        """
        使用LLM提取实体和关系

        Args:
            text: 输入文本（田野调查笔记）
            max_length: 最大处理长度

        Returns:
            (entities, relations)
        """
        if not self.use_llm:
            return [], []

        # 截断过长文本
        if len(text) > max_length:
            text = text[:max_length] + "..."

        try:
            if "ANTHROPIC_API_KEY" in os.environ:
                return self._extract_with_claude(text)
            elif "OPENAI_API_KEY" in os.environ:
                return self._extract_with_openai(text)
        except Exception as e:
            logger.error(f"LLM提取失败: {e}")
            return [], []

        return [], []

    def _extract_with_claude(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """使用Claude提取"""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

            prompt = f"""请从以下田野调查文本中提取实体和关系。

文本：
{text}

请返回JSON格式：
{{
  "entities": [
    {{"name": "实体名称", "type": "PERSON|LOCATION|ORGANIZATION|CONCEPT|EVENT", "properties": {{}}}},
    ...
  ],
  "relations": [
    {{"source": "实体1", "target": "实体2", "type": "关系类型", "confidence": 0.9}},
    ...
  ]
}}

注意：
1. 人物（PERSON）：受访者、研究者、提到的人名
2. 地点（LOCATION）：村庄、城市、具体地点
3. 组织（ORGANIZATION）：单位、团体、机构
4. 概念（CONCEPT）：习俗、仪式、观念、术语
5. 事件（EVENT）：节日、活动、重要事件
6. 关系类型：居住于、属于、参与、认为、影响等

只返回JSON，不要其他文字。"""

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            result = json.loads(content)

            entities = result.get("entities", [])
            relations = result.get("relations", [])

            logger.info(f"✅ Claude提取: {len(entities)}个实体, {len(relations)}个关系")
            return entities, relations

        except Exception as e:
            logger.error(f"Claude提取失败: {e}")
            return [], []

    def _extract_with_openai(self, text: str) -> Tuple[List[Dict], List[Dict]]:
        """使用OpenAI提取"""
        try:
            import openai

            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            prompt = f"""请从以下田野调查文本中提取实体和关系。

文本：
{text}

请返回JSON格式：
{{
  "entities": [
    {{"name": "实体名称", "type": "PERSON|LOCATION|ORGANIZATION|CONCEPT|EVENT", "properties": {{}}}},
    ...
  ],
  "relations": [
    {{"source": "实体1", "target": "实体2", "type": "关系类型", "confidence": 0.9}},
    ...
  ]
}}

注意：
1. 人物（PERSON）：受访者、研究者、提到的人名
2. 地点（LOCATION）：村庄、城市、具体地点
3. 组织（ORGANIZATION）：单位、团体、机构
4. 概念（CONCEPT）：习俗、仪式、观念、术语
5. 事件（EVENT）：节日、活动、重要事件
6. 关系类型：居住于、属于、参与、认为、影响等

只返回JSON，不要其他文字。"""

            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "你是一个专业的田野调查数据分析助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            entities = result.get("entities", [])
            relations = result.get("relations", [])

            logger.info(f"✅ GPT-4提取: {len(entities)}个实体, {len(relations)}个关系")
            return entities, relations

        except Exception as e:
            logger.error(f"OpenAI提取失败: {e}")
            return [], []


# 全局单例
_llm_extractor = None

def get_llm_extractor() -> LLMEnhancedExtractor:
    """获取LLM提取器单例"""
    global _llm_extractor
    if _llm_extractor is None:
        _llm_extractor = LLMEnhancedExtractor()
    return _llm_extractor
