"""
Skill Evolution Integration for SynthesisAgent
将Skill演化记忆集成到SynthesisAgent中
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.services.skill_evolution_service import get_skill_evolution_service
from app.models.skill_version import SkillVersion

logger = logging.getLogger(__name__)


class SkillEvolutionIntegration:
    """技能演化集成模块 - SynthesisAgent的Skill记忆扩展"""

    def __init__(self):
        self.evolution_service = get_skill_evolution_service()
        self.logger = logger

    async def track_skill_execution(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        execution_result: Dict[str, Any],
    ) -> None:
        """
        追踪Skill执行结果，自动记录使用统计

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            execution_result: 执行结果
                {
                    "success": bool,
                    "execution_time": float,
                    "error": str (optional),
                    "output": Any
                }
        """
        success = execution_result.get("success", False)
        execution_time = execution_result.get("execution_time")

        try:
            self.evolution_service.record_usage(
                db=db,
                skill_id=skill_id,
                project_id=project_id,
                success=success,
                execution_time=execution_time,
            )
            self.logger.debug(
                f"📊 Tracked skill execution: skill_id={skill_id}, success={success}"
            )
        except Exception as e:
            self.logger.error(f"❌ Failed to track skill execution: {e}")

    async def auto_detect_skill_changes(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        current_content: str,
        change_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[SkillVersion]:
        """
        自动检测Skill的变更并创建新版本

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            current_content: 当前技能内容
            change_context: 变更上下文
                {
                    "user_id": int,
                    "change_reason": str,
                    "adjustment_type": str  # "manual", "auto_optimize", "feedback_based"
                }

        Returns:
            Optional[SkillVersion]: 如果检测到变更，返回新版本；否则返回None
        """
        try:
            # 获取当前活跃版本
            active_version = self.evolution_service.get_active_version(
                db, skill_id, project_id
            )

            if not active_version:
                self.logger.warning(
                    f"No active version found for skill_id={skill_id}, creating initial version"
                )
                # 如果没有活跃版本，创建初始版本
                return self.evolution_service.create_initial_version(
                    db=db,
                    skill_id=skill_id,
                    project_id=project_id,
                    skill_name=change_context.get("skill_name", f"Skill-{skill_id}"),
                    skill_content=current_content,
                    user_id=change_context.get("user_id") if change_context else None,
                )

            # 检查内容是否有变化
            if active_version.skill_content == current_content:
                self.logger.debug(f"No content change detected for skill_id={skill_id}")
                return None

            # 根据变更类型记录新版本
            adjustment_type = (
                change_context.get("adjustment_type", "manual") if change_context else "manual"
            )
            change_reason = (
                change_context.get("change_reason", "User adjustment")
                if change_context
                else "User adjustment"
            )
            user_id = change_context.get("user_id") if change_context else None

            if adjustment_type == "auto_optimize":
                new_version = self.evolution_service.record_optimization(
                    db=db,
                    skill_id=skill_id,
                    project_id=project_id,
                    optimized_content=current_content,
                    optimization_reason=change_reason,
                    user_id=user_id,
                )
            else:
                new_version = self.evolution_service.record_adjustment(
                    db=db,
                    skill_id=skill_id,
                    project_id=project_id,
                    new_skill_content=current_content,
                    adjustment_description=change_reason,
                    user_id=user_id,
                )

            self.logger.info(
                f"✅ Detected and recorded skill change: v{active_version.version_number} → v{new_version.version_number}"
            )
            return new_version

        except Exception as e:
            self.logger.error(f"❌ Failed to detect skill changes: {e}")
            return None

    async def get_skill_evolution_summary(
        self, db: Session, skill_id: int, project_id: int
    ) -> Dict[str, Any]:
        """
        获取技能的演化摘要

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID

        Returns:
            Dict: 演化摘要
        """
        try:
            # 获取版本历史
            history = self.evolution_service.get_version_history(
                db, skill_id, project_id, limit=10
            )

            # 获取活跃版本
            active_version = self.evolution_service.get_active_version(
                db, skill_id, project_id
            )

            # 生成优化建议
            suggestions = self.evolution_service.generate_optimization_suggestions(
                db, skill_id, project_id
            )

            return {
                "skill_id": skill_id,
                "project_id": project_id,
                "total_versions": len(history),
                "active_version": active_version.to_dict() if active_version else None,
                "recent_history": [v.to_dict() for v in history[:5]],
                "optimization_suggestions": suggestions,
                "evolution_timeline": [
                    {
                        "version": v.version_number,
                        "change_type": v.change_type,
                        "created_at": v.created_at.isoformat() if v.created_at else None,
                        "success_rate": v.success_rate,
                        "usage_count": v.usage_count,
                    }
                    for v in history
                ],
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get skill evolution summary: {e}")
            return {
                "skill_id": skill_id,
                "project_id": project_id,
                "error": str(e),
            }

    async def suggest_skill_optimization(
        self, db: Session, skill_id: int, project_id: int
    ) -> List[Dict[str, Any]]:
        """
        基于使用统计建议Skill优化方案

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID

        Returns:
            List[Dict]: 优化建议列表
        """
        try:
            suggestions = self.evolution_service.generate_optimization_suggestions(
                db, skill_id, project_id
            )

            # 增强建议：添加具体的优化行动
            enhanced_suggestions = []
            for suggestion in suggestions:
                enhanced = suggestion.copy()

                if suggestion["type"] == "low_success_rate":
                    enhanced["recommended_actions"] = [
                        "检查Skill逻辑是否正确",
                        "添加更多错误处理",
                        "优化输入验证",
                        "考虑回滚到成功率更高的历史版本",
                    ]

                elif suggestion["type"] == "high_execution_time":
                    enhanced["recommended_actions"] = [
                        "优化算法复杂度",
                        "添加缓存机制",
                        "减少外部API调用",
                        "使用异步处理",
                    ]

                elif suggestion["type"] == "better_historical_version":
                    enhanced["recommended_actions"] = [
                        f"考虑回滚到版本 v{suggestion['suggested_version']}",
                        "对比当前版本与历史版本的差异",
                        "分析导致性能下降的变更",
                    ]

                elif suggestion["type"] == "low_usage":
                    enhanced["recommended_actions"] = [
                        "评估Skill的实际价值",
                        "考虑归档或删除",
                        "重新设计以提高实用性",
                        "与用户沟通了解需求",
                    ]

                enhanced_suggestions.append(enhanced)

            return enhanced_suggestions

        except Exception as e:
            self.logger.error(f"❌ Failed to generate optimization suggestions: {e}")
            return []

    async def compare_skill_versions(
        self,
        db: Session,
        skill_id: int,
        project_id: int,
        version_a: int,
        version_b: int,
    ) -> Dict[str, Any]:
        """
        比较两个Skill版本的差异和性能

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID
            version_a: 版本A号
            version_b: 版本B号

        Returns:
            Dict: 比较结果
        """
        try:
            comparison = self.evolution_service.compare_versions(
                db, skill_id, project_id, version_a, version_b
            )

            # 添加可视化建议
            perf_a = comparison["performance_comparison"]["version_a"]
            perf_b = comparison["performance_comparison"]["version_b"]

            recommendation = None
            if (
                perf_a["success_rate"] is not None
                and perf_b["success_rate"] is not None
            ):
                if perf_a["success_rate"] > perf_b["success_rate"] + 0.1:
                    recommendation = f"版本 v{version_a} 表现更优，建议回滚到此版本"
                elif perf_b["success_rate"] > perf_a["success_rate"] + 0.1:
                    recommendation = f"版本 v{version_b} 表现更优，继续使用当前版本"
                else:
                    recommendation = "两个版本性能相近，根据功能需求选择"

            comparison["recommendation"] = recommendation
            return comparison

        except Exception as e:
            self.logger.error(f"❌ Failed to compare skill versions: {e}")
            return {"error": str(e)}

    async def export_skill_evolution_to_cognee(
        self, db: Session, skill_id: int, project_id: int
    ) -> Dict[str, Any]:
        """
        将Skill演化历史导出到Cognee知识图谱

        Args:
            db: 数据库会话
            skill_id: 技能ID
            project_id: 项目ID

        Returns:
            Dict: 导出结果
        """
        try:
            # 获取演化历史
            history = self.evolution_service.get_version_history(
                db, skill_id, project_id, limit=50
            )

            if not history:
                return {"success": False, "message": "No history found"}

            # 构建知识图谱数据
            skill_name = history[0].skill_name
            knowledge_entries = []

            # 主Skill节点
            main_entry = {
                "type": "skill",
                "id": f"skill_{skill_id}",
                "name": skill_name,
                "project_id": project_id,
                "total_versions": len(history),
                "created_at": history[-1].created_at.isoformat()
                if history[-1].created_at
                else None,
            }
            knowledge_entries.append(main_entry)

            # 版本节点和关系
            for version in history:
                version_entry = {
                    "type": "skill_version",
                    "id": f"skill_version_{version.id}",
                    "version_number": version.version_number,
                    "change_type": version.change_type,
                    "change_summary": version.change_summary,
                    "success_rate": version.success_rate,
                    "usage_count": version.usage_count,
                    "created_at": version.created_at.isoformat()
                    if version.created_at
                    else None,
                    "parent_skill": f"skill_{skill_id}",
                }

                if version.parent_version_id:
                    version_entry["evolved_from"] = f"skill_version_{version.parent_version_id}"

                knowledge_entries.append(version_entry)

            # 这里可以调用Cognee API存储
            # 由于Cognee集成在SynthesisAgent中，这里返回结构化数据
            # 实际存储由SynthesisAgent调用

            self.logger.info(
                f"✅ Prepared {len(knowledge_entries)} knowledge entries for Cognee export"
            )

            return {
                "success": True,
                "skill_id": skill_id,
                "skill_name": skill_name,
                "entries_count": len(knowledge_entries),
                "knowledge_entries": knowledge_entries,
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to export to Cognee: {e}")
            return {"success": False, "error": str(e)}


# 全局单例
_skill_evolution_integration: Optional[SkillEvolutionIntegration] = None


def get_skill_evolution_integration() -> SkillEvolutionIntegration:
    """获取技能演化集成单例"""
    global _skill_evolution_integration
    if _skill_evolution_integration is None:
        _skill_evolution_integration = SkillEvolutionIntegration()
    return _skill_evolution_integration
