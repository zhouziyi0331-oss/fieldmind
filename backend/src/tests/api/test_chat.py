"""智能对话API测试"""
import pytest
from unittest.mock import patch, MagicMock


class TestChatAPI:
    """智能对话API测试类"""

    def test_create_chat_session_success(self, client, auth_headers):
        """测试成功创建对话会话"""
        # 先创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={
                "name": "Test Project for Chat",
                "description": "Project for testing chat"
            }
        )
        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        # 创建对话会话
        response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "name": "Test Chat Session",
                "document_ids": [],
                "config": {"use_deep_thinking": True}
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Chat Session"
        assert data["project_id"] == project_id
        assert data["message_count"] == 0
        assert "id" in data
        assert "created_at" in data

    def test_create_chat_session_project_not_found(self, client, auth_headers):
        """测试创建会话时项目不存在"""
        response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": 99999,
                "name": "Test Session",
                "document_ids": []
            }
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_chat_session(self, client, auth_headers):
        """测试获取对话会话详情"""
        # 创建项目和会话
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        session_response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "name": "Test Session",
                "document_ids": []
            }
        )
        session_id = session_response.json()["id"]

        # 获取会话详情
        response = client.get(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["name"] == "Test Session"
        assert data["project_id"] == project_id

    def test_get_chat_session_not_found(self, client, auth_headers):
        """测试获取不存在的会话"""
        response = client.get(
            "/api/chat/sessions/99999",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_project_sessions(self, client, auth_headers):
        """测试获取项目的对话会话列表"""
        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        # 创建多个会话
        for i in range(3):
            client.post(
                "/api/chat/sessions",
                headers=auth_headers,
                json={
                    "project_id": project_id,
                    "name": f"Session {i+1}",
                    "document_ids": []
                }
            )

        # 获取会话列表
        response = client.get(
            f"/api/chat/projects/{project_id}/sessions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "sessions" in data
        assert data["total"] == 3
        assert len(data["sessions"]) == 3

    def test_send_message_success(self, client, auth_headers):
        """测试发送消息并获取AI响应"""
        # 创建项目和会话
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        session_response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "name": "Test Session",
                "document_ids": []
            }
        )
        session_id = session_response.json()["id"]

        # Mock AI服务
        with patch('app.api.chat.mem0_service') as mock_mem0, \
             patch('app.api.chat.intelligent_agent') as mock_agent:

            mock_mem0.search_memories.return_value = []
            mock_agent.generate_response.return_value = {
                "message": "This is a test AI response",
                "thinking_process": "Test thinking process",
                "sources": [],
                "model": "test-model",
                "tokens_used": 100
            }

            # 发送消息
            response = client.post(
                f"/api/chat/sessions/{session_id}/messages",
                headers=auth_headers,
                json={"content": "Hello, AI!"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["role"] == "assistant"
            assert data["content"] == "This is a test AI response"
            assert data["thinking_process"] == "Test thinking process"
            assert data["session_id"] == session_id
            assert "id" in data
            assert "created_at" in data

    def test_send_message_session_not_found(self, client, auth_headers):
        """测试向不存在的会话发送消息"""
        response = client.post(
            "/api/chat/sessions/99999/messages",
            headers=auth_headers,
            json={"content": "Hello"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_session_messages(self, client, auth_headers):
        """测试获取会话的所有消息"""
        # 创建项目和会话
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        session_response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "name": "Test Session",
                "document_ids": []
            }
        )
        session_id = session_response.json()["id"]

        # 发送几条消息
        with patch('app.api.chat.mem0_service') as mock_mem0, \
             patch('app.api.chat.intelligent_agent') as mock_agent:

            mock_mem0.search_memories.return_value = []
            mock_agent.generate_response.return_value = {
                "message": "AI response",
                "sources": []
            }

            for i in range(3):
                client.post(
                    f"/api/chat/sessions/{session_id}/messages",
                    headers=auth_headers,
                    json={"content": f"Message {i+1}"}
                )

        # 获取消息列表
        response = client.get(
            f"/api/chat/sessions/{session_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "messages" in data
        # 3条用户消息 + 3条AI响应 = 6条消息
        assert data["total"] == 6
        assert len(data["messages"]) == 6

    def test_get_messages_session_not_found(self, client, auth_headers):
        """测试获取不存在会话的消息"""
        response = client.get(
            "/api/chat/sessions/99999/messages",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_session(self, client, auth_headers):
        """测试删除对话会话"""
        # 创建项目和会话
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        session_response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "name": "Test Session",
                "document_ids": []
            }
        )
        session_id = session_response.json()["id"]

        # 删除会话
        response = client.delete(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()

        # 验证会话已删除
        get_response = client.get(
            f"/api/chat/sessions/{session_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_session_not_found(self, client, auth_headers):
        """测试删除不存在的会话"""
        response = client.delete(
            "/api/chat/sessions/99999",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_session_pagination(self, client, auth_headers):
        """测试会话列表分页"""
        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        # 创建5个会话
        for i in range(5):
            client.post(
                "/api/chat/sessions",
                headers=auth_headers,
                json={
                    "project_id": project_id,
                    "name": f"Session {i+1}",
                    "document_ids": []
                }
            )

        # 测试分页
        response = client.get(
            f"/api/chat/projects/{project_id}/sessions?skip=0&limit=3",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["sessions"]) == 3

    def test_message_pagination(self, client, auth_headers):
        """测试消息列表分页"""
        # 创建项目和会话
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        session_response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "name": "Test Session",
                "document_ids": []
            }
        )
        session_id = session_response.json()["id"]

        # 发送多条消息
        with patch('app.api.chat.mem0_service') as mock_mem0, \
             patch('app.api.chat.intelligent_agent') as mock_agent:

            mock_mem0.search_memories.return_value = []
            mock_agent.generate_response.return_value = {
                "message": "AI response",
                "sources": []
            }

            for i in range(5):
                client.post(
                    f"/api/chat/sessions/{session_id}/messages",
                    headers=auth_headers,
                    json={"content": f"Message {i+1}"}
                )

        # 测试分页
        response = client.get(
            f"/api/chat/sessions/{session_id}/messages?skip=0&limit=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10  # 5条用户消息 + 5条AI响应
        assert len(data["messages"]) == 5

    def test_session_with_config(self, client, auth_headers):
        """测试创建带配置的会话"""
        # 创建项目
        project_response = client.post(
            "/api/projects/",
            headers=auth_headers,
            json={"name": "Test Project", "description": "Test"}
        )
        project_id = project_response.json()["id"]

        # 创建带配置的会话
        response = client.post(
            "/api/chat/sessions",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "name": "Configured Session",
                "document_ids": [],
                "config": {
                    "use_deep_thinking": False,
                    "enable_web_search": True,
                    "temperature": 0.7
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["config"]["use_deep_thinking"] is False
        assert data["config"]["enable_web_search"] is True
        assert data["config"]["temperature"] == 0.7
