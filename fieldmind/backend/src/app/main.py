"""
FieldMind Backend - FastAPI Application
田野调查知识管理系统 - 主应用入口
"""

# ============= 🔥 Monkey Patch: 必须在导入 FastAPI 之前 =============
from starlette.routing import Router

# 保存原始方法
_original_router_call = Router.__call__

async def _patched_router_call(self, scope, receive, send):
    """强制禁用 redirect_slashes"""
    original_value = self.redirect_slashes
    self.redirect_slashes = False  # 强制设置为 False
    try:
        await _original_router_call(self, scope, receive, send)
    finally:
        self.redirect_slashes = original_value

# 应用 Monkey Patch
Router.__call__ = _patched_router_call
print("✅ Monkey Patch 已应用：彻底禁用 Starlette Router 的 307 重定向")
# ============= 结束 Monkey Patch =============

from fastapi import FastAPI, WebSocket, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn
import traceback
import logging
import importlib
import os

from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import get_db
from app.contracts import error_response, ErrorCodes

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
RUNTIME_VERSION = "fieldmind-native-v3.1-unified-data"


def runtime_host() -> str:
    return os.getenv("HOST") or getattr(settings, "host", "0.0.0.0")


def runtime_port() -> int:
    configured = os.getenv("PORT")
    if configured:
        try:
            return int(configured)
        except ValueError:
            logger.warning("无效 PORT 环境变量: %s", configured)
    return int(getattr(settings, "port", 8000))

