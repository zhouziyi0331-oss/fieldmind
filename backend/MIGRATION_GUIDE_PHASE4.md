# Phase 4工具函数迁移指南

## 概述

Phase 4将旧Agent的核心功能提取为独立的工具函数，提供更灵活、更易维护的API。本指南帮助用户从旧Agent迁移到新工具。

## 快速对比

| 旧方式 | 新方式 | 优势 |
|--------|--------|------|
| 实例化Agent → 调用方法 | 直接调用函数 | 更轻量、无状态 |
| 紧耦合到Agent生命周期 | 独立可复用 | 可在任何地方调用 |
| 需要理解Agent架构 | 简单函数调用 | 学习曲线低 |

## 迁移映射

### 1. 音频转录：TranscriptAgent → transcribe_audio()

**旧方式（已废弃）：**
```python
from app.services.agents.transcript_agent import TranscriptAgent

agent = TranscriptAgent()  # ⚠️ 触发废弃警告
result = agent.run(task={
    'file_path': '/path/to/audio.mp3',
    'file_type': 'audio'
})
text = result.output['transcript']
```

**新方式（推荐）：**
```python
from app.tools.transcript import transcribe_audio

result = transcribe_audio(
    file_path='/path/to/audio.mp3',
    file_type='audio',
    language='auto',           # 可选：自动检测语言
    enable_metrics=True,       # 可选：提取量化指标
    enable_cleaning=True       # 可选：自动清洗文本
)

# 返回值结构
{
    'transcript': {
        'full_text': '完整转录文本',
        'segments': [...],      # 时间轴分段
        'cleaned_text': '...'   # 清洗后文本（如果enable_cleaning=True）
    },
    'metadata': {
        'status': 'success',
        'duration': 120.5,
        'language': 'zh',
        'model': 'whisper-large-v3'
    },
    'metrics': {               # 如果enable_metrics=True
        'professional_terms': [...],
        'key_people': [...],
        'special_events': [...]
    }
}
```

---

### 2. 实体识别：EntityAgent → extract_entities()

**旧方式（已废弃）：**
```python
from app.services.agents.entity_agent import EntityAgent

agent = EntityAgent()  # ⚠️ 触发废弃警告
result = agent.run(task={'text': '...'})
entities = result.output['entities']
```

**新方式（推荐）：**
```python
from app.tools.entity import extract_entities

result = extract_entities(
    text='张三在北京大学学习人类学',
    merge_threshold=0.85,      # 可选：实体合并相似度阈值
    extract_context=True       # 可选：是否提取上下文
)

# 返回值结构
{
    'entities': [
        {
            'text': '张三',
            'type': 'PER',         # 人物
            'start': 0,
            'end': 2,
            'confidence': 0.98,
            'context': '...'       # 如果extract_context=True
        },
        {
            'text': '北京大学',
            'type': 'ORG',         # 机构
            'start': 3,
            'end': 7,
            'confidence': 0.95
        }
    ],
    'statistics': {
        'total': 2,
        'by_type': {
            'PER': 1,
            'ORG': 1
        }
    }
}
```

**实体类型说明：**
- `PER`: 人物
- `ORG`: 机构/组织
- `LOC`: 地点
- `TIME`: 时间
- `CONCEPT`: 文化概念

---

### 3. 关系抽取：RelationAgent → extract_relations()

**旧方式（已废弃）：**
```python
from app.services.agents.relation_agent import RelationAgent

agent = RelationAgent()  # ⚠️ 触发废弃警告
result = agent.run(task={'text': '...', 'entities': [...]})
relations = result.output['relations']
```

**新方式（推荐）：**
```python
from app.tools.relation import extract_relations

result = extract_relations(
    text='张三是李四的学生，他们在北京大学工作',
    entities=[                 # 可选：预先提取的实体列表
        {'text': '张三', 'type': 'PER'},
        {'text': '李四', 'type': 'PER'},
        {'text': '北京大学', 'type': 'ORG'}
    ],
    max_relations=100          # 可选：最大关系数
)

# 返回值结构
{
    'triples': [
        {
            'head': '张三',
            'relation': '师生',
            'tail': '李四',
            'type': 'social',
            'confidence': 0.92,
            'evidence': '张三是李四的学生'
        },
        {
            'head': '张三',
            'relation': '工作于',
            'tail': '北京大学',
            'type': 'organization',
            'confidence': 0.88
        }
    ],
    'statistics': {
        'total': 2,
        'by_type': {
            'social': 1,
            'organization': 1
        }
    }
}
```

**关系类型说明：**
- `family`: 家族关系
- `social`: 社会关系
- `organization`: 组织关系
- `location`: 位置关系
- `time`: 时间关系
- `ownership`: 所属关系
- `event`: 事件关系

---

### 4. Skills分析：SummaryAgent → analyze_with_skills()

**旧方式（已废弃）：**
```python
from app.services.agents.summary_agent import SummaryAgent

agent = SummaryAgent()  # ⚠️ 触发废弃警告
result = agent.run(task={'content': '...'})
summary = result.output['summary']
```

