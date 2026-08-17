"""
FieldMind Backend - FastAPI Application
田野调查知识管理系统 - 主应用入口
"""

from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import traceback
import logging

from contextlib import asynccontextmanager

from app.config import settings
from app.contracts import error_response, ErrorCodes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.api.v1 import (
    audio, documents as v1_documents, search, rag,
    auth, crawler, skills, industry, reports, enhanced_chat,
    projects as v1_projects, project_chat, project_documents, super_agents
)
from app.api import (
    chat,
    documents,
    keyword_search,
    creative_analysis,
    business_analysis,
    document_processing,
    conversation_memory
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    print("🚀 FieldMind Backend 启动中...")
    print(f"📝 API文档: http://{settings.HOST}:{settings.PORT}/docs")

    # 初始化数据库
    try:
        from app.core.database import init_db
        init_db()
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"⚠️  数据库初始化警告: {e}")

    yield

    # 关闭
    print("👋 FieldMind Backend 关闭中...")
    # 清理资源


# 创建FastAPI应用
app = FastAPI(
    title="FieldMind API",
    description="田野调查知识管理系统 - AI后端服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ============= 全局异常拦截器（杀死"假装成功"） =============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器

    规则：
    1. 打印完整堆栈到终端（方便调试）
    2. 返回HTTP 500，且错误信息必须具体
    3. 严禁返回"系统繁忙"等模糊信息
    """
    # 打印完整堆栈
    logger.error(f"全局异常捕获: {str(exc)}")
    logger.error(traceback.format_exc())

    # 返回具体错误信息
    return JSONResponse(
        status_code=500,
        content=error_response(
            code=ErrorCodes.INTERNAL_ERROR,
            message=f"服务器内部错误: {str(exc)}"
        )
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            code=exc.status_code,
            message=str(exc.detail)
        )
    )


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    logger.info(f"收到请求: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        logger.info(f"响应状态: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"请求处理异常: {str(e)}")
        raise

# ============= 结束全局异常拦截器 =============

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 性能监控中间件
try:
    from app.middleware.performance import PerformanceMiddleware
    app.add_middleware(PerformanceMiddleware)
    logger.info("✅ 性能监控中间件已加载")
except ImportError:
    logger.warning("⚠️ 性能监控中间件未找到")

# 注册路由
# 认证系统 (v1版本)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证(v1)"])

# 认证系统 (新版本，直接使用v1的auth，只是改变前缀)
# REMOVED: app.include_router(auth.router, prefix="/api/auth", tags=["认证"], include_in_schema=False)  # 重复路由，已使用v1版本

# 新的项目管理系统（带Mem0长记忆和智能Agent）
# REMOVED: app.include_router(projects.router, prefix="/api/projects", tags=["项目管理(新)"])  # 重复路由，已使用v1版本
app.include_router(chat.router, prefix="/api/chat", tags=["智能对话"])

# RAG对话路由（真正的向量检索）
from app.api import chat_rag
app.include_router(chat_rag.router, prefix="/api/chat-rag", tags=["RAG对话"])

# 报告生成路由（真实数据）
from app.api import reports_real
app.include_router(reports_real.router, prefix="/api/reports", tags=["报告生成"])

# Skill配置管理路由（旧版 - 待废弃）
from app.api import skill_config
app.include_router(skill_config.router, prefix="/api/skills-old", tags=["Skill配置(旧)"])

# Skills分析路由（新版 - 6个学术方法论）
from app.api.routes import skills as skills_new
app.include_router(skills_new.router, tags=["Skills学术分析"])

# Dashboard统计路由
from app.api import dashboard
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# 批量处理路由
from app.api import batch_processing
app.include_router(batch_processing.router, prefix="/api/batch", tags=["批量处理"])

# 知识图谱路由（链路十一）
from app.api import knowledge_graph as kg_new
app.include_router(kg_new.router, prefix="/api/knowledge-graph", tags=["知识图谱"])

# 知识图谱v2路由（NetworkX增强版）
try:
    from app.api.v1 import knowledge_graph_api
    app.include_router(knowledge_graph_api.router, prefix="/api/knowledge-graph-v2", tags=["知识图谱v2"])
    logger.info("✅ 知识图谱v2 API已加载")
except ImportError as e:
    logger.warning(f"⚠️ 知识图谱v2 API未找到: {e}")

# 时间线路由（链路十一）
from app.api import timeline as timeline_new
app.include_router(timeline_new.router, prefix="/api/timeline", tags=["时间线"])

# 工作流路由（链路十二）
from app.api import workflows as workflows_new
app.include_router(workflows_new.router, prefix="/api/workflows", tags=["工作流编排"])

# 工作流v2路由（使用6-Agent v2架构）
from app.api import workflows_v2 as workflows_v2_new
app.include_router(workflows_v2_new.router, tags=["工作流v2-6Agent架构"])

# 记忆管理路由（链路十三）
from app.api import memory as memory_new
app.include_router(memory_new.router, prefix="/api/memory", tags=["记忆管理"])

# 文档处理v2路由（链路十四）
from app.api import document_processing_v2
app.include_router(document_processing_v2.router, prefix="/api/document-processing-v2", tags=["文档处理v2-引用溯源"])

# 知识图谱v3路由（链路十六：证据链绑定）- 未使用，隐藏不在API文档显示
from app.api import knowledge_graph_v3
app.include_router(knowledge_graph_v3.router, prefix="/api/knowledge-graph-v3", tags=["知识图谱v3-证据链"], include_in_schema=False)

# 🔪 破茧三刀：动态发现API（零硬编码）
from app.api import dynamic_discovery_api
app.include_router(dynamic_discovery_api.router, prefix="/api/dynamic-discovery", tags=["🔪破茧三刀-动态发现"])

# 🧠 数据联邦：四层关联智能中控
from app.api import federation_api
app.include_router(federation_api.router, prefix="/api/federation", tags=["🧠数据联邦-关联智能"])

# 分层检索路由（链路十七：报告优先级）
from app.api import hierarchical_retrieval
app.include_router(hierarchical_retrieval.router, prefix="/api/hierarchical-retrieval", tags=["分层检索-报告优先级"])

# 数据分析路由（基于SQL聚合，非向量检索）
from app.api import analytics
app.include_router(analytics.router, prefix="/api/analytics", tags=["数据分析-SQL聚合"])

# 数据聚合路由（统一数据快照，解决模块间数据不一致）
from app.api import aggregate
app.include_router(aggregate.router, prefix="/api/aggregate", tags=["数据聚合"])

# 文献引用管理路由
from app.api import citations
app.include_router(citations.router, prefix="/api", tags=["文献引用"])

# 照片管理路由（带EXIF支持）
from app.api import photos
app.include_router(photos.router, prefix="/api", tags=["照片管理"])

# 文件管理路由（虚拟文件夹）
from app.api import file_manager
app.include_router(file_manager.router, prefix="/api", tags=["文件管理"])

app.include_router(documents.router, prefix="/api/documents", tags=["文档管理(新)"])
app.include_router(keyword_search.router, prefix="/api/keyword-search", tags=["关键词检索"])
app.include_router(creative_analysis.router, prefix="/api/creative-analysis", tags=["文创分析"])
app.include_router(business_analysis.router, prefix="/api/business-analysis", tags=["业态分析"])
app.include_router(document_processing.router, prefix="/api/document-processing", tags=["文档处理流水线"])
app.include_router(conversation_memory.router, prefix="/api/conversation-memory", tags=["对话增强记忆"])

# 核心功能路由
app.include_router(v1_projects.router, prefix="/api/v1/projects", tags=["项目管理"])
app.include_router(project_chat.router, prefix="/api/v1/projects", tags=["项目对话"])
app.include_router(project_documents.router, prefix="/api/v1/projects", tags=["项目文档"])
app.include_router(skills.router, prefix="/api/v1/skills", tags=["技能管理"])
app.include_router(industry.router, prefix="/api/v1/industry", tags=["业态分析"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["报告生成"])
app.include_router(enhanced_chat.router, prefix="/api/v1", tags=["增强对话"])

# 原有路由
app.include_router(audio.router, prefix="/api/v1/audio", tags=["音频"])
app.include_router(v1_documents.router, prefix="/api/v1/documents", tags=["文档"])
app.include_router(crawler.router, prefix="/api/v1/crawler", tags=["爬虫"])
app.include_router(search.router, prefix="/api/v1/search", tags=["搜索"])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"])
# REMOVED: app.include_router(v1_workflows.router, prefix="/api/v1/workflows", tags=["工作流"])  # 未使用，已被workflows.py和workflows_v2.py替代

# SuperAgents API (Phase 3)
app.include_router(super_agents.router, tags=["SuperAgents"])
logger.info("✅ SuperAgents API已加载")


# ============= 前后端兼容层 =============
# 前端调用的路径与后端注册的路径不完全匹配，这里添加兼容路由

from fastapi import Depends, Query
from app.core.database import get_db
from sqlalchemy.orm import Session
from typing import Optional

# 1. 项目管理无版本号兼容路由（前端调用 /api/projects/）
app.include_router(v1_projects.router, prefix="/api/projects", tags=["项目管理(兼容)"], include_in_schema=False)

# 2. 项目文档兼容路由
@app.get("/api/projects/{project_id}/documents")
async def get_project_documents_compat(
    project_id: int,
    db: Session = Depends(get_db)
):
    """兼容路由：前端调用 /api/projects/{project_id}/documents"""
    from app.models.document import Document
    from app.models.project import ProjectDocument

    # 查询项目的所有文档
    documents = db.query(Document).join(
        ProjectDocument, Document.id == ProjectDocument.document_id
    ).filter(
        ProjectDocument.project_id == project_id
    ).all()

    return documents

# 3. 项目上下文兼容路由
@app.get("/api/projects/{project_id}/contexts")
async def get_project_contexts_compat(
    project_id: int,
    db: Session = Depends(get_db)
):
    """兼容路由：前端调用 /api/projects/{project_id}/contexts"""
    from app.models.project import ProjectContext

    contexts = db.query(ProjectContext).filter(ProjectContext.project_id == project_id).all()
    return contexts

# 4. 项目统计兼容路由
@app.get("/api/projects/{project_id}/stats")
async def get_project_stats_compat(
    project_id: int,
    db: Session = Depends(get_db)
):
    """兼容路由：前端调用 /api/projects/{project_id}/stats - Dashboard统计"""
    from app.models.document import Document
    from app.models.project import ProjectDocument
    from app.models.entity import Entity
    from sqlalchemy import func, distinct
    from datetime import datetime, timedelta

    # 统计文档数量
    total_documents = db.query(func.count(ProjectDocument.id)).filter(
        ProjectDocument.project_id == project_id
    ).scalar() or 0

    # 统计实体数量（从项目文档中提取）
    total_entities = db.query(func.count(Entity.id)).filter(
        Entity.project_id == project_id
    ).scalar() or 0

    # 统计关键词数量（从实体中提取唯一的名称）
    total_keywords = db.query(func.count(distinct(Entity.name))).filter(
        Entity.project_id == project_id
    ).scalar() or 0

    # 最近7天上传的文档数
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_uploads = db.query(func.count(ProjectDocument.id)).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.created_at >= seven_days_ago
    ).scalar() or 0

    # 文档类型分布
    doc_types = db.query(
        ProjectDocument.file_type,
        func.count(ProjectDocument.id).label('count')
    ).filter(
        ProjectDocument.project_id == project_id
    ).group_by(ProjectDocument.file_type).all()

    document_types = {doc_type or "unknown": count for doc_type, count in doc_types}

    # 实体类型分布
    entity_types_data = db.query(
        Entity.entity_type,
        func.count(Entity.id).label('count')
    ).filter(
        Entity.project_id == project_id
    ).group_by(Entity.entity_type).all()

    entity_types = {entity_type or "unknown": count for entity_type, count in entity_types_data}

    # 每日上传趋势（最近30天）
    thirty_days_ago = datetime.now() - timedelta(days=30)
    daily_uploads = db.query(
        func.date(ProjectDocument.created_at).label('date'),
        func.count(ProjectDocument.id).label('count')
    ).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.created_at >= thirty_days_ago
    ).group_by(func.date(ProjectDocument.created_at)).all()

    upload_trend = [
        {"date": str(date), "count": count}
        for date, count in daily_uploads
    ]

    return {
        "total_documents": total_documents,
        "total_entities": total_entities,
        "total_keywords": total_keywords,
        "recent_uploads": recent_uploads,
        "document_types": document_types,
        "entity_types": entity_types,
        "upload_trend": upload_trend,
        "storage_used": 0,  # TODO: 实现存储统计
        "last_analysis_time": None  # TODO: 实现分析时间追踪
    }

# 5. 知识图谱兼容路由（前端调用 /api/graph/*）
@app.post("/api/graph/build")
async def build_graph_compat(
    request: dict,
    db: Session = Depends(get_db)
):
    """兼容路由：前端调用 /api/graph/build"""
    from app.api import knowledge_graph as kg_api

    project_id = request.get("project_id")
    document_ids = request.get("document_ids")

    # 调用真实的知识图谱构建API
    try:
        return await kg_api.build_knowledge_graph(
            project_id=project_id,
            document_ids=document_ids,
            db=db
        )
    except Exception as e:
        # 如果knowledge_graph API不存在，返回基本的实体关系图
        from app.models.entity import Entity
        from app.models.project import ProjectDocument

        query = db.query(Entity).join(
            ProjectDocument, Entity.document_id == ProjectDocument.id
        ).filter(ProjectDocument.project_id == project_id)

        if document_ids:
            query = query.filter(ProjectDocument.id.in_(document_ids))

        entities = query.limit(100).all()

        nodes = [
            {
                "id": str(entity.id),
                "label": entity.name,
                "type": entity.entity_type or "unknown"
            }
            for entity in entities
        ]

        return {
            "nodes": nodes,
            "edges": [],
            "statistics": {
                "node_count": len(nodes),
                "edge_count": 0
            }
        }

@app.get("/api/graph/statistics")
async def get_graph_statistics_compat(
    project_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """兼容路由：前端调用 /api/graph/statistics"""
    from app.models.entity import Entity
    from app.models.project import ProjectDocument
    from sqlalchemy import func, distinct

    # 统计节点数（实体数）
    node_count = db.query(func.count(distinct(Entity.id))).join(
        ProjectDocument, Entity.document_id == ProjectDocument.id
    ).filter(
        ProjectDocument.project_id == project_id
    ).scalar() or 0

    # 统计实体类型分布
    type_distribution = db.query(
        Entity.entity_type,
        func.count(Entity.id).label('count')
    ).join(
        ProjectDocument, Entity.document_id == ProjectDocument.id
    ).filter(
        ProjectDocument.project_id == project_id
    ).group_by(Entity.entity_type).all()

    return {
        "node_count": node_count,
        "edge_count": 0,  # TODO: 实现关系统计
        "type_distribution": {
            entity_type or "unknown": count
            for entity_type, count in type_distribution
        }
    }

# ============= 结束前后端兼容层 =============


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "FieldMind API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查 - 检查所有依赖服务状态"""
    from app.core.database import SessionLocal
    from sqlalchemy import text
    import time

    start_time = time.time()
    services = {}
    overall_status = "healthy"

    # 检查API
    services["api"] = "ok"

    # 检查数据库
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        services["database"] = "ok"
    except Exception as e:
        services["database"] = f"error: {str(e)[:50]}"
        overall_status = "degraded"

    # 检查Redis（可选）
    try:
        from app.core.cache import cache_backend
        if cache_backend:
            cache_backend.set("health_check", "ok", ttl=60)
            test_val = cache_backend.get("health_check")
            services["redis"] = "ok" if test_val == "ok" else "degraded"
        else:
            services["redis"] = "not_configured"
    except Exception as e:
        services["redis"] = "not_configured"

    # 检查Neo4j（可选）
    try:
        # 如果配置了Neo4j，这里可以添加检查
        services["neo4j"] = "not_configured"
    except Exception as e:
        services["neo4j"] = "not_configured"

    response_time = round((time.time() - start_time) * 1000, 2)

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "response_time_ms": response_time,
        "services": services
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
