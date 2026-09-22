# 数据边界重新设计 - 可验证版本

## 🎯 核心问题和解决方案

### 问题1：识别不完整
**场景**：一个5000字的PDF，只识别了10个字，就说"识别完成"？

**解决方案**：**完整性必须可验证**

```python
# 音频/视频：完整性 = 已转写时长 / 总时长
completeness = transcribed_duration / total_duration

示例：
- 总时长：3600秒（1小时）
- 转写覆盖：3500秒
- 完整性：3500/3600 = 97.2%

# PDF/文档：完整性 = 已提取页数 / 总页数
completeness = extracted_pages / total_pages

示例：
- 总页数：50页
- 提取成功：48页
- 完整性：48/50 = 96%

# 图片：完整性 = OCR覆盖区域 / 总区域
completeness = ocr_coverage_area / total_area

示例：
- 图片总面积：1920x1080
- OCR识别区域：80%
- 完整性：80%
```

---

### 问题2：质量分数随便估
**场景**：说"完整度75%"，但没有验证逻辑？

**解决方案**：**每个分数都有明确计算公式**

```python
# 边界1：完整性分数（可验证）
completeness_score = {
    # 1. 内容覆盖率（40%权重）
    "coverage": extracted_content_size / source_file_size,
    
    # 2. 必需项完成率（30%权重）
    "required_items": completed_items / total_required_items,
    
    # 3. 元数据完整率（20%权重）
    "metadata": present_metadata / required_metadata,
    
    # 4. 质量指标达标率（10%权重）
    "quality": passed_checks / total_checks
}

# 最终分数（加权平均）
final_score = (
    coverage * 0.4 +
    required_items * 0.3 +
    metadata * 0.2 +
    quality * 0.1
)

# 边界2：知识丰富度（可验证）
richness_score = {
    # 1. 实体密度（30%权重）
    "entity_density": entity_count / (word_count / 100),  # 每100字多少实体
    
    # 2. 事件密度（30%权重）
    "event_density": event_count / (word_count / 500),  # 每500字多少事件
    
    # 3. 关系完整度（20%权重）
    "relationship_ratio": relationship_count / (entity_count + event_count),
    
    # 4. 连通性（20%权重）
    "connectivity": connected_nodes / total_nodes
}

# 最终分数（加权平均）
final_score = (
    normalize(entity_density) * 0.3 +
    normalize(event_density) * 0.3 +
    relationship_ratio * 0.2 +
    connectivity * 0.2
)
```

---

### 问题3：无法追溯来源
**场景**：提取了"张三"这个实体，但不知道从哪来的？AI编的？

**解决方案**：**每个知识点都标记来源**

```python
# 实体示例
entity = {
    "name": "张三",
    "type": "人物",
    "source": {
        "type": "extracted",  # extracted（提取的）或 inferred（推理的）
        "document_id": 123,
        "text_position": {
            "start": 1250,    # 在文本的第1250个字符
            "end": 1252,      # 到第1252个字符
            "context": "...村长张三说..."  # 上下文
        },
        "audio_position": {  # 如果是音频
            "start_time": 125.5,  # 第125.5秒
            "end_time": 126.0,
            "speaker": "speaker_2"
        },
        "confidence": 0.95,   # 提取置信度
        "method": "NER"       # 提取方法（NER/规则/手动）
    }
}

# 关系示例
relationship = {
    "source": "张三",
    "target": "古庙",
    "type": "管理",
    "source": {
        "type": "inferred",  # 推理得出
        "evidence": [        # 推理依据
            {
                "document_id": 123,
                "text": "张三负责古庙的日常维护",
                "position": {"start": 2500, "end": 2520},
                "confidence": 0.88
            }
        ],
        "inference_rule": "职责关系推理",  # 推理规则
        "is_ai_generated": True  # 明确标记AI生成
    }
}
```

---

## 📐 边界1：完整性验证（可验证版本）

