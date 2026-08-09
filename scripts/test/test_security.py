"""
安全模块测试
Security Module Tests

测试JWT、密码管理、API密钥、RBAC、OAuth2等功能
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.security import (
    # Auth
    TokenType,
    Permission,
    TokenPayload,
    AuthConfig,
    JWTManager,
    PasswordManager,
    APIKeyManager,
    RBACManager,
    AuthenticationService,

    # OAuth
    OAuthProvider,
    OAuthConfig,
    OAuthUserInfo,
    OAuthClient,
    OAuthManager,
    OAuthProviderConfigs,
)


# ============================================================================
# JWT Manager Tests
# ============================================================================

class TestJWTManager:
    """JWT管理器测试"""

    @pytest.fixture
    def config(self):
        return AuthConfig(
            secret_key="test_secret_key_12345",
            algorithm="HS256",
            access_token_expire_minutes=30,
            refresh_token_expire_days=7
        )

    @pytest.fixture
    def jwt_manager(self, config):
        return JWTManager(config)

    def test_create_access_token(self, jwt_manager):
        """测试创建访问令牌"""
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            permissions=["document:read", "document:write"],
            metadata={"role": "user"}
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, jwt_manager):
        """测试创建刷新令牌"""
        token = jwt_manager.create_refresh_token(
            user_id=1,
            username="testuser"
        )

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self, jwt_manager):
        """测试验证访问令牌"""
        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            permissions=["document:read"]
        )

        payload = jwt_manager.verify_token(token, TokenType.ACCESS)

        assert payload.user_id == 1
        assert payload.username == "testuser"
        assert payload.token_type == TokenType.ACCESS
        assert "document:read" in payload.permissions

    def test_verify_refresh_token(self, jwt_manager):
        """测试验证刷新令牌"""
        token = jwt_manager.create_refresh_token(
            user_id=1,
            username="testuser"
        )

        payload = jwt_manager.verify_token(token, TokenType.REFRESH)

        assert payload.user_id == 1
        assert payload.username == "testuser"
        assert payload.token_type == TokenType.REFRESH

    def test_verify_expired_token(self, config):
        """测试验证过期令牌"""
        # 创建立即过期的配置
        expired_config = AuthConfig(
            secret_key=config.secret_key,
            access_token_expire_minutes=-1  # 负数导致立即过期
        )
        jwt_manager = JWTManager(expired_config)

        token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            permissions=[]
        )

        # 等待一点时间确保过期
        import time
        time.sleep(0.1)

        with pytest.raises(ValueError, match="Token has expired"):
            jwt_manager.verify_token(token)

    def test_verify_invalid_token(self, jwt_manager):
        """测试验证无效令牌"""
        with pytest.raises(ValueError, match="Invalid token"):
            jwt_manager.verify_token("invalid_token_string")

    def test_verify_wrong_token_type(self, jwt_manager):
        """测试验证错误类型的令牌"""
        access_token = jwt_manager.create_access_token(
            user_id=1,
            username="testuser",
            permissions=[]
        )

        with pytest.raises(ValueError, match="Invalid token type"):
            jwt_manager.verify_token(access_token, TokenType.REFRESH)

    def test_refresh_access_token(self, jwt_manager):
        """测试刷新访问令牌"""
        refresh_token = jwt_manager.create_refresh_token(
            user_id=1,
            username="testuser"
        )

        new_access_token = jwt_manager.refresh_access_token(
            refresh_token,
            permissions=["document:read", "ai:query"]
        )

        payload = jwt_manager.verify_token(new_access_token, TokenType.ACCESS)
        assert payload.user_id == 1
        assert payload.username == "testuser"
        assert "document:read" in payload.permissions
        assert "ai:query" in payload.permissions


# ============================================================================
# Password Manager Tests
# ============================================================================

class TestPasswordManager:
    """密码管理器测试"""

    @pytest.fixture
    def config(self):
        return AuthConfig(
            secret_key="test_key",
            min_password_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_digit=True,
            require_special=True,
            password_hash_rounds=4  # 降低轮数加快测试
        )

    @pytest.fixture
    def password_manager(self, config):
        return PasswordManager(config)

    def test_hash_password(self, password_manager):
        """测试密码哈希"""
        password = "TestPassword123!"
        hashed = password_manager.hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_correct_password(self, password_manager):
        """测试验证正确密码"""
        password = "TestPassword123!"
        hashed = password_manager.hash_password(password)

        assert password_manager.verify_password(password, hashed) is True

    def test_verify_incorrect_password(self, password_manager):
        """测试验证错误密码"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = password_manager.hash_password(password)

        assert password_manager.verify_password(wrong_password, hashed) is False

    def test_validate_strong_password(self, password_manager):
        """测试验证强密码"""
        password = "StrongPass123!"
        is_valid, errors = password_manager.validate_password_strength(password)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_weak_password_too_short(self, password_manager):
        """测试验证过短密码"""
        password = "Sh0rt!"
        is_valid, errors = password_manager.validate_password_strength(password)

        assert is_valid is False
        assert any("at least 8 characters" in err for err in errors)

    def test_validate_weak_password_no_uppercase(self, password_manager):
        """测试验证无大写字母密码"""
        password = "weakpass123!"
        is_valid, errors = password_manager.validate_password_strength(password)

        assert is_valid is False
        assert any("uppercase letter" in err for err in errors)

    def test_validate_weak_password_no_digit(self, password_manager):
        """测试验证无数字密码"""
        password = "WeakPassword!"
        is_valid, errors = password_manager.validate_password_strength(password)

        assert is_valid is False
        assert any("digit" in err for err in errors)

    def test_validate_weak_password_no_special(self, password_manager):
        """测试验证无特殊字符密码"""
        password = "WeakPassword123"
        is_valid, errors = password_manager.validate_password_strength(password)

        assert is_valid is False
        assert any("special character" in err for err in errors)


