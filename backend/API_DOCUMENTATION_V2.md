# 6-Agent v2 API文档

## 概述

6-Agent v2是FieldMind的新一代智能分析架构，由6个专职Agent组成流水线，配合独立的工具函数层，提供高效、灵活的内容处理能力。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     6-Agent v2 Pipeline                      │
└─────────────────────────────────────────────────────────────┘

输入 → IngestionAgent → ChunkingAgent → VectorizationAgent
           ↓                ↓                  ↓
       [transcript]     [chunking]        [embedding]
       
    → KnowledgeAgent → SynthesisAgent → ReportAgent → 输出
           ↓                ↓                ↓
      [entity/rel]     [synthesis]      [skills]


┌─────────────────────────────────────────────────────────────┐
│                      工具函数层 (Tools)                       │
└─────────────────────────────────────────────────────────────┘

app/tools/
├── transcript/         # 音频转录工具
├── entity/            # 实体识别工具
├── relation/          # 关系抽取工具
└── summary/           # Skills分析工具
```

---

## Agent详细说明

### 1. IngestionAgent - 数据摄取专员

**职责：** 
- 接收多种格式文件（音频/视频/文档）
- 转录音视频为文字（使用 `transcribe_audio` 工具）
- 提取文本内容
- 标准化为统一格式

**使用方式：**
```python
from app.agents.v2.ingestion_agent import IngestionAgent

agent = IngestionAgent()
result = agent.run(
    project_id=123,
    file_path='/path/to/audio.mp3',
    file_type='audio'
)

# 返回
{
    'text': '转录的完整文本',
    'metadata': {
        'duration': 120.5,
        'language': 'zh',
        'model': 'whisper-large-v3'
    }
}
```

**内部使用的工具：**
- `app.tools.transcript.transcribe_audio()` - 音频转录

**支持格式：**
- 音频：mp3, wav, m4a, flac
- 视频：mp4, avi, mov, mkv
- 文档：pdf, docx, txt, md

---

### 2. ChunkingAgent - 文档分块专员

**职责：**
- 将长文本智能分块
- 保持语义完整性
- 生成chunk元数据
- 存储到DocumentChunk表

**使用方式：**
```python
from app.agents.v2.chunking_agent import ChunkingAgent

agent = ChunkingAgent()
result = agent.run(
    document_id=456,
    text='长文本内容...',
    chunk_size=1000,
    overlap=200
)

# 返回
{
    'chunks': [
        {
            'id': 789,
            'text': 'chunk文本',
            'start': 0,
            'end': 1000,
            'metadata': {...}
        },
        ...
    ],
    'chunk_count': 15
}
```

**分块策略：**
- 基于语义边界分块
- 保持段落完整性
- 支持自定义chunk大小和重叠

---

### 3. VectorizationAgent - 向量化专员

**职责：**
- 为文本chunks生成向量
- 使用预训练embedding模型
- 存储到向量数据库
- 支持后续相似度搜索

**使用方式：**
```python
from app.agents.v2.vectorization_agent import VectorizationAgent

agent = VectorizationAgent()
result = agent.run(
    chunk_ids=[789, 790, 791],
    model='text-embedding-ada-002'
)

# 返回
{
    'vectorized_count': 3,
    'embeddings': [
        {'chunk_id': 789, 'vector': [0.1, 0.2, ...]},
        ...
    ]
}
```

**支持模型：**
- OpenAI: text-embedding-ada-002
- 本地模型: sentence-transformers/all-MiniLM-L6-v2

---

### 4. KnowledgeAgent - 知识构建专员

**职责：**
- 从文本中提取实体（使用 `extract_entities` 工具）
- 抽取实体关系（使用 `extract_relations` 工具）
- 构建知识图谱
- 跨文档实体合并

**使用方式：**
```python
from app.agents.v2.knowledge_agent import KnowledgeAgent

agent = KnowledgeAgent()
result = agent.run(
    document_ids=[456, 457],
    enable_graph=True
)

# 返回
{
    'entities': [
        {'text': '张三', 'type': 'PER', 'count': 5},
        {'text': '北京大学', 'type': 'ORG', 'count': 3}
    ],
    'relations': [
        {'head': '张三', 'relation': '就读于', 'tail': '北京大学'}
    ],
    'knowledge_graph': {
        'nodes': [...],
        'edges': [...]
    }
}
```

**内部使用的工具：**
- `app.tools.entity.extract_entities()` - 实体识别
- `app.tools.relation.extract_relations()` - 关系抽取

**实体类型：**
- PER: 人物
- ORG: 机构
- LOC: 地点
- TIME: 时间
- CONCEPT: 文化概念

---

### 5. SynthesisAgent - 综合分析专员

**职责：**
- 跨文档信息融合
- 主题聚类分析
- 趋势识别
- 生成综合见解

**使用方式：**
```python
from app.agents.v2.synthesis_agent import SynthesisAgent

agent = SynthesisAgent()
result = agent.run(
    project_id=123,
    analysis_type='theme'  # 'theme' | 'trend' | 'comparison'
)

# 返回
{
    'themes': [
        {'name': '传统文化保护', 'documents': [456, 457], 'score': 0.92},
        {'name': '乡村振兴', 'documents': [457, 458], 'score': 0.88}
    ],
    'insights': [
        '主题1与主题2存在强关联...'
    ]
}
```

**分析类型：**
- `theme`: 主题聚类
- `trend`: 趋势分析
- `comparison`: 对比分析

---

### 6. ReportAgent - 报告生成专员

**职责：**
- 整合所有分析结果
- 应用6大Skills（使用 `analyze_with_skills` 工具）
- 生成结构化报告
- 支持多种输出格式

**使用方式：**
```python
from app.agents.v2.report_agent import ReportAgent

