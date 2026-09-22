"""
Celery 任务测试
"""

import pytest
import time
from unittest.mock import Mock, patch


class TestCeleryConfiguration:
    """Celery 配置测试"""

    @pytest.mark.unit
    def test_celery_app_exists(self):
        """测试 Celery 应用创建"""
        from app.core.celery_app import celery_app

        assert celery_app is not None
        assert celery_app.main == "fieldmind"

    @pytest.mark.unit
    def test_celery_queues_configured(self):
        """测试队列配置"""
        from app.core.celery_app import celery_app

        queues = celery_app.conf.task_queues

        assert len(queues) >= 4
        queue_names = [q.name for q in queues]

        assert "default" in queue_names
        assert "documents" in queue_names
        assert "processing" in queue_names
        assert "low_priority" in queue_names

    @pytest.mark.unit
    def test_celery_task_routes(self):
        """测试任务路由"""
        from app.core.celery_app import celery_app

        routes = celery_app.conf.task_routes

        assert "app.tasks.document_tasks.*" in routes
        assert routes["app.tasks.document_tasks.*"]["queue"] == "documents"


class TestDocumentTasks:
    """文档任务测试"""

    @pytest.mark.unit
    @patch('app.tasks.document_tasks.get_db_session')
    def test_process_document_task_dispatch(self, mock_db):
        """测试文档处理任务调度"""
        from app.tasks.document_tasks import process_document_task
        from app.models.document import Document, DocumentType, DocumentStatus
        from tests.utils import TestDataFactory

        # Mock 数据库
        mock_session = Mock()
        mock_db.return_value = mock_session

        # Mock 文档
        doc_data = TestDataFactory.create_document(type=DocumentType.DOCUMENT)
        mock_doc = Mock(spec=Document)
        mock_doc.id = doc_data["id"]
        mock_doc.type = DocumentType.DOCUMENT
        mock_doc.status = DocumentStatus.UPLOADED

        mock_session.query.return_value.filter.return_value.first.return_value = mock_doc

        # 模拟任务执行（不实际调用 apply_async）
        with patch('app.tasks.document_tasks.process_document_content.apply_async') as mock_task:
            mock_task.return_value.id = "task_123"

            result = process_document_task(doc_data["id"])

            assert result["document_id"] == doc_data["id"]
            assert result["status"] == "dispatched"
            assert result["task_id"] == "task_123"

    @pytest.mark.unit
    def test_task_retry_on_failure(self):
        """测试任务失败重试"""
        from app.tasks.document_tasks import process_document_task

        # 测试任务配置
        assert process_document_task.max_retries == 3
        assert process_document_task.default_retry_delay == 60


class TestTaskManager:
    """任务管理器测试"""

    @pytest.mark.unit
    def test_get_task_status(self):
        """测试获取任务状态"""
        from app.core.task_manager import TaskManager

        # 创建一个假任务ID
        task_id = "test_task_123"

        status = TaskManager.get_task_status(task_id)

        assert "task_id" in status
        assert "state" in status
        assert status["task_id"] == task_id

    @pytest.mark.unit
    @patch('app.core.task_manager.celery_app.control.inspect')
    def test_get_active_tasks(self, mock_inspect):
        """测试获取活跃任务"""
        from app.core.task_manager import TaskManager

        # Mock inspect
        mock_inspect_instance = Mock()
        mock_inspect.return_value = mock_inspect_instance

        mock_inspect_instance.active.return_value = {
            "worker1": [
                {
                    "id": "task1",
                    "name": "app.tasks.document_tasks.process_document_task",
                    "args": ["doc_001"],
                    "time_start": 1234567890
                }
            ]
        }

        tasks = TaskManager.get_active_tasks()

        assert len(tasks) == 1
        assert tasks[0]["task_id"] == "task1"
        assert tasks[0]["worker"] == "worker1"

    @pytest.mark.unit
    def test_submit_document_processing(self):
        """测试提交文档处理"""
        from app.core.task_manager import submit_document_processing

        with patch('app.tasks.document_tasks.process_document_task.apply_async') as mock_task:
            mock_task.return_value.id = "task_abc123"

            task_id = submit_document_processing("doc_001")

            assert task_id == "task_abc123"
            mock_task.assert_called_once()


class TestTaskAPI:
    """任务 API 测试"""

    @pytest.mark.integration
    def test_trigger_document_processing_api(self, client):
        """测试触发文档处理 API"""
        with patch('app.core.task_manager.submit_document_processing') as mock_submit:
            mock_submit.return_value = "task_123"

            response = client.post("/api/v1/tasks/documents/doc_001/process")

            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["task_id"] == "task_123"

    @pytest.mark.integration
    def test_get_task_status_api(self, client):
        """测试获取任务状态 API"""
        with patch('app.core.task_manager.TaskManager.get_task_status') as mock_status:
            mock_status.return_value = {
                "task_id": "task_123",
                "state": "SUCCESS",
                "result": {"status": "completed"}
            }

            response = client.get("/api/v1/tasks/task_123/status")

            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["task_id"] == "task_123"
            assert data["data"]["state"] == "SUCCESS"

    @pytest.mark.integration
    def test_cancel_task_api(self, client):
        """测试取消任务 API"""
        with patch('app.core.task_manager.TaskManager.cancel_task') as mock_cancel:
            mock_cancel.return_value = True

            response = client.post("/api/v1/tasks/task_123/cancel")

            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "cancelled"

    @pytest.mark.integration
    def test_get_active_tasks_api(self, client):
        """测试获取活跃任务 API"""
        with patch('app.core.task_manager.TaskManager.get_active_tasks') as mock_active:
            mock_active.return_value = [
                {"task_id": "task1", "name": "process_document"},
                {"task_id": "task2", "name": "process_image"}
            ]

            response = client.get("/api/v1/tasks/active")

            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["data"]["count"] == 2

    @pytest.mark.integration
    def test_get_worker_stats_api(self, client):
        """测试获取 Worker 统计 API"""
        with patch('app.core.task_manager.TaskManager.get_worker_stats') as mock_stats:
            mock_stats.return_value = {
                "worker1": {
                    "stats": {"total": 100},
                    "active_tasks": 2
                }
            }

            response = client.get("/api/v1/tasks/workers")

            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert "worker1" in data["data"]


@pytest.mark.slow
class TestTaskExecution:
    """任务执行测试（慢速测试）"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not pytest.config.getoption("--run-slow"),
        reason="需要 --run-slow 选项"
    )
    def test_document_processing_end_to_end(self, db_session, storage_client):
        """测试文档处理端到端流程"""
        from app.tasks.document_tasks import process_document_task
        from tests.utils import DBHelper

        # 创建测试文档
        doc = DBHelper.create_test_document(
            db_session,
            type="document",
            status="uploaded"
        )

        # 同步执行任务（测试环境）
        result = process_document_task(doc.id)

        assert result["document_id"] == doc.id
        assert result["status"] in ["dispatched", "processed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
