"""
提取洞察 Skill - 基于实体和事件频率分析
"""
from typing import Dict, Any, List
from collections import Counter


class ExtractInsightsSkill:
    """
    洞察提取Skill

    方法论：Entity + Event Density Analysis
    - 高频实体分析：识别关键主题
    - 事件密度分析：识别重要时刻
    - 趋势识别：识别模式和变化
    """

    METADATA = {
        "name": "extract_insights",
        "version": "1.0.0",
        "type": "frequency_analysis",
        "output_type": "洞察"
    }

    def __init__(self, db_session):
        self.db = db_session

    def extract(self, chunks: List[Dict[str, Any]],
                entities: List[Dict[str, Any]],
                relations: List[Dict[str, Any]],
                events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行洞察提取

        参数:
            chunks: 文本块列表
            entities: 实体列表
            relations: 关系列表
            events: 事件列表

        返回:
            洞察列表，每个包含：
            - content: 洞察内容
            - category: 类别（高频主题/事件密度/趋势）
            - evidence: 证据数据
            - credibility: 可信度
            - confidence: 置信度
            - source_chunks: 来源块ID列表
        """
        insights = []

        # 1. 高频实体分析
        entity_insights = self._analyze_high_frequency_entities(entities, chunks)
        insights.extend(entity_insights)

        # 2. 事件密度分析
        event_insights = self._analyze_event_density(events, chunks)
        insights.extend(event_insights)

        # 3. 趋势识别
        trend_insights = self._analyze_trends(entities, events, chunks)
        insights.extend(trend_insights)

        return insights

    def _analyze_high_frequency_entities(self, entities: List[Dict[str, Any]],
                                        chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析高频实体"""
        insights = []

        # 统计实体类型和名称频率
        entity_types = Counter()
        entity_names = Counter()
        entity_chunk_map = {}

        for entity in entities:
            etype = entity.get("entity_type", "未知")
            ename = entity.get("entity_name", "")
            chunk_id = entity.get("chunk_id")

            entity_types[etype] += 1
            entity_names[ename] += 1

            if ename not in entity_chunk_map:
                entity_chunk_map[ename] = set()
            if chunk_id:
                entity_chunk_map[ename].add(chunk_id)

        # 生成高频实体洞察（出现5次以上）
        for entity_name, count in entity_names.most_common(10):
            if count >= 5:
                source_chunks = list(entity_chunk_map.get(entity_name, set()))

                insight = {
                    "content": f"高频主题: '{entity_name}' 在文档中出现{count}次，是核心讨论焦点",
                    "category": "高频主题",
                    "evidence": {
                        "entity_name": entity_name,
                        "frequency": count,
                        "chunk_count": len(source_chunks)
                    },
                    "credibility": min(0.7 + (count / 100), 0.95),  # 频率越高越可信
                    "confidence": min(0.6 + (len(source_chunks) / 50), 0.9),
                    "source_chunks": source_chunks[:20]  # 最多20个来源
                }
                insights.append(insight)

        return insights

    def _analyze_event_density(self, events: List[Dict[str, Any]],
                               chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析事件密度"""
        insights = []

        # 按chunk统计事件数量
        chunk_event_count = Counter()
        chunk_event_map = {}

        for event in events:
            chunk_id = event.get("chunk_id")
            if chunk_id:
                chunk_event_count[chunk_id] += 1
                if chunk_id not in chunk_event_map:
                    chunk_event_map[chunk_id] = []
                chunk_event_map[chunk_id].append(event)

        # 找到事件密集的chunk（至少3个事件）
        for chunk_id, count in chunk_event_count.most_common(5):
            if count >= 3:
                chunk_events = chunk_event_map[chunk_id]
                event_types = [e.get("event_type", "未知") for e in chunk_events]

                insight = {
                    "content": f"事件密集区域: chunk #{chunk_id} 包含{count}个事件，涉及{len(set(event_types))}种事件类型",
                    "category": "事件密度",
                    "evidence": {
                        "chunk_id": chunk_id,
                        "event_count": count,
                        "event_types": list(set(event_types))
                    },
                    "credibility": min(0.65 + (count / 20), 0.9),
                    "confidence": 0.75,
                    "source_chunks": [chunk_id]
                }
                insights.append(insight)

        return insights

    def _analyze_trends(self, entities: List[Dict[str, Any]],
                       events: List[Dict[str, Any]],
                       chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析趋势"""
        insights = []

        # 简单趋势：实体类型分布
        entity_types = Counter(e.get("entity_type", "未知") for e in entities)

        if len(entity_types) > 0:
            dominant_type = entity_types.most_common(1)[0]
            type_name, type_count = dominant_type
            total = sum(entity_types.values())
            percentage = (type_count / total * 100) if total > 0 else 0

            if percentage > 40:  # 超过40%占比
                insight = {
                    "content": f"主导类型: '{type_name}' 类型的实体占比{percentage:.1f}%，是文档的主要关注点",
                    "category": "趋势识别",
                    "evidence": {
                        "dominant_type": type_name,
                        "count": type_count,
                        "percentage": percentage
                    },
                    "credibility": 0.8,
                    "confidence": 0.7,
                    "source_chunks": []  # 趋势不绑定特定chunk
                }
                insights.append(insight)

        return insights
