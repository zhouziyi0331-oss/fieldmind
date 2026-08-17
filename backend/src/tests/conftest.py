"""
Pytest 配置文件
"""
import os
import pytest
import tempfile

# ⚠️ 重要：必须在导入任何app模块之前设置环境变量
# 使用临时文件数据库而不是内存数据库，避免连接隔离问题
test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
test_db_path = test_db_file.name
test_db_file.close()

os.environ["DATABASE_URL"] = f"sqlite:///{test_db_path}"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-for-testing-only"

# 现在导入app模块
from fastapi.testclient import TestClient
from app.core.database import Base, engine
from app.main_simple import app

# 导入所有模型以确保它们被注册到Base.metadata
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.federation import FieldMindObject, ObjectRelation, FactStatement


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时清理临时数据库文件"""
    import os
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@pytest.fixture(scope="function")
def client():
    """创建测试客户端"""
    # 先创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建TestClient，并禁用lifespan事件
    # 这样可以避免startup事件再次尝试创建表
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    # 测试结束后清理所有表
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(client):
    """创建测试用户"""
    # 通过API注册用户，确保使用相同的密码哈希方式
    response = client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """获取认证token"""
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """返回带认证的请求头"""
    return {"Authorization": f"Bearer {auth_token}"}