### 核心原则
1. **完整性可量化** - 用实际数据计算，不估算
2. **所有数据保留** - 不管完整性多低
3. **标记质量等级** - 明确告诉用户数据质量

### 验证公式

#### 音频/视频文件

```python
def calculate_audio_completeness(metadata):
    """
    音频完整性验证
    
    可验证指标：
    1. 时间覆盖率：转写覆盖了多少音频时长
    2. 文本完整率：有多少片段被成功转写
    3. 说话人覆盖：说话人是否都被识别
    """
    total_duration = metadata["audio_duration"]  # 总时长（秒）
    transcript = metadata.get("transcript", [])
    
    # 1. 时间覆盖率
    if transcript:
        transcribed_duration = sum(
            seg["end"] - seg["start"] 
            for seg in transcript 
            if "start" in seg and "end" in seg
        )
        time_coverage = transcribed_duration / total_duration
    else:
        time_coverage = 0
    
    # 2. 片段完整率
    # 假设理想情况下，每5秒一个片段
    expected_segments = total_duration / 5
    actual_segments = len(transcript)
    segment_coverage = min(actual_segments / expected_segments, 1.0)
    
    # 3. 说话人覆盖
    segments_with_speaker = sum(
        1 for seg in transcript if "speaker" in seg
    )
    speaker_coverage = segments_with_speaker / len(transcript) if transcript else 0
    
    # 加权平均
    completeness = (
        time_coverage * 0.5 +      # 时间覆盖最重要（50%）
        segment_coverage * 0.3 +   # 片段完整性（30%）
        speaker_coverage * 0.2     # 说话人识别（20%）
    )
    
    return {
        "completeness": completeness,
        "details": {
            "time_coverage": time_coverage,
            "segment_coverage": segment_coverage,
            "speaker_coverage": speaker_coverage,
            "total_duration": total_duration,
            "transcribed_duration": transcribed_duration if transcript else 0,
            "segments": len(transcript)
        },
        "verification": {
            "formula": "0.5*时间覆盖 + 0.3*片段完整 + 0.2*说话人覆盖",
            "verifiable": True
        }
    }
```

#### PDF/文档文件

```python
def calculate_document_completeness(metadata):
    """
    文档完整性验证
    
    可验证指标：
    1. 页面提取率：提取了多少页
    2. 字数合理性：提取的字数 vs 预期字数
    3. 结构完整性：标题、段落是否完整
    """
    total_pages = metadata.get("page_count", 1)
    extracted_pages = metadata.get("extracted_pages", 0)
    
    # 1. 页面提取率
    page_extraction = extracted_pages / total_pages if total_pages > 0 else 0
    
    # 2. 字数合理性
    # PDF一般：300-500字/页，取中间值400
    expected_words = total_pages * 400
    actual_words = metadata.get("word_count", 0)
    
    # 字数比例在50%-150%之间算合理
    word_ratio = actual_words / expected_words if expected_words > 0 else 0
    word_reasonableness = 1.0 if 0.5 <= word_ratio <= 1.5 else max(0, 1 - abs(word_ratio - 1))
    
    # 3. 结构完整性
    has_structure = metadata.get("structure_info") is not None
    structure_score = 1.0 if has_structure else 0.5
    
    # 加权平均
    completeness = (
        page_extraction * 0.5 +       # 页面提取最重要（50%）
        word_reasonableness * 0.3 +   # 字数合理性（30%）
        structure_score * 0.2          # 结构完整性（20%）
    )
    
    return {
        "completeness": completeness,
        "details": {
            "page_extraction": page_extraction,
            "word_ratio": word_ratio,
            "structure_complete": has_structure,
            "total_pages": total_pages,
            "extracted_pages": extracted_pages,
            "expected_words": expected_words,
            "actual_words": actual_words
        },
        "verification": {
            "formula": "0.5*页面提取 + 0.3*字数合理 + 0.2*结构完整",
            "verifiable": True
        }
    }
```

#### 图片文件

