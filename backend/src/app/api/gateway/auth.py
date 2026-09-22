"""
认证中间件 (Authentication Middleware)

支持JWT、API Key等多种认证方式
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
JWT_SECRET = "your-secret-key-change-in-production"  # 生产环境应从环境变量读取
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = timedelta(hours=1)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """认证中间件"""

    def __init__(self, app, skip_paths: Optional[list] = None):
        """
        初始化认证中间件

        Args:
            app: FastAPI应用
            skip_paths: 跳过认证的路径列表
        """
        super().__init__(app)

        # 默认跳过的路径
        self.skip_paths = skip_paths or [
            "/health",
            "/stats",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]

        logger.info("✅ 认证中间件初始化")

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否跳过认证
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        # 执行认证
        try:
            user = await self._authenticate(request)
            if user:
                request.state.user = user
                request.state.authenticated = True
            else:
                request.state.authenticated = False

            response = await call_next(request)
            return response

        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"❌ 认证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

    def _should_skip_auth(self, path: str) -> bool:
        """检查是否应该跳过认证"""
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return True
        return False

    async def _authenticate(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        执行认证

        优先级：JWT Token > API Key > Session

        Args:
            request: 请求对象

        Returns:
            用户信息字典，失败返回None
        """
        # 1. 尝试JWT认证
        user = await self._authenticate_jwt(request)
        if user:
            return user

        # 2. 尝试API Key认证
        user = await self._authenticate_api_key(request)
        if user:
            return user

        # 3. 未认证
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    async def _authenticate_jwt(self, request: Request) -> Optional[Dict[str, Any]]:
        """JWT认证"""
        # 从请求头获取token
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            # 验证并解码token
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            # 检查过期时间
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )

            # 返回用户信息
            return {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'email': payload.get('email'),
                'roles': payload.get('roles', []),
                'auth_type': 'jwt'
            }

        except jwt.InvalidTokenError as e:
            logger.warning(f"⚠️ JWT验证失败: {e}")
            return None

    async def _authenticate_api_key(self, request: Request) -> Optional[Dict[str, Any]]:
        """API Key认证"""
        # 从请求头获取API Key
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return None

        # TODO: 从数据库验证API Key
        # 这里简化实现
        if self._validate_api_key(api_key):
            return {
                'user_id': 'api_user',
                'username': 'api_user',
                'email': None,
                'roles': ['api'],
                'auth_type': 'api_key'
            }

        return None

    def _validate_api_key(self, api_key: str) -> bool:
        """验证API Key（简化实现）"""
        # TODO: 从数据库验证
        return len(api_key) == 32  # 简单验证


class AuthService:
    """认证服务"""

    @staticmethod
    def create_jwt_token(
        user_id: int,
        username: str,
        email: str,
        roles: list = None
    ) -> str:
        """
        创建JWT Token

        Args:
            user_id: 用户ID
            username: 用户名
            email: 邮箱
            roles: 角色列表

        Returns:
            JWT token字符串
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'roles': roles or [],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + JWT_EXPIRATION
        }

        token = jwt.encode(
            payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        return token

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT Token

        Args:
            token: JWT token

        Returns:
            解码后的payload，失败返回None
        """
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )
            return payload
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def hash_password(password: str) -> str:
        """
        密码哈希

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 哈希密码

        Returns:
            是否匹配
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def generate_api_key() -> str:
        """
        生成API Key

        Returns:
            32字符的API Key
        """
        import secrets
        return secrets.token_hex(16)


def require_auth(request: Request) -> Dict[str, Any]:
    """
    依赖项：要求认证

    使用方法：
    @app.get("/protected")
    async def protected_route(user = Depends(require_auth)):
        return {"user": user}

    Args:
        request: 请求对象

    Returns:
        用户信息

    Raises:
        HTTPException: 未认证
    """
    if not getattr(request.state, 'authenticated', False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    return request.state.user


def require_roles(allowed_roles: list):
    """
    依赖项：要求特定角色

    使用方法：
    @app.get("/admin")
    async def admin_route(user = Depends(require_roles(['admin']))):
        return {"message": "Admin only"}

    Args:
        allowed_roles: 允许的角色列表

    Returns:
        依赖项函数
    """
    def role_checker(request: Request) -> Dict[str, Any]:
        user = require_auth(request)

        user_roles = user.get('roles', [])
        if not any(role in allowed_roles for role in user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {allowed_roles}"
            )

        return user

    return role_checker