# ============================================================================
# API Key Manager Tests
# ============================================================================

class TestAPIKeyManager:
    """API密钥管理器测试"""

    @pytest.fixture
    def config(self):
        return AuthConfig(
            secret_key="test_key",
            api_key_prefix="fma_",
            api_key_length=32
        )

    @pytest.fixture
    def api_key_manager(self, config):
        return APIKeyManager(config)

    def test_generate_api_key(self, api_key_manager):
        """测试生成API密钥"""
        raw_key, hashed_key = api_key_manager.generate_api_key()

        assert raw_key.startswith("fma_")
        assert isinstance(hashed_key, str)
        assert len(hashed_key) == 64  # SHA256十六进制长度

    def test_verify_api_key(self, api_key_manager):
        """测试验证API密钥"""
        raw_key, hashed_key = api_key_manager.generate_api_key()

        assert api_key_manager.verify_api_key(raw_key, hashed_key) is True

    def test_verify_wrong_api_key(self, api_key_manager):
        """测试验证错误的API密钥"""
        _, hashed_key = api_key_manager.generate_api_key()
        wrong_raw_key, _ = api_key_manager.generate_api_key()

        assert api_key_manager.verify_api_key(wrong_raw_key, hashed_key) is False


# ============================================================================
# RBAC Manager Tests
# ============================================================================

