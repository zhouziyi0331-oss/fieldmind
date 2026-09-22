# FieldMind 脏数据→干净数据双通道架构
## 正确理解用户需求的设计

---

## 🎯 核心概念澄清

### 脏数据通道 (Dirty Data Pipeline)
**目标**: 完整性 (Completeness) > 质量 (Quality)  
**任务**: 无损地将所有形式的内容转换为标准文档文本  
**原则**: 宁可冗余，不可遗漏

```
┌─────────────────────────────────────────────────────────────────┐
│                    脏数据通道                                     │
│               "把一切变成完整的文档文本"                          │
└─────────────────────────────────────────────────────────────────┘

输入: 任何形式的内容
  ├─ 🎵 音频文件 (MP3, WAV, M4A...)
  ├─ 🎬 视频文件 (MP4, AVI, MOV...)
  ├─ 🖼️ 图片文件 (JPG, PNG, PDF扫描件...)
  ├─ 📊 表格文件 (Excel, CSV...)
  └─ 📄 文档文件 (PDF, Word, TXT...)

          ↓ [规范化处理 - 追求完整性]

处理方式:
  🎵 音频 → Whisper转录
      ↓
      "呃，今天我们开会讨论了，嗯，那个项目的进度，
       然后张三说要延期，嗯嗯，李四不同意，最后王五，
       啊，王五说要再评估一下，对吧..."
      
      特点: 保留所有口语、语气词、重复、停顿
      质量: ⭐⭐⭐ (可能不流畅)
      完整性: ⭐⭐⭐⭐⭐ (100%还原)

  🎬 视频 → 场景提取 + 视觉理解 + 语音转录
      ↓
      "[场景1: 会议室, 10:00-10:15]
       画面: 5个人围坐在会议桌旁，投影仪显示项目甘特图
       对话: 张三: '我们的进度落后了...' 李四: '我不同意...'
       [场景2: 会议室, 10:15-10:30]
       画面: 白板上写满文字，王五站在白板前讲解
       对话: 王五: '我建议重新评估风险...'"
       
      特点: 场景完整记录，对话逐字转录
      质量: ⭐⭐⭐ (可能冗长重复)
      完整性: ⭐⭐⭐⭐⭐ (所有场景+所有对话)

  🖼️ 图片 → OCR + 视觉理解
      ↓
      "识别文字: 项目进度报告 2024年Q1
       图表内容: 柱状图显示三个项目的完成率分别为60%、75%、40%
       图片描述: 一张会议室照片，墙上挂着公司logo，
       桌上放着咖啡杯和笔记本电脑，窗外可以看到城市天际线"
       
      特点: 文字+视觉内容全提取
      质量: ⭐⭐⭐⭐ (OCR可能有错字)
      完整性: ⭐⭐⭐⭐⭐ (所有可见信息)

  📄 文档 → 直接提取
      ↓
      "第一章 项目概述\n\n    本项目旨在...\n\n
       [页眉: 机密文件] [页脚: 第1页/共10页]\n
       第二章 项目范围\n    2.1 范围说明..."
       
      特点: 保留所有原始内容，包括格式标记
      质量: ⭐⭐⭐⭐ (可能有格式噪声)
      完整性: ⭐⭐⭐⭐⭐ (100%原文)

          ↓

输出: 标准文档对象 (Normalized Document)
  {
    "document_id": 123,
    "original_type": "audio" | "video" | "image" | "document",
    "full_text": "完整的、未清洗的、冗余的原始文本内容",
    "length": 50000,  // 字符数，可能很长
    "completeness_score": 0.98,  // 完整性评分
    "quality_score": 0.65,  // 质量可能较低，不重要
    "metadata": {
      "duration": "15:32",  // 如果是音视频
      "scene_count": 8,  // 如果是视频
      "word_count": 8500,
      "original_format": "mp4"
    }
  }

存储位置: document_chunks.normalized_content (完整原始文本)
```

---

### 干净数据通道 (Clean Data Pipeline)
**目标**: 精确性 (Precision) > 召回率 (Recall)  
**任务**: 从完整文本中提取核心结构化知识  
**原则**: 只要最核心的信息，去除冗余

