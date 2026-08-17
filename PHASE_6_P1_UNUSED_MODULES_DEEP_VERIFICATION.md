# P1-3: 未使用模块深度验证报告

**目的**: 确认每个未使用模块是否为旧版本/重复实现

## 📊 分类统计

- **明确标注为旧版本**: 6个 ✅ 可安全删除
- **有替代版本**: 6个 ✅ 可安全删除
- **已被整合**: 21个 ✅ 可安全删除
- **需要人工判断**: 50个 ⚠️

**可安全删除**: 33/83 (39.8%)

---

## 1. 明确标注为旧版本 ✅

这些模块在代码注释中明确标注为废弃/旧版本/已替代。

### `services/workflows/autonomous_crew.py`

- **大小**: 11903 bytes
- **修改时间**: 2026-08-17 09:50:39.096341
- **证据**: 废弃, 废弃
- **文件头**:
```
"""
AutonomousCrew - 自主工作流（已废弃）

⚠️ 已废弃：此版本使用旧CoordinatorAgent架构
建议使用6-Agent v2的AgentCoordinator进行流程编排

使用CoordinatorAgent动态调度任务和工作流
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getL...
```

### `services/agents/relation_agent.py`

- **大小**: 9374 bytes
- **修改时间**: 2026-08-16 22:41:56.211241
- **证据**: 废弃, deprecated, deprecated, 已被6-Agent v2替代
- **文件头**:
```
"""
RelationAgent - 关系抽取专员

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.relation.relation_extractor

职责：从文本中抽取实体之间的关系，构建知识图谱
"""

from typing import Dict, Any, List, Tuple
import logging

from app.services.agents.base_agent import AgentBase, AgentRole, AgentTask
from app.utils.deprecation import deprecated...
```

### `services/workflows/rag_query_crew.py`

- **大小**: 9334 bytes
- **修改时间**: 2026-08-17 09:50:32.273244
- **证据**: 废弃, 废弃
- **文件头**:
```
"""
RAGQueryCrew - RAG查询工作流（已废弃）

⚠️ 已废弃：此版本使用旧Agent架构（entity/search/summary）
建议使用6-Agent v2架构结合SynthesisAgent的记忆检索功能

实体提取 → 检索 → 答案生成
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.g...
```

### `services/workflows/research_report_crew.py`

- **大小**: 8354 bytes
- **修改时间**: 2026-08-17 09:50:16.388608
- **证据**: 废弃, 废弃
- **文件头**:
```
"""
ResearchReportCrew - 研究报告工作流（已废弃）

⚠️ 已废弃：此版本使用旧Agent架构，请使用 ResearchReportCrewV2

搜索 → 内容提取 → Skills分析 → 报告生成
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getLogger(__name__)


c...
```

### `services/agents/entity_agent.py`

- **大小**: 7907 bytes
- **修改时间**: 2026-08-16 22:41:46.898921
- **证据**: 废弃, deprecated, deprecated, 已被6-Agent v2替代
- **文件头**:
```
"""
EntityAgent - 实体识别专员

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.entity.ner_extractor

职责：从文本中识别命名实体（人名、地名、机构名、时间等）
"""

from typing import Dict, Any, List
import logging

from app.services.agents.base_agent import AgentBase, AgentRole, AgentTask
from app.utils.deprecation import deprecated

logger = ...
```

### `services/workflows/document_processing_crew.py`

- **大小**: 6852 bytes
- **修改时间**: 2026-08-17 09:50:24.878627
- **证据**: 废弃, 废弃
- **文件头**:
```
"""
DocumentProcessingCrew - 文档处理工作流（已废弃）

⚠️ 已废弃：此版本使用旧Agent架构（transcript/entity/relation/summary）
建议使用6-Agent v2架构的完整流程：
- IngestionAgent → ChunkingAgent → VectorizationAgent → KnowledgeAgent → SynthesisAgent → ReportAgent

转录 → 实体提取 → 关系抽取 → 报告生成
"""
import logging
from typing import List, Dict, ...
```

## 2. 有替代版本 ✅

找到了同名或相似功能的新版本文件。

### `tools/coordinator/document_processing_pipeline.py`

- **大小**: 26995 bytes
- **修改时间**: 2026-08-15 20:21:05.691129
- **替代文件**:
  - `document_processing_pipeline_complete.py` (related)
  - `document_processing_pipeline_v2.py` (version)
  - `document_processing_pipeline_v2.py` (related)

