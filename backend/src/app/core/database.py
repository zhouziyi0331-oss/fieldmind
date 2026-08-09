"""数据库配置和连接"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
import logging

# 数据库URL - 从环境变量或配置读取
from app.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = settings.DATABASE_URL

# 创建引擎 - 根据数据库类型调整参数
if DATABASE_URL.startswith('sqlite'):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库（创建所有表）"""
    # 导入所有模型
    from app.models.user import User
    from app.models.skill import Skill, SkillValidation
    from app.models.timeline import TimelineEvent
    from app.models.report import Report
    from app.models.industry import IndustryCategory
    from app.models.workflow import Workflow, WorkflowExecution  # 工作流模型
    from app.models.project import (
        Project, ProjectDocument, ProjectContext,
        ProjectChatSession, ProjectChatMessage, ProjectMemory
    )
    from app.models.entity import Entity
    from app.models.entity_evidence import EntityEvidence  # 链路16：证据链模型

    # 创建所有表
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 数据库表创建成功")