```python
def calculate_image_completeness(metadata):
    """
    图片完整性验证
    
    可验证指标：
    1. OCR覆盖率：识别了多少文字区域
    2. 图像描述：是否有视觉描述
    """
    # 1. OCR覆盖率
    ocr_regions = metadata.get("ocr_regions", [])
    image_area = metadata.get("width", 1) * metadata.get("height", 1)
    
    if ocr_regions:
        ocr_area = sum(
            region.get("width", 0) * region.get("height", 0)
            for region in ocr_regions
        )
        ocr_coverage = min(ocr_area / image_area, 1.0)
    else:
        ocr_coverage = 0
    
    # 2. 图像描述
    description = metadata.get("image_description", "")
    has_description = len(description) >= 20
    description_score = 1.0 if has_description else 0
    
    # 加权
    completeness = (
        ocr_coverage * 0.4 +       # OCR覆盖（40%）
        description_score * 0.6    # 图像描述（60%）- 更重要
    )
    
    return {
        "completeness": completeness,
        "details": {
            "ocr_coverage": ocr_coverage,
            "has_description": has_description,
            "description_length": len(description),
            "ocr_regions": len(ocr_regions)
        },
        "verification": {
            "formula": "0.4*OCR覆盖 + 0.6*图像描述",
            "verifiable": True
        }
    }
```

---

## 📐 边界2：知识丰富度验证（可验证版本）

### 核心原则
1. **丰富度可量化** - 基于实际提取的数据计算
2. **相对值，不是绝对值** - 每100字多少实体，而不是总数
3. **标记来源** - 每个知识点都可追溯

### 验证公式

```python
def calculate_knowledge_richness(document, pipeline_result):
    """
    知识丰富度验证
    
    可验证指标：
    1. 实体密度：每100字提取多少实体
    2. 事件密度：每500字提取多少事件
    3. 关系完整度：实体和事件之间的关系比例
    4. 知识连通性：知识图谱的连通程度
    """
    word_count = document.get("word_count", 1)
    results = pipeline_result.get("results", {})
    
    # Step 3: 实体
    entities_count = results.get(3, {}).get("entities_count", 0)
    # Step 4: 事件
    events_count = results.get(4, {}).get("events_count", 0)
    # Step 5: 关系
    relationships_count = results.get(5, {}).get("relationships_count", 0)
    # KG节点和边
    kg_nodes = results.get(3, {}).get("kg_nodes_created", 0) + results.get(4, {}).get("kg_nodes_created", 0)
    kg_edges = results.get(5, {}).get("kg_edges_created", 0)
    
    # 1. 实体密度（每100字）
    entity_density = (entities_count / word_count) * 100
    # 正常范围：0.5-3个/100字，取2为满分
    entity_score = min(entity_density / 2.0, 1.0)
    
    # 2. 事件密度（每500字）
    event_density = (events_count / word_count) * 500
    # 正常范围：0.2-2个/500字，取1为满分
    event_score = min(event_density / 1.0, 1.0)
    
    # 3. 关系完整度
    # 理想情况：每个实体和事件至少有1个关系
    expected_relationships = entities_count + events_count
    relationship_ratio = relationships_count / expected_relationships if expected_relationships > 0 else 0
    relationship_score = min(relationship_ratio, 1.0)
    
    # 4. 知识连通性
    if kg_nodes > 0:
        # 简化连通性计算：有边的节点数 / 总节点数
        max_connected = min(kg_edges * 2, kg_nodes)  # 每条边连接2个节点
        connectivity = max_connected / kg_nodes
    else:
        connectivity = 0
    
    # 加权平均
    richness = (
        entity_score * 0.3 +
        event_score * 0.3 +
        relationship_score * 0.2 +
        connectivity * 0.2
    )
    
    return {
        "richness": richness,
        "details": {
            "entity_density": entity_density,
            "event_density": event_density,
            "relationship_ratio": relationship_ratio,
            "connectivity": connectivity,
            "entities": entities_count,
            "events": events_count,
            "relationships": relationships_count,
            "kg_nodes": kg_nodes,
            "kg_edges": kg_edges,
            "word_count": word_count
        },
        "verification": {
            "formula": "0.3*实体密度 + 0.3*事件密度 + 0.2*关系完整度 + 0.2*连通性",
            "entity_density_formula": f"{entities_count}/{word_count}*100 = {entity_density:.2f}个/100字",
            "event_density_formula": f"{events_count}/{word_count}*500 = {event_density:.2f}个/500字",
            "relationship_ratio_formula": f"{relationships_count}/({entities_count}+{events_count}) = {relationship_ratio:.2f}",
            "connectivity_formula": f"{max_connected if kg_nodes > 0 else 0}/{kg_nodes} = {connectivity:.2f}",
            "verifiable": True
        }
    }
```

