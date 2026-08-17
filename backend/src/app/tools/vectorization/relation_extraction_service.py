"""
关系抽取服务
专为田野调查设计 - 包含组织架构和外部支持关系
"""
import re
import logging
from typing import List, Dict, Any, Optional

from app.models.enriched_chunk import Entity, Relation, EntityType, RelationType

logger = logging.getLogger(__name__)


class RelationExtractionService:
    """关系抽取服务 - 专为田野调查设计"""

    def __init__(self):
        # 组织架构模式 ⭐
        self.org_patterns = self._load_organizational_patterns()

        # 支持关系模式 ⭐
        self.support_patterns = self._load_support_patterns()

        logger.info("关系抽取服务初始化完成")

    def _load_organizational_patterns(self) -> Dict[str, str]:
        """加载组织架构关系模式"""
        return {
            'succession': r'第(\d+)代(\S{2,6})是(\S{2,10})',  # 职位继承
            'membership': r'(\S{2,10})是(\S{2,20}协会|\S{2,20}基金会|\S{2,20}委会|\S{2,20}合作社)的?(\S{0,6}成员|\S{0,6}理事|\S{0,6}会长|\S{0,6}主任)',
            'hierarchy': r'(\S{2,10})(?:领导|管理|负责)(\S{2,20})',
            'appointment': r'(\S{2,10})(?:担任|出任|被任命为)(\S{2,10})',
        }

    def _load_support_patterns(self) -> Dict[str, str]:
        """加载外部支持关系模式"""
        return {
            'funding': r'(\S{2,30}基金会|\S{2,30}协会|\S{2,30}组织)(?:\S{0,3}资助|\S{0,3}捐赠|\S{0,3}拨款)了?(\d+\.?\d*万?元)?(?:\S{0,3}用于)?(\S{2,20}项目|\S{2,20}保护|\S{2,20}建设)?',
            'help': r'(\S{2,30}协会|\S{2,30}组织|\S{2,30}NGO)(?:\S{0,3}帮助|\S{0,3}协助|\S{0,3}支持)(\S{2,20})(?:建立|培训|提供|开展|实施)(\S{2,20})',
            'partnership': r'(\S{2,20})(?:与|和)(\S{2,30}协会|\S{2,30}组织|\S{2,30}基金会)(?:合作|联合|共同)(\S{2,20})',
            'government': r'(\S{2,20}政府|\S{2,20}部门)(?:\S{0,3}支持|\S{0,3}扶持|\S{0,3}资助)(\S{2,20})',
        }

    def extract_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """提取所有类型的关系

        Args:
            text: 输入文本
            entities: 已识别的实体列表

        Returns:
            关系列表
        """
        relations = []

        # 1. 基础关系抽取（人际、亲缘、地理、文化）
        base_relations = self._extract_base_relations(text, entities)
        relations.extend(base_relations)

        # 2. 组织架构关系抽取 ⭐
        org_relations = self._extract_organizational_relations(text, entities)
        relations.extend(org_relations)

        # 3. 外部支持关系抽取 ⭐
        support_relations = self._extract_support_relations(text, entities)
        relations.extend(support_relations)

        # 4. 关系去重和验证
        relations = self._deduplicate_and_validate_relations(relations)

        logger.info(f"提取关系完成: {len(relations)} 个关系")
        return relations

    def _extract_base_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """提取基础关系（人际、亲缘、地理、文化）"""
        relations = []

        # 人际关系模式
        relations.extend(self._extract_interpersonal_relations(text, entities))

        # 亲缘关系模式
        relations.extend(self._extract_kinship_relations(text, entities))

        # 地理关系模式
        relations.extend(self._extract_geographic_relations(text, entities))

        # 文化关系模式
        relations.extend(self._extract_cultural_relations(text, entities))

        return relations

    def _extract_interpersonal_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """提取人际关系"""
        relations = []

        # 师生关系
        mentorship_pattern = r'(\S{2,10})(?:是|为)(\S{2,10})的?(?:老师|师傅|师父)'
        for match in re.finditer(mentorship_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.MENTORSHIP,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.85,
                context=match.group(0)
            ))

        # 同事关系
        colleague_pattern = r'(\S{2,10})(?:和|与)(\S{2,10})(?:是|为)?(?:同事|同僚|共事)'
        for match in re.finditer(colleague_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.COLLEAGUE,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.80,
                context=match.group(0)
            ))

        # 邻居关系
        neighbor_pattern = r'(\S{2,10})(?:和|与)(\S{2,10})(?:是|为)?邻居'
        for match in re.finditer(neighbor_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.NEIGHBOR,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.85,
                context=match.group(0)
            ))

        # 朋友关系
        friendship_pattern = r'(\S{2,10})(?:和|与)(\S{2,10})(?:是|为)?朋友'
        for match in re.finditer(friendship_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.FRIENDSHIP,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.85,
                context=match.group(0)
            ))

        return relations

    def _extract_kinship_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """提取亲缘关系"""
        relations = []

        # 父子/母女关系
        parent_child_pattern = r'(\S{2,10})(?:是|为)(\S{2,10})的?(?:父亲|母亲|爸爸|妈妈|儿子|女儿|孩子)'
        for match in re.finditer(parent_child_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.PARENT_CHILD,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.90,
                context=match.group(0)
            ))

        # 兄弟姐妹关系
        sibling_pattern = r'(\S{2,10})(?:和|与)(\S{2,10})(?:是|为)?(?:兄弟|姐妹|兄妹|姐弟)'
        for match in re.finditer(sibling_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.SIBLING,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.90,
                context=match.group(0)
            ))

        # 配偶关系
        spouse_pattern = r'(\S{2,10})(?:和|与)(\S{2,10})(?:是|为)?(?:夫妻|配偶|丈夫|妻子)'
        for match in re.finditer(spouse_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.SPOUSE,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.90,
                context=match.group(0)
            ))

        # 祖孙关系
        grandparent_pattern = r'(\S{2,10})(?:是|为)(\S{2,10})的?(?:爷爷|奶奶|外公|外婆|祖父|祖母|孙子|孙女|外孙|外孙女)'
        for match in re.finditer(grandparent_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.GRANDPARENT_GRANDCHILD,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.90,
                context=match.group(0)
            ))

        return relations

    def _extract_geographic_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """提取地理关系"""
        relations = []

        # 位于关系
        located_in_pattern = r'(\S{2,20})(?:位于|坐落在|在)(\S{2,20}省|\S{2,20}市|\S{2,20}县|\S{2,20}区|\S{2,20}镇|\S{2,20}乡|\S{2,20}村)'
        for match in re.finditer(located_in_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.LOCATION,
                relation=RelationType.LOCATED_IN,
                object=match.group(2),
                object_type=EntityType.LOCATION,
                confidence=0.85,
                context=match.group(0)
            ))

        # 毗邻关系
        adjacent_pattern = r'(\S{2,20})(?:毗邻|邻近|靠近|紧挨)(\S{2,20})'
        for match in re.finditer(adjacent_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.LOCATION,
                relation=RelationType.ADJACENT_TO,
                object=match.group(2),
                object_type=EntityType.LOCATION,
                confidence=0.80,
                context=match.group(0)
            ))

        # 属于关系
        belongs_pattern = r'(\S{2,20})(?:属于|隶属于)(\S{2,20})'
        for match in re.finditer(belongs_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.LOCATION,
                relation=RelationType.BELONGS_TO,
                object=match.group(2),
                object_type=EntityType.LOCATION,
                confidence=0.85,
                context=match.group(0)
            ))

        return relations

    def _extract_cultural_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """提取文化关系"""
        relations = []

        # 文化传承关系
        inheritance_pattern = r'(\S{2,10})(?:传承自|学自|师从)(\S{2,10})'
        for match in re.finditer(inheritance_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.CULTURAL_INHERITANCE,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.88,
                context=match.group(0),
                evidence=f"{match.group(1)} → {match.group(2)}"
            ))

        # 文化影响关系
        influence_pattern = r'(\S{2,20})(?:受|深受)(\S{2,20})(?:的)?(?:影响|熏陶)'
        for match in re.finditer(influence_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.PERSON,
                relation=RelationType.CULTURAL_INFLUENCE,
                object=match.group(2),
                object_type=EntityType.PERSON,
                confidence=0.80,
                context=match.group(0)
            ))

        # 文化融合关系
        fusion_pattern = r'(\S{2,20})(?:与|和)(\S{2,20})(?:融合|结合|交融)'
        for match in re.finditer(fusion_pattern, text):
            relations.append(Relation(
                subject=match.group(1),
                subject_type=EntityType.INTANGIBLE_HERITAGE,
                relation=RelationType.CULTURAL_FUSION,
                object=match.group(2),
                object_type=EntityType.INTANGIBLE_HERITAGE,
                confidence=0.75,
                context=match.group(0)
            ))

        return relations

    def _extract_organizational_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """抽取组织架构关系 ⭐

        模式示例：
        - "第一代村支书是张三，第二代是李四"
        - "王五接任了村长职位"
        - "赵六是村委会成员"
        """
        relations = []

        # 模式1：职位继承（"第X代...是..."）
        succession_pattern = self.org_patterns['succession']
        matches = list(re.finditer(succession_pattern, text))

        for match in matches:
            generation = int(match.group(1))
            position = match.group(2)
            person = match.group(3)

            # 查找前一代
            prev_generation = generation - 1
            if prev_generation > 0:
                prev_pattern = rf'第{prev_generation}代{position}是(\S{{2,10}})'
                prev_match = re.search(prev_pattern, text)

                if prev_match:
                    prev_person = prev_match.group(1)

                    relation = Relation(
                        subject=person,
                        subject_type=EntityType.PERSON,
                        relation=RelationType.ORGANIZATIONAL_SUCCESSION,
                        object=prev_person,
                        object_type=EntityType.PERSON,
                        confidence=0.90,
                        position=position,
                        generation=generation,
                        context=match.group(0),
                        evidence=f"{prev_person} → {person} ({position})"
                    )
                    relations.append(relation)

        # 模式2：组织成员（"...是...成员"）
        membership_pattern = self.org_patterns['membership']
        for match in re.finditer(membership_pattern, text):
            person = match.group(1)
            organization = match.group(2)
            role = match.group(3) if match.group(3) else "成员"

            relation = Relation(
                subject=person,
                subject_type=EntityType.PERSON,
                relation=RelationType.ORGANIZATIONAL_MEMBERSHIP,
                object=organization,
                object_type=EntityType.ORGANIZATION,
                confidence=0.85,
                position=role,
                context=match.group(0)
            )
            relations.append(relation)

        # 模式3：组织层级（"...领导/管理..."）
        hierarchy_pattern = self.org_patterns['hierarchy']
        for match in re.finditer(hierarchy_pattern, text):
            person = match.group(1)
            organization = match.group(2)

            relation = Relation(
                subject=person,
                subject_type=EntityType.PERSON,
                relation=RelationType.ORGANIZATIONAL_HIERARCHY,
                object=organization,
                object_type=EntityType.ORGANIZATION,
                confidence=0.80,
                context=match.group(0)
            )
            relations.append(relation)

        # 模式4：职位任命（"...担任..."）
        appointment_pattern = self.org_patterns['appointment']
        for match in re.finditer(appointment_pattern, text):
            person = match.group(1)
            position = match.group(2)

            relation = Relation(
                subject=person,
                subject_type=EntityType.PERSON,
                relation=RelationType.ORGANIZATIONAL_MEMBERSHIP,
                object=position,
                object_type=EntityType.ORGANIZATION,
                confidence=0.85,
                position=position,
                context=match.group(0)
            )
            relations.append(relation)

        return relations

    def _extract_support_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relation]:
        """抽取外部支持关系 ⭐

        模式示例：
        - "某某基金会资助了10万元用于蜡染保护"
        - "中国文化遗产保护协会帮助建立了传习所"
        - "联合国教科文组织支持该项目"
        """
        relations = []

        # 模式1：资金支持（"...资助了...元"）
        funding_pattern = self.support_patterns['funding']
        for match in re.finditer(funding_pattern, text):
            supporter = match.group(1)
            amount = match.group(2) if match.group(2) else None
            project = match.group(3) if match.group(3) else None

            # 确定被支持对象
            supported = project if project else "本地社区"

            relation_type = (
                RelationType.FOUNDATION_SUPPORT if "基金会" in supporter
                else RelationType.ASSOCIATION_HELP
            )

            relation = Relation(
                subject=supporter,
                subject_type=EntityType.ORGANIZATION,
                relation=relation_type,
                object=supported,
                object_type=EntityType.ORGANIZATION,
                confidence=0.85,
                support_type="资金支持",
                support_amount=amount,
                project_name=project,
                context=match.group(0)
            )
            relations.append(relation)

        # 模式2：技术/能力支持（"...帮助..."）
        help_pattern = self.support_patterns['help']
        for match in re.finditer(help_pattern, text):
            supporter = match.group(1)
            supported = match.group(2)
            action = match.group(3)

            relation_type = (
                RelationType.ASSOCIATION_HELP if "协会" in supporter
                else RelationType.NGO_PARTNERSHIP
            )

            relation = Relation(
                subject=supporter,
                subject_type=EntityType.ORGANIZATION,
                relation=relation_type,
                object=supported,
                object_type=EntityType.ORGANIZATION,
                confidence=0.80,
                support_type="技术支持",
                project_name=action,
                context=match.group(0)
            )
            relations.append(relation)

        # 模式3：合作伙伴关系
        partnership_pattern = self.support_patterns['partnership']
        for match in re.finditer(partnership_pattern, text):
            partner1 = match.group(1)
            partner2 = match.group(2)
            project = match.group(3)

            relation = Relation(
                subject=partner1,
                subject_type=EntityType.ORGANIZATION,
                relation=RelationType.NGO_PARTNERSHIP,
                object=partner2,
                object_type=EntityType.ORGANIZATION,
                confidence=0.80,
                project_name=project,
                context=match.group(0)
            )
            relations.append(relation)

        # 模式4：政府支持
        government_pattern = self.support_patterns['government']
        for match in re.finditer(government_pattern, text):
            government = match.group(1)
            supported = match.group(2)

            relation = Relation(
                subject=government,
                subject_type=EntityType.ORGANIZATION,
                relation=RelationType.GOVERNMENT_FUNDING,
                object=supported,
                object_type=EntityType.ORGANIZATION,
                confidence=0.85,
                support_type="政府支持",
                context=match.group(0)
            )
            relations.append(relation)

        return relations

    def _deduplicate_and_validate_relations(
        self,
        relations: List[Relation]
    ) -> List[Relation]:
        """去重和验证关系"""
        if not relations:
            return []

        # 去重：相同的主体-关系-客体组合
        unique_relations = {}
        for relation in relations:
            key = f"{relation.subject}|{relation.relation.value}|{relation.object}"

            if key not in unique_relations:
                unique_relations[key] = relation
            else:
                # 保留置信度更高的
                if relation.confidence > unique_relations[key].confidence:
                    unique_relations[key] = relation

        return list(unique_relations.values())