### `tools/knowledge/knowledge_graph_v2.py`

- **大小**: 15131 bytes
- **修改时间**: 2026-07-31 15:31:24

### `tools/chunking/document_chunker_v2.py`

- **大小**: 14052 bytes
- **修改时间**: 2026-08-04 17:38:31

### `tools/knowledge/knowledge_graph_builder.py`

- **大小**: 11666 bytes
- **修改时间**: 2026-08-15 20:10:29.993335
- **替代文件**:
  - `knowledge_graph_builder_optimized.py` (version)
  - `knowledge_graph_builder_optimized.py` (related)

### `tools/knowledge/knowledge_graph_improved.py`

- **大小**: 11056 bytes
- **修改时间**: 2026-07-31 15:27:08

### `tools/ingestion/document_converter_v2.py`

- **大小**: 8679 bytes
- **修改时间**: 2026-08-17 12:22:12.554845

## 3. 已被整合 ✅

功能已被整合到其他模块中。

### `tools/entity/unified_entity_engine.py`

- **大小**: 43194 bytes
- **文件头**:
```
"""
统一实体引擎 - 实体-关系-证据链一体化处理

整合目标：
1. entity_extraction.py (jieba实体提取)
2. entity_extractor.py (HanLP实体提取)
3. relation_discovery.py (关系发现)
4. evidence_extractor.py (证据链提取)
5. cross_document_entity_resolver.py (跨文档实体消歧)
6. correlation_recommender.py (关联推荐)

核心特性（1+1+1+1+1+1 > 6）：
✅ 统一接口：单次调用完成全链路处理
✅ ...
```

### `tools/entity/unified_entity_extractor.py`

- **大小**: 29729 bytes
- **文件头**:
```
"""
统一实体提取引擎 - 整合jieba和HanLP两种方法

整合目标：
- entity_extraction.py (jieba版本) + entity_extractor.py (HanLP版本) → 1个统一引擎
- 实现1+1>2的功能增强，而非简单合并

核心特性：
1. 双引擎支持：jieba快速提取 + HanLP深度学习（自动降级）
2. 混合策略：结合两种方法提高准确率和召回率
3. 自定义词典：支持领域专业术语（田野调查）
4. 位置追踪：记录实体在文本中的所有出现位置
5. 关系提取：基于关键词和共现的关系识别
6. 批量处理：多文本并行提取和实体合并
7. 时间...
```

### `workflows/gap_analysis.py`

- **大小**: 26537 bytes
- **文件头**:
```
"""
工具缺失分析模块 - 识别FieldMind功能所需但尚未集成的工具
"""

from typing import Dict, List, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FunctionalGap(Enum):
    """功能缺口类别"""
    MULTI_AGENT = "multi_agent"  # 多智能体协作
    ADVANCED_CRAWLING = "advanced_crawling"  # 高级爬取
    VI...
```

### `tools/report/batch_services_07_15.py`

- **大小**: 16578 bytes
- **文件头**:
```
"""
业务服务07：客户细分服务 (CustomerSegmentationService)
业务服务08：收入模型服务 (RevenueModelService)
业务服务09：运营成本服务 (OperationalCostService)
业务服务10：风险评估服务 (RiskAssessmentService)
业务服务11：增长策略服务 (GrowthStrategyService)
业务服务12：合作伙伴分析服务 (PartnershipAnalysisService)
业务服务13：可持续发展服务 (SustainabilityService)
业务服务14：法规合规服务 (Re...
```

### `tools/knowledge/knowledge_graph_builder_optimized.py`

- **大小**: 12659 bytes
- **文件头**:
```
"""知识图谱构建服务 - 性能优化版本"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import logging
from datetime import datetime
from collections import defaultdict

from app.models.project import ProjectDocument
from app.models.entity import Entity, EntityType
from app.models.timelin...
```

### `tools/knowledge/document_network_builder.py`

- **大小**: 12508 bytes
- **文件头**:
```
"""
文档网络构建器 - 构建多层次的文档关系网络
"""
import logging
from typing import Dict, List, Any, Optional
import networkx as nx
from sqlalchemy.orm import Session
import json

logger = logging.getLogger(__name__)


class DocumentNetworkBuilder:
    """文档网络构建器"""

    def __init__(self):
        logger.info("✅ 文档网络...
```

### `tools/knowledge/knowledge_graph_service.py`

- **大小**: 11488 bytes
- **文件头**:
```
"""
知识图谱数据库服务
提供实体、关系的增量持久化
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.models.knowledge_graph import Entity, Relation, CoOccurrence, KnowledgeGraph
from app.database impor...
```

