"""
知识图谱构建器 - 深度集成Graphiti

从SBPACK自动构建动态知识图谱：
- 实体提取和消歧
- 关系识别和验证
- 时序事件追踪
- 图谱优化和维护
"""
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import json

from app.models.knowledge_graph import Entity, Relation, TemporalEvent, EntityMention
from app.models.sbpack import SBPACKPackage, KnowledgeItem, SkillItem
from app.services.llm_enhancer import LLMEnhancer

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    """
    知识图谱构建器

    从多种来源构建统一的知识图谱：
    1. SBPACK蒸馏结果
    2. Obsidian笔记
    3. 用户手动输入
    """

    # 实体类型映射
    ENTITY_TYPES = {
        'PERSON': '人物',
        'ORGANIZATION': '组织',
        'CONCEPT': '概念',
        'EVENT': '事件',
        'LOCATION': '地点',
        'SKILL': '技能',
        'KNOWLEDGE': '知识点',
        'PRODUCT': '产品',
        'TECHNOLOGY': '技术'
    }

    # 关系类型
    RELATION_TYPES = {
        'WORKS_FOR': '就职于',
        'FOUNDED': '创立',
        'INVENTED': '发明',
        'LOCATED_IN': '位于',
        'PART_OF': '属于',
        'PREREQUISITE': '前置条件',
        'RELATED_TO': '相关',
        'CAUSES': '导致',
        'ENABLES': '使能',
        'APPLIES_TO': '应用于'
    }

    def __init__(self, db: Session, llm_enhancer: Optional[LLMEnhancer] = None):
        self.db = db
        self.llm = llm_enhancer
        self.entity_cache = {}  # 名称 -> Entity的缓存

    async def build_from_sbpack(self, package_id: int) -> Dict[str, Any]:
        """
        从SBPACK构建知识图谱

        流程：
        1. 加载SBPACK数据
        2. 提取实体
        3. 识别关系
        4. 构建时序事件
        5. 消歧和合并
        6. 保存图谱
        """
        logger.info(f"开始从SBPACK构建知识图谱: package_id={package_id}")

        # 1. 加载SBPACK数据
        package = self.db.query(SBPACKPackage).filter(SBPACKPackage.id == package_id).first()
        if not package:
            raise ValueError(f"Package {package_id} not found")

        knowledge_items = self.db.query(KnowledgeItem).filter(
            KnowledgeItem.package_id == package_id
        ).all()

        skill_items = self.db.query(SkillItem).filter(
            SkillItem.package_id == package_id
        ).all()

        # 2. 提取实体
        entities = await self._extract_entities_from_sbpack(
            knowledge_items,
            skill_items,
            package_id
        )

        logger.info(f"提取了 {len(entities)} 个实体")

        # 3. 识别关系
        relations = await self._extract_relations_from_sbpack(
            entities,
            knowledge_items,
            skill_items,
            package_id
        )

        logger.info(f"识别了 {len(relations)} 个关系")

        # 4. 构建时序事件
        events = await self._extract_temporal_events(
            knowledge_items,
            skill_items,
            package_id
        )

        logger.info(f"构建了 {len(events)} 个时序事件")

        # 5. 消歧和合并
        deduplicated_entities = await self._deduplicate_entities(entities)
        logger.info(f"去重后剩余 {len(deduplicated_entities)} 个实体")

        # 6. 保存图谱
        saved_entities = self._save_entities(deduplicated_entities)
        saved_relations = self._save_relations(relations, saved_entities)
        saved_events = self._save_events(events)

        # 7. 更新统计
        self._update_graph_statistics(saved_entities, saved_relations)

        return {
            "success": True,
            "package_id": package_id,
            "entities": len(saved_entities),
            "relations": len(saved_relations),
            "events": len(saved_events),
            "entity_types": self._get_entity_type_distribution(saved_entities)
        }

    async def _extract_entities_from_sbpack(
        self,
        knowledge_items: List[KnowledgeItem],
        skill_items: List[SkillItem],
        package_id: int
    ) -> List[Dict[str, Any]]:
        """从SBPACK提取实体"""
        entities = []

        # 从知识点提取概念实体
        for item in knowledge_items:
            # 标题作为主要实体
            entity = {
                "name": item.title,
                "entity_type": self._map_knowledge_type_to_entity_type(item.knowledge_type),
                "description": item.statement,
                "attributes": {
                    "knowledge_type": item.knowledge_type,
                    "scope": item.scope,
                    "why_matters": item.why_matters
                },
                "source_documents": [{
                    "package_id": package_id,
                    "knowledge_id": item.knowledge_id,
                    "type": "knowledge"
                }],
                "extraction_method": "sbpack_structured"
            }
            entities.append(entity)

            # 从内容中提取提及的其他实体
            if self.llm and self.llm.enabled:
                mentioned_entities = await self._extract_entities_with_llm(
                    item.explanation,
                    package_id
                )
                entities.extend(mentioned_entities)

        # 从技能提取技能实体
        for item in skill_items:
            entity = {
                "name": item.name,
                "entity_type": "SKILL",
                "description": item.description,
                "attributes": {
                    "difficulty": item.difficulty if hasattr(item, 'difficulty') else None,
                    "rationale": item.rationale,
                    "cangjie_version": item.cangjie_version
                },
                "source_documents": [{
                    "package_id": package_id,
                    "skill_id": item.skill_id,
                    "type": "skill"
                }],
                "extraction_method": "sbpack_structured"
            }
            entities.append(entity)

        return entities

    def _map_knowledge_type_to_entity_type(self, knowledge_type: str) -> str:
        """将知识类型映射到实体类型"""
        mapping = {
            "concept": "CONCEPT",
            "claim": "CONCEPT",
            "principle": "CONCEPT",
            "mechanism": "CONCEPT",
            "reportedFact": "EVENT",
            "argument": "CONCEPT",
            "boundary": "CONCEPT",
            "counterexample": "EVENT"
        }
        return mapping.get(knowledge_type, "CONCEPT")

    async def _extract_entities_with_llm(
        self,
        text: str,
        package_id: int
    ) -> List[Dict[str, Any]]:
        """使用LLM提取文本中的实体"""
        if not self.llm or not self.llm.enabled:
            return []

        prompt = f"""
        从以下文本中提取命名实体。返回JSON格式。

        文本：
        {text[:1000]}

        提取以下类型的实体：
        - PERSON（人物）
        - ORGANIZATION（组织）
        - CONCEPT（概念）
        - LOCATION（地点）
        - TECHNOLOGY（技术）
        - PRODUCT（产品）

        返回格式：
        {{
            "entities": [
                {{"name": "实体名称", "type": "PERSON", "description": "简短描述"}},
                ...
            ]
        }}
        """

        try:
            response = await self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的实体提取专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            extracted = []

            for entity_data in result.get("entities", []):
                extracted.append({
                    "name": entity_data["name"],
                    "entity_type": entity_data["type"],
                    "description": entity_data.get("description", ""),
                    "attributes": {},
                    "source_documents": [{"package_id": package_id, "type": "llm_extracted"}],
                    "extraction_method": "llm"
                })

            return extracted

        except Exception as e:
            logger.error(f"LLM实体提取失败: {str(e)}")
            return []

    async def _extract_relations_from_sbpack(
        self,
        entities: List[Dict[str, Any]],
        knowledge_items: List[KnowledgeItem],
        skill_items: List[SkillItem],
        package_id: int
    ) -> List[Dict[str, Any]]:
        """从SBPACK提取关系"""
        relations = []

        # 创建实体名称到实体的映射
        entity_map = {e["name"]: e for e in entities}

        # 从技能的前置关系提取
        for skill in skill_items:
            if hasattr(skill, 'prerequisites') and skill.prerequisites:
                for prereq_id in skill.prerequisites:
                    # 查找前置技能
                    prereq_skill = next(
                        (s for s in skill_items if s.skill_id == prereq_id),
                        None
                    )
                    if prereq_skill:
                        relation = {
                            "source_name": prereq_skill.name,
                            "target_name": skill.name,
                            "relation_type": "PREREQUISITE",
                            "description": f"{prereq_skill.name} 是 {skill.name} 的前置技能",
                            "properties": {"strength": "required"},
                            "source_documents": [{
                                "package_id": package_id,
                                "skill_id": skill.skill_id
                            }],
                            "extraction_method": "sbpack_structured"
                        }
                        relations.append(relation)

        # 从知识点内容提取关系
        if self.llm and self.llm.enabled:
            for item in knowledge_items[:10]:  # 限制数量避免过多LLM调用
                extracted_relations = await self._extract_relations_with_llm(
                    item.explanation,
                    list(entity_map.keys()),
                    package_id
                )
                relations.extend(extracted_relations)

        return relations

    async def _extract_relations_with_llm(
        self,
        text: str,
        entity_names: List[str],
        package_id: int
    ) -> List[Dict[str, Any]]:
        """使用LLM提取关系"""
        if not self.llm or not self.llm.enabled:
            return []

        # 限制实体列表大小
        entity_sample = entity_names[:50]

        prompt = f"""
        从以下文本中提取实体间的关系。

        文本：
        {text[:800]}

        已知实体：
        {', '.join(entity_sample)}

        提取关系类型包括：
        - WORKS_FOR（工作于）
        - FOUNDED（创立）
        - INVENTED（发明）
        - CAUSES（导致）
        - ENABLES（使能）
        - RELATED_TO（相关）

        返回JSON格式：
        {{
            "relations": [
                {{"source": "实体A", "target": "实体B", "type": "WORKS_FOR", "description": "描述"}},
                ...
            ]
        }}
        """

        try:
            response = await self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": "你是一个关系提取专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            extracted = []

            for rel_data in result.get("relations", []):
                extracted.append({
                    "source_name": rel_data["source"],
                    "target_name": rel_data["target"],
                    "relation_type": rel_data["type"],
                    "description": rel_data.get("description", ""),
                    "properties": {},
                    "source_documents": [{"package_id": package_id}],
                    "extraction_method": "llm"
                })

            return extracted

        except Exception as e:
            logger.error(f"LLM关系提取失败: {str(e)}")
            return []

    async def _extract_temporal_events(
        self,
        knowledge_items: List[KnowledgeItem],
        skill_items: List[SkillItem],
        package_id: int
    ) -> List[Dict[str, Any]]:
        """提取时序事件"""
        events = []

        # 创建包的事件
        events.append({
            "event_type": "PACKAGE_CREATED",
            "description": f"SBPACK包创建",
            "timestamp": datetime.utcnow(),
            "entities": [],
            "event_data": {
                "package_id": package_id,
                "knowledge_count": len(knowledge_items),
                "skill_count": len(skill_items)
            }
        })

        # 从知识点中提取事件（reportedFact类型）
        for item in knowledge_items:
            if item.knowledge_type == "reportedFact":
                events.append({
                    "event_type": "FACT_REPORTED",
                    "description": item.statement[:200],
                    "timestamp": item.created_at,
                    "entities": [],
                    "event_data": {
                        "knowledge_id": item.knowledge_id,
                        "statement": item.statement
                    }
                })

        return events

    async def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """实体去重和消歧"""
        # 简单的名称去重
        seen_names = set()
        deduplicated = []

        for entity in entities:
            name = entity["name"].lower().strip()
            if name not in seen_names:
                seen_names.add(name)
                deduplicated.append(entity)
            else:
                # 合并属性和来源
                existing = next(e for e in deduplicated if e["name"].lower().strip() == name)
                existing["observation_count"] = existing.get("observation_count", 1) + 1
                if "source_documents" in entity:
                    existing["source_documents"].extend(entity["source_documents"])

        return deduplicated

    def _save_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Entity]:
        """保存实体到数据库"""
        saved = {}

        for entity_data in entities:
            entity = Entity(
                name=entity_data["name"],
                entity_type=entity_data["entity_type"],
                description=entity_data.get("description", ""),
                attributes=entity_data.get("attributes", {}),
                source_documents=entity_data.get("source_documents", []),
                extraction_method=entity_data.get("extraction_method", "unknown"),
                observation_count=entity_data.get("observation_count", 1)
            )
            self.db.add(entity)
            saved[entity_data["name"]] = entity

        self.db.commit()
        return saved

    def _save_relations(
        self,
        relations: List[Dict[str, Any]],
        entity_map: Dict[str, Entity]
    ) -> List[Relation]:
        """保存关系到数据库"""
        saved = []

        for rel_data in relations:
            source_entity = entity_map.get(rel_data["source_name"])
            target_entity = entity_map.get(rel_data["target_name"])

            if source_entity and target_entity:
                relation = Relation(
                    source_id=source_entity.id,
                    target_id=target_entity.id,
                    relation_type=rel_data["relation_type"],
                    description=rel_data.get("description", ""),
                    properties=rel_data.get("properties", {}),
                    source_documents=rel_data.get("source_documents", []),
                    extraction_method=rel_data.get("extraction_method", "unknown")
                )
                self.db.add(relation)
                saved.append(relation)

        self.db.commit()
        return saved

    def _save_events(self, events: List[Dict[str, Any]]) -> List[TemporalEvent]:
        """保存事件到数据库"""
        saved = []

        for event_data in events:
            event = TemporalEvent(
                event_type=event_data["event_type"],
                description=event_data["description"],
                timestamp=event_data["timestamp"],
                entities=event_data.get("entities", []),
                event_data=event_data.get("event_data", {})
            )
            self.db.add(event)
            saved.append(event)

        self.db.commit()
        return saved

    def _update_graph_statistics(self, entities: Dict[str, Entity], relations: List[Relation]):
        """更新图谱统计信息"""
        # 更新实体的关系计数
        for entity in entities.values():
            out_count = len([r for r in relations if r.source_id == entity.id])
            in_count = len([r for r in relations if r.target_id == entity.id])
            entity.relation_count = out_count + in_count

        self.db.commit()

    def _get_entity_type_distribution(self, entities: Dict[str, Entity]) -> Dict[str, int]:
        """获取实体类型分布"""
        distribution = {}
        for entity in entities.values():
            entity_type = entity.entity_type
            distribution[entity_type] = distribution.get(entity_type, 0) + 1
        return distribution
