"""
Thinking Pattern Service - 思维模式服务
从项目实践中提取思维模式，更新到Skill知识库
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
import logging

from app.models.thinking_pattern import ThinkingPattern, SkillKnowledgeBase, DomainKnowledge

logger = logging.getLogger(__name__)


class ThinkingPatternService:
    """思维模式服务 - 提取、管理和应用思维模式"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.logger = logger

    # ==================== 思维模式提取 ====================

    def extract_pattern_from_execution(
        self,
        db: Session,
        project_id: int,
        execution_data: Dict[str, Any],
        extraction_method: str = "auto",
    ) -> Optional[ThinkingPattern]:
        """
        从项目执行中提取思维模式

        Args:
            db: 数据库会话
            project_id: 项目ID
            execution_data: 执行数据
                {
                    "pattern_name": str,
                    "pattern_type": str,  # problem_solving, decision_making, analysis, optimization
                    "pattern_description": str,
                    "thought_process": str,
                    "trigger_conditions": dict,
                    "expected_outcome": str,
                    "implementation_steps": list,
                    "skill_id": str (optional),
                    "user_id": int (optional),
                    "source_type": str,
                    "source_id": str
                }
            extraction_method: 提取方法

        Returns:
            ThinkingPattern: 创建的思维模式
        """
        try:
            # 检查是否已存在类似模式
            existing = self._find_similar_pattern(
                db, project_id, execution_data.get("pattern_name")
            )

            if existing:
                self.logger.info(f"发现相似模式，更新而非创建新模式: {execution_data.get('pattern_name')}")
                return self._update_pattern_from_execution(db, existing, execution_data)

            pattern = ThinkingPattern(
                project_id=project_id,
                skill_id=execution_data.get("skill_id"),
                user_id=execution_data.get("user_id"),
                pattern_name=execution_data["pattern_name"],
                pattern_type=execution_data["pattern_type"],
                pattern_description=execution_data["pattern_description"],
                pattern_context=execution_data.get("pattern_context"),
                trigger_conditions=execution_data.get("trigger_conditions"),
                thought_process=execution_data["thought_process"],
                expected_outcome=execution_data.get("expected_outcome"),
                implementation_steps=execution_data.get("implementation_steps"),
                source_type=execution_data.get("source_type", "project_execution"),
                source_id=execution_data.get("source_id"),
                extraction_method=extraction_method,
                is_active=True,
                is_validated=False,
                confidence_score=0.7,  # 初始置信度
                tags=execution_data.get("tags", []),
            )

            db.add(pattern)
            db.commit()
            db.refresh(pattern)

            self.logger.info(f"✅ 提取思维模式: {pattern.pattern_name} (type: {pattern.pattern_type})")
            return pattern

        except Exception as e:
            self.logger.error(f"❌ 提取思维模式失败: {e}")
            db.rollback()
            return None

    def extract_patterns_from_skill_optimization(
        self,
        db: Session,
        project_id: int,
        skill_id: str,
        optimization_history: List[Dict[str, Any]],
    ) -> List[ThinkingPattern]:
        """
        从Skill优化历史中提取思维模式

        Args:
            db: 数据库会话
            project_id: 项目ID
            skill_id: Skill ID
            optimization_history: 优化历史

        Returns:
            List[ThinkingPattern]: 提取的模式列表
        """
        patterns = []

        for opt in optimization_history:
            # 分析优化类型并提取模式
            if opt.get("change_type") == "optimized" and opt.get("optimization_reason"):
                pattern_data = {
                    "pattern_name": f"{opt.get('skill_name', 'Skill')}_优化模式",
                    "pattern_type": "optimization",
                    "pattern_description": opt.get("optimization_reason", ""),
                    "thought_process": opt.get("change_summary", ""),
                    "skill_id": skill_id,
                    "source_type": "skill_optimization",
                    "source_id": str(opt.get("version_id")),
                    "trigger_conditions": {
                        "success_rate": opt.get("success_rate"),
                        "execution_time": opt.get("avg_execution_time"),
                    },
                }

                pattern = self.extract_pattern_from_execution(
                    db, project_id, pattern_data, extraction_method="auto"
                )

                if pattern:
                    patterns.append(pattern)

        self.logger.info(f"✅ 从Skill优化中提取 {len(patterns)} 个思维模式")
        return patterns

    # ==================== 跨项目模式检索 ====================

    def retrieve_patterns_cross_project(
        self,
        db: Session,
        current_project_id: int,
        pattern_type: Optional[str] = None,
        min_confidence: float = 0.6,
        limit: int = 10,
    ) -> List[ThinkingPattern]:
        """
        跨项目检索思维模式（不是记忆）

        Args:
            db: 数据库会话
            current_project_id: 当前项目ID
            pattern_type: 模式类型筛选
            min_confidence: 最小置信度
            limit: 返回数量

        Returns:
            List[ThinkingPattern]: 跨项目的思维模式
        """
        query = db.query(ThinkingPattern).filter(
            and_(
                ThinkingPattern.project_id != current_project_id,  # 其他项目
                ThinkingPattern.is_active == True,
                ThinkingPattern.is_validated == True,  # 只检索已验证的
                ThinkingPattern.confidence_score >= min_confidence,
            )
        )

        if pattern_type:
            query = query.filter(ThinkingPattern.pattern_type == pattern_type)

        patterns = (
            query.order_by(desc(ThinkingPattern.confidence_score))
            .limit(limit)
            .all()
        )

        self.logger.info(f"🔍 跨项目检索到 {len(patterns)} 个思维模式")
        return patterns

    def find_applicable_patterns(
        self,
        db: Session,
        project_id: int,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        根据上下文查找适用的思维模式

        Args:
            db: 数据库会话
            project_id: 项目ID
            context: 当前上下文
                {
                    "problem_type": str,
                    "current_state": dict,
                    "constraints": list
                }

        Returns:
            List[Dict]: 适用的模式及匹配度
        """
        # 本项目模式
        local_patterns = db.query(ThinkingPattern).filter(
            and_(
                ThinkingPattern.project_id == project_id,
                ThinkingPattern.is_active == True,
            )
        ).all()

        # 跨项目模式
        cross_patterns = self.retrieve_patterns_cross_project(
            db, project_id, limit=20
        )

        all_patterns = local_patterns + cross_patterns
        applicable = []

        for pattern in all_patterns:
            match_score = self._calculate_pattern_match_score(pattern, context)
            if match_score > 0.5:
                applicable.append({
                    "pattern": pattern.to_dict(),
                    "match_score": match_score,
                    "source": "local" if pattern.project_id == project_id else "cross_project",
                })

        # 按匹配度排序
        applicable.sort(key=lambda x: x["match_score"], reverse=True)
        return applicable[:10]

    # ==================== 更新到Skill知识库 ====================

    def update_skill_knowledge_from_patterns(
        self,
        db: Session,
        project_id: int,
        pattern_ids: List[int],
        user_id: Optional[int] = None,
    ) -> SkillKnowledgeBase:
        """
        将思维模式更新到Skill知识库

        Args:
            db: 数据库会话
            project_id: 项目ID
            pattern_ids: 模式ID列表
            user_id: 用户ID

        Returns:
            SkillKnowledgeBase: 知识条目
        """
        patterns = db.query(ThinkingPattern).filter(
            ThinkingPattern.id.in_(pattern_ids)
        ).all()

        if not patterns:
            raise ValueError("未找到指定的思维模式")

        # 综合多个模式形成知识
        knowledge_content = self._synthesize_knowledge_from_patterns(patterns)

        knowledge = SkillKnowledgeBase(
            project_id=project_id,
            skill_id=patterns[0].skill_id if patterns[0].skill_id else None,
            user_id=user_id,
            knowledge_title=f"{patterns[0].pattern_name} - 实践知识",
            knowledge_type="best_practice" if len(patterns) > 1 else "pattern",
            knowledge_content=knowledge_content["content"],
            knowledge_context=knowledge_content["context"],
            source_patterns=pattern_ids,
            derived_from=f"提炼自 {len(patterns)} 个思维模式",
            when_to_use=knowledge_content["when_to_use"],
            when_not_to_use=knowledge_content["when_not_to_use"],
            expected_benefits=knowledge_content["benefits"],
            is_active=True,
            confidence_level="high" if all(p.confidence_score >= 0.8 for p in patterns) else "medium",
            tags=list(set(sum([p.tags or [] for p in patterns], []))),
        )

        db.add(knowledge)
        db.commit()
        db.refresh(knowledge)

        self.logger.info(f"✅ 更新Skill知识库: {knowledge.knowledge_title}")
        return knowledge

    def auto_sync_patterns_to_knowledge(
        self,
        db: Session,
        project_id: int,
        min_pattern_count: int = 3,
    ) -> List[SkillKnowledgeBase]:
        """
        自动同步思维模式到知识库（批量）

        Args:
            db: 数据库会话
            project_id: 项目ID
            min_pattern_count: 最小模式数量

        Returns:
            List[SkillKnowledgeBase]: 创建的知识条目
        """
        # 获取已验证的高质量模式
        patterns = db.query(ThinkingPattern).filter(
            and_(
                ThinkingPattern.project_id == project_id,
                ThinkingPattern.is_active == True,
                ThinkingPattern.is_validated == True,
                ThinkingPattern.confidence_score >= 0.7,
            )
        ).all()

        if len(patterns) < min_pattern_count:
            self.logger.info(f"模式数量不足 ({len(patterns)} < {min_pattern_count})，跳过自动同步")
            return []

        # 按类型分组
        patterns_by_type = {}
        for p in patterns:
            if p.pattern_type not in patterns_by_type:
                patterns_by_type[p.pattern_type] = []
            patterns_by_type[p.pattern_type].append(p)

        knowledge_entries = []
        for pattern_type, type_patterns in patterns_by_type.items():
            if len(type_patterns) >= 2:  # 至少2个同类型模式
                pattern_ids = [p.id for p in type_patterns[:5]]  # 最多5个
                knowledge = self.update_skill_knowledge_from_patterns(
                    db, project_id, pattern_ids
                )
                knowledge_entries.append(knowledge)

        self.logger.info(f"✅ 自动同步 {len(knowledge_entries)} 个知识条目")
        return knowledge_entries

    # ==================== 模式使用和验证 ====================

    def record_pattern_usage(
        self,
        db: Session,
        pattern_id: int,
        success: bool,
        effectiveness_score: Optional[float] = None,
    ) -> None:
        """记录模式使用情况"""
        pattern = db.query(ThinkingPattern).filter(ThinkingPattern.id == pattern_id).first()
        if not pattern:
            return

        pattern.usage_count += 1
        if success:
            pattern.success_count += 1
        else:
            pattern.failure_count += 1

        # 更新平均有效性
        if effectiveness_score is not None:
            if pattern.avg_effectiveness is None:
                pattern.avg_effectiveness = effectiveness_score
            else:
                total = pattern.avg_effectiveness * (pattern.usage_count - 1) + effectiveness_score
                pattern.avg_effectiveness = total / pattern.usage_count

        pattern.last_used_at = datetime.utcnow()

        # 自动验证：如果成功次数>=5且成功率>=0.8，标记为已验证
        if pattern.usage_count >= 5 and pattern.success_rate >= 0.8:
            pattern.is_validated = True
            pattern.validated_at = datetime.utcnow()
            pattern.confidence_score = min(0.95, pattern.success_rate)

        db.commit()
        self.logger.debug(f"📊 记录模式使用: {pattern.pattern_name} (成功: {success})")

    def validate_pattern(
        self,
        db: Session,
        pattern_id: int,
        validation_result: bool,
        validator_id: Optional[int] = None,
    ) -> None:
        """手动验证模式"""
        pattern = db.query(ThinkingPattern).filter(ThinkingPattern.id == pattern_id).first()
        if not pattern:
            return

        pattern.is_validated = validation_result
        pattern.validated_at = datetime.utcnow()

        if validation_result:
            pattern.confidence_score = 0.9
        else:
            pattern.confidence_score = 0.3
            pattern.is_active = False

        db.commit()
        self.logger.info(f"✅ 验证模式: {pattern.pattern_name} - {'通过' if validation_result else '未通过'}")

    # ==================== 领域知识管理 ====================

    def add_domain_knowledge(
        self,
        db: Session,
        domain: str,
        topic: str,
        knowledge_content: str,
        knowledge_type: str,
        source_type: str = "manual_input",
        source_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> DomainKnowledge:
        """
        添加领域知识（仅作为常识背景）

        Args:
            db: 数据库会话
            domain: 领域
            topic: 主题
            knowledge_content: 知识内容
            knowledge_type: 知识类型
            source_type: 来源类型
            source_url: 来源URL
            tags: 标签

        Returns:
            DomainKnowledge: 领域知识条目
        """
        knowledge = DomainKnowledge(
            domain=domain,
            topic=topic,
            knowledge_content=knowledge_content,
            knowledge_type=knowledge_type,
            source_type=source_type,
            source_url=source_url,
            source_reliability="medium",
            usage_constraint="background_only",
            can_influence_decision=False,  # 固定为False
            can_influence_analysis=False,  # 固定为False
            can_influence_report=False,    # 固定为False
            tags=tags or [],
        )

        db.add(knowledge)
        db.commit()
        db.refresh(knowledge)

        self.logger.info(f"✅ 添加领域知识: {domain}/{topic} (仅作为常识背景)")
        return knowledge

    def query_domain_knowledge(
        self,
        db: Session,
        domain: Optional[str] = None,
        topic: Optional[str] = None,
        limit: int = 10,
    ) -> List[DomainKnowledge]:
        """查询领域知识（仅用于显示，不影响决策）"""
        query = db.query(DomainKnowledge)

        if domain:
            query = query.filter(DomainKnowledge.domain == domain)
        if topic:
            query = query.filter(DomainKnowledge.topic.ilike(f"%{topic}%"))

        knowledge = query.order_by(desc(DomainKnowledge.created_at)).limit(limit).all()

        # 更新访问时间
        for k in knowledge:
            k.last_accessed_at = datetime.utcnow()
        db.commit()

        return knowledge

    # ==================== 内部辅助方法 ====================

    def _find_similar_pattern(
        self, db: Session, project_id: int, pattern_name: str
    ) -> Optional[ThinkingPattern]:
        """查找相似模式"""
        return db.query(ThinkingPattern).filter(
            and_(
                ThinkingPattern.project_id == project_id,
                ThinkingPattern.pattern_name == pattern_name,
                ThinkingPattern.is_active == True,
            )
        ).first()

    def _update_pattern_from_execution(
        self, db: Session, pattern: ThinkingPattern, execution_data: Dict[str, Any]
    ) -> ThinkingPattern:
        """更新已有模式"""
        pattern.usage_count += 1
        pattern.thought_process = execution_data.get("thought_process", pattern.thought_process)
        pattern.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(pattern)
        return pattern

    def _calculate_pattern_match_score(
        self, pattern: ThinkingPattern, context: Dict[str, Any]
    ) -> float:
        """计算模式与上下文的匹配度"""
        score = 0.0

        # 基础置信度
        score += (pattern.confidence_score or 0.5) * 0.3

        # 成功率
        if pattern.success_rate:
            score += pattern.success_rate * 0.3

        # 使用次数（经验值）
        if pattern.usage_count > 10:
            score += 0.2
        elif pattern.usage_count > 5:
            score += 0.1

        # 是否已验证
        if pattern.is_validated:
            score += 0.2

        return min(1.0, score)

    def _synthesize_knowledge_from_patterns(
        self, patterns: List[ThinkingPattern]
    ) -> Dict[str, Any]:
        """综合多个模式形成知识"""
        # 合并思维过程
        thought_processes = [p.thought_process for p in patterns]

        # 提取共同点
        all_tags = list(set(sum([p.tags or [] for p in patterns], [])))

        return {
            "content": "\n\n".join(thought_processes),
            "context": f"综合自 {len(patterns)} 个实践案例",
            "when_to_use": "当遇到类似问题场景时",
            "when_not_to_use": "当上下文显著不同时",
            "benefits": [
                f"经过 {sum(p.usage_count for p in patterns)} 次实践验证",
                f"平均成功率: {sum(p.success_rate or 0 for p in patterns) / len(patterns):.1%}",
            ],
        }


# 全局单例
_thinking_pattern_service: Optional[ThinkingPatternService] = None


def get_thinking_pattern_service() -> ThinkingPatternService:
    """获取思维模式服务单例"""
    global _thinking_pattern_service
    if _thinking_pattern_service is None:
        _thinking_pattern_service = ThinkingPatternService()
    return _thinking_pattern_service