class TestRBACManager:
    """RBAC管理器测试"""

    @pytest.fixture
    def rbac_manager(self):
        return RBACManager()

    def test_default_roles(self, rbac_manager):
        """测试默认角色"""
        assert "admin" in rbac_manager.role_permissions
        assert "user" in rbac_manager.role_permissions
        assert "guest" in rbac_manager.role_permissions

    def test_add_custom_role(self, rbac_manager):
        """测试添加自定义角色"""
        rbac_manager.add_role("editor", {
            Permission.DOCUMENT_READ.value,
            Permission.DOCUMENT_WRITE.value
        })

        assert "editor" in rbac_manager.role_permissions
        assert Permission.DOCUMENT_READ.value in rbac_manager.role_permissions["editor"]

    def test_add_permission_to_role(self, rbac_manager):
        """测试为角色添加权限"""
        rbac_manager.add_permission_to_role("user", Permission.AI_TRAIN.value)

        assert Permission.AI_TRAIN.value in rbac_manager.role_permissions["user"]

    def test_remove_permission_from_role(self, rbac_manager):
        """测试从角色移除权限"""
        rbac_manager.remove_permission_from_role("user", Permission.DOCUMENT_WRITE.value)

        assert Permission.DOCUMENT_WRITE.value not in rbac_manager.role_permissions["user"]

    def test_assign_role_to_user(self, rbac_manager):
        """测试为用户分配角色"""
        user_id = 1
        rbac_manager.assign_role_to_user(user_id, "admin")

        assert "admin" in rbac_manager.user_roles[user_id]

    def test_remove_role_from_user(self, rbac_manager):
        """测试从用户移除角色"""
        user_id = 1
        rbac_manager.assign_role_to_user(user_id, "admin")
        rbac_manager.remove_role_from_user(user_id, "admin")

        assert "admin" not in rbac_manager.user_roles.get(user_id, set())

    def test_get_user_permissions(self, rbac_manager):
        """测试获取用户权限"""
        user_id = 1
        rbac_manager.assign_role_to_user(user_id, "user")

        permissions = rbac_manager.get_user_permissions(user_id)

        assert Permission.DOCUMENT_READ.value in permissions
        assert Permission.DOCUMENT_WRITE.value in permissions

    def test_has_permission(self, rbac_manager):
        """测试检查用户权限"""
        user_id = 1
        rbac_manager.assign_role_to_user(user_id, "user")

        assert rbac_manager.has_permission(user_id, Permission.DOCUMENT_READ.value) is True
        assert rbac_manager.has_permission(user_id, Permission.USER_DELETE.value) is False

    def test_admin_has_all_permissions(self, rbac_manager):
        """测试管理员拥有所有权限"""
        user_id = 1
        rbac_manager.assign_role_to_user(user_id, "admin")

        # 管理员应该有任何权限（因为有admin:*）
        assert rbac_manager.has_permission(user_id, Permission.DOCUMENT_READ.value) is True
        assert rbac_manager.has_permission(user_id, Permission.USER_DELETE.value) is True

    def test_has_any_permission(self, rbac_manager):
        """测试检查用户是否有任意权限"""
        user_id = 1
        rbac_manager.assign_role_to_user(user_id, "guest")

        assert rbac_manager.has_any_permission(user_id, [
            Permission.DOCUMENT_READ.value,
            Permission.DOCUMENT_WRITE.value
        ]) is True

    def test_has_all_permissions(self, rbac_manager):
        """测试检查用户是否有所有权限"""
        user_id = 1
        rbac_manager.assign_role_to_user(user_id, "user")

        assert rbac_manager.has_all_permissions(user_id, [
            Permission.DOCUMENT_READ.value,
            Permission.DOCUMENT_WRITE.value
        ]) is True

        assert rbac_manager.has_all_permissions(user_id, [
            Permission.DOCUMENT_READ.value,
            Permission.USER_DELETE.value
        ]) is False


# ============================================================================
# Authentication Service Tests
# ============================================================================

