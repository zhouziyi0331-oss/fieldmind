"""
技能推荐服务 - 增强版

整合多个数据源提供智能技能推荐：
1. Hermes学习引擎的历史经验
2. 知识蒸馏生成的技能
3. 性能指标和优化建议
4. 用户行为模式
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from app.models.generated_skill import GeneratedSkill, SkillGenerationStatus
from app.models.skill_optimization import PerformanceMetric, OptimizationRecommendation
from app.services.hermes_learning_engine import get_learning_engine, LearningType

logger = logging.getLogger(__name__)


class SkillRecommendationService:
    """技能推荐服务"""

    def __init__(self, db: Session):
        self.db = db
        self.hermes_engine = get_learning_engine()
        # 注入数据库会话
        if not self.hermes_engine.db:
            self.hermes_engine.db = db

    def recommend_for_project(
        self,
        project_id: int,
        context: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        为项目推荐技能

        Args:
            project_id: 项目ID
            context: 当前上下文（任务类型、关键词等）
            limit: 返回数量

        Returns:
            推荐技能列表，按相关性排序
        """
        recommendations = []

        # 1. 从知识蒸馏获取相关技能
        distilled_skills = self._get_distilled_skills(project_id, context)
        for skill in distilled_skills:
            recommendations.append({
                "skill_id": f"distilled_{skill.id}",
                "skill_name": skill.skill_name,
                "description": skill.description,
                "source": "knowledge_distillation",
                "relevance_score": self._calculate_relevance(skill, context),
                "confidence": 0.85,
                "usage_count": 0,
                "success_rate": 1.0,
                "metadata": {
                    "keywords": skill.keywords,
                    "context": skill.context,
                    "created_at": skill.created_at.isoformat()
                }
            })

        # 2. 从Hermes学习引擎获取学习到的技能
        hermes_skills = self._get_hermes_skills(project_id, context)
        recommendations.extend(hermes_skills)

        # 3. 获取性能优异的技能
        high_performance_skills = self._get_high_performance_skills(project_id)
        recommendations.extend(high_performance_skills)

        # 4. 去重并排序
        recommendations = self._deduplicate_and_sort(recommendations)

        return recommendations[:limit]

    def _get_distilled_skills(
        self,
        project_id: int,
        context: Optional[Dict[str, Any]]
    ) -> List[GeneratedSkill]:
        """获取蒸馏生成的技能"""
        query = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.project_id == project_id,
            GeneratedSkill.is_active == True,
            GeneratedSkill.status == SkillGenerationStatus.DEPLOYED
        )

        # 如果有上下文，使用关键词过滤
        if context and context.get("keywords"):
            keywords = context["keywords"]
            if isinstance(keywords, list):
                keywords = ",".join(keywords)

            # 简单的关键词匹配
            filters = []
            for keyword in keywords.split(","):
                keyword = keyword.strip()
                if keyword:
                    filters.append(GeneratedSkill.keywords.like(f"%{keyword}%"))

            if filters:
                from sqlalchemy import or_
                query = query.filter(or_(*filters))

        return query.order_by(GeneratedSkill.created_at.desc()).limit(20).all()

    def _get_hermes_skills(
        self,
        project_id: int,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """从Hermes学习引擎获取技能"""
        recommendations = []

        # 加载项目的蒸馏技能到Hermes引擎
        self.hermes_engine.load_distilled_skills(project_id)

        # 获取所有技能
        for skill_id, skill in self.hermes_engine.skills.items():
            # 过滤：只包含与项目相关的技能
            if skill.skill_type == "distilled_knowledge":
                # 已在蒸馏技能中包含，跳过
                continue

            recommendations.append({
                "skill_id": skill.skill_id,
                "skill_name": skill.skill_name,
                "description": skill.description,
                "source": "hermes_learning",
                "relevance_score": self._calculate_hermes_relevance(skill, context),
                "confidence": skill.confidence_score,
                "usage_count": skill.usage_count,
                "success_rate": skill.success_rate,
                "metadata": {
                    "skill_type": skill.skill_type,
                    "learned_from": skill.learned_from,
                    "last_updated": skill.last_updated.isoformat()
                }
            })

        return recommendations

    def _get_high_performance_skills(
        self,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """获取性能优异的技能"""
        recommendations = []

        # 查询最近30天的性能数据
        since = datetime.utcnow() - timedelta(days=30)

        # 统计每个技能的性能
        from sqlalchemy import func
        performance_stats = self.db.query(
            PerformanceMetric.skill_id,
            func.count(PerformanceMetric.id).label("total_executions"),
            func.avg(PerformanceMetric.execution_time).label("avg_time"),
            func.sum(func.cast(PerformanceMetric.success, int)).label("success_count")
        ).filter(
            PerformanceMetric.project_id == project_id,
            PerformanceMetric.measured_at >= since
        ).group_by(
            PerformanceMetric.skill_id
        ).having(
            func.count(PerformanceMetric.id) >= 5  # 至少执行5次
        ).all()

        for stat in performance_stats:
            success_rate = stat.success_count / stat.total_executions if stat.total_executions > 0 else 0

            # 只推荐成功率高且性能好的技能
            if success_rate >= 0.9 and stat.avg_time < 10.0:
                recommendations.append({
                    "skill_id": stat.skill_id,
                    "skill_name": f"Skill {stat.skill_id}",  # 需要从skill表获取名称
                    "description": "高性能技能",
                    "source": "performance_analysis",
                    "relevance_score": success_rate * 0.5 + (1.0 / (1.0 + stat.avg_time)) * 0.5,
                    "confidence": 0.9,
                    "usage_count": stat.total_executions,
                    "success_rate": success_rate,
                    "metadata": {
                        "avg_execution_time": float(stat.avg_time),
                        "total_executions": stat.total_executions
                    }
                })

        return recommendations

    def _calculate_relevance(
        self,
        skill: GeneratedSkill,
        context: Optional[Dict[str, Any]]
    ) -> float:
        """计算蒸馏技能的相关性得分"""
        if not context:
            return 0.5  # 默认中等相关性

        score = 0.0
        factors = 0

        # 关键词匹配
        if context.get("keywords") and skill.keywords:
            context_keywords = set(context["keywords"])
            skill_keywords = set(skill.keywords.split(","))

            overlap = len(context_keywords & skill_keywords)
            if overlap > 0:
                score += overlap / len(context_keywords)
                factors += 1

        # 上下文匹配
        if context.get("context") and skill.context:
            # 简单的文本包含检查
            if context["context"].lower() in skill.context.lower():
                score += 1.0
                factors += 1

        return score / factors if factors > 0 else 0.3

    def _calculate_hermes_relevance(
        self,
        skill: Any,  # LearnedSkill
        context: Optional[Dict[str, Any]]
    ) -> float:
        """计算Hermes技能的相关性得分"""
        if not context:
            return skill.confidence_score

        # 基于置信度和使用次数
        base_score = skill.confidence_score

        # 使用次数加成（归一化）
        usage_bonus = min(skill.usage_count / 100.0, 0.2)

        return min(base_score + usage_bonus, 1.0)

    def _deduplicate_and_sort(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重并按相关性排序"""
        # 按skill_name去重（保留相关性最高的）
        seen = {}
        for rec in recommendations:
            name = rec["skill_name"]
            if name not in seen or rec["relevance_score"] > seen[name]["relevance_score"]:
                seen[name] = rec

        # 按相关性排序
        sorted_recs = sorted(
            seen.values(),
            key=lambda x: (x["relevance_score"], x["confidence"], x["usage_count"]),
            reverse=True
        )

        return sorted_recs

    def suggest_skill_improvements(
        self,
        skill_id: str,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        为技能提供改进建议

        基于性能指标和优化建议
        """
        suggestions = []

        # 1. 获取性能指标
        recent_metrics = self.db.query(PerformanceMetric).filter(
            PerformanceMetric.skill_id == skill_id,
            PerformanceMetric.project_id == project_id,
            PerformanceMetric.measured_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(PerformanceMetric.measured_at.desc()).limit(50).all()

        if recent_metrics:
            # 分析性能
            avg_time = sum(m.execution_time for m in recent_metrics) / len(recent_metrics)
            success_rate = sum(1 for m in recent_metrics if m.success) / len(recent_metrics)

            if avg_time > 5.0:
                suggestions.append({
                    "type": "performance",
                    "title": "优化执行时间",
                    "description": f"当前平均执行时间{avg_time:.2f}秒，建议优化算法或添加缓存",
                    "priority": "high" if avg_time > 10 else "medium"
                })

            if success_rate < 0.9:
                suggestions.append({
                    "type": "reliability",
                    "title": "提高成功率",
                    "description": f"当前成功率{success_rate:.2%}，建议添加错误处理和重试机制",
                    "priority": "high"
                })

        # 2. 获取优化建议
        recommendations = self.db.query(OptimizationRecommendation).filter(
            OptimizationRecommendation.skill_id == skill_id,
            OptimizationRecommendation.is_applied == False
        ).order_by(OptimizationRecommendation.created_at.desc()).limit(5).all()

        for rec in recommendations:
            suggestions.append({
                "type": rec.recommendation_type.value,
                "title": rec.title,
                "description": rec.description,
                "priority": rec.priority,
                "metadata": rec.recommendation_data
            })

        return suggestions

    def get_skill_usage_trends(
        self,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取技能使用趋势

        Args:
            project_id: 项目ID
            days: 统计天数

        Returns:
            趋势数据
        """
        since = datetime.utcnow() - timedelta(days=days)

        # 查询性能数据
        metrics = self.db.query(PerformanceMetric).filter(
            PerformanceMetric.project_id == project_id,
            PerformanceMetric.measured_at >= since
        ).all()

        # 按技能统计
        skill_stats = defaultdict(lambda: {
            "executions": 0,
            "successes": 0,
            "total_time": 0.0,
            "dates": defaultdict(int)
        })

        for metric in metrics:
            stats = skill_stats[metric.skill_id]
            stats["executions"] += 1
            if metric.success:
                stats["successes"] += 1
            stats["total_time"] += metric.execution_time
            date_key = metric.measured_at.date().isoformat()
            stats["dates"][date_key] += 1

        # 转换为结果格式
        trends = []
        for skill_id, stats in skill_stats.items():
            trends.append({
                "skill_id": skill_id,
                "total_executions": stats["executions"],
                "success_rate": stats["successes"] / stats["executions"] if stats["executions"] > 0 else 0,
                "avg_execution_time": stats["total_time"] / stats["executions"] if stats["executions"] > 0 else 0,
                "daily_usage": dict(stats["dates"])
            })

        # 按使用次数排序
        trends.sort(key=lambda x: x["total_executions"], reverse=True)

        return {
            "period_days": days,
            "total_skills": len(trends),
            "total_executions": sum(t["total_executions"] for t in trends),
            "skills": trends[:20]  # 返回前20个
        }
