"""
项目API测试
"""
import pytest
from fastapi.testclient import TestClient


class TestProjectAPI:
    """项目API测试类"""

    def test_create_project_success(self, client, auth_headers):
        """测试：成功创建项目"""
        response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "测试项目",
                "description": "这是一个测试项目"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "测试项目"
        assert data["description"] == "这是一个测试项目"
        assert "id" in data
        assert "created_at" in data

    def test_create_project_no_auth(self, client):
        """测试：未认证创建项目失败"""
        response = client.post(
            "/api/projects/",
            json={
                "name": "测试项目",
                "description": "这是一个测试项目"
            }
        )

        assert response.status_code == 401

    def test_create_project_missing_name(self, client, auth_headers):
        """测试：缺少项目名称"""
        response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "description": "这是一个测试项目"
            }
        )

        assert response.status_code == 422

    def test_list_projects(self, client, auth_headers):
        """测试：获取项目列表"""
        # 先创建两个项目
        client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "项目1", "description": "描述1"}
        )
        client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "项目2", "description": "描述2"}
        )

        # 获取列表
        response = client.get("/api/projects/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "projects" in data
        assert data["total"] >= 2
        assert len(data["projects"]) >= 2
        project_names = [p["name"] for p in data["projects"]]
        assert "项目1" in project_names
        assert "项目2" in project_names

    def test_get_project_by_id(self, client, auth_headers):
        """测试：根据ID获取项目"""
        # 创建项目
        create_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "测试项目", "description": "描述"}
        )
        project_id = create_response.json()["id"]

        # 获取项目
        response = client.get(f"/api/projects/{project_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "测试项目"

    def test_get_project_not_found(self, client, auth_headers):
        """测试：获取不存在的项目"""
        response = client.get(
            "/api/projects/99999",  # 使用一个不太可能存在的ID
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_project(self, client, auth_headers):
        """测试：更新项目"""
        # 创建项目
        create_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "原始名称", "description": "原始描述"}
        )
        project_id = create_response.json()["id"]

        # 更新项目
        response = client.put(
            f"/api/projects/{project_id}",
            headers=auth_headers,
            json={"name": "更新名称", "description": "更新描述"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "更新名称"
        assert data["description"] == "更新描述"

    def test_delete_project(self, client, auth_headers):
        """测试：删除项目"""
        # 创建项目
        create_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "待删除项目", "description": "描述"}
        )
        project_id = create_response.json()["id"]

        # 删除项目
        response = client.delete(
            f"/api/projects/{project_id}",
            headers=auth_headers
        )

        assert response.status_code == 200

        # 验证项目已删除
        get_response = client.get(
            f"/api/projects/{project_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_project_not_found(self, client, auth_headers):
        """测试：删除不存在的项目"""
        response = client.delete(
            "/api/projects/99999",
            headers=auth_headers
        )

        assert response.status_code == 404
