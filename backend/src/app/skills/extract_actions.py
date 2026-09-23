"""
提取行动建议 Skill - 基于差距和趋势分析
"""
from typing import Dict, Any, List
from collections import Counter


class ExtractActionsSkill:
    """
    行动建议提取Skill

    方法论：Gap + Trend Analysis
    - 识别问题和差距
    - 分析趋势和机会
    - 生成可执行建议
    - 优先级排序
    """

    METADATA = {
        "name": "extract_actions",
        "version": "1.0.0",
        "type": "gap_analysis",
        "output_type": "行动建议"
    }

    # 问题关键词
    PROBLEM_KEYWORDS = [
        "问题", "困难", "挑战", "障碍", "瓶颈",
        "不足", "缺陷", "缺少", "缺乏",
        "风险", "威胁", "危机",
        "problem", "issue", "challenge", "risk"
    ]

    # 机会关键词
    OPPORTUNITY_KEYWORDS = [
        "机会", "优势", "潜力", "可能",
        "改进", "优化", "提升", "增强",
        "opportunity", "potential", "improve"
    ]

    # 行动关键词
    ACTION_KEYWORDS = [
        "应该", "需要", "必须", "建议",
        "可以", "能够", "尝试",
        "should", "need", "must", "suggest"
    ]

    def __init__(self, db_session):
        self.db = db_session

    def extract(self, chunks: List[Dict[str, Any]],
                entities: List[Dict[str, Any]],
                relations: List[Dict[str, Any]],
                events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行行动建议提取

        参数:
            chunks: 文本块列表
            entities: 实体列表
            relations: 关系列表
            events: 事件列表

        返回:
            行动建议列表，每个包含：
            - content: 建议内容
            - category: 类别（问题解决/机会把握/趋势应对）
            - priority: 优先级（高/中/低）
            - rationale: 建议理由
            - credibility: 可信度
            - confidence: 置信度
            - source_chunks: 来源块ID列表
        """
        actions = []

        # 1. 从问题中提取建议
        problem_actions = self._extract_from_problems(chunks)
        actions.extend(problem_actions)

        # 2. 从机会中提取建议
        opportunity_actions = self._extract_from_opportunities(chunks)
        actions.extend(opportunity_actions)

        # 3. 从趋势中提取建议
        trend_actions = self._extract_from_trends(entities, events)
        actions.extend(trend_actions)

        # 4. 优先级排序
        actions = self._prioritize_actions(actions)

        return actions

    def _extract_from_problems(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从问题中提取建议"""
        actions = []

        for chunk in chunks:
            chunk_id = chunk.get("id")
            text = chunk.get("content", "")

            # 检查是否包含问题关键词
            problem_count = sum(1 for kw in self.PROBLEM_KEYWORDS if kw in text)

            if problem_count > 0:
                # 检查是否也包含行动关键词
                has_action = any(kw in text for kw in self.ACTION_KEYWORDS)

                if has_action:
                    action = {
                        "content": f"针对识别的问题采取行动: {text[:200]}...",
                        "category": "问题解决",
                        "priority": "高" if problem_count >= 2 else "中",
                        "rationale": f"文本中识别到{problem_count}个问题指示词",
                        "credibility": 0.7,
                        "confidence": 0.65,
                        "source_chunks": [chunk_id]
                    }
                    actions.append(action)

        return actions

    def _extract_from_opportunities(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从机会中提取建议"""
        actions = []

        for chunk in chunks:
            chunk_id = chunk.get("id")
            text = chunk.get("content", "")

            # 检查是否包含机会关键词
            opportunity_count = sum(1 for kw in self.OPPORTUNITY_KEYWORDS if kw in text)

            if opportunity_count > 0:
                action = {
                    "content": f"把握识别的机会: {text[:200]}...",
                    "category": "机会把握",
                    "priority": "中",
                    "rationale": f"文本中识别到{opportunity_count}个机会指示词",
                    "credibility": 0.65,
                    "confidence": 0.6,
                    "source_chunks": [chunk_id]
                }
                actions.append(action)

        return actions

    def _extract_from_trends(self, entities: List[Dict[str, Any]],
                           events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """从趋势中提取建议"""
        actions = []

        # 分析实体增长趋势（简化版：高频实体）
        entity_counter = Counter(e.get("entity_name") for e in entities)
        top_entities = entity_counter.most_common(3)

        for entity_name, count in top_entities:
            if count >= 5:
                action = {
                    "content": f"关注高频主题 '{entity_name}' 的发展趋势（出现{count}次）",
                    "category": "趋势应对",
                    "priority": "中",
                    "rationale": f"该主题在文档中高频出现，可能是重要方向",
                    "credibility": 0.7,
                    "confidence": 0.7,
                    "source_chunks": []  # 趋势不绑定特定chunk
                }
                actions.append(action)

        return actions

    def _prioritize_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优先级排序"""
        # 定义优先级权重
        priority_weight = {
            "高": 3,
            "中": 2,
            "低": 1
        }

        # 按优先级和可信度排序
        sorted_actions = sorted(
            actions,
            key=lambda a: (
                priority_weight.get(a.get("priority", "中"), 2),
                a.get("credibility", 0)
            ),
            reverse=True
        )

        return sorted_actions