from app.api.v1 import (
    audio, documents as v1_documents, search, rag, workflows as v1_workflows,
    auth, crawler, skills, industry, reports, enhanced_chat,
    projects as v1_projects, project_chat, project_documents, learning
)
from app.api import (
    chat,
    documents,
    keyword_search,
    creative_analysis,
    business_analysis,
    document_processing,
    conversation_memory,
    document_normalization
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("🚀 FieldMind Backend 启动中...")
    logger.info(f"📝 API文档: http://{runtime_host()}:{runtime_port()}/docs")

    # 初始化缓存后端（P3-C）
    try:
        from app.core.cache import init_cache_backend
        init_cache_backend(
            use_redis=settings.use_redis_cache,
            redis_url=settings.redis.url if settings.use_redis_cache else None
        )
        logger.info("✅ 缓存系统初始化成功")
    except Exception as e:
        logger.warning(f"⚠️  缓存系统初始化警告: {e}")

    # 初始化数据库
    try:
        from app.core.database import init_db
        # 延迟加载：确保配置已正确加载
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
        init_db()
        logger.info("✅ 数据库初始化成功")
    except Exception as e:
        logger.warning(f"⚠️  数据库初始化警告: {e}")

    # 初始化WebSocket事件监听器（Phase 3.7）
    try:
        from app.services.event_emitter import setup_websocket_listeners
        import asyncio
        asyncio.create_task(setup_websocket_listeners())
        logger.info("✅ WebSocket事件监听器已初始化")
    except Exception as e:
        logger.warning(f"⚠️  WebSocket初始化警告: {e}")

    # 启动心跳检查任务（Phase 3.7）
    try:
        from app.services.websocket_manager import heartbeat_task
        import asyncio
        asyncio.create_task(heartbeat_task())
        logger.info("✅ WebSocket心跳任务已启动")
    except Exception as e:
        logger.warning(f"⚠️  心跳任务启动警告: {e}")

    # 启动定时任务调度器（Phase 2.5）
    try:
        from app.services.scheduler import scheduler_service
        from app.core.database import get_db
        scheduler_service.start()
        # 加载所有活跃任务
        db = next(get_db())
        scheduler_service.load_all_tasks(db, get_db)
        db.close()
        logger.info("✅ 定时任务调度器已启动")
    except Exception as e:
        logger.warning(f"⚠️  定时任务调度器启动警告: {e}")

    # 启动审计日志清理任务
    try:
        from app.tasks.audit_cleanup import audit_cleanup_task
        await audit_cleanup_task.start()
        logger.info("✅ 审计日志清理任务已启动")
    except Exception as e:
        logger.warning(f"⚠️  审计日志清理任务启动警告: {e}")

    # 初始化事件处理器（统一管道协调器）
    try:
        from app.services.event_handlers.event_handler_registry import initialize_event_handlers
        initialize_event_handlers()
        logger.info("✅ 事件处理器已初始化（支持自动缩影生成）")
    except Exception as e:
        logger.warning(f"⚠️  事件处理器初始化警告: {e}")

    yield

    # 关闭
    logger.info("👋 FieldMind Backend 关闭中...")

    # 关闭审计日志清理任务
    try:
        from app.tasks.audit_cleanup import audit_cleanup_task
        await audit_cleanup_task.stop()
        logger.info("✅ 审计日志清理任务已关闭")
    except Exception as e:
        logger.warning(f"⚠️  审计日志清理任务关闭警告: {e}")

    # 关闭定时任务调度器
    try:
        from app.services.scheduler import scheduler_service
        scheduler_service.shutdown()
        logger.info("✅ 定时任务调度器已关闭")
    except Exception as e:
        logger.warning(f"⚠️  定时任务调度器关闭警告: {e}")

    # 清理资源


# 创建FastAPI应用
app = FastAPI(
    title="FieldMind API",
    description="田野调查知识管理系统 - AI后端服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    redirect_slashes=False,  # 禁用尾部斜杠重定向，修复前端 404
)

# 禁用尾部斜杠重定向（修复前端 404）
app.router.redirect_slashes = False


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


# ============= API 网关中间件（新增）=============
@app.middleware("http")
async def api_gateway_middleware(request: Request, call_next):
    """API 网关中间件 - 限流、日志、监控"""
    try:
        from app.core.api_gateway import api_gateway
        return await api_gateway.process_request(request, call_next)
    except ImportError:
        logger.warning("API 网关模块不可用")
        return await call_next(request)

# Prometheus 监控中间件
@app.middleware("http")
async def prometheus_monitoring(request: Request, call_next):
    """Prometheus 监控中间件"""
    try:
        from app.middleware.prometheus_middleware import prometheus_middleware
        return await prometheus_middleware(request, call_next)
    except ImportError:
        # 如果监控模块不可用，继续正常处理
        return await call_next(request)

# 强力修复 307 重定向中间件（必须在所有中间件之前）
@app.middleware("http")
async def fix_trailing_slash_redirect(request: Request, call_next):
    """
    彻底修复 FastAPI 的 307 重定向问题

    方案：直接拦截 307 响应，重新调用带斜杠的路由
    """
    original_path = request.url.path

    # 先正常处理请求
    response = await call_next(request)

    # 如果返回 307 重定向
    if response.status_code == 307:
        # 获取重定向目标
        location = response.headers.get("location", "")

        # 如果是尾部斜杠重定向（location = original_path + "/"）
        if location and location.endswith("/") and original_path + "/" in location:
            # 不返回 307，而是直接重新调用带斜杠的路由
            from starlette.datastructures import URL
            from copy import copy

            # 创建新的请求
            new_scope = copy(request.scope)
            new_scope["path"] = original_path + "/"
            new_scope["raw_path"] = (original_path + "/").encode()

            # 重新构造请求
            from starlette.requests import Request as StarletteRequest
            new_request = StarletteRequest(new_scope, request.receive)

            # 重新调用
            response = await call_next(new_request)

    return response


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

# HEAD请求处理中间件 - 自动将HEAD转换为GET
@app.middleware("http")
async def handle_head_requests(request: Request, call_next):
    """
    处理HEAD请求：将HEAD转换为GET，然后移除响应体
    这样所有GET端点自动支持HEAD，解决macOS URLSession的兼容性问题
    """
    original_method = request.method
    if request.method == "HEAD":
        # 临时修改为GET
        request.scope["method"] = "GET"

    response = await call_next(request)

    if original_method == "HEAD":
        # HEAD请求不应该有响应体
        return Response(
            content=b"",
            status_code=response.status_code,
            headers=dict(response.headers)
        )

    return response

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
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
logger.info("🔧 [DEBUG] 开始注册路由...")


def include_optional_router(module_path: str, prefix: str = "", tags: list[str] | None = None):
    """注册可选功能路由。导入失败只记录，不阻断主应用启动。"""
    try:
        module = importlib.import_module(module_path)
        router = getattr(module, "router")
        app.include_router(router, prefix=prefix, tags=tags)
        logger.info(f"✅ 可选路由已注册: {module_path}")
    except Exception as e:
        logger.warning(f"⚠️ 可选路由未注册 {module_path}: {e}")


# 认证系统 (v1版本)
logger.info("🔧 [DEBUG] 注册auth路由...")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证(v1)"])
logger.info(f"🔧 [DEBUG] auth注册后路由数: {len(list(app.routes))}")

# 认证系统兼容路由（供测试和旧前端使用）
app.include_router(auth.router, prefix="/api/auth", tags=["认证(兼容)"], include_in_schema=False)
logger.info(f"🔧 [DEBUG] auth兼容路由注册后路由数: {len(list(app.routes))}")

# 项目工作流路由（P0: 统一分析端点）
from app.api.v1 import project_workflow
logger.info("🔧 [DEBUG] 注册project_workflow路由...")
app.include_router(project_workflow.router, prefix="/api/v1", tags=["项目工作流"])
logger.info(f"🔧 [DEBUG] project_workflow注册后路由数: {len(list(app.routes))}")

# 认证系统 (新版本，直接使用v1的auth，只是改变前缀)
# REMOVED: app.include_router(auth.router, prefix="/api/auth", tags=["认证"], include_in_schema=False)  # 重复路由，已使用v1版本

# 新的项目管理系统（带Mem0长记忆和智能Agent）
# REMOVED: app.include_router(projects.router, prefix="/api/projects", tags=["项目管理(新)"])  # 重复路由，已使用v1版本
logger.info(f"🔧 [DEBUG] 准备注册chat路由，当前路由数: {len(list(app.routes))}")
app.include_router(chat.router, prefix="/api/chat", tags=["智能对话"])
logger.info(f"🔧 [DEBUG] chat注册后路由数: {len(list(app.routes))}")

# RAG对话路由（真正的向量检索）
from app.api import chat_rag
app.include_router(chat_rag.router, prefix="/api/chat-rag", tags=["RAG对话"])

# 报告生成路由（真实数据）
# from app.api import reports_real
# app.include_router(reports_real.router, prefix="/api/reports", tags=["报告生成"])

# Skill配置管理路由
from app.api import skill_config
app.include_router(skill_config.router, prefix="/api/skills", tags=["Skill配置"])

# Dashboard统计路由
from app.api import dashboard
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

# 文件缩影路由（知识缩影系统）
from app.api import file_summaries
app.include_router(file_summaries.router, prefix="/api/v1", tags=["文件缩影"])
logger.info("✅ 文件缩影API已注册")

# 缩影导出路由（导出为 PDF/Word）
from app.api import export_summaries
app.include_router(export_summaries.router, prefix="/api/v1", tags=["缩影导出"])
logger.info("✅ 缩影导出API已注册")

# 缩影可视化路由（词云、分布图、网络图）
from app.api import visualize_summaries
app.include_router(visualize_summaries.router, prefix="/api/v1", tags=["缩影可视化"])
logger.info("✅ 缩影可视化API已注册")

# 审计日志路由（架构升级 - 阶段2）
from app.api.v1 import audit
app.include_router(audit.router, prefix="/api/v1", tags=["审计日志"])
logger.info("✅ 审计日志API已注册")

# 权限管理路由（架构升级 - 阶段3）
from app.api.v1 import permissions
app.include_router(permissions.router, prefix="/api/v1", tags=["权限管理"])
logger.info("✅ 权限管理API已注册")

# 数据血缘路由（架构升级 - 阶段4）
from app.api.v1 import lineage
app.include_router(lineage.router, prefix="/api/v1/lineage", tags=["数据血缘"])
logger.info("✅ 数据血缘API已注册")

# 工作流引擎路由（架构升级 - 阶段5）
from app.api.v1 import workflows
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["工作流引擎"])
logger.info("✅ 工作流引擎API已注册")