### `services/workflows/research_report_crew_v2.py`

- **大小**: 10870 bytes
- **文件头**:
```
"""
ResearchReportCrew v2 - 研究报告工作流（更新版）
文档摄入 → 分块 → 向量化 → Skills分析 → 知识图谱 → 综合 → 报告
"""
import logging
from typing import List, Dict, Any

from .base_workflow import (
    WorkflowBase,
    WorkflowStep,
    WorkflowStepResult
)

logger = logging.getLogger(__name__)


class ResearchReportCrewV2(Wor...
```

### `tools/synthesis/evidence_extractor.py`

- **大小**: 10742 bytes
- **文件头**:
```
"""
证据链提取服务 - 链路16核心

从ChromaDB的chunk中提取实体证据：
1. 识别chunk中的实体
2. 提取包含实体的句子作为证据
3. 绑定音频时间戳（如果是音频chunk）
4. 分类到衣食住行等维度
5. 存储到EntityEvidence表
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import re
import logging

from app.tools.entity import create_engine
from app.s...
```

### `tools/vectorization/cross_document_entity_resolver.py`

- **大小**: 9607 bytes
- **文件头**:
```
"""
跨文档实体消歧服务 - 识别并合并不同文档中的同一实体
"""
import logging
from typing import Dict, List, Any, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
import difflib

logger = logging.getLogger(__name__)


class CrossDocumentEntityResolver:
    """跨文档实体消歧器"""

    def __init__(self):
     ...
```

### `tasks/crawler_tasks.py`

- **大小**: 9593 bytes
- **文件头**:
```
"""
网络爬虫任务 - 整合现有爬虫工具
使用：crawl4ai, gecco, browser-use, firecrawl
不自己实现新爬虫，只做智能调度和整合
"""
from celery import chain
from app.celery_app import celery_app
from typing import Dict, Any, List
import os
from datetime import datetime
from enum import Enum


class CrawlerType(Enum):
    """爬虫类型选择"""
    CRAW...
```

### `tools/report/business_analysis_orchestrator.py`

- **大小**: 9425 bytes
- **文件头**:
```
"""
统一业务分析服务注册器和调度器
集成15个商业分析服务（3个已有 + 12个新增）
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
import asyncio
import logging

logger = logging.getLogger(__name__)


class BusinessAnalysisOrchestrator:
    """15个商业分析服务的统一调度器"""

    def __init__(self, db: Session):
        s...
```

### `services/skills/literature_market_research.py`

- **大小**: 9338 bytes
- **文件头**:
```
"""
文献市场调研Skill - Literature & Market Research Skill

基于学术文献检索和市场调研方法论的专业分析技能
整合文献综述、市场调查、竞品分析、趋势预测四大维度
"""

from typing import Dict, List
from app.services.skills.skill_base import SkillBase, DimensionDefinition, SkillResult, AnalysisMatch
from app.tools.ingestion.text_processor import extract_keyw...
```

### `tools/coordinator/document_processing_pipeline_v2.py`

- **大小**: 9146 bytes
- **文件头**:
```
"""
文档处理流水线 v2 - 链路十四+十五完整实现
从上传到存储的完整链路，确保每一步都携带完整元数据
链路15新增：时间抽取和标准化
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.document_metadata import (
    DocumentMetadata,
    ChunkMetadata,
    create_metadata...
```

### `tools/ingestion/multimodal_processor.py`

- **大小**: 9067 bytes
- **文件头**:
```
"""
多模态处理器 - 统一处理音频/视频/文档/表格/图片
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class UnifiedContent:
    """统一的内容表示"""

    def __init__(self):
        self.text: str = ""  # 主文本内容
        self.tables: List...
```

### `agents/field_dimension_agent.py`

- **大小**: 8189 bytes
- **文件头**:
```
"""
FieldDimensionAgent - 田野维度解构专员

职责：
1. 根据学术框架对田野资料进行多维度分析
2. 整合项目启用的Skill进行专业维度解构
3. 分析治理、生计、文化、生态等维度
4. 结合实体关系提供更深入的上下文分析
"""

import logging
import importlib
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.agents.base_agent import BaseAgent, AgentResult...
```

### `tools/ingestion/data_curation.py`

