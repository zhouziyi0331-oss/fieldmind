"""
指标系统服务

提供指标快照、事件追踪、项目指标聚合和价值展示功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, between
from sqlalchemy.orm import selectinload

from app.models.metrics import (
    MetricsSnapshot,
    MetricsEvent,
    ProjectMetrics,
    WorkloadCalculation,
    ValueExhibition
)


class MetricsService:
    """指标服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== 指标快照 ====================

    async def create_snapshot(
        self,
        project_id: int,
        metric_type: str,
        metric_name: str,
        value: float,
        unit: str,
        dimensions: Optional[Dict[str, Any]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> MetricsSnapshot:
        """
        创建指标快照

        Args:
            project_id: 项目ID
            metric_type: 指标类型（performance, quality, usage, progress等）
            metric_name: 指标名称（document_count, entity_count等）
            value: 指标值
            unit: 单位（count, percentage, seconds等）
            dimensions: 维度信息（如按文档类型、用户等分组）
            extra_metadata: 额外元数据

        Returns:
            创建的快照
        """
        snapshot = MetricsSnapshot(
            project_id=project_id,
            metric_type=metric_type,
            metric_name=metric_name,
            value=value,
            unit=unit,
            dimensions=dimensions or {},
            extra_metadata=extra_metadata or {},
            captured_at=datetime.utcnow()
        )

        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)

        return snapshot

    async def get_latest_snapshots(
        self,
        project_id: int,
        metric_type: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: int = 50
    ) -> List[MetricsSnapshot]:
        """
        获取最新的指标快照

        Args:
            project_id: 项目ID
            metric_type: 可选，筛选指标类型
            metric_name: 可选，筛选指标名称
            limit: 返回数量限制

        Returns:
            快照列表
        """
        conditions = [MetricsSnapshot.project_id == project_id]
        if metric_type:
            conditions.append(MetricsSnapshot.metric_type == metric_type)
        if metric_name:
            conditions.append(MetricsSnapshot.metric_name == metric_name)

        result = await self.db.execute(
            select(MetricsSnapshot)
            .where(and_(*conditions))
            .order_by(desc(MetricsSnapshot.captured_at))
            .limit(limit)
        )

        return result.scalars().all()

    async def get_metric_trend(
        self,
        project_id: int,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        获取指标趋势（时间序列）

        Args:
            project_id: 项目ID
            metric_name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
            interval_minutes: 聚合间隔（分钟）

        Returns:
            趋势数据列表
        """
        result = await self.db.execute(
            select(MetricsSnapshot)
            .where(
                and_(
                    MetricsSnapshot.project_id == project_id,
                    MetricsSnapshot.metric_name == metric_name,
                    between(MetricsSnapshot.captured_at, start_time, end_time)
                )
            )
            .order_by(MetricsSnapshot.captured_at)
        )
        snapshots = result.scalars().all()

        # 按时间间隔聚合
        trend_data = []
        current_bucket = None
        bucket_values = []

        for snapshot in snapshots:
            bucket_time = snapshot.captured_at.replace(
                minute=(snapshot.captured_at.minute // interval_minutes) * interval_minutes,
                second=0,
                microsecond=0
            )

            if current_bucket != bucket_time:
                if bucket_values:
                    trend_data.append({
                        "timestamp": current_bucket.isoformat(),
                        "value": sum(bucket_values) / len(bucket_values),
                        "count": len(bucket_values),
                        "min": min(bucket_values),
                        "max": max(bucket_values)
                    })
                current_bucket = bucket_time
                bucket_values = []

            bucket_values.append(snapshot.value)

        # 处理最后一个桶
        if bucket_values:
            trend_data.append({
                "timestamp": current_bucket.isoformat(),
                "value": sum(bucket_values) / len(bucket_values),
                "count": len(bucket_values),
                "min": min(bucket_values),
                "max": max(bucket_values)
            })

        return trend_data

    # ==================== 指标事件 ====================

    async def record_event(
        self,
        project_id: int,
        event_type: str,
        event_name: str,
        actor_type: str,
        actor_id: Optional[int] = None,
        impact_score: Optional[float] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> MetricsEvent:
        """
        记录指标事件

        Args:
            project_id: 项目ID
            event_type: 事件类型（user_action, system_event, milestone等）
            event_name: 事件名称（document_uploaded, analysis_completed等）
            actor_type: 操作者类型（user, ai, system）
            actor_id: 操作者ID
            impact_score: 影响分数（0-100）
            event_data: 事件数据

        Returns:
            创建的事件记录
        """
        event = MetricsEvent(
            project_id=project_id,
            event_type=event_type,
            event_name=event_name,
            actor_type=actor_type,
            actor_id=actor_id,
            impact_score=impact_score,
            event_data=event_data or {},
            occurred_at=datetime.utcnow()
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        return event

    async def get_events(
        self,
        project_id: int,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MetricsEvent]:
        """
        查询指标事件

        Args:
            project_id: 项目ID
            event_type: 可选，筛选事件类型
            start_time: 可选，开始时间
            end_time: 可选，结束时间
            limit: 返回数量限制

        Returns:
            事件列表
        """
        conditions = [MetricsEvent.project_id == project_id]
        if event_type:
            conditions.append(MetricsEvent.event_type == event_type)
        if start_time:
            conditions.append(MetricsEvent.occurred_at >= start_time)
        if end_time:
            conditions.append(MetricsEvent.occurred_at <= end_time)

        result = await self.db.execute(
            select(MetricsEvent)
            .where(and_(*conditions))
            .order_by(desc(MetricsEvent.occurred_at))
            .limit(limit)
        )

        return result.scalars().all()

    async def get_event_statistics(
        self,
        project_id: int,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        获取事件统计

        Args:
            project_id: 项目ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计数据
        """
        # 按事件类型统计
        result = await self.db.execute(
            select(
                MetricsEvent.event_type,
                func.count(MetricsEvent.id).label('count'),
                func.avg(MetricsEvent.impact_score).label('avg_impact')
            )
            .where(
                and_(
                    MetricsEvent.project_id == project_id,
                    between(MetricsEvent.occurred_at, start_time, end_time)
                )
            )
            .group_by(MetricsEvent.event_type)
        )
        by_type = {row[0]: {"count": row[1], "avg_impact": row[2]} for row in result.all()}

        # 按操作者类型统计
        result = await self.db.execute(
            select(
                MetricsEvent.actor_type,
                func.count(MetricsEvent.id).label('count')
            )
            .where(
                and_(
                    MetricsEvent.project_id == project_id,
                    between(MetricsEvent.occurred_at, start_time, end_time)
                )
            )
            .group_by(MetricsEvent.actor_type)
        )
        by_actor = {row[0]: row[1] for row in result.all()}

        # 总事件数
        result = await self.db.execute(
            select(func.count(MetricsEvent.id))
            .where(
                and_(
                    MetricsEvent.project_id == project_id,
                    between(MetricsEvent.occurred_at, start_time, end_time)
                )
            )
        )
        total_events = result.scalar() or 0

        return {
            "total_events": total_events,
            "by_type": by_type,
            "by_actor": by_actor,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            }
        }

    # ==================== 项目指标聚合 ====================

    async def update_project_metrics(
        self,
        project_id: int,
        document_count: Optional[int] = None,
        entity_count: Optional[int] = None,
        relationship_count: Optional[int] = None,
        analysis_count: Optional[int] = None,
        total_storage_mb: Optional[float] = None,
        ai_calls_count: Optional[int] = None,
        avg_processing_time: Optional[float] = None
    ) -> ProjectMetrics:
        """
        更新项目聚合指标

        Args:
            project_id: 项目ID
            document_count: 文档数
            entity_count: 实体数
            relationship_count: 关系数
            analysis_count: 分析次数
            total_storage_mb: 总存储大小（MB）
            ai_calls_count: AI调用次数
            avg_processing_time: 平均处理时间（秒）

        Returns:
            更新后的项目指标
        """
        # 查询现有记录
        result = await self.db.execute(
            select(ProjectMetrics).where(ProjectMetrics.project_id == project_id)
        )
        metrics = result.scalar_one_or_none()

        if not metrics:
            # 创建新记录
            metrics = ProjectMetrics(
                project_id=project_id,
                document_count=document_count or 0,
                entity_count=entity_count or 0,
                relationship_count=relationship_count or 0,
                analysis_count=analysis_count or 0,
                total_storage_mb=total_storage_mb or 0.0,
                ai_calls_count=ai_calls_count or 0,
                avg_processing_time=avg_processing_time or 0.0,
                last_activity_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(metrics)
        else:
            # 更新现有记录
            if document_count is not None:
                metrics.document_count = document_count
            if entity_count is not None:
                metrics.entity_count = entity_count
            if relationship_count is not None:
                metrics.relationship_count = relationship_count
            if analysis_count is not None:
                metrics.analysis_count = analysis_count
            if total_storage_mb is not None:
                metrics.total_storage_mb = total_storage_mb
            if ai_calls_count is not None:
                metrics.ai_calls_count = ai_calls_count
            if avg_processing_time is not None:
                metrics.avg_processing_time = avg_processing_time

            metrics.last_activity_at = datetime.utcnow()
            metrics.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(metrics)

        return metrics

    async def get_project_metrics(self, project_id: int) -> Optional[ProjectMetrics]:
        """
        获取项目聚合指标

        Args:
            project_id: 项目ID

        Returns:
            项目指标
        """
        result = await self.db.execute(
            select(ProjectMetrics).where(ProjectMetrics.project_id == project_id)
        )
        return result.scalar_one_or_none()

    async def increment_metric(
        self,
        project_id: int,
        metric_name: str,
        increment: int = 1
    ) -> ProjectMetrics:
        """
        增量更新指标

        Args:
            project_id: 项目ID
            metric_name: 指标名称（document_count, entity_count等）
            increment: 增量值

        Returns:
            更新后的项目指标
        """
        metrics = await self.get_project_metrics(project_id)

        if not metrics:
            # 初始化
            kwargs = {metric_name: increment}
            return await self.update_project_metrics(project_id, **kwargs)

        # 增量更新
        current_value = getattr(metrics, metric_name, 0)
        kwargs = {metric_name: current_value + increment}
        return await self.update_project_metrics(project_id, **kwargs)

    # ==================== 工作量计算 ====================

    async def calculate_workload(
        self,
        project_id: int,
        calculation_period_days: int = 7
    ) -> WorkloadCalculation:
        """
        计算工作量

        Args:
            project_id: 项目ID
            calculation_period_days: 计算周期（天数）

        Returns:
            工作量计算结果
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=calculation_period_days)

        # 统计各类操作次数
        result = await self.db.execute(
            select(
                MetricsEvent.event_name,
                func.count(MetricsEvent.id).label('count')
            )
            .where(
                and_(
                    MetricsEvent.project_id == project_id,
                    between(MetricsEvent.occurred_at, start_time, end_time)
                )
            )
            .group_by(MetricsEvent.event_name)
        )
        operation_counts = {row[0]: row[1] for row in result.all()}

        # 获取项目指标
        metrics = await self.get_project_metrics(project_id)

        # 计算工作量分数
        workload_score = self._calculate_workload_score(operation_counts, metrics)

        # 保存计算结果
        calculation = WorkloadCalculation(
            project_id=project_id,
            calculation_period_days=calculation_period_days,
            operation_counts=operation_counts,
            workload_score=workload_score,
            calculated_at=datetime.utcnow()
        )

        self.db.add(calculation)
        await self.db.commit()
        await self.db.refresh(calculation)

        return calculation

    def _calculate_workload_score(
        self,
        operation_counts: Dict[str, int],
        metrics: Optional[ProjectMetrics]
    ) -> float:
        """计算工作量分数（0-100）"""
        score = 0.0

        # 基于操作次数
        total_operations = sum(operation_counts.values())
        score += min(total_operations * 0.5, 40)  # 最多40分

        # 基于项目指标
        if metrics:
            score += min(metrics.document_count * 2, 20)  # 最多20分
            score += min(metrics.entity_count * 0.05, 20)  # 最多20分
            score += min(metrics.analysis_count * 1, 20)  # 最多20分

        return min(score, 100)

    async def get_workload_history(
        self,
        project_id: int,
        limit: int = 30
    ) -> List[WorkloadCalculation]:
        """
        获取工作量历史

        Args:
            project_id: 项目ID
            limit: 返回数量限制

        Returns:
            工作量计算历史
        """
        result = await self.db.execute(
            select(WorkloadCalculation)
            .where(WorkloadCalculation.project_id == project_id)
            .order_by(desc(WorkloadCalculation.calculated_at))
            .limit(limit)
        )
        return result.scalars().all()

    # ==================== 价值展示 ====================

    async def create_value_exhibition(
        self,
        project_id: int,
        exhibition_type: str,
        title: str,
        description: str,
        metrics_summary: Dict[str, Any],
        visual_data: Optional[Dict[str, Any]] = None,
        created_by: Optional[int] = None
    ) -> ValueExhibition:
        """
        创建价值展示

        Args:
            project_id: 项目ID
            exhibition_type: 展示类型（achievement, insight, impact等）
            title: 标题
            description: 描述
            metrics_summary: 指标摘要
            visual_data: 可视化数据
            created_by: 创建者ID

        Returns:
            创建的价值展示
        """
        exhibition = ValueExhibition(
            project_id=project_id,
            exhibition_type=exhibition_type,
            title=title,
            description=description,
            metrics_summary=metrics_summary,
            visual_data=visual_data or {},
            created_by=created_by,
            created_at=datetime.utcnow()
        )

        self.db.add(exhibition)
        await self.db.commit()
        await self.db.refresh(exhibition)

        return exhibition

    async def list_value_exhibitions(
        self,
        project_id: int,
        exhibition_type: Optional[str] = None,
        limit: int = 20
    ) -> List[ValueExhibition]:
        """
        查询价值展示列表

        Args:
            project_id: 项目ID
            exhibition_type: 可选，筛选展示类型
            limit: 返回数量限制

        Returns:
            价值展示列表
        """
        conditions = [ValueExhibition.project_id == project_id]
        if exhibition_type:
            conditions.append(ValueExhibition.exhibition_type == exhibition_type)

        result = await self.db.execute(
            select(ValueExhibition)
            .where(and_(*conditions))
            .order_by(desc(ValueExhibition.created_at))
            .limit(limit)
        )

        return result.scalars().all()