# Dashboard和指标系统路由（架构升级 - 阶段6）
from app.api.v1 import dashboard as dashboard_v1
app.include_router(dashboard_v1.router, prefix="/api/v1/dashboard", tags=["Dashboard和指标"])
logger.info("✅ Dashboard和指标系统API已注册")

# 对话记忆路由（架构升级 - 阶段7）
from app.api.v1 import conversation
app.include_router(conversation.router, prefix="/api/v1/memory", tags=["对话记忆"])
logger.info("✅ 对话记忆API已注册")

# 用户分析路由（架构升级 - 阶段8）
from app.api.v1 import user_analysis
app.include_router(user_analysis.router, prefix="/api/v1/analysis", tags=["用户分析"])
logger.info("✅ 用户分析API已注册")

# 学习日志路由（架构升级 - 阶段9）
from app.api.v1 import learning
app.include_router(learning.router, prefix="/api/v1/learning", tags=["学习日志"])
logger.info("✅ 学习日志API已注册")

# 用户喂养路由（架构升级 - 阶段10）
from app.api.v1 import feeding
app.include_router(feeding.router, prefix="/api/v1/feeding", tags=["用户喂养"])

# ============= 新增 API 路由 =============
# API 管理接口（API 网关）
try:
    from app.api.v1 import api_management
    app.include_router(api_management.router, prefix="/api/v1", tags=["API 管理"])
    logger.info("✅ API 管理路由已注册")
