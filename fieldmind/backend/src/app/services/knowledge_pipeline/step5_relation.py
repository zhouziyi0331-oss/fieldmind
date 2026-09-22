"""
Step 5: 关系发现服务
Relation Discovery Service

功能：
1. 关系模式匹配（40+ 模式）
2. 共现分析
3. 关系分类
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class RelationType(str, Enum):
    """关系类型"""
    # 人物关系
    FAMILY = "family"  # 家庭关系
    COLLEAGUE = "colleague"  # 同事关系
    TEACHER_STUDENT = "teacher_student"  # 师生关系
    FRIEND = "friend"  # 朋友关系
    SUPERIOR_SUBORDINATE = "superior_subordinate"  # 上下级

    # 组织关系
    MEMBER_OF = "member_of"  # 成员关系
    PART_OF = "part_of"  # 部分关系
    OWNS = "owns"  # 拥有关系
    AFFILIATED_WITH = "affiliated_with"  # 附属关系

    # 地理关系
    LOCATED_IN = "located_in"  # 位于
    ADJACENT_TO = "adjacent_to"  # 邻近

    # 事件关系
    PARTICIPATES_IN = "participates_in"  # 参与
    OCCURS_AT = "occurs_at"  # 发生于
    CAUSES = "causes"  # 导致
    PRECEDED_BY = "preceded_by"  # 先于

    # 其他
    CREATES = "creates"  # 创造
    USES = "uses"  # 使用
    DESCRIBES = "describes"  # 描述
    SIMILAR_TO = "similar_to"  # 相似
    OPPOSITE_TO = "opposite_to"  # 相反


@dataclass
class Relation:
    """关系"""
    id: str
    type: RelationType
    source_id: str  # 源实体ID
    target_id: str  # 目标实体ID
    source_name: str  # 源实体名称
    target_name: str  # 目标实体名称

    # 证据
    evidence: List[str] = field(default_factory=list)  # 证据句子
    pattern: Optional[str] = None  # 匹配的模式
    confidence: float = 1.0

    # 属性
    attributes: Dict[str, Any] = field(default_factory=dict)


class RelationPatternMatcher:
    """关系模式匹配器（40+ 模式）"""

    def __init__(self):
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[RelationType, List[Tuple[str, float]]]:
        """初始化关系模式"""
        patterns = {
            RelationType.FAMILY: [
                (r'(.+)是(.+)的(?:父亲|母亲|爸爸|妈妈|儿子|女儿|兄弟|姐妹|丈夫|妻子)', 0.95),
                (r'(.+)的(?:父亲|母亲|爸爸|妈妈|儿子|女儿|兄弟|姐妹|丈夫|妻子)(?:是|为)(.+)', 0.95),
                (r'(.+)(?:娶|嫁)(.+)', 0.9),
                (r'(.+)(?:生|育|产)(.+)', 0.85),
            ],
            RelationType.COLLEAGUE: [
                (r'(.+)(?:和|与)(.+)(?:共事|合作|协作|一起工作)', 0.9),
                (r'(.+)(?:是|为)(.+)的(?:同事|同僚|同仁)', 0.9),
            ],
            RelationType.TEACHER_STUDENT: [
                (r'(.+)(?:是|为)(.+)的(?:老师|教师|师傅|导师)', 0.95),
                (r'(.+)(?:师从|拜师|学于)(.+)', 0.95),
                (r'(.+)(?:教授|教导|指导)(.+)', 0.85),
                (r'(.+)(?:是|为)(.+)的(?:学生|弟子|门生)', 0.9),
            ],
            RelationType.FRIEND: [
                (r'(.+)(?:和|与)(.+)(?:是|为)(?:朋友|好友|挚友)', 0.9),
                (r'(.+)(?:结交|结识)(.+)', 0.85),
            ],
            RelationType.SUPERIOR_SUBORDINATE: [
                (r'(.+)(?:是|为)(.+)的(?:上司|领导|老板|主管)', 0.95),
                (r'(.+)(?:管理|领导|指挥)(.+)', 0.85),
                (r'(.+)(?:向|对)(.+)(?:汇报|报告)', 0.85),
                (r'(.+)(?:任命|提拔|升任)(.+)', 0.8),
            ],
            RelationType.MEMBER_OF: [
                (r'(.+)(?:是|为)(.+)的(?:成员|会员|队员|成员之一)', 0.95),
                (r'(.+)(?:加入|参加|入会)(.+)', 0.9),
                (r'(.+)(?:属于|隶属于)(.+)', 0.9),
            ],
            RelationType.PART_OF: [
                (r'(.+)(?:是|为)(.+)的(?:一部分|组成部分)', 0.95),
                (r'(.+)(?:包含|包括|含有)(.+)', 0.85),
                (r'(.+)(?:位于|在)(.+)(?:内|中)', 0.8),
            ],
            RelationType.OWNS: [
                (r'(.+)(?:拥有|持有|占有)(.+)', 0.9),
                (r'(.+)(?:是|为)(.+)的(?:所有者|拥有者|持有人)', 0.95),
                (r'(.+)(?:属于|归)(.+)(?:所有|拥有)', 0.9),
            ],
            RelationType.AFFILIATED_WITH: [
                (r'(.+)(?:附属于|从属于)(.+)', 0.9),
                (r'(.+)(?:与)(.+)(?:有关联|相关联)', 0.8),
            ],
            RelationType.LOCATED_IN: [
                (r'(.+)(?:位于|坐落于|在)(.+)', 0.9),
                (r'(.+)(?:地处|处于)(.+)', 0.85),
            ],
            RelationType.ADJACENT_TO: [
                (r'(.+)(?:邻近|毗邻|接壤)(.+)', 0.9),
                (r'(.+)(?:与)(.+)(?:相邻|相接)', 0.9),
            ],
            RelationType.PARTICIPATES_IN: [
                (r'(.+)(?:参与|参加|加入)(.+)', 0.9),
                (r'(.+)(?:在)(.+)(?:中|里)', 0.7),
            ],
            RelationType.OCCURS_AT: [
                (r'(.+)(?:发生于|发生在)(.+)', 0.95),
                (r'(.+)(?:在)(.+)(?:发生|举行|进行)', 0.9),
            ],
            RelationType.CAUSES: [
                (r'(.+)(?:导致|引起|造成|引发)(.+)', 0.9),
                (r'(.+)(?:使|让)(.+)(?:发生|出现)', 0.85),
                (r'由于(.+)[，,](.+)', 0.8),
            ],
            RelationType.PRECEDED_BY: [
                (r'(.+)(?:之前|以前|先于)(.+)', 0.85),
                (r'在(.+)(?:之后|以后|后)(.+)', 0.85),
            ],
            RelationType.CREATES: [
                (r'(.+)(?:创造|创作|创建|建立)(.+)', 0.9),
                (r'(.+)(?:发明|研制|开发)(.+)', 0.9),
                (r'(.+)(?:写|著|撰写|编写)(.+)', 0.85),
            ],
            RelationType.USES: [
                (r'(.+)(?:使用|运用|采用|利用)(.+)', 0.85),
                (r'(.+)(?:用|以)(.+)', 0.7),
            ],
            RelationType.DESCRIBES: [
                (r'(.+)(?:描述|描写|记载|记录)(.+)', 0.85),
                (r'(.+)(?:关于|涉及)(.+)', 0.75),
            ],
        }

        return patterns

    def match(
        self,
        text: str,
        entities: List[Any]
    ) -> List[Relation]:
        """模式匹配"""
        relations = []
        relation_id = 0

        # 创建实体索引
        entity_dict = {}
        if entities:
            for entity in entities:
                if hasattr(entity, 'id') and hasattr(entity, 'name'):
                    entity_dict[entity.name] = entity

        # 对每种关系类型进行匹配
        for rel_type, patterns in self.patterns.items():
            for pattern, confidence in patterns:
                for match in re.finditer(pattern, text):
                    source_text = match.group(1).strip()
                    target_text = match.group(2).strip()

                    # 查找对应的实体
                    source_entity = entity_dict.get(source_text)
                    target_entity = entity_dict.get(target_text)

                    if source_entity and target_entity:
                        # 提取证据句子
                        evidence = self._extract_evidence(text, match.start(), match.end())

                        relation = Relation(
                            id=f"rel_{relation_id}",
                            type=rel_type,
                            source_id=source_entity.id,
                            target_id=target_entity.id,
                            source_name=source_text,
                            target_name=target_text,
                            evidence=[evidence],
                            pattern=pattern,
                            confidence=confidence
                        )
                        relations.append(relation)
                        relation_id += 1

        logger.info(f"✅ 模式匹配：{len(relations)} 个关系")
        return relations

    def _extract_evidence(self, text: str, start: int, end: int) -> str:
        """提取证据句子"""
        # 向前查找句子开始
        sent_start = start
        while sent_start > 0:
            if text[sent_start] in ['。', '！', '？', '\n']:
                sent_start += 1
                break
            sent_start -= 1

        # 向后查找句子结束
        sent_end = end
        while sent_end < len(text):
            if text[sent_end] in ['。', '！', '？', '\n']:
                sent_end += 1
                break
            sent_end += 1

        return text[sent_start:sent_end].strip()


class CooccurrenceAnalyzer:
    """共现分析器"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size

    def analyze(
        self,
        text: str,
        entities: List[Any]
    ) -> List[Relation]:
        """共现分析"""
        relations = []
        relation_id = 0

        if not entities:
            return relations

        # 为每个实体找到其在文本中的位置
        entity_positions = defaultdict(list)
        for entity in entities:
            if not hasattr(entity, 'name'):
                continue
            for match in re.finditer(re.escape(entity.name), text):
                entity_positions[entity.id].append({
                    'entity': entity,
                    'position': match.start()
                })

        # 计算共现
        cooccurrences = defaultdict(lambda: {'count': 0, 'evidence': []})

        for entity1 in entities:
            for entity2 in entities:
                if entity1.id >= entity2.id:  # 避免重复和自身
                    continue

                # 检查是否在窗口内共现
                for pos1_info in entity_positions[entity1.id]:
                    for pos2_info in entity_positions[entity2.id]:
                        distance = abs(pos1_info['position'] - pos2_info['position'])
                        if distance <= self.window_size:
                            key = (entity1.id, entity2.id)
                            cooccurrences[key]['count'] += 1

                            # 提取共现上下文
                            min_pos = min(pos1_info['position'], pos2_info['position'])
                            max_pos = max(pos1_info['position'], pos2_info['position'])
                            evidence = text[max(0, min_pos - 50):min(len(text), max_pos + 50)]
                            cooccurrences[key]['evidence'].append(evidence)

        # 创建关系
        for (source_id, target_id), info in cooccurrences.items():
            if info['count'] >= 2:  # 至少共现2次
                source = next(e for e in entities if e.id == source_id)
                target = next(e for e in entities if e.id == target_id)

                # 推测关系类型
                rel_type = self._infer_relation_type(source, target, info['evidence'])

                relation = Relation(
                    id=f"rel_cooc_{relation_id}",
                    type=rel_type,
                    source_id=source_id,
                    target_id=target_id,
                    source_name=source.name,
                    target_name=target.name,
                    evidence=info['evidence'][:3],  # 最多3个证据
                    confidence=min(0.5 + info['count'] * 0.1, 0.9)
                )
                relations.append(relation)
                relation_id += 1

        logger.info(f"✅ 共现分析：{len(relations)} 个关系")
        return relations

    def _infer_relation_type(
        self,
        source: Any,
        target: Any,
        evidence: List[str]
    ) -> RelationType:
        """推断关系类型"""
        # 根据实体类型组合推断
        source_type = source.type.value if hasattr(source, 'type') else 'other'
        target_type = target.type.value if hasattr(target, 'type') else 'other'

        type_pair = (source_type, target_type)

        # 规则映射
        type_mapping = {
            ('person', 'person'): RelationType.COLLEAGUE,
            ('person', 'organization'): RelationType.MEMBER_OF,
            ('person', 'location'): RelationType.LOCATED_IN,
            ('person', 'event'): RelationType.PARTICIPATES_IN,
            ('organization', 'location'): RelationType.LOCATED_IN,
            ('event', 'location'): RelationType.OCCURS_AT,
        }

        return type_mapping.get(type_pair, RelationType.DESCRIBES)


