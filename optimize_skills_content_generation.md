# Skills 内容生成质量优化方案

## 🎯 目标
将生成字数从 169-458 字/章提升到 1000+ 字/章，并提高内容深度和可读性。

## 📊 当前问题诊断

### ✅ 数据已成功提取
- ✓ 66个文档块（chunks）
- ✓ 60个关键词（布依族、全景、深度、仪式等）
- ✓ 8个时间线事件（1985-2026）
- ✓ 66个结构化insights（主题+人物+地点）
- ✓ 11个关键词社区

### ❌ 内容生成质量低
**根本原因：Skills 没有充分利用已提取的数据**

当前生成逻辑：
```python
# field_investigation_skill.py L218-233
content += f"本项目共收集文档 {stats.get('total_chunks', 0)} 段"
content += f"识别出 {len(items)} 个{direction}相关的文化元素"
for item in items[:10]:
    content += f"- **{item.raw_content}**：{item.story_line}\n"
```

问题：
1. **只用关键词列表** - 没有使用 chunks 的实际文本内容
2. **模板化占位符** - "故事线索"、"情感触点"都是空的占位符文本
3. **没有引用原文** - citation_pool 有66条，但只在末尾象征性引用1条
4. **缺少深度分析** - 没有利用 structured_insights 中的主题、人物、地点

## 🔧 优化方案

### 方案1：增强 Skills 内部逻辑（推荐）

**目标：让 Skills 真正使用提取的数据**

#### 1.1 改进 `_write_resource_section`
```python
def _write_resource_section(self, excavations, material):
    content = "### 文化遗产资源概览\n\n"
    
    # ✅ 使用实际数据
    chunks = material.get("citation_pool", [])
    keywords = material.get("main_keywords", [])
    timeline = material.get("timeline", [])
    
    # 生成详细的资源分析（800-1000字）
    content += self._analyze_cultural_resources(chunks, keywords, timeline)
    content += self._categorize_by_heritage_type(chunks)
    content += self._highlight_unique_features(keywords, chunks)
    
    return content

def _analyze_cultural_resources(self, chunks, keywords, timeline):
    """从chunks中提取实际内容，生成详细分析"""
    # 找到包含关键词最多的chunks
    relevant_chunks = self._find_relevant_chunks(chunks, keywords[:10])
    
    content = "#### 资源分布与特征\n\n"
    content += "基于田野调查资料，本项目的文化遗产资源呈现以下特点：\n\n"
    
    # 为每个主关键词生成一段200-300字的分析
    for kw in keywords[:3]:  # 取前3个关键词
        kw_text = kw.get('keyword', '')
        # 找到包含该关键词的chunks
        related_chunks = [c for c in chunks if kw_text in c.get('content', '')]
        
        if related_chunks:
            # 提取该关键词的上下文（实际内容）
            context = related_chunks[0].get('content', '')[:200]
            content += f"**{kw_text}**：{context}...\n\n"
            content += f"（来源：{related_chunks[0].get('citation_format', '')}）\n\n"
    
    return content
```

#### 1.2 使用 structured_insights 生成深度内容
```python
def _write_thematic_analysis(self, material):
    """利用structured_insights生成主题分析"""
    # 从数据库查询structured_insights
    insights = self._get_structured_insights(material['project_id'])
    
    # 按主题分组
    by_topic = {}
    for insight in insights:
        topics = insight['topics'].split(',')
        for topic in topics:
            if topic not in by_topic:
                by_topic[topic] = []
            by_topic[topic].append(insight)
    
    content = "### 主题深度分析\n\n"
    
    # 为每个主题生成300-500字的分析
    for topic, items in by_topic.items():
        content += f"#### {topic}\n\n"
        content += f"在{len(items)}段田野资料中，我们发现关于{topic}的以下核心内容：\n\n"
        
        # 提取人物、地点信息
        persons = set()
        locations = set()
        for item in items:
            if item['persons']:
                persons.update(item['persons'].split(','))
            if item['locations']:
                locations.update(item['locations'].split(','))
        
        content += f"涉及人物：{', '.join(list(persons)[:10])}\n\n"
        content += f"涉及地点：{', '.join(list(locations)[:10])}\n\n"
        
        # 引用原文
        for item in items[:2]:
            content += f"{item['original_text'][:150]}...\n\n"
        
        content += "\n"
    
    return content
```