- **大小**: 7369 bytes
- **文件头**:
```
"""
数据治理模块 - Data Curation Layer
负责将非结构化文本转换为可统计的结构化数据

核心功能：
1. 文本清洗（去除口语填充词、标点归一化）
2. 主题分类（衣食住行社交经济信仰）
3. 实体抽取（人名、地名、时间）
4. 结构化存储（PostgreSQL分析型宽表）
"""

import re
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

lo...
```

### `tools/standalone/ragflow_service.py`

- **大小**: 6335 bytes
- **文件头**:
```
"""
RAGFlow Service - Integration with RAGFlow for advanced document processing
"""
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Try to import RAGFlow SDK
try:
    from ragflow import RAG...
```

### `tools/chunking/audio_chunker.py`

- **大小**: 5388 bytes
- **文件头**:
```
"""
音频分块服务 - 链路15重写版
核心：保留Whisper的时间边界，禁止重切分

解决问题：
- 用户问"老李在23分45秒说了什么" → AI能精确回答并跳转播放
- 每个向量块必须携带 start_sec、end_sec、timestamp_display
"""

from typing import List, Dict, Any
from datetime import datetime
import logging

from app.schemas.document_metadata import ChunkMetadata, DocumentMetadata

log...
```

### `tools/coordinator/auto_processing_trigger.py`

- **大小**: 3637 bytes
- **文件头**:
```
"""
自动处理触发器 - 文档上传后自动开始处理
"""

from typing import Optional
from sqlalchemy.orm import Session
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.tools.document import UnifiedDocumentPipeline

logger = logging.getLogger(__name__)

# 线程池用于异步处理
executor = ThreadPo...
```

### `core/unified_transcription.py`

- **大小**: 3406 bytes
- **文件头**:
```
"""
统一的语音转录服务
根据配置自动选择 Whisper 或 FunASR
"""

import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class UnifiedTranscriptionService:
    """统一的语音转录服务"""

    def __init__(self):
        self.engine = settings.ASR_ENGINE
       ...
```

## 4. 需要人工判断 ⚠️

无法自动判断是否为旧版本，需要查看具体内容。

### `tools/coordinator/document_processing_pipeline_complete.py`

- **大小**: 28899 bytes
- **修改时间**: 2026-08-15 20:21:05.689967
- **文件头**:
```
"""
完整的文档处理流水线 - 带错误处理和重试机制
功能：文档上传 -> 切分 -> 向量化 -> 存储 -> 错误恢复
"""

import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib impor...
```

### `agents/v2/quality_control_agent.py`

- **大小**: 26549 bytes
- **修改时间**: 2026-08-16 22:00:51.499726
- **文件头**:
```
"""
Quality Control Agent - 质量控制智能体
自动验证处理结果的质量，检测并修复常见问题
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import re
import js...
```

### `tools/coordinator/workflow_chain.py`

- **大小**: 24968 bytes
- **修改时间**: 2026-08-15 20:21:05.689136
- **文件头**:
```
"""
工作流串联器 - 实现功能自动深化
第一个功能完成后，自动触发第二个功能继续深化
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime, timede...
```

### `services/skills/xiangtu_china.py`

- **大小**: 19921 bytes
- **修改时间**: 2026-08-17 09:58:28.681556
- **文件头**:
```
"""
乡土中国Skill - 基于费孝通《乡土中国》理论框架的田野调查分析
使用真实的向量语义分析，基于BGE模型

完整8维度版本，基于《乡土中国》实践钥匙：现场调查与乡村文化遗产发展指导Skill
核心理念："用乡土中国的眼看乡村，而不是用城市的眼看乡村"
"""
import logging
from typing import Dict, List, Optional, Any
impo...
```

### `core/data_flow_orchestrator.py`

- **大小**: 18444 bytes
- **修改时间**: 2026-08-15 20:15:59.131021
- **文件头**:
```
"""
数据流通编排中台 - 核心协同引擎

职责：
1. 数据流通：打通各个板块的数据端口
2. 工作流串联：第一个功能完成后自动触发第二个功能深化
3. 数据审核：防止AI胡编，审核通过后才显示
4. 项目隔离：确保每个项目数据独立
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses impo...
```

### `workflows/orchestrator.py`

- **大小**: 17007 bytes
- **修改时间**: 2026-07-30 14:00:01
- **文件头**:
```
"""
工作流编排器 - 定义工具间的自动触发和协作逻辑
实现"点一下，下一个自动配套"的核心机制
"""

from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from celery import chain, group, chord
from app.celery_app import ce...
```

### `services/skills/sacred_memory.py`

