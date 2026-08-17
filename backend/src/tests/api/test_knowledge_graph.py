"""
知识图谱 API 测试
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectDocument
from app.core.database import get_db


@pytest.fixture
def db():
    """获取数据库会话"""
    db_gen = get_db()
    db_session = next(db_gen)
    yield db_session
    db_session.close()


class TestKnowledgeGraphAPI:
    """知识图谱 API 测试类"""

    def test_get_project_graph_success(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：成功获取项目知识图谱"""
        # 创建测试项目
        project = Project(
            name="测试项目",
            description="知识图谱测试",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # 创建测试文档
        doc = ProjectDocument(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/fake/path/test.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="张三在北京大学学习人工智能。李四是张三的同学。"
        )
        db.add(doc)
        db.commit()

        # Mock 知识图谱服务
        mock_graph = {
            "nodes": [
                {"id": "张三", "type": "PERSON", "properties": {}},
                {"id": "北京大学", "type": "ORGANIZATION", "properties": {}},
                {"id": "人工智能", "type": "FIELD", "properties": {}}
            ],
            "edges": [
                {"source": "张三", "target": "北京大学", "relation": "学习于"},
                {"source": "张三", "target": "人工智能", "relation": "学习"}
            ],
            "statistics": {
                "total_nodes": 3,
                "total_edges": 2,
                "node_types": {"PERSON": 1, "ORGANIZATION": 1, "FIELD": 1}
            }
        }

        with patch('app.api.knowledge_graph.knowledge_graph_service.build_graph_from_documents') as mock_build:
            mock_build.return_value = mock_graph

            response = client.get(
                f"/api/knowledge-graph/projects/{project.id}/graph",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "statistics" in data
        assert len(data["nodes"]) == 3
        assert len(data["edges"]) == 2
        assert data["statistics"]["total_nodes"] == 3

    def test_get_project_graph_not_found(self, client: TestClient, auth_headers: dict):
        """测试：项目不存在"""
        response = client.get(
            "/api/knowledge-graph/projects/99999/graph",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "项目不存在" in response.json()["detail"]

    def test_get_project_graph_empty_project(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：空项目返回空图谱"""
        # 创建空项目
        project = Project(
            name="空项目",
            description="无文档",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        response = client.get(
            f"/api/knowledge-graph/projects/{project.id}/graph",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == []
        assert data["edges"] == []
        assert data["statistics"]["total_nodes"] == 0
        assert "暂无已处理的文档" in data["message"]

    def test_get_project_graph_only_completed_documents(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：只处理已完成的文档"""
        project = Project(
            name="测试项目",
            description="测试",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        # 创建pending状态的文档
        doc = ProjectDocument(
            project_id=project.id,
            filename="pending.txt",
            original_filename="pending.txt",
            file_path="/fake/path/pending.txt",
            file_type="text/plain",
            file_size=1024,
            status="pending",
            text_content="这是待处理文档"
        )
        db.add(doc)
        db.commit()

        response = client.get(
            f"/api/knowledge-graph/projects/{project.id}/graph",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nodes"] == []
        assert "暂无已处理的文档" in data["message"]

    def test_get_project_keywords_success(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：成功获取项目关键词"""
        project = Project(
            name="测试项目",
            description="关键词测试",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        doc = ProjectDocument(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/fake/path/test.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="人工智能是计算机科学的一个分支。机器学习是人工智能的核心技术。"
        )
        db.add(doc)
        db.commit()

        # Mock 关键词提取
        mock_keywords = [
            {"keyword": "人工智能", "score": 0.95, "count": 2},
            {"keyword": "机器学习", "score": 0.85, "count": 1},
            {"keyword": "计算机科学", "score": 0.75, "count": 1}
        ]

        with patch('app.api.knowledge_graph.knowledge_graph_service.extract_keywords') as mock_extract:
            mock_extract.return_value = mock_keywords

            response = client.get(
                f"/api/knowledge-graph/projects/{project.id}/keywords",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["keyword"] == "人工智能"
        assert data[0]["score"] == 0.95

    def test_get_project_keywords_with_top_k(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：指定top_k参数"""
        project = Project(
            name="测试项目",
            description="测试",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        doc = ProjectDocument(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/fake/path/test.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="测试文档内容"
        )
        db.add(doc)
        db.commit()

        mock_keywords = [{"keyword": f"关键词{i}", "score": 0.9 - i*0.1} for i in range(20)]

        with patch('app.api.knowledge_graph.knowledge_graph_service.extract_keywords') as mock_extract:
            mock_extract.return_value = mock_keywords

            response = client.get(
                f"/api/knowledge-graph/projects/{project.id}/keywords?top_k=20",
                headers=auth_headers
            )

            # 验证传递了正确的top_k参数
            mock_extract.assert_called_once()
            call_args = mock_extract.call_args
            assert call_args[0][1] == 20

        assert response.status_code == 200

    def test_get_project_keywords_not_found(self, client: TestClient, auth_headers: dict):
        """测试：项目不存在"""
        response = client.get(
            "/api/knowledge-graph/projects/99999/keywords",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "项目不存在" in response.json()["detail"]

    def test_get_project_keywords_empty_project(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：空项目返回空列表"""
        project = Project(
            name="空项目",
            description="无文档",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        response = client.get(
            f"/api/knowledge-graph/projects/{project.id}/keywords",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_document_entities_success(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：成功获取文档实体"""
        project = Project(
            name="测试项目",
            description="测试",
            owner_id=1
        )
        db.add(project)
        db.commit()

        doc = ProjectDocument(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/fake/path/test.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="张三在北京大学学习。2023年毕业。"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Mock 实体提取
        mock_entities = {
            "PERSON": ["张三"],
            "ORGANIZATION": ["北京大学"],
            "DATE": ["2023年"]
        }

        with patch('app.api.knowledge_graph.knowledge_graph_service.extract_entities') as mock_extract:
            mock_extract.return_value = mock_entities

            response = client.get(
                f"/api/knowledge-graph/documents/{doc.id}/entities",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "statistics" in data
        assert data["entities"]["PERSON"] == ["张三"]
        assert data["statistics"]["PERSON"] == 1
        assert data["statistics"]["ORGANIZATION"] == 1

    def test_get_document_entities_not_found(self, client: TestClient, auth_headers: dict):
        """测试：文档不存在"""
        response = client.get(
            "/api/knowledge-graph/documents/99999/entities",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "文档不存在" in response.json()["detail"]

    def test_get_document_entities_no_content(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：文档无内容"""
        project = Project(
            name="测试项目",
            description="测试",
            owner_id=1
        )
        db.add(project)
        db.commit()

        doc = ProjectDocument(
            project_id=project.id,
            filename="empty.txt",
            original_filename="empty.txt",
            file_path="/fake/path/empty.txt",
            file_type="text/plain",
            file_size=0,
            status="completed",
            text_content=None
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        response = client.get(
            f"/api/knowledge-graph/documents/{doc.id}/entities",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["entities"] == {}
        assert "暂无文本内容" in data["message"]

    def test_get_project_graph_service_error(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：知识图谱服务异常"""
        project = Project(
            name="测试项目",
            description="测试",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        doc = ProjectDocument(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/fake/path/test.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="测试内容"
        )
        db.add(doc)
        db.commit()

        with patch('app.api.knowledge_graph.knowledge_graph_service.build_graph_from_documents') as mock_build:
            mock_build.side_effect = Exception("服务错误")

            response = client.get(
                f"/api/knowledge-graph/projects/{project.id}/graph",
                headers=auth_headers
            )

        assert response.status_code == 500
        assert "构建知识图谱失败" in response.json()["detail"]

    def test_get_keywords_service_error(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：关键词提取服务异常"""
        project = Project(
            name="测试项目",
            description="测试",
            owner_id=1
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        doc = ProjectDocument(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/fake/path/test.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="测试内容"
        )
        db.add(doc)
        db.commit()

        with patch('app.api.knowledge_graph.knowledge_graph_service.extract_keywords') as mock_extract:
            mock_extract.side_effect = Exception("提取错误")

            response = client.get(
                f"/api/knowledge-graph/projects/{project.id}/keywords",
                headers=auth_headers
            )

        assert response.status_code == 500
        assert "提取关键词失败" in response.json()["detail"]

    def test_get_entities_service_error(self, client: TestClient, auth_headers: dict, db: Session):
        """测试：实体提取服务异常"""
        project = Project(
            name="测试项目",
            description="测试",
            owner_id=1
        )
        db.add(project)
        db.commit()

        doc = ProjectDocument(
            project_id=project.id,
            filename="test.txt",
            original_filename="test.txt",
            file_path="/fake/path/test.txt",
            file_type="text/plain",
            file_size=1024,
            status="completed",
            text_content="测试内容"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        with patch('app.api.knowledge_graph.knowledge_graph_service.extract_entities') as mock_extract:
            mock_extract.side_effect = Exception("提取错误")

            response = client.get(
                f"/api/knowledge-graph/documents/{doc.id}/entities",
                headers=auth_headers
            )

        assert response.status_code == 500
        assert "提取实体失败" in response.json()["detail"]