except ImportError as e:
    logger.warning(f"⚠️  API 管理模块导入失败: {e}")

# 知识图谱接口
try:
    from app.api.v1 import knowledge_graph
    app.include_router(knowledge_graph.router, prefix="/api/v1", tags=["知识图谱"])
    logger.info("✅ 知识图谱路由已注册")
except ImportError as e:
    logger.warning(f"⚠️  知识图谱模块导入失败: {e}")

# 数据质量监控接口
try:
    from app.api.v1 import data_quality
    app.include_router(data_quality.router, prefix="/api/v1", tags=["数据质量"])
    logger.info("✅ 数据质量路由已注册")
except ImportError as e:
    logger.warning(f"⚠️  数据质量模块导入失败: {e}")

# 溯源回溯接口
try:
    from app.api.v1 import traceability
    app.include_router(traceability.router, prefix="/api/v1", tags=["溯源回溯"])
    logger.info("✅ 溯源回溯路由已注册")
except ImportError as e:
    logger.warning(f"⚠️  溯源回溯模块导入失败: {e}")

# 协作与权限接口
try:
    from app.api.v1 import collaboration
    app.include_router(collaboration.router, prefix="/api/v1", tags=["协作与权限"])
    logger.info("✅ 协作与权限路由已注册")
except ImportError as e:
    logger.warning(f"⚠️  协作与权限模块导入失败: {e}")
# ============= 结束新增 API 路由 =============
logger.info("✅ 用户喂养API已注册")

# 用户标注路由（架构升级 - 阶段11）
from app.api.v1 import annotation
app.include_router(annotation.router, prefix="/api/v1/annotation", tags=["用户标注"])
logger.info("✅ 用户标注API已注册")

# 用户标签路由（架构升级 - 阶段12）
from app.api.v1 import tagging
app.include_router(tagging.router, prefix="/api/v1/tagging", tags=["用户标签"])
logger.info("✅ 用户标签API已注册")

# 执行追踪路由（自学习系统 - 阶段13）
from app.api.v1 import execution_tracking
app.include_router(execution_tracking.router, prefix="/api/v1/execution", tags=["执行追踪"])
logger.info("✅ 执行追踪API已注册")

# 模式识别路由（自学习系统 - 阶段14）
from app.api.v1 import pattern_recognition
app.include_router(pattern_recognition.router, prefix="/api/v1/patterns", tags=["模式识别"])
logger.info("✅ 模式识别API已注册")

# 技能生成路由（自学习系统 - 阶段15）
from app.api.v1 import skill_generation
app.include_router(skill_generation.router, prefix="/api/v1/skill-gen", tags=["技能生成"])
logger.info("✅ 技能生成API已注册")

# 技能优化路由（自学习系统 - 阶段16）
from app.api.v1 import skill_optimization
app.include_router(skill_optimization.router, prefix="/api/v1/skill-opt", tags=["技能优化"])
logger.info("✅ 技能优化API已注册")

# 反馈闭环路由（自学习系统 - 阶段17）
from app.api.v1 import feedback_loops
app.include_router(feedback_loops.router, prefix="/api/v1/feedback", tags=["反馈闭环"])
logger.info("✅ 反馈闭环API已注册")

# 后台学习路由（自学习系统 - 阶段18）
from app.api.v1 import background_learning
app.include_router(background_learning.router, prefix="/api/v1/learning", tags=["后台学习"])
logger.info("✅ 后台学习API已注册")

# 经验图谱路由（自学习系统 - 阶段19）
from app.api.v1 import experience_graph
app.include_router(experience_graph.router, prefix="/api/v1/experience-graph", tags=["经验图谱"])
logger.info("✅ 经验图谱API已注册")

