"""
项目 API 集成测试
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestProjectsAPI:
    """项目 API 测试"""

    def test_list_projects_empty(self, client: TestClient, db_session):
        """测试获取空项目列表"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_list_projects_with_data(self, client: TestClient, multiple_projects):
        """测试获取项目列表"""
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_project_by_id(self, client: TestClient, sample_project):
        """测试获取单个项目"""
        response = client.get(f"/api/v1/projects/{sample_project.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == sample_project.name

    def test_get_nonexistent_project(self, client: TestClient):
        """测试获取不存在的项目"""
        response = client.get("/api/v1/projects/99999")
        assert response.status_code == 404

    def test_create_project(self, client: TestClient, sample_user):
        """测试创建项目"""
        project_data = {
            "name": "New Test Project",
            "description": "A new test project",
            "settings": {}
        }
        response = client.post("/api/v1/projects", json=project_data)
        assert response.status_code in [200, 201]

    def test_update_project(self, client: TestClient, sample_project):
        """测试更新项目"""
        update_data = {
            "name": "Updated Project Name",
            "description": "Updated description"
        }
        response = client.put(
            f"/api/v1/projects/{sample_project.id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Project Name"

    def test_delete_project(self, client: TestClient, sample_project):
        """测试删除项目"""
        response = client.delete(f"/api/v1/projects/{sample_project.id}")
        assert response.status_code == 200

        # 验证项目已删除
        get_response = client.get(f"/api/v1/projects/{sample_project.id}")
        assert get_response.status_code == 404


@pytest.mark.integration
class TestProjectsPagination:
    """项目分页测试"""

    def test_pagination_first_page(self, client: TestClient, multiple_projects):
        """测试第一页"""
        response = client.get("/api/v1/projects?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["data"]) <= 2

    def test_pagination_second_page(self, client: TestClient, multiple_projects):
        """测试第二页"""
        response = client.get("/api/v1/projects?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["data"]) <= 2

    def test_pagination_limit_validation(self, client: TestClient):
        """测试分页限制验证"""
        # 负数应该被拒绝或转换为默认值
        response = client.get("/api/v1/projects?skip=-1&limit=-1")
        # 应该返回 422 验证错误或使用默认值
        assert response.status_code in [200, 422]


@pytest.mark.integration
class TestProjectsFiltering:
    """项目过滤测试"""

    def test_filter_by_status(self, client: TestClient, sample_project):
        """测试按状态过滤"""
        response = client.get("/api/v1/projects?status=active")
        assert response.status_code == 200

    def test_filter_archived_projects(self, client: TestClient):
        """测试过滤归档项目"""
        response = client.get("/api/v1/projects?include_archived=true")
        assert response.status_code == 200

    def test_search_projects(self, client: TestClient, sample_project):
        """测试搜索项目"""
        response = client.get(f"/api/v1/projects?search={sample_project.name}")
        assert response.status_code == 200
