"""
Step 8: 知识单元化服务
Knowledge Unitization Service

功能：
1. 事实提取
2. 洞察生成
3. 摘要创建
4. 知识评分（重要性、置信度、完整性）
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class KnowledgeUnitType(str, Enum):
    """知识单元类型"""
    FACT = "fact"  # 事实
    INSIGHT = "insight"  # 洞察
    INFERENCE = "inference"  # 推理
    SUMMARY = "summary"  # 摘要


@dataclass
class KnowledgeUnit:
    """知识单元"""
    id: str
    type: KnowledgeUnitType
    content: str
    title: str = ""

    # 评分
    importance: float = 0.5  # 重要性 0-1
    confidence: float = 1.0  # 置信度 0-1
    completeness: float = 1.0  # 完整性 0-1

    # 关联
    related_entities: List[str] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    related_relations: List[str] = field(default_factory=list)

    # 元数据
    tags: List[str] = field(default_factory=list)
    source: str = ""
    evidence: List[str] = field(default_factory=list)


class FactExtractor:
    """事实提取器"""

    def extract(
        self,
        entities: List[Any],
        relations: List[Any],
        events: List[Any]
    ) -> List[KnowledgeUnit]:
        """从实体、关系、事件中提取事实"""
        facts = []
        fact_id = 0

        # 1. 从实体提取事实
        for entity in entities:
            if not hasattr(entity, 'name'):
                continue

            content = f"{entity.name}"
            if hasattr(entity, 'type'):
                content += f"是一个{entity.type.value}"

            fact = KnowledgeUnit(
                id=f"fact_{fact_id}",
                type=KnowledgeUnitType.FACT,
                content=content,
                title=entity.name,
                importance=0.6,
                confidence=entity.confidence if hasattr(entity, 'confidence') else 1.0,
                completeness=1.0,
                related_entities=[entity.id],
                tags=[entity.type.value] if hasattr(entity, 'type') else [],
                source="entity"
            )
            facts.append(fact)
            fact_id += 1

        # 2. 从关系提取事实
        for relation in relations:
            if not (hasattr(relation, 'source_name') and hasattr(relation, 'target_name')):
                continue

            content = f"{relation.source_name} {self._relation_to_text(relation.type.value)} {relation.target_name}"

            fact = KnowledgeUnit(
                id=f"fact_{fact_id}",
                type=KnowledgeUnitType.FACT,
                content=content,
                title=f"{relation.source_name}-{relation.target_name}",
                importance=0.7,
                confidence=relation.confidence if hasattr(relation, 'confidence') else 1.0,
                completeness=1.0,
                related_entities=[relation.source_id, relation.target_id] if hasattr(relation, 'source_id') else [],
                related_relations=[relation.id] if hasattr(relation, 'id') else [],
                tags=[relation.type.value] if hasattr(relation, 'type') else [],
                source="relation",
                evidence=relation.evidence if hasattr(relation, 'evidence') else []
            )
            facts.append(fact)
            fact_id += 1

        # 3. 从事件提取事实
        for event in events:
            if not hasattr(event, 'what'):
                continue

            content = event.what
            if hasattr(event, 'who') and event.who:
                content = f"{', '.join(event.who)} {content}"
            if hasattr(event, 'when') and event.when:
                content += f"（{', '.join(event.when)}）"
            if hasattr(event, 'where') and event.where:
                content += f"在{', '.join(event.where)}"

            fact = KnowledgeUnit(
                id=f"fact_{fact_id}",
                type=KnowledgeUnitType.FACT,
                content=content,
                title=event.trigger if hasattr(event, 'trigger') else "事件",
                importance=0.8,
                confidence=event.confidence if hasattr(event, 'confidence') else 1.0,
                completeness=self._calculate_event_completeness(event),
                related_events=[event.id] if hasattr(event, 'id') else [],
                tags=[event.type.value] if hasattr(event, 'type') else [],
                source="event"
            )
            facts.append(fact)
            fact_id += 1

        logger.info(f"✅ 事实提取：{len(facts)} 个事实")
        return facts

    def _relation_to_text(self, rel_type: str) -> str:
        """关系类型转文本"""
        mapping = {
            'family': '是...的家人',
            'colleague': '与...是同事',
            'teacher_student': '是...的老师/学生',
            'friend': '与...是朋友',
            'member_of': '是...的成员',
            'located_in': '位于',
            'participates_in': '参与了',
            'occurs_at': '发生在',
            'causes': '导致',
        }
        return mapping.get(rel_type, rel_type)

    def _calculate_event_completeness(self, event: Any) -> float:
        """计算事件完整性"""
        score = 0.0
        if hasattr(event, 'who') and event.who:
            score += 0.2
        if hasattr(event, 'what') and event.what:
            score += 0.3
        if hasattr(event, 'when') and event.when:
            score += 0.2
        if hasattr(event, 'where') and event.where:
            score += 0.2
        if hasattr(event, 'why') and event.why:
            score += 0.05
        if hasattr(event, 'how') and event.how:
            score += 0.05
        return min(score, 1.0)


class InsightGenerator:
    """洞察生成器"""

    def generate(
        self,
        inference_findings: List[Any],
        conflicts: List[Any],
        ontology: Optional[Any] = None
    ) -> List[KnowledgeUnit]:
        """从推理结果生成洞察"""
        insights = []
        insight_id = 0

        # 1. 从推理发现生成洞察
        for finding in inference_findings:
            if not hasattr(finding, 'conclusion'):
                continue

            content = f"通过推理发现：{finding.conclusion.predicate}({finding.conclusion.subject}, {finding.conclusion.object})"
            if hasattr(finding, 'reasoning_steps') and finding.reasoning_steps:
                content += f"\n推理过程：" + " → ".join(finding.reasoning_steps)

            insight = KnowledgeUnit(
                id=f"insight_{insight_id}",
                type=KnowledgeUnitType.INSIGHT,
                content=content,
                title=f"推理：{finding.conclusion.predicate}",
                importance=0.75,
                confidence=finding.confidence if hasattr(finding, 'confidence') else 0.8,
                completeness=1.0,
                tags=['inference', finding.type.value] if hasattr(finding, 'type') else ['inference'],
                source="inference"
            )
            insights.append(insight)
            insight_id += 1

        # 2. 从冲突生成洞察
        for conflict in conflicts:
            if not hasattr(conflict, 'description'):
                continue

            content = f"发现冲突：{conflict.description}"
            severity_text = "严重" if conflict.severity > 0.7 else "中等" if conflict.severity > 0.4 else "轻微"

            insight = KnowledgeUnit(
                id=f"insight_{insight_id}",
                type=KnowledgeUnitType.INSIGHT,
                content=content,
                title=f"冲突：{conflict.type.value}",
                importance=conflict.severity,
                confidence=1.0,
                completeness=1.0,
                tags=['conflict', conflict.type.value, severity_text],
                source="conflict_detection"
            )
            insights.append(insight)
            insight_id += 1

        # 3. 从本体生成洞察
        if ontology and hasattr(ontology, 'concepts'):
            # 找出最大的概念类别
            top_concepts = sorted(
                ontology.concepts.values(),
                key=lambda c: c.instance_count if hasattr(c, 'instance_count') else 0,
                reverse=True
            )[:5]

            for concept in top_concepts:
                content = f"主要概念类别：{concept.name}，包含 {concept.instance_count} 个实例"
                insight = KnowledgeUnit(
                    id=f"insight_{insight_id}",
                    type=KnowledgeUnitType.INSIGHT,
                    content=content,
                    title=f"概念：{concept.name}",
                    importance=0.7,
                    confidence=1.0,
                    completeness=1.0,
                    tags=['ontology', 'concept'],
                    source="ontology_analysis"
                )
                insights.append(insight)
                insight_id += 1

        logger.info(f"✅ 洞察生成：{len(insights)} 个洞察")
        return insights


class SummaryCreator:
    """摘要创建器"""

    def create(
        self,
        entities: List[Any],
        events: List[Any],
        relations: List[Any],
        knowledge_units: List[KnowledgeUnit]
    ) -> List[KnowledgeUnit]:
        """创建摘要"""
        summaries = []
        summary_id = 0

        # 1. 总体摘要
        overall_summary = self._create_overall_summary(entities, events, relations)
        summaries.append(KnowledgeUnit(
            id=f"summary_{summary_id}",
            type=KnowledgeUnitType.SUMMARY,
            content=overall_summary,
            title="总体摘要",
            importance=1.0,
            confidence=1.0,
            completeness=1.0,
            tags=['overall', 'summary'],
            source="summary_creator"
        ))
        summary_id += 1

        # 2. 按类别摘要
        category_summaries = self._create_category_summaries(knowledge_units)
        for category, content in category_summaries.items():
            summaries.append(KnowledgeUnit(
                id=f"summary_{summary_id}",
                type=KnowledgeUnitType.SUMMARY,
                content=content,
                title=f"{category}摘要",
                importance=0.8,
                confidence=1.0,
                completeness=1.0,
                tags=[category, 'summary'],
                source="summary_creator"
            ))
            summary_id += 1

        logger.info(f"✅ 摘要创建：{len(summaries)} 个摘要")
        return summaries

    def _create_overall_summary(
        self,
        entities: List[Any],
        events: List[Any],
        relations: List[Any]
    ) -> str:
        """创建总体摘要"""
        # 统计
        entity_count = len(entities)
        event_count = len(events)
        relation_count = len(relations)

        # 统计实体类型
        entity_types = Counter()
        for entity in entities:
            if hasattr(entity, 'type'):
                entity_types[entity.type.value] += 1

        # 统计事件类型
        event_types = Counter()
        for event in events:
            if hasattr(event, 'type'):
                event_types[event.type.value] += 1

        summary = f"本文档包含 {entity_count} 个实体、{event_count} 个事件、{relation_count} 个关系。"

        if entity_types:
            top_entity_types = entity_types.most_common(3)
            summary += f"\n主要实体类型：{', '.join(f'{t}({c}个)' for t, c in top_entity_types)}。"

        if event_types:
            top_event_types = event_types.most_common(3)
            summary += f"\n主要事件类型：{', '.join(f'{t}({c}个)' for t, c in top_event_types)}。"

        return summary

    def _create_category_summaries(self, knowledge_units: List[KnowledgeUnit]) -> Dict[str, str]:
        """按类别创建摘要"""
        summaries = {}

        # 按标签分组
        tag_groups = defaultdict(list)
        for unit in knowledge_units:
            for tag in unit.tags:
                tag_groups[tag].append(unit)

        # 为每个标签创建摘要
        for tag, units in tag_groups.items():
            if len(units) < 2:
                continue

            summary = f"{tag}类别包含 {len(units)} 个知识单元。"

            # 找出最重要的几个
            top_units = sorted(units, key=lambda u: u.importance, reverse=True)[:3]
            if top_units:
                summary += "\n关键内容：\n"
                for unit in top_units:
                    summary += f"- {unit.content[:100]}...\n"

            summaries[tag] = summary

        return summaries


class KnowledgeScorer:
    """知识评分器"""

    def score(self, knowledge_units: List[KnowledgeUnit]) -> List[KnowledgeUnit]:
        """评分知识单元"""
        for unit in knowledge_units:
            # 重要性评分
            unit.importance = self._score_importance(unit)

            # 置信度已在创建时设置

            # 完整性评分
            unit.completeness = self._score_completeness(unit)

        logger.info(f"✅ 知识评分：{len(knowledge_units)} 个单元")
        return knowledge_units

    def _score_importance(self, unit: KnowledgeUnit) -> float:
        """评分重要性"""
        score = 0.5

        # 根据类型调整
        if unit.type == KnowledgeUnitType.SUMMARY:
            score += 0.3
        elif unit.type == KnowledgeUnitType.INSIGHT:
            score += 0.2
        elif unit.type == KnowledgeUnitType.INFERENCE:
            score += 0.15

        # 根据关联数量调整
        related_count = (
            len(unit.related_entities) +
            len(unit.related_events) +
            len(unit.related_relations)
        )
        score += min(related_count * 0.05, 0.2)

        # 根据标签调整
        important_tags = ['conflict', 'inference', 'summary', 'political', 'military']
        if any(tag in important_tags for tag in unit.tags):
            score += 0.1

        return min(score, 1.0)

    def _score_completeness(self, unit: KnowledgeUnit) -> float:
        """评分完整性"""
        score = 0.5

        # 有标题
        if unit.title:
            score += 0.1

        # 有内容
        if unit.content and len(unit.content) > 10:
            score += 0.2

        # 有关联
        if unit.related_entities or unit.related_events or unit.related_relations:
            score += 0.1

        # 有证据
        if unit.evidence:
            score += 0.1

        return min(score, 1.0)


class KnowledgeUnitizationService:
    """知识单元化服务"""

    def __init__(self):
        self.fact_extractor = FactExtractor()
        self.insight_generator = InsightGenerator()
        self.summary_creator = SummaryCreator()
        self.scorer = KnowledgeScorer()

    async def unitize(
        self,
        entities: List[Any],
        relations: List[Any],
        events: List[Any],
        inference_result: Dict[str, Any],
        ontology: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        知识单元化

        Args:
            entities: 实体列表
            relations: 关系列表
            events: 事件列表
            inference_result: 推理结果
            ontology: 本体（可选）

        Returns:
            知识单元化结果
        """
        logger.info(f"开始知识单元化")

        # 1. 事实提取
        facts = await asyncio.to_thread(
            self.fact_extractor.extract, entities, relations, events
        )

        # 2. 洞察生成
        inference_findings = inference_result.get('findings', [])
        conflicts = inference_result.get('conflicts', [])
        insights = await asyncio.to_thread(
            self.insight_generator.generate, inference_findings, conflicts, ontology
        )

        # 3. 合并所有知识单元
        all_units = facts + insights

        # 4. 摘要创建
        summaries = await asyncio.to_thread(
            self.summary_creator.create, entities, events, relations, all_units
        )
        all_units.extend(summaries)

        # 5. 知识评分
        all_units = await asyncio.to_thread(self.scorer.score, all_units)

        # 统计
        statistics = {
            'total_units': len(all_units),
            'facts': len(facts),
            'insights': len(insights),
            'summaries': len(summaries),
            'avg_importance': sum(u.importance for u in all_units) / len(all_units) if all_units else 0,
            'avg_confidence': sum(u.confidence for u in all_units) / len(all_units) if all_units else 0,
            'avg_completeness': sum(u.completeness for u in all_units) / len(all_units) if all_units else 0,
        }

        result = {
            'knowledge_units': all_units,
            'statistics': statistics
        }

        logger.info(f"✅ 知识单元化完成：{len(all_units)} 个知识单元")
        return result
