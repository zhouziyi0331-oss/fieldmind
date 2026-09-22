"""
后台学习服务

管理异步的持续学习任务（GEPA机制）
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func, or_
import asyncio

from app.models.background_learning import (
    BackgroundLearningTask,
    LearningCheckpoint,
    LearningSchedule,
    LearningInsight,
    LearningTaskType,
    LearningTaskStatus,
    LearningTaskPriority
)
from app.models.execution_record import ExecutionRecord
from app.models.pattern_library import PatternLibrary


class BackgroundLearner:
    """后台学习器 - 管理异步学习任务"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 任务创建 ====================

    def create_learning_task(
        self,
        project_id: int,
        task_type: LearningTaskType,
        task_name: str,
        task_description: str,
        task_config: Dict[str, Any],
        priority: LearningTaskPriority = LearningTaskPriority.MEDIUM,
        scheduled_at: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> BackgroundLearningTask:
        """
        创建学习任务

        Args:
            project_id: 项目ID
            task_type: 任务类型
            task_name: 任务名称
            task_description: 任务描述
            task_config: 任务配置
            priority: 优先级
            scheduled_at: 调度时间
            user_id: 触发用户ID

        Returns:
            创建的任务
        """
        task = BackgroundLearningTask(
            task_type=task_type,
            task_name=task_name,
            task_description=task_description,
            project_id=project_id,
            triggered_by_user_id=user_id,
            task_config=task_config,
            priority=priority,
            scheduled_at=scheduled_at or datetime.utcnow(),
            status=LearningTaskStatus.SCHEDULED
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    # ==================== 任务执行 ====================

    def execute_task(
        self,
        task_id: str
    ) -> BackgroundLearningTask:
        """
        执行学习任务

        Args:
            task_id: 任务ID

        Returns:
            更新后的任务
        """
        task = self.db.query(BackgroundLearningTask).filter(
            BackgroundLearningTask.id == task_id
        ).first()

        if not task:
            raise ValueError(f"学习任务 {task_id} 不存在")

        # 更新状态
        task.status = LearningTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        self.db.commit()

        try:
            # 根据任务类型执行不同的学习逻辑
            if task.task_type == LearningTaskType.PATTERN_MINING:
                results = self._execute_pattern_mining(task)
            elif task.task_type == LearningTaskType.SKILL_OPTIMIZATION:
                results = self._execute_skill_optimization(task)
            elif task.task_type == LearningTaskType.KNOWLEDGE_CONSOLIDATION:
                results = self._execute_knowledge_consolidation(task)
            elif task.task_type == LearningTaskType.PERFORMANCE_ANALYSIS:
                results = self._execute_performance_analysis(task)
            elif task.task_type == LearningTaskType.ANOMALY_DETECTION:
                results = self._execute_anomaly_detection(task)
            else:
                raise ValueError(f"不支持的任务类型: {task.task_type}")

            # 更新成功状态
            task.status = LearningTaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
            task.learning_results = results
            task.progress_percentage = 100.0

        except Exception as e:
            # 更新失败状态
            task.status = LearningTaskStatus.FAILED
            task.error_message = str(e)
            task.retry_count += 1

            # 如果未达到最大重试次数，重新调度
            if task.retry_count < task.max_retries:
                task.status = LearningTaskStatus.SCHEDULED
                task.scheduled_at = datetime.utcnow() + timedelta(minutes=30)

        self.db.commit()
        self.db.refresh(task)

        return task

    def _execute_pattern_mining(
        self,
        task: BackgroundLearningTask
    ) -> Dict[str, Any]:
        """执行模式挖掘"""
        config = task.task_config

        # 获取数据范围
        data_range = config.get("data_range", {})
        start_date = datetime.fromisoformat(data_range.get("start_date", (datetime.utcnow() - timedelta(days=30)).isoformat()))
        end_date = datetime.fromisoformat(data_range.get("end_date", datetime.utcnow().isoformat()))

        # 查询执行记录
        executions = self.db.query(ExecutionRecord).filter(
            and_(
                ExecutionRecord.project_id == task.project_id,
                ExecutionRecord.completed_at >= start_date,
                ExecutionRecord.completed_at <= end_date
            )
        ).all()

        # 创建检查点
        self._create_checkpoint(task, "data_loaded", {
            "executions_count": len(executions),
            "processed": 0
        })

        # 简单的模式识别逻辑
        patterns_found = []
        for i, exec_record in enumerate(executions):
            # 更新进度
            task.progress_percentage = (i / len(executions)) * 100
            task.progress_message = f"分析执行记录 {i+1}/{len(executions)}"
            self.db.commit()

            # 这里应该调用实际的模式识别算法
            # 简化示例：检查是否有重复的步骤序列
            if exec_record.execution_steps and len(exec_record.execution_steps) > 0:
                patterns_found.append({
                    "execution_id": exec_record.id,
                    "pattern": "detected_sequence",
                    "confidence": 0.8
                })

        # 生成洞察
        if patterns_found:
            insight = self._create_insight(
                task,
                "pattern_discovery",
                f"发现 {len(patterns_found)} 个潜在模式",
                f"通过分析 {len(executions)} 次执行，识别出重复的操作模式",
                {
                    "patterns_count": len(patterns_found),
                    "sample_patterns": patterns_found[:5]
                }
            )

        return {
            "patterns_discovered": len(patterns_found),
            "insights_generated": 1 if patterns_found else 0,
            "data_processed": {
                "executions_analyzed": len(executions),
                "time_range": f"{start_date.date()} to {end_date.date()}"
            }
        }

    def _execute_skill_optimization(
        self,
        task: BackgroundLearningTask
    ) -> Dict[str, Any]:
        """执行技能优化分析"""
        # 查找性能不佳的技能
        from app.models.generated_skill import GeneratedSkill

        skills = self.db.query(GeneratedSkill).filter(
            and_(
                GeneratedSkill.project_id == task.project_id,
                GeneratedSkill.is_active == True
            )
        ).all()

        optimizations_proposed = 0
        for skill in skills:
            # 检查是否需要优化
            if skill.success_count > 0:
                success_rate = skill.success_count / (skill.success_count + skill.failure_count)
                if success_rate < 0.8:
                    # 生成优化建议
                    self._create_insight(
                        task,
                        "skill_optimization",
                        f"技能 {skill.skill_name} 需要优化",
                        f"成功率仅为 {success_rate:.1%}，建议进行优化",
                        {
                            "skill_id": skill.id,
                            "current_success_rate": success_rate,
                            "target_success_rate": 0.9
                        }
                    )
                    optimizations_proposed += 1

        return {
            "skills_analyzed": len(skills),
            "optimizations_proposed": optimizations_proposed
        }

    def _execute_knowledge_consolidation(
        self,
        task: BackgroundLearningTask
    ) -> Dict[str, Any]:
        """执行知识整合"""
        # 整合分散的模式和技能
        patterns = self.db.query(PatternLibrary).filter(
            PatternLibrary.project_id == task.project_id
        ).all()

        # 查找可以合并的模式
        consolidated = 0
        for i, pattern1 in enumerate(patterns):
            for pattern2 in patterns[i+1:]:
                # 简单的相似度检查
                if self._patterns_similar(pattern1, pattern2):
                    consolidated += 1

        return {
            "patterns_reviewed": len(patterns),
            "consolidations_performed": consolidated
        }

    def _execute_performance_analysis(
        self,
        task: BackgroundLearningTask
    ) -> Dict[str, Any]:
        """执行性能分析"""
        from app.models.skill_optimization import PerformanceMetric

        # 分析最近的性能数据
        metrics = self.db.query(PerformanceMetric).filter(
            and_(
                PerformanceMetric.project_id == task.project_id,
                PerformanceMetric.measured_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).all()

        # 识别性能问题
        slow_executions = [m for m in metrics if m.execution_time > 5.0]

        if slow_executions:
            self._create_insight(
                task,
                "performance_issue",
                f"发现 {len(slow_executions)} 次慢执行",
                f"有 {len(slow_executions)} 次执行超过5秒",
                {
                    "slow_count": len(slow_executions),
                    "total_count": len(metrics)
                }
            )

        return {
            "metrics_analyzed": len(metrics),
            "issues_detected": len(slow_executions)
        }

    def _execute_anomaly_detection(
        self,
        task: BackgroundLearningTask
    ) -> Dict[str, Any]:
        """执行异常检测"""
        # 检测异常执行模式
        executions = self.db.query(ExecutionRecord).filter(
            and_(
                ExecutionRecord.project_id == task.project_id,
                ExecutionRecord.completed_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).all()

        anomalies = []
        for exec_record in executions:
            # 检测异常
            if exec_record.duration_seconds and exec_record.duration_seconds > 60:
                anomalies.append({
                    "execution_id": exec_record.id,
                    "anomaly_type": "timeout",
                    "severity": "high"
                })

        if anomalies:
            self._create_insight(
                task,
                "anomaly_detected",
                f"检测到 {len(anomalies)} 个异常",
                f"发现执行时间异常的情况",
                {
                    "anomalies": anomalies[:10]
                }
            )

        return {
            "executions_checked": len(executions),
            "anomalies_detected": len(anomalies)
        }

    def _patterns_similar(
        self,
        pattern1: PatternLibrary,
        pattern2: PatternLibrary
    ) -> bool:
        """判断两个模式是否相似"""
        # 简单的相似度判断
        return pattern1.pattern_type == pattern2.pattern_type

    # ==================== 辅助方法 ====================

    def _create_checkpoint(
        self,
        task: BackgroundLearningTask,
        checkpoint_name: str,
        state: Dict[str, Any]
    ):
        """创建检查点"""
        checkpoint = LearningCheckpoint(
            task_id=task.id,
            project_id=task.project_id,
            checkpoint_name=checkpoint_name,
            state_snapshot=state
        )
        self.db.add(checkpoint)
        self.db.commit()

    def _create_insight(
        self,
        task: BackgroundLearningTask,
        insight_type: str,
        title: str,
        description: str,
        data: Dict[str, Any]
    ) -> LearningInsight:
        """创建洞察"""
        insight = LearningInsight(
            task_id=task.id,
            project_id=task.project_id,
            insight_type=insight_type,
            insight_title=title,
            insight_description=description,
            insight_data=data,
            importance_score=0.7,
            actionability_score=0.8,
            confidence_score=0.75
        )
        self.db.add(insight)
        self.db.commit()
        return insight

    # ==================== 调度管理 ====================

    def create_schedule(
        self,
        project_id: int,
        schedule_name: str,
        schedule_description: str,
        task_type: LearningTaskType,
        cron_expression: str,
        task_config_template: Dict[str, Any],
        priority: LearningTaskPriority = LearningTaskPriority.MEDIUM
    ) -> LearningSchedule:
        """创建学习调度"""
        schedule = LearningSchedule(
            schedule_name=schedule_name,
            schedule_description=schedule_description,
            project_id=project_id,
            task_type=task_type,
            cron_expression=cron_expression,
            task_config_template=task_config_template,
            priority=priority,
            is_active=True
        )

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        return schedule

    def get_due_schedules(self) -> List[LearningSchedule]:
        """获取到期的调度"""
        now = datetime.utcnow()

        schedules = self.db.query(LearningSchedule).filter(
            and_(
                LearningSchedule.is_active == True,
                or_(
                    LearningSchedule.next_run_at <= now,
                    LearningSchedule.next_run_at == None
                )
            )
        ).all()

        return schedules

    # ==================== 查询接口 ====================

    def get_tasks(
        self,
        project_id: int,
        status: Optional[LearningTaskStatus] = None,
        task_type: Optional[LearningTaskType] = None,
        limit: int = 100
    ) -> List[BackgroundLearningTask]:
        """获取学习任务列表"""
        query = self.db.query(BackgroundLearningTask).filter(
            BackgroundLearningTask.project_id == project_id
        )

        if status:
            query = query.filter(BackgroundLearningTask.status == status)

        if task_type:
            query = query.filter(BackgroundLearningTask.task_type == task_type)

        return query.order_by(
            desc(BackgroundLearningTask.created_at)
        ).limit(limit).all()

    def get_insights(
        self,
        project_id: int,
        insight_type: Optional[str] = None,
        is_reviewed: Optional[bool] = None,
        min_importance: float = 0.0
    ) -> List[LearningInsight]:
        """获取学习洞察列表"""
        query = self.db.query(LearningInsight).filter(
            and_(
                LearningInsight.project_id == project_id,
                LearningInsight.importance_score >= min_importance
            )
        )

        if insight_type:
            query = query.filter(LearningInsight.insight_type == insight_type)

        if is_reviewed is not None:
            query = query.filter(LearningInsight.is_reviewed == is_reviewed)

        return query.order_by(
            desc(LearningInsight.importance_score),
            desc(LearningInsight.discovered_at)
        ).all()