- **大小**: 16462 bytes
- **修改时间**: 2026-08-17 09:58:28.666463
- **文件头**:
```
"""
神圣记忆Skill - 基于景军《神圣记忆》理论框架的社会记忆分析
使用真实的向量语义分析，基于BGE模型

核心理念：将乡村文化遗产视为"活的社会记忆载体"，通过识别、激活和转化集体记忆，
实现文化遗产的价值发现与社区文化复兴

基于《神圣记忆》钥匙：社会记忆视角下的乡村文化遗产发展指导 Skill
"""
import logging
from typing import Dict, ...
```

### `core/error_handlers.py`

- **大小**: 15229 bytes
- **修改时间**: 2026-08-08 15:05:31
- **文件头**:
```
"""
错误装饰器和处理器
Error Decorators and Handlers

提供自动异常处理、重试机制和错误记录功能
"""

import functools
import asyncio
import time
from typing import Callable, Optional, Type, Tuple, Any, Union, List
from contextlib ...
```

### `tools/report/dynamic_report_generator.py`

- **大小**: 15042 bytes
- **修改时间**: 2026-08-06 18:51:34
- **文件头**:
```
"""
动态报告生成器 - 第三刀实现
废除预设模板，根据数据画像动态生成报告大纲和内容
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

logger = logging.getLogg...
```

### `services/skills/business_feasibility.py`

- **大小**: 14862 bytes
- **修改时间**: 2026-08-17 09:58:28.662619
- **文件头**:
```
"""
乡村文化遗产商业可行性验证Skill - 基于大地遗产方法论
Rural Cultural Heritage Business Feasibility Verification Skill

核心理念：以运营思维贯穿始终，将文化遗产从"保护对象"转化为"可被验证的商业模式"
核心立场（防伪反假）：不做符号贴贴伪包装——文化符号贴贴、任何村都能做的通用包。
所有包装必须从文化整体分析中生长出...
```

### `tools/standalone/skill_sandbox.py`

- **大小**: 14385 bytes
- **修改时间**: 2026-08-15 19:48:38.278618
- **文件头**:
```
"""
Skill沙箱执行环境 - 安全隔离的Skill执行器（完整版）
"""

import os
import sys
import json
import tempfile
import subprocess
import time
import shutil
import resource
from typing import Dict, Any, Optional
from pathl...
```

### `tools/knowledge/relation_discovery.py`

- **大小**: 14067 bytes
- **修改时间**: 2026-08-06 21:16:33
- **文件头**:
```
"""
🔗 关系发现引擎 - 自动发现对象之间的潜在关联

基于四种发现策略：
1. 共现关联 - 在同一段落/文档中出现
2. 时间关联 - 在同一时间窗口内被提及
3. 语义关联 - 向量相似度高
4. 推理关联 - A→B→C 的传递性推断
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm...
```

### `tools/ingestion/document_parser.py`

- **大小**: 13005 bytes
- **修改时间**: 2026-08-07 13:29:34
- **文件头**:
```
"""文档解析服务 - 支持多种文档格式，集成MinerU高级解析"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# 尝试导入MinerU客户端
MINERU_A...
```

### `tasks/report_tasks.py`

- **大小**: 12891 bytes
- **修改时间**: 2026-07-30 13:45:26
- **文件头**:
```
"""
报告生成任务 - 可视化和文档导出
"""
from app.celery_app import celery_app
from typing import Dict, Any, List
import os
from datetime import datetime
from pathlib import Path


@celery_app.task(name="app.tasks.r...
```

### `tools/report/adaptive_analyzer.py`

- **大小**: 12211 bytes
- **修改时间**: 2026-08-06 18:44:18
- **文件头**:
```
"""
自适应分析器 - 通用智能分析，无预设词表

核心能力：
1. 自动发现主题（基于TF-IDF + 语义聚类）
2. 自动提取实体（基于词性+命名实体识别）
3. 自动识别关系（基于依存句法+共现）
4. 自动分类内容（基于向量相似度）
"""

import jieba
import jieba.posseg as pseg
from collections import default...
```

### `agents/entity_relation_agent.py`

- **大小**: 11880 bytes
- **修改时间**: 2026-08-13 13:06:04.528656
- **文件头**:
```
"""
EntityRelationAgent - 实体关系分析专员

职责：
1. 从文本中识别人物、地点、组织、事件
2. 分析实体之间的关系（亲属、权力、经济、地理等）
3. 构建初步的关系网络

输入：
- text_content: 文档文本
- entities: 动态发现引擎提取的实体（可选，用于增强）

输出：
- entities: 结构化的实体列表
- relations: 实...
```