#### 1.3 使用 timeline 生成历史脉络
```python
def _write_historical_timeline(self, material):
    """使用timeline_events生成历史脉络分析"""
    timeline = material.get("timeline", [])
    
    if not timeline:
        return ""
    
    content = "### 历史发展脉络\n\n"
    content += f"基于{len(timeline)}个时间节点的梳理，本项目呈现以下历史发展轨迹：\n\n"
    
    # 按时间顺序叙述
    for i, event in enumerate(timeline):
        timestamp = event.get('timestamp', '')
        event_content = event.get('content', '')
        
        if timestamp and event_content:
            # 每个事件生成100-200字描述
            content += f"**{timestamp[:10]}**\n\n"
            content += f"{event_content[:300]}\n\n"
            
            # 分析该事件的意义
            content += f"这一时期标志着{self._analyze_event_significance(event_content)}。\n\n"
    
    return content
```

### 方案2：优化 ReportContentEngine 的章节填充

**目标：在调用 Skills 前预处理数据**

```python
# report_content_engine.py
def fill_section(self, section_outline, material, report_level):
    # 预处理：将 material 转换为更易用的格式
    enriched_material = self._enrich_material(material)
    
    # 调用 Skill
    if report_level == 1:
        content = self.field_skill.generate_field_report_content(
            enriched_material,  # 传递增强后的素材
            section_outline['chapter']
        )
    
    return content

def _enrich_material(self, material):
    """增强素材：添加更多可直接使用的数据"""
    enriched = material.__dict__.copy()
    
    # 添加：主题聚类分析
    enriched['theme_clusters'] = self._cluster_by_theme(material)
    
    # 添加：高频实体上下文
    enriched['entity_contexts'] = self._extract_entity_contexts(material)
    
    # 添加：关键词共现网络
    enriched['keyword_cooccurrence'] = self._build_keyword_network(material)
    
    # 添加：每个chunk的主题标签
    enriched['chunk_themes'] = self._tag_chunks(material)
    
    return enriched
```

### 方案3：引入 LLM 辅助扩写（可选）

**仅在本地数据无法生成足够内容时使用**

```python
def _expand_section_with_llm(self, base_content, material, min_words=1000):
    """使用LLM扩写内容（保留引用）"""
    current_words = len(base_content)
    
    if current_words >= min_words:
        return base_content
    
    # 构造 prompt
    prompt = f"""
    基于以下田野调查素材，扩写章节内容至{min_words}字：
    
    当前内容：
    {base_content}
    
    可用素材：
    - 关键词：{', '.join([kw['keyword'] for kw in material.main_keywords[:20]])}
    - 时间线：{len(material.timeline)}个事件
    - 原文片段：{len(material.citation_pool)}段
    
    要求：
    1. 保持原有结构和引用
    2. 深入分析关键词背后的文化内涵
    3. 补充历史脉络和社会背景
    4. 每个观点必须基于提供的素材
    """
    
    # 调用 LLM (如果配置了API key)
    expanded = call_llm(prompt)
    
    return expanded
```

## 📋 实施步骤

### Phase 1：立即可做（不改代码）
1. ✅ **完成** - 音寨文档已处理，数据已提取

### Phase 2：最小改动优化（1-2小时）
1. 修改 `_write_resource_section` - 从 citation_pool 提取实际文本
2. 修改 `_write_general_section` - 使用 structured_insights 的数据
3. 在每个章节中引用3-5段原文（而不是只1段）

### Phase 3：深度优化（2-4小时）
1. 实现 `_analyze_cultural_resources` 方法
2. 实现 `_write_thematic_analysis` 方法
3. 实现 `_write_historical_timeline` 方法
4. 添加数据库查询 structured_insights 的方法

### Phase 4：高级功能（可选）
1. 引入 LLM 辅助扩写
2. 实现关键词共现分析
3. 实现实体关系网络可视化生成

## 🎯 预期效果

### 优化前（当前）
- Level 1: 458字/章
- Level 3: 169字/章
- 内容：模板化，空洞

### 优化后（Phase 2）
- Level 1: 800-1200字/章
- Level 3: 600-800字/章
- 内容：有实际数据支撑，有原文引用

### 优化后（Phase 3）
- Level 1: 1500-2000字/章
- Level 3: 1000-1500字/章
- 内容：深度分析，结构清晰，数据丰富

## 💡 关键洞察

**问题不在数据，在于 Skills 没有使用数据！**

✅ 数据提取完整：
- 66个chunks，每个300-500字
- 60个关键词
- 8个时间线事件
- 66个结构化insights

❌ Skills 当前使用情况：
- 只用了关键词列表（text）
- 完全忽略了chunks的内容
- 完全忽略了structured_insights
- 象征性引用1条原文

**解决方案：让 Skills 真正读取和使用这些数据！**
