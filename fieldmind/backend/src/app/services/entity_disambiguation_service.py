"""
实体消歧服务
当不同文档提到同一个人名时，通过多维度验证判断是否为同一实体

策略：
1. 行为相似度 - 看他做的事情
2. 上下文相似度 - 看上下文
3. 时间线一致性 - 时间线是否一致
4. 关系网络推理 - 从关系网来推（同村场景，地域无效）
5. 人工确认机制 - 标记需要人工确认的case
"""
from typing import List, Dict, Any, Tuple
import numpy as np
from datetime import datetime
from app.models.knowledge_graph import (
    GraphNode,
    EntityDisambiguationResult
)


class EntityDisambiguationService:
    """实体消歧服务"""

    def __init__(self):
        # 阈值配置
        self.auto_merge_threshold = 0.75  # > 0.75 自动合并
        self.human_confirm_threshold = 0.50  # 0.5-0.75 需要人工确认
        # < 0.5 视为不同实体

        # 权重配置（根据田野调查场景优化）
        self.weights = {
            'behavior': 0.30,      # 行为相似度（重要）
            'context': 0.25,       # 上下文相似度
            'timeline': 0.20,      # 时间线一致性
            'network': 0.25,       # 关系网络（同村场景最重要）
        }

    def disambiguate(
        self,
        entity1: GraphNode,
        entity2: GraphNode
    ) -> EntityDisambiguationResult:
        """
        判断两个实体是否为同一实体

        Args:
            entity1: 实体1
            entity2: 实体2

        Returns:
            EntityDisambiguationResult: 消歧结果
        """
        # 1. 计算行为相似度
        behavior_sim = self._calculate_behavior_similarity(entity1, entity2)

        # 2. 计算上下文相似度（使用向量）
        context_sim = self._calculate_context_similarity(entity1, entity2)

        # 3. 检查时间线一致性
        timeline_consistency = self._check_timeline_consistency(entity1, entity2)

        # 4. 计算关系网络相似度（关键！）
        network_sim = self._calculate_network_similarity(entity1, entity2)

        # 5. 加权综合分数
        total_score = (
            self.weights['behavior'] * behavior_sim +
            self.weights['context'] * context_sim +
            self.weights['timeline'] * timeline_consistency +
            self.weights['network'] * network_sim
        )

        # 6. 决策
        is_same = False
        needs_human = False
        decision_reason = ""

        if total_score >= self.auto_merge_threshold:
            is_same = True
            decision_reason = f"高置信度匹配 (分数={total_score:.3f})"
        elif total_score >= self.human_confirm_threshold:
            is_same = False  # 暂不合并
            needs_human = True
            decision_reason = f"中等置信度，需要人工确认 (分数={total_score:.3f})"
        else:
            is_same = False
            decision_reason = f"低置信度，视为不同实体 (分数={total_score:.3f})"

        return EntityDisambiguationResult(
            entity1_id=entity1.id,
            entity2_id=entity2.id,
            is_same=is_same,
            confidence=total_score,
            behavior_similarity=behavior_sim,
            context_similarity=context_sim,
            timeline_consistency=timeline_consistency,
            network_similarity=network_sim,
            decision_reason=decision_reason,
            needs_human_confirmation=needs_human
        )

    def _calculate_behavior_similarity(
        self,
        entity1: GraphNode,
        entity2: GraphNode
    ) -> float:
        """
        计算行为相似度 - 看他们做的事情

        例如：
        - 实体1的actions: ["担任村支书", "主持修路", "组织春节活动"]
        - 实体2的actions: ["村支书工作", "修建道路", "举办春节庆典"]

        Returns:
            0-1的相似度分数
        """
        actions1 = set(entity1.actions)
        actions2 = set(entity2.actions)

        if not actions1 or not actions2:
            return 0.0

        # 计算Jaccard相似度
        intersection = len(actions1 & actions2)
        union = len(actions1 | actions2)

        if union == 0:
            return 0.0

        jaccard = intersection / union

        # 使用模糊匹配增强（考虑语义相似的行为）
        fuzzy_matches = 0
        for a1 in actions1:
            for a2 in actions2:
                if self._fuzzy_match_action(a1, a2):
                    fuzzy_matches += 1

        fuzzy_score = fuzzy_matches / max(len(actions1), len(actions2))

        # 综合Jaccard和模糊匹配
        return (jaccard * 0.6 + fuzzy_score * 0.4)

    def _fuzzy_match_action(self, action1: str, action2: str) -> bool:
        """
        模糊匹配行为（考虑同义词和近义词）

        例如：
        - "担任村支书" 和 "村支书工作" 应该匹配
        - "修路" 和 "修建道路" 应该匹配
        """
        # 关键词映射
        synonyms = [
            {"村支书", "村委会书记", "支部书记"},
            {"修路", "修建道路", "道路建设"},
            {"组织", "主持", "举办", "召集"},
            {"春节", "过年", "新年"},
        ]

        # 提取关键词
        keywords1 = set()
        keywords2 = set()

        for syn_group in synonyms:
            for syn in syn_group:
                if syn in action1:
                    keywords1.add(frozenset(syn_group))
                if syn in action2:
                    keywords2.add(frozenset(syn_group))

        return bool(keywords1 & keywords2)

    def _calculate_context_similarity(
        self,
        entity1: GraphNode,
        entity2: GraphNode
    ) -> float:
        """
        计算上下文相似度（使用向量）

        使用Agent 3生成的context_vector (1024维)
        """
        if entity1.context_vector is None or entity2.context_vector is None:
            # 如果没有向量，降级到文本相似度
            return self._text_similarity(
                entity1.context_summary or "",
                entity2.context_summary or ""
            )

        vec1 = np.array(entity1.context_vector)
        vec2 = np.array(entity2.context_vector)

        # 余弦相似度
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        cosine_sim = dot_product / (norm1 * norm2)

        # 归一化到0-1
        return (cosine_sim + 1) / 2

    def _text_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度（降级方案）"""
        if not text1 or not text2:
            return 0.0

        # 简单的字符级Jaccard相似度
        set1 = set(text1)
        set2 = set(text2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _check_timeline_consistency(
        self,
        entity1: GraphNode,
        entity2: GraphNode
    ) -> float:
        """
        检查时间线一致性

        如果时间线冲突（比如同时在两个地方），返回0
        如果时间线一致或重叠，返回1
        如果没有时间线信息，返回0.5（中性）

        例如：
        - 实体1: 2010-2015年担任村支书
        - 实体2: 2012-2018年担任村支书
        → 时间线重叠，可能是同一人
        """
        timeline1 = entity1.timeline
        timeline2 = entity2.timeline

        if not timeline1 or not timeline2:
            return 0.5  # 没有时间线信息，中性

        # 检查是否有时间冲突
        conflicts = 0
        overlaps = 0

        for event1 in timeline1:
            start1 = event1.get('start_time')
            end1 = event1.get('end_time')
            location1 = event1.get('location')

            for event2 in timeline2:
                start2 = event2.get('start_time')
                end2 = event2.get('end_time')
                location2 = event2.get('location')

                # 检查时间重叠
                if self._time_overlap(start1, end1, start2, end2):
                    # 同时间在不同地点 → 冲突
                    if location1 and location2 and location1 != location2:
                        conflicts += 1
                    else:
                        overlaps += 1

        if conflicts > 0:
            return 0.0  # 有冲突，不是同一人

        if overlaps > 0:
            return 1.0  # 有重叠，可能是同一人

        return 0.5  # 时间线不重叠，无法判断

    def _time_overlap(
        self,
        start1: Any,
        end1: Any,
        start2: Any,
        end2: Any
    ) -> bool:
        """判断两个时间段是否重叠"""
        if not all([start1, end1, start2, end2]):
            return False

        # 转换为datetime
        if isinstance(start1, str):
            start1 = datetime.fromisoformat(start1)
        if isinstance(end1, str):
            end1 = datetime.fromisoformat(end1)
        if isinstance(start2, str):
            start2 = datetime.fromisoformat(start2)
        if isinstance(end2, str):
            end2 = datetime.fromisoformat(end2)

        return not (end1 < start2 or end2 < start1)

    def _calculate_network_similarity(
        self,
        entity1: GraphNode,
        entity2: GraphNode
    ) -> float:
        """
        计算关系网络相似度

        ⭐ 这是同村场景下最重要的判断依据！

        通过关系网络指纹（relationship_fingerprint）判断
        关系网络指纹 = 与该实体相关联的其他实体ID集合

        例如：
        - 实体1的关系网络: {张三, 李四, 王五, 村委会, XX协会}
        - 实体2的关系网络: {张三, 李四, 赵六, 村委会, YY基金会}
        → 共同关系人越多，越可能是同一人
        """
        if not entity1.relationship_fingerprint or not entity2.relationship_fingerprint:
            return 0.5  # 没有关系网络信息，中性

        # 关系网络指纹是逗号分隔的ID列表
        network1 = set(entity1.relationship_fingerprint.split(','))
        network2 = set(entity2.relationship_fingerprint.split(','))

        if not network1 or not network2:
            return 0.5

        # 计算Jaccard相似度
        intersection = len(network1 & network2)
        union = len(network1 | network2)

        if union == 0:
            return 0.5

        jaccard = intersection / union

        # 关系网络相似度 > 0.3 通常意味着是同一人
        # 因为同村场景下，同名但不同人的关系网络重叠很小
        return jaccard

    def batch_disambiguate(
        self,
        entities: List[GraphNode]
    ) -> Dict[str, List[str]]:
        """
        批量消歧：找出所有需要合并的实体组

        Returns:
            Dict[canonical_id, List[duplicate_ids]]
            例如: {
                "entity_001": ["entity_123", "entity_456"],  # entity_123和456应该合并到001
                "entity_002": ["entity_789"]
            }
        """
        merge_groups = {}
        processed = set()

        for i, entity1 in enumerate(entities):
            if entity1.id in processed:
                continue

            duplicates = []

            for j, entity2 in enumerate(entities):
                if i >= j or entity2.id in processed:
                    continue

                # 只对同类型、同名称的实体进行消歧
                if entity1.type != entity2.type or entity1.name != entity2.name:
                    continue

                result = self.disambiguate(entity1, entity2)

                if result.is_same:
                    duplicates.append(entity2.id)
                    processed.add(entity2.id)

            if duplicates:
                merge_groups[entity1.id] = duplicates

        return merge_groups