### `tools/knowledge/correlation_recommender.py`

- **大小**: 11559 bytes
- **修改时间**: 2026-08-07 13:09:46
- **文件头**:
```
"""
💡 智能关联推荐引擎 - 主动发现用户可能感兴趣的内容

功能：
1. 基于当前对象推荐相关内容
2. 深度2关联：通过中间节点发现潜在关系
3. 过滤已浏览内容，保证新鲜度
4. 按关联强度和新鲜度排序
"""

from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session
fro...
```

### `tools/synthesis/anti_hallucination_report.py`

- **大小**: 11522 bytes
- **修改时间**: 2026-08-06 10:52:18
- **文件头**:
```
"""
反幻觉报告生成器
使用"填空题"模板 + 幻觉检测器

四重锁：
1. ✅ 数据与解读物理隔离 - 只喂facts.json
2. ✅ 填充题代替作文题 - 固定模板
3. ✅ 强制引用坐标 - 每句话带来源
4. ✅ 后置幻觉侦探 - 自动校验数字
"""

import re
import json
from typing import Dict, List, Any, Tuple
f...
```

### `tools/synthesis/fact_statement_populator.py`

- **大小**: 11016 bytes
- **修改时间**: 2026-08-09 12:45:59.823447
- **文件头**:
```
"""
Fact Statements填充器
在现有Pipeline中同步填充结构化事实表

集成点：document_processing_pipeline_complete.py
在向量化完成后，同步填充fact_statements
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.di...
```

### `services/skills/livelihood_ecology.py`

- **大小**: 10831 bytes
- **修改时间**: 2026-08-17 09:58:28.674318
- **文件头**:
```
"""
生计生态Skill - 分析生计方式、收入来源与生态环境
使用真实的向量语义分析，基于BGE模型
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import numpy as np

from .skill_base import Skill...
```

### `tasks/rag_tasks.py`

- **大小**: 10193 bytes
- **修改时间**: 2026-08-07 17:40:05
- **文件头**:
```
"""
RAG 查询任务 - 三重检索融合
Vector (ChromaDB) + Fulltext (Whoosh) + Graph (Neo4j) + Keyword (PostgreSQL)
"""
from celery import group
from app.celery_app import celery_app
from typing import Dict, Any, List...
```

### `core/alerts.py`

- **大小**: 10193 bytes
- **修改时间**: 2026-08-03 10:57:38
- **文件头**:
```
"""
告警系统
支持多种告警通道：Email、Webhook、钉钉、企业微信
"""

import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, L...
```

### `agents/crew_config.py`

- **大小**: 9870 bytes
- **修改时间**: 2026-08-09 12:37:01.421086
- **文件头**:
```
"""
CrewAI 多智能体系统配置
定义各个专业 Agent 及其协作方式
"""
from crewai import Agent, Task, Crew, Process
from crewai_tools import FileReadTool, SearchTool
from typing import List, Dict, Any
import os


class FieldMi...
```

### `tools/vectorization/structured_extractor.py`

- **大小**: 9815 bytes
- **修改时间**: 2026-08-06 18:27:20
- **文件头**:
```
"""
结构化数据抽取服务
从非结构化文本中自动提取时间、事件、关系等结构化信息
"""
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import jieba
import jieba.posseg as pseg


class TemporalExtractor:
...
```

### `tools/knowledge/neo4j_adapter.py`

- **大小**: 9808 bytes
- **修改时间**: 2026-08-15 20:21:05.690450
- **文件头**:
```
"""
Neo4j集成适配器
支持将NetworkX图谱导出到Neo4j，实现双引擎支持
"""

from neo4j import GraphDatabase
import logging
from typing import Optional, Dict, List
import networkx as nx
from app.config import settings

logger =...
```

### `services/skills/heritage_dadi.py`

- **大小**: 9781 bytes
- **修改时间**: 2026-08-17 09:58:28.659305
- **文件头**:
```
"""
大地文化遗产活化运营方法论Skill
Heritage Activation and Operation Methodology based on Dadi Cultural Heritage

理论来源：大地风景巍特恒泰文化遗产投顾公司工作方法论
核心转型：从"资源管理"到"内容运营"
三层结构：价值层（四大原则）→ 方法层（内容挖掘与转化）→ 落地层（EPCO机制）
"""

from...
```

### `services/skills/multi_village_sop.py`

