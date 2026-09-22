#!/usr/bin/env python3
"""
创建知识模型数据库表
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from app.core.database import engine
from app.models.knowledge import Base, PipelineExecution, KnowledgeEntity, KnowledgeRelation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info('开始创建知识模型表...')
    try:
        Base.metadata.create_all(bind=engine, tables=[
            PipelineExecution.__table__,
            KnowledgeEntity.__table__,
            KnowledgeRelation.__table__
        ])
        logger.info('✅ 知识模型表创建完成')
        print('\n成功创建以下表:')
        print('  - pipeline_executions')
        print('  - knowledge_entities')
        print('  - knowledge_relations')
    except Exception as e:
        logger.error(f'❌ 创建表失败: {e}')
        raise