agent = ReportAgent()
result = agent.run(
    project_id=123,
    enabled_skills=['heritage_dadi', 'xiangtu_china'],
    report_format='full'  # 'full' | 'summary' | 'export'
)

# 返回
{
    'report': {
        'executive_summary': '...',
        'key_findings': [...],
        'skills_analysis': {
            'heritage_dadi': {
                'findings': [...],
                'score': 85
            }
        },
        'recommendations': [...]
    },
    'metadata': {
        'generated_at': '2026-08-14T10:00:00',
        'version': '2.0'
    }
}
```

**内部使用的工具：**
- `app.tools.summary.analyze_with_skills()` - Skills分析

**可用Skills：**
1. `heritage_dadi` - 遗产大地分析
2. `business_feasibility` - 商业可行性分析
3. `multi_village_sop` - 多村落标准化分析
4. `literature_market_research` - 文献市场研究
5. `xiangtu_china` - 乡土中国理论分析
6. `sacred_memory` - 神圣记忆分析

---

## 工具函数API

### transcript工具

```python
from app.tools.transcript import transcribe_audio, clean_transcript, extract_metrics

# 转录音频
result = transcribe_audio(
    file_path: str,
    file_type: str = 'audio',
    language: str = 'auto',
    enable_metrics: bool = True,
    enable_cleaning: bool = True
) -> Dict[str, Any]

# 清洗转录文本
cleaned = clean_transcript(text: str) -> str

# 提取量化指标
metrics = extract_metrics(
    text: str,
    segments: Optional[List[Dict]] = None
) -> Dict[str, Any]
```

### entity工具

```python
from app.tools.entity import extract_entities

result = extract_entities(
    text: str,
    merge_threshold: float = 0.85,
    extract_context: bool = True
) -> Dict[str, Any]
```

### relation工具

```python
from app.tools.relation import extract_relations

result = extract_relations(
    text: str,
    entities: List[Dict[str, Any]] = None,
    max_relations: int = 100
) -> Dict[str, Any]
```

### summary工具

```python
from app.tools.summary import analyze_with_skills

result = analyze_with_skills(
    content: str,
    enabled_skills: Optional[List[str]] = None,
    report_format: str = 'full',
    include_statistics: bool = True
) -> Dict[str, Any]
```

---

## 完整工作流示例

```python
from app.agents.v2 import (
    IngestionAgent,
    ChunkingAgent,
    VectorizationAgent,
    KnowledgeAgent,
    SynthesisAgent,
    ReportAgent
)

# 1. 数据摄取
ingestion = IngestionAgent()
text_result = ingestion.run(
    project_id=123,
    file_path='/path/to/interview.mp3',
    file_type='audio'
)

# 2. 文档分块
chunking = ChunkingAgent()
chunk_result = chunking.run(
    document_id=456,
    text=text_result['text']
)

# 3. 向量化
vectorization = VectorizationAgent()
vector_result = vectorization.run(
    chunk_ids=[c['id'] for c in chunk_result['chunks']]
)

# 4. 知识构建
knowledge = KnowledgeAgent()
kg_result = knowledge.run(
    document_ids=[456],
    enable_graph=True
)

# 5. 综合分析
synthesis = SynthesisAgent()
syn_result = synthesis.run(
    project_id=123,
    analysis_type='theme'
)

# 6. 报告生成
report = ReportAgent()
final_result = report.run(
    project_id=123,
    enabled_skills=['heritage_dadi', 'xiangtu_china'],
    report_format='full'
)

print(final_result['report'])
```

---

## 错误处理

所有Agent和工具函数使用统一的错误处理：

```python
try:
    result = agent.run(...)
except ValueError as e:
    # 参数错误
    print(f"参数错误: {e}")
except FileNotFoundError as e:
    # 文件不存在
    print(f"文件未找到: {e}")
except RuntimeError as e:
    # 运行时错误
    print(f"执行失败: {e}")
except Exception as e:
    # 其他错误
    print(f"未知错误: {e}")
```

---

## 性能优化

### 1. 批量处理

```python
# 批量向量化
vectorization.run(chunk_ids=[1, 2, 3, 4, 5])  # 一次处理多个
```

### 2. 异步执行

```python
import asyncio

async def process_multiple_files():
    tasks = [
        ingestion.run_async(file_path=f)
        for f in files
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### 3. 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_entities(text: str):
    return extract_entities(text=text)
```

---

## 配置

在 `.env` 中配置：

```bash
# Whisper模型
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cpu

# Embedding模型
EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_API_KEY=sk-...

# 数据库
DATABASE_URL=postgresql://...
VECTOR_DB_URL=qdrant://localhost:6333
```

---

## 版本信息

- **当前版本**: 2.0
- **发布日期**: 2026-08-14
- **兼容性**: 向后兼容旧Agent（带废弃警告）

---

## 更新日志

### v2.0 (2026-08-14)
- ✅ 重构为6-Agent v2架构
- ✅ 提取4个核心工具函数
- ✅ 标记旧Agent为废弃
- ✅ 100%测试覆盖

### v1.x (遗留版本)
- 旧Agent架构
- Coordinator模式
- SuperAgent层

---

## 技术支持

- **迁移指南**: `MIGRATION_GUIDE_PHASE4.md`
- **测试报告**: `PHASE5_INTEGRATION_TEST_REPORT.md`
- **完成总结**: `PHASE4_5_COMPLETION_SUMMARY.md`
