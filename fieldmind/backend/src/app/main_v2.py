"""
生产级应用启动脚本
集成新的配置管理、日志系统、健康检查
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
import uvicorn
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入新的配置系统
from app.core.config import settings, setup_logging, get_logger
from app.core.config.constants import Environment

# 导入统一异常处理框架
from app.core.exceptions import (
    FieldMindException,
    ErrorCode,
    ValidationException,
    ResourceNotFoundException,
)

# 导入监控系统
from app.core.monitoring import metrics_manager, track_request, record_error

# 导入Sentry集成
from app.core.sentry_integration import init_sentry, capture_exception

# 初始化日志系统
setup_logging(
    level=settings.monitoring.log_level,
    log_format=settings.monitoring.log_format,
    log_file=settings.monitoring.log_file,
    rotation=settings.monitoring.log_rotation,
    retention=settings.monitoring.log_retention,
    compression=settings.monitoring.log_compression
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info("🚀 FieldMind Backend 启动中...")
    logger.info(f"📦 环境: {settings.environment.value}")
    logger.info(f"🐛 调试模式: {settings.debug}")
    logger.info(f"📝 API文档: http://{settings.host}:{settings.port}/docs")
    logger.info(f"📊 监控指标: http://{settings.host}:{settings.port}/metrics")
    logger.info("=" * 60)

    # 初始化Sentry错误追踪
    try:
        sentry_initialized = init_sentry(
            environment=settings.environment.value,
            release=settings.version,
            traces_sample_rate=0.1 if settings.is_production() else 0.0,
            debug=settings.debug,
        )
        if sentry_initialized:
            logger.info("✅ Sentry错误追踪已启用")
        else:
            logger.info("ℹ️  Sentry错误追踪未配置")
    except Exception as e:
        logger.warning(f"⚠️  Sentry初始化失败: {e}")

    # 初始化数据库
    try:
        from app.core.database import init_db
        init_db()
        logger.info("✅ 数据库连接池初始化成功")
        logger.info(f"   - Pool size: {settings.database.pool_size}")
        logger.info(f"   - Max overflow: {settings.database.max_overflow}")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}", exc_info=True)
        if settings.is_production():
            raise  # 生产环境数据库失败应该中止启动

    # 初始化Redis连接池
    try:
        from app.core.cache import init_redis
        init_redis()
        logger.info("✅ Redis连接池初始化成功")
    except Exception as e:
        logger.warning(f"⚠️  Redis初始化失败: {e}")
        if settings.is_production():
            logger.error("生产环境Redis不可用，请检查配置")

    # 初始化Neo4j连接
    try:
        from app.services.knowledge_graph_service import knowledge_graph_service
        knowledge_graph_service.driver  # 触发连接
        logger.info("✅ Neo4j连接成功")
    except Exception as e:
        logger.warning(f"⚠️  Neo4j初始化失败: {e}")

    # 初始化向量数据库
    try:
        from app.core.vector_store import init_vector_store
        init_vector_store()
        logger.info("✅ 向量数据库初始化成功")
    except Exception as e:
        logger.warning(f"⚠️  向量数据库初始化失败: {e}")

    # 创建必要目录
    settings.storage.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.storage.data_dir.mkdir(parents=True, exist_ok=True)
    settings.storage.temp_dir.mkdir(parents=True, exist_ok=True)
    logger.info("✅ 存储目录检查完成")

    # 启动后台任务（如果需要）
    logger.info("✅ FieldMind Backend 启动完成！")
    logger.info("=" * 60)

    yield

    # 关闭时清理资源
    logger.info("=" * 60)
    logger.info("👋 FieldMind Backend 关闭中...")

    # 关闭数据库连接池
    try:
        from app.core.database import close_db
        close_db()
        logger.info("✅ 数据库连接池已关闭")
    except Exception as e:
        logger.error(f"❌ 数据库关闭失败: {e}")

    # 关闭Redis连接池
    try:
        from app.core.cache import close_redis
        close_redis()
        logger.info("✅ Redis连接池已关闭")
    except Exception as e:
        logger.error(f"❌ Redis关闭失败: {e}")

    # 关闭Neo4j连接
    try:
        from app.services.knowledge_graph_service import knowledge_graph_service
        knowledge_graph_service.close()
        logger.info("✅ Neo4j连接已关闭")
    except Exception as e:
        logger.error(f"❌ Neo4j关闭失败: {e}")

    logger.info("✅ FieldMind Backend 已关闭")
    logger.info("=" * 60)


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="田野调查知识管理系统 - 生产级AI后端服务",
    version=settings.version,
    docs_url="/docs" if not settings.is_production() else None,  # 生产环境可选关闭文档
    redoc_url="/redoc" if not settings.is_production() else None,
    lifespan=lifespan,
    debug=settings.debug,
)


# ==================== 全局异常处理 ====================

@app.exception_handler(FieldMindException)
async def fieldmind_exception_handler(request: Request, exc: FieldMindException):
    """FieldMind自定义异常处理器"""
    # 记录错误到监控系统
    record_error(
        error_code=exc.error_code,
        error_type=type(exc).__name__,
        component="api_handler",
        details={
            'path': str(request.url.path),
            'method': request.method,
            **exc.details
        }
    )

    # 记录到Sentry
    capture_exception(
        exc,
        level="error",
        tags={
            "error_code": str(exc.error_code.code),
            "endpoint": str(request.url.path),
        },
        extras=exc.details
    )

    # 记录到日志
    logger.error(
        f"业务异常: {exc.error_code.name} - {exc.message}",
        extra={
            'extra_data': {
                'path': str(request.url.path),
                'method': request.method,
                'error_code': exc.error_code.code,
                'details': exc.details,
            }
        }
    )

    return JSONResponse(
        status_code=exc.error_code.http_status,
        content={
            'success': False,
            'error': exc.to_dict()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    # 记录错误到监控系统
    error_type = type(exc).__name__
    record_error(
        error_code=ErrorCode.UNKNOWN_ERROR,
        error_type=error_type,
        component="global_handler",
        details={
            'path': str(request.url.path),
            'method': request.method,
            'error_message': str(exc)
        }
    )

    # 记录到Sentry
    capture_exception(
        exc,
        level="error",
        tags={
            "endpoint": str(request.url.path),
            "method": request.method,
        }
    )

    # 记录详细错误
    logger.error(
        f"全局异常捕获: {error_type}",
        exc_info=True,
        extra={
            'extra_data': {
                'path': str(request.url.path),
                'method': request.method,
                'client': request.client.host if request.client else None,
            }
        }
    )

    # 生产环境隐藏详细错误信息
    if settings.is_production():
        message = "服务器内部错误，请稍后重试"
    else:
        message = f"{error_type}: {str(exc)}"

    return JSONResponse(
        status_code=500,
        content={
            'success': False,
            'error': {
                'code': ErrorCode.UNKNOWN_ERROR.code,
                'message': message,
                'type': error_type
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(
        f"HTTP异常: {exc.status_code}",
        extra={
            'extra_data': {
                'path': str(request.url.path),
                'method': request.method,
                'detail': exc.detail,
            }
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            'success': False,
            'error': {
                'code': str(exc.status_code),
                'message': exc.detail
            }
        }
    )


# ==================== 中间件 ====================

# 请求日志和监控中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求并追踪指标"""
    import time
    from app.core.config.logging_config import set_log_context, clear_log_context
    import uuid

    # 生成请求ID
    request_id = str(uuid.uuid4())

    # 设置日志上下文
    set_log_context(
        request_id=request_id,
        path=str(request.url.path),
        method=request.method
    )

    start_time = time.time()

    logger.info(f"请求开始: {request.method} {request.url.path}")

    # 提取endpoint（去除查询参数）
    endpoint = str(request.url.path)
    status_code = 500  # 默认状态码

    try:
        # 添加request_id到请求状态
        request.state.request_id = request_id

        response = await call_next(request)
        status_code = response.status_code

        # 计算耗时
        duration = time.time() - start_time

        # 记录到 Prometheus
        metrics_manager.http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        metrics_manager.http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        logger.info(
            f"请求完成",
            extra={
                'extra_data': {
                    'status_code': status_code,
                    'duration_seconds': round(duration, 3)
                }
            }
        )

        # 添加请求ID到响应头
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        duration = time.time() - start_time

        # 记录失败的请求到 Prometheus
        metrics_manager.http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=500
        ).inc()

        metrics_manager.http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        logger.error(
            f"请求异常",
            exc_info=True,
            extra={
                'extra_data': {
                    'duration_seconds': round(duration, 3),
                    'error': str(e)
                }
            }
        )
        raise
    finally:
        clear_log_context()


# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=settings.security.cors_allow_credentials,
    allow_methods=settings.security.cors_allow_methods,
    allow_headers=settings.security.cors_allow_headers,
)

# Gzip压缩
app.add_middleware(GZipMiddleware, minimum_size=1000)


# ==================== 健康检查 ====================

@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    from app.core.database import get_db
    from app.core.cache import get_redis_client

    health_status = {
        "status": "healthy",
        "environment": settings.environment.value,
        "version": settings.version,
        "services": {}
    }

    # 检查数据库
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # 检查Redis
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # 检查Neo4j
    try:
        from app.services.knowledge_graph_service import knowledge_graph_service
        with knowledge_graph_service.driver.session() as session:
            session.run("RETURN 1")
        health_status["services"]["neo4j"] = "healthy"
    except Exception as e:
        health_status["services"]["neo4j"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    return health_status


@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment.value,
        "docs": "/docs" if not settings.is_production() else "disabled",
        "health": "/health",
        "metrics": "/metrics"
    }


@app.get("/metrics", tags=["监控"])
async def metrics():
    """Prometheus 指标端点"""
    from app.core.monitoring import get_metrics_handler

    content, content_type = get_metrics_handler()
    return Response(content=content, media_type=content_type)


# ==================== 导入并注册路由 ====================

