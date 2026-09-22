"""
Skills集成服务 - 知识图谱 ↔ 文件 ↔ Skills 三者互动

🎯 核心功能：
1. 知识图谱节点 → Skills（节点关联的思路、书籍技能）
2. Skills → 知识图谱节点（技能涉及的实体和概念）
3. 文件 → 知识图谱节点（文档中提取的实体）
4. 三者互动：Skills ↔ 图谱 ↔ 文件，双向关联

使用场景：
- 点击图谱节点"张三" → 显示相关技能（木工技艺）、相关文档
- 点击技能"民俗调查方法" → 显示涉及的实体、文档
- 点击文档"XX村调研报告.pdf" → 显示提取的图谱节点

架构：
┌─────────────────────────────────────────────────────────────┐
│                  SkillsIntegrationService                    │
│                                                               │
│   ┌────────────┐      ┌──────────────┐      ┌────────────┐ │
│   │   Skills   │◄────►│ Knowledge     │◄────►│ Documents  │ │
│   │  (思路/书籍) │      │ Graph (图谱) │      │  (调研文件) │ │
│   └────────────┘      └──────────────┘      └────────────┘ │
│         ▲                     ▲                     ▲         │
│         │                     │                     │         │
│         └─────────────────────┴─────────────────────┘         │
│                      关联度评分引擎                             │
└─────────────────────────────────────────────────────────────┘

作者：FieldMind Team
日期：2024
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from app.core.logging import logger
from app.models.knowledge_graph import GraphNode, GraphEdge, NodeType, EdgeType
from pydantic import BaseModel, Field
from enum import Enum
import hashlib


class AssociationType(str, Enum):
    """关联类型"""
    SKILL_TO_NODE = "skill_to_node"           # 技能 → 节点
    NODE_TO_SKILL = "node_to_skill"           # 节点 → 技能
    DOCUMENT_TO_NODE = "document_to_node"     # 文档 → 节点
    NODE_TO_DOCUMENT = "node_to_document"     # 节点 → 文档
    SKILL_TO_DOCUMENT = "skill_to_document"   # 技能 → 文档
    DOCUMENT_TO_SKILL = "document_to_skill"   # 文档 → 技能


class SkillType(str, Enum):
    """技能类型（中文）"""
    THOUGHT = "思路"      # 思路类技能（分析方法、理论框架）
    BOOK = "书籍"         # 书籍类技能（参考文献、理论来源）
    METHOD = "方法"       # 方法类技能（调研方法、分析工具）
    TOOL = "工具"         # 工具类技能（技术工具）
    OTHER = "其他"


class Association(BaseModel):
    """关联记录"""
    association_id: str
    association_type: AssociationType

    # 三个主体（至少两个非空）
    skill_id: Optional[str] = None
    skill_name: Optional[str] = None
    skill_type: Optional[SkillType] = None

    node_id: Optional[str] = None
    node_name: Optional[str] = None
    node_type: Optional[NodeType] = None

    document_id: Optional[str] = None
    document_name: Optional[str] = None
    document_path: Optional[str] = None

    # 关联强度
    strength: float = Field(ge=0.0, le=1.0, description="关联强度 0.0-1.0")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0.0-1.0")

    # 证据
    evidence: List[str] = Field(default_factory=list, description="关联证据")
    reasoning: Optional[str] = Field(None, description="关联推理说明")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    verified: bool = False


class SkillGraphLink(BaseModel):
    """技能-图谱链接"""
    skill_id: str
    skill_name: str
    skill_type: SkillType

    related_nodes: List[str] = Field(default_factory=list, description="相关节点ID列表")
    core_concepts: List[str] = Field(default_factory=list, description="核心概念列表（中文）")

    # 统计
    total_nodes: int = 0
    avg_association_strength: float = 0.0


class DocumentGraphLink(BaseModel):
    """文档-图谱链接"""
    document_id: str
    document_name: str
    document_path: str

    extracted_nodes: List[str] = Field(default_factory=list, description="提取的节点ID列表")
    extracted_relations: List[str] = Field(default_factory=list, description="提取的关系ID列表")

    # 统计
    total_entities: int = 0
    total_relations: int = 0


class TripleInteractionResult(BaseModel):
    """三者互动查询结果"""
    query_type: str  # "from_skill" / "from_node" / "from_document"
    query_id: str
    query_name: str

    # 关联的三者
    related_skills: List[SkillGraphLink] = Field(default_factory=list)
    related_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    related_documents: List[DocumentGraphLink] = Field(default_factory=list)

    # 统计
    total_associations: int = 0


class SkillsIntegrationService:
    """
    Skills集成服务

    核心功能：
    1. 建立 知识图谱节点 ↔ Skills 双向关联
    2. 建立 文档 ↔ 知识图谱节点 双向关联
    3. 建立 Skills ↔ 文档 双向关联
    4. 三者互动查询
    5. 关联强度评分
    """
    def __init__(self, use_workflow_engine: bool = True):

        # 关联存储（内存，实际应该持久化到数据库）
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.associations: Dict[str, Association] = {}

        # 索引（快速查询）
        self.skill_to_nodes: Dict[str, Set[str]] = {}      # skill_id → {node_ids}
        self.node_to_skills: Dict[str, Set[str]] = {}      # node_id → {skill_ids}
        self.document_to_nodes: Dict[str, Set[str]] = {}   # document_id → {node_ids}
        self.node_to_documents: Dict[str, Set[str]] = {}   # node_id → {document_ids}
        self.skill_to_documents: Dict[str, Set[str]] = {}  # skill_id → {document_ids}
        self.document_to_skills: Dict[str, Set[str]] = {}  # document_id → {skill_ids}

        logger.info("✅ SkillsIntegrationService initialized")

    def link_skill_to_nodes(
        self,
        skill_id: str,
        skill_name: str,
        skill_type: SkillType,
        nodes: List[GraphNode],
        reasoning: str = "自动关联"
    ) -> List[Association]:
        """
        将技能关联到图谱节点

        使用场景：
        - 技能"民俗调查方法" → 关联到节点"春节习俗"、"婚丧嫁娶"
        - 技能"口述史理论"（书籍） → 关联到节点"村史访谈"、"老人口述"

        Args:
            skill_id: 技能ID
            skill_name: 技能名称
            skill_type: 技能类型（思路/书籍/方法/工具）
            nodes: 要关联的节点列表
            reasoning: 关联推理说明

        Returns:
            创建的关联记录列表
        """
        associations = []

        for node in nodes:
            # 计算关联强度
            strength = self._calculate_skill_node_strength(
                skill_name, skill_type, node
            )

            # 生成关联ID
            association_id = self._generate_association_id(
                skill_id, node.id, AssociationType.SKILL_TO_NODE
            )

            # 创建关联
            association = Association(
                association_id=association_id,
                association_type=AssociationType.SKILL_TO_NODE,
                skill_id=skill_id,
                skill_name=skill_name,
                skill_type=skill_type,
                node_id=node.id,
                node_name=node.name,
                node_type=node.type,
                strength=strength,
                confidence=0.8,  # 默认置信度
                evidence=[f"技能'{skill_name}'与节点'{node.name}'语义相关"],
                reasoning=reasoning,
            )

            # 保存关联
            self.associations[association_id] = association
            associations.append(association)

            # 更新索引
            if skill_id not in self.skill_to_nodes:
                self.skill_to_nodes[skill_id] = set()
            self.skill_to_nodes[skill_id].add(node.id)

            if node.id not in self.node_to_skills:
                self.node_to_skills[node.id] = set()
            self.node_to_skills[node.id].add(skill_id)

            logger.debug(f"技能'{skill_name}' → 节点'{node.name}' (强度={strength:.2f})")

        logger.info(f"✅ 技能'{skill_name}'关联到{len(nodes)}个节点")
        return associations

    def link_document_to_nodes(
        self,
        document_id: str,
        document_name: str,
        document_path: str,
        nodes: List[GraphNode],
        relations: List[GraphEdge] = None
    ) -> DocumentGraphLink:
        """
        将文档关联到图谱节点

        使用场景：
        - 文档"XX村调研报告.pdf" → 提取出节点"张三"、"李四"、"春节习俗"

        Args:
            document_id: 文档ID
            document_name: 文档名称
            document_path: 文档路径
            nodes: 从文档中提取的节点列表
            relations: 从文档中提取的关系列表

        Returns:
            文档-图谱链接
        """
        relations = relations or []

        for node in nodes:
            # 生成关联ID
            association_id = self._generate_association_id(
                document_id, node.id, AssociationType.DOCUMENT_TO_NODE
            )

            # 创建关联
            association = Association(
                association_id=association_id,
                association_type=AssociationType.DOCUMENT_TO_NODE,
                document_id=document_id,
                document_name=document_name,
                document_path=document_path,
                node_id=node.id,
                node_name=node.name,
                node_type=node.type,
                strength=1.0,  # 文档直接提取，强度为1.0
                confidence=node.confidence,
                evidence=[f"从文档'{document_name}'中提取"],
                reasoning="实体识别提取",
            )

            self.associations[association_id] = association

            # 更新索引
            if document_id not in self.document_to_nodes:
                self.document_to_nodes[document_id] = set()
            self.document_to_nodes[document_id].add(node.id)

            if node.id not in self.node_to_documents:
                self.node_to_documents[node.id] = set()
            self.node_to_documents[node.id].add(document_id)

        # 创建文档-图谱链接
        link = DocumentGraphLink(
            document_id=document_id,
            document_name=document_name,
            document_path=document_path,
            extracted_nodes=[n.id for n in nodes],
            extracted_relations=[r.id for r in relations],
            total_entities=len(nodes),
            total_relations=len(relations),
        )

        logger.info(f"✅ 文档'{document_name}'关联到{len(nodes)}个节点，{len(relations)}个关系")
        return link

    def link_skill_to_documents(
        self,
        skill_id: str,
        skill_name: str,
        skill_type: SkillType,
        document_ids: List[str],
        document_names: List[str],
        reasoning: str = "技能应用于文档"
    ) -> List[Association]:
        """
        将技能关联到文档

        使用场景：
        - 技能"民俗分析框架" → 应用于"春节习俗调研.pdf"、"婚礼仪式记录.pdf"

        Args:
            skill_id: 技能ID
            skill_name: 技能名称
            skill_type: 技能类型
            document_ids: 文档ID列表
            document_names: 文档名称列表
            reasoning: 关联推理

        Returns:
            关联记录列表
        """
        associations = []

        for doc_id, doc_name in zip(document_ids, document_names):
            association_id = self._generate_association_id(
                skill_id, doc_id, AssociationType.SKILL_TO_DOCUMENT
            )

            association = Association(
                association_id=association_id,
                association_type=AssociationType.SKILL_TO_DOCUMENT,
                skill_id=skill_id,
                skill_name=skill_name,
                skill_type=skill_type,
                document_id=doc_id,
                document_name=doc_name,
                strength=0.8,
                confidence=0.8,
                evidence=[f"技能'{skill_name}'应用于文档'{doc_name}'"],
                reasoning=reasoning,
            )

            self.associations[association_id] = association
            associations.append(association)

            # 更新索引
            if skill_id not in self.skill_to_documents:
                self.skill_to_documents[skill_id] = set()
            self.skill_to_documents[skill_id].add(doc_id)

            if doc_id not in self.document_to_skills:
                self.document_to_skills[doc_id] = set()
            self.document_to_skills[doc_id].add(skill_id)

        logger.info(f"✅ 技能'{skill_name}'关联到{len(document_ids)}个文档")
        return associations

    def query_from_skill(
        self,
        skill_id: str,
        skill_name: str,
        include_nodes: bool = True,
        include_documents: bool = True
    ) -> TripleInteractionResult:
        """
        从技能出发，查询关联的节点和文档

        使用场景：
        - 点击技能"民俗调查方法" → 显示涉及的实体、文档

        Args:
            skill_id: 技能ID
            skill_name: 技能名称
            include_nodes: 是否包含关联节点
            include_documents: 是否包含关联文档

        Returns:
            三者互动查询结果
        """
        result = TripleInteractionResult(
            query_type="from_skill",
            query_id=skill_id,
            query_name=skill_name,
        )

        # 查询关联的节点
        if include_nodes and skill_id in self.skill_to_nodes:
            related_node_ids = self.skill_to_nodes[skill_id]

            for node_id in related_node_ids:
                # 获取关联信息
                association_id = self._generate_association_id(
                    skill_id, node_id, AssociationType.SKILL_TO_NODE
                )
                association = self.associations.get(association_id)

                if association:
                    result.related_nodes.append({
                        "node_id": node_id,
                        "node_name": association.node_name,
                        "node_type": association.node_type,
                        "strength": association.strength,
                        "confidence": association.confidence,
                    })

        # 查询关联的文档
        if include_documents and skill_id in self.skill_to_documents:
            related_doc_ids = self.skill_to_documents[skill_id]

            for doc_id in related_doc_ids:
                association_id = self._generate_association_id(
                    skill_id, doc_id, AssociationType.SKILL_TO_DOCUMENT
                )
                association = self.associations.get(association_id)

                if association:
                    result.related_documents.append(
                        DocumentGraphLink(
                            document_id=doc_id,
                            document_name=association.document_name,
                            document_path=association.document_path or "",
                            extracted_nodes=[],
                            extracted_relations=[],
                        )
                    )

        result.total_associations = len(result.related_nodes) + len(result.related_documents)

        logger.info(f"✅ 技能'{skill_name}': {len(result.related_nodes)}个节点, {len(result.related_documents)}个文档")
        return result

    def query_from_node(
        self,
        node_id: str,
        node_name: str,
        include_skills: bool = True,
        include_documents: bool = True
    ) -> TripleInteractionResult:
        """
        从图谱节点出发，查询关联的技能和文档

        使用场景：
        - 点击节点"张三" → 显示相关技能（木工技艺）、相关文档

        Args:
            node_id: 节点ID
            node_name: 节点名称
            include_skills: 是否包含关联技能
            include_documents: 是否包含关联文档

        Returns:
            三者互动查询结果
        """
        result = TripleInteractionResult(
            query_type="from_node",
            query_id=node_id,
            query_name=node_name,
        )

        # 查询关联的技能
        if include_skills and node_id in self.node_to_skills:
            related_skill_ids = self.node_to_skills[node_id]

            for skill_id in related_skill_ids:
                association_id = self._generate_association_id(
                    skill_id, node_id, AssociationType.SKILL_TO_NODE
                )
                association = self.associations.get(association_id)

                if association:
                    # 获取该技能的所有关联节点
                    all_nodes = self.skill_to_nodes.get(skill_id, set())

                    result.related_skills.append(
                        SkillGraphLink(
                            skill_id=skill_id,
                            skill_name=association.skill_name,
                            skill_type=association.skill_type,
                            related_nodes=list(all_nodes),
                            total_nodes=len(all_nodes),
                            avg_association_strength=association.strength,
                        )
                    )

        # 查询关联的文档
        if include_documents and node_id in self.node_to_documents:
            related_doc_ids = self.node_to_documents[node_id]

            for doc_id in related_doc_ids:
                association_id = self._generate_association_id(
                    doc_id, node_id, AssociationType.DOCUMENT_TO_NODE
                )
                association = self.associations.get(association_id)

                if association:
                    # 获取该文档的所有关联节点
                    all_nodes = self.document_to_nodes.get(doc_id, set())

                    result.related_documents.append(
                        DocumentGraphLink(
                            document_id=doc_id,
                            document_name=association.document_name,
                            document_path=association.document_path or "",
                            extracted_nodes=list(all_nodes),
                            extracted_relations=[],
                            total_entities=len(all_nodes),
                        )
                    )

        result.total_associations = len(result.related_skills) + len(result.related_documents)

        logger.info(f"✅ 节点'{node_name}': {len(result.related_skills)}个技能, {len(result.related_documents)}个文档")
        return result

    def query_from_document(
        self,
        document_id: str,
        document_name: str,
        include_nodes: bool = True,
        include_skills: bool = True
    ) -> TripleInteractionResult:
        """
        从文档出发，查询提取的节点和应用的技能

        使用场景：
        - 点击文档"XX村调研报告.pdf" → 显示提取的图谱节点、应用的技能

        Args:
            document_id: 文档ID
            document_name: 文档名称
            include_nodes: 是否包含提取的节点
            include_skills: 是否包含应用的技能

        Returns:
            三者互动查询结果
        """
        result = TripleInteractionResult(
            query_type="from_document",
            query_id=document_id,
            query_name=document_name,
        )

        # 查询提取的节点
        if include_nodes and document_id in self.document_to_nodes:
            related_node_ids = self.document_to_nodes[document_id]

            for node_id in related_node_ids:
                association_id = self._generate_association_id(
                    document_id, node_id, AssociationType.DOCUMENT_TO_NODE
                )
                association = self.associations.get(association_id)

                if association:
                    result.related_nodes.append({
                        "node_id": node_id,
                        "node_name": association.node_name,
                        "node_type": association.node_type,
                        "strength": association.strength,
                        "confidence": association.confidence,
                    })

        # 查询应用的技能
        if include_skills and document_id in self.document_to_skills:
            related_skill_ids = self.document_to_skills[document_id]

            for skill_id in related_skill_ids:
                association_id = self._generate_association_id(
                    skill_id, document_id, AssociationType.SKILL_TO_DOCUMENT
                )
                association = self.associations.get(association_id)

                if association:
                    result.related_skills.append(
                        SkillGraphLink(
                            skill_id=skill_id,
                            skill_name=association.skill_name,
                            skill_type=association.skill_type,
                            related_nodes=[],
                            total_nodes=0,
                        )
                    )

        result.total_associations = len(result.related_nodes) + len(result.related_skills)

        logger.info(f"✅ 文档'{document_name}': {len(result.related_nodes)}个节点, {len(result.related_skills)}个技能")
        return result

    def _calculate_skill_node_strength(
        self,
        skill_name: str,
        skill_type: SkillType,
        node: GraphNode
    ) -> float:
        """
        计算技能-节点关联强度

        评分维度：
        1. 名称相似度（30%）
        2. 类型匹配度（20%）
        3. 上下文相似度（30%）
        4. 重要性加权（20%）

        Returns:
            0.0-1.0
        """
        score = 0.0

        # 1. 名称相似度（简单的包含关系）
        if skill_name in node.name or node.name in skill_name:
            score += 0.3
        elif any(word in node.name for word in skill_name.split()):
            score += 0.15

        # 2. 类型匹配度
        if skill_type == SkillType.THOUGHT and node.type == NodeType.CORE_KEYWORD:
            score += 0.2  # 思路类技能 ↔ 核心关键词
        elif skill_type == SkillType.BOOK and node.type in [NodeType.PERSON, NodeType.ORGANIZATION]:
            score += 0.15  # 书籍 ↔ 人物/组织
        elif skill_type == SkillType.METHOD and node.type in [NodeType.CUSTOM, NodeType.RITUAL]:
            score += 0.2  # 方法 ↔ 民俗/仪式
        else:
            score += 0.1

        # 3. 上下文相似度（基于描述）
        if node.description and skill_name:
            if skill_name in node.description or any(word in node.description for word in skill_name.split()):
                score += 0.3
            else:
                score += 0.1

        # 4. 重要性加权
        if node.is_core_keyword:
            score += 0.2
        elif node.importance_score > 0.7:
            score += 0.15
        else:
            score += 0.1

        return min(score, 1.0)

    def _generate_association_id(
        self,
        id1: str,
        id2: str,
        association_type: AssociationType
    ) -> str:
        """生成关联ID（基于MD5哈希）"""
        raw = f"{id1}_{id2}_{association_type}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_associations": len(self.associations),
            "skills": {
                "total": len(self.skill_to_nodes),
                "linked_to_nodes": sum(len(nodes) for nodes in self.skill_to_nodes.values()),
                "linked_to_documents": sum(len(docs) for docs in self.skill_to_documents.values()),
            },
            "nodes": {
                "total": len(self.node_to_skills) + len(self.node_to_documents),
                "linked_to_skills": sum(len(skills) for skills in self.node_to_skills.values()),
                "linked_to_documents": sum(len(docs) for docs in self.node_to_documents.values()),
            },
            "documents": {
                "total": len(self.document_to_nodes),
                "extracted_nodes": sum(len(nodes) for nodes in self.document_to_nodes.values()),
                "linked_to_skills": sum(len(skills) for skills in self.document_to_skills.values()),
            },
        }


# ========== 工厂函数 ==========

def get_skills_integration_service() -> SkillsIntegrationService:
    """获取Skills集成服务单例"""
    return SkillsIntegrationService()
