#!/usr/bin/env python3
"""
直接创建所有数据库表
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.database import Base, engine
from app.models.user import User
from app.models.project import Project, ProjectDocument
from app.models.document import Document
from app.models.entity import Entity
from app.models.context import Context
from app.models.chat import ChatSession, ChatMessage
from app.models.skill import Skill
from app.models.timeline import TimelineEvent
from app.models.analysis_report import AnalysisReport
from app.models.report import Report
from app.models.industry import IndustryCategory
from app.models.knowledge_graph import KnowledgeGraph
from app.models.citation import Citation
from app.models.workflow import Workflow

# 导入其他模型
try:
    from app.models.document_relation import DocumentRelation
    from app.models.chunk_entity import ChunkEntity
    from app.models.enriched_chunk import EnrichedChunk
    from app.models.entity_alignment import EntityAlignment
    from app.models.entity_evidence import EntityEvidence
    from app.models.structured_insight import StructuredInsight
    from app.models.thinking_pattern import ThinkingPattern
    from app.models.skill_version import SkillVersion
    from app.models.batch_operation import BatchOperation
    from app.models.scheduled_task import ScheduledTask
    from app.models.pipeline_execution import PipelineExecution
    from app.models.pipeline_state import PipelineState
except ImportError as e:
    print(f"警告: 某些模型无法导入 - {e}")

print("开始创建数据库表...")
Base.metadata.create_all(bind=engine)
print("✅ 所有表创建完成!")
