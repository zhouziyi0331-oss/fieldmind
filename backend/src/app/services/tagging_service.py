"""
用户标签服务

提供用户自定义标签、分类和组织功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from app.models.user_engagement import UserTagging


class TaggingService:
    """用户标签服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    def create_tag(
        self,
        user_id: int,
        project_id: int,
        target_type: str,
        target_id: int,
        tag_name: str,
        tag_color: Optional[str] = None,
        tag_metadata: Optional[Dict[str, Any]] = None
    ) -> UserTagging:
        """
        创建标签

        Args:
            user_id: 用户ID
            project_id: 项目ID
            target_type: 标签目标类型（document, entity, relationship等）
            target_id: 标签目标ID
            tag_name: 标签名称
            tag_color: 标签颜色
            tag_metadata: 标签元数据

        Returns:
            创建的标签
        """
        tag = UserTagging(
            user_id=user_id,
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            tag_name=tag_name,
            tag_color=tag_color or "#808080",
            tag_metadata=tag_metadata or {},
            created_at=datetime.utcnow()
        )

        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)

        return tag

    def get_tags(
        self,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        tag_name: Optional[str] = None,
        limit: int = 200
    ) -> List[UserTagging]:
        """
        获取标签列表

        Args:
            user_id: 可选，用户ID
            project_id: 可选，项目ID
            target_type: 可选，目标类型
            target_id: 可选，目标ID
            tag_name: 可选，标签名称
            limit: 返回数量

        Returns:
            标签列表
        """
        query = self.db.query(UserTagging)

        if user_id:
            query = query.filter(UserTagging.user_id == user_id)
        if project_id:
            query = query.filter(UserTagging.project_id == project_id)
        if target_type:
            query = query.filter(UserTagging.target_type == target_type)
        if target_id:
            query = query.filter(UserTagging.target_id == target_id)
        if tag_name:
            query = query.filter(UserTagging.tag_name == tag_name)

        tags = query.order_by(
            desc(UserTagging.created_at)
        ).limit(limit).all()

        return tags

    def get_tag_by_id(
        self,
        tag_id: int
    ) -> Optional[UserTagging]:
        """
        根据ID获取标签

        Args:
            tag_id: 标签ID

        Returns:
            标签对象
        """
        return self.db.query(UserTagging).filter(
            UserTagging.id == tag_id
        ).first()

    def delete_tag(
        self,
        tag_id: int,
        user_id: int
    ) -> bool:
        """
        删除标签

        Args:
            tag_id: 标签ID
            user_id: 用户ID（验证权限）

        Returns:
            是否成功删除
        """
        tag = self.db.query(UserTagging).filter(
            and_(
                UserTagging.id == tag_id,
                UserTagging.user_id == user_id
            )
        ).first()

        if not tag:
            return False

        self.db.delete(tag)
        self.db.commit()

        return True

    def get_tags_for_target(
        self,
        target_type: str,
        target_id: int,
        project_id: Optional[int] = None
    ) -> List[UserTagging]:
        """
        获取特定目标的所有标签

        Args:
            target_type: 目标类型
            target_id: 目标ID
            project_id: 可选，项目ID

        Returns:
            标签列表
        """
        query = self.db.query(UserTagging).filter(
            and_(
                UserTagging.target_type == target_type,
                UserTagging.target_id == target_id
            )
        )

        if project_id:
            query = query.filter(UserTagging.project_id == project_id)

        return query.order_by(desc(UserTagging.created_at)).all()

    def get_all_tag_names(
        self,
        user_id: int,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取所有标签名称（去重）

        Args:
            user_id: 用户ID
            project_id: 项目ID

        Returns:
            标签名称列表（包含使用次数）
        """
        tags = self.db.query(UserTagging).filter(
            and_(
                UserTagging.user_id == user_id,
                UserTagging.project_id == project_id
            )
        ).all()

        # 统计每个标签的使用次数
        tag_counts = {}
        tag_colors = {}
        for tag in tags:
            name = tag.tag_name
            tag_counts[name] = tag_counts.get(name, 0) + 1
            if name not in tag_colors:
                tag_colors[name] = tag.tag_color

        # 转换为列表
        result = [
            {
                "tag_name": name,
                "count": count,
                "color": tag_colors[name]
            }
            for name, count in tag_counts.items()
        ]

        # 按使用次数排序
        result.sort(key=lambda x: x["count"], reverse=True)

        return result

    def get_targets_by_tag(
        self,
        user_id: int,
        project_id: int,
        tag_name: str
    ) -> List[Dict[str, Any]]:
        """
        根据标签获取所有目标

        Args:
            user_id: 用户ID
            project_id: 项目ID
            tag_name: 标签名称

        Returns:
            目标列表
        """
        tags = self.db.query(UserTagging).filter(
            and_(
                UserTagging.user_id == user_id,
                UserTagging.project_id == project_id,
                UserTagging.tag_name == tag_name
            )
        ).all()

        # 按目标类型分组
        targets_by_type = {}
        for tag in tags:
            target_type = tag.target_type
            if target_type not in targets_by_type:
                targets_by_type[target_type] = []
            targets_by_type[target_type].append({
                "target_id": tag.target_id,
                "tagged_at": tag.created_at.isoformat()
            })

        return [
            {
                "target_type": target_type,
                "targets": targets
            }
            for target_type, targets in targets_by_type.items()
        ]

    def get_tag_statistics(
        self,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取标签统计

        Args:
            project_id: 项目ID
            days: 统计天数

        Returns:
            统计数据
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        tags = self.db.query(UserTagging).filter(
            and_(
                UserTagging.project_id == project_id,
                UserTagging.created_at >= start_date
            )
        ).all()

        # 统计标签名称
        tag_name_counts = {}
        for tag in tags:
            name = tag.tag_name
            tag_name_counts[name] = tag_name_counts.get(name, 0) + 1

        # 按目标类型统计
        target_type_counts = {}
        for tag in tags:
            target_type = tag.target_type
            target_type_counts[target_type] = target_type_counts.get(target_type, 0) + 1

        # 按用户统计
        user_counts = {}
        for tag in tags:
            user_id = tag.user_id
            user_counts[user_id] = user_counts.get(user_id, 0) + 1

        return {
            "period_days": days,
            "total_tags": len(tags),
            "unique_tag_names": len(tag_name_counts),
            "by_tag_name": sorted(
                tag_name_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20],
            "by_target_type": target_type_counts,
            "by_user": user_counts,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }

    def get_user_tag_summary(
        self,
        user_id: int,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户标签摘要

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 统计天数

        Returns:
            用户标签摘要
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        tags = self.db.query(UserTagging).filter(
            and_(
                UserTagging.user_id == user_id,
                UserTagging.project_id == project_id,
                UserTagging.created_at >= start_date
            )
        ).all()

        # 统计标签名称
        tag_name_counts = {}
        for tag in tags:
            name = tag.tag_name
            tag_name_counts[name] = tag_name_counts.get(name, 0) + 1

        # 按目标类型统计
        target_type_counts = {}
        for tag in tags:
            target_type = tag.target_type
            target_type_counts[target_type] = target_type_counts.get(target_type, 0) + 1

        return {
            "period_days": days,
            "total_tags": len(tags),
            "unique_tag_names": len(tag_name_counts),
            "top_tags": sorted(
                tag_name_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "by_target_type": target_type_counts,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }

    def search_tags(
        self,
        user_id: int,
        project_id: int,
        keyword: str,
        limit: int = 50
    ) -> List[UserTagging]:
        """
        搜索标签

        Args:
            user_id: 用户ID
            project_id: 项目ID
            keyword: 搜索关键词
            limit: 返回数量

        Returns:
            匹配的标签列表
        """
        tags = self.db.query(UserTagging).filter(
            and_(
                UserTagging.user_id == user_id,
                UserTagging.project_id == project_id
            )
        ).all()

        # 关键词匹配
        matched = [
            tag for tag in tags
            if keyword.lower() in tag.tag_name.lower()
        ]

        # 按时间排序
        matched.sort(key=lambda x: x.created_at, reverse=True)

        return matched[:limit]

    def get_tag_trend(
        self,
        project_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取标签趋势

        Args:
            project_id: 项目ID
            days: 统计天数

        Returns:
            每日标签统计
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        tags = self.db.query(UserTagging).filter(
            and_(
                UserTagging.project_id == project_id,
                UserTagging.created_at >= start_date
            )
        ).all()

        # 按日期分组
        daily_stats = {}
        for tag in tags:
            date_key = tag.created_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "date": date_key,
                    "count": 0,
                    "unique_tags": set()
                }
            daily_stats[date_key]["count"] += 1
            daily_stats[date_key]["unique_tags"].add(tag.tag_name)

        # 转换为列表并排序
        trend = []
        for date_key, stats in daily_stats.items():
            trend.append({
                "date": stats["date"],
                "count": stats["count"],
                "unique_tag_count": len(stats["unique_tags"])
            })

        trend.sort(key=lambda x: x["date"])

        return trend

    def bulk_tag(
        self,
        user_id: int,
        project_id: int,
        target_type: str,
        target_ids: List[int],
        tag_name: str,
        tag_color: Optional[str] = None
    ) -> List[UserTagging]:
        """
        批量标签

        Args:
            user_id: 用户ID
            project_id: 项目ID
            target_type: 目标类型
            target_ids: 目标ID列表
            tag_name: 标签名称
            tag_color: 标签颜色

        Returns:
            创建的标签列表
        """
        tags = []
        for target_id in target_ids:
            tag = UserTagging(
                user_id=user_id,
                project_id=project_id,
                target_type=target_type,
                target_id=target_id,
                tag_name=tag_name,
                tag_color=tag_color or "#808080",
                tag_metadata={},
                created_at=datetime.utcnow()
            )
            self.db.add(tag)
            tags.append(tag)

        self.db.commit()

        for tag in tags:
            self.db.refresh(tag)

        return tags

    def remove_tags_from_target(
        self,
        user_id: int,
        target_type: str,
        target_id: int,
        tag_name: Optional[str] = None
    ) -> int:
        """
        从目标移除标签

        Args:
            user_id: 用户ID
            target_type: 目标类型
            target_id: 目标ID
            tag_name: 可选，指定标签名称（不指定则移除所有标签）

        Returns:
            移除的标签数量
        """
        query = self.db.query(UserTagging).filter(
            and_(
                UserTagging.user_id == user_id,
                UserTagging.target_type == target_type,
                UserTagging.target_id == target_id
            )
        )

        if tag_name:
            query = query.filter(UserTagging.tag_name == tag_name)

        count = query.count()
        query.delete()
        self.db.commit()

        return count
