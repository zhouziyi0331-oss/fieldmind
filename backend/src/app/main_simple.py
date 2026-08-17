"""
FieldMind Backend - Simplified FastAPI Application
只包含新的项目管理、智能对话和文档管理功能
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

from app.config import settings
from app.api import (
    projects, chat, documents, knowledge_graph, timeline, auth,
    keyword_search, creative_analysis, business_analysis, monitoring, websocket
)
from app.middleware.monitoring import MonitoringMiddleware, PerformanceMonitoringMiddleware
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    logger.info("🚀 FieldMind Backend (Simple) 启动中...")
    logger.info(f"📝 API文档: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"📊 监控面板: http://{settings.HOST}:{settings.PORT}/monitoring/health")

    # 初始化数据库
    try:
        from app.core.database import init_db
        init_db()
        logger.info("✅ 数据库初始化成功")
    except Exception as e:
        logger.warning(f"⚠️  数据库初始化警告: {e}")

    yield

    # 关闭事件
    logger.info("👋 FieldMind Backend 关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="FieldMind API (Simple)",
    description="田野调查知识管理系统 - 简化版API服务",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 监控中间件（放在最外层，最先执行）
app.add_middleware(MonitoringMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware, slow_threshold_ms=1000)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 使用配置的CORS源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册新的API路由
app.include_router(monitoring.router, tags=["监控"])  # 监控路由，不加 /api 前缀
app.include_router(websocket.router, tags=["WebSocket"])  # WebSocket 路由 ⭐ NEW
app.include_router(auth.router, prefix="/api", tags=["认证"])
app.include_router(projects.router, prefix="/api", tags=["项目管理"])
app.include_router(chat.router, prefix="/api", tags=["智能对话"])
app.include_router(documents.router, prefix="/api", tags=["文档管理"])
app.include_router(knowledge_graph.router, prefix="/api", tags=["知识图谱"])
app.include_router(timeline.router, prefix="/api", tags=["时间线"])
app.include_router(keyword_search.router, prefix="/api", tags=["关键词检索"])
app.include_router(creative_analysis.router, prefix="/api", tags=["文创分析"])
app.include_router(business_analysis.router, prefix="/api", tags=["业态分析"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "FieldMind API (Simple)",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "features": [
            "项目管理 (Project Isolation)",
            "智能对话 (AI Chat with Deep Thinking)",
            "长期记忆 (Mem0 Integration)",
            "文档管理 (14+ File Formats)",
            "技能框架 (Self-Evolving AI)",
            "知识图谱 (Knowledge Graph)",
            "时间线 (Timeline Events)",
            "关键词智能检索 (Keyword Search with Video Timestamps) ⭐NEW",
            "在地文创分析 (Creative Analysis) ⭐NEW",
            "业态分析系统 (Business Analysis) ⭐NEW"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "api": "ok",
            "database": "ok"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main_simple:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
