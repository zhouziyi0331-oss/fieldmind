"""
Pytest 配置和共享 fixtures
"""

import pytest
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base
from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.models.project import Project


# ==================== 数据库 Fixtures ====================

@pytest.fixture(scope="function")
def db_engine():
    """创建测试数据库引擎（内存 SQLite）"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """创建测试客户端"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==================== 数据 Fixtures ====================

@pytest.fixture
def sample_user(db_session: Session):
    """创建测试用户"""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="$2b$12$test_hashed_password",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session: Session):
    """创建管理员用户"""
    user = User(
        email="admin@example.com",
        username="admin",
        hashed_password="$2b$12$test_hashed_password",
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_project(db_session: Session, sample_user):
    """创建测试项目"""
    project = Project(
        name="Test Project",
        description="A test project",
        owner_id=sample_user.id,
        status="active"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def multiple_projects(db_session: Session, sample_user):
    """创建多个测试项目"""
    projects = []
    for i in range(5):
        project = Project(
            name=f"Test Project {i+1}",
            description=f"Description {i+1}",
            owner_id=sample_user.id,
            status="active"
        )
        db_session.add(project)
        projects.append(project)

    db_session.commit()
    for project in projects:
        db_session.refresh(project)

    return projects


# ==================== 认证 Fixtures ====================

@pytest.fixture
def auth_headers(sample_user):
    """创建认证头部"""
    # 简化版本，实际应该生成真实的 JWT token
    token = "test_token_123"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    """创建管理员认证头部"""
    token = "admin_token_123"
    return {"Authorization": f"Bearer {token}"}


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_cache():
    """Mock 缓存服务"""
    from unittest.mock import MagicMock
    cache = MagicMock()
    cache.get.return_value = None
    cache.set.return_value = True
    cache.delete.return_value = True
    return cache


@pytest.fixture
def mock_sentry():
    """Mock Sentry 服务"""
    from unittest.mock import MagicMock
    sentry = MagicMock()
    sentry.enabled = False
    return sentry


@pytest.fixture
def mock_prometheus():
    """Mock Prometheus 服务"""
    from unittest.mock import MagicMock
    prometheus = MagicMock()
    prometheus.enabled = False
    return prometheus


# ==================== 配置 ====================

def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