class TestAuthenticationService:
    """认证服务测试"""

    @pytest.fixture
    def config(self):
        return AuthConfig(
            secret_key="test_secret_key",
            max_login_attempts=3,
            lockout_duration_minutes=15,
            password_hash_rounds=4
        )

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.fixture
    def auth_service(self, config, mock_session):
        return AuthenticationService(config, mock_session)

    @pytest.mark.asyncio
    async def test_register_user(self, auth_service):
        """测试用户注册"""
        result = await auth_service.register_user(
            username="newuser",
            password="StrongPass123!",
            email="newuser@example.com",
            roles=["user"]
        )

        assert result["username"] == "newuser"
        assert result["email"] == "newuser@example.com"
        assert "user" in result["roles"]

    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, auth_service):
        """测试注册弱密码用户"""
        with pytest.raises(ValueError, match="Password validation failed"):
            await auth_service.register_user(
                username="newuser",
                password="weak",
                email="newuser@example.com"
            )

    @pytest.mark.asyncio
    async def test_account_lockout(self, auth_service):
        """测试账户锁定"""
        username = "testuser"

        # 记录多次失败尝试
        for _ in range(auth_service.config.max_login_attempts):
            auth_service._record_login_attempt(username)

        # 应该被锁定
        assert auth_service._is_account_locked(username) is True

    @pytest.mark.asyncio
    async def test_clear_login_attempts(self, auth_service):
        """测试清除登录尝试"""
        username = "testuser"

        # 记录失败尝试
        auth_service._record_login_attempt(username)
        assert len(auth_service.login_attempts[username]) > 0

        # 清除
        auth_service._clear_login_attempts(username)
        assert username not in auth_service.login_attempts

    @pytest.mark.asyncio
    async def test_create_api_key(self, auth_service):
        """测试创建API密钥"""
        result = await auth_service.create_api_key(
            user_id=1,
            name="test_api_key",
            permissions=["document:read", "ai:query"],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        assert result["api_key"].startswith("fma_")
        assert result["name"] == "test_api_key"
        assert "document:read" in result["permissions"]


# ============================================================================
# OAuth Client Tests
# ============================================================================

class TestOAuthClient:
    """OAuth客户端测试"""

    @pytest.fixture
    def oauth_config(self):
        return OAuthConfig(
            provider=OAuthProvider.GITHUB,
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/auth/callback",
            scope=["user:email", "read:user"],
            authorize_url=OAuthProviderConfigs.GITHUB["authorize_url"],
            token_url=OAuthProviderConfigs.GITHUB["token_url"],
            userinfo_url=OAuthProviderConfigs.GITHUB["userinfo_url"]
        )

    @pytest.fixture
    def oauth_client(self, oauth_config):
        return OAuthClient(oauth_config)

    def test_get_authorization_url(self, oauth_client):
        """测试获取授权URL"""
        url, state = oauth_client.get_authorization_url()

        assert "github.com/login/oauth/authorize" in url
        assert "client_id=test_client_id" in url
        assert f"state={state}" in url
        assert len(state) > 0

    def test_get_authorization_url_with_state(self, oauth_client):
        """测试使用自定义状态获取授权URL"""
        custom_state = "my_custom_state"
        url, state = oauth_client.get_authorization_url(state=custom_state)

        assert state == custom_state
        assert f"state={custom_state}" in url

    @pytest.mark.asyncio
    async def test_exchange_code_for_token(self, oauth_client):
        """测试交换授权码"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "scope": "user:email"
        }

        with patch.object(oauth_client.http_client, 'post', return_value=mock_response):
            result = await oauth_client.exchange_code_for_token("test_code")

            assert result["access_token"] == "test_access_token"
            assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_get_user_info_github(self, oauth_client):
        """测试获取GitHub用户信息"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 12345,
            "login": "testuser",
            "email": "test@example.com",
            "name": "Test User",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345"
        }

        with patch.object(oauth_client.http_client, 'get', return_value=mock_response):
            user_info = await oauth_client.get_user_info("test_access_token")

            assert user_info.provider == OAuthProvider.GITHUB
            assert user_info.provider_user_id == "12345"
            assert user_info.email == "test@example.com"
            assert user_info.name == "Test User"

    @pytest.mark.asyncio
    async def test_authenticate_flow(self, oauth_client):
        """测试完整认证流程"""
        # Mock令牌交换
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer"
        }

        # Mock用户信息获取
        mock_user_response = MagicMock()
        mock_user_response.status_code = 200
        mock_user_response.json.return_value = {
            "id": 12345,
            "email": "test@example.com",
            "name": "Test User"
        }

        async def mock_post(*args, **kwargs):
            return mock_token_response

        async def mock_get(*args, **kwargs):
            return mock_user_response

        with patch.object(oauth_client.http_client, 'post', side_effect=mock_post):
            with patch.object(oauth_client.http_client, 'get', side_effect=mock_get):
                token_response, user_info = await oauth_client.authenticate("test_code")

                assert token_response["access_token"] == "test_access_token"
                assert user_info.provider_user_id == "12345"
                assert user_info.email == "test@example.com"


# ============================================================================
# OAuth Manager Tests
# ============================================================================

class TestOAuthManager:
    """OAuth管理器测试"""

    @pytest.fixture
    def oauth_manager(self):
        return OAuthManager()

    def test_register_github_provider(self, oauth_manager):
        """测试注册GitHub提供商"""
        oauth_manager.register_provider(
            provider=OAuthProvider.GITHUB,
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback"
        )

        client = oauth_manager.get_client(OAuthProvider.GITHUB)
        assert client is not None
        assert client.config.provider == OAuthProvider.GITHUB

    def test_register_google_provider(self, oauth_manager):
        """测试注册Google提供商"""
        oauth_manager.register_provider(
            provider=OAuthProvider.GOOGLE,
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8000/callback"
        )

        client = oauth_manager.get_client(OAuthProvider.GOOGLE)
        assert client is not None
        assert client.config.provider == OAuthProvider.GOOGLE

    def test_get_nonexistent_client(self, oauth_manager):
        """测试获取不存在的客户端"""
        client = oauth_manager.get_client(OAuthProvider.GITLAB)
        assert client is None

    @pytest.mark.asyncio
    async def test_close_all_clients(self, oauth_manager):
        """测试关闭所有客户端"""
        oauth_manager.register_provider(
            provider=OAuthProvider.GITHUB,
            client_id="test_id",
            client_secret="test_secret",
            redirect_uri="http://localhost/callback"
        )

        await oauth_manager.close_all()
        # 验证没有抛出异常即可


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
