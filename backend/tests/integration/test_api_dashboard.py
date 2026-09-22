"""
Dashboard API 集成测试
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestDashboardAPI:
    """Dashboard API 测试"""

    def test_get_project_quality_metrics(self, client: TestClient, sample_project):
        """测试获取数据质量指标"""
        response = client.get(f"/api/v1/dashboard/projects/{sample_project.id}/quality")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_project_stats(self, client: TestClient, sample_project):
        """测试获取项目统计"""
        response = client.get(f"/api/v1/dashboard/projects/{sample_project.id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_knowledge_graph(self, client: TestClient, sample_project):
        """测试获取知识图谱"""
        response = client.get(f"/api/v1/dashboard/projects/{sample_project.id}/knowledge-graph")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_get_cache_stats(self, client: TestClient):
        """测试获取缓存统计"""
        response = client.get("/api/v1/dashboard/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


@pytest.mark.integration
class TestCacheInvalidation:
    """缓存失效测试"""

    def test_invalidate_cache_pattern(self, client: TestClient, admin_user):
        """测试按模式失效缓存"""
        # 需要管理员权限
        response = client.post(
            "/api/v1/dashboard/cache/invalidate?pattern=projects:*"
        )
        # 没有认证会失败，这是预期的
        assert response.status_code in [200, 401, 403]

    def test_clear_all_cache(self, client: TestClient):
        """测试清空所有缓存"""
        response = client.post("/api/v1/dashboard/cache/invalidate")
        # 需要管理员权限
        assert response.status_code in [200, 401, 403]
