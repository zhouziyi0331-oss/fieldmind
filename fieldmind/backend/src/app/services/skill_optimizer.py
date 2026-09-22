"""
技能优化服务

自动监控技能性能并生成优化建议
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func, or_
import numpy as np
from collections import defaultdict

from app.models.skill_optimization import (
    SkillOptimization,
    PerformanceMetric,
    OptimizationRecommendation,
    OptimizationType,
    OptimizationStatus
)
from app.models.generated_skill import GeneratedSkill


class SkillOptimizer:
    """技能优化器 - 监控和优化技能性能"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 性能监控 ====================

    def record_performance(
        self,
        skill_id: str,
        execution_id: str,
        project_id: int,
        execution_time: float,
        success: bool,
        cpu_usage: Optional[float] = None,
        memory_usage: Optional[float] = None,
        api_calls: int = 0,
        tokens_used: int = 0,
        quality_score: Optional[float] = None,
        error_type: Optional[str] = None,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
        complexity_level: Optional[str] = None
    ) -> PerformanceMetric:
        """
        记录性能指标

        Args:
            skill_id: 技能ID
            execution_id: 执行记录ID
            project_id: 项目ID
            execution_time: 执行时间
            success: 是否成功
            其他性能指标...

        Returns:
            性能指标记录
        """
        metric = PerformanceMetric(
            skill_id=skill_id,
            execution_id=execution_id,
            project_id=project_id,
            execution_time=execution_time,
            cpu_usage_percent=cpu_usage,
            memory_usage_mb=memory_usage,
            api_calls_count=api_calls,
            tokens_used=tokens_used,
            success=success,
            quality_score=quality_score,
            error_type=error_type,
            input_size=input_size,
            output_size=output_size,
            complexity_level=complexity_level
        )

        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)

        # 检查是否需要优化
        self._check_optimization_needed(skill_id, project_id)

        return metric

    def _check_optimization_needed(
        self,
        skill_id: str,
        project_id: int
    ):
        """检查是否需要优化"""
        # 获取最近的性能数据
        recent_metrics = self.db.query(PerformanceMetric).filter(
            and_(
                PerformanceMetric.skill_id == skill_id,
                PerformanceMetric.measured_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).all()

        if len(recent_metrics) < 10:
            return  # 数据不足

        # 分析性能趋势
        issues = self._analyze_performance_issues(recent_metrics)

        # 如果发现问题，生成优化建议
        if issues:
            for issue in issues:
                self._generate_optimization_recommendation(
                    skill_id,
                    project_id,
                    issue
                )

    def _analyze_performance_issues(
        self,
        metrics: List[PerformanceMetric]
    ) -> List[Dict[str, Any]]:
        """分析性能问题"""
        issues = []

        # 1. 性能问题
        execution_times = [m.execution_time for m in metrics]
        avg_time = np.mean(execution_times)

        if avg_time > 5.0:  # 平均执行时间超过5秒
            issues.append({
                "type": OptimizationType.PERFORMANCE,
                "title": "执行时间过长",
                "description": f"平均执行时间{avg_time:.2f}秒，建议优化",
                "severity": "high" if avg_time > 10 else "medium",
                "data": {
                    "avg_time": avg_time,
                    "max_time": max(execution_times),
                    "min_time": min(execution_times)
                }
            })

        # 2. 可靠性问题
        success_rate = sum(1 for m in metrics if m.success) / len(metrics)

        if success_rate < 0.9:  # 成功率低于90%
            # 统计错误类型
            error_types = defaultdict(int)
            for m in metrics:
                if not m.success and m.error_type:
                    error_types[m.error_type] += 1

            issues.append({
                "type": OptimizationType.RELIABILITY,
                "title": "可靠性不足",
                "description": f"成功率{success_rate:.2%}，低于预期",
                "severity": "high" if success_rate < 0.8 else "medium",
                "data": {
                    "success_rate": success_rate,
                    "common_errors": dict(error_types)
                }
            })

        # 3. 资源使用问题
        memory_usages = [m.memory_usage_mb for m in metrics if m.memory_usage_mb]
        if memory_usages:
            avg_memory = np.mean(memory_usages)

            if avg_memory > 512:  # 平均内存使用超过512MB
                issues.append({
                    "type": OptimizationType.RESOURCE,
                    "title": "内存使用过高",
                    "description": f"平均内存使用{avg_memory:.0f}MB，建议优化",
                    "severity": "medium",
                    "data": {
                        "avg_memory": avg_memory,
                        "max_memory": max(memory_usages)
                    }
                })

        return issues

    def _generate_optimization_recommendation(
        self,
        skill_id: str,
        project_id: int,
        issue: Dict[str, Any]
    ):
        """生成优化建议"""
        # 检查是否已有类似建议
        existing = self.db.query(OptimizationRecommendation).filter(
            and_(
                OptimizationRecommendation.skill_id == skill_id,
                OptimizationRecommendation.recommendation_type == issue["type"],
                OptimizationRecommendation.is_applied == False
            )
        ).first()

        if existing:
            return  # 已有未应用的建议

        # 生成解决方案
        solution = self._suggest_solution(issue)

        # 计算优先级
        priority = self._calculate_priority(issue)

        recommendation = OptimizationRecommendation(
            skill_id=skill_id,
            project_id=project_id,
            recommendation_type=issue["type"],
            recommendation_title=issue["title"],
            recommendation_description=issue["description"],
            analysis_data=issue["data"],
            suggested_solution=solution,
            priority_score=priority,
            potential_improvement=solution.get("expected_improvement_pct")
        )

        self.db.add(recommendation)
        self.db.commit()

    def _suggest_solution(
        self,
        issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """建议解决方案"""
        issue_type = issue["type"]

        if issue_type == OptimizationType.PERFORMANCE:
            return {
                "solution_type": "性能优化",
                "suggestions": [
                    "使用批处理减少API调用",
                    "添加缓存机制",
                    "优化循环和算法"
                ],
                "implementation": "分析瓶颈，针对性优化",
                "expected_improvement_pct": 50,
                "effort_level": "medium"
            }

        elif issue_type == OptimizationType.RELIABILITY:
            return {
                "solution_type": "可靠性增强",
                "suggestions": [
                    "添加错误处理",
                    "增加重试机制",
                    "改进输入验证"
                ],
                "implementation": "针对常见错误类型添加处理逻辑",
                "expected_improvement_pct": 30,
                "effort_level": "low"
            }

        elif issue_type == OptimizationType.RESOURCE:
            return {
                "solution_type": "资源优化",
                "suggestions": [
                    "优化内存使用",
                    "使用流式处理",
                    "及时释放资源"
                ],
                "implementation": "分析内存占用，优化数据结构",
                "expected_improvement_pct": 40,
                "effort_level": "medium"
            }

        return {}

    def _calculate_priority(
        self,
        issue: Dict[str, Any]
    ) -> float:
        """计算优先级"""
        severity_scores = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3
        }

        base_score = severity_scores.get(issue.get("severity", "medium"), 0.5)

        # 根据影响调整
        issue_type = issue["type"]
        if issue_type == OptimizationType.RELIABILITY:
            base_score += 0.1  # 可靠性问题优先级更高

        return min(1.0, base_score)

    # ==================== 优化管理 ====================

    def create_optimization(
        self,
        skill_id: str,
        project_id: int,
        optimization_type: OptimizationType,
        title: str,
        description: str,
        identified_issues: Dict[str, Any],
        proposed_changes: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> SkillOptimization:
        """
        创建优化记录

        Args:
            skill_id: 技能ID
            project_id: 项目ID
            optimization_type: 优化类型
            title: 标题
            description: 描述
            identified_issues: 识别的问题
            proposed_changes: 提议的改变
            user_id: 用户ID

        Returns:
            优化记录
        """
        # 获取优化前的性能指标
        before_metrics = self._get_current_metrics(skill_id)

        optimization = SkillOptimization(
            skill_id=skill_id,
            project_id=project_id,
            triggered_by_user_id=user_id,
            optimization_type=optimization_type,
            optimization_title=title,
            optimization_description=description,
            identified_issues=identified_issues,
            proposed_changes=proposed_changes,
            before_metrics=before_metrics,
            status=OptimizationStatus.PROPOSED
        )

        self.db.add(optimization)
        self.db.commit()
        self.db.refresh(optimization)

        return optimization

    def _get_current_metrics(
        self,
        skill_id: str
    ) -> Dict[str, Any]:
        """获取当前性能指标"""
        recent = self.db.query(PerformanceMetric).filter(
            and_(
                PerformanceMetric.skill_id == skill_id,
                PerformanceMetric.measured_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).all()

        if not recent:
            return {}

        return {
            "avg_execution_time": np.mean([m.execution_time for m in recent]),
            "success_rate": sum(1 for m in recent if m.success) / len(recent),
            "avg_memory_usage": np.mean([m.memory_usage_mb for m in recent if m.memory_usage_mb]) if any(m.memory_usage_mb for m in recent) else None,
            "sample_size": len(recent)
        }

    def apply_optimization(
        self,
        optimization_id: str
    ) -> SkillOptimization:
        """
        应用优化

        Args:
            optimization_id: 优化ID

        Returns:
            更新后的优化记录
        """
        optimization = self.db.query(SkillOptimization).filter(
            SkillOptimization.id == optimization_id
        ).first()

        if not optimization:
            raise ValueError(f"优化记录 {optimization_id} 不存在")

        if optimization.status != OptimizationStatus.VALIDATED:
            raise ValueError("优化必须先验证才能应用")

        optimization.status = OptimizationStatus.APPLIED
        optimization.applied_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(optimization)

        return optimization

    def validate_optimization(
        self,
        optimization_id: str,
        after_metrics: Dict[str, Any],
        ab_test_data: Optional[Dict[str, Any]] = None
    ) -> SkillOptimization:
        """
        验证优化效果

        Args:
            optimization_id: 优化ID
            after_metrics: 优化后的指标
            ab_test_data: A/B测试数据

        Returns:
            更新后的优化记录
        """
        optimization = self.db.query(SkillOptimization).filter(
            SkillOptimization.id == optimization_id
        ).first()

        if not optimization:
            raise ValueError(f"优化记录 {optimization_id} 不存在")

        optimization.after_metrics = after_metrics
        optimization.ab_test_data = ab_test_data

        # 计算改进百分比
        if optimization.before_metrics and after_metrics:
            improvement = self._calculate_improvement(
                optimization.before_metrics,
                after_metrics
            )
            optimization.improvement_percentage = improvement
            optimization.is_effective = improvement > 10  # 改进超过10%才算有效

        # 计算验证分数
        validation_score = self._calculate_validation_score(
            optimization.before_metrics,
            after_metrics,
            ab_test_data
        )
        optimization.validation_score = validation_score

        optimization.status = OptimizationStatus.VALIDATED
        optimization.validated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(optimization)

        return optimization

    def _calculate_improvement(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any]
    ) -> float:
        """计算改进百分比"""
        improvements = []

        # 执行时间改进
        if "avg_execution_time" in before and "avg_execution_time" in after:
            time_improvement = (before["avg_execution_time"] - after["avg_execution_time"]) / before["avg_execution_time"] * 100
            improvements.append(time_improvement)

        # 成功率改进
        if "success_rate" in before and "success_rate" in after:
            rate_improvement = (after["success_rate"] - before["success_rate"]) * 100
            improvements.append(rate_improvement)

        return np.mean(improvements) if improvements else 0

    def _calculate_validation_score(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
        ab_test: Optional[Dict[str, Any]]
    ) -> float:
        """计算验证分数"""
        score = 0.5  # 基础分

        # 改进幅度加分
        improvement = self._calculate_improvement(before, after)
        if improvement > 20:
            score += 0.3
        elif improvement > 10:
            score += 0.2
        elif improvement > 5:
            score += 0.1

        # A/B测试显著性加分
        if ab_test and ab_test.get("statistical_significance", 0) > 0.9:
            score += 0.2

        return min(1.0, score)

    def revert_optimization(
        self,
        optimization_id: str,
        reason: str
    ) -> SkillOptimization:
        """
        回滚优化

        Args:
            optimization_id: 优化ID
            reason: 回滚原因

        Returns:
            更新后的优化记录
        """
        optimization = self.db.query(SkillOptimization).filter(
            SkillOptimization.id == optimization_id
        ).first()

        if not optimization:
            raise ValueError(f"优化记录 {optimization_id} 不存在")

        if not optimization.can_revert:
            raise ValueError("该优化不支持回滚")

        optimization.status = OptimizationStatus.REVERTED
        optimization.revert_reason = reason
        optimization.reverted_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(optimization)

        return optimization

    # ==================== 查询接口 ====================

    def get_optimizations(
        self,
        skill_id: Optional[str] = None,
        project_id: Optional[int] = None,
        status: Optional[OptimizationStatus] = None
    ) -> List[SkillOptimization]:
        """获取优化记录列表"""
        query = self.db.query(SkillOptimization)

        if skill_id:
            query = query.filter(SkillOptimization.skill_id == skill_id)

        if project_id:
            query = query.filter(SkillOptimization.project_id == project_id)

        if status:
            query = query.filter(SkillOptimization.status == status)

        return query.order_by(desc(SkillOptimization.proposed_at)).all()

    def get_recommendations(
        self,
        skill_id: Optional[str] = None,
        project_id: Optional[int] = None,
        is_applied: Optional[bool] = None,
        min_priority: float = 0.0
    ) -> List[OptimizationRecommendation]:
        """获取优化建议列表"""
        query = self.db.query(OptimizationRecommendation).filter(
            OptimizationRecommendation.priority_score >= min_priority
        )

        if skill_id:
            query = query.filter(OptimizationRecommendation.skill_id == skill_id)

        if project_id:
            query = query.filter(OptimizationRecommendation.project_id == project_id)

        if is_applied is not None:
            query = query.filter(OptimizationRecommendation.is_applied == is_applied)

        return query.order_by(
            desc(OptimizationRecommendation.priority_score)
        ).all()

    def get_performance_summary(
        self,
        skill_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取性能摘要"""
        start_date = datetime.utcnow() - timedelta(days=days)

        metrics = self.db.query(PerformanceMetric).filter(
            and_(
                PerformanceMetric.skill_id == skill_id,
                PerformanceMetric.measured_at >= start_date
            )
        ).all()

        if not metrics:
            return {}

        execution_times = [m.execution_time for m in metrics]
        success_count = sum(1 for m in metrics if m.success)

        return {
            "period_days": days,
            "total_executions": len(metrics),
            "success_rate": success_count / len(metrics),
            "avg_execution_time": np.mean(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "std_execution_time": np.std(execution_times),
            "p50_execution_time": np.percentile(execution_times, 50),
            "p95_execution_time": np.percentile(execution_times, 95),
            "p99_execution_time": np.percentile(execution_times, 99)
        }