class RelationClassifier:
    """关系分类器"""

    def classify(
        self,
        entity1: Any,
        entity2: Any,
        context: str
    ) -> Tuple[RelationType, float]:
        """分类关系"""
        # 简化版：基于实体类型和上下文关键词

        entity1_type = entity1.type.value if hasattr(entity1, 'type') else 'other'
        entity2_type = entity2.type.value if hasattr(entity2, 'type') else 'other'

        # 关键词检测
        if any(kw in context for kw in ['父', '母', '子', '女', '妻', '夫']):
            return RelationType.FAMILY, 0.9
        elif any(kw in context for kw in ['老师', '学生', '师从', '门生']):
            return RelationType.TEACHER_STUDENT, 0.9
        elif any(kw in context for kw in ['同事', '合作', '共事']):
            return RelationType.COLLEAGUE, 0.85
        elif any(kw in context for kw in ['成员', '属于', '隶属']):
            return RelationType.MEMBER_OF, 0.85
        elif any(kw in context for kw in ['位于', '在', '坐落']):
            return RelationType.LOCATED_IN, 0.8
        elif any(kw in context for kw in ['参与', '参加', '加入']):
            return RelationType.PARTICIPATES_IN, 0.8
        elif any(kw in context for kw in ['导致', '引起', '造成']):
            return RelationType.CAUSES, 0.85

        # 默认
        return RelationType.DESCRIBES, 0.5


