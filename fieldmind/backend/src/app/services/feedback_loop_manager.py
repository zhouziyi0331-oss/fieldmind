"""
反馈闭环服务

管理完整的执行-反馈-学习-改进循环
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func
import json

from app.models.feedback_loop import (
    FeedbackLoop,
    FeedbackAnalysis,
    ImprovementTask,
    LoopMetrics,
    FeedbackType,
    FeedbackSentiment,
    ImprovementPriority
)
from app.models.execution_record import ExecutionRecord


class FeedbackLoopManager:
    """反馈闭环管理器 - 管理完整的学习循环"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 闭环创建 ====================

    def start_feedback_loop(
        self,
        execution_id: str,
        project_id: int,
        user_id: int,
        skill_id: Optional[str] = None,
        pattern_id: Optional[str] = None
    ) -> FeedbackLoop:
        """
        启动反馈闭环

        Args:
            execution_id: 执行记录ID
            project_id: 项目ID
            user_id: 用户ID
            skill_id: 可选，技能ID
            pattern_id: 可选，模式ID

        Returns:
            反馈闭环记录
        """
        # 获取执行记录
        execution = self.db.query(ExecutionRecord).filter(
            ExecutionRecord.id == execution_id
        ).first()

        if not execution:
            raise ValueError(f"执行记录 {execution_id} 不存在")

        # 提取执行上下文和结果
        execution_context = {
            "input": execution.input_data,
            "parameters": {},
            "environment": {
                "execution_type": execution.execution_type.value,
                "started_at": execution.started_at.isoformat()
            }
        }

        execution_result = {
            "output": execution.output_data,
            "status": execution.status.value,
            "duration": execution.duration_seconds,
            "quality_score": execution.quality_score
        }

        # 创建闭环记录
        loop = FeedbackLoop(
            execution_id=execution_id,
            skill_id=skill_id,
            pattern_id=pattern_id,
            project_id=project_id,
            user_id=user_id,
            execution_context=execution_context,
            execution_result=execution_result,
            feedback_collected={},
            feedback_sentiment=FeedbackSentiment.NEUTRAL,
            feedback_score=0.5,
            execution_started_at=execution.started_at or datetime.utcnow(),
            completion_percentage=0.25  # 执行阶段完成
        )

        self.db.add(loop)
        self.db.commit()
        self.db.refresh(loop)

        return loop

    # ==================== 反馈收集 ====================

    def collect_feedback(
        self,
        loop_id: str,
        user_rating: Optional[int] = None,
        user_comment: Optional[str] = None,
        automatic_metrics: Optional[Dict[str, Any]] = None
    ) -> FeedbackLoop:
        """
        收集反馈

        Args:
            loop_id: 闭环ID
            user_rating: 用户评分（1-5）
            user_comment: 用户评论
            automatic_metrics: 自动收集的指标

        Returns:
            更新后的闭环记录
        """
        loop = self.db.query(FeedbackLoop).filter(
            FeedbackLoop.id == loop_id
        ).first()

        if not loop:
            raise ValueError(f"反馈闭环 {loop_id} 不存在")

        # 收集反馈
        feedback = {}
        if user_rating:
            feedback["user_rating"] = user_rating
        if user_comment:
            feedback["user_comment"] = user_comment
        if automatic_metrics:
            feedback["automatic_metrics"] = automatic_metrics

        loop.feedback_collected = feedback
        loop.feedback_received_at = datetime.utcnow()

        # 分析反馈情感
        sentiment, score = self._analyze_feedback_sentiment(feedback)
        loop.feedback_sentiment = sentiment
        loop.feedback_score = score

        loop.completion_percentage = 0.5  # 反馈阶段完成

        self.db.commit()
        self.db.refresh(loop)

        # 创建反馈分析
        self._create_feedback_analysis(loop)

        return loop

    def _analyze_feedback_sentiment(
        self,
        feedback: Dict[str, Any]
    ) -> Tuple[FeedbackSentiment, float]:
        """分析反馈情感"""
        score = 0.5  # 默认中性

        # 基于用户评分
        if "user_rating" in feedback:
            rating = feedback["user_rating"]
            score = rating / 5.0

            if rating >= 4:
                sentiment = FeedbackSentiment.POSITIVE
            elif rating <= 2:
                sentiment = FeedbackSentiment.NEGATIVE
            else:
                sentiment = FeedbackSentiment.NEUTRAL
        else:
            sentiment = FeedbackSentiment.NEUTRAL

        # 基于自动指标调整
        if "automatic_metrics" in feedback:
            metrics = feedback["automatic_metrics"]
            if "accuracy" in metrics:
                score = (score + metrics["accuracy"]) / 2

        return sentiment, score

    def _create_feedback_analysis(
        self,
        loop: FeedbackLoop
    ):
        """创建反馈分析"""
        # 情感分析
        sentiment_analysis = {
            "sentiment": loop.feedback_sentiment.value,
            "confidence": 0.8,
            "keywords": self._extract_keywords(
                loop.feedback_collected.get("user_comment", "")
            )
        }

        # 根本原因分析
        root_cause = self._analyze_root_cause(loop)

        # 影响评估
        impact = self._assess_impact(loop)

        # 可操作的洞察
        insights = self._generate_actionable_insights(loop, root_cause)

        analysis = FeedbackAnalysis(
            feedback_loop_id=loop.id,
            project_id=loop.project_id,
            feedback_type=FeedbackType.USER_RATING,
            feedback_source="user",
            sentiment_analysis=sentiment_analysis,
            root_cause_analysis=root_cause,
            impact_assessment=impact,
            actionable_insights=insights
        )

        self.db.add(analysis)
        self.db.commit()

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        if not text:
            return []

        # 简单的关键词提取（实际应该使用NLP）
        positive_keywords = ["好", "快", "准确", "有用", "满意", "excellent", "great", "fast", "accurate"]
        negative_keywords = ["慢", "错", "差", "失败", "不满", "slow", "wrong", "bad", "failed"]

        keywords = []
        text_lower = text.lower()

        for word in positive_keywords:
            if word in text_lower:
                keywords.append(word)

        for word in negative_keywords:
            if word in text_lower:
                keywords.append(word)

        return keywords

    def _analyze_root_cause(
        self,
        loop: FeedbackLoop
    ) -> Dict[str, Any]:
        """分析根本原因"""
        causes = []

        # 基于反馈分数
        if loop.feedback_score < 0.6:
            # 检查执行结果
            result = loop.execution_result
            if result.get("duration", 0) > 5:
                causes.append("执行时间过长")
            if result.get("quality_score", 1) < 0.7:
                causes.append("质量分数偏低")

        primary_cause = causes[0] if causes else "无明显问题"

        return {
            "primary_cause": primary_cause,
            "contributing_factors": causes[1:] if len(causes) > 1 else [],
            "recommendation": self._get_recommendation(primary_cause)
        }

    def _get_recommendation(self, cause: str) -> str:
        """根据原因生成建议"""
        recommendations = {
            "执行时间过长": "优化算法性能或使用缓存",
            "质量分数偏低": "改进输出质量或调整参数",
            "无明显问题": "保持当前方法"
        }
        return recommendations.get(cause, "需要进一步分析")

    def _assess_impact(
        self,
        loop: FeedbackLoop
    ) -> Dict[str, Any]:
        """评估影响"""
        severity = "low"
        if loop.feedback_score < 0.4:
            severity = "high"
        elif loop.feedback_score < 0.6:
            severity = "medium"

        return {
            "severity": severity,
            "affected_users": 1,
            "frequency": "single",
            "business_impact": severity
        }

    def _generate_actionable_insights(
        self,
        loop: FeedbackLoop,
        root_cause: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成可操作的洞察"""
        insights = []

        if loop.feedback_score < 0.7:
            insights.append({
                "insight": root_cause["primary_cause"],
                "action": root_cause["recommendation"],
                "priority": "high" if loop.feedback_score < 0.5 else "medium",
                "estimated_effort": "medium"
            })

        return insights

    # ==================== 学习阶段 ====================

    def perform_learning(
        self,
        loop_id: str
    ) -> FeedbackLoop:
        """
        执行学习阶段

        Args:
            loop_id: 闭环ID

        Returns:
            更新后的闭环记录
        """
        loop = self.db.query(FeedbackLoop).filter(
            FeedbackLoop.id == loop_id
        ).first()

        if not loop:
            raise ValueError(f"反馈闭环 {loop_id} 不存在")

        # 提取洞察
        insights = self._extract_insights(loop)
        loop.insights_learned = insights

        # 提取经验教训
        lessons = self._extract_lessons(loop, insights)
        loop.lessons_extracted = lessons

        loop.learning_completed_at = datetime.utcnow()
        loop.completion_percentage = 0.75  # 学习阶段完成

        self.db.commit()
        self.db.refresh(loop)

        return loop

    def _extract_insights(
        self,
        loop: FeedbackLoop
    ) -> Dict[str, Any]:
        """提取洞察"""
        insights = {
            "success_factors": [],
            "failure_factors": [],
            "patterns_identified": [],
            "correlations": {}
        }

        # 基于反馈分析成功/失败因素
        if loop.feedback_score >= 0.7:
            insights["success_factors"].append("高质量输出")
            if loop.execution_result.get("duration", 0) < 3:
                insights["success_factors"].append("快速执行")
        else:
            insights["failure_factors"].append("用户不满意")

        # 识别相关性
        result = loop.execution_result
        if result.get("duration"):
            if result["duration"] > 5:
                insights["correlations"]["execution_time"] = "long"
            else:
                insights["correlations"]["execution_time"] = "acceptable"

        return insights

    def _extract_lessons(
        self,
        loop: FeedbackLoop,
        insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取经验教训"""
        lessons = {
            "what_worked": [],
            "what_failed": [],
            "recommendations": []
        }

        # 基于洞察生成教训
        for factor in insights.get("success_factors", []):
            lessons["what_worked"].append(f"保持{factor}")

        for factor in insights.get("failure_factors", []):
            lessons["what_failed"].append(factor)
            lessons["recommendations"].append(f"改进{factor}")

        return lessons

    # ==================== 改进阶段 ====================

    def propose_improvements(
        self,
        loop_id: str
    ) -> FeedbackLoop:
        """
        提出改进建议

        Args:
            loop_id: 闭环ID

        Returns:
            更新后的闭环记录
        """
        loop = self.db.query(FeedbackLoop).filter(
            FeedbackLoop.id == loop_id
        ).first()

        if not loop:
            raise ValueError(f"反馈闭环 {loop_id} 不存在")

        # 生成改进建议
        improvements = self._generate_improvements(loop)
        loop.improvements_proposed = improvements
        loop.improvements_proposed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(loop)

        # 创建改进任务
        for improvement in improvements:
            self._create_improvement_task(loop, improvement)

        return loop

    def _generate_improvements(
        self,
        loop: FeedbackLoop
    ) -> List[Dict[str, Any]]:
        """生成改进建议"""
        improvements = []

        # 基于学习结果生成改进
        if loop.lessons_extracted:
            for rec in loop.lessons_extracted.get("recommendations", []):
                improvement_type = "quality"
                if "性能" in rec or "速度" in rec:
                    improvement_type = "performance"

                improvements.append({
                    "type": improvement_type,
                    "description": rec,
                    "expected_impact": "提升用户满意度",
                    "priority": "high" if loop.feedback_score < 0.5 else "medium"
                })

        return improvements

    def _create_improvement_task(
        self,
        loop: FeedbackLoop,
        improvement: Dict[str, Any]
    ):
        """创建改进任务"""
        priority_map = {
            "critical": ImprovementPriority.CRITICAL,
            "high": ImprovementPriority.HIGH,
            "medium": ImprovementPriority.MEDIUM,
            "low": ImprovementPriority.LOW
        }

        task = ImprovementTask(
            feedback_loop_id=loop.id,
            skill_id=loop.skill_id,
            project_id=loop.project_id,
            task_title=f"{improvement['type']}优化",
            task_description=improvement["description"],
            improvement_type=improvement["type"],
            priority=priority_map.get(improvement.get("priority", "medium"), ImprovementPriority.MEDIUM),
            expected_impact=improvement.get("expected_impact"),
            estimated_effort="medium"
        )

        self.db.add(task)
        self.db.commit()

    def complete_loop(
        self,
        loop_id: str
    ) -> FeedbackLoop:
        """
        完成闭环

        Args:
            loop_id: 闭环ID

        Returns:
            完成的闭环记录
        """
        loop = self.db.query(FeedbackLoop).filter(
            FeedbackLoop.id == loop_id
        ).first()

        if not loop:
            raise ValueError(f"反馈闭环 {loop_id} 不存在")

        loop.loop_completed = True
        loop.completion_percentage = 1.0
        loop.loop_closed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(loop)

        return loop

    # ==================== 查询接口 ====================

    def get_feedback_loops(
        self,
        project_id: int,
        completed: Optional[bool] = None,
        min_feedback_score: float = 0.0,
        limit: int = 100
    ) -> List[FeedbackLoop]:
        """获取反馈闭环列表"""
        query = self.db.query(FeedbackLoop).filter(
            and_(
                FeedbackLoop.project_id == project_id,
                FeedbackLoop.feedback_score >= min_feedback_score
            )
        )

        if completed is not None:
            query = query.filter(FeedbackLoop.loop_completed == completed)

        return query.order_by(desc(FeedbackLoop.created_at)).limit(limit).all()

    def get_improvement_tasks(
        self,
        project_id: int,
        status: Optional[str] = None,
        priority: Optional[ImprovementPriority] = None
    ) -> List[ImprovementTask]:
        """获取改进任务列表"""
        query = self.db.query(ImprovementTask).filter(
            ImprovementTask.project_id == project_id
        )

        if status:
            query = query.filter(ImprovementTask.status == status)

        if priority:
            query = query.filter(ImprovementTask.priority == priority)

        return query.order_by(
            ImprovementTask.priority,
            desc(ImprovementTask.created_at)
        ).all()

    def calculate_loop_metrics(
        self,
        project_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> LoopMetrics:
        """计算闭环指标"""
        loops = self.db.query(FeedbackLoop).filter(
            and_(
                FeedbackLoop.project_id == project_id,
                FeedbackLoop.created_at >= start_date,
                FeedbackLoop.created_at <= end_date
            )
        ).all()

        completed_loops = [l for l in loops if l.loop_completed]

        # 计算平均闭环时长
        avg_duration = None
        if completed_loops:
            durations = []
            for loop in completed_loops:
                if loop.loop_closed_at and loop.execution_started_at:
                    duration = (loop.loop_closed_at - loop.execution_started_at).total_seconds() / 3600
                    durations.append(duration)
            if durations:
                avg_duration = sum(durations) / len(durations)

        # 统计反馈
        positive_count = sum(1 for l in loops if l.feedback_sentiment == FeedbackSentiment.POSITIVE)
        negative_count = sum(1 for l in loops if l.feedback_sentiment == FeedbackSentiment.NEGATIVE)

        metrics = LoopMetrics(
            project_id=project_id,
            period_start=start_date,
            period_end=end_date,
            total_loops=len(loops),
            completed_loops=len(completed_loops),
            avg_loop_duration_hours=avg_duration,
            total_feedback_received=len([l for l in loops if l.feedback_received_at]),
            positive_feedback_count=positive_count,
            negative_feedback_count=negative_count,
            avg_feedback_score=sum(l.feedback_score for l in loops) / len(loops) if loops else None
        )

        self.db.add(metrics)
        self.db.commit()
        self.db.refresh(metrics)

        return metrics