# 统一插件系统路由（插件整合 - 阶段20）
from app.api.v1 import unified_plugins
app.include_router(unified_plugins.router, prefix="/api/v1/plugins", tags=["统一插件"])

# 知识脉络路由（知识网络可视化）
from app.api.v1 import knowledge_network
app.include_router(knowledge_network.router, prefix="/api/v1", tags=["知识脉络"])
logger.info("✅ 知识脉络API已注册")

# 在地业态分析路由（业态推演和可行性评估）
# from app.api.v1 import business_analysis as business_analysis_v1
# app.include_router(business_analysis_v1.router, prefix="/api/v1", tags=["在地业态分析"])
# logger.info("✅ 在地业态分析API已注册")

# 数据增强路由（NLP处理和自动分类）
from app.api.v1 import data_enrichment
app.include_router(data_enrichment.router, prefix="/api/v1", tags=["数据增强"])
logger.info("✅ 数据增强API已注册")
logger.info("✅ 统一插件系统API已注册")

# 工作舱统一服务路由（工作舱核心 - 阶段21）
from app.api.v1 import workbench
app.include_router(workbench.router, tags=["工作舱"])
logger.info("✅ 工作舱统一服务API已注册")


@app.get("/api/v1/dashboard/stats/{project_id}")
def dashboard_stats_v1(project_id: int, db=Depends(get_db)):
    return dashboard.get_dashboard_stats(project_id=project_id, db=db)


@app.get("/api/v1/dashboard/timeline/{project_id}")
def dashboard_timeline_v1(project_id: int, days: int = 7, db=Depends(get_db)):
    return dashboard.get_project_timeline(project_id=project_id, days=days, db=db)


@app.get("/api/v1/dashboard/progress/{project_id}")
def dashboard_progress_v1(project_id: int, db=Depends(get_db)):
    return dashboard.get_project_progress(project_id=project_id, db=db)

# 批量处理路由
from app.api import batch_processing
app.include_router(batch_processing.router, prefix="/api/batch", tags=["批量处理"])

# 知识图谱路由（链路十一）
from app.api import knowledge_graph as kg_new
app.include_router(kg_new.router, prefix="/api/knowledge-graph", tags=["知识图谱"])
# 添加 /api/kg 别名路由以兼容前端
app.include_router(kg_new.router, prefix="/api/kg", tags=["知识图谱"])

# 知识图谱v2路由（NetworkX增强版）
try:
    from app.api.v1 import knowledge_graph_api
    app.include_router(knowledge_graph_api.router, prefix="/api/knowledge-graph-v2", tags=["知识图谱v2"])
    logger.info("✅ 知识图谱v2 API已加载")
except ImportError as e:
    logger.warning(f"⚠️ 知识图谱v2 API未找到: {e}")

# 知识图谱增强版路由（三数据库集成 + Skills集成 + 推理 + 时间线）
try:
    from app.api.v1 import knowledge_graph_enhanced
    app.include_router(knowledge_graph_enhanced.router, prefix="/api/v1", tags=["知识图谱增强"])
    logger.info("✅ 知识图谱增强版 API已加载")
except ImportError as e:
    logger.warning(f"⚠️ 知识图谱增强版 API未找到: {e}")

# 时间线路由（链路十一）
from app.api import timeline as timeline_new
app.include_router(timeline_new.router, prefix="/api/timeline", tags=["时间线"])

# 工作流路由（链路十二）
from app.api import workflows as workflows_new
app.include_router(workflows_new.router, prefix="/api/workflows", tags=["工作流编排"])

# 记忆管理路由（链路十三）
from app.api import memory as memory_new
app.include_router(memory_new.router, prefix="/api/memory", tags=["记忆管理"])

# 文档处理v2路由（链路十四）
from app.api import document_processing_v2
app.include_router(document_processing_v2.router, prefix="/api/document-processing-v2", tags=["文档处理v2-引用溯源"])

# 知识图谱v3路由（链路十六：证据链绑定）
from app.api import knowledge_graph_v3
app.include_router(knowledge_graph_v3.router, prefix="/api/knowledge-graph-v3", tags=["知识图谱v3-证据链"])

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

# 可视化路由（Phase 3.5）
from app.api import visualize
app.include_router(visualize.router, prefix="/api/visualize", tags=["数据可视化"])

# 深度RAG对话路由（Phase 3.6）
from app.api import deep_rag
app.include_router(deep_rag.router, prefix="/api/deep-rag", tags=["深度RAG对话"])

