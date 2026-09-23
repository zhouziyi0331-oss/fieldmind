"""
蒸馏功能 - 核心洞察提取 Skill
从结构化数据中识别高频主题和关键洞察
"""

SKILL_NAME = "distill_insights"
SKILL_VERSION = "1.0.0"
SKILL_DESCRIPTION = "提取核心洞察：分析高频实体、关键词和事件密度"

PROMPT_TEMPLATE = """
你是一个专业的数据分析专家，擅长从结构化数据中提取核心洞察。

# 任务
分析以下数据，识别出最核心的洞察和主题：

## 输入数据
{data_summary}

## 分析维度
1. **高频实体分析**
   - 识别出现频率最高的人物、组织、地点、概念
   - 关注出现≥3次的核心实体

2. **领域标签统计**
   - 统计各类domain_tags的分布
   - 识别主要研究领域和话题

3. **事件密度分析**
   - 分析时间线上的事件分布
   - 识别关键时间节点和密集期

4. **关联性分析**
   - 分析实体之间的共现关系
   - 识别核心关注网络

## 输出要求
请以JSON格式输出1-3个核心洞察，每个洞察包含：
- title: 洞察标题（简洁，10-20字）
- content: 洞察内容（详细描述，50-200字）
- evidence: 支持证据（实体列表、频次等）
- confidence: 置信度（0-1之间）

## 示例输出
{{
  "insights": [
    {{
      "title": "核心关注点：乡村振兴与土地改革",
      "content": "研究聚焦于乡村振兴战略下的土地改革实践。李明、王教授等关键人物在访谈中反复提及土地流转、农民收入、集体经济等核心议题。数据显示这些主题在文档中出现频率最高，构成了研究的核心关注网络。",
      "evidence": {{
        "top_entities": ["李明", "王教授", "土地改革"],
        "frequency": {{"李明": 15, "土地改革": 12}},
        "related_tags": ["乡村振兴", "土地流转", "农民收入"]
      }},
      "confidence": 0.92
    }}
  ]
}}

请基于提供的数据进行分析并输出。
"""

def extract_insights(chunks, entities, events, relations):
    """
    使用规则+提示词混合方式提取洞察

    Args:
        chunks: 文档块列表
        entities: 实体列表
        events: 事件列表
        relations: 关系列表

    Returns:
        洞察列表
    """
    from collections import Counter
    import json

    # 1. 统计高频实体
    entity_counter = Counter()
    for chunk in chunks:
        if chunk.key_entities:
            try:
                key_entities = json.loads(chunk.key_entities) if isinstance(chunk.key_entities, str) else chunk.key_entities
                for entity in key_entities:
                    name = entity.get("name") if isinstance(entity, dict) else str(entity)
                    if name:
                        entity_counter[name] += 1
            except:
                pass

    # 2. 统计领域标签
    tag_counter = Counter()
    for chunk in chunks:
        if chunk.domain_tags:
            try:
                tags = json.loads(chunk.domain_tags) if isinstance(chunk.domain_tags, str) else chunk.domain_tags
                tag_counter.update(tags)
            except:
                pass

    # 3. 构建数据摘要
    data_summary = {
        "total_chunks": len(chunks),
        "total_entities": len(entities),
        "total_events": len(events),
        "top_entities": dict(entity_counter.most_common(10)),
        "top_tags": dict(tag_counter.most_common(10)),
        "event_timeline": [
            {"title": e.title, "date": e.date.isoformat() if e.date else None}
            for e in sorted(events, key=lambda x: x.date if x.date else "")[:5]
        ] if events else []
    }

    # 4. 如果配置了LLM，使用提示词增强
    # 否则使用规则提取

    return data_summary


# Skill元数据
SKILL_METADATA = {
    "name": SKILL_NAME,
    "version": SKILL_VERSION,
    "description": SKILL_DESCRIPTION,
    "category": "distillation",
    "input_fields": ["chunks", "entities", "events", "relations"],
    "output_fields": ["insights"],
    "requires_llm": False,  # 可选，不强制
    "recommended_model": "claude-sonnet-3-5",
    "estimated_tokens": 2000,
}
