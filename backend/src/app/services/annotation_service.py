"""
用户标注服务

提供用户对数据的标注、分类和质量反馈功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from app.models.user_engagement import UserAnnotation, AnnotationType


class AnnotationService:
    """用户标注服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def create_annotation(
        self,
        user_id: int,
        project_id: int,
        target_type: str,
        target_id: int,
        annotation_type: AnnotationType,
        annotation_content: Dict[str, Any],
        confidence: float = 1.0
    ) -> UserAnnotation:
        """
        创建标注

        Args:
            user_id: 用户ID
            project_id: 项目ID
            target_type: 标注目标类型（document, entity, relationship等）
            target_id: 标注目标ID
            annotation_type: 标注类型
            annotation_content: 标注内容
            confidence: 置信度（0-1）

        Returns:
            创建的标注
        """
        annotation = UserAnnotation(
            user_id=user_id,
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            annotation_type=annotation_type,
            annotation_content=annotation_content,
            confidence=confidence,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(annotation)
        self.db.commit()
        self.db.refresh(annotation)

        return annotation

    def get_annotations(
        self,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        annotation_type: Optional[AnnotationType] = None,
        limit: int = 100
    ) -> List[UserAnnotation]:
        """
        获取标注列表

        Args:
            user_id: 可选，用户ID
            project_id: 可选，项目ID
            target_type: 可选，目标类型
            target_id: 可选，目标ID
            annotation_type: 可选，标注类型
            limit: 返回数量

        Returns:
            标注列表
        """
        query = self.db.query(UserAnnotation)

        if user_id:
            query = query.filter(UserAnnotation.user_id == user_id)
        if project_id:
            query = query.filter(UserAnnotation.project_id == project_id)
        if target_type:
            query = query.filter(UserAnnotation.target_type == target_type)
        if target_id:
            query = query.filter(UserAnnotation.target_id == target_id)
        if annotation_type:
            query = query.filter(UserAnnotation.annotation_type == annotation_type)

        annotations = query.order_by(
            desc(UserAnnotation.created_at)
        ).limit(limit).all()

        return annotations

    def get_annotation_by_id(
        self,
        annotation_id: int
    ) -> Optional[UserAnnotation]:
        """
        根据ID获取标注

        Args:
            annotation_id: 标注ID

        Returns:
            标注对象
        """
        return self.db.query(UserAnnotation).filter(
            UserAnnotation.id == annotation_id
        ).first()

    def update_annotation(
        self,
        annotation_id: int,
        annotation_content: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None
    ) -> UserAnnotation:
        """
        更新标注

        Args:
            annotation_id: 标注ID
            annotation_content: 可选，新的标注内容
            confidence: 可选，新的置信度

        Returns:
            更新后的标注
        """
        annotation = self.get_annotation_by_id(annotation_id)

        if not annotation:
            raise ValueError(f"标注 {annotation_id} 不存在")

        if annotation_content is not None:
            annotation.annotation_content = annotation_content

        if confidence is not None:
            annotation.confidence = max(0.0, min(1.0, confidence))

        annotation.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(annotation)

        return annotation

    def delete_annotation(
        self,
        annotation_id: int,
        user_id: int
    ) -> bool:
        """
        删除标注

        Args:
            annotation_id: 标注ID
            user_id: 用户ID（验证权限）

        Returns:
            是否成功删除
        """
        annotation = self.db.query(UserAnnotation).filter(
            and_(
                UserAnnotation.id == annotation_id,
                UserAnnotation.user_id == user_id
            )
        ).first()

        if not annotation:
            return False

        self.db.delete(annotation)
        self.db.commit()

        return True

    def get_annotations_for_target(
        self,
        target_type: str,
        target_id: int,
        project_id: Optional[int] = None
    ) -> List[UserAnnotation]:
        """
        获取特定目标的所有标注

        Args:
            target_type: 目标类型
            target_id: 目标ID
            project_id: 可选，项目ID

        Returns:
            标注列表
        """
        query = self.db.query(UserAnnotation).filter(
            and_(
                UserAnnotation.target_type == target_type,
                UserAnnotation.target_id == target_id
            )
        )

        if project_id:
            query = query.filter(UserAnnotation.project_id == project_id)

        return query.order_by(desc(UserAnnotation.created_at)).all()

    def get_annotation_statistics(
        self,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取标注统计

        Args:
            project_id: 项目ID
            days: 统计天数

        Returns:
            统计数据
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        annotations = self.db.query(UserAnnotation).filter(
            and_(
                UserAnnotation.project_id == project_id,
                UserAnnotation.created_at >= start_date
            )
        ).all()

        # 按类型统计
        type_counts = {}
        for ann in annotations:
            ann_type = ann.annotation_type.value
            type_counts[ann_type] = type_counts.get(ann_type, 0) + 1

        # 按目标类型统计
        target_counts = {}
        for ann in annotations:
            target_type = ann.target_type
            target_counts[target_type] = target_counts.get(target_type, 0) + 1

        # 计算平均置信度
        avg_confidence = (
            sum(ann.confidence for ann in annotations) / len(annotations)
            if annotations else 0
        )

        # 按用户统计
        user_counts = {}
        for ann in annotations:
            user_id = ann.user_id
            user_counts[user_id] = user_counts.get(user_id, 0) + 1

        return {
            "period_days": days,
            "total_annotations": len(annotations),
            "by_annotation_type": type_counts,
            "by_target_type": target_counts,
            "avg_confidence": round(avg_confidence, 2),
            "by_user": user_counts,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }

    def get_user_annotation_summary(
        self,
        user_id: int,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户标注摘要

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 统计天数

        Returns:
            用户标注摘要
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        annotations = self.db.query(UserAnnotation).filter(
            and_(
                UserAnnotation.user_id == user_id,
                UserAnnotation.project_id == project_id,
                UserAnnotation.created_at >= start_date
            )
        ).all()

        # 按类型统计
        type_counts = {}
        for ann in annotations:
            ann_type = ann.annotation_type.value
            type_counts[ann_type] = type_counts.get(ann_type, 0) + 1

        return {
            "period_days": days,
            "total_annotations": len(annotations),
            "by_type": type_counts,
            "avg_confidence": round(
                sum(ann.confidence for ann in annotations) / len(annotations), 2
            ) if annotations else 0,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }

    def search_annotations(
        self,
        project_id: int,
        keyword: str,
        limit: int = 50
    ) -> List[UserAnnotation]:
        """
        搜索标注

        Args:
            project_id: 项目ID
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            匹配的标注列表
        """
        annotations = self.db.query(UserAnnotation).filter(
            UserAnnotation.project_id == project_id
        ).all()

        # 在标注内容中搜索
        matched = []
        for ann in annotations:
            content_str = str(ann.annotation_content)
            if keyword.lower() in content_str.lower():
                matched.append(ann)

        # 按时间排序
        matched.sort(key=lambda x: x.created_at, reverse=True)

        return matched[:limit]

    def get_annotation_trend(
        self,
        project_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取标注趋势

        Args:
            project_id: 项目ID
            days: 统计天数

        Returns:
            每日标注统计
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        annotations = self.db.query(UserAnnotation).filter(
            and_(
                UserAnnotation.project_id == project_id,
                UserAnnotation.created_at >= start_date
            )
        ).all()

        # 按日期分组
        daily_stats = {}
        for ann in annotations:
            date_key = ann.created_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "date": date_key,
                    "count": 0,
                    "by_type": {}
                }
            daily_stats[date_key]["count"] += 1

            ann_type = ann.annotation_type.value
            if ann_type not in daily_stats[date_key]["by_type"]:
                daily_stats[date_key]["by_type"][ann_type] = 0
            daily_stats[date_key]["by_type"][ann_type] += 1

        # 转换为列表并排序
        trend = sorted(daily_stats.values(), key=lambda x: x["date"])

        return trend

    def get_quality_feedback(
        self,
        project_id: int,
        target_type: str
    ) -> List[UserAnnotation]:
        """
        获取质量反馈标注

        Args:
            project_id: 项目ID
            target_type: 目标类型

        Returns:
            质量反馈标注列表
        """
        return self.db.query(UserAnnotation).filter(
            and_(
                UserAnnotation.project_id == project_id,
                UserAnnotation.target_type == target_type,
                UserAnnotation.annotation_type == AnnotationType.QUALITY_FEEDBACK
            )
        ).order_by(desc(UserAnnotation.created_at)).all()

    def get_corrections(
        self,
        project_id: int,
        target_type: Optional[str] = None
    ) -> List[UserAnnotation]:
        """
        获取纠正标注

        Args:
            project_id: 项目ID
            target_type: 可选，目标类型

        Returns:
            纠正标注列表
        """
        query = self.db.query(UserAnnotation).filter(
            and_(
                UserAnnotation.project_id == project_id,
                UserAnnotation.annotation_type == AnnotationType.CORRECTION
            )
        )

        if target_type:
            query = query.filter(UserAnnotation.target_type == target_type)

        return query.order_by(desc(UserAnnotation.created_at)).all()
