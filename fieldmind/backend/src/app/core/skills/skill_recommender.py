"""
技能推荐器 (Skill Recommender)

基于上下文智能推荐技能
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.core.skills.skill_registry import Skill, SkillRegistry, SkillStatus

logger = logging.getLogger(__name__)


@dataclass
class SkillRecommendation:
    """技能推荐结果"""
    skill: Skill              # 推荐的技能
    score: float              # 相关度分数 (0-1)
    reason: str               # 推荐理由
    confidence: float         # 置信度 (0-1)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'skill': self.skill.to_dict(),
            'score': self.score,
            'reason': self.reason,
            'confidence': self.confidence
        }


class SkillRecommender:
    """技能推荐器"""

    def __init__(self, skill_registry: SkillRegistry):
        """
        初始化技能推荐器

        Args:
            skill_registry: 技能注册中心
        """
        self.skill_registry = skill_registry

        # 推荐策略权重
        self.weights = {
            'name_match': 0.3,          # 名称匹配
            'description_match': 0.25,  # 描述匹配
            'tag_match': 0.2,           # 标签匹配
            'category_match': 0.15,     # 类别匹配
            'quality': 0.05,            # 质量分数
            'usage': 0.05              # 使用频率
        }

        logger.info("✅ 技能推荐器初始化")

    # ==================== 核心推荐方法 ====================

    def recommend(
        self,
        context: Dict[str, Any],
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[SkillRecommendation]:
        """
        推荐技能

        Args:
            context: 上下文信息，包含：
                - query: 用户查询/任务描述
                - task_type: 任务类型
                - input_data: 输入数据示例
                - history: 历史技能使用
                - user_preferences: 用户偏好
            top_k: 返回前K个推荐
            min_score: 最低分数阈值

        Returns:
            推荐的技能列表
        """
        logger.info(f"🎯 开始技能推荐: top_k={top_k}")

        # 1. 获取所有活跃技能
        all_skills = self.skill_registry.list_skills(
            status=SkillStatus.ACTIVE,
            limit=1000
        )

        if not all_skills:
            logger.warning("⚠️ 没有可用的技能")
            return []

        # 2. 计算每个技能的相关度
        recommendations = []

        for skill in all_skills:
            score = self.calculate_relevance(skill, context)

            if score >= min_score:
                reason = self._generate_reason(skill, context, score)
                confidence = self._calculate_confidence(skill, score)

                recommendations.append(SkillRecommendation(
                    skill=skill,
                    score=score,
                    reason=reason,
                    confidence=confidence
                ))

        # 3. 排序
        recommendations.sort(key=lambda x: x.score, reverse=True)

        # 4. 返回top_k
        result = recommendations[:top_k]

        logger.info(
            f"✅ 推荐完成: {len(result)} 个技能, "
            f"top={result[0].skill.name if result else 'None'}"
        )

        return result

    def calculate_relevance(
        self,
        skill: Skill,
        context: Dict[str, Any]
    ) -> float:
        """
        计算技能相关度

        Args:
            skill: 技能对象
            context: 上下文

        Returns:
            相关度分数 (0-1)
        """
        total_score = 0.0

        query = context.get('query', '').lower()
        task_type = context.get('task_type', '').lower()

        # 1. 名称匹配
        name_score = self._calculate_name_match(skill.name, query)
        total_score += name_score * self.weights['name_match']

        # 2. 描述匹配
        if skill.description:
            desc_score = self._calculate_text_match(skill.description, query)
            total_score += desc_score * self.weights['description_match']

        # 3. 标签匹配
        tag_score = self._calculate_tag_match(skill.tags, query)
        total_score += tag_score * self.weights['tag_match']

        # 4. 类别匹配
        if skill.category and task_type:
            category_score = 1.0 if task_type in skill.category.lower() else 0.0
            total_score += category_score * self.weights['category_match']

        # 5. 质量分数
        quality_score = skill.quality_score / 100.0  # 归一化到0-1
        total_score += quality_score * self.weights['quality']

        # 6. 使用频率
        usage_score = min(skill.usage_count / 100.0, 1.0)  # 归一化
        total_score += usage_score * self.weights['usage']

        # 7. 历史使用加成
        if 'history' in context:
            history = context['history']
            if skill.id in history:
                total_score *= 1.2  # 20%加成

        return min(total_score, 1.0)

    def _calculate_name_match(self, name: str, query: str) -> float:
        """计算名称匹配度"""
        name_lower = name.lower()
        query_lower = query.lower()

        # 完全匹配
        if query_lower == name_lower:
            return 1.0

        # 包含匹配
        if query_lower in name_lower or name_lower in query_lower:
            return 0.8

        # 单词匹配
        query_words = set(query_lower.split())
        name_words = set(name_lower.split())
        common_words = query_words & name_words

        if common_words:
            return len(common_words) / max(len(query_words), len(name_words))

        return 0.0

    def _calculate_text_match(self, text: str, query: str) -> float:
        """计算文本匹配度"""
        text_lower = text.lower()
        query_lower = query.lower()

        # 包含匹配
        if query_lower in text_lower:
            return 0.7

        # 单词匹配
        query_words = set(query_lower.split())
        text_words = set(text_lower.split())
        common_words = query_words & text_words

        if common_words:
            return 0.5 * (len(common_words) / len(query_words))

        return 0.0

    def _calculate_tag_match(self, tags: List[str], query: str) -> float:
        """计算标签匹配度"""
        if not tags:
            return 0.0

        query_lower = query.lower()
        matches = 0

        for tag in tags:
            if query_lower in tag.lower() or tag.lower() in query_lower:
                matches += 1

        if matches > 0:
            return min(matches / len(tags), 1.0)

        return 0.0

    def _calculate_confidence(self, skill: Skill, score: float) -> float:
        """
        计算推荐置信度

        基于：
        - 相关度分数
        - 技能使用次数
        - 成功率
        """
        confidence = score

        # 使用次数加权
        if skill.usage_count > 10:
            confidence *= 1.1
        elif skill.usage_count == 0:
            confidence *= 0.8

        # 成功率加权
        if skill.usage_count > 0:
            success_rate = skill.success_count / skill.usage_count
            confidence *= (0.8 + success_rate * 0.2)

        return min(confidence, 1.0)

    def _generate_reason(
        self,
        skill: Skill,
        context: Dict[str, Any],
        score: float
    ) -> str:
        """生成推荐理由"""
        reasons = []

        query = context.get('query', '').lower()

        # 名称匹配
        if query in skill.name.lower():
            reasons.append(f"名称匹配查询")

        # 描述匹配
        if skill.description and query in skill.description.lower():
            reasons.append(f"描述相关")

        # 高质量
        if skill.quality_score > 80:
            reasons.append(f"高质量技能 ({skill.quality_score:.0f}分)")

        # 常用
        if skill.usage_count > 50:
            reasons.append(f"常用技能 (使用{skill.usage_count}次)")

        # 成功率高
        if skill.usage_count > 0:
            success_rate = skill.success_count / skill.usage_count
            if success_rate > 0.9:
                reasons.append(f"成功率高 ({success_rate*100:.0f}%)")

        if reasons:
            return "、".join(reasons)
        else:
            return f"相关度: {score:.2f}"

    # ==================== 高级推荐 ====================

    def recommend_by_similarity(
        self,
        reference_skill_id: str,
        top_k: int = 5
    ) -> List[SkillRecommendation]:
        """
        基于相似性推荐技能

        Args:
            reference_skill_id: 参考技能ID
            top_k: 返回数量

        Returns:
            相似的技能列表
        """
        logger.info(f"🔍 基于相似性推荐: reference={reference_skill_id}")

        reference_skill = self.skill_registry.get_skill(reference_skill_id)
        if not reference_skill:
            logger.warning(f"⚠️ 参考技能未找到: {reference_skill_id}")
            return []

        all_skills = self.skill_registry.list_skills(
            status=SkillStatus.ACTIVE,
            limit=1000
        )

        recommendations = []

        for skill in all_skills:
            if skill.id == reference_skill_id:
                continue  # 跳过自己

            similarity = self._calculate_skill_similarity(
                reference_skill,
                skill
            )

            if similarity > 0.3:
                recommendations.append(SkillRecommendation(
                    skill=skill,
                    score=similarity,
                    reason=f"与 '{reference_skill.name}' 相似",
                    confidence=similarity
                ))

        # 排序
        recommendations.sort(key=lambda x: x.score, reverse=True)

        return recommendations[:top_k]

    def _calculate_skill_similarity(
        self,
        skill1: Skill,
        skill2: Skill
    ) -> float:
        """
        计算两个技能的相似度

        基于：
        - 类别相同
        - 标签重叠
        - 描述相似
        """
        similarity = 0.0

        # 类别相同
        if skill1.category and skill2.category:
            if skill1.category == skill2.category:
                similarity += 0.4

        # 标签重叠
        if skill1.tags and skill2.tags:
            common_tags = set(skill1.tags) & set(skill2.tags)
            if common_tags:
                tag_similarity = len(common_tags) / len(set(skill1.tags) | set(skill2.tags))
                similarity += tag_similarity * 0.3

        # 描述相似（简单词重叠）
        if skill1.description and skill2.description:
            words1 = set(skill1.description.lower().split())
            words2 = set(skill2.description.lower().split())
            common_words = words1 & words2

            if common_words:
                desc_similarity = len(common_words) / len(words1 | words2)
                similarity += desc_similarity * 0.3

        return min(similarity, 1.0)

    # ==================== 批量推荐 ====================

    def recommend_for_workflow(
        self,
        workflow_steps: List[Dict[str, Any]],
        top_k_per_step: int = 3
    ) -> Dict[int, List[SkillRecommendation]]:
        """
        为工作流的每个步骤推荐技能

        Args:
            workflow_steps: 工作流步骤列表
            top_k_per_step: 每步推荐数量

        Returns:
            每个步骤的推荐 {step_index: [recommendations]}
        """
        logger.info(f"📋 为工作流推荐技能: {len(workflow_steps)} 个步骤")

        recommendations = {}

        for idx, step in enumerate(workflow_steps):
            step_recommendations = self.recommend(
                context=step,
                top_k=top_k_per_step
            )
            recommendations[idx] = step_recommendations

        return recommendations

    # ==================== 统计和分析 ====================

    def get_popular_skills(
        self,
        limit: int = 10,
        time_period: Optional[str] = None
    ) -> List[Skill]:
        """
        获取热门技能

        Args:
            limit: 返回数量
            time_period: 时间段（暂不实现）

        Returns:
            热门技能列表
        """
        all_skills = self.skill_registry.list_skills(
            status=SkillStatus.ACTIVE,
            limit=1000
        )

        # 按使用次数排序
        sorted_skills = sorted(
            all_skills,
            key=lambda s: s.usage_count,
            reverse=True
        )

        return sorted_skills[:limit]

    def get_high_quality_skills(
        self,
        limit: int = 10,
        min_usage: int = 5
    ) -> List[Skill]:
        """
        获取高质量技能

        Args:
            limit: 返回数量
            min_usage: 最少使用次数

        Returns:
            高质量技能列表
        """
        all_skills = self.skill_registry.list_skills(
            status=SkillStatus.ACTIVE,
            limit=1000
        )

        # 过滤使用次数 + 按质量排序
        quality_skills = [
            s for s in all_skills
            if s.usage_count >= min_usage
        ]

        sorted_skills = sorted(
            quality_skills,
            key=lambda s: s.quality_score,
            reverse=True
        )

        return sorted_skills[:limit]

    def get_recommender_status(self) -> Dict[str, Any]:
        """获取推荐器状态"""
        return {
            'weights': self.weights,
            'total_skills': len(self.skill_registry.list_skills(limit=10000)),
            'active_skills': len(self.skill_registry.list_skills(
                status=SkillStatus.ACTIVE,
                limit=10000
            ))
        }


# 工厂函数
def create_skill_recommender(skill_registry: SkillRegistry) -> SkillRecommender:
    """创建技能推荐器实例"""
    return SkillRecommender(skill_registry)