```
┌─────────────────────────────────────────────────────────────────┐
│                    干净数据通道                                   │
│         "从完整文档中提取核心人/地点/事件/关系"                   │
└─────────────────────────────────────────────────────────────────┘

输入: 脏数据通道产生的完整文本 (normalized_content)

          ↓ [智能提取 - 追求精确性]

Step 1: 提取核心事件 (1-3个最重要的)
───────────────────────────────────────────
原始文本 (8500字):
  "呃，今天我们开会讨论了，嗯，那个项目的进度，
   然后张三说要延期，嗯嗯，李四不同意，blah blah...
   (大量冗余对话)
   ...最后决定延期两周，由王五负责重新评估风险..."

          ↓ [事件提取]

核心事件:
  Event 1: {
    "event_type": "决策",
    "event_name": "项目延期决策",
    "description": "会议决定项目延期两周",
    "participants": [
      {"name": "张三", "role": "提议者"},
      {"name": "李四", "role": "反对者"},
      {"name": "王五", "role": "负责人"}
    ],
    "time": "2024-01-15 10:00-10:30",
    "location": "会议室",
    "outcome": "延期两周",
    "next_action": "王五负责风险评估"
  }

  Event 2: {
    "event_type": "任务分配",
    "event_name": "风险评估任务",
    "description": "指派王五进行项目风险重新评估",
    "participants": [
      {"name": "王五", "role": "执行者"}
    ],
    "deadline": "2024-01-20"
  }

注意: 只提取1-3个核心事件，忽略90%的冗余对话

Step 2: 提取核心实体
───────────────────────────────────────────
从事件中提取最小化信息节点:

实体类型: 人物 (Person)
  ├─ 张三: {"role": "项目成员", "action": "提议延期"}
  ├─ 李四: {"role": "项目成员", "action": "反对延期"}
  └─ 王五: {"role": "负责人", "action": "风险评估"}

实体类型: 地点 (Location)
  └─ 会议室: {"type": "物理空间"}

实体类型: 时间 (Time)
  ├─ 2024-01-15: {"event": "会议"}
  └─ 2024-01-20: {"event": "评估截止"}

实体类型: 概念 (Concept)
  ├─ 项目延期: {"category": "项目管理"}
  └─ 风险评估: {"category": "项目管理"}

Step 3: 提取核心关系
───────────────────────────────────────────
关系三元组 (Subject - Predicate - Object):

1. (张三) --[提议]--> (项目延期)
2. (李四) --[反对]--> (项目延期)
3. (王五) --[负责]--> (风险评估)
4. (项目延期) --[导致]--> (风险评估)
5. (会议) --[参与者]--> (张三, 李四, 王五)

Step 4: 最小化信息节点
───────────────────────────────────────────
每个事件必须回答的5W1H:

Event 1: 项目延期决策
  • Who (谁):  张三、李四、王五
  • What (什么): 决定项目延期两周
  • When (何时): 2024-01-15 10:00-10:30
  • Where (何地): 会议室
  • Why (为何): 项目进度落后
  • How (如何): 会议讨论后决策

          ↓

输出: 结构化知识对象
  {
    "document_id": 123,
    "extracted_events": [
      {Event 1 对象},
      {Event 2 对象}
    ],
    "extracted_entities": [
      {"name": "张三", "type": "person", ...},
      {"name": "李四", "type": "person", ...},
      {"name": "王五", "type": "person", ...},
      {"name": "会议室", "type": "location", ...}
    ],
    "extracted_relations": [
      {关系1}, {关系2}, ...
    ],
    "summary": "会议决定项目延期两周，由王五负责风险评估",
    "key_points": [
      "项目延期决策",
      "王五负责风险评估",
      "截止日期: 2024-01-20"
    ]
  }

存储位置: 
  - entities_unified 表
  - events_unified 表
  - relationships_unified 表
```

---

## 📊 双通道对比

| 维度 | 脏数据通道 | 干净数据通道 |
|------|-----------|-------------|
| **目标** | 完整性 100% | 精确性 90%+ |
| **输入** | 原始多模态文件 | 脏通道的完整文本 |
| **输出** | 冗长的完整文本 | 精简的结构化数据 |
| **文本长度** | 8500字 | 200字摘要 + 结构化数据 |
| **处理原则** | 宁多勿少 | 宁精勿滥 |
| **质量要求** | 可以低质量 | 必须高精度 |
| **冗余处理** | 保留所有冗余 | 去除90%冗余 |
| **应用场景** | 全文检索、原文查看 | 知识图谱、智能问答 |
| **存储位置** | `document_chunks.normalized_content` | `entities/events/relationships` 表 |

---

## 🔄 完整的数据流转