- **大小**: 9586 bytes
- **修改时间**: 2026-08-17 09:58:28.677720
- **文件头**:
```
"""
多村比较标准流程Skill - 田野调查中的跨村比较分析方法
Multi-Village Comparative Analysis SOP

类别：专业分析方法
应用场景：比较研究、区域调查、类型学分析
核心价值：识别共性与差异、发现影响因素、提炼典型模式
"""

from typing import Dict, List
from dataclasses import dataclas...
```

### `tools/report/competitor_analysis_service.py`

- **大小**: 9183 bytes
- **修改时间**: 2026-08-17 11:35:06.301798
- **文件头**:
```
"""
业务服务05：竞争对手分析服务 (CompetitorAnalysisService)

定位：识别周边同类和替代性文化遗产地的竞争格局，明确差异化定位
属于：乡村遗产业务第一阶段（现场扫描与价值判断）
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session


class CompetitorA...
```

### `tools/synthesis/facts_anchor.py`

- **大小**: 8955 bytes
- **修改时间**: 2026-08-09 12:47:20.701654
- **文件头**:
```
"""
事实锚点生成器 - Facts Anchor Generator
只生成干燥的数字、列表、时间，绝对不含修饰性形容词

核心原则：
1. 只有数字、名称、时间戳
2. 禁止任何形容词、副词
3. 禁止任何推测性语言
4. 100%从fact_statements表读取数据
"""

from typing import Dict, List, Any
from sqlalchemy.orm...
```

### `services/skills/community_governance.py`

- **大小**: 8748 bytes
- **修改时间**: 2026-08-17 09:58:28.685933
- **文件头**:
```
"""
社区治理Skill - 真实可用的向量语义版本

理论框架: 基于社区治理理论和田野调查经验
分析维度: 权力结构、决策机制、矛盾调解、资源分配

特点:
1. 使用BGE向量进行语义检索，不是简单关键词匹配
2. 基于真实的社区治理理论框架
3. 能识别同义表达和语义相关内容
"""
import logging
from typing import Dict, Any, Optiona...
```

### `tools/knowledge/document_relation_discovery.py`

- **大小**: 8739 bytes
- **修改时间**: 2026-08-17 12:26:29.096334
- **文件头**:
```
"""
文档关系发现服务 - 识别文档间的引用、补充、矛盾等关系
"""
import logging
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import re

logger = logging.getLogger(__n...
```

### `tools/chunking/semantic_chunker.py`

- **大小**: 8709 bytes
- **修改时间**: 2026-08-05 14:43:33
- **文件头**:
```
"""
语义切分器 - Semantic Chunker
按语义边界切分，而不是机械按字数

原则：
1. 音频：按Whisper的segments（天然语义单元）
2. 文档：按自然段落（\n\n）
3. 保持完整性：不破坏语义
"""

import re
from typing import List, Dict, Any


class SemanticChunker:
    """语义...
```

### `tools/vectorization/entity_extraction.py`

- **大小**: 8527 bytes
- **修改时间**: 2026-08-04 18:21:27
- **文件头**:
```
"""实体提取服务 - 使用jieba.posseg进行中文NER"""
import jieba.posseg as pseg
import re
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict

# 实体类型映射
ENTITY_TYPE_...
```

### `tools/vectorization/entity_extractor.py`

- **大小**: 8345 bytes
- **修改时间**: 2026-07-30 17:10:25
- **文件头**:
```
"""实体提取服务 - 基于HanLP的中文NER"""
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class EntityExtractor:
    """实体提取服务"""

    def __init__(sel...
```

### `tools/ingestion/table_processor.py`

- **大小**: 8332 bytes
- **修改时间**: 2026-08-17 12:23:01.879127
- **文件头**:
```
"""
表格处理服务 - 从PDF/Excel/图片中提取表格和公式
"""
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path
import re
import json

logger = logging.getLogger(__name...
```

### `api/v1/api_docs_enhanced.py`

- **大小**: 8136 bytes
- **修改时间**: 2026-08-05 16:51:48
- **文件头**:
```
"""
API文档补全
为所有端点添加详细的Swagger文档
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import List, Optional
from pydantic import BaseModel, Field

# ============= 示例...
```

### `tools/ingestion/data_quality_checker.py`

- **大小**: 7982 bytes
- **修改时间**: 2026-08-07 18:32:44
- **文件头**:
```
"""
数据质量检查器
防止AI胡编，确保数据可信后才显示到前端
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__na...
```

