"""
蒸馏引擎 - Distillation Engine
从结构化数据中提炼可复用、可溯源、可调用的知识单元
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from collections import Counter

from app.models.distillation import DistilledUnit, DistilledUnitRelation

logger = logging.getLogger(__name__)


class DistillationEngine:
    """蒸馏引擎 - 6类知识单元的提取"""

    def __init__(self, db: Session):
        self.db = db

    def distill_project(self, project_id: int) -> Dict[str, Any]:
        """
        对项目进行完整蒸馏

        Args:
            project_id: 项目ID

        Returns:
            蒸馏结果统计
        """
        logger.info(f"开始蒸馏项目 {project_id}")

        # 1. 加载结构化数据
        structured_data = self._load_structured_data(project_id)

        if not structured_data:
            logger.warning(f"项目 {project_id} 没有结构化数据")
            return {"error": "No structured data found"}

        # 2. 提取6类蒸馏产物
        results = {
            "insights": self._extract_insights(project_id, structured_data),
            "quotes": self._extract_quotes(project_id, structured_data),
            "models": self._extract_models(project_id, structured_data),
            "cases": self._extract_cases(project_id, structured_data),
            "actions": self._extract_actions(project_id, structured_data),
            "methods": self._extract_methods(project_id, structured_data),
        }

        # 3. 统计结果
        total_units = sum(len(units) for units in results.values())

        logger.info(f"项目 {project_id} 蒸馏完成: {total_units} 个知识单元")

        return {
            "project_id": project_id,
            "total_units": total_units,
            "breakdown": {k: len(v) for k, v in results.items()},
            "timestamp": datetime.utcnow().isoformat()
        }

    def _load_structured_data(self, project_id: int) -> Dict[str, Any]:
        """加载项目的结构化数据"""
        from app.models.document_chunk import DocumentChunk
        from app.models.entity import Entity, EntityRelation, DocumentEntity
        from app.models.timeline import TimelineEvent

        logger.info(f"开始加载项目 {project_id} 的结构化数据")

        # 1. 加载chunks
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.project_id == project_id
        ).all()

        # 2. 加载entities（通过document_entities关联）
        # 先获取项目的所有文档ID
        doc_ids = [chunk.document_id for chunk in chunks]
        doc_ids = list(set(doc_ids))  # 去重

        # 通过document_entities获取实体
        entity_ids = self.db.query(DocumentEntity.entity_id).filter(
            DocumentEntity.document_id.in_([str(d) for d in doc_ids])
        ).distinct().all()
        entity_ids = [e[0] for e in entity_ids]

        entities = self.db.query(Entity).filter(
            Entity.id.in_(entity_ids)
        ).all() if entity_ids else []

        # 3. 加载实体关系
        relations = self.db.query(EntityRelation).filter(
            EntityRelation.source_entity_id.in_(entity_ids)
        ).all() if entity_ids else []

        # 4. 加载时间线事件
        events = self.db.query(TimelineEvent).filter(
            TimelineEvent.project_id == project_id
        ).all()

        logger.info(f"加载完成: {len(chunks)} chunks, {len(entities)} entities, "
                   f"{len(relations)} relations, {len(events)} events")

        return {
            "chunks": chunks,
            "entities": entities,
            "relations": relations,
            "events": events,
            "doc_ids": doc_ids
        }

    # ==================== 1. 核心洞察提取 ====================
    def _extract_insights(self, project_id: int, data: Dict[str, Any]) -> List[DistilledUnit]:
        """
        提取核心洞察
        逻辑: 高频关键词 + 情绪峰值 + 事件密度高的区域
        """
        insights = []
        chunks = data.get("chunks", [])
        entities = data.get("entities", [])
        events = data.get("events", [])

        if not chunks:
            logger.warning(f"项目 {project_id} 没有chunks数据，无法提取洞察")
            return insights

        # 1. 分析高频实体和关键词
        entity_counter = Counter()
        keyword_counter = Counter()

        for chunk in chunks:
            # 统计实体
            if chunk.key_entities:
                key_entities = chunk.key_entities if isinstance(chunk.key_entities, list) else json.loads(chunk.key_entities or "[]")
                for entity in key_entities:
                    if isinstance(entity, dict):
                        entity_counter[entity.get("name", "")] += 1
                    else:
                        entity_counter[str(entity)] += 1

            # 统计领域标签
            if chunk.domain_tags:
                tags = chunk.domain_tags if isinstance(chunk.domain_tags, list) else json.loads(chunk.domain_tags or "[]")
                for tag in tags:
                    keyword_counter[tag] += 1

        # 2. 识别高频主题（出现在3个以上chunks中的实体/关键词）
        top_entities = [e for e, count in entity_counter.most_common(10) if count >= 3]
        top_keywords = [k for k, count in keyword_counter.most_common(10) if count >= 3]

        # 3. 基于高频主题生成洞察
        if top_entities:
            # 构建洞察：核心关注点
            source_chunk_ids = []
            relevant_chunks = []

            for chunk in chunks:
                chunk_entities = []
                if chunk.key_entities:
                    key_entities = chunk.key_entities if isinstance(chunk.key_entities, list) else json.loads(chunk.key_entities or "[]")
                    chunk_entities = [e.get("name", "") if isinstance(e, dict) else str(e) for e in key_entities]

                # 如果包含高频实体
                if any(entity in chunk_entities for entity in top_entities[:3]):
                    source_chunk_ids.append(chunk.id)
                    relevant_chunks.append(chunk)

            if source_chunk_ids:
                insight_content = f"研究聚焦于：{', '.join(top_entities[:5])}。"
                if top_keywords:
                    insight_content += f" 主要涉及领域：{', '.join(top_keywords[:3])}。"

                # 添加事件密度信息
                if events:
                    insight_content += f" 时间线中记录了{len(events)}个关键事件。"

                insight = DistilledUnit(
                    project_id=project_id,
                    unit_type="insight",
                    title=f"核心关注点：{top_entities[0]}",
                    content=insight_content,
                    source_chunks=json.dumps(source_chunk_ids[:20]),  # 最多20个来源
                    credibility=self._calculate_credibility(source_chunk_ids, len(top_entities)),
                    confidence=min(len(source_chunk_ids) / 10.0, 0.95),
                    extra_data=json.dumps({
                        "top_entities": top_entities[:5],
                        "top_keywords": top_keywords[:5],
                        "entity_frequency": {e: entity_counter[e] for e in top_entities[:5]},
                        "extraction_method": "frequency_analysis"
                    })
                )
                self.db.add(insight)
                insights.append(insight)

        # 4. 事件密度分析洞察
        if events and len(events) >= 3:
            # 按时间排序事件
            sorted_events = sorted(events, key=lambda e: e.date if e.date else datetime.min)

            # 识别事件密集期
            event_periods = []
            for i, event in enumerate(sorted_events):
                if event.date:
                    event_periods.append({
                        "date": event.date,
                        "title": event.title,
                        "id": event.id
                    })

            if len(event_periods) >= 3:
                insight_content = f"时间线显示{len(event_periods)}个关键事件。"
                if event_periods:
                    first_date = event_periods[0]["date"].strftime("%Y-%m-%d")
                    last_date = event_periods[-1]["date"].strftime("%Y-%m-%d")
                    insight_content += f" 时间跨度：{first_date} 至 {last_date}。"

                insight = DistilledUnit(
                    project_id=project_id,
                    unit_type="insight",
                    title="时间线关键节点",
                    content=insight_content,
                    source_chunks=json.dumps([]),  # 事件不关联chunks
                    credibility=min(len(events) / 10.0, 0.95),
                    confidence=0.9,
                    extra_data=json.dumps({
                        "event_count": len(events),
                        "time_span": f"{first_date} - {last_date}",
                        "event_ids": [e["id"] for e in event_periods[:10]],
                        "extraction_method": "event_density_analysis"
                    })
                )
                self.db.add(insight)
                insights.append(insight)

        self.db.commit()
        logger.info(f"提取了 {len(insights)} 个核心洞察")
        return insights

    # ==================== 2. 经典原话提取 ====================
    def _extract_quotes(self, project_id: int, data: Dict[str, Any]) -> List[DistilledUnit]:
        """
        提取经典原话
        逻辑: 包含核心实体 + 情绪强度高 + 有代表性表述
        """
        quotes = []
        chunks = data.get("chunks", [])
        entities = data.get("entities", [])

        if not chunks:
            return quotes

        # 1. 识别核心实体（高频实体）
        entity_counter = Counter()
        for chunk in chunks:
            if chunk.key_entities:
                key_entities = chunk.key_entities if isinstance(chunk.key_entities, list) else json.loads(chunk.key_entities or "[]")
                for entity in key_entities:
                    if isinstance(entity, dict):
                        entity_counter[entity.get("name", "")] += 1

        core_entities = [e for e, count in entity_counter.most_common(5) if count >= 2]

        if not core_entities:
            logger.info("没有发现核心实体，无法提取经典原话")
            return quotes

        # 2. 提取包含核心实体且有说话人的chunks（访谈记录）
        quote_candidates = []

        for chunk in chunks:
            # 优先提取有说话人的chunks（音频转写）
            if chunk.speaker:
                chunk_entities = []
                if chunk.key_entities:
                    key_entities = chunk.key_entities if isinstance(chunk.key_entities, list) else json.loads(chunk.key_entities or "[]")
                    chunk_entities = [e.get("name", "") if isinstance(e, dict) else str(e) for e in key_entities]

                # 检查是否包含核心实体
                matching_entities = [e for e in core_entities if e in chunk_entities]

                if matching_entities:
                    # 计算"情绪强度"：包含感叹号、问号、重复词等
                    emotion_score = 0
                    text = chunk.text or ""

                    if "！" in text or "!" in text:
                        emotion_score += 0.3
                    if "？" in text or "?" in text:
                        emotion_score += 0.2
                    if len(text) > 50 and len(text) < 200:  # 长度适中
                        emotion_score += 0.2
                    if any(word in text for word in ["非常", "特别", "真的", "确实", "绝对"]):
                        emotion_score += 0.3

                    quote_candidates.append({
                        "chunk": chunk,
                        "speaker": chunk.speaker,
                        "entities": matching_entities,
                        "emotion_score": min(emotion_score, 1.0),
                        "text_length": len(text)
                    })

        # 3. 按情绪强度排序，提取top quotes
        quote_candidates.sort(key=lambda x: x["emotion_score"], reverse=True)

        for candidate in quote_candidates[:5]:  # 最多提取5条经典原话
            chunk = candidate["chunk"]
            text = chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text

            quote = DistilledUnit(
                project_id=project_id,
                unit_type="quote",
                title=f"{candidate['speaker']}说：{text[:30]}...",
                content=text,
                source_chunks=json.dumps([chunk.id]),
                credibility=0.95,  # 原话可信度高
                confidence=candidate["emotion_score"],
                extra_data=json.dumps({
                    "speaker": candidate["speaker"],
                    "entities": candidate["entities"],
                    "timestamp_start": chunk.timestamp_start,
                    "timestamp_end": chunk.timestamp_end,
                    "emotion_score": candidate["emotion_score"],
                    "extraction_method": "entity_emotion_analysis"
                })
            )
            self.db.add(quote)
            quotes.append(quote)

        self.db.commit()
        logger.info(f"提取了 {len(quotes)} 条经典原话")
        return quotes

    # ==================== 3. 思维模型匹配 ====================
    def _extract_models(self, project_id: int, data: Dict[str, Any]) -> List[DistilledUnit]:
        """
        提取思维模型
        逻辑: 调用理论 Skill + 匹配已有实体关系
        """
        models = []
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        chunks = data.get("chunks", [])

        if not relations or len(relations) < 3:
            logger.info("实体关系数量不足，无法提取思维模型")
            return models

        # 1. 分析实体关系模式
        relation_types = Counter()
        for relation in relations:
            relation_types[relation.relation_type] += 1

        # 2. 识别常见的思维模型模式
        model_patterns = {
            "因果关系网络": ["导致", "影响", "引起", "造成", "产生"],
            "层级结构": ["属于", "包含", "下属", "管理", "领导"],
            "协作网络": ["合作", "协同", "配合", "参与", "共同"],
            "时间演化": ["之前", "之后", "发展为", "转变为", "演变"],
        }

        detected_models = []
        for model_name, keywords in model_patterns.items():
            matching_relations = [r for r in relations if any(kw in r.relation_type for kw in keywords)]
            if len(matching_relations) >= 2:
                detected_models.append({
                    "model_name": model_name,
                    "relations": matching_relations,
                    "count": len(matching_relations)
                })

        # 3. 为每个检测到的模型生成描述
        for detected in detected_models[:3]:  # 最多提取3个模型
            model_name = detected["model_name"]
            matching_relations = detected["relations"]

            # 构建模型描述
            relation_examples = []
            source_chunk_ids = []

            for rel in matching_relations[:5]:  # 最多5个关系示例
                # 获取实体名称
                source_entity = next((e for e in entities if e.id == rel.source_entity_id), None)
                target_entity = next((e for e in entities if e.id == rel.target_entity_id), None)

                if source_entity and target_entity:
                    relation_examples.append(
                        f"{source_entity.text} → {rel.relation_type} → {target_entity.text}"
                    )

                # 收集相关chunk
                if rel.source_documents:
                    docs = rel.source_documents if isinstance(rel.source_documents, list) else json.loads(rel.source_documents or "[]")
                    # 从文档ID映射到chunk ID（简化：使用前几个chunk）
                    relevant_chunks = [c.id for c in chunks if str(c.document_id) in [str(d) for d in docs]]
                    source_chunk_ids.extend(relevant_chunks[:3])

            content = f"发现{model_name}模式，共{len(matching_relations)}个关系。\n\n"
            content += "关系示例：\n" + "\n".join(relation_examples[:5])

            model = DistilledUnit(
                project_id=project_id,
                unit_type="model",
                title=f"思维模型：{model_name}",
                content=content,
                source_chunks=json.dumps(list(set(source_chunk_ids))[:20]),
                credibility=min(len(matching_relations) / 5.0, 0.9),
                confidence=0.75,
                extra_data=json.dumps({
                    "model_type": model_name,
                    "relation_count": len(matching_relations),
                    "relation_types": [r.relation_type for r in matching_relations[:10]],
                    "entity_count": len(set([r.source_entity_id for r in matching_relations] +
                                           [r.target_entity_id for r in matching_relations])),
                    "extraction_method": "relation_pattern_matching"
                })
            )
            self.db.add(model)
            models.append(model)

        self.db.commit()
        logger.info(f"提取了 {len(models)} 个思维模型")
        return models

    # ==================== 4. 案例与应用生成 ====================
    def _extract_cases(self, project_id: int, data: Dict[str, Any]) -> List[DistilledUnit]:
        """
        提取案例与应用
        逻辑: 匹配商业 Skill + 匹配可行性评分
        """
        cases = []
        chunks = data.get("chunks", [])
        events = data.get("events", [])
        entities = data.get("entities", [])

        if not chunks:
            return cases

        # 1. 识别具有案例特征的chunks
        case_indicators = {
            "成功案例": ["成功", "实现", "达到", "完成", "成果", "效果"],
            "失败案例": ["失败", "问题", "困难", "挑战", "教训", "失误"],
            "创新案例": ["创新", "首次", "突破", "改革", "变革", "探索"],
            "经验总结": ["经验", "总结", "启示", "收获", "体会", "感悟"]
        }

        case_candidates = []

        for chunk in chunks:
            text = chunk.text or ""

            # 检查是否包含案例指示词
            for case_type, keywords in case_indicators.items():
                if any(kw in text for kw in keywords):
                    # 计算案例质量分数
                    quality_score = 0

                    # 有具体实体（人、地点）
                    if chunk.key_entities:
                        quality_score += 0.3

                    # 有时间信息
                    if chunk.temporal_context or chunk.timestamp_start:
                        quality_score += 0.2

                    # 有空间信息
                    if chunk.spatial_context or chunk.page_number:
                        quality_score += 0.2

                    # 文本长度适中（100-500字）
                    if 100 <= len(text) <= 500:
                        quality_score += 0.3

                    case_candidates.append({
                        "chunk": chunk,
                        "case_type": case_type,
                        "quality_score": quality_score,
                        "text_length": len(text)
                    })
                    break  # 一个chunk只算一种类型

        # 2. 按质量分数排序
        case_candidates.sort(key=lambda x: x["quality_score"], reverse=True)

        # 3. 提取top cases
        for candidate in case_candidates[:5]:  # 最多5个案例
            chunk = candidate["chunk"]
            case_type = candidate["case_type"]

            # 提取摘要（前150字）
            summary = chunk.text[:150] + "..." if len(chunk.text) > 150 else chunk.text

            # 提取关联实体
            case_entities = []
            if chunk.key_entities:
                key_entities = chunk.key_entities if isinstance(chunk.key_entities, list) else json.loads(chunk.key_entities or "[]")
                case_entities = [e.get("name", "") if isinstance(e, dict) else str(e) for e in key_entities][:5]

            # 计算可行性评分（基于数据完整度）
            feasibility = candidate["quality_score"]

            content = f"【{case_type}】\n\n{summary}\n\n"
            if case_entities:
                content += f"涉及：{', '.join(case_entities)}"

            case = DistilledUnit(
                project_id=project_id,
                unit_type="case",
                title=f"{case_type}：{case_entities[0] if case_entities else '案例分析'}",
                content=content,
                source_chunks=json.dumps([chunk.id]),
                credibility=candidate["quality_score"],
                confidence=feasibility,
                extra_data=json.dumps({
                    "case_type": case_type,
                    "entities": case_entities,
                    "temporal_context": chunk.temporal_context,
                    "spatial_context": chunk.spatial_context,
                    "quality_score": candidate["quality_score"],
                    "extraction_method": "case_pattern_matching"
                })
            )
            self.db.add(case)
            cases.append(case)

        self.db.commit()
        logger.info(f"提取了 {len(cases)} 个案例")
        return cases

    # ==================== 5. 行动建议生成 ====================
    def _extract_actions(self, project_id: int, data: Dict[str, Any]) -> List[DistilledUnit]:
        """
        提取行动建议
        逻辑: 缺口分析 + 趋势分析 + 优先级排序
        """
        actions = []
        chunks = data.get("chunks", [])
        entities = data.get("entities", [])
        events = data.get("events", [])

        if not chunks:
            return actions

        # 1. 缺口分析：识别问题、需求、待办事项
        gap_keywords = {
            "问题缺口": ["问题", "不足", "缺陷", "短板", "弱点", "瓶颈"],
            "需求缺口": ["需要", "需求", "希望", "期待", "要求", "建议"],
            "待办事项": ["应该", "需要", "建议", "可以", "计划", "准备"]
        }

        action_candidates = []

        for chunk in chunks:
            text = chunk.text or ""

            for gap_type, keywords in gap_keywords.items():
                keyword_matches = [kw for kw in keywords if kw in text]
                if keyword_matches:
                    # 计算紧急度（基于关键词强度）
                    urgency = 0
                    if any(word in text for word in ["立即", "紧急", "马上", "尽快", "亟需"]):
                        urgency = 0.9
                    elif any(word in text for word in ["应该", "需要", "必须"]):
                        urgency = 0.7
                    else:
                        urgency = 0.5

                    # 提取可能的行动内容
                    action_text = text[:200] if len(text) <= 200 else text[:200] + "..."

                    action_candidates.append({
                        "chunk": chunk,
                        "gap_type": gap_type,
                        "urgency": urgency,
                        "keywords": keyword_matches,
                        "action_text": action_text
                    })
                    break

        # 2. 趋势分析：基于时间线事件
        if events and len(events) >= 2:
            sorted_events = sorted([e for e in events if e.date], key=lambda e: e.date)

            if len(sorted_events) >= 2:
                recent_events = sorted_events[-3:]  # 最近3个事件
                trend_content = "基于近期事件趋势，建议关注以下方向：\n"

                for event in recent_events:
                    trend_content += f"- {event.title}\n"

                action = DistilledUnit(
                    project_id=project_id,
                    unit_type="action",
                    title="趋势跟进建议",
                    content=trend_content,
                    source_chunks=json.dumps([]),
                    credibility=0.75,
                    confidence=0.8,
                    extra_data=json.dumps({
                        "action_type": "trend_follow",
                        "event_ids": [e.id for e in recent_events],
                        "urgency": 0.6,
                        "extraction_method": "trend_analysis"
                    })
                )
                self.db.add(action)
                actions.append(action)

        # 3. 优先级排序：按紧急度排序
        action_candidates.sort(key=lambda x: x["urgency"], reverse=True)

        # 4. 生成行动建议
        for candidate in action_candidates[:5]:  # 最多5个建议
            chunk = candidate["chunk"]

            # 构建建议内容
            content = f"【{candidate['gap_type']}】\n\n{candidate['action_text']}\n\n"
            content += f"紧急度：{'高' if candidate['urgency'] >= 0.8 else '中' if candidate['urgency'] >= 0.6 else '低'}"

            action = DistilledUnit(
                project_id=project_id,
                unit_type="action",
                title=f"行动建议：{candidate['gap_type']}",
                content=content,
                source_chunks=json.dumps([chunk.id]),
                credibility=0.7,
                confidence=candidate["urgency"],
                extra_data=json.dumps({
                    "action_type": candidate["gap_type"],
                    "urgency": candidate["urgency"],
                    "keywords": candidate["keywords"],
                    "extraction_method": "gap_analysis"
                })
            )
            self.db.add(action)
            actions.append(action)

        self.db.commit()
        logger.info(f"提取了 {len(actions)} 个行动建议")
        return actions

    # ==================== 6. 方法论沉淀 ====================
    def _extract_methods(self, project_id: int, data: Dict[str, Any]) -> List[DistilledUnit]:
        """
        提取方法论沉淀
        逻辑: 记录本次使用的分析框架和参数
        """
        methods = []
        chunks = data.get("chunks", [])
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        events = data.get("events", [])

        # 1. 记录数据处理方法论
        data_stats = {
            "total_chunks": len(chunks),
            "total_entities": len(entities),
            "total_relations": len(relations),
            "total_events": len(events),
        }

        # 2. 分析使用的分析维度
        analysis_dimensions = []

        # 实体分析
        if entities:
            entity_types = Counter([e.type for e in entities])
            analysis_dimensions.append({
                "dimension": "实体识别",
                "count": len(entities),
                "types": dict(entity_types.most_common(5))
            })

        # 关系分析
        if relations:
            relation_types = Counter([r.relation_type for r in relations])
            analysis_dimensions.append({
                "dimension": "关系抽取",
                "count": len(relations),
                "types": dict(relation_types.most_common(5))
            })

        # 时间线分析
        if events:
            analysis_dimensions.append({
                "dimension": "时间线构建",
                "count": len(events),
                "time_span": self._calculate_time_span(events)
            })

        # 语义增强分析
        enhanced_chunks = [c for c in chunks if c.key_entities or c.domain_tags]
        if enhanced_chunks:
            analysis_dimensions.append({
                "dimension": "语义增强",
                "enhanced_count": len(enhanced_chunks),
                "coverage": f"{len(enhanced_chunks)/len(chunks)*100:.1f}%"
            })

        # 3. 生成方法论文档
        if analysis_dimensions:
            content = "本次研究使用的分析方法论：\n\n"

            for dim in analysis_dimensions:
                content += f"**{dim['dimension']}**\n"
                content += f"- 处理数量：{dim.get('count', dim.get('enhanced_count', 0))}\n"
                if 'types' in dim:
                    content += f"- 主要类型：{', '.join([f'{k}({v})' for k, v in list(dim['types'].items())[:3]])}\n"
                if 'coverage' in dim:
                    content += f"- 覆盖率：{dim['coverage']}\n"
                if 'time_span' in dim:
                    content += f"- 时间跨度：{dim['time_span']}\n"
                content += "\n"

            # 添加数据质量评估
            content += "**数据质量评估**\n"
            content += f"- 文本块：{data_stats['total_chunks']} 个\n"
            content += f"- 实体：{data_stats['total_entities']} 个\n"
            content += f"- 关系：{data_stats['total_relations']} 个\n"
            content += f"- 事件：{data_stats['total_events']} 个\n"

            method = DistilledUnit(
                project_id=project_id,
                unit_type="method",
                title="研究方法论",
                content=content,
                source_chunks=json.dumps([]),
                credibility=0.95,  # 方法论基于实际数据，可信度高
                confidence=0.9,
                extra_data=json.dumps({
                    "data_stats": data_stats,
                    "analysis_dimensions": analysis_dimensions,
                    "extraction_timestamp": datetime.utcnow().isoformat(),
                    "extraction_method": "methodology_recording"
                })
            )
            self.db.add(method)
            methods.append(method)

        # 4. 记录蒸馏参数配置
        distillation_config = {
            "insight_threshold": {"min_entity_frequency": 3, "min_source_chunks": 5},
            "quote_threshold": {"min_emotion_score": 0.3, "max_quotes": 5},
            "model_threshold": {"min_relations": 2, "max_models": 3},
            "case_threshold": {"min_quality_score": 0.5, "max_cases": 5},
            "action_threshold": {"min_urgency": 0.5, "max_actions": 5}
        }

        config_content = "蒸馏引擎配置参数：\n\n"
        for key, value in distillation_config.items():
            config_content += f"**{key}**\n"
            for param, val in value.items():
                config_content += f"- {param}: {val}\n"
            config_content += "\n"

        config_method = DistilledUnit(
            project_id=project_id,
            unit_type="method",
            title="蒸馏参数配置",
            content=config_content,
            source_chunks=json.dumps([]),
            credibility=1.0,
            confidence=1.0,
            extra_data=json.dumps({
                "config": distillation_config,
                "extraction_method": "configuration_recording"
            })
        )
        self.db.add(config_method)
        methods.append(config_method)

        self.db.commit()
        logger.info(f"提取了 {len(methods)} 个方法论")
        return methods

    def _calculate_time_span(self, events: list) -> str:
        """计算事件时间跨度"""
        dated_events = [e for e in events if e.date]
        if not dated_events:
            return "未知"

        dates = sorted([e.date for e in dated_events])
        if len(dates) < 2:
            return dates[0].strftime("%Y-%m-%d")

        start_date = dates[0].strftime("%Y-%m-%d")
        end_date = dates[-1].strftime("%Y-%m-%d")
        return f"{start_date} 至 {end_date}"

    # ==================== 辅助方法 ====================
    def _calculate_credibility(self, sources: List[int], evidence_count: int) -> float:
        """计算可信度评分"""
        # 基于来源数量和证据数量计算可信度
        source_score = min(len(sources) / 5.0, 1.0)  # 5个来源满分
        evidence_score = min(evidence_count / 10.0, 1.0)  # 10个证据满分
        return (source_score * 0.6 + evidence_score * 0.4)

    def _calculate_confidence(self, strength: float, consistency: float) -> float:
        """计算蒸馏置信度"""
        # 基于信号强度和一致性计算置信度
        return (strength * 0.7 + consistency * 0.3)

    def get_distilled_units(
        self,
        project_id: int,
        unit_type: Optional[str] = None
    ) -> List[DistilledUnit]:
        """
        获取项目的蒸馏产物

        Args:
            project_id: 项目ID
            unit_type: 产物类型筛选（可选）

        Returns:
            蒸馏产物列表
        """
        query = self.db.query(DistilledUnit).filter(
            DistilledUnit.project_id == project_id
        )

        if unit_type:
            query = query.filter(DistilledUnit.unit_type == unit_type)

        return query.order_by(DistilledUnit.credibility.desc()).all()

    def get_unit_sources(self, unit_id: int) -> List[Dict[str, Any]]:
        """
        获取蒸馏产物的来源

        Args:
            unit_id: 蒸馏产物ID

        Returns:
            来源信息列表
        """
        from app.models.document_chunk import DocumentChunk
        from app.models.document import Document

        unit = self.db.query(DistilledUnit).filter(
            DistilledUnit.id == unit_id
        ).first()

        if not unit or not unit.source_chunks:
            return []

        try:
            chunk_ids = json.loads(unit.source_chunks)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"无法解析 unit {unit_id} 的 source_chunks")
            return []

        if not chunk_ids:
            return []

        # 查询chunk详情
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.id.in_(chunk_ids)
        ).all()

        sources = []
        for chunk in chunks:
            # 获取文档信息
            document = self.db.query(Document).filter(
                Document.id == chunk.document_id
            ).first()

            source_info = {
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                "full_content": chunk.text,
                "document_id": chunk.document_id,
                "document_name": document.filename if document else "未知文档",
                "page_number": chunk.page_number,
                "speaker": chunk.speaker,
                "timestamp_start": chunk.timestamp_start,
                "timestamp_end": chunk.timestamp_end,
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None
            }
            sources.append(source_info)

        return sources
