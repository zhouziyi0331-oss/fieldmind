"""
认证API测试
"""
import pytest
from fastapi.testclient import TestClient


class TestAuthAPI:
    """认证API测试类"""

    def test_register_user_success(self, client):
        """测试：成功注册用户"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["role"] == "researcher"
        assert data["is_active"] is True
        assert "id" in data

    def test_register_duplicate_email(self, client, test_user):
        """测试：重复邮箱注册失败"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",  # 已存在
                "username": "anotheruser",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "邮箱已被注册" in response.json()["detail"]

    def test_register_duplicate_username(self, client, test_user):
        """测试：重复用户名注册失败"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "another@example.com",
                "username": "testuser",  # 已存在
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "用户名已被使用" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """测试：无效邮箱格式"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "newuser",
                "password": "password123"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client):
        """测试：密码过短"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.com",
                "username": "newuser",
                "password": "123"  # 少于6字符
            }
        )

        assert response.status_code == 422

    def test_login_success(self, client, test_user):
        """测试：成功登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """测试：错误密码登录失败"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """测试：不存在的用户登录失败"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """测试：获取当前用户信息"""
        response = client.get(
            "/api/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "researcher"

    def test_get_current_user_no_token(self, client):
        """测试：无token获取用户信息失败"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """测试：无效token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    def test_refresh_token(self, client, test_user):
        """测试：刷新token"""
        # 先登录获取refresh_token
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )

        refresh_token = login_response.json()["refresh_token"]

        # 使用refresh_token获取新的access_token
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
