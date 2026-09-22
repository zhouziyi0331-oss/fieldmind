"""
Step 7: 逻辑推理服务
Logic Inference Service

功能：
1. Prolog 风格规则引擎
2. 传递闭包计算
3. 缺失信息补全
4. 冲突检测
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class InferenceType(str, Enum):
    """推理类型"""
    DEDUCTIVE = "deductive"  # 演绎推理
    INDUCTIVE = "inductive"  # 归纳推理
    ABDUCTIVE = "abductive"  # 溯因推理
    TRANSITIVE = "transitive"  # 传递推理
    COMPLETION = "completion"  # 补全推理


class ConflictType(str, Enum):
    """冲突类型"""
    TIME_CONFLICT = "time_conflict"  # 时间冲突
    SPACE_CONFLICT = "space_conflict"  # 空间冲突
    LOGIC_CONFLICT = "logic_conflict"  # 逻辑冲突
    CONSTRAINT_VIOLATION = "constraint_violation"  # 约束违反
    CIRCULAR_DEPENDENCY = "circular_dependency"  # 循环依赖


@dataclass
class Fact:
    """事实"""
    predicate: str  # 谓词
    subject: str  # 主体
    object: Optional[str] = None  # 客体
    confidence: float = 1.0
    source: str = ""  # 来源


@dataclass
class Rule:
    """推理规则"""
    id: str
    premises: List[str]  # 前提（谓词模式）
    conclusion: str  # 结论（谓词模式）
    confidence: float = 1.0
    description: str = ""


@dataclass
class InferenceFinding:
    """推理发现"""
    id: str
    type: InferenceType
    conclusion: Fact  # 推理出的结论
    premises: List[Fact]  # 前提事实
    rule: Optional[Rule] = None  # 使用的规则
    confidence: float = 1.0
    reasoning_steps: List[str] = field(default_factory=list)


@dataclass
class Conflict:
    """冲突"""
    id: str
    type: ConflictType
    description: str
    conflicting_facts: List[Fact]
    severity: float = 1.0  # 严重程度 0-1


class RuleEngine:
    """Prolog 风格规则引擎"""

    def __init__(self):
        self.facts: List[Fact] = []
        self.rules: List[Rule] = []
        self._initialize_rules()

    def _initialize_rules(self):
        """初始化推理规则"""
        # 传递性规则
        self.rules.append(Rule(
            id="rule_transitive_located_in",
            premises=["located_in(?X, ?Y)", "located_in(?Y, ?Z)"],
            conclusion="located_in(?X, ?Z)",
            confidence=0.95,
            description="位置关系的传递性：如果X在Y，Y在Z，则X在Z"
        ))

        self.rules.append(Rule(
            id="rule_transitive_part_of",
            premises=["part_of(?X, ?Y)", "part_of(?Y, ?Z)"],
            conclusion="part_of(?X, ?Z)",
            confidence=0.95,
            description="部分关系的传递性"
        ))

        self.rules.append(Rule(
            id="rule_transitive_superior",
            premises=["superior_subordinate(?X, ?Y)", "superior_subordinate(?Y, ?Z)"],
            conclusion="superior_subordinate(?X, ?Z)",
            confidence=0.9,
            description="上下级关系的传递性"
        ))

        # 对称性规则
        self.rules.append(Rule(
            id="rule_symmetric_colleague",
            premises=["colleague(?X, ?Y)"],
            conclusion="colleague(?Y, ?X)",
            confidence=1.0,
            description="同事关系的对称性"
        ))

        self.rules.append(Rule(
            id="rule_symmetric_friend",
            premises=["friend(?X, ?Y)"],
            conclusion="friend(?Y, ?X)",
            confidence=1.0,
            description="朋友关系的对称性"
        ))

        # 组合规则
        self.rules.append(Rule(
            id="rule_member_located",
            premises=["member_of(?Person, ?Org)", "located_in(?Org, ?Location)"],
            conclusion="associated_with(?Person, ?Location)",
            confidence=0.8,
            description="如果人是组织成员，组织在某地，则人与该地有关联"
        ))

        self.rules.append(Rule(
            id="rule_participates_occurs",
            premises=["participates_in(?Person, ?Event)", "occurs_at(?Event, ?Location)"],
            conclusion="was_at(?Person, ?Location)",
            confidence=0.85,
            description="如果人参与事件，事件发生在某地，则人在该地"
        ))

        # 家庭关系推理
        self.rules.append(Rule(
            id="rule_family_parent_child",
            premises=["family(?Parent, ?Child)", "is_parent(?Parent)"],
            conclusion="has_child(?Parent, ?Child)",
            confidence=0.9,
            description="家庭关系中的父母-子女关系"
        ))

        # 时间推理
        self.rules.append(Rule(
            id="rule_temporal_order",
            premises=["preceded_by(?Event1, ?Event2)", "preceded_by(?Event2, ?Event3)"],
            conclusion="preceded_by(?Event1, ?Event3)",
            confidence=0.9,
            description="时间顺序的传递性"
        ))

        logger.info(f"✅ 规则引擎初始化：{len(self.rules)} 条规则")

    def add_facts(self, facts: List[Fact]):
        """添加事实"""
        self.facts.extend(facts)

    def infer(self) -> List[InferenceFinding]:
        """执行推理"""
        findings = []
        finding_id = 0

        # 对每条规则进行模式匹配
        for rule in self.rules:
            matches = self._match_rule(rule)
            for match in matches:
                # 创建推理发现
                finding = InferenceFinding(
                    id=f"inference_{finding_id}",
                    type=InferenceType.DEDUCTIVE,
                    conclusion=match['conclusion'],
                    premises=match['premises'],
                    rule=rule,
                    confidence=rule.confidence * min(p.confidence for p in match['premises']),
                    reasoning_steps=match['steps']
                )
                findings.append(finding)
                finding_id += 1

                # 将推理出的结论加入事实库（用于链式推理）
                self.facts.append(match['conclusion'])

        logger.info(f"✅ 推理完成：{len(findings)} 个新发现")
        return findings

    def _match_rule(self, rule: Rule) -> List[Dict[str, Any]]:
        """匹配规则"""
        matches = []

        # 简化版：只处理2个前提的情况
        if len(rule.premises) == 1:
            # 单前提规则（如对称性）
            premise_pattern = rule.premises[0]
            predicate = premise_pattern.split('(')[0]

            for fact in self.facts:
                if fact.predicate == predicate:
                    # 应用规则
                    conclusion = self._apply_rule_single(rule, fact)
                    if conclusion and not self._fact_exists(conclusion):
                        matches.append({
                            'premises': [fact],
                            'conclusion': conclusion,
                            'steps': [
                                f"已知：{fact.predicate}({fact.subject}, {fact.object})",
                                f"应用规则：{rule.description}",
                                f"推理：{conclusion.predicate}({conclusion.subject}, {conclusion.object})"
                            ]
                        })

        elif len(rule.premises) == 2:
            # 双前提规则（如传递性、组合）
            pattern1 = rule.premises[0]
            pattern2 = rule.premises[1]

            predicate1 = pattern1.split('(')[0]
            predicate2 = pattern2.split('(')[0]

            # 查找匹配的事实对
            for fact1 in self.facts:
                if fact1.predicate != predicate1:
                    continue

                for fact2 in self.facts:
                    if fact2.predicate != predicate2:
                        continue

                    # 检查变量绑定
                    if self._check_binding(pattern1, pattern2, fact1, fact2):
                        conclusion = self._apply_rule_double(rule, fact1, fact2)
                        if conclusion and not self._fact_exists(conclusion):
                            matches.append({
                                'premises': [fact1, fact2],
                                'conclusion': conclusion,
                                'steps': [
                                    f"已知1：{fact1.predicate}({fact1.subject}, {fact1.object})",
                                    f"已知2：{fact2.predicate}({fact2.subject}, {fact2.object})",
                                    f"应用规则：{rule.description}",
                                    f"推理：{conclusion.predicate}({conclusion.subject}, {conclusion.object})"
                                ]
                            })

        return matches

    def _check_binding(self, pattern1: str, pattern2: str, fact1: Fact, fact2: Fact) -> bool:
        """检查变量绑定是否一致"""
        # 简化版：检查传递性模式 predicate(?X, ?Y) 和 predicate(?Y, ?Z)
        # fact1.object 应该等于 fact2.subject
        return fact1.object == fact2.subject

    def _apply_rule_single(self, rule: Rule, fact: Fact) -> Optional[Fact]:
        """应用单前提规则"""
        conclusion_pattern = rule.conclusion
        predicate = conclusion_pattern.split('(')[0]

        # 对称性：交换主体和客体
        if '?Y, ?X' in conclusion_pattern:
            return Fact(
                predicate=predicate,
                subject=fact.object,
                object=fact.subject,
                confidence=fact.confidence * rule.confidence,
                source=f"inferred_by_{rule.id}"
            )

        return None

    def _apply_rule_double(self, rule: Rule, fact1: Fact, fact2: Fact) -> Optional[Fact]:
        """应用双前提规则"""
        conclusion_pattern = rule.conclusion
        predicate = conclusion_pattern.split('(')[0]

        # 传递性：?X 和 ?Z
        # fact1: predicate(?X, ?Y)
        # fact2: predicate(?Y, ?Z)
        # conclusion: predicate(?X, ?Z)

        if '?X, ?Z' in conclusion_pattern or '?X, ?Y' in conclusion_pattern:
            return Fact(
                predicate=predicate,
                subject=fact1.subject,
                object=fact2.object,
                confidence=min(fact1.confidence, fact2.confidence) * rule.confidence,
                source=f"inferred_by_{rule.id}"
            )

        # 组合规则：可能是不同谓词
        # 需要根据具体规则处理
        return Fact(
            predicate=predicate,
            subject=fact1.subject,
            object=fact2.object,
            confidence=min(fact1.confidence, fact2.confidence) * rule.confidence,
            source=f"inferred_by_{rule.id}"
        )

    def _fact_exists(self, fact: Fact) -> bool:
        """检查事实是否已存在"""
        for existing in self.facts:
            if (existing.predicate == fact.predicate and
                existing.subject == fact.subject and
                existing.object == fact.object):
                return True
        return False


class TransitiveClosureCalculator:
    """传递闭包计算器"""

    def calculate(self, relations: List[Any], relation_type: str) -> List[Tuple[str, str]]:
        """
        计算传递闭包（Floyd-Warshall 算法）

        Args:
            relations: 关系列表
            relation_type: 关系类型

        Returns:
            传递闭包（源ID，目标ID）对列表
        """
        # 过滤指定类型的关系
        typed_relations = [
            r for r in relations
            if hasattr(r, 'type') and r.type.value == relation_type
        ]

        if not typed_relations:
            return []

        # 构建邻接表
        graph = defaultdict(set)
        nodes = set()

        for rel in typed_relations:
            if hasattr(rel, 'source_id') and hasattr(rel, 'target_id'):
                graph[rel.source_id].add(rel.target_id)
                nodes.add(rel.source_id)
                nodes.add(rel.target_id)

        # Floyd-Warshall 算法
        nodes_list = list(nodes)
        n = len(nodes_list)
        node_to_idx = {node: i for i, node in enumerate(nodes_list)}

        # 初始化可达性矩阵
        reachable = [[False] * n for _ in range(n)]

        # 初始化直接边
        for i in range(n):
            reachable[i][i] = True  # 自反性
            node = nodes_list[i]
            for target in graph[node]:
                j = node_to_idx[target]
                reachable[i][j] = True

        # Floyd-Warshall
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if reachable[i][k] and reachable[k][j]:
                        reachable[i][j] = True

        # 提取传递闭包（排除原有直接边和自反边）
        closure = []
        for i in range(n):
            for j in range(n):
                if i != j and reachable[i][j]:
                    source = nodes_list[i]
                    target = nodes_list[j]
                    # 检查是否是新推理出的边
                    if target not in graph[source]:
                        closure.append((source, target))

        logger.info(f"✅ 传递闭包计算：{len(typed_relations)} 个关系 → {len(closure)} 个推理关系")
        return closure


class MissingInfoCompleter:
    """缺失信息补全器"""

    def complete(
        self,
        entities: List[Any],
        events: List[Any],
        relations: List[Any]
    ) -> List[InferenceFinding]:
        """补全缺失信息"""
        findings = []
        finding_id = 0

        # 1. 补全事件的地点信息
        for event in events:
            if not hasattr(event, 'where') or not event.where:
                # 尝试从参与者的位置推断
                if hasattr(event, 'who') and event.who:
                    for person_name in event.who:
                        # 查找人物实体
                        person = next((e for e in entities if hasattr(e, 'name') and e.name == person_name), None)
                        if person:
                            # 查找人物的位置关系
                            person_locations = [
                                r.target_name for r in relations
                                if (hasattr(r, 'source_id') and r.source_id == person.id and
                                    hasattr(r, 'type') and r.type.value == 'located_in')
                            ]
                            if person_locations:
                                # 推断事件发生地
                                inferred_location = person_locations[0]
                                conclusion = Fact(
                                    predicate="occurs_at",
                                    subject=event.id,
                                    object=inferred_location,
                                    confidence=0.7,
                                    source="inferred_from_participant_location"
                                )
                                finding = InferenceFinding(
                                    id=f"completion_{finding_id}",
                                    type=InferenceType.COMPLETION,
                                    conclusion=conclusion,
                                    premises=[],
                                    confidence=0.7,
                                    reasoning_steps=[
                                        f"事件：{event.trigger}",
                                        f"参与者：{person_name}",
                                        f"参与者位于：{inferred_location}",
                                        f"推断事件发生地：{inferred_location}"
                                    ]
                                )
                                findings.append(finding)
                                finding_id += 1
                                break

        # 2. 补全事件的时间信息
        for event in events:
            if not hasattr(event, 'when') or not event.when:
                # 尝试从前后事件推断
                # 简化版：暂不实现
                pass

        logger.info(f"✅ 缺失信息补全：{len(findings)} 个补全")
        return findings


class ConflictDetector:
    """冲突检测器"""

    def detect(
        self,
        entities: List[Any],
        events: List[Any],
        relations: List[Any],
        ontology: Optional[Any] = None
    ) -> List[Conflict]:
        """检测冲突"""
        conflicts = []
        conflict_id = 0

        # 1. 时间冲突检测
        time_conflicts = self._detect_time_conflicts(events)
        conflicts.extend(time_conflicts)

        # 2. 空间冲突检测
        space_conflicts = self._detect_space_conflicts(events)
        conflicts.extend(space_conflicts)

        # 3. 逻辑冲突检测
        logic_conflicts = self._detect_logic_conflicts(relations)
        conflicts.extend(logic_conflicts)

        # 4. 约束违反检测
        if ontology:
            constraint_violations = self._detect_constraint_violations(relations, ontology)
            conflicts.extend(constraint_violations)

        # 5. 循环依赖检测
        circular_deps = self._detect_circular_dependencies(relations)
        conflicts.extend(circular_deps)

        logger.info(f"✅ 冲突检测：{len(conflicts)} 个冲突")
        return conflicts

    def _detect_time_conflicts(self, events: List[Any]) -> List[Conflict]:
        """检测时间冲突（一个人同时出现在两个地方）"""
        conflicts = []
        # 简化版：检查同一人物在相同时间参与多个事件
        # 实际需要解析时间并比较
        return conflicts

    def _detect_space_conflicts(self, events: List[Any]) -> List[Conflict]:
        """检测空间冲突"""
        conflicts = []
        # 简化版：检查物理上不可能的空间关系
        return conflicts

    def _detect_logic_conflicts(self, relations: List[Any]) -> List[Conflict]:
        """检测逻辑冲突"""
        conflicts = []
        conflict_id = 0

        # 检查对称关系的不一致
        symmetric_types = ['colleague', 'friend', 'adjacent_to']

        for rel_type in symmetric_types:
            typed_rels = [r for r in relations if hasattr(r, 'type') and r.type.value == rel_type]

            # 构建关系对
            rel_pairs = {}
            for rel in typed_rels:
                if hasattr(rel, 'source_id') and hasattr(rel, 'target_id'):
                    key = tuple(sorted([rel.source_id, rel.target_id]))
                    if key not in rel_pairs:
                        rel_pairs[key] = []
                    rel_pairs[key].append(rel)

            # 检查是否有反向关系
            for (id1, id2), rels in rel_pairs.items():
                # 应该有两个方向的关系
                directions = set()
                for rel in rels:
                    if rel.source_id == id1:
                        directions.add('forward')
                    else:
                        directions.add('backward')

                if len(directions) == 1:
                    # 缺少反向关系（轻微冲突）
                    conflicts.append(Conflict(
                        id=f"conflict_{conflict_id}",
                        type=ConflictType.LOGIC_CONFLICT,
                        description=f"对称关系 {rel_type} 缺少反向关系",
                        conflicting_facts=[],
                        severity=0.3
                    ))
                    conflict_id += 1

        return conflicts

    def _detect_constraint_violations(self, relations: List[Any], ontology: Any) -> List[Conflict]:
        """检测约束违反"""
        conflicts = []
        # 检查定义域和值域约束
        # 实际需要访问本体的约束定义
        return conflicts

    def _detect_circular_dependencies(self, relations: List[Any]) -> List[Conflict]:
        """检测循环依赖"""
        conflicts = []
        conflict_id = 0

        # 检查非对称关系的循环（如 superior_subordinate）
        non_symmetric_types = ['superior_subordinate', 'teacher_student', 'part_of']

        for rel_type in non_symmetric_types:
            typed_rels = [r for r in relations if hasattr(r, 'type') and r.type.value == rel_type]

            # 构建有向图
            graph = defaultdict(list)
            for rel in typed_rels:
                if hasattr(rel, 'source_id') and hasattr(rel, 'target_id'):
                    graph[rel.source_id].append(rel.target_id)

            # DFS 检测环
            visited = set()
            rec_stack = set()

            def has_cycle(node):
                visited.add(node)
                rec_stack.add(node)

                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True

                rec_stack.remove(node)
                return False

            for node in graph:
                if node not in visited:
                    if has_cycle(node):
                        conflicts.append(Conflict(
                            id=f"conflict_{conflict_id}",
                            type=ConflictType.CIRCULAR_DEPENDENCY,
                            description=f"关系 {rel_type} 存在循环依赖",
                            conflicting_facts=[],
                            severity=0.8
                        ))
                        conflict_id += 1
                        break

        return conflicts


class LogicInferenceService:
    """逻辑推理服务"""

    def __init__(self, use_workflow_engine: bool = True):
        self.rule_engine = RuleEngine()
        self.transitive_calculator = TransitiveClosureCalculator()
        self.info_completer = MissingInfoCompleter()
        self.conflict_detector = ConflictDetector()
        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)

    async def infer(
        self,
        entities: List[Any],
        relations: List[Any],
        events: List[Any],
        ontology: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        逻辑推理

        Args:
            entities: 实体列表
            relations: 关系列表
            events: 事件列表
            ontology: 本体（可选）

        Returns:
            推理结果
        """
        logger.info(f"开始逻辑推理")

        # 1. 构建事实库
        facts = self._build_facts(entities, relations, events)
        self.rule_engine.add_facts(facts)
        logger.info(f"✅ 事实库构建：{len(facts)} 个事实")

        # 2. 规则推理
        deductive_findings = await asyncio.to_thread(self.rule_engine.infer)

        # 3. 传递闭包计算
        transitive_relations = []
        for rel_type in ['located_in', 'part_of', 'superior_subordinate']:
            closure = await asyncio.to_thread(
                self.transitive_calculator.calculate, relations, rel_type
            )
            transitive_relations.extend(closure)

        # 4. 缺失信息补全
        completion_findings = await asyncio.to_thread(
            self.info_completer.complete, entities, events, relations
        )

        # 5. 冲突检测
        conflicts = await asyncio.to_thread(
            self.conflict_detector.detect, entities, events, relations, ontology
        )

        # 统计
        all_findings = deductive_findings + completion_findings
        statistics = {
            'total_findings': len(all_findings),
            'deductive_findings': len(deductive_findings),
            'completion_findings': len(completion_findings),
            'transitive_relations': len(transitive_relations),
            'conflicts': len(conflicts),
            'conflict_by_type': self._count_by_type(conflicts),
        }

        result = {
            'findings': all_findings,
            'transitive_relations': transitive_relations,
            'conflicts': conflicts,
            'statistics': statistics
        }

        logger.info(f"✅ 逻辑推理完成：{len(all_findings)} 个发现，{len(conflicts)} 个冲突")
        return result

    def _build_facts(
        self,
        entities: List[Any],
        relations: List[Any],
        events: List[Any]
    ) -> List[Fact]:
        """构建事实库"""
        facts = []

        # 从关系构建事实
        for rel in relations:
            if hasattr(rel, 'type') and hasattr(rel, 'source_id') and hasattr(rel, 'target_id'):
                fact = Fact(
                    predicate=rel.type.value,
                    subject=rel.source_id,
                    object=rel.target_id,
                    confidence=rel.confidence if hasattr(rel, 'confidence') else 1.0,
                    source="relation"
                )
                facts.append(fact)

        # 从事件构建事实
        for event in events:
            if hasattr(event, 'who'):
                for person_name in event.who:
                    fact = Fact(
                        predicate="participates_in",
                        subject=person_name,
                        object=event.id,
                        confidence=0.9,
                        source="event"
                    )
                    facts.append(fact)

            if hasattr(event, 'where'):
                for location_name in event.where:
                    fact = Fact(
                        predicate="occurs_at",
                        subject=event.id,
                        object=location_name,
                        confidence=0.9,
                        source="event"
                    )
                    facts.append(fact)

        return facts

    def _count_by_type(self, conflicts: List[Conflict]) -> Dict[str, int]:
        """按类型统计冲突"""
        counts = defaultdict(int)
        for conflict in conflicts:
            counts[conflict.type.value] += 1
        return dict(counts)