# WebSocket实时通知路由（Phase 3.7）
from app.api import websocket as websocket_router
app.include_router(websocket_router.router, prefix="/api/websocket", tags=["WebSocket实时通知"])

# OCR文本识别路由（Phase 3.8）
from app.api import ocr
app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR文本识别"])

# 质量控制路由（Phase 3.9）
# DISABLED: from app.api import quality
# DISABLED: app.include_router(quality.router, prefix="/api/quality", tags=["质量控制"])

# 定时任务路由（Phase 2.5）
from app.api import scheduler
app.include_router(scheduler.router, tags=["定时任务"])

# 引用管理路由
from app.api import citations
app.include_router(citations.router, prefix="/api/citations", tags=["引用管理"])

# 文件管理路由
from app.api import file_manager
app.include_router(file_manager.router, prefix="/api", tags=["文件管理"])

# 照片管理路由 - 必须在 documents.router 之前注册，避免 /{document_id} 通配符冲突
from app.api.photos import router as photos_router
app.include_router(photos_router, prefix="/api", tags=["照片管理"])

# 表格管理与统一上传共用 project_documents 主表。
from app.api import tables as tables_api
app.include_router(tables_api.router, prefix="/api/v1", tags=["表格管理"])

# documents.router 自身已声明 /documents 前缀，这里只补 /api，避免形成
# /api/documents/documents/upload，保证旧客户端的统一上传入口可用。
app.include_router(documents.router, prefix="/api", tags=["文档管理(新)"])
app.include_router(document_normalization.router, tags=["文档规范化"])
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
logger.info(f"🔧 [DEBUG] 注册audio前路由数: {len(list(app.routes))}")
app.include_router(audio.router, prefix="/api/v1/audio", tags=["音频"])
logger.info(f"🔧 [DEBUG] 注册audio后路由数: {len(list(app.routes))}")
# v1_documents.router 自身已声明 /documents 前缀。
app.include_router(v1_documents.router, prefix="/api/v1", tags=["文档"])

logger.info(f"🔧 [DEBUG] 注册v1_documents后路由数: {len(list(app.routes))}")
app.include_router(crawler.router, prefix="/api/v1/crawler", tags=["爬虫"])
app.include_router(search.router, prefix="/api/v1/search", tags=["搜索"])
app.include_router(rag.router, tags=["RAG"])
app.include_router(learning.router, prefix="/api/v1", tags=["学习引擎"])  # Hermes Learning Engine
logger.info(f"🔧 [DEBUG] 学习引擎API已注册")

# 可选但已有实现的功能入口，避免功能文件存在却没有程序入口。
include_optional_router("app.api.quality", prefix="/api/quality", tags=["质量控制"])
include_optional_router("app.api.monitoring", prefix="/api")
include_optional_router("app.api.permissions", prefix="/api")
include_optional_router("app.api.proposal", prefix="/api")
include_optional_router("app.api.source_traceback", prefix="/api")
include_optional_router("app.api.v1.tasks", prefix="/api/v1")
include_optional_router("app.api.v1.super_agents")
include_optional_router("app.api.v1.chunks_quantification")
include_optional_router("app.api.v1.topic_analysis")
include_optional_router("app.api.quantification")

