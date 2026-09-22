#!/usr/bin/env python3
"""
直接创建所有数据库表
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.database import Base, engine

# 导入所有模型以注册到Base.metadata
import app.models.user
import app.models.project
import app.models.document
import app.models.entity
import app.models.context
import app.models.chat
import app.models.skill
import app.models.timeline
import app.models.analysis_report
import app.models.report
import app.models.industry

# 尝试导入其他模型
for model_name in ['citation', 'workflow', 'document_relation', 'chunk_entity',
                   'enriched_chunk', 'entity_alignment', 'entity_evidence',
                   'structured_insight', 'thinking_pattern', 'skill_version',
                   'batch_operation', 'scheduled_task', 'pipeline_execution', 'pipeline_state']:
    try:
        __import__(f'app.models.{model_name}')
    except ImportError as e:
        print(f"⚠️  跳过模型 {model_name}: {e}")

print("开始创建数据库表...")
Base.metadata.create_all(bind=engine)
print("✅ 所有表创建完成!")

# 显示创建的表
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\n📊 已创建 {len(tables)} 个表:")
for table in sorted(tables):
    print(f"  - {table}")