class RelationDiscoveryService:
    """关系发现服务"""

    def __init__(self):
        self.pattern_matcher = RelationPatternMatcher()
        self.cooccurrence_analyzer = CooccurrenceAnalyzer(window_size=100)
        self.classifier = RelationClassifier()

    async def discover(
        self,
        text: str,
        entities: List[Any],
        events: List[Any] = None
    ) -> Dict[str, Any]:
        """
        关系发现

        Args:
            text: 清洗后的文本
            entities: 实体列表
            events: 事件列表（可选）

        Returns:
            关系发现结果
        """
        logger.info(f"开始关系发现")

        # 1. 模式匹配
        pattern_relations = await asyncio.to_thread(
            self.pattern_matcher.match, text, entities
        )

        # 2. 共现分析
        cooc_relations = await asyncio.to_thread(
            self.cooccurrence_analyzer.analyze, text, entities
        )

        # 3. 事件关联关系
        event_relations = []
        if events:
            event_relations = self._extract_event_relations(events, entities)

        # 4. 合并去重
        all_relations = pattern_relations + cooc_relations + event_relations
        unique_relations = self._deduplicate_relations(all_relations)

        # 统计
        statistics = self._calculate_statistics(unique_relations)

        result = {
            'relations': unique_relations,
            'statistics': statistics
        }

        logger.info(f"✅ 关系发现完成：{len(unique_relations)} 个关系")
        return result

    def _extract_event_relations(
        self,
        events: List[Any],
        entities: List[Any]
    ) -> List[Relation]:
        """从事件中提取关系"""
        relations = []
        relation_id = 0

        for event in events:
            if not hasattr(event, 'who') or not hasattr(event, 'where'):
                continue

            # 人物-事件关系
            for person_name in event.who:
                person = next((e for e in entities if hasattr(e, 'name') and e.name == person_name), None)
                if person:
                    relations.append(Relation(
                        id=f"rel_event_{relation_id}",
                        type=RelationType.PARTICIPATES_IN,
                        source_id=person.id,
                        target_id=event.id,
                        source_name=person_name,
                        target_name=event.trigger,
                        evidence=[event.sentence],
                        confidence=0.9
                    ))
                    relation_id += 1

            # 事件-地点关系
            for location_name in event.where:
                location = next((e for e in entities if hasattr(e, 'name') and e.name == location_name), None)
                if location:
                    relations.append(Relation(
                        id=f"rel_event_{relation_id}",
                        type=RelationType.OCCURS_AT,
                        source_id=event.id,
                        target_id=location.id,
                        source_name=event.trigger,
                        target_name=location_name,
                        evidence=[event.sentence],
                        confidence=0.9
                    ))
                    relation_id += 1

        logger.info(f"✅ 事件关系提取：{len(relations)} 个关系")
        return relations

    def _deduplicate_relations(self, relations: List[Relation]) -> List[Relation]:
        """关系去重"""
        # 按 (source_id, target_id, type) 去重，保留置信度最高的
        seen = {}

        for relation in relations:
            key = (relation.source_id, relation.target_id, relation.type.value)
            if key not in seen:
                seen[key] = relation
            else:
                if relation.confidence > seen[key].confidence:
                    # 合并证据
                    seen[key].evidence.extend(relation.evidence)
                    seen[key].confidence = relation.confidence

        return list(seen.values())

    def _calculate_statistics(self, relations: List[Relation]) -> Dict[str, Any]:
        """计算统计信息"""
        type_counts = defaultdict(int)
        for relation in relations:
            type_counts[relation.type.value] += 1

        confidence_sum = sum(r.confidence for r in relations)

        return {
            'total_relations': len(relations),
            'relation_by_type': dict(type_counts),
            'avg_confidence': confidence_sum / len(relations) if relations else 0,
            'high_confidence_count': sum(1 for r in relations if r.confidence >= 0.8),
        }