```
用户上传视频: "2024-01-15项目会议录像.mp4" (15分钟)
    ↓
┌─────────────────────────────────────────────────────┐
│ 阶段1: 脏数据通道 (无损转换)                         │
└─────────────────────────────────────────────────────┘
    ↓
文件类型检测: video/mp4
    ↓
视频处理流程:
  1. PySceneDetect 场景分割 → 8个场景
  2. Whisper 语音转录 → 8500字对话文本
  3. BLIP-2 关键帧理解 → 场景描述
    ↓
生成完整文档 (normalized_content):
  """
  [场景1: 00:00-02:15] 会议室
  画面: 5人围坐，投影仪显示甘特图
  对话: 
  张三: "呃，大家好，今天我们，嗯，讨论一下项目进度..."
  李四: "我看了一下，嗯嗯，进度好像落后了..."
  (完整的8500字转录，包含所有语气词、重复、停顿)
  ...
  [场景8: 13:30-15:00] 会议室
  画面: 王五在白板前总结
  对话:
  王五: "好，那我们，啊，最后决定延期两周，然后我来..."
  """
    ↓
存储: document_chunks.normalized_content
大小: 8500字 (完整)
质量: ⭐⭐⭐ (有冗余)
完整性: ⭐⭐⭐⭐⭐ (100%)

════════════════════════════════════════════════════════

    ↓
┌─────────────────────────────────────────────────────┐
│ 阶段2: 干净数据通道 (结构化提取)                     │
└─────────────────────────────────────────────────────┘
    ↓
输入: 上述8500字完整文本
    ↓
AI分析处理:
  - 去除语气词: "呃"、"嗯"、"啊"
  - 去除重复内容: 90%的冗余对话
  - 识别关键转折: "最后决定"、"那我们"
  - 提取核心论点: 张三提议、李四反对、王五总结
    ↓
提取1-3个核心事件:
  Event 1: "项目延期决策"
    - 参与者: 张三、李四、王五
    - 时间: 2024-01-15 10:00
    - 地点: 会议室
    - 决策: 延期两周
    - 原因: 进度落后
    
  Event 2: "风险评估任务分配"
    - 负责人: 王五
    - 截止: 2024-01-20
    ↓
提取核心实体:
  - 张三 (人物, 提议者)
  - 李四 (人物, 反对者)
  - 王五 (人物, 负责人)
  - 会议室 (地点)
  - 项目延期 (概念)
    ↓
提取核心关系:
  - (张三) --提议--> (项目延期)
  - (李四) --反对--> (项目延期)
  - (王五) --负责--> (风险评估)
    ↓
生成结构化知识:
  存储到:
  - entities_unified: 3条记录 (张三、李四、王五)
  - events_unified: 2条记录 (延期决策、任务分配)
  - relationships_unified: 3条记录
  
大小: 200字摘要 + 结构化数据
质量: ⭐⭐⭐⭐⭐ (高精度)
覆盖率: 20% (只保留核心)
```

---

## 🏗️ 统一流水线实现