---

## 🎨 前端展示（可追溯版本）

### 文档列表 - 显示质量分数

```
┌─────────────────────────────────────────────────────────┐
│ 📄 田野调研_村长访谈.mp3                                  │
├─────────────────────────────────────────────────────────┤
│ 完整性: ██████████████░░░░░░ 72% (可验证 ℹ️)              │
│   └─ 点击查看: 时间覆盖85% + 片段完整60% + 说话人覆盖70%   │
│                                                          │
│ 知识丰富度: ████████████████░░ 81% (可验证 ℹ️)             │
│   └─ 点击查看: 5实体/100字 + 0.8事件/500字 + 关系度90%    │
│                                                          │
│ 提取结果:                                                 │
│   实体: 15个 | 事件: 10个 | 关系: 30个                     │
│                                                          │
│ 状态: ✅ 已处理 | 🕐 2024-01-15 14:30                     │
└─────────────────────────────────────────────────────────┘
```

### 知识图谱 - 标记来源

```
节点: 张三 (人物)
  ├─ 来源: 提取 ✅
  ├─ 位置: 第125.5-126.0秒
  ├─ 说话人: speaker_2
  ├─ 原文: "...村长张三说..."
  └─ 置信度: 95%

关系: 张三 --[管理]--> 古庙
  ├─ 来源: AI推理 🤖
  ├─ 依据: "张三负责古庙的日常维护"
  ├─ 位置: 第2500-2520字符
  ├─ 推理规则: 职责关系推理
  └─ 置信度: 88%
```

### 点击"可验证"按钮 - 显示计算公式

```
┌─────────────────────────────────────────────────────────┐
│ 📊 完整性验证详情                                          │
├─────────────────────────────────────────────────────────┤
│ 总分: 72%                                                 │
│                                                          │
│ 计算公式:                                                 │
│   0.5 × 时间覆盖 + 0.3 × 片段完整 + 0.2 × 说话人覆盖       │
│                                                          │
│ 详细计算:                                                 │
│   时间覆盖 = 3100秒 / 3600秒 = 86%                        │
│   片段完整 = 620段 / 720段(预期) = 86%                     │
│   说话人覆盖 = 580段 / 620段 = 94%                        │
│                                                          │
│ 最终得分:                                                 │
│   0.5 × 0.86 + 0.3 × 0.86 + 0.2 × 0.94 = 0.72 = 72%    │
│                                                          │
│ ✅ 所有数据可验证                                          │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ 总结：可验证的边界系统

### 边界1：完整性（可验证）
- ✅ 用实际数据计算（时长、页数、区域）
- ✅ 公式透明（加权平均，权重明确）
- ✅ 所有数据保留（不筛选）
- ✅ 质量可追溯（显示计算过程）

### 边界2：知识丰富度（可验证）
- ✅ 用相对密度（每100字多少实体）
- ✅ 公式透明（密度、比例、连通性）
- ✅ 所有知识保留（不筛选）
- ✅ 来源可追溯（标记提取/推理，显示原文位置）

### 前端展示：
- ✅ 显示质量分数
- ✅ 点击查看公式
- ✅ 标记AI生成（不同颜色）
- ✅ 点击追溯来源（跳转到原文位置）

**这个方案解决你的顾虑了吗？**
