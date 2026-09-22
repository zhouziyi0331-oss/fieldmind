"""
经验知识图谱服务

基于现有知识图谱基础设施，实现AI自学习的经验沉淀
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.knowledge_graph import (
    KnowledgeNode,
    KnowledgeRelation,
    NodeType,
    RelationType
)


class ExperienceGraphService:
    """经验图谱服务 - 使用现有知识图谱基础设施"""
    def __init__(self, db: Session, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.db = db
        self.graph_type = "experience_learning"  # 标识为经验学习图谱

    # ==================== 节点管理 ====================

    def create_experience_node(
        self,
        project_id: int,
        node_type: str,  # "概念", "模式", "技能", "经验", "洞察", "教训"
        node_name: str,
        description: str,
        content: Dict[str, Any],
        confidence: float = 0.5,
        tags: Optional[List[str]] = None,
        related_ids: Optional[Dict[str, Any]] = None
    ) -> KnowledgeNode:
        """
        创建经验知识节点

        Args:
            project_id: 项目ID
            node_type: 节点类型
            node_name: 节点名称
            description: 描述
            content: 内容（what/when/how/why/evidence）
            confidence: 置信度
            tags: 标签
            related_ids: 关联的实体ID

        Returns:
            知识节点
        """
        # 将自学习系统的节点类型映射到现有NodeType
        type_mapping = {
            "概念": NodeType.CONCEPT,
            "模式": NodeType.PATTERN,
            "技能": NodeType.SKILL,
            "经验": NodeType.EXPERIENCE,
            "洞察": NodeType.INSIGHT,
            "教训": NodeType.LESSON
        }

        # 如果NodeType枚举中没有这些类型，使用CUSTOM
        mapped_type = type_mapping.get(node_type, NodeType.CUSTOM)

        # 扩展content，添加图谱类型标识
        extended_content = {
            "graph_type": self.graph_type,
            "core_content": content,
            "confidence_score": confidence
        }

        if related_ids:
            extended_content["related_entities"] = related_ids

        # 创建节点
        node = KnowledgeNode(
            node_type=mapped_type,
            name_zh=node_name,
            name_en=node_name,  # 英文名暂时与中文相同
            description_zh=description,
            description_en=description,
            project_id=project_id,
            properties=extended_content,
            tags=tags or []
        )

        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)

        return node

    def create_relation(
        self,
        source_node_id: str,
        target_node_id: str,
        relation_type: str,  # "派生自", "依赖于", "相似于", etc.
        project_id: int,
        strength: float = 0.5,
        description: Optional[str] = None,
        evidence: Optional[List[str]] = None
    ) -> KnowledgeRelation:
        """
        创建节点关系

        Args:
            source_node_id: 源节点ID
            target_node_id: 目标节点ID
            relation_type: 关系类型
            project_id: 项目ID
            strength: 关系强度
            description: 描述
            evidence: 证据

        Returns:
            知识关系
        """
        # 映射关系类型
        type_mapping = {
            "派生自": RelationType.DERIVED_FROM,
            "依赖于": RelationType.DEPENDS_ON,
            "相似于": RelationType.SIMILAR_TO,
            "矛盾于": RelationType.CONTRADICTS,
            "导致": RelationType.LEADS_TO,
            "属于": RelationType.PART_OF,
            "启用": RelationType.ENABLES
        }

        mapped_type = type_mapping.get(relation_type, RelationType.RELATED_TO)

        # 创建关系
        relation = KnowledgeRelation(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relation_type=mapped_type,
            description_zh=description or f"{relation_type}关系",
            project_id=project_id,
            properties={
                "graph_type": self.graph_type,
                "strength": strength,
                "evidence": evidence or []
            }
        )

        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)

        return relation

    # ==================== 从自学习系统导入 ====================

    def import_from_pattern(
        self,
        pattern_id: str,
        project_id: int
    ) -> KnowledgeNode:
        """从模式创建知识节点"""
        from app.models.pattern_library import PatternLibrary

        pattern = self.db.query(PatternLibrary).filter(
            PatternLibrary.id == pattern_id
        ).first()

        if not pattern:
            raise ValueError(f"模式 {pattern_id} 不存在")

        # 将模式转换为知识节点
        content = {
            "what": f"识别出的{pattern.pattern_type.value}模式",
            "pattern_definition": pattern.pattern_definition,
            "success_rate": pattern.success_count / pattern.occurrence_count if pattern.occurrence_count > 0 else 0,
            "usage_count": pattern.usage_count,
            "evidence": pattern.source_execution_ids
        }

        node = self.create_experience_node(
            project_id=project_id,
            node_type="模式",
            node_name=pattern.pattern_name,
            description=pattern.pattern_description,
            content=content,
            confidence=pattern.confidence_score,
            tags=[pattern.pattern_type.value],
            related_ids={"pattern_id": pattern_id}
        )

        return node

    def import_from_skill(
        self,
        skill_id: str,
        project_id: int
    ) -> KnowledgeNode:
        """从生成的技能创建知识节点"""
        from app.models.generated_skill import GeneratedSkill

        skill = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.id == skill_id
        ).first()

        if not skill:
            raise ValueError(f"技能 {skill_id} 不存在")

        # 将技能转换为知识节点
        content = {
            "what": f"自动生成的{skill.skill_category}技能",
            "how": "从模式自动生成",
            "code_snippet": skill.skill_code[:500],  # 只保存前500字符
            "success_rate": skill.success_count / (skill.success_count + skill.failure_count) if (skill.success_count + skill.failure_count) > 0 else 0,
            "quality_score": skill.quality_score,
            "evidence": skill.source_execution_ids
        }

        node = self.create_experience_node(
            project_id=project_id,
            node_type="技能",
            node_name=skill.skill_name,
            description=skill.skill_description,
            content=content,
            confidence=skill.confidence_score,
            tags=[skill.skill_category] if skill.skill_category else [],
            related_ids={"skill_id": skill_id}
        )

        return node

    def import_from_insight(
        self,
        insight_id: str,
        project_id: int
    ) -> KnowledgeNode:
        """从学习洞察创建知识节点"""
        from app.models.background_learning import LearningInsight

        insight = self.db.query(LearningInsight).filter(
            LearningInsight.id == insight_id
        ).first()

        if not insight:
            raise ValueError(f"洞察 {insight_id} 不存在")

        # 将洞察转换为知识节点
        content = {
            "what": insight.insight_title,
            "why": insight.insight_description,
            "evidence": insight.insight_data,
            "suggested_actions": insight.suggested_actions,
            "importance": insight.importance_score
        }

        node = self.create_experience_node(
            project_id=project_id,
            node_type="洞察",
            node_name=insight.insight_title,
            description=insight.insight_description,
            content=content,
            confidence=insight.confidence_score,
            tags=[insight.insight_type],
            related_ids={"insight_id": insight_id}
        )

        return node

    def import_from_feedback_loop(
        self,
        loop_id: str,
        project_id: int
    ) -> KnowledgeNode:
        """从反馈闭环创建经验节点"""
        from app.models.feedback_loop import FeedbackLoop

        loop = self.db.query(FeedbackLoop).filter(
            FeedbackLoop.id == loop_id
        ).first()

        if not loop:
            raise ValueError(f"反馈闭环 {loop_id} 不存在")

        # 将反馈闭环的教训转换为知识节点
        if not loop.lessons_extracted:
            return None

        lessons = loop.lessons_extracted
        content = {
            "what": "从执行反馈中学到的经验",
            "when": f"执行ID: {loop.execution_id}",
            "what_worked": lessons.get("what_worked", []),
            "what_failed": lessons.get("what_failed", []),
            "recommendations": lessons.get("recommendations", []),
            "feedback_score": loop.feedback_score
        }

        node = self.create_experience_node(
            project_id=project_id,
            node_type="经验" if loop.feedback_score >= 0.7 else "教训",
            node_name=f"反馈闭环经验_{loop.id[:8]}",
            description="从用户反馈和执行结果中提取的经验教训",
            content=content,
            confidence=loop.feedback_score,
            tags=["feedback_loop"],
            related_ids={
                "feedback_loop_id": loop_id,
                "execution_id": loop.execution_id
            }
        )

        return node

    # ==================== 查询接口 ====================

    def query_experience_nodes(
        self,
        project_id: int,
        node_type: Optional[str] = None,
        min_confidence: float = 0.0,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """查询经验知识节点"""
        query = self.db.query(KnowledgeNode).filter(
            KnowledgeNode.project_id == project_id
        )

        # 筛选经验学习图谱的节点
        # 通过properties字段中的graph_type来识别
        nodes = query.all()

        experience_nodes = []
        for node in nodes:
            if node.properties and node.properties.get("graph_type") == self.graph_type:
                # 应用过滤条件
                if node_type and node.node_type.value != node_type:
                    continue

                confidence = node.properties.get("confidence_score", 0)
                if confidence < min_confidence:
                    continue

                if tags and not any(tag in node.tags for tag in tags):
                    continue

                experience_nodes.append(node)

                if len(experience_nodes) >= limit:
                    break

        return experience_nodes

    def get_related_nodes(
        self,
        node_id: str,
        relation_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取相关节点"""
        relations = self.db.query(KnowledgeRelation).filter(
            KnowledgeRelation.source_node_id == node_id
        ).all()

        if relation_types:
            relations = [r for r in relations if r.relation_type.value in relation_types]

        result = []
        for relation in relations:
            target_node = self.db.query(KnowledgeNode).filter(
                KnowledgeNode.id == relation.target_node_id
            ).first()

            if target_node:
                result.append({
                    "relation": relation,
                    "node": target_node
                })

        return result

    def build_graph_from_learning_history(
        self,
        project_id: int
    ) -> Dict[str, int]:
        """
        从学习历史构建知识图谱

        Returns:
            统计信息
        """
        stats = {
            "patterns_imported": 0,
            "skills_imported": 0,
            "insights_imported": 0,
            "experiences_imported": 0,
            "relations_created": 0
        }

        # 1. 导入模式
        from app.models.pattern_library import PatternLibrary
        patterns = self.db.query(PatternLibrary).filter(
            PatternLibrary.project_id == project_id
        ).limit(50).all()

        for pattern in patterns:
            try:
                self.import_from_pattern(pattern.id, project_id)
                stats["patterns_imported"] += 1
            except:
                pass

        # 2. 导入技能
        from app.models.generated_skill import GeneratedSkill
        skills = self.db.query(GeneratedSkill).filter(
            GeneratedSkill.project_id == project_id,
            GeneratedSkill.is_active == True
        ).limit(50).all()

        for skill in skills:
            try:
                self.import_from_skill(skill.id, project_id)
                stats["skills_imported"] += 1
            except:
                pass

        # 3. 导入洞察
        from app.models.background_learning import LearningInsight
        insights = self.db.query(LearningInsight).filter(
            LearningInsight.project_id == project_id,
            LearningInsight.importance_score >= 0.7
        ).limit(50).all()

        for insight in insights:
            try:
                self.import_from_insight(insight.id, project_id)
                stats["insights_imported"] += 1
            except:
                pass

        return stats