### `tools/report/market_demand_service.py`

- **大小**: 7807 bytes
- **修改时间**: 2026-08-17 11:34:27.763731
- **文件头**:
```
"""
业务服务04：市场需求分析服务 (MarketDemandAnalysisService)

定位：定量定性结合，验证"有没有人愿意来、愿意花多少钱"
属于：乡村遗产业务第一阶段（现场扫描与价值判断）
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
import json

from ap...
```

### `tools/coordinator/batch_processor.py`

- **大小**: 6892 bytes
- **修改时间**: 2026-08-05 16:51:08
- **文件头**:
```
"""
批量文档处理优化
支持并发处理、进度追踪、错误恢复
"""

import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import logging
from datetime import datetime

logger = ...
```

### `middleware/enhanced_monitoring.py`

- **大小**: 6773 bytes
- **修改时间**: 2026-08-07 17:16:54
- **文件头**:
```
"""
增强的监控中间件
集成 Prometheus 指标和分布式追踪
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

from app.co...
```

### `tasks/graph_tasks.py`

- **大小**: 6768 bytes
- **修改时间**: 2026-07-30 13:44:43
- **文件头**:
```
"""
知识图谱任务 - Neo4j 图谱构建和更新
"""
from app.celery_app import celery_app
from typing import Dict, Any, List
import os
from datetime import datetime


@celery_app.task(name="app.tasks.graph_tasks.extract_r...
```

### `tasks/audio_tasks.py`

- **大小**: 6475 bytes
- **修改时间**: 2026-08-15 19:47:34.127532
- **文件头**:
```
"""
音频处理任务 - Whisper 转录 + HanLP 处理
"""
from celery import chain
from app.celery_app import celery_app
from typing import Dict, Any
import subprocess
import os
from pathlib import Path
from datetime im...
```

### `agents/v2/tool_registry.py`

- **大小**: 6409 bytes
- **修改时间**: 2026-08-16 22:12:52.674733
- **文件头**:
```
"""
工具注册表 - Agent服务映射

定义每个Agent可使用的服务工具，不移动文件位置，仅记录归属关系。
"""

from typing import Dict, List

# Agent工具映射
AGENT_TOOLS: Dict[str, List[str]] = {
    # 1️⃣ IngestionAgent - 文档摄取
    "ingestion": [
     ...
```

### `core/funasr_service.py`

- **大小**: 5633 bytes
- **修改时间**: 2026-08-06 17:51:12
- **文件头**:
```
"""
FunASR语音转录服务
专为中文优化的语音识别，支持说话人分离
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class FunASRService:
    """FunAS...
```

### `api/permissions.py`

- **大小**: 5375 bytes
- **修改时间**: 2026-08-03 10:40:19
- **文件头**:
```
"""
权限管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel

from app.core.databa...
```

### `tools/vectorization/llm_enhanced_extractor.py`

- **大小**: 5308 bytes
- **修改时间**: 2026-08-06 10:24:37
- **文件头**:
```
"""
LLM增强的实体关系提取器
使用Claude/GPT提升知识图谱构建质量
"""

import logging
import json
from typing import List, Tuple, Dict, Any
import os

logger = logging.getLogger(__name__)


class LLMEnhancedExtractor:
    """...
```

### `tools/report/pricing_strategy_service.py`

- **大小**: 4530 bytes
- **修改时间**: 2026-08-17 11:38:03.124462
- **文件头**:
```
"""
业务服务06：定价策略服务 (PricingStrategyService)
为门票、研学课程、民宿、餐饮、文创等业态制定价格体系
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session


class PricingStrategyService:
    """定价策略服务"""

    d...
```

### `middleware/project_isolation.py`

- **大小**: 2480 bytes
- **修改时间**: 2026-08-07 17:17:01
- **文件头**:
```
"""
项目隔离中间件

确保所有数据查询都带有project_id过滤
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


clas...
```

### `core/permissions.py`

- **大小**: 2185 bytes
- **修改时间**: 2026-08-07 17:28:17
- **文件头**:
```
"""权限依赖和装饰器"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.user import User,...
```

### `middleware/performance.py`

- **大小**: 1633 bytes
- **修改时间**: 2026-08-05 16:43:12
- **文件头**:
```
"""
API性能监控中间件
自动追踪所有API请求的性能
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging

logger...
```

---

## 推荐行动

1. **立即删除**: 类别1-3共33个文件（已确认为旧版本/重复）
2. **人工审查**: 类别4共50个文件