# 监控和健康检查端点
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus 指标端点"""
    try:
        from app.middleware.prometheus_middleware import metrics_endpoint
        return metrics_endpoint()
    except ImportError:
        from fastapi import Response
        return Response(content="Metrics not available", status_code=503)

@app.get("/health")
async def health():
    """健康检查端点"""
    try:
        from app.core.health_check import health_endpoint
        return await health_endpoint()
    except ImportError:
        return {"status": "unknown"}

@app.get("/health/ready")
async def readiness():
    """就绪检查端点"""
    try:
        from app.core.health_check import readiness_endpoint
        return await readiness_endpoint()
    except ImportError:
        return {"status": "ready"}

@app.get("/health/live")
async def liveness():
    """存活检查端点"""
    try:
        from app.core.health_check import liveness_endpoint
        return await liveness_endpoint()
    except ImportError:
        return {"status": "alive"}


@app.get("/api/runtime/version", include_in_schema=False)
async def runtime_version(request: Request):
    """桌面启动器用来确认当前端口加载的是唯一正版后端。"""
    server = request.scope.get("server")
    active_port = server[1] if isinstance(server, tuple) and len(server) > 1 else runtime_port()
    return {"version": RUNTIME_VERSION, "port": active_port}

logger.info(f"🔧 [DEBUG] 所有路由注册完成，最终路由数: {len(list(app.routes))}")
app.include_router(v1_workflows.router, prefix="/api/v1/workflows", tags=["工作流"])


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
    from app.models.project import ProjectDocument

    # 当前主表就是 ProjectDocument；历史版本曾通过不存在的 document_id
    # 连接旧 documents 表，导致前端项目文档列表直接 500。
    documents = db.query(ProjectDocument).filter(
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
    from app.models.project import ProjectDocument
    from sqlalchemy import func
    from datetime import datetime, timedelta

    # 统计文档数量
    total_documents = db.query(func.count(ProjectDocument.id)).filter(
        ProjectDocument.project_id == project_id
    ).scalar() or 0

    # 实体和关键词统一从主文档表的真实派生字段统计，避免误查旧 documents/entities 表。
    project_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).all()
    total_entities = 0
    keywords = set()
    for doc in project_docs:
        entities = doc.extracted_entities or doc.entities or []
        if isinstance(entities, dict):
            entities = list(entities.values())
        if isinstance(entities, list):
            total_entities += len(entities)
        for keyword in (doc.keywords or []):
            if isinstance(keyword, dict):
                keyword = keyword.get("word") or keyword.get("keyword")
            if keyword:
                keywords.add(str(keyword))
    total_keywords = len(keywords)

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

    # 实体类型分布：实体通过 metadata.project_ids/document_ids 与项目关联。
    # 当前统一实体表没有 project_id 列，不能再走历史查询。
    entity_types = {}
    project_document_ids = {str(doc.id) for doc in project_docs}
    for entity in db.query(Entity).all():
        metadata = entity.metadata_json or {}
        document_ids = {str(value) for value in (entity.document_ids or [])}
        project_ids = {str(value) for value in (metadata.get("project_ids") or [])}
        if str(project_id) not in project_ids and not (document_ids & project_document_ids):
            continue
        entity_type = entity.type or "unknown"
        entity_types[entity_type] = entity_types.get(entity_type, 0) + 1

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
        "storage_used": sum(int(doc.file_size or 0) for doc in project_docs),
        "last_analysis_time": max(
            (doc.processed_at for doc in project_docs if doc.processed_at),
            default=None,
        ),
    }

# 5. 知识图谱兼容路由（前端调用 /api/graph/*）
@app.post("/api/graph/build")
async def build_graph_compat(
    request: dict,
    db: Session = Depends(get_db)
):
    """兼容路由：前端调用 /api/graph/build"""
    from app.api import knowledge_graph as kg_api
    from fastapi import BackgroundTasks

    project_id = request.get("project_id")
    document_ids = request.get("document_ids")

    # 调用真实的知识图谱构建API
    try:
        return await kg_api.build_knowledge_graph(
            request=kg_api.BuildGraphRequest(
                project_id=project_id,
                document_ids=document_ids,
                force_rebuild=bool(request.get("force_rebuild", False)),
            ),
            background_tasks=BackgroundTasks(),
            db=db,
        )
    except Exception as e:
        from app.models.project import ProjectDocument
        logger.error("知识图谱构建兼容入口失败: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"知识图谱构建失败: {e}")

@app.get("/api/graph/statistics")
async def get_graph_statistics_compat(
    project_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """兼容路由：前端调用 /api/graph/statistics"""
    from app.models.project import ProjectDocument
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).all()
    node_count = 0
    type_distribution = {}
    for document in documents:
        entities = document.extracted_entities or document.entities or []
        if isinstance(entities, dict):
            entities = list(entities.values())
        for entity in entities if isinstance(entities, list) else []:
            node_count += 1
            entity_type = (
                entity.get("type") or entity.get("entity_type") or "unknown"
                if isinstance(entity, dict)
                else "unknown"
            )
            type_distribution[entity_type] = type_distribution.get(entity_type, 0) + 1

    return {
        "node_count": node_count,
        "edge_count": 0,
        "type_distribution": type_distribution,
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


@app.get("/health/dependencies", include_in_schema=False)
async def dependency_health_check():
    """依赖服务检查；主健康入口保持为 /health。"""
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
        host=runtime_host(),
        port=runtime_port(),
        reload=bool(getattr(settings, "debug", False)),
        log_level="info"
    )
