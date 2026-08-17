"""
FieldMind单元测试框架
使用pytest进行全面测试
"""

import pytest
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

# 测试配置
from app.core.database import SessionLocal, engine
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import text

# 创建测试客户端
client = TestClient(app)


class TestHealthCheck:
    """健康检查测试"""

    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]


class TestAuthentication:
    """认证测试"""

    def test_register_success(self):
        """测试用户注册成功"""
        import time
        user_data = {
            "username": f"test_user_{int(time.time())}",
            "email": "test@example.com",
            "password": "Test123456",
            "full_name": "测试用户"
        }
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data or "user_id" in data

    def test_login_success(self):
        """测试用户登录成功"""
        # 先注册
        import time
        username = f"test_user_{int(time.time())}"
        password = "Test123456"

        register_data = {
            "username": username,
            "email": "test@example.com",
            "password": password,
            "full_name": "测试用户"
        }
        client.post("/api/auth/register", json=register_data)

        # 再登录
        login_data = {
            "username": username,
            "password": password
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_password(self):
        """测试错误密码登录失败"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code in [401, 404]


class TestProjects:
    """项目管理测试"""

    @pytest.fixture
    def auth_token(self):
        """获取认证token"""
        import time
        username = f"test_user_{int(time.time())}"
        password = "Test123456"

        # 注册
        register_data = {
            "username": username,
            "email": "test@example.com",
            "password": password,
            "full_name": "测试用户"
        }
        client.post("/api/auth/register", json=register_data)

        # 登录
        login_data = {
            "username": username,
            "password": password
        }
        response = client.post("/api/auth/login", data=login_data)
        return response.json()["access_token"]

    def test_list_projects(self, auth_token):
        """测试获取项目列表"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/api/projects/", headers=headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_project(self, auth_token):
        """测试创建项目"""
        import time
        headers = {"Authorization": f"Bearer {auth_token}"}
        project_data = {
            "name": f"测试项目_{int(time.time())}",
            "description": "单元测试创建的项目"
        }
        response = client.post("/api/projects/", json=project_data, headers=headers)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["name"] == project_data["name"]


class TestDocuments:
    """文档管理测试"""

    @pytest.fixture
    def auth_and_project(self):
        """获取认证token和项目ID"""
        import time
        username = f"test_user_{int(time.time())}"
        password = "Test123456"

        # 注册
        register_data = {
            "username": username,
            "email": "test@example.com",
            "password": password,
            "full_name": "测试用户"
        }
        client.post("/api/auth/register", json=register_data)

        # 登录
        login_data = {
            "username": username,
            "password": password
        }
        response = client.post("/api/auth/login", data=login_data)
        token = response.json()["access_token"]

        # 创建项目
        headers = {"Authorization": f"Bearer {token}"}
        project_data = {
            "name": f"测试项目_{int(time.time())}",
            "description": "单元测试项目"
        }
        response = client.post("/api/projects/", json=project_data, headers=headers)
        project_id = response.json()["id"]

        return token, project_id

    def test_upload_document(self, auth_and_project):
        """测试上传文档"""
        token, project_id = auth_and_project
        headers = {"Authorization": f"Bearer {token}"}

        import io
        test_content = "测试内容：王大爷说杀猪菜是传统美食".encode('utf-8')
        files = {
            "file": ("test.txt", io.BytesIO(test_content), "text/plain")
        }
        data = {"project_id": project_id}

        response = client.post("/api/documents/upload", files=files, data=data, headers=headers)
        assert response.status_code in [200, 201]
        result = response.json()
        assert "id" in result or "document_id" in result


class TestFactStatements:
    """fact_statements测试"""

    def test_fact_statements_table_exists(self):
        """测试fact_statements表存在"""
        db = SessionLocal()
        try:
            count = db.execute(text("SELECT COUNT(*) FROM fact_statements")).scalar()
            assert count >= 0
        finally:
            db.close()

    def test_fact_statement_populator(self):
        """测试事实陈述填充器"""
        from app.services.fact_statement_populator import FactStatementPopulator

        populator = FactStatementPopulator()
        test_text = "王大爷说，杀猪菜是我们村的传统美食。"

        statements = populator.extract_statements(test_text)
        assert len(statements) > 0
        assert statements[0]['content'] == test_text


class TestAntiHallucination:
    """反幻觉系统测试"""

    def test_hallucination_detector(self):
        """测试幻觉检测器"""
        from app.services.anti_hallucination_report import HallucinationDetector

        # 测试1: 正常报告（应该通过）
        facts = {"count": 45}
        report = "共发现45次提及"
        is_valid, errors = HallucinationDetector.validate_report(report, facts)
        assert is_valid
        assert len(errors) == 0

        # 测试2: 编造数字（应该拦截）
        report_fake = "共发现100次提及"
        is_valid, errors = HallucinationDetector.validate_report(report_fake, facts)
        assert not is_valid
        assert len(errors) > 0


class TestEmbedding:
    """向量化测试"""

    def test_flag_embedding_service(self):
        """测试FlagEmbedding服务"""
        from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend

        service = FlagEmbeddingService()

        # 测试编码
        test_texts = ["测试文本：王大爷说杀猪菜是传统美食"]
        embeddings = service.encode_documents(test_texts)

        assert embeddings.shape[0] == 1
        assert embeddings.shape[1] == 512  # bge-small-zh-v1.5的维度


class TestRAGEngine:
    """RAG引擎测试"""

    def test_rag_engine_initialization(self):
        """测试RAG引擎初始化"""
        from app.core.rag_engine import rag_engine

        assert rag_engine is not None
        assert rag_engine.embeddings is not None
        assert rag_engine.collection is not None

    def test_chromadb_query(self):
        """测试ChromaDB查询"""
        from app.core.rag_engine import rag_engine

        if rag_engine.collection.count() > 0:
            # 测试查询
            results = rag_engine.collection.query(
                query_texts=["传统美食"],
                n_results=1
            )
            assert "ids" in results
            assert len(results["ids"]) > 0


# 运行测试
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 运行FieldMind单元测试")
    print("=" * 70)

    # 使用pytest运行
    pytest.main([__file__, "-v", "--tb=short"])
