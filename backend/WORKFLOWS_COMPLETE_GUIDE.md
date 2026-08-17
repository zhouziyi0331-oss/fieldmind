# FieldMind 工作流完整指南

**版本**: v2.0  
**更新时间**: 2024-08-14  
**状态**: Phase 6 补充文档

---

## 📋 目录

1. [概述](#概述)
2. [工作流架构](#工作流架构)
3. [核心工作流](#核心工作流)
4. [工作流类型分类](#工作流类型分类)
5. [工作流执行引擎](#工作流执行引擎)
6. [使用指南](#使用指南)
7. [扩展开发](#扩展开发)

---

## 概述

### 什么是工作流？

FieldMind采用**工作流驱动架构**，将复杂的业务逻辑分解为可复用的步骤链。每个工作流由多个Agent协同完成特定任务。

### 设计原则

1. **单一职责**: 每个工作流只负责一类任务
2. **可组合性**: 工作流可以嵌套和串联
3. **可观测性**: 每步都有进度反馈和日志
4. **容错性**: 支持重试、降级和部分失败
5. **可扩展性**: 易于添加新的步骤和Agent

---

## 工作流架构

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户请求层                                │
│  API Endpoints / CLI / Web UI / Desktop App                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     工作流协调层                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  CoordinatorAgent (自主任务分配)                         │   │
│  │  • 解析用户意图                                          │   │
│  │  • 选择合适的工作流                                      │   │
│  │  • 动态调度Agent                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Crew类    │  │  Pipeline类  │  │  Task异步   │
│  工作流     │  │  工作流      │  │  工作流     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent执行层                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │Ingestion│  │Chunking │  │Knowledge│  │Synthesis│  ...      │
│  │Agent    │  │Agent    │  │Agent    │  │Agent    │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      工具函数层                                  │
│  transcript() | entity_extract() | relation_extract() | ...     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据存储层                                    │
│  PostgreSQL | Redis | Vector Store | File System                │
└─────────────────────────────────────────────────────────────────┘
```

### 三种工作流类型对比

| 类型 | 基类 | 调度方式 | 适用场景 | 示例 |
|------|------|---------|---------|------|
| **Crew工作流** | `WorkflowBase` | Agent间协作 | 复杂多步骤任务 | 研究报告生成 |
| **Pipeline工作流** | 无基类 | 线性流水线 | 数据处理任务 | 文档处理 |
| **Task工作流** | Celery Task | 异步队列 | 耗时后台任务 | 视频处理 |

---

## 核心工作流

### 1. 文档处理流 (Document Processing)

**目标**: 从原始文档到可检索的知识库  
**类型**: Pipeline工作流  
**实现**: `UnifiedDocumentPipeline`

#### 流程图

```
输入: 上传的文档文件
  │
  ├─→ [1. 提取 Extract] ─────────────────────────┐
  │     • 文件类型识别                            │
  │     • 内容提取 (PDF/DOCX/TXT/...)           │
  │     • 元数据解析                             │
  │                                              │
  ├─→ [2. 清洗 Clean] ──────────────────────────┤
  │     • 去除噪音                               │  UnifiedDocumentPipeline
  │     • 格式标准化                             │  (同步执行)
  │     • 去重                                   │
  │                                              │
  ├─→ [3. 切分 Chunk] ──────────────────────────┤
  │     • 语义切分 (200-500字)                   │
  │     • 保留上下文                             │
  │     • 生成chunk_id                           │
  │                                              │
  ├─→ [4. 向量化 Vectorize] ─────────────────────┤
  │     • Sentence-BERT编码                      │
  │     • 生成embedding向量                      │
  │                                              │
  └─→ [5. 入库 Index] ──────────────────────────┘
        • 存储到PostgreSQL
        • 建立向量索引
        • 更新统计信息
          ↓
输出: document_id + 统计数据
```

#### 代码示例

```python
from app.tools.document import UnifiedDocumentPipeline

pipeline = UnifiedDocumentPipeline()

result = pipeline.process_document(
    document_id=123,
    file_path="/path/to/file.pdf",
    project_id=1,
    db=db_session,
    progress_callback=lambda stage, progress, msg: print(f"{stage}: {progress*100}%")
)

# result = {
#     'success': True,
#     'stages': {
#         'extract': {'text_length': 5000},
#         'clean': {'cleaned_length': 4800},
#         'chunk': {'total_chunks': 15},
#         'vectorize': {'vectorized_chunks': 15},
#         'index': {'stored_chunks': 15}
#     }
# }
```

#### 异步版本 (Celery Task)

```python
from app.tasks.document_tasks import process_document

# 提交异步任务
task = process_document.apply_async(args=[document_id])

# 查询任务状态
result = task.get()
```

---

### 2. 研究报告流 (Research Report)

**目标**: 从关键词到结构化研究报告  
**类型**: Crew工作流  
**实现**: `ResearchReportCrew`

#### 流程图

```
输入: query="乡村振兴 文化遗产"
  │
  ├─→ [1. Search] SearchAgent ──────────────────┐
  │     • 多源搜索 (学术/新闻/政策)              │
  │     • 结果去重                               │
  │     • 相关性排序                             │
  │     输出: search_results[]                   │
  │                                              │
  ├─→ [2. Analyze] AnalysisAgent ────────────────┤  ResearchReportCrew
  │     • 提取关键信息                           │  (步骤间传递上下文)
  │     • 识别主题                               │
  │     • 生成洞察                               │
  │     输出: analysis_insights[]                │
  │                                              │
  ├─→ [3. Skills] MultiSkillAgent ───────────────┤
  │     • 应用分析维度Skills                     │
  │     • 文创分析                               │
  │     • 业态分析                               │
  │     • 政策分析                               │
  │     输出: skill_results[]                    │
  │                                              │
  └─→ [4. Report] ReportAgent ───────────────────┘
        • 汇总所有结果
        • 生成Markdown报告
        • 添加引用和溯源
        输出: final_report (Markdown)
          ↓
输出: {status, report, execution_summary}
```

#### 代码示例

```python
from app.services.workflows.research_report_crew import ResearchReportCrew

crew = ResearchReportCrew()

result = crew.execute_research(
    query="乡村振兴 文化遗产",
    max_results=10,
    extract_content=True
)

# result = {
#     'status': 'success',
#     'query': '乡村振兴 文化遗产',
#     'search_summary': {...},
#     'key_insights': [...],
#     'report': '# 研究报告\n\n...',
#     'execution_summary': {
#         'total_steps': 4,
#         'successful_steps': 4,
#         'total_time': 12.5
#     }
# }
```

---

### 3. RAG查询流 (RAG Query)

**目标**: 基于知识库的智能问答  
**类型**: Crew工作流  
**实现**: `RAGQueryCrew`

#### 流程图

```
输入: question="如何保护乡村文化遗产？"
  │
  ├─→ [1. Entity Extract] EntityAgent ───────────┐
  │     • 从问题中提取实体                        │
  │     • 识别关键概念                           │
  │     • 生成搜索查询                           │
  │     输出: entities[], search_query           │
  │                                              │
  ├─→ [2. Retrieve] SearchAgent ─────────────────┤  RAGQueryCrew
  │     • 向量检索 (基于embedding)               │  (实体驱动的检索)
  │     • 关键词检索                             │
  │     • 混合排序                               │
  │     输出: relevant_chunks[]                  │
  │                                              │
  └─→ [3. Generate] SynthesisAgent ──────────────┘
        • 结合问题和检索结果
        • 生成答案
        • 添加引用来源
        输出: answer (带citation)
          ↓
输出: {status, query, answer, sources}
```

#### 代码示例

```python
from app.services.workflows.rag_query_crew import RAGQueryCrew

crew = RAGQueryCrew()

result = crew.query(
    question="如何保护乡村文化遗产？",
    max_results=5
)

# result = {
#     'status': 'success',
#     'query': '如何保护乡村文化遗产？',
#     'query_analysis': {
#         'entities': [{'entity': '乡村', 'type': 'Location'}, ...],
#         'search_query': '乡村 文化遗产 保护'
#     },
#     'retrieval': {
#         'total_results': 5,
#         'sources': [...]
#     },
#     'answer': {
#         'text': '...',
#         'citations': [...],
#         'insights': [...]
#     }
# }
```

---

### 4. 自主协作流 (Autonomous Crew)

**目标**: AI自动理解任务并选择工作流  
**类型**: Crew工作流 + 动态调度  
**实现**: `AutonomousCrew` + `CoordinatorAgent`

#### 流程图

```
输入: task_description="搜索机器学习的最新研究"
  │
  ├─→ [1. Analyze] CoordinatorAgent ─────────────┐
  │     • 解析任务意图                           │
  │     • 识别任务类型                           │
  │     • 推断最佳工作流                         │
  │     输出: inferred_workflow, entities[]      │
  │                                              │
  ├─→ [2. Select Workflow] ──────────────────────┤  AutonomousCrew
  │     决策树:                                  │  (动态工作流选择)
  │     • "搜索..." → ResearchReportCrew         │
  │     • "如何..." → RAGQueryCrew               │
  │     • "处理文档..." → DocumentPipeline       │
  │                                              │
  └─→ [3. Execute] 选中的工作流 ─────────────────┘
        • 执行对应的Crew/Pipeline
        • 返回执行结果
          ↓
输出: {status, workflow_executed, result}
```

#### 代码示例

```python
from app.services.workflows.autonomous_crew import AutonomousCrew

crew = AutonomousCrew()

result = crew.execute_autonomous(
    task_description="搜索机器学习的最新研究",
    max_results=5
)

# result = {
#     'status': 'success',
#     'task_description': '搜索机器学习的最新研究',
#     'task_analysis': {
#         'inferred_workflow': 'research_report',
#         'entities': [{'entity': '机器学习', 'type': 'Technology'}]
#     },
#     'coordination': {
#         'workflow_executed': 'ResearchReportCrew',
#         'completed_steps': 4
#     },
#     'result': {...}  # 实际工作流的输出
# }
```

---

### 5. 音频转录流 (Audio Transcript)

**目标**: 从音频文件到结构化知识  
**类型**: 混合流程 (Agent + Tool)  
**实现**: 6-Agent v2 架构

#### 流程图

```
输入: audio_file.mp3
  │
  ├─→ [1. Transcribe] IngestionAgent ────────────┐
  │     工具: transcript.audio_transcript()      │
  │     • Whisper ASR转录                        │
  │     • 时间戳对齐                             │
  │     • 语言识别                               │
  │     输出: transcript_text                    │
  │                                              │
  ├─→ [2. Entity Extract] KnowledgeAgent ────────┤  6-Agent v2流程
  │     工具: entity.entity_extract()            │  (顺序执行)
  │     • NER实体识别                            │
  │     • 实体类型分类                           │
  │     输出: entities[]                         │
  │                                              │
  ├─→ [3. Relation Extract] KnowledgeAgent ──────┤
  │     工具: relation.relation_extract()        │
  │     • 关系抽取                               │
  │     • 知识图谱构建                           │
  │     输出: relations[]                        │
  │                                              │
  └─→ [4. Report] ReportAgent ───────────────────┘
        工具: summary.generate_summary()
        • 生成摘要
        • 文化分析
        • 关键洞察
        输出: final_report
          ↓
输出: {transcript, entities, relations, report}
```

#### 代码示例

```python
from app.agents_v2.ingestion_agent import IngestionAgentV2
from app.agents_v2.knowledge_agent import KnowledgeAgentV2
from app.agents_v2.report_agent import ReportAgentV2

# Step 1: 转录
ingestion = IngestionAgentV2()
transcript_result = ingestion.process_audio(audio_path)

# Step 2: 实体提取
knowledge = KnowledgeAgentV2()
entity_result = knowledge.extract_entities(transcript_result['text'])

# Step 3: 关系抽取
relation_result = knowledge.extract_relations(
    transcript_result['text'],
    entity_result['entities']
)

# Step 4: 生成报告
report = ReportAgentV2()
final_report = report.generate_report({
    'transcript': transcript_result,
    'entities': entity_result,
    'relations': relation_result
})
```

---

### 6. 提案生成流 (Proposal Generation)

**目标**: 从项目数据到可汇报的提案  
**类型**: Pipeline工作流  
**实现**: API endpoint + 多Agent协作

#### 流程图

```
输入: project_id=1, proposal_type="government"
  │
  ├─→ [1. Gather Context] ───────────────────────┐
  │     • 查询项目文档                           │
  │     • 查询分析结果                           │
  │     • 查询chunks和实体                       │
  │     输出: project_context                    │
  │                                              │
  ├─→ [2. Analyze] Skills应用 ────────────────────┤  ProposalFlow
  │     • 文创分析                               │  (数据汇聚 → 分析 → 生成)
  │     • 业态分析                               │
  │     • 政策分析                               │
  │     输出: analysis_results                   │
  │                                              │
  ├─→ [3. Structure] ReportAgent ─────────────────┤
  │     • 确定提案结构                           │
  │     • 分配章节                               │
  │     输出: proposal_structure                 │
  │                                              │
  └─→ [4. Generate] SynthesisAgent ───────────────┘
        • 生成各章节内容
        • 添加预算和风险分析
        • 格式化为Markdown
        输出: final_proposal.md
          ↓
输出: {proposal: {title, type, sections, markdown}}
```

#### 代码示例

```python
# API调用
import requests

response = requests.post(
    "http://localhost:8000/api/proposal/projects/1/generate",
    json={
        'proposal_type': 'government',
        'include_budget': True,
        'include_risk': True
    }
)

result = response.json()
proposal = result['proposal']

print(proposal['title'])
print(proposal['markdown'])

# proposal = {
#     'title': '某某项目实施方案',
#     'type': 'government',
#     'sections': [
#         {'title': '项目背景', 'content': '...'},
#         {'title': '实施方案', 'content': '...'},
#         ...
#     ],
#     'markdown': '# 某某项目实施方案\n\n...'
# }
```

---

### 7. 视频处理流 (Video Processing)

**目标**: 从视频文件到多模态知识  
**类型**: Task异步工作流  
**实现**: Celery Task + VideoProcessor

#### 流程图

```
输入: video_file.mp4
  │
  ├─→ [1. Audio Extract] ────────────────────────┐
  │     • FFmpeg提取音轨                         │
  │     输出: audio.mp3                          │
  │                                              │
  ├─→ [2. Frame Extract] ────────────────────────┤
  │     • 关键帧提取                             │  VideoProcessingTask
  │     • 场景检测                               │  (异步后台执行)
  │     输出: frames[]                           │
  │                                              │
  ├─→ [3. Transcribe] → 音频转录流 ──────────────┤
  │     复用音频转录流程                         │
  │     输出: transcript, entities, relations    │
  │                                              │
  ├─→ [4. Vision Analysis] (可选) ───────────────┤
  │     • 图像识别                               │
  │     • OCR文字识别                            │
  │     输出: visual_elements[]                  │
  │                                              │
  └─→ [5. Merge] ────────────────────────────────┘
        • 合并音频和视觉信息
        • 时间戳对齐
        输出: multimodal_result
          ↓
输出: {video_id, transcript, frames, analysis}
```

#### 代码示例

```python
from app.tasks.audio_tasks import process_video

# 提交异步任务
task = process_video.apply_async(args=[video_id])

# 轮询任务状态
while not task.ready():
    status = task.info
    print(f"Progress: {status.get('progress', 0)}%")
    time.sleep(2)

result = task.get()
```

---

### 8. 批量导入流 (Batch Import)

**目标**: 批量处理多个文件  
**类型**: Pipeline工作流 + 并发控制  
**实现**: 自定义Pipeline

#### 流程图

```
输入: file_list = [file1.pdf, file2.docx, ...]
  │
  ├─→ [1. Validate] ─────────────────────────────┐
  │     • 检查文件存在性                         │
  │     • 检查格式支持                           │
  │     • 检查文件大小                           │
  │     输出: valid_files[]                      │
  │                                              │
  ├─→ [2. Parallel Process] ─────────────────────┤  BatchImportPipeline
  │     并发执行 (max_workers=5):                │  (并发 + 进度聚合)
  │     for each file:                           │
  │       → UnifiedDocumentPipeline              │
  │     输出: processed_results[]                │
  │                                              │
  ├─→ [3. Aggregate] ────────────────────────────┤
  │     • 汇总统计                               │
  │     • 错误收集                               │
  │     输出: summary                            │
  │                                              │
  └─→ [4. Notify] ───────────────────────────────┘
        • 发送完成通知
        • 更新项目统计
          ↓
输出: {total, success, failed, summary}
```

#### 代码示例

```python
from concurrent.futures import ThreadPoolExecutor
from app.tools.document import UnifiedDocumentPipeline

def batch_import(file_paths, project_id, max_workers=5):
    pipeline = UnifiedDocumentPipeline()
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for file_path in file_paths:
            future = executor.submit(
                pipeline.process_document,
                file_path=file_path,
                project_id=project_id
            )
            futures.append(future)
        
        for future in futures:
            results.append(future.result())
    
    return {
        'total': len(file_paths),
        'success': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        'results': results
    }
```

---

## 工作流类型分类

### 按执行模式分类

| 类别 | 执行方式 | 优点 | 缺点 | 适用场景 |
|------|---------|------|------|---------|
| **同步流程** | 阻塞等待完成 | 简单直接、易于调试 | 占用连接、超时风险 | 快速处理(<30s) |
| **异步流程** | 后台队列执行 | 不阻塞、可扩展 | 复杂度高、状态管理 | 耗时任务(>30s) |
| **流式流程** | 逐步返回结果 | 用户体验好 | 实现复杂 | 实时反馈场景 |

### 按协作模式分类

| 类别 | 协作方式 | 数据传递 | 示例 |
|------|---------|---------|------|
| **串行流程** | 步骤顺序执行 | 上一步输出 → 下一步输入 | 文档处理流 |
| **并行流程** | 步骤同时执行 | 共享输入、独立输出 | 多维度分析 |
| **条件流程** | 根据结果分支 | 动态路由 | 自主协作流 |
| **循环流程** | 迭代优化 | 反馈循环 | 质量检查流 |

---

## 工作流执行引擎

### WorkflowBase基类

所有Crew工作流继承 `WorkflowBase`，提供统一的执行框架。

#### 核心概念

```python
from app.services.workflows.base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowInput,
    WorkflowResult,
    WorkflowStatus
)

class MyCustomWorkflow(WorkflowBase):
    def name(self) -> str:
        return "MyCustomWorkflow"
    
    def description(self) -> str:
        return "这是一个自定义工作流"
    
    def _define_steps(self) -> List[WorkflowStep]:
        return [
            WorkflowStep(
                step_id="step1",
                step_name="第一步",
                agent_type="search",
                input_mapping={"query": "user_query"},
                output_mapping={"results": "search_results"},
                required=True,
                retry_on_failure=True,
                max_retries=3
            ),
            WorkflowStep(
                step_id="step2",
                step_name="第二步",
                agent_type="summary",
                input_mapping={"text": "search_results"},
                output_mapping={"summary": "final_summary"},
                required=False
            )
        ]
```

#### 执行流程

```python
# 1. 创建工作流实例
workflow = MyCustomWorkflow()

# 2. 准备输入
workflow_input = WorkflowInput(
    workflow_id=workflow.workflow_id,
    input_data={'user_query': '乡村振兴'},
    config={'max_results': 10}
)

# 3. 执行
result = workflow.execute(workflow_input)

# 4. 检查结果
if result.success:
    print(f"✓ 工作流完成，耗时 {result.total_execution_time:.2f}秒")
    print(f"  完成步骤: {len([r for r in result.steps_results if r.success])}/{len(result.steps_results)}")
    print(f"  最终输出: {result.final_output}")
else:
    print(f"✗ 工作流失败")
    for error in result.errors:
        print(f"  - {error}")
```

#### 关键特性

1. **步骤管理**
   - 定义步骤顺序
   - 配置输入输出映射
   - 标记必需/可选步骤

2. **上下文传递**
   - 步骤间自动传递数据
   - 通过 `input_mapping` 和 `output_mapping` 控制
   - 维护全局 `context` 字典

3. **Agent池**
   - 自动管理Agent实例
   - 复用已创建的Agent
   - 减少初始化开销

4. **容错机制**
   - 可选步骤失败不影响整体
   - 支持重试配置
   - 详细的错误日志

5. **可观测性**
   - 每步执行时间
   - 成功/失败状态
   - 错误和警告收集

---

## 使用指南

### 场景1: 上传文档并处理

```python
# Step 1: 上传文件 (API)
files = {'file': open('interview.docx', 'rb')}
response = requests.post(
    'http://localhost:8000/api/documents/upload',
    files=files,
    data={'project_id': 1}
)
document_id = response.json()['id']

# Step 2: 处理文档 (同步)
from app.tools.document import UnifiedDocumentPipeline

pipeline = UnifiedDocumentPipeline()
result = pipeline.process_document(
    document_id=document_id,
    file_path=document.file_path,
    project_id=1,
    db=db_session
)

print(f"处理完成: {result['stages']['chunk']['total_chunks']} chunks")
```

### 场景2: 生成研究报告

```python
from app.services.workflows.research_report_crew import ResearchReportCrew

crew = ResearchReportCrew()

result = crew.execute_research(
    query="非遗数字化保护",
    max_results=15,
    extract_content=True
)

# 保存报告
with open('research_report.md', 'w', encoding='utf-8') as f:
    f.write(result['report'])

print(f"报告已生成，共 {len(result['key_insights'])} 条洞察")
```

### 场景3: 智能问答

```python
from app.services.workflows.rag_query_crew import RAGQueryCrew

crew = RAGQueryCrew()

result = crew.query(
    question="布依族有哪些重要的文化遗产？",
    max_results=5
)

print(f"答案: {result['answer']['text']}")
print(f"来源: {len(result['retrieval']['sources'])} 个文档")
```

### 场景4: 让AI自主选择工作流

```python
from app.services.workflows.autonomous_crew import AutonomousCrew

crew = AutonomousCrew()

result = crew.execute_autonomous(
    task_description="帮我搜索一下乡村旅游的成功案例"
)

print(f"AI选择的工作流: {result['coordination']['workflow_executed']}")
print(f"执行结果: {result['status']}")
```

### 场景5: 异步处理视频

```python
from app.tasks.audio_tasks import process_video

# 提交异步任务
task = process_video.apply_async(
    args=[video_id],
    kwargs={'extract_frames': True}
)

print(f"任务ID: {task.id}")

# 查询状态 (在另一个请求中)
from celery.result import AsyncResult

task_result = AsyncResult(task.id)
if task_result.ready():
    result = task_result.get()
    print(f"视频处理完成: {result}")
else:
    print(f"处理中: {task_result.info}")
```

---

## 扩展开发

### 创建新的Crew工作流

```python
from app.services.workflows.base_workflow import WorkflowBase, WorkflowStep
from typing import List

class DataAnalysisCrew(WorkflowBase):
    """数据分析工作流"""
    
    def name(self) -> str:
        return "DataAnalysisCrew"
    
    def description(self) -> str:
        return "对项目数据进行多维度分析"
    
    def _define_steps(self) -> List[WorkflowStep]:
        return [
            WorkflowStep(
                step_id="gather",
                step_name="收集数据",
                agent_type="search",
                input_mapping={"project_id": "project_id"},
                output_mapping={"data": "raw_data"},
                required=True
            ),
            WorkflowStep(
                step_id="analyze",
                step_name="分析数据",
                agent_type="analysis",
                input_mapping={"data": "raw_data"},
                output_mapping={"insights": "analysis_insights"},
                required=True
            ),
            WorkflowStep(
                step_id="visualize",
                step_name="可视化",
                agent_type="visualization",
                input_mapping={"insights": "analysis_insights"},
                output_mapping={"charts": "visualization_charts"},
                required=False
            )
        ]
    
    def execute_analysis(self, project_id: int):
        """便捷执行方法"""
        from app.services.workflows.base_workflow import WorkflowInput
        
        workflow_input = WorkflowInput(
            workflow_id=self.workflow_id,
            input_data={'project_id': project_id}
        )
        
        return self.execute(workflow_input)
```

### 创建新的Pipeline工作流

```python
class ImageProcessingPipeline:
    """图像处理流水线"""
    
    def process_image(self, image_path: str, project_id: int):
        """
        图像处理流程: 读取 → 识别 → 提取 → 存储
        """
        result = {
            'success': True,
            'stages': {}
        }
        
        try:
            # Stage 1: 读取图像
            image = self._load_image(image_path)
            result['stages']['load'] = {'loaded': True}
            
            # Stage 2: OCR识别
            text = self._ocr_extract(image)
            result['stages']['ocr'] = {'text_length': len(text)}
            
            # Stage 3: 对象识别
            objects = self._object_detection(image)
            result['stages']['detection'] = {'object_count': len(objects)}
            
            # Stage 4: 存储
            stored = self._store_results(project_id, text, objects)
            result['stages']['store'] = {'stored': stored}
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def _load_image(self, image_path):
        from PIL import Image
        return Image.open(image_path)
    
    def _ocr_extract(self, image):
        # 使用OCR工具提取文字
        pass
    
    def _object_detection(self, image):
        # 使用视觉模型识别对象
        pass
    
    def _store_results(self, project_id, text, objects):
        # 存储到数据库
        pass
```

### 添加新的Agent类型

如果需要新的Agent类型，需要在 `WorkflowBase._create_agent()` 中注册：

```python
# 在 base_workflow.py 中
def _create_agent(self, agent_type: str):
    """创建Agent实例"""
    if agent_type == 'transcript':
        from app.services.agents.transcript_agent import TranscriptAgent
        return TranscriptAgent()
    elif agent_type == 'my_new_agent':
        from app.services.agents.my_new_agent import MyNewAgent
        return MyNewAgent()
    # ... 其他Agent类型
    else:
        raise ValueError(f'未知的Agent类型: {agent_type}')
```

---

## 最佳实践

### 1. 工作流设计原则

- ✅ **单一职责**: 每个工作流只做一件事
- ✅ **可组合性**: 大工作流由小工作流组合
- ✅ **幂等性**: 相同输入产生相同输出
- ✅ **容错性**: 优雅处理错误
- ✅ **可观测性**: 提供详细的日志和进度

### 2. 性能优化

- **并行执行**: 无依赖的步骤并行执行
- **缓存结果**: 相同输入缓存输出
- **批量处理**: 合并小任务
- **异步执行**: 耗时任务放后台
- **资源池**: 复用Agent和数据库连接

### 3. 错误处理

```python
# 错误处理示例
try:
    result = pipeline.process_document(...)
    if not result['success']:
        # 记录失败原因
        logger.error(f"处理失败: {result.get('error')}")
        # 尝试降级方案
        result = fallback_process(...)
except Exception as e:
    # 捕获异常
    logger.exception(f"意外错误: {str(e)}")
    # 通知管理员
    notify_admin(f"Critical error in workflow: {str(e)}")
```

### 4. 监控和调试

```python
# 添加进度回调
def progress_callback(stage, progress, message):
    print(f"[{stage}] {progress*100:.1f}% - {message}")
    # 发送到监控系统
    metrics.gauge('workflow.progress', progress, tags=[f'stage:{stage}'])

pipeline.process_document(
    document_id=123,
    progress_callback=progress_callback
)
```

---

## 工作流对比矩阵

| 工作流 | 类型 | 输入 | 输出 | 平均耗时 | 适用场景 |
|--------|------|------|------|---------|---------|
| 文档处理流 | Pipeline | 文档文件 | chunks + vectors | 5-30s | 文档上传后处理 |
| 研究报告流 | Crew | 关键词 | Markdown报告 | 10-60s | 生成研究报告 |
| RAG查询流 | Crew | 问题 | 答案+来源 | 2-10s | 智能问答 |
| 自主协作流 | Crew | 任务描述 | 动态结果 | 变化 | AI自主决策 |
| 音频转录流 | Agent链 | 音频文件 | 转录+知识 | 30-300s | 访谈记录处理 |
| 提案生成流 | Pipeline | project_id | Markdown提案 | 10-30s | 生成汇报材料 |
| 视频处理流 | Task | 视频文件 | 多模态数据 | 2-30min | 视频资料处理 |
| 批量导入流 | Pipeline | 文件列表 | 统计结果 | 变化 | 批量上传 |

---

## 附录

### A. 完整文件清单

#### Crew工作流
- `/app/services/workflows/base_workflow.py` - Workflow基类
- `/app/services/workflows/research_report_crew.py` - 研究报告流
- `/app/services/workflows/rag_query_crew.py` - RAG查询流
- `/app/services/workflows/autonomous_crew.py` - 自主协作流
- `/app/services/workflows/document_processing_crew.py` - 文档处理Crew版

#### Pipeline实现
- `/app/tools/document/unified_pipeline.py` - 文档处理Pipeline
- `/app/services/video_processor.py` - 视频处理Pipeline

#### Task实现
- `/app/tasks/document_tasks.py` - 文档异步任务
- `/app/tasks/audio_tasks.py` - 音频/视频异步任务
- `/app/tasks/report_tasks.py` - 报告生成异步任务

#### 测试文件
- `/tests/test_workflows.py` - 工作流测试
- `/demo_complete_workflow.py` - 完整流程演示

### B. 相关文档

- [API_DOCUMENTATION_V2.md](API_DOCUMENTATION_V2.md) - API文档
- [ARCHITECTURE_DIAGRAM_V2.md](ARCHITECTURE_DIAGRAM_V2.md) - 架构图
- [MIGRATION_GUIDE_PHASE4.md](MIGRATION_GUIDE_PHASE4.md) - 迁移指南
- [6_AGENT_ARCHITECTURE_COMPLETE.md](6_AGENT_ARCHITECTURE_COMPLETE.md) - 6-Agent架构

### C. 术语表

- **Crew**: 多Agent协作的工作流类型，基于WorkflowBase
- **Pipeline**: 线性流水线工作流，通常是数据处理任务
- **Task**: 异步后台任务，基于Celery
- **Step**: 工作流中的单个步骤
- **Agent**: 执行特定任务的智能单元
- **Tool**: 可复用的功能函数
- **Context**: 工作流执行时的上下文数据
- **Mapping**: 步骤间的数据映射关系

---

**文档版本**: v2.0  
**最后更新**: 2024-08-14  
**维护者**: FieldMind开发团队

如有问题，请查阅 [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) 或提issue。
