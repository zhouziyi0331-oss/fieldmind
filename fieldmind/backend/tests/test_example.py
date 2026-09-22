"""
响应格式测试示例
演示如何使用测试框架
"""

import pytest
from tests.utils import AssertHelper, TestDataFactory


class TestResponseFormat:
    """响应格式测试"""

    def test_success_response(self):
        """测试成功响应格式"""
        from app.schemas.response import success_response

        data = {"id": "doc_001", "name": "test.pdf"}
        response = success_response(data, request_id="req_123")

        # 使用 AssertHelper
        AssertHelper.assert_response_success(response)
        assert response["data"]["id"] == "doc_001"
        assert response["metadata"]["request_id"] == "req_123"

    def test_error_response(self):
        """测试错误响应格式"""
        from app.schemas.response import error_response

        response = error_response(
            code="NOT_FOUND",
            message="Document not found",
            request_id="req_456"
        )

        # 使用 AssertHelper
        AssertHelper.assert_response_error(response, expected_code="NOT_FOUND")
        assert response["error"]["message"] == "Document not found"

    def test_paginated_response(self):
        """测试分页响应格式"""
        from app.schemas.response import paginated_response

        data = [{"id": f"doc_{i:03d}"} for i in range(20)]
        response = paginated_response(
            data=data,
            page=1,
            page_size=20,
            total=100
        )

        # 使用 AssertHelper
        AssertHelper.assert_paginated_response(
            response,
            expected_page=1,
            expected_total=100
        )


class TestExceptions:
    """异常测试"""

    def test_not_found_exception(self):
        """测试资源不存在异常"""
        from app.core.exceptions import DocumentNotFoundException

        with pytest.raises(DocumentNotFoundException) as exc_info:
            raise DocumentNotFoundException("doc_001")

        exc = exc_info.value
        assert exc.error_code.value == "DOCUMENT_NOT_FOUND"
        assert exc.status_code == 404
        assert "doc_001" in exc.message

    def test_validation_exception(self):
        """测试验证异常"""
        from app.core.exceptions import ValidationException

        with pytest.raises(ValidationException) as exc_info:
            raise ValidationException(
                message="Invalid email",
                field="email"
            )

        exc = exc_info.value
        assert exc.error_code.value == "VALIDATION_ERROR"
        assert exc.status_code == 422
        assert exc.field == "email"


@pytest.mark.database
class TestDatabaseModels:
    """数据库模型测试"""

    def test_create_document(self, db_session):
        """测试创建文档"""
        from tests.utils import DBHelper

        # 使用 DBHelper 创建文档
        doc = DBHelper.create_test_document(
            db_session,
            name="test.pdf",
            type="document"
        )

        assert doc.id is not None
        assert doc.name == "test.pdf"
        assert doc.type == "document"

    def test_create_chunks(self, db_session):
        """测试创建分块"""
        from tests.utils import DBHelper

        # 创建文档
        doc = DBHelper.create_test_document(db_session)

        # 创建分块
        chunks = DBHelper.create_test_chunks(
            db_session,
            document_id=doc.id,
            count=5
        )

        assert len(chunks) == 5
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == doc.id
            assert chunk.sequence == i


@pytest.mark.storage
class TestObjectStorage:
    """对象存储测试"""

    def test_upload_file(self, storage_client, temp_file):
        """测试文件上传"""
        bucket = "test-bucket"
        object_name = "test_file.txt"

        # 上传文件
        success = storage_client.upload_file(
            bucket=bucket,
            object_name=object_name,
            file_path=str(temp_file)
        )

        assert success is True

        # 验证文件存在
        exists = storage_client.file_exists(bucket, object_name)
        assert exists is True

    def test_download_file(self, storage_client, temp_file, temp_dir):
        """测试文件下载"""
        bucket = "test-bucket"
        object_name = "test_file.txt"
        download_path = temp_dir / "downloaded.txt"

        # 先上传
        storage_client.upload_file(bucket, object_name, str(temp_file))

        # 下载
        success = storage_client.download_file(
            bucket=bucket,
            object_name=object_name,
            file_path=str(download_path)
        )

        assert success is True
        assert download_path.exists()
        assert download_path.read_text() == temp_file.read_text()


@pytest.mark.vector
class TestVectorStore:
    """向量存储测试"""

    def test_insert_vector(self, vector_store):
        """测试插入向量"""
        from tests.utils import TestDataFactory

        # 创建测试向量
        vector_data = TestDataFactory.create_vector(
            document_id="doc_test_001",
            chunk_id="chunk_test_001"
        )

        # 插入
        success = vector_store.insert_vector(**vector_data)
        assert success is True

        # 验证存在
        exists = vector_store.vector_exists("chunk_test_001")
        assert exists is True

    def test_search_vectors(self, vector_store):
        """测试向量搜索"""
        from tests.utils import TestDataFactory

        # 插入多个向量
        for i in range(10):
            vector_data = TestDataFactory.create_vector(
                document_id=f"doc_{i}",
                chunk_id=f"chunk_{i}"
            )
            vector_store.insert_vector(**vector_data)

        # 搜索
        query_vector = TestDataFactory.create_vector(
            document_id="query",
            chunk_id="query"
        )["embedding"]

        results = vector_store.search_similar_vectors(
            query_embedding=query_vector,
            top_k=5
        )

        assert len(results) == 5
        for result in results:
            AssertHelper.assert_has_fields(
                result,
                "chunk_id",
                "document_id",
                "similarity"
            )


@pytest.mark.slow
class TestPerformance:
    """性能测试"""

    def test_vector_search_performance(self, vector_store, benchmark_timer):
        """测试向量搜索性能"""
        from tests.utils import TestDataFactory, AssertHelper

        # 插入1000个向量
        for i in range(1000):
            vector_data = TestDataFactory.create_vector(
                document_id=f"doc_{i}",
                chunk_id=f"chunk_{i}"
            )
            vector_store.insert_vector(**vector_data)

        # 测试搜索性能
        query_vector = TestDataFactory.create_vector(
            document_id="query",
            chunk_id="query"
        )["embedding"]

        benchmark_timer.start()
        results = vector_store.search_similar_vectors(
            query_embedding=query_vector,
            top_k=10
        )
        benchmark_timer.stop()

        # 断言性能
        AssertHelper.assert_performance(
            duration=benchmark_timer.elapsed,
            max_duration=0.1,  # 100ms
            operation="Vector search (1000 vectors)"
        )

    def test_batch_insert_performance(self, vector_store, benchmark_timer):
        """测试批量插入性能"""
        from tests.utils import TestDataFactory, AssertHelper

        # 准备数据
        vectors = [
            TestDataFactory.create_vector(
                document_id=f"doc_{i}",
                chunk_id=f"chunk_{i}"
            )
            for i in range(100)
        ]

        # 测试批量插入
        benchmark_timer.start()
        success_count, fail_count = vector_store.batch_insert_vectors(vectors)
        benchmark_timer.stop()

        assert success_count == 100
        assert fail_count == 0

        # 断言性能
        AssertHelper.assert_performance(
            duration=benchmark_timer.elapsed,
            max_duration=2.0,  # 2秒
            operation="Batch insert (100 vectors)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