**新方式（推荐）：**
```python
from app.tools.summary import analyze_with_skills

result = analyze_with_skills(
    content='本次田野调查在某村进行...',
    enabled_skills=[           # 可选：指定启用的Skills
        'heritage_dadi',       # 遗产大地
        'xiangtu_china'        # 乡土中国
    ],
    report_format='summary',   # 可选：'full' | 'summary'
    include_statistics=True    # 可选：包含统计信息
)

# 返回值结构
{
    'skills_summary': {
        'heritage_dadi': {
            'findings': [
                '发现传统建筑群...',
                '保存完整的祭祀仪式...'
            ],
            'recommendations': ['建议申报文化遗产'],
            'score': 85
        },
        'xiangtu_china': {
            'findings': ['村落保持传统社会结构'],
            'score': 78
        }
    },
    'statistics': {
        'skills_used': 2,
        'total_findings': 3,
        'average_score': 81.5
    }
}
```

**可用Skills列表：**
- `heritage_dadi`: 遗产大地分析
- `business_feasibility`: 商业可行性分析
- `multi_village_sop`: 多村落标准化分析
- `literature_market_research`: 文献市场研究
- `xiangtu_china`: 乡土中国理论分析
- `sacred_memory`: 神圣记忆分析

---

## 在6-Agent v2中的使用

新工具函数已集成到6-Agent v2中，无需手动调用：

```python
from app.agents.v2 import IngestionAgent, KnowledgeAgent, ReportAgent

# IngestionAgent 自动使用 transcribe_audio()
ingestion_agent = IngestionAgent()
result = ingestion_agent.run(...)  # 内部调用transcribe_audio

# KnowledgeAgent 自动使用 extract_entities() + extract_relations()
knowledge_agent = KnowledgeAgent()
result = knowledge_agent.run(...)  # 内部调用entity/relation工具

# ReportAgent 自动使用 analyze_with_skills()
report_agent = ReportAgent()
result = report_agent.run(...)     # 内部调用skills分析
```

---

## 组合使用示例

工具函数可以灵活组合：

```python
from app.tools.transcript import transcribe_audio
from app.tools.entity import extract_entities
from app.tools.relation import extract_relations

# 1. 转录音频
transcript_result = transcribe_audio(
    file_path='/path/to/interview.mp3',
    language='zh'
)
text = transcript_result['transcript']['full_text']

# 2. 提取实体
entity_result = extract_entities(text=text)
entities = entity_result['entities']

# 3. 提取关系
relation_result = extract_relations(
    text=text,
    entities=entities
)
relations = relation_result['triples']

# 4. 构建知识图谱
knowledge_graph = {
    'entities': entities,
    'relations': relations
}
```

---

## 错误处理

新工具函数使用标准异常，便于捕获：

```python
from app.tools.transcript import transcribe_audio

try:
    result = transcribe_audio(file_path='/path/to/audio.mp3')
except FileNotFoundError:
    print("音频文件不存在")
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"转录失败: {e}")
```

---

## 性能优化建议

### 1. 批量处理
```python
from app.tools.entity import extract_entities

texts = ['文本1', '文本2', '文本3']
results = [extract_entities(text=t) for t in texts]
```

### 2. 关闭不需要的功能
```python
# 如果不需要指标提取，关闭可提升性能
result = transcribe_audio(
    file_path='...',
    enable_metrics=False,
    enable_cleaning=False
)
```

### 3. 调整阈值
```python
# 降低合并阈值可减少计算量
result = extract_entities(
    text='...',
    merge_threshold=0.7  # 默认0.85
)
```

---

## 向后兼容性

旧Agent代码仍然可以运行，但会触发废弃警告：

```python
from app.services.agents.transcript_agent import TranscriptAgent

agent = TranscriptAgent()  
# ⚠️  TranscriptAgent 已废弃: 核心功能已提取为工具函数
# 请使用: app.tools.transcript.transcribe_audio()
# 将在版本 2.0 中移除
```

**建议：** 在v2.0发布前完成迁移。

---

## FAQ

### Q1: 旧Agent什么时候会被删除？
A: 计划在v2.0版本删除，预计3-6个月后。

### Q2: 新工具函数的性能如何？
A: 性能与旧Agent相同，因为核心逻辑完全一致，只是去除了Agent包装层。

### Q3: 可以混用新旧方式吗？
A: 可以，但不推荐。建议统一使用新工具函数。

### Q4: 如何在旧项目中渐进式迁移？
A: 优先迁移新功能和经常修改的模块，稳定模块可延后迁移。

### Q5: 工具函数是否线程安全？
A: 是的，所有工具函数都是无状态的，可以安全并发调用。

---

## 技术支持

遇到问题？
- 查看详细测试报告：`PHASE5_INTEGRATION_TEST_REPORT.md`
- 查看完成总结：`PHASE4_5_COMPLETION_SUMMARY.md`
- 提交issue或联系开发团队
