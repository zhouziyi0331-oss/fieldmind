"""
Step 6: 本体构建服务（核心步骤）
Ontology Construction Service - CORE STEP

功能：
1. 概念聚类（Concept Clustering）
2. 关系泛化（Relation Generalization）
3. 约束定义（Constraint Definition）
4. 公理生成（Axiom Generation）
5. OWL 导出（OWL Export）

这是核心步骤，定义知识世界的"分类体系和交通规则"
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, Counter
import xml.etree.ElementTree as ET
from xml.dom import minidom

logger = logging.getLogger(__name__)


class ConceptType(str, Enum):
    """概念类型"""
    ENTITY_CONCEPT = "entity_concept"  # 实体概念
    EVENT_CONCEPT = "event_concept"  # 事件概念
    RELATION_CONCEPT = "relation_concept"  # 关系概念
    ATTRIBUTE_CONCEPT = "attribute_concept"  # 属性概念


class AxiomType(str, Enum):
    """公理类型"""
    SUBCLASS = "subclass"  # 子类关系
    EQUIVALENT = "equivalent"  # 等价关系
    DISJOINT = "disjoint"  # 互斥关系
    TRANSITIVE = "transitive"  # 传递性
    SYMMETRIC = "symmetric"  # 对称性
    FUNCTIONAL = "functional"  # 函数性
    INVERSE = "inverse"  # 逆关系
    DOMAIN = "domain"  # 定义域
    RANGE = "range"  # 值域
    COMPOSITION = "composition"  # 组合关系


@dataclass
class Concept:
    """概念"""
    id: str
    name: str
    type: ConceptType
    description: str = ""

    # 层次
    parent_concepts: List[str] = field(default_factory=list)
    child_concepts: List[str] = field(default_factory=list)

    # 实例
    instances: List[str] = field(default_factory=list)  # 实体ID列表

    # 属性
    attributes: Dict[str, Any] = field(default_factory=dict)

    # 统计
    instance_count: int = 0
    confidence: float = 1.0


@dataclass
class RelationType:
    """关系类型（泛化后的关系）"""
    id: str
    name: str
    description: str = ""

    # 约束
    domain: List[str] = field(default_factory=list)  # 定义域（源概念）
    range: List[str] = field(default_factory=list)  # 值域（目标概念）

    # 属性
    is_transitive: bool = False
    is_symmetric: bool = False
    is_functional: bool = False
    inverse_of: Optional[str] = None

    # 实例
    instances: List[str] = field(default_factory=list)  # 关系ID列表
    instance_count: int = 0


@dataclass
class Axiom:
    """公理"""
    id: str
    type: AxiomType
    subject: str  # 主体（概念或关系ID）
    object: Optional[str] = None  # 客体（概念或关系ID）
    description: str = ""
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)


@dataclass
class Ontology:
    """本体"""
    name: str
    version: str = "1.0"

    # 核心组件
    concepts: Dict[str, Concept] = field(default_factory=dict)
    relation_types: Dict[str, RelationType] = field(default_factory=dict)
    axioms: List[Axiom] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConceptClusterer:
    """概念聚类器"""

    def cluster(self, entities: List[Any]) -> List[Concept]:
        """将实体聚类为概念"""
        concepts = []
        concept_id = 0

        # 按实体类型分组
        type_groups = defaultdict(list)
        for entity in entities:
            if hasattr(entity, 'type'):
                entity_type = entity.type.value
                type_groups[entity_type].append(entity)

        # 为每个类型创建概念
        for entity_type, entity_list in type_groups.items():
            # 基础概念
            base_concept = Concept(
                id=f"concept_{concept_id}",
                name=self._type_to_concept_name(entity_type),
                type=ConceptType.ENTITY_CONCEPT,
                description=f"所有{entity_type}类型的实体",
                instances=[e.id for e in entity_list if hasattr(e, 'id')],
                instance_count=len(entity_list)
            )
            concepts.append(base_concept)
            concept_id += 1

            # 进一步细分（基于属性或名称模式）
            subconcepts = self._create_subconcepts(entity_list, entity_type, concept_id)
            for subconcept in subconcepts:
                subconcept.parent_concepts = [base_concept.id]
                base_concept.child_concepts.append(subconcept.id)
            concepts.extend(subconcepts)
            concept_id += len(subconcepts)

        logger.info(f"✅ 概念聚类：{len(entities)} 个实体 → {len(concepts)} 个概念")
        return concepts

    def _type_to_concept_name(self, entity_type: str) -> str:
        """实体类型转概念名称"""
        mapping = {
            'person': '人物',
            'location': '地点',
            'organization': '组织',
            'time': '时间',
            'event': '事件',
            'object': '物品',
            'concept': '概念',
        }
        return mapping.get(entity_type, entity_type)

    def _create_subconcepts(
        self,
        entities: List[Any],
        base_type: str,
        start_id: int
    ) -> List[Concept]:
        """创建子概念"""
        subconcepts = []

        if base_type == 'person':
            # 人物子类：按职业、身份等分类
            occupation_groups = defaultdict(list)
            for entity in entities:
                if hasattr(entity, 'name'):
                    # 简单启发式：根据称谓判断
                    name = entity.name
                    if any(title in name for title in ['教授', '博士', '学者']):
                        occupation_groups['学者'].append(entity)
                    elif any(title in name for title in ['总统', '主席', '市长', '县长']):
                        occupation_groups['政治人物'].append(entity)
                    elif any(title in name for title in ['将军', '元帅', '司令']):
                        occupation_groups['军事人物'].append(entity)
                    else:
                        occupation_groups['一般人物'].append(entity)

            for occupation, group in occupation_groups.items():
                if len(group) >= 2:  # 至少2个实例
                    subconcepts.append(Concept(
                        id=f"concept_{start_id + len(subconcepts)}",
                        name=occupation,
                        type=ConceptType.ENTITY_CONCEPT,
                        description=f"{occupation}类人物",
                        instances=[e.id for e in group if hasattr(e, 'id')],
                        instance_count=len(group)
                    ))

        elif base_type == 'location':
            # 地点子类：按行政级别分类
            level_groups = defaultdict(list)
            for entity in entities:
                if hasattr(entity, 'name'):
                    name = entity.name
                    if '省' in name:
                        level_groups['省级行政区'].append(entity)
                    elif '市' in name:
                        level_groups['市级行政区'].append(entity)
                    elif '县' in name:
                        level_groups['县级行政区'].append(entity)
                    elif any(geo in name for geo in ['山', '河', '湖', '海']):
                        level_groups['自然地理'].append(entity)
                    else:
                        level_groups['一般地点'].append(entity)

            for level, group in level_groups.items():
                if len(group) >= 2:
                    subconcepts.append(Concept(
                        id=f"concept_{start_id + len(subconcepts)}",
                        name=level,
                        type=ConceptType.ENTITY_CONCEPT,
                        description=f"{level}类地点",
                        instances=[e.id for e in group if hasattr(e, 'id')],
                        instance_count=len(group)
                    ))

        elif base_type == 'organization':
            # 组织子类：按类型分类
            org_groups = defaultdict(list)
            for entity in entities:
                if hasattr(entity, 'name'):
                    name = entity.name
                    if any(kw in name for kw in ['大学', '学院', '学校']):
                        org_groups['教育机构'].append(entity)
                    elif any(kw in name for kw in ['公司', '集团', '企业']):
                        org_groups['商业机构'].append(entity)
                    elif any(kw in name for kw in ['医院', '诊所']):
                        org_groups['医疗机构'].append(entity)
                    elif any(kw in name for kw in ['局', '部', '委', '会']):
                        org_groups['政府机构'].append(entity)
                    else:
                        org_groups['一般组织'].append(entity)

            for org_type, group in org_groups.items():
                if len(group) >= 2:
                    subconcepts.append(Concept(
                        id=f"concept_{start_id + len(subconcepts)}",
                        name=org_type,
                        type=ConceptType.ENTITY_CONCEPT,
                        description=f"{org_type}类组织",
                        instances=[e.id for e in group if hasattr(e, 'id')],
                        instance_count=len(group)
                    ))

        return subconcepts


class RelationGeneralizer:
    """关系泛化器"""

    def generalize(self, relations: List[Any], concepts: List[Concept]) -> List[RelationType]:
        """将关系实例泛化为关系类型"""
        relation_types = []
        type_id = 0

        # 按关系类型分组
        type_groups = defaultdict(list)
        for relation in relations:
            if hasattr(relation, 'type'):
                rel_type = relation.type.value
                type_groups[rel_type].append(relation)

        # 为每种关系类型创建 RelationType
        for rel_type_name, rel_list in type_groups.items():
            # 分析定义域和值域
            domain_concepts, range_concepts = self._analyze_domain_range(
                rel_list, concepts
            )

            # 分析关系属性
            is_transitive = self._is_transitive(rel_type_name)
            is_symmetric = self._is_symmetric(rel_type_name)
            is_functional = self._is_functional(rel_type_name)
            inverse_name = self._find_inverse(rel_type_name)

            relation_type = RelationType(
                id=f"reltype_{type_id}",
                name=rel_type_name,
                description=f"{rel_type_name}类型的关系",
                domain=domain_concepts,
                range=range_concepts,
                is_transitive=is_transitive,
                is_symmetric=is_symmetric,
                is_functional=is_functional,
                inverse_of=inverse_name,
                instances=[r.id for r in rel_list if hasattr(r, 'id')],
                instance_count=len(rel_list)
            )
            relation_types.append(relation_type)
            type_id += 1

        logger.info(f"✅ 关系泛化：{len(relations)} 个关系 → {len(relation_types)} 个关系类型")
        return relation_types

    def _analyze_domain_range(
        self,
        relations: List[Any],
        concepts: List[Concept]
    ) -> Tuple[List[str], List[str]]:
        """分析关系的定义域和值域"""
        source_concepts = set()
        target_concepts = set()

        # 创建实体ID到概念的映射
        entity_to_concept = {}
        for concept in concepts:
            for instance_id in concept.instances:
                entity_to_concept[instance_id] = concept.id

        # 统计源和目标所属概念
        for relation in relations:
            if hasattr(relation, 'source_id') and hasattr(relation, 'target_id'):
                source_concept = entity_to_concept.get(relation.source_id)
                target_concept = entity_to_concept.get(relation.target_id)

                if source_concept:
                    source_concepts.add(source_concept)
                if target_concept:
                    target_concepts.add(target_concept)

        return list(source_concepts), list(target_concepts)

    def _is_transitive(self, rel_type: str) -> bool:
        """判断关系是否具有传递性"""
        transitive_relations = [
            'part_of',  # A是B的一部分，B是C的一部分 → A是C的一部分
            'located_in',  # A在B，B在C → A在C
            'preceded_by',  # A先于B，B先于C → A先于C
            'causes',  # A导致B，B导致C → A间接导致C
            'superior_subordinate',  # A管理B，B管理C → A间接管理C
        ]
        return rel_type in transitive_relations

    def _is_symmetric(self, rel_type: str) -> bool:
        """判断关系是否对称"""
        symmetric_relations = [
            'colleague',  # A和B是同事 ↔ B和A是同事
            'friend',  # A和B是朋友 ↔ B和A是朋友
            'adjacent_to',  # A邻近B ↔ B邻近A
            'similar_to',  # A相似于B ↔ B相似于A
        ]
        return rel_type in symmetric_relations

    def _is_functional(self, rel_type: str) -> bool:
        """判断关系是否函数性（一个源只能对应一个目标）"""
        functional_relations = [
            'family',  # 一个人只有一个父亲
        ]
        return rel_type in functional_relations

    def _find_inverse(self, rel_type: str) -> Optional[str]:
        """查找逆关系"""
        inverse_pairs = {
            'teacher_student': 'student_teacher',
            'superior_subordinate': 'subordinate_superior',
            'parent_of': 'child_of',
            'owns': 'owned_by',
            'creates': 'created_by',
        }
        return inverse_pairs.get(rel_type)


class ConstraintDefiner:
    """约束定义器"""

    def define_constraints(
        self,
        concepts: List[Concept],
        relation_types: List[RelationType]
    ) -> List[Axiom]:
        """定义约束"""
        axioms = []
        axiom_id = 0

        # 1. 定义域和值域约束
        for rel_type in relation_types:
            if rel_type.domain:
                for concept_id in rel_type.domain:
                    axioms.append(Axiom(
                        id=f"axiom_{axiom_id}",
                        type=AxiomType.DOMAIN,
                        subject=rel_type.id,
                        object=concept_id,
                        description=f"关系 {rel_type.name} 的定义域是 {concept_id}",
                        confidence=0.9
                    ))
                    axiom_id += 1

            if rel_type.range:
                for concept_id in rel_type.range:
                    axioms.append(Axiom(
                        id=f"axiom_{axiom_id}",
                        type=AxiomType.RANGE,
                        subject=rel_type.id,
                        object=concept_id,
                        description=f"关系 {rel_type.name} 的值域是 {concept_id}",
                        confidence=0.9
                    ))
                    axiom_id += 1

        # 2. 互斥约束（不同类型的实体互斥）
        base_concepts = [c for c in concepts if not c.parent_concepts]
        for i, concept1 in enumerate(base_concepts):
            for concept2 in base_concepts[i+1:]:
                axioms.append(Axiom(
                    id=f"axiom_{axiom_id}",
                    type=AxiomType.DISJOINT,
                    subject=concept1.id,
                    object=concept2.id,
                    description=f"{concept1.name} 和 {concept2.name} 互斥",
                    confidence=1.0
                ))
                axiom_id += 1

        logger.info(f"✅ 约束定义：{len(axioms)} 个约束")
        return axioms


class AxiomGenerator:
    """公理生成器"""

    def generate(
        self,
        concepts: List[Concept],
        relation_types: List[RelationType],
        existing_axioms: List[Axiom]
    ) -> List[Axiom]:
        """生成公理"""
        axioms = existing_axioms.copy()
        axiom_id = len(axioms)

        # 1. 子类公理
        for concept in concepts:
            for parent_id in concept.parent_concepts:
                axioms.append(Axiom(
                    id=f"axiom_{axiom_id}",
                    type=AxiomType.SUBCLASS,
                    subject=concept.id,
                    object=parent_id,
                    description=f"{concept.name} 是 {parent_id} 的子类",
                    confidence=1.0
                ))
                axiom_id += 1

        # 2. 关系属性公理
        for rel_type in relation_types:
            if rel_type.is_transitive:
                axioms.append(Axiom(
                    id=f"axiom_{axiom_id}",
                    type=AxiomType.TRANSITIVE,
                    subject=rel_type.id,
                    description=f"关系 {rel_type.name} 具有传递性",
                    confidence=0.95
                ))
                axiom_id += 1

            if rel_type.is_symmetric:
                axioms.append(Axiom(
                    id=f"axiom_{axiom_id}",
                    type=AxiomType.SYMMETRIC,
                    subject=rel_type.id,
                    description=f"关系 {rel_type.name} 具有对称性",
                    confidence=0.95
                ))
                axiom_id += 1

            if rel_type.is_functional:
                axioms.append(Axiom(
                    id=f"axiom_{axiom_id}",
                    type=AxiomType.FUNCTIONAL,
                    subject=rel_type.id,
                    description=f"关系 {rel_type.name} 具有函数性",
                    confidence=0.9
                ))
                axiom_id += 1

            if rel_type.inverse_of:
                axioms.append(Axiom(
                    id=f"axiom_{axiom_id}",
                    type=AxiomType.INVERSE,
                    subject=rel_type.id,
                    object=rel_type.inverse_of,
                    description=f"关系 {rel_type.name} 的逆关系是 {rel_type.inverse_of}",
                    confidence=0.9
                ))
                axiom_id += 1

        # 3. 组合公理（关系组合）
        composition_rules = [
            ('located_in', 'located_in', 'located_in'),  # A在B，B在C → A在C
            ('part_of', 'part_of', 'part_of'),  # A是B的部分，B是C的部分 → A是C的部分
        ]

        for rel1_name, rel2_name, result_rel_name in composition_rules:
            rel1 = next((r for r in relation_types if r.name == rel1_name), None)
            rel2 = next((r for r in relation_types if r.name == rel2_name), None)
            result_rel = next((r for r in relation_types if r.name == result_rel_name), None)

            if rel1 and rel2 and result_rel:
                axioms.append(Axiom(
                    id=f"axiom_{axiom_id}",
                    type=AxiomType.COMPOSITION,
                    subject=f"{rel1.id}∘{rel2.id}",
                    object=result_rel.id,
                    description=f"{rel1_name} ∘ {rel2_name} → {result_rel_name}",
                    confidence=0.9
                ))
                axiom_id += 1

        logger.info(f"✅ 公理生成：共 {len(axioms)} 个公理")
        return axioms


class OWLExporter:
    """OWL 导出器（可导入 Protégé）"""

    def export(self, ontology: Ontology) -> str:
        """导出为 OWL/XML 格式"""
        # OWL命名空间
        NS_OWL = "http://www.w3.org/2002/07/owl#"
        NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#"
        NS_XSD = "http://www.w3.org/2001/XMLSchema#"
        NS_ONTOLOGY = f"http://fieldmind.ai/ontology/{ontology.name}#"

        # 创建根元素
        rdf = ET.Element("{%s}RDF" % NS_RDF)
        rdf.set("xmlns:owl", NS_OWL)
        rdf.set("xmlns:rdf", NS_RDF)
        rdf.set("xmlns:rdfs", NS_RDFS)
        rdf.set("xmlns:xsd", NS_XSD)
        rdf.set("xmlns", NS_ONTOLOGY)

        # Ontology声明
        ontology_elem = ET.SubElement(rdf, "{%s}Ontology" % NS_OWL)
        ontology_elem.set("{%s}about" % NS_RDF, NS_ONTOLOGY)

        # 导出概念（Classes）
        for concept in ontology.concepts.values():
            self._export_concept(rdf, concept, NS_OWL, NS_RDF, NS_RDFS, NS_ONTOLOGY)

        # 导出关系类型（ObjectProperties）
        for rel_type in ontology.relation_types.values():
            self._export_relation_type(rdf, rel_type, NS_OWL, NS_RDF, NS_RDFS, NS_ONTOLOGY)

        # 导出公理
        for axiom in ontology.axioms:
            self._export_axiom(rdf, axiom, ontology, NS_OWL, NS_RDF, NS_RDFS, NS_ONTOLOGY)

        # 格式化输出
        xml_str = ET.tostring(rdf, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")

        logger.info(f"✅ OWL 导出完成")
        return pretty_xml

    def _export_concept(self, parent, concept, NS_OWL, NS_RDF, NS_RDFS, NS_ONTOLOGY):
        """导出概念"""
        cls = ET.SubElement(parent, "{%s}Class" % NS_OWL)
        cls.set("{%s}about" % NS_RDF, f"{NS_ONTOLOGY}{concept.id}")

        # 标签
        label = ET.SubElement(cls, "{%s}label" % NS_RDFS)
        label.text = concept.name

        # 注释
        if concept.description:
            comment = ET.SubElement(cls, "{%s}comment" % NS_RDFS)
            comment.text = concept.description

        # 子类关系
        for parent_id in concept.parent_concepts:
            subclass = ET.SubElement(cls, "{%s}subClassOf" % NS_RDFS)
            subclass.set("{%s}resource" % NS_RDF, f"{NS_ONTOLOGY}{parent_id}")

    def _export_relation_type(self, parent, rel_type, NS_OWL, NS_RDF, NS_RDFS, NS_ONTOLOGY):
        """导出关系类型"""
        prop = ET.SubElement(parent, "{%s}ObjectProperty" % NS_OWL)
        prop.set("{%s}about" % NS_RDF, f"{NS_ONTOLOGY}{rel_type.id}")

        # 标签
        label = ET.SubElement(prop, "{%s}label" % NS_RDFS)
        label.text = rel_type.name

        # 描述
        if rel_type.description:
            comment = ET.SubElement(prop, "{%s}comment" % NS_RDFS)
            comment.text = rel_type.description

        # 定义域
        for domain_id in rel_type.domain:
            domain_elem = ET.SubElement(prop, "{%s}domain" % NS_RDFS)
            domain_elem.set("{%s}resource" % NS_RDF, f"{NS_ONTOLOGY}{domain_id}")

        # 值域
        for range_id in rel_type.range:
            range_elem = ET.SubElement(prop, "{%s}range" % NS_RDFS)
            range_elem.set("{%s}resource" % NS_RDF, f"{NS_ONTOLOGY}{range_id}")

        # 传递性
        if rel_type.is_transitive:
            trans = ET.SubElement(prop, "{%s}TransitiveProperty" % NS_OWL)

        # 对称性
        if rel_type.is_symmetric:
            sym = ET.SubElement(prop, "{%s}SymmetricProperty" % NS_OWL)

        # 函数性
        if rel_type.is_functional:
            func = ET.SubElement(prop, "{%s}FunctionalProperty" % NS_OWL)

    def _export_axiom(self, parent, axiom, ontology, NS_OWL, NS_RDF, NS_RDFS, NS_ONTOLOGY):
        """导出公理"""
        # 公理已在概念和关系中体现，此处可选择性导出额外约束
        pass


class OntologyConstructionService:
    """本体构建服务（核心步骤）"""

    def __init__(self, use_workflow_engine: bool = True):
        self.concept_clusterer = ConceptClusterer()
        self.relation_generalizer = RelationGeneralizer()
        self.constraint_definer = ConstraintDefiner()
        self.axiom_generator = AxiomGenerator()
        self.owl_exporter = OWLExporter()
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    async def construct(
        self,
        entities: List[Any],
        relations: List[Any],
        ontology_name: str = "FieldMindOntology"
    ) -> Dict[str, Any]:
        """
        本体构建（核心步骤）

        Args:
            entities: 实体列表
            relations: 关系列表
            ontology_name: 本体名称

        Returns:
            本体构建结果
        """
        if self.use_workflow_engine:
            return self._construct_with_workflow_engine(entities, relations, ontology_name)
        else:
            return await self._construct_traditional(entities, relations, ontology_name)

    async def _construct_traditional(
        self,
        entities: List[Any],
        relations: List[Any],
        ontology_name: str = "FieldMindOntology"
    ) -> Dict[str, Any]:
        """传统顺序执行模式（向后兼容）"""
        logger.info(f"🔥 开始本体构建（核心步骤）")

        # 1. 概念聚类
        concepts = await asyncio.to_thread(self.concept_clusterer.cluster, entities)
        logger.info(f"✅ 概念聚类：{len(concepts)} 个概念")

        # 2. 关系泛化
        relation_types = await asyncio.to_thread(
            self.relation_generalizer.generalize, relations, concepts
        )
        logger.info(f"✅ 关系泛化：{len(relation_types)} 个关系类型")

        # 3. 约束定义
        constraint_axioms = await asyncio.to_thread(
            self.constraint_definer.define_constraints, concepts, relation_types
        )
        logger.info(f"✅ 约束定义：{len(constraint_axioms)} 个约束")

        # 4. 公理生成
        all_axioms = await asyncio.to_thread(
            self.axiom_generator.generate, concepts, relation_types, constraint_axioms
        )
        logger.info(f"✅ 公理生成：{len(all_axioms)} 个公理")

        # 5. 构建本体对象
        ontology = Ontology(
            name=ontology_name,
            version="1.0",
            concepts={c.id: c for c in concepts},
            relation_types={r.id: r for r in relation_types},
            axioms=all_axioms,
            metadata={
                'entity_count': len(entities),
                'relation_count': len(relations),
                'concept_count': len(concepts),
                'relation_type_count': len(relation_types),
                'axiom_count': len(all_axioms),
            }
        )

        # 6. 导出 OWL
        owl_xml = await asyncio.to_thread(self.owl_exporter.export, ontology)

        result = {
            'ontology': ontology,
            'owl_xml': owl_xml,
            'statistics': ontology.metadata
        }

        logger.info(f"🔥✅ 本体构建完成（核心步骤）：{len(concepts)} 概念，{len(relation_types)} 关系类型，{len(all_axioms)} 公理")
        return result

    def _construct_with_workflow_engine(
        self,
        entities: List[Any],
        relations: List[Any],
        ontology_name: str = "FieldMindOntology"
    ) -> Dict[str, Any]:
        """使用 WorkflowEngine 执行（DAG模式）"""
        logger.info(f"🔥 开始本体构建 (WorkflowEngine模式)")

        result = self.workflow_engine.execute({
            "cluster_concepts": {
                "task": self._task_cluster_concepts,
                "params": {"entities": entities}
            },
            "generalize_relations": {
                "task": self._task_generalize_relations,
                "params": {
                    "relations": relations,
                    "concepts": "$cluster_concepts.concepts"
                },
                "depends_on": ["cluster_concepts"]
            },
            "define_constraints": {
                "task": self._task_define_constraints,
                "params": {
                    "concepts": "$cluster_concepts.concepts",
                    "relation_types": "$generalize_relations.relation_types"
                },
                "depends_on": ["cluster_concepts", "generalize_relations"]
            },
            "generate_axioms": {
                "task": self._task_generate_axioms,
                "params": {
                    "concepts": "$cluster_concepts.concepts",
                    "relation_types": "$generalize_relations.relation_types",
                    "constraint_axioms": "$define_constraints.axioms"
                },
                "depends_on": ["define_constraints"]
            },
            "build_ontology": {
                "task": self._task_build_ontology,
                "params": {
                    "ontology_name": ontology_name,
                    "concepts": "$cluster_concepts.concepts",
                    "relation_types": "$generalize_relations.relation_types",
                    "axioms": "$generate_axioms.axioms",
                    "entities": entities,
                    "relations": relations
                },
                "depends_on": ["generate_axioms"]
            },
            "export_owl": {
                "task": self._task_export_owl,
                "params": {"ontology": "$build_ontology.ontology"},
                "depends_on": ["build_ontology"]
            }
        })

        logger.info(f"🔥✅ 本体构建完成 (WorkflowEngine): {len(result['cluster_concepts']['concepts'])} 概念")

        return {
            'ontology': result['build_ontology']['ontology'],
            'owl_xml': result['export_owl']['owl_xml'],
            'statistics': result['build_ontology']['ontology'].metadata
        }

    # ==================== WorkflowEngine 任务函数 ====================

    def _task_cluster_concepts(self, entities: List[Any], _context: dict) -> dict:
        """任务1: 概念聚类"""
        concepts = self.concept_clusterer.cluster(entities)
        logger.info(f"✅ 概念聚类：{len(concepts)} 个概念")
        return {"concepts": concepts}

    def _task_generalize_relations(
        self,
        relations: List[Any],
        concepts: List[Concept],
        _context: dict
    ) -> dict:
        """任务2: 关系泛化"""
        relation_types = self.relation_generalizer.generalize(relations, concepts)
        logger.info(f"✅ 关系泛化：{len(relation_types)} 个关系类型")
        return {"relation_types": relation_types}

    def _task_define_constraints(
        self,
        concepts: List[Concept],
        relation_types: List[RelationType],
        _context: dict
    ) -> dict:
        """任务3: 约束定义"""
        axioms = self.constraint_definer.define_constraints(concepts, relation_types)
        logger.info(f"✅ 约束定义：{len(axioms)} 个约束")
        return {"axioms": axioms}

    def _task_generate_axioms(
        self,
        concepts: List[Concept],
        relation_types: List[RelationType],
        constraint_axioms: List[Axiom],
        _context: dict
    ) -> dict:
        """任务4: 公理生成"""
        all_axioms = self.axiom_generator.generate(concepts, relation_types, constraint_axioms)
        logger.info(f"✅ 公理生成：{len(all_axioms)} 个公理")
        return {"axioms": all_axioms}

    def _task_build_ontology(
        self,
        ontology_name: str,
        concepts: List[Concept],
        relation_types: List[RelationType],
        axioms: List[Axiom],
        entities: List[Any],
        relations: List[Any],
        _context: dict
    ) -> dict:
        """任务5: 构建本体对象"""
        ontology = Ontology(
            name=ontology_name,
            version="1.0",
            concepts={c.id: c for c in concepts},
            relation_types={r.id: r for r in relation_types},
            axioms=axioms,
            metadata={
                'entity_count': len(entities),
                'relation_count': len(relations),
                'concept_count': len(concepts),
                'relation_type_count': len(relation_types),
                'axiom_count': len(axioms),
            }
        )
        logger.info(f"✅ 本体对象构建完成")
        return {"ontology": ontology}

    def _task_export_owl(self, ontology: Ontology, _context: dict) -> dict:
        """任务6: 导出OWL"""
        owl_xml = self.owl_exporter.export(ontology)
        logger.info(f"✅ OWL导出完成")
        return {"owl_xml": owl_xml}