# 注意：这里先导入旧的路由，逐步迁移到新的错误处理
try:
    from app.api.v1 import (
        audio, documents as v1_documents, search, rag, workflows as v1_workflows,
        auth, crawler, skills, industry, reports, enhanced_chat,
        projects as v1_projects, project_chat, project_documents
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

    # 注册路由
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
    app.include_router(v1_projects.router, prefix="/api/v1/projects", tags=["项目管理"])
    app.include_router(project_documents.router, prefix="/api/v1/project-documents", tags=["项目文档"])
    app.include_router(project_chat.router, prefix="/api/v1/project-chat", tags=["项目对话"])
    app.include_router(chat.router, prefix="/api/chat", tags=["智能对话"])

    # RAG对话路由
    from app.api import chat_rag
    app.include_router(chat_rag.router, prefix="/api/chat-rag", tags=["RAG对话"])

    # 报告生成路由
    from app.api import reports_real
    app.include_router(reports_real.router, prefix="/api/reports", tags=["报告生成"])

    # Skill配置管理路由
    from app.api import skill_config
    app.include_router(skill_config.router, prefix="/api/skills", tags=["Skill配置"])

    # Dashboard统计路由
    from app.api import dashboard
    app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

    # 批量处理路由
    from app.api import batch_processing
    app.include_router(batch_processing.router, prefix="/api/batch", tags=["批量处理"])

    # 知识图谱路由
    from app.api import knowledge_graph as kg_new
    app.include_router(kg_new.router, prefix="/api/knowledge-graph", tags=["知识图谱"])

    # 知识图谱v2路由
    try:
        from app.api.v1 import knowledge_graph_api
        app.include_router(knowledge_graph_api.router, prefix="/api/knowledge-graph-v2", tags=["知识图谱v2"])
    except ImportError as e:
        logger.warning(f"知识图谱v2 API未加载: {e}")

    # 时间线路由
    from app.api import timeline as timeline_new
    app.include_router(timeline_new.router, prefix="/api/timeline", tags=["时间线"])

    # 工作流路由
    from app.api import workflows as workflows_new
    app.include_router(workflows_new.router, prefix="/api/workflows", tags=["工作流编排"])

    logger.info("✅ 所有API路由已注册")

except ImportError as e:
    logger.error(f"❌ 路由导入失败: {e}", exc_info=True)
    raise


# ==================== 启动服务 ====================

if __name__ == "__main__":
    uvicorn.run(
        "app.main_v2:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.monitoring.log_level.lower(),
        access_log=True,
    )
