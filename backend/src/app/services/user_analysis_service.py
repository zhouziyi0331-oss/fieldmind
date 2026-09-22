"""
用户分析服务

提供用户行为分析、兴趣挖掘和个性化推荐功能
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from app.models.user_engagement import (
    UserAnalysisDimension,
    UserThinkingPattern,
    PatternType
)


class UserAnalysisService:
    """用户分析服务"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db

    # ==================== 分析维度管理 ====================

    def record_dimension(
        self,
        user_id: int,
        project_id: int,
        dimension_name: str,
        interest_score: float,
        evidence: Optional[Dict[str, Any]] = None,
        related_entities: Optional[List[str]] = None
    ) -> UserAnalysisDimension:
        """
        记录用户分析维度

        Args:
            user_id: 用户ID
            project_id: 项目ID
            dimension_name: 维度名称（如"权力关系"、"社会结构"）
            interest_score: 兴趣分数（0-1）
            evidence: 证据数据
            related_entities: 相关实体

        Returns:
            分析维度记录
        """
        # 检查是否已存在
        existing = self.db.query(UserAnalysisDimension).filter(
            and_(
                UserAnalysisDimension.user_id == user_id,
                UserAnalysisDimension.project_id == project_id,
                UserAnalysisDimension.dimension_name == dimension_name
            )
        ).first()

        if existing:
            # 更新现有记录
            existing.interest_score = interest_score
            existing.evidence = evidence or {}
            existing.related_entities = related_entities or []
            existing.last_updated = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # 创建新记录
        dimension = UserAnalysisDimension(
            user_id=user_id,
            project_id=project_id,
            dimension_name=dimension_name,
            interest_score=interest_score,
            evidence=evidence or {},
            related_entities=related_entities or [],
            identified_at=datetime.utcnow(),
            last_updated=datetime.utcnow()
        )

        self.db.add(dimension)
        self.db.commit()
        self.db.refresh(dimension)

        return dimension

    def get_user_dimensions(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        min_score: float = 0.0
    ) -> List[UserAnalysisDimension]:
        """
        获取用户的分析维度

        Args:
            user_id: 用户ID
            project_id: 可选，项目ID
            min_score: 最小兴趣分数

        Returns:
            分析维度列表
        """
        query = self.db.query(UserAnalysisDimension).filter(
            and_(
                UserAnalysisDimension.user_id == user_id,
                UserAnalysisDimension.interest_score >= min_score
            )
        )

        if project_id:
            query = query.filter(UserAnalysisDimension.project_id == project_id)

        dimensions = query.order_by(
            desc(UserAnalysisDimension.interest_score)
        ).all()

        return dimensions

    def get_top_interests(
        self,
        user_id: int,
        project_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取用户的核心兴趣点

        Args:
            user_id: 用户ID
            project_id: 项目ID
            limit: 返回数量

        Returns:
            兴趣点列表
        """
        dimensions = self.db.query(UserAnalysisDimension).filter(
            and_(
                UserAnalysisDimension.user_id == user_id,
                UserAnalysisDimension.project_id == project_id
            )
        ).order_by(
            desc(UserAnalysisDimension.interest_score)
        ).limit(limit).all()

        return [
            {
                "dimension": d.dimension_name,
                "score": d.interest_score,
                "entities": d.related_entities,
                "last_updated": d.last_updated.isoformat()
            }
            for d in dimensions
        ]

    # ==================== 思维模式识别 ====================

    def record_thinking_pattern(
        self,
        user_id: int,
        project_id: int,
        pattern_type: PatternType,
        pattern_description: str,
        examples: Optional[List[str]] = None,
        confidence: float = 0.5
    ) -> UserThinkingPattern:
        """
        记录用户思维模式

        Args:
            user_id: 用户ID
            project_id: 项目ID
            pattern_type: 模式类型
            pattern_description: 模式描述
            examples: 示例列表
            confidence: 置信度（0-1）

        Returns:
            思维模式记录
        """
        pattern = UserThinkingPattern(
            user_id=user_id,
            project_id=project_id,
            pattern_type=pattern_type,
            pattern_description=pattern_description,
            examples=examples or [],
            confidence=confidence,
            identified_at=datetime.utcnow(),
            last_observed=datetime.utcnow()
        )

        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)

        return pattern

    def get_thinking_patterns(
        self,
        user_id: int,
        project_id: Optional[int] = None,
        pattern_type: Optional[PatternType] = None
    ) -> List[UserThinkingPattern]:
        """
        获取用户的思维模式

        Args:
            user_id: 用户ID
            project_id: 可选，项目ID
            pattern_type: 可选，模式类型

        Returns:
            思维模式列表
        """
        query = self.db.query(UserThinkingPattern).filter(
            UserThinkingPattern.user_id == user_id
        )

        if project_id:
            query = query.filter(UserThinkingPattern.project_id == project_id)

        if pattern_type:
            query = query.filter(UserThinkingPattern.pattern_type == pattern_type)

        patterns = query.order_by(
            desc(UserThinkingPattern.confidence)
        ).all()

        return patterns

    def update_pattern_confidence(
        self,
        pattern_id: int,
        confidence: float,
        add_example: Optional[str] = None
    ) -> UserThinkingPattern:
        """
        更新思维模式置信度

        Args:
            pattern_id: 模式ID
            confidence: 新置信度
            add_example: 可选，添加新示例

        Returns:
            更新后的模式
        """
        pattern = self.db.query(UserThinkingPattern).filter(
            UserThinkingPattern.id == pattern_id
        ).first()

        if not pattern:
            raise ValueError(f"思维模式 {pattern_id} 不存在")

        pattern.confidence = max(0.0, min(1.0, confidence))
        pattern.last_observed = datetime.utcnow()

        if add_example:
            pattern.examples.append(add_example)

        self.db.commit()
        self.db.refresh(pattern)

        return pattern

    # ==================== 用户行为分析 ====================

    def analyze_user_focus(
        self,
        user_id: int,
        project_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        分析用户关注焦点

        Args:
            user_id: 用户ID
            project_id: 项目ID
            days: 分析天数

        Returns:
            分析结果
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # 获取分析维度
        dimensions = self.db.query(UserAnalysisDimension).filter(
            and_(
                UserAnalysisDimension.user_id == user_id,
                UserAnalysisDimension.project_id == project_id,
                UserAnalysisDimension.last_updated >= start_date
            )
        ).all()

        # 获取思维模式
        patterns = self.db.query(UserThinkingPattern).filter(
            and_(
                UserThinkingPattern.user_id == user_id,
                UserThinkingPattern.project_id == project_id,
                UserThinkingPattern.last_observed >= start_date
            )
        ).all()

        # 分析主要关注点
        focus_areas = sorted(
            dimensions,
            key=lambda d: d.interest_score,
            reverse=True
        )[:5]

        # 分析思维特征
        thinking_traits = {}
        for pattern in patterns:
            trait = pattern.pattern_type.value
            if trait not in thinking_traits:
                thinking_traits[trait] = []
            thinking_traits[trait].append({
                "description": pattern.pattern_description,
                "confidence": pattern.confidence
            })

        return {
            "period_days": days,
            "focus_areas": [
                {
                    "dimension": d.dimension_name,
                    "score": d.interest_score,
                    "entities": d.related_entities[:5]
                }
                for d in focus_areas
            ],
            "thinking_traits": thinking_traits,
            "total_dimensions": len(dimensions),
            "total_patterns": len(patterns),
            "analysis_date": datetime.utcnow().isoformat()
        }

    def get_personalized_suggestions(
        self,
        user_id: int,
        project_id: int
    ) -> List[Dict[str, Any]]:
        """
        获取个性化建议

        Args:
            user_id: 用户ID
            project_id: 项目ID

        Returns:
            建议列表
        """
        # 获取用户兴趣维度
        dimensions = self.get_user_dimensions(
            user_id=user_id,
            project_id=project_id,
            min_score=0.5
        )

        # 获取思维模式
        patterns = self.get_thinking_patterns(
            user_id=user_id,
            project_id=project_id
        )

        suggestions = []

        # 基于兴趣维度生成建议
        for dim in dimensions[:3]:
            suggestions.append({
                "type": "interest_exploration",
                "title": f"深入探索：{dim.dimension_name}",
                "reason": f"您对此维度的兴趣分数为 {dim.interest_score:.2f}",
                "actions": [
                    f"查看相关实体：{', '.join(dim.related_entities[:3])}",
                    "生成专题分析报告",
                    "扩展知识图谱连接"
                ]
            })

        # 基于思维模式生成建议
        for pattern in patterns[:2]:
            if pattern.confidence > 0.6:
                suggestions.append({
                    "type": "thinking_enhancement",
                    "title": f"优化{pattern.pattern_type.value}方法",
                    "reason": pattern.pattern_description,
                    "actions": [
                        "查看相关分析范例",
                        "尝试不同的分析角度",
                        "记录分析心得"
                    ]
                })

        return suggestions

    def compare_with_baseline(
        self,
        user_id: int,
        project_id: int
    ) -> Dict[str, Any]:
        """
        与基准对比用户特征

        Args:
            user_id: 用户ID
            project_id: 项目ID

        Returns:
            对比结果
        """
        # 获取用户数据
        user_dimensions = self.get_user_dimensions(user_id, project_id)
        user_patterns = self.get_thinking_patterns(user_id, project_id)

        # 统计所有用户的平均数据（作为基准）
        all_dimensions = self.db.query(UserAnalysisDimension).filter(
            UserAnalysisDimension.project_id == project_id
        ).all()

        if not all_dimensions:
            return {
                "status": "insufficient_data",
                "message": "基准数据不足"
            }

        # 计算平均兴趣分数
        avg_score = sum(d.interest_score for d in all_dimensions) / len(all_dimensions)
        user_avg = (
            sum(d.interest_score for d in user_dimensions) / len(user_dimensions)
            if user_dimensions else 0
        )

        return {
            "user_avg_interest": round(user_avg, 2),
            "baseline_avg_interest": round(avg_score, 2),
            "difference": round(user_avg - avg_score, 2),
            "user_focus_count": len(user_dimensions),
            "user_pattern_count": len(user_patterns),
            "comparison_date": datetime.utcnow().isoformat()
        }