```python
class UnifiedPipeline:
    """
    统一流水线: 脏数据通道 → 干净数据通道
    """
    
    async def process_document(self, document_id: int):
        """完整流程"""
        
        # ========== 脏数据通道 ==========
        logger.info("🔴 进入脏数据通道: 追求完整性")
        
        # 步骤1: 文件类型检测
        doc = self.get_document(document_id)
        file_type = self.detect_file_type(doc)
        
        # 步骤2: 无损转换为文本
        if file_type == 'audio':
            full_text = await self.transcribe_audio_complete(doc)
            # 完整转录，保留所有内容
            
        elif file_type == 'video':
            full_text = await self.process_video_complete(doc)
            # 场景+对话完整提取
            
        elif file_type == 'image':
            full_text = await self.ocr_and_describe_complete(doc)
            # OCR + 视觉描述完整
            
        else:  # document
            full_text = self.extract_text_complete(doc)
            # 原文完整提取
        
        # 步骤3: 保存完整文本
        self.save_normalized_content(
            document_id=document_id,
            full_text=full_text,
            completeness_score=0.98,  # 完整性优先
            quality_score=0.65  # 质量可能较低，不重要
        )
        
        logger.info(f"✅ 脏数据通道完成: {len(full_text)} 字符")
        
        # ========== 干净数据通道 ==========
        logger.info("🟢 进入干净数据通道: 追求精确性")
        
        # 步骤4: 提取核心事件 (1-3个)
        core_events = await self.extract_core_events(
            text=full_text,
            max_events=3,  # 只要最核心的
            min_importance=0.8  # 高重要性阈值
        )
        
        logger.info(f"提取到 {len(core_events)} 个核心事件")
        
        # 步骤5: 提取核心实体 (最小化节点)
        core_entities = await self.extract_core_entities(
            events=core_events,
            text=full_text
        )
        
        logger.info(f"提取到 {len(core_entities)} 个核心实体")
        
        # 步骤6: 提取核心关系
        core_relations = await self.extract_core_relations(
            entities=core_entities,
            events=core_events
        )
        
        logger.info(f"提取到 {len(core_relations)} 个核心关系")
        
        # 步骤7: 保存结构化知识
        self.save_structured_knowledge(
            document_id=document_id,
            events=core_events,
            entities=core_entities,
            relations=core_relations
        )
        
        logger.info("✅ 干净数据通道完成")
        
        return {
            'dirty_pipeline': {
                'full_text_length': len(full_text),
                'completeness': 0.98
            },
            'clean_pipeline': {
                'events': len(core_events),
                'entities': len(core_entities),
                'relations': len(core_relations)
            }
        }
    
    async def extract_core_events(
        self,
        text: str,
        max_events: int = 3,
        min_importance: float = 0.8
    ) -> List[Event]:
        """
        提取核心事件 - 干净数据通道的关键
        
        原则:
        1. 只提取最重要的1-3个事件
        2. 每个事件必须有明确的 who/what/when/where
        3. 去除90%的冗余信息
        """
        
        # 使用LLM分析
        prompt = f"""
        从以下文本中提取1-3个最核心的事件。
        
        要求:
        1. 只要最重要的事件，忽略细枝末节
        2. 每个事件必须包含: 参与者、动作、时间、地点
        3. 用简洁的语言描述，去除冗余
        
        文本 ({len(text)} 字):
        {text}
        
        输出格式:
        Event 1:
          - 名称: 
          - 参与者: 
          - 动作: 
          - 时间: 
          - 地点: 
          - 结果: 
        """
        
        response = await self.llm.generate(prompt)
        events = self.parse_events(response)
        
        # 过滤低重要性事件
        events = [e for e in events if e.importance >= min_importance]
        
        # 限制数量
        events = events[:max_events]
        
        return events
    
    async def extract_core_entities(
        self,
        events: List[Event],
        text: str
    ) -> List[Entity]:
        """
        提取核心实体 - 最小化信息节点
        
        原则:
        1. 只提取事件中出现的实体
        2. 每个实体必须有明确的类型和作用
        3. 去除不重要的实体
        """
        
        # 从事件中提取参与者
        entities = []
        
        for event in events:
            for participant in event.participants:
                entity = Entity(
                    name=participant['name'],
                    type='person',
                    role=participant['role'],
                    related_events=[event.id]
                )
                entities.append(entity)
            
            # 提取地点
            if event.location:
                entity = Entity(
                    name=event.location,
                    type='location',
                    related_events=[event.id]
                )
                entities.append(entity)
        
        # 去重
        entities = self.deduplicate_entities(entities)
        
        return entities
    
    async def process_video_complete(self, doc: Document) -> str:
        """
        视频完整处理 - 脏数据通道
        
        目标: 100%还原所有场景和对话
        """
        
        # 1. 场景分割
        scenes = await self.scene_detector.detect_scenes(doc.file_path)
        
        full_content = []
        
        for i, scene in enumerate(scenes, 1):
            scene_text = f"[场景{i}: {scene.start_time}-{scene.end_time}] {scene.location}\n"
            
            # 2. 视觉理解
            visual_desc = await self.blip2.describe_scene(scene.key_frame)
            scene_text += f"画面: {visual_desc}\n"
            
            # 3. 语音转录 (完整)
            audio_transcript = await self.whisper.transcribe(
                scene.audio,
                task='transcribe',
                word_timestamps=True,  # 保留时间戳
                verbose=True  # 保留所有细节
            )
            scene_text += f"对话:\n{audio_transcript}\n\n"
            
            full_content.append(scene_text)
        
        # 返回完整的、未清洗的文本
        return '\n'.join(full_content)
```

---

## ✅ 关键差异总结

### 你的真实需求 vs 我之前的理解

| 概念 | 我之前的理解 ❌ | 你的真实需求 ✅ |
|------|---------------|---------------|
| **脏数据通道** | AI输出可能有错误，需要清洗 | 完整性优先，保留所有信息，即使冗余 |
| **干净数据通道** | 清洗后的文本 | 从完整文本中提取核心结构化知识 |
| **处理目标** | 文本质量提升 | 完整转换 → 精准提取 |
| **核心任务** | 去噪、去重 | 无损规范化 → 核心事件/实体提取 |
| **最小节点** | 文本块 | 人/地点/事件的5W1H |
| **1-3个事件** | 没理解 | 只提取最核心的事件，不是全部 |

### 新的架构核心

1. **脏数据通道 = 完整性通道**
   - 音视频图片 → 完整的文档文本 (可以冗长、重复)
   - 宁可多不可少，100%召回

2. **干净数据通道 = 精准提取通道**
   - 完整文本 → 核心事件(1-3个) + 核心实体 + 核心关系
   - 只要精华，去除90%冗余

3. **两个通道是串联关系**
   - 脏 → 干，不可跳过
   - 脏提供原料，干提取精华

这样理解是否正确？
