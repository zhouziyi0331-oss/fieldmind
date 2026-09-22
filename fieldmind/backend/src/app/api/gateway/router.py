"""
路由管理器 (Router Manager)

管理所有API路由，将请求分发到对应的服务
"""
import logging
from typing import Dict, Any, Optional, Callable
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.api.gateway.auth import require_auth, require_roles
from app.core.database import get_db
from app.services.unified_ai_service import UnifiedAIService

logger = logging.getLogger(__name__)


class RouterManager:
    """路由管理器"""

    def __init__(self):
        """初始化路由管理器"""
        # 创建路由器
        self.v1_router = APIRouter(prefix="/api/v1")

        # 服务映射
        self._service_cache = {}

        logger.info("✅ 路由管理器初始化")

    def setup_routes(self):
        """配置所有路由"""
        self._setup_auth_routes()
        self._setup_chat_routes()
        self._setup_agents_routes()
        self._setup_rag_routes()
        self._setup_skills_routes()

        logger.info("✅ 所有路由已配置")

    # ==================== 认证路由 ====================

    def _setup_auth_routes(self):
        """配置认证相关路由"""
        from app.api.gateway.auth import AuthService

        @self.v1_router.post("/auth/login")
        async def login(
            username: str,
            password: str,
            db: Session = Depends(get_db)
        ):
            """
            用户登录

            Args:
                username: 用户名
                password: 密码

            Returns:
                JWT token
            """
            # TODO: 从数据库验证用户
            # 这里简化实现
            if username and password:
                token = AuthService.create_jwt_token(
                    user_id=1,
                    username=username,
                    email=f"{username}@example.com",
                    roles=['user']
                )

                return {
                    "success": True,
                    "data": {
                        "token": token,
                        "token_type": "bearer",
                        "expires_in": 3600
                    }
                }

            return {
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid username or password"
                }
            }

        @self.v1_router.post("/auth/register")
        async def register(
            username: str,
            password: str,
            email: str,
            db: Session = Depends(get_db)
        ):
            """
            用户注册

            Args:
                username: 用户名
                password: 密码
                email: 邮箱

            Returns:
                注册结果
            """
            # TODO: 实现用户注册逻辑
            return {
                "success": True,
                "data": {
                    "message": "User registered successfully",
                    "user_id": 1
                }
            }

        @self.v1_router.get("/auth/me")
        async def get_current_user(
            request: Request,
            user = Depends(require_auth)
        ):
            """
            获取当前用户信息

            Returns:
                用户信息
            """
            return {
                "success": True,
                "data": user
            }

    # ==================== 对话路由 ====================

    def _setup_chat_routes(self):
        """配置对话相关路由"""

        @self.v1_router.post("/chat")
        async def chat(
            request: Request,
            query: str,
            session_id: str,
            project_id: Optional[int] = None,
            config: Optional[Dict[str, Any]] = None,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            AI对话

            Args:
                query: 用户查询
                session_id: 会话ID
                project_id: 项目ID
                config: 对话配置

            Returns:
                对话结果
            """
            service = UnifiedAIService(db)

            result = service.chat.chat(
                query=query,
                session_id=session_id,
                project_id=project_id,
                user_id=user['user_id'],
                config=config or {}
            )

            return {
                "success": True,
                "data": result
            }

        @self.v1_router.post("/chat/stream")
        async def chat_stream(
            request: Request,
            query: str,
            session_id: str,
            project_id: Optional[int] = None,
            config: Optional[Dict[str, Any]] = None,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            流式对话

            Args:
                query: 用户查询
                session_id: 会话ID
                project_id: 项目ID
                config: 对话配置

            Returns:
                流式响应
            """
            from fastapi.responses import StreamingResponse

            service = UnifiedAIService(db)

            async def generate():
                async for chunk in service.chat.stream_chat(
                    query=query,
                    session_id=session_id,
                    project_id=project_id,
                    user_id=user['user_id'],
                    config=config or {}
                ):
                    yield f"data: {chunk}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

    # ==================== Agent路由 ====================

    def _setup_agents_routes(self):
        """配置Agent相关路由"""

        @self.v1_router.post("/agents/execute")
        async def execute_agent(
            request: Request,
            agent_type: str,
            input_data: Dict[str, Any],
            config: Optional[Dict[str, Any]] = None,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            执行单个Agent

            Args:
                agent_type: Agent类型
                input_data: 输入数据
                config: 配置

            Returns:
                执行结果
            """
            service = UnifiedAIService(db)

            result = service.agents.execute_agent(
                agent_type=agent_type,
                input_data=input_data,
                config=config or {}
            )

            return {
                "success": True,
                "data": result
            }

        @self.v1_router.post("/agents/orchestrate")
        async def orchestrate_agents(
            request: Request,
            tasks: list,
            mode: str = "dependency",
            config: Optional[Dict[str, Any]] = None,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            编排多个Agent

            Args:
                tasks: 任务列表
                mode: 执行模式
                config: 配置

            Returns:
                编排结果
            """
            service = UnifiedAIService(db)

            result = service.agents.orchestrate_agents(
                tasks=tasks,
                mode=mode,
                config=config or {}
            )

            return {
                "success": True,
                "data": result
            }

        @self.v1_router.get("/agents/list")
        async def list_agents(
            request: Request,
            capability: Optional[str] = None,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            列出可用的Agent

            Args:
                capability: 能力过滤

            Returns:
                Agent列表
            """
            service = UnifiedAIService(db)

            agents = service.agents.list_available_agents(
                capability=capability
            )

            return {
                "success": True,
                "data": agents
            }

    # ==================== RAG路由 ====================

    def _setup_rag_routes(self):
        """配置RAG相关路由"""

        @self.v1_router.post("/rag/query")
        async def rag_query(
            request: Request,
            query: str,
            mode: str = "adaptive",
            top_k: int = 5,
            project_id: Optional[str] = None,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            RAG检索查询

            Args:
                query: 查询文本
                mode: 检索模式
                top_k: 返回数量
                project_id: 项目ID

            Returns:
                检索结果
            """
            service = UnifiedAIService(db)

            from app.core.rag.base_interface import RAGMode
            import asyncio

            # 转换模式
            rag_mode = RAGMode(mode)

            # 执行查询
            result = await service.rag.query(
                query=query,
                mode=rag_mode,
                top_k=top_k,
                project_id=project_id
            )

            return {
                "success": True,
                "data": result.to_dict() if hasattr(result, 'to_dict') else result
            }

        @self.v1_router.post("/rag/ingest")
        async def rag_ingest(
            request: Request,
            content: str,
            document_id: str,
            project_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            RAG文档索引

            Args:
                content: 文档内容
                document_id: 文档ID
                project_id: 项目ID
                metadata: 元数据

            Returns:
                索引结果
            """
            service = UnifiedAIService(db)

            result = await service.rag.ingest(
                content=content,
                document_id=document_id,
                project_id=project_id,
                metadata=metadata
            )

            return {
                "success": True,
                "data": result
            }

    # ==================== 技能路由 ====================

    def _setup_skills_routes(self):
        """配置技能相关路由"""

        @self.v1_router.post("/skills/execute")
        async def execute_skill(
            request: Request,
            skill_id: str,
            input_data: Dict[str, Any],
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            执行技能

            Args:
                skill_id: 技能ID
                input_data: 输入数据

            Returns:
                执行结果
            """
            service = UnifiedAIService(db)

            result = await service.skills.execute_skill(
                skill_id=skill_id,
                input_data=input_data
            )

            return {
                "success": True,
                "data": result.to_dict() if hasattr(result, 'to_dict') else result
            }

        @self.v1_router.get("/skills/list")
        async def list_skills(
            request: Request,
            category: Optional[str] = None,
            status: Optional[str] = None,
            limit: int = 100,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            列出技能

            Args:
                category: 类别过滤
                status: 状态过滤
                limit: 返回数量

            Returns:
                技能列表
            """
            service = UnifiedAIService(db)

            skills = service.skills.list_skills(
                category=category,
                limit=limit
            )

            return {
                "success": True,
                "data": [s.to_dict() for s in skills]
            }

        @self.v1_router.post("/skills/recommend")
        async def recommend_skills(
            request: Request,
            context: Dict[str, Any],
            top_k: int = 5,
            user = Depends(require_auth),
            db: Session = Depends(get_db)
        ):
            """
            推荐技能

            Args:
                context: 上下文信息
                top_k: 返回数量

            Returns:
                推荐结果
            """
            service = UnifiedAIService(db)

            recommendations = service.skills.recommend_skills(
                context=context,
                top_k=top_k
            )

            return {
                "success": True,
                "data": [r.to_dict() for r in recommendations]
            }

    # ==================== 工具方法 ====================

    def get_router(self) -> APIRouter:
        """获取路由器"""
        return self.v1_router

    def get_routes_info(self) -> list:
        """获取所有路由信息"""
        routes_info = []

        for route in self.v1_router.routes:
            routes_info.append({
                'path': route.path,
                'methods': list(route.methods) if hasattr(route, 'methods') else [],
                'name': route.name
            })

        return routes_info


# 全局单例
_router_manager_instance = None


def get_router_manager() -> RouterManager:
    """获取路由管理器单例"""
    global _router_manager_instance
    if _router_manager_instance is None:
        _router_manager_instance = RouterManager()
        _router_manager_instance.setup_routes()
    return _router_manager_instance
