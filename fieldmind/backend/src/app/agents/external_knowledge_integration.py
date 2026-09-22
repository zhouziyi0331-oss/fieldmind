"""
External Knowledge Integration for SynthesisAgent
将外部知识关联集成到SynthesisAgent中
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.services.thinking_pattern_service import get_thinking_pattern_service
from app.models.thinking_pattern import ThinkingPattern, SkillKnowledgeBase, DomainKnowledge

logger = logging.getLogger(__name__)


class ExternalKnowledgeIntegration:
    """外部知识集成模块 - SynthesisAgent的Phase 4扩展"""

    def __init__(self):
        self.pattern_service = get_thinking_pattern_service()
        self.logger = logger

    # ==================== 1. 跨项目知识检索（思维模式） ====================

    async def retrieve_thinking_patterns_cross_project(
        self,
        db: Session,
        current_project_id: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        跨项目检索思维模式（不是记忆）

        Args:
            db: 数据库会话
            current_project_id: 当前项目ID
            context: 上下文信息
                {
                    "problem_type": str,
                    "pattern_type": str (optional),
                    "min_confidence": float (optional)
                }

        Returns:
            Dict: 检索结果
        """
        try:
            pattern_type = context.get("pattern_type") if context else None
            min_confidence = context.get("min_confidence", 0.6) if context else 0.6

            # 跨项目检索思维模式
            patterns = self.pattern_service.retrieve_patterns_cross_project(
                db=db,
                current_project_id=current_project_id,
                pattern_type=pattern_type,
                min_confidence=min_confidence,
                limit=15,
            )

            self.logger.info(f"🔍 跨项目检索到 {len(patterns)} 个思维模式")

            return {
                "success": True,
                "project_id": current_project_id,
                "patterns_count": len(patterns),
                "patterns": [p.to_dict() for p in patterns],
                "pattern_types": list(set(p.pattern_type for p in patterns)),
                "avg_confidence": sum(p.confidence_score or 0 for p in patterns) / len(patterns) if patterns else 0,
            }

        except Exception as e:
            self.logger.error(f"❌ 跨项目检索失败: {e}")
            return {"success": False, "error": str(e)}

    async def find_applicable_patterns_for_context(
        self,
        db: Session,
        project_id: int,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        根据当前上下文查找适用的思维模式

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
            Dict: 适用的模式
        """
        try:
            applicable_patterns = self.pattern_service.find_applicable_patterns(
                db=db,
                project_id=project_id,
                context=context,
            )

            self.logger.info(f"✅ 找到 {len(applicable_patterns)} 个适用模式")

            return {
                "success": True,
                "applicable_count": len(applicable_patterns),
                "patterns": applicable_patterns,
                "recommendations": [
                    {
                        "pattern_name": p["pattern"]["pattern_name"],
                        "match_score": p["match_score"],
                        "source": p["source"],
                    }
                    for p in applicable_patterns[:5]
                ],
            }

        except Exception as e:
            self.logger.error(f"❌ 查找适用模式失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 2. Skill知识库更新（我安什么是什么） ====================

    async def extract_and_update_skill_knowledge(
        self,
        db: Session,
        project_id: int,
        skill_id: Optional[str],
        execution_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        从项目执行中提取思维模式并更新到Skill知识库

        Args:
            db: 数据库会话
            project_id: 项目ID
            skill_id: Skill ID
            execution_data: 执行数据
                {
                    "pattern_name": str,
                    "pattern_type": str,
                    "thought_process": str,
                    "outcome": dict
                }

        Returns:
            Dict: 更新结果
        """
        try:
            # 1. 提取思维模式
            pattern = self.pattern_service.extract_pattern_from_execution(
                db=db,
                project_id=project_id,
                execution_data={
                    **execution_data,
                    "skill_id": skill_id,
                },
            )

            if not pattern:
                return {"success": False, "error": "模式提取失败"}

            # 2. 自动更新到知识库（如果模式已验证）
            if pattern.is_validated or pattern.confidence_score >= 0.8:
                knowledge = self.pattern_service.update_skill_knowledge_from_patterns(
                    db=db,
                    project_id=project_id,
                    pattern_ids=[pattern.id],
                )

                self.logger.info(f"✅ 提取模式并更新知识库: {pattern.pattern_name} → {knowledge.knowledge_title}")

                return {
                    "success": True,
                    "pattern": pattern.to_dict(),
                    "knowledge": knowledge.to_dict(),
                    "action": "extracted_and_updated",
                }
            else:
                self.logger.info(f"📝 提取模式待验证: {pattern.pattern_name}")

                return {
                    "success": True,
                    "pattern": pattern.to_dict(),
                    "action": "extracted_pending_validation",
                }

        except Exception as e:
            self.logger.error(f"❌ 提取并更新知识失败: {e}")
            return {"success": False, "error": str(e)}

    async def sync_patterns_to_skill_knowledge_batch(
        self,
        db: Session,
        project_id: int,
    ) -> Dict[str, Any]:
        """
        批量同步思维模式到Skill知识库

        Args:
            db: 数据库会话
            project_id: 项目ID

        Returns:
            Dict: 同步结果
        """
        try:
            knowledge_entries = self.pattern_service.auto_sync_patterns_to_knowledge(
                db=db,
                project_id=project_id,
                min_pattern_count=3,
            )

            self.logger.info(f"✅ 批量同步 {len(knowledge_entries)} 个知识条目")

            return {
                "success": True,
                "synced_count": len(knowledge_entries),
                "knowledge_entries": [k.to_dict() for k in knowledge_entries],
            }

        except Exception as e:
            self.logger.error(f"❌ 批量同步失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_skill_knowledge_base(
        self,
        db: Session,
        project_id: int,
        skill_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取Skill知识库内容

        Args:
            db: 数据库会话
            project_id: 项目ID
            skill_id: Skill ID (optional)

        Returns:
            Dict: 知识库内容
        """
        try:
            query = db.query(SkillKnowledgeBase).filter(
                SkillKnowledgeBase.project_id == project_id,
                SkillKnowledgeBase.is_active == True,
            )

            if skill_id:
                query = query.filter(SkillKnowledgeBase.skill_id == skill_id)

            knowledge_entries = query.order_by(SkillKnowledgeBase.created_at.desc()).all()

            self.logger.info(f"📚 获取知识库: {len(knowledge_entries)} 个条目")

            return {
                "success": True,
                "project_id": project_id,
                "skill_id": skill_id,
                "entries_count": len(knowledge_entries),
                "knowledge_base": [k.to_dict() for k in knowledge_entries],
                "knowledge_types": list(set(k.knowledge_type for k in knowledge_entries)),
            }

        except Exception as e:
            self.logger.error(f"❌ 获取知识库失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 3. 领域知识库（仅作为常识背景） ====================

    async def add_domain_knowledge_as_background(
        self,
        db: Session,
        domain: str,
        topic: str,
        knowledge_content: str,
        source_type: str = "manual_input",
        source_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        添加领域知识作为常识背景（不影响决策/分析/报告）

        Args:
            db: 数据库会话
            domain: 领域
            topic: 主题
            knowledge_content: 知识内容
            source_type: 来源类型
            source_url: 来源URL

        Returns:
            Dict: 添加结果
        """
        try:
            knowledge = self.pattern_service.add_domain_knowledge(
                db=db,
                domain=domain,
                topic=topic,
                knowledge_content=knowledge_content,
                knowledge_type="reference",
                source_type=source_type,
                source_url=source_url,
            )

            # 验证约束
            assert knowledge.can_influence_decision == False, "领域知识不能影响决策"
            assert knowledge.can_influence_analysis == False, "领域知识不能影响分析"
            assert knowledge.can_influence_report == False, "领域知识不能影响报告"

            self.logger.info(f"✅ 添加领域知识（仅背景）: {domain}/{topic}")

            return {
                "success": True,
                "knowledge": knowledge.to_dict(),
                "constraints": {
                    "can_influence_decision": False,
                    "can_influence_analysis": False,
                    "can_influence_report": False,
                    "usage": "background_only",
                },
                "warning": "此知识仅作为常识背景，不会影响任何决策、分析或报告",
            }

        except Exception as e:
            self.logger.error(f"❌ 添加领域知识失败: {e}")
            return {"success": False, "error": str(e)}

    async def query_domain_knowledge_for_context(
        self,
        db: Session,
        domain: Optional[str],
        topic: Optional[str],
    ) -> Dict[str, Any]:
        """
        查询领域知识（仅用于显示，不影响决策）

        Args:
            db: 数据库会话
            domain: 领域
            topic: 主题

        Returns:
            Dict: 领域知识
        """
        try:
            knowledge_list = self.pattern_service.query_domain_knowledge(
                db=db,
                domain=domain,
                topic=topic,
                limit=10,
            )

            self.logger.info(f"📖 查询领域知识: {len(knowledge_list)} 个条目")

            return {
                "success": True,
                "domain": domain,
                "topic": topic,
                "knowledge_count": len(knowledge_list),
                "knowledge_list": [k.to_dict() for k in knowledge_list],
                "usage_note": "这些知识仅作为常识参考，不会影响决策、分析或报告",
            }

        except Exception as e:
            self.logger.error(f"❌ 查询领域知识失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 模式使用追踪 ====================

    async def track_pattern_usage(
        self,
        db: Session,
        pattern_id: int,
        usage_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        追踪思维模式的使用结果

        Args:
            db: 数据库会话
            pattern_id: 模式ID
            usage_result: 使用结果
                {
                    "success": bool,
                    "effectiveness_score": float (0-1)
                }

        Returns:
            Dict: 追踪结果
        """
        try:
            self.pattern_service.record_pattern_usage(
                db=db,
                pattern_id=pattern_id,
                success=usage_result.get("success", False),
                effectiveness_score=usage_result.get("effectiveness_score"),
            )

            self.logger.info(f"📊 追踪模式使用: pattern_id={pattern_id}, success={usage_result.get('success')}")

            return {"success": True, "pattern_id": pattern_id}

        except Exception as e:
            self.logger.error(f"❌ 追踪模式使用失败: {e}")
            return {"success": False, "error": str(e)}

    async def validate_pattern(
        self,
        db: Session,
        pattern_id: int,
        validation_result: bool,
        validator_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        验证思维模式

        Args:
            db: 数据库会话
            pattern_id: 模式ID
            validation_result: 验证结果
            validator_id: 验证者ID

        Returns:
            Dict: 验证结果
        """
        try:
            self.pattern_service.validate_pattern(
                db=db,
                pattern_id=pattern_id,
                validation_result=validation_result,
                validator_id=validator_id,
            )

            self.logger.info(f"✅ 验证模式: pattern_id={pattern_id}, result={validation_result}")

            return {
                "success": True,
                "pattern_id": pattern_id,
                "validation_result": validation_result,
            }

        except Exception as e:
            self.logger.error(f"❌ 验证模式失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 综合查询 ====================

    async def get_external_knowledge_summary(
        self,
        db: Session,
        project_id: int,
    ) -> Dict[str, Any]:
        """
        获取外部知识关联的综合摘要

        Args:
            db: 数据库会话
            project_id: 项目ID

        Returns:
            Dict: 综合摘要
        """
        try:
            # 1. 思维模式统计
            local_patterns = db.query(ThinkingPattern).filter(
                ThinkingPattern.project_id == project_id,
                ThinkingPattern.is_active == True,
            ).all()

            # 2. 跨项目可用模式
            cross_patterns = self.pattern_service.retrieve_patterns_cross_project(
                db=db,
                current_project_id=project_id,
                limit=50,
            )

            # 3. Skill知识库
            skill_knowledge = db.query(SkillKnowledgeBase).filter(
                SkillKnowledgeBase.project_id == project_id,
                SkillKnowledgeBase.is_active == True,
            ).all()

            # 4. 领域知识
            domain_knowledge = db.query(DomainKnowledge).all()

            return {
                "success": True,
                "project_id": project_id,
                "summary": {
                    "local_patterns": {
                        "total": len(local_patterns),
                        "validated": sum(1 for p in local_patterns if p.is_validated),
                        "by_type": self._count_by_type(local_patterns),
                    },
                    "cross_project_patterns": {
                        "available": len(cross_patterns),
                        "avg_confidence": sum(p.confidence_score or 0 for p in cross_patterns) / len(cross_patterns) if cross_patterns else 0,
                    },
                    "skill_knowledge_base": {
                        "total_entries": len(skill_knowledge),
                        "by_type": self._count_knowledge_by_type(skill_knowledge),
                    },
                    "domain_knowledge": {
                        "total_entries": len(domain_knowledge),
                        "usage_constraint": "background_only",
                        "influence_flags": {
                            "can_influence_decision": False,
                            "can_influence_analysis": False,
                            "can_influence_report": False,
                        },
                    },
                },
            }

        except Exception as e:
            self.logger.error(f"❌ 获取外部知识摘要失败: {e}")
            return {"success": False, "error": str(e)}

    # ==================== 辅助方法 ====================

    def _count_by_type(self, patterns: List[ThinkingPattern]) -> Dict[str, int]:
        """统计模式类型分布"""
        counts = {}
        for p in patterns:
            counts[p.pattern_type] = counts.get(p.pattern_type, 0) + 1
        return counts

    def _count_knowledge_by_type(self, knowledge_list: List[SkillKnowledgeBase]) -> Dict[str, int]:
        """统计知识类型分布"""
        counts = {}
        for k in knowledge_list:
            counts[k.knowledge_type] = counts.get(k.knowledge_type, 0) + 1
        return counts


# 全局单例
_external_knowledge_integration: Optional[ExternalKnowledgeIntegration] = None


def get_external_knowledge_integration() -> ExternalKnowledgeIntegration:
    """获取外部知识集成单例"""
    global _external_knowledge_integration
    if _external_knowledge_integration is None:
        _external_knowledge_integration = ExternalKnowledgeIntegration()
    return _external_knowledge_integration
