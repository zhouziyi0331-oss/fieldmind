"""
测试工具类
提供常用的测试辅助函数
"""

import random
import string
from typing import List, Dict, Any
from datetime import datetime, timedelta


class TestDataFactory:
    """测试数据工厂"""

    @staticmethod
    def random_string(length: int = 10) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def random_email() -> str:
        """生成随机邮箱"""
        username = TestDataFactory.random_string(8)
        domain = TestDataFactory.random_string(6)
        return f"{username}@{domain}.com"

    @staticmethod
    def random_document_id() -> str:
        """生成随机文档ID"""
        return f"doc_{TestDataFactory.random_string(16)}"

    @staticmethod
    def random_chunk_id() -> str:
        """生成随机分块ID"""
        return f"chunk_{TestDataFactory.random_string(16)}"

    @staticmethod
    def create_document(
        project_id: int = 1,
        doc_type: str = "document",
        **kwargs
    ) -> Dict[str, Any]:
        """创建测试文档数据"""
        doc_id = kwargs.get("id", TestDataFactory.random_document_id())

        return {
            "id": doc_id,
            "project_id": project_id,
            "name": kwargs.get("name", f"test_{doc_type}.pdf"),
            "type": doc_type,
            "size": kwargs.get("size", random.randint(1000, 1000000)),
            "mime_type": kwargs.get("mime_type", "application/pdf"),
            "storage_path": kwargs.get("storage_path", f"documents/{doc_id}"),
            "hash": kwargs.get("hash", TestDataFactory.random_string(32)),
            "status": kwargs.get("status", "uploaded"),
            "created_at": kwargs.get("created_at", datetime.utcnow()),
            "updated_at": kwargs.get("updated_at", datetime.utcnow())
        }

    @staticmethod
    def create_chunk(
        document_id: str,
        sequence: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """创建测试分块数据"""
        return {
            "id": kwargs.get("id", TestDataFactory.random_chunk_id()),
            "document_id": document_id,
            "content": kwargs.get("content", f"This is test chunk {sequence}"),
            "sequence": sequence,
            "token_count": kwargs.get("token_count", random.randint(10, 100)),
            "metadata": kwargs.get("metadata", {}),
            "created_at": kwargs.get("created_at", datetime.utcnow())
        }

    @staticmethod
    def create_vector(
        document_id: str,
        chunk_id: str,
        dimension: int = 1536,
        **kwargs
    ) -> Dict[str, Any]:
        """创建测试向量数据"""
        import numpy as np

        # 生成随机向量
        vector = np.random.rand(dimension).astype(np.float32)
        vector = vector / np.linalg.norm(vector)  # 归一化

        return {
            "document_id": document_id,
            "chunk_id": chunk_id,
            "embedding": kwargs.get("embedding", vector.tolist()),
            "model_name": kwargs.get("model_name", "text-embedding-ada-002")
        }


class AssertHelper:
    """断言辅助类"""

    @staticmethod
    def assert_response_success(response: Dict[str, Any]):
        """断言响应成功"""
        assert response["success"] is True, f"Response not successful: {response}"
        assert response["data"] is not None, "Response data is None"
        assert response["error"] is None, f"Response has error: {response['error']}"

    @staticmethod
    def assert_response_error(
        response: Dict[str, Any],
        expected_code: str = None
    ):
        """断言响应错误"""
        assert response["success"] is False, "Response is successful but error expected"
        assert response["data"] is None, f"Response has data: {response['data']}"
        assert response["error"] is not None, "Response has no error"

        if expected_code:
            assert response["error"]["code"] == expected_code, \
                f"Expected error code {expected_code}, got {response['error']['code']}"

    @staticmethod
    def assert_paginated_response(
        response: Dict[str, Any],
        expected_page: int = None,
        expected_total: int = None
    ):
        """断言分页响应"""
        AssertHelper.assert_response_success(response)

        assert "pagination" in response, "No pagination in response"
        pagination = response["pagination"]

        assert "page" in pagination
        assert "page_size" in pagination
        assert "total" in pagination
        assert "total_pages" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination

        if expected_page:
            assert pagination["page"] == expected_page

        if expected_total is not None:
            assert pagination["total"] == expected_total

    @staticmethod
    def assert_has_fields(obj: Dict[str, Any], *fields: str):
        """断言对象包含指定字段"""
        for field in fields:
            assert field in obj, f"Field '{field}' not found in object"

    @staticmethod
    def assert_time_close(
        time1: datetime,
        time2: datetime,
        delta_seconds: int = 5
    ):
        """断言两个时间接近"""
        diff = abs((time1 - time2).total_seconds())
        assert diff < delta_seconds, \
            f"Time difference {diff}s exceeds threshold {delta_seconds}s"

    @staticmethod
    def assert_performance(
        duration: float,
        max_duration: float,
        operation: str = "Operation"
    ):
        """断言性能"""
        assert duration <= max_duration, \
            f"{operation} took {duration:.3f}s, exceeds max {max_duration}s"


class MockHelper:
    """Mock 辅助类"""

    @staticmethod
    def mock_openai_completion(content: str = "Mocked response"):
        """Mock OpenAI completion 响应"""
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }

    @staticmethod
    def mock_openai_embedding(dimension: int = 1536):
        """Mock OpenAI embedding 响应"""
        import numpy as np

        embedding = np.random.rand(dimension).tolist()

        return {
            "data": [
                {
                    "embedding": embedding,
                    "index": 0
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "total_tokens": 10
            }
        }

    @staticmethod
    def mock_file_upload(
        filename: str = "test.pdf",
        content: bytes = b"test content",
        content_type: str = "application/pdf"
    ):
        """Mock 文件上传"""
        from io import BytesIO

        return {
            "file": (BytesIO(content), filename),
            "content_type": content_type
        }


class DBHelper:
    """数据库辅助类"""

    @staticmethod
    def create_test_document(session, **kwargs):
        """创建测试文档"""
        from app.models.document import Document

        doc_data = TestDataFactory.create_document(**kwargs)
        doc = Document(**doc_data)

        session.add(doc)
        session.commit()
        session.refresh(doc)

        return doc

    @staticmethod
    def create_test_chunks(session, document_id: str, count: int = 5):
        """创建测试分块"""
        from app.models.document_chunk import DocumentChunk

        chunks = []
        for i in range(count):
            chunk_data = TestDataFactory.create_chunk(document_id, sequence=i)
            chunk = DocumentChunk(**chunk_data)
            session.add(chunk)
            chunks.append(chunk)

        session.commit()

        for chunk in chunks:
            session.refresh(chunk)

        return chunks

    @staticmethod
    def cleanup_test_data(session, model_class):
        """清理测试数据"""
        session.query(model_class).filter(
            model_class.id.like("test_%")
        ).delete(synchronize_session=False)
        session.commit()


class PerformanceHelper:
    """性能测试辅助类"""

    @staticmethod
    def measure_time(func, *args, **kwargs):
        """测量函数执行时间"""
        import time

        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        return result, duration

    @staticmethod
    def run_benchmark(
        func,
        iterations: int = 100,
        warmup: int = 10,
        *args,
        **kwargs
    ):
        """运行性能基准测试"""
        import time
        import statistics

        # 预热
        for _ in range(warmup):
            func(*args, **kwargs)

        # 测试
        durations = []
        for _ in range(iterations):
            start = time.time()
            func(*args, **kwargs)
            duration = time.time() - start
            durations.append(duration)

        return {
            "iterations": iterations,
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "stdev": statistics.stdev(durations) if len(durations) > 1 else 0,
            "min": min(durations),
            "max": max(durations),
            "p95": statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
            "p99": statistics.quantiles(durations, n=100)[98] if len(durations) > 100 else max(durations)
        }


class FileHelper:
    """文件测试辅助类"""

    @staticmethod
    def create_test_pdf(file_path: str, content: str = "Test PDF"):
        """创建测试 PDF 文件"""
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(file_path)
        c.drawString(100, 750, content)
        c.save()

    @staticmethod
    def create_test_image(file_path: str, size=(100, 100), color='red'):
        """创建测试图片文件"""
        from PIL import Image

        img = Image.new('RGB', size, color=color)
        img.save(file_path)

    @staticmethod
    def create_test_text(file_path: str, lines: int = 100):
        """创建测试文本文件"""
        with open(file_path, 'w') as f:
            for i in range(lines):
                f.write(f"Line {i+1}: This is a test line.\n")

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """获取文件哈希"""
        import hashlib

        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()
