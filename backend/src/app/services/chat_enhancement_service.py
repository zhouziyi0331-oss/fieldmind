"""
对话增强集成服务

整合Hermes学习引擎和技能推荐，提供智能对话增强功能
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from app.services.enhanced_chat_service import EnhancedChatService
from app.services.hermes_learning_engine import get_learning_engine, LearningType
from app.services.skill_recommendation_service import SkillRecommendationService

logger = logging.getLogger(__name__)


class ChatEnhancementService:
    """对话增强服务"""

    def __init__(self, db: Session):
        self.db = db
        self.chat_service = EnhancedChatService()
        self.hermes_engine = get_learning_engine()
        self.skill_recommender = SkillRecommendationService(db)

        # 确保Hermes引擎有数据库连接
        if not self.hermes_engine.db:
            self.hermes_engine.db = db

    def chat_with_learning(
        self,
        query: str,
        session_id: str,
        project_id: int,
        skill_config: Optional[Dict] = None,
        memory_config: Optional[Dict] = None,
        use_deep_thinking: bool = False,
        learn_from_interaction: bool = True
    ) -> Dict[str, Any]:
        """
        带学习功能的对话

        Args:
            query: 用户查询
            session_id: 会话ID
            project_id: 项目ID
            skill_config: 技能配置
            memory_config: 记忆配置
            use_deep_thinking: 是否使用深度思考
            learn_from_interaction: 是否从交互中学习

        Returns:
            增强的对话响应
        """
        start_time = datetime.utcnow()

        # 1. 获取相关技能建议
        skill_suggestions = self._get_skill_suggestions(query, project_id)

        # 2. 从Hermes引擎获取历史经验
        similar_experiences = self._get_similar_experiences(query, project_id)

        # 3. 增强上下文
        enhanced_context = self._build_enhanced_context(
            query=query,
            skill_suggestions=skill_suggestions,
            experiences=similar_experiences
        )

        # 4. 执行对话
        response = self.chat_service.chat_with_skill(
            query=query,
            session_id=session_id,
            skill_config=skill_config or {},
            memory_config=memory_config,
            project_id=project_id,
            use_deep_thinking=use_deep_thinking
        )

        # 5. 记录学习经验
        if learn_from_interaction and not response.get("error"):
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._record_interaction_experience(
                project_id=project_id,
                query=query,
                response=response,
                execution_time=execution_time,
                skill_used=skill_config.get("skill_name") if skill_config else None
            )

        # 6. 增强响应
        response["skill_suggestions"] = skill_suggestions[:3]  # 返回前3个建议
        response["learning_applied"] = len(similar_experiences) > 0

        return response

    def _get_skill_suggestions(
        self,
        query: str,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """获取技能建议"""
        try:
            # 从查询中提取关键词
            keywords = self._extract_keywords(query)

            context = {
                "keywords": keywords,
                "context": query
            }

            suggestions = self.skill_recommender.recommend_for_project(
                project_id=project_id,
                context=context,
                limit=5
            )

            return suggestions

        except Exception as e:
            logger.error(f"获取技能建议失败: {e}")
            return []

    def _get_similar_experiences(
        self,
        query: str,
        project_id: int
    ) -> List[Any]:
        """获取相似的历史经验"""
        try:
            # 构建上下文
            context = {
                "query": query,
                "project_id": project_id
            }

            # 从Hermes引擎获取相似经验
            similar = self.hermes_engine.get_similar_experiences(
                context=context,
                learning_type=None,  # 所有类型
                limit=3
            )

            return similar

        except Exception as e:
            logger.error(f"获取历史经验失败: {e}")
            return []

    def _build_enhanced_context(
        self,
        query: str,
        skill_suggestions: List[Dict[str, Any]],
        experiences: List[Any]
    ) -> str:
        """构建增强上下文"""
        context_parts = []

        # 添加技能建议
        if skill_suggestions:
            context_parts.append("相关技能建议:")
            for i, skill in enumerate(skill_suggestions[:3], 1):
                context_parts.append(
                    f"{i}. {skill['skill_name']}: {skill['description']}"
                )
            context_parts.append("")

        # 添加历史经验
        if experiences:
            context_parts.append("相似历史经验:")
            for i, exp in enumerate(experiences, 1):
                context_parts.append(
                    f"{i}. 类型: {exp.learning_type.value}, "
                    f"成功: {'是' if exp.success else '否'}"
                )
            context_parts.append("")

        return "\n".join(context_parts)

    def _record_interaction_experience(
        self,
        project_id: int,
        query: str,
        response: Dict[str, Any],
        execution_time: float,
        skill_used: Optional[str]
    ):
        """记录交互经验"""
        try:
            self.hermes_engine.record_experience(
                project_id=project_id,
                learning_type=LearningType.PATTERN_RECOGNITION,
                context={
                    "query": query,
                    "skill_used": skill_used,
                    "contexts_used": response.get("contexts_used", {})
                },
                action={
                    "type": "chat_interaction",
                    "model": response.get("metadata", {}).get("model")
                },
                result={
                    "response_length": len(response.get("response", "")),
                    "thinking_used": response.get("thinking") is not None
                },
                success=not response.get("error", False),
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"记录交互经验失败: {e}")

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词（简化版）"""
        # TODO: 使用NLP技术提取关键词
        # 当前实现：简单的分词
        import re

        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)

        # 分词并过滤
        words = text.split()
        keywords = [w for w in words if len(w) > 2]

        return keywords[:10]  # 返回前10个

    def get_conversation_insights(
        self,
        session_id: str,
        project_id: int
    ) -> Dict[str, Any]:
        """
        获取对话洞察

        基于历史交互分析对话模式
        """
        try:
            # 获取会话相关的经验
            session_experiences = [
                exp for exp in self.hermes_engine.experiences
                if exp.project_id == project_id
            ]

            if not session_experiences:
                return {
                    "total_interactions": 0,
                    "patterns": [],
                    "recommendations": []
                }

            # 统计
            total = len(session_experiences)
            success_count = sum(1 for exp in session_experiences if exp.success)
            avg_time = sum(exp.execution_time for exp in session_experiences) / total

            # 识别模式
            patterns = self._identify_patterns(session_experiences)

            # 生成建议
            recommendations = self._generate_recommendations(patterns)

            return {
                "total_interactions": total,
                "success_rate": success_count / total if total > 0 else 0,
                "avg_execution_time": avg_time,
                "patterns": patterns,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"获取对话洞察失败: {e}")
            return {
                "total_interactions": 0,
                "patterns": [],
                "recommendations": [],
                "error": str(e)
            }

    def _identify_patterns(
        self,
        experiences: List[Any]
    ) -> List[Dict[str, Any]]:
        """识别对话模式"""
        patterns = []

        # 按学习类型分组
        from collections import defaultdict
        type_groups = defaultdict(list)

        for exp in experiences:
            type_groups[exp.learning_type.value].append(exp)

        # 识别频繁模式
        for learning_type, exps in type_groups.items():
            if len(exps) >= 3:  # 至少出现3次
                success_rate = sum(1 for e in exps if e.success) / len(exps)

                patterns.append({
                    "type": learning_type,
                    "frequency": len(exps),
                    "success_rate": success_rate,
                    "description": f"频繁使用 {learning_type} 模式"
                })

        return patterns

    def _generate_recommendations(
        self,
        patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """基于模式生成建议"""
        recommendations = []

        for pattern in patterns:
            if pattern["success_rate"] < 0.7:
                recommendations.append(
                    f"改进 {pattern['type']} 模式的成功率（当前 {pattern['success_rate']:.1%}）"
                )
            elif pattern["frequency"] > 10:
                recommendations.append(
                    f"考虑为 {pattern['type']} 模式创建专用技能"
                )

        if not recommendations:
            recommendations.append("继续保持良好的对话质量")

        return recommendations
