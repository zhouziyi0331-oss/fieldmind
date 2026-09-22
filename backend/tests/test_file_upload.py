"""
文件上传服务测试
"""

import pytest
from io import BytesIO

from tests.utils import TestDataFactory, AssertHelper, FileHelper


class TestFileUploadService:
    """文件上传服务测试"""

    @pytest.mark.unit
    def test_validate_file_success(self, storage_client, db_session):
        """测试文件验证 - 成功"""
        from app.services.file_upload import FileUploadService

        service = FileUploadService(storage=storage_client, db_session=db_session)

        # 创建测试文件
        file = BytesIO(b"Test PDF content")
        filename = "test.pdf"
        mime_type = "application/pdf"

        # 应该不抛出异常
        service._validate_file(file, filename, mime_type)

    @pytest.mark.unit
    def test_validate_file_unsupported_type(self, storage_client, db_session):
        """测试文件验证 - 不支持的类型"""
        from app.services.file_upload import FileUploadService
        from app.core.exceptions import ValidationException

        service = FileUploadService(storage=storage_client, db_session=db_session)

        file = BytesIO(b"Test content")
        filename = "test.xyz"
        mime_type = "application/xyz"

        with pytest.raises(ValidationException) as exc_info:
            service._validate_file(file, filename, mime_type)

        assert exc_info.value.error_code.value == "VALIDATION_ERROR"

    @pytest.mark.unit
    def test_validate_file_empty(self, storage_client, db_session):
        """测试文件验证 - 空文件"""
        from app.services.file_upload import FileUploadService
        from app.core.exceptions import ValidationException

        service = FileUploadService(storage=storage_client, db_session=db_session)

        file = BytesIO(b"")
        filename = "test.pdf"
        mime_type = "application/pdf"

        with pytest.raises(ValidationException) as exc_info:
            service._validate_file(file, filename, mime_type)

        assert "empty" in exc_info.value.message.lower()

    @pytest.mark.unit
    def test_classify_file(self, storage_client, db_session):
        """测试文件分类"""
        from app.services.file_upload import FileUploadService
        from app.models.document import DocumentType

        service = FileUploadService(storage=storage_client, db_session=db_session)

        # 测试PDF
        doc_type = service._classify_file("application/pdf", "test.pdf")
        assert doc_type == DocumentType.DOCUMENT

        # 测试图片
        doc_type = service._classify_file("image/jpeg", "test.jpg")
        assert doc_type == DocumentType.IMAGE

        # 测试音频
        doc_type = service._classify_file("audio/mpeg", "test.mp3")
        assert doc_type == DocumentType.AUDIO

    @pytest.mark.unit
    def test_calculate_hash(self, storage_client, db_session):
        """测试哈希计算"""
        from app.services.file_upload import FileUploadService

        service = FileUploadService(storage=storage_client, db_session=db_session)

        # 创建测试文件
        content = b"Test content for hashing"
        file = BytesIO(content)

        # 计算哈希
        file_hash, file_size = service._calculate_hash_and_size(file)

        assert len(file_hash) == 64  # SHA256
        assert file_size == len(content)

    @pytest.mark.unit
    def test_generate_storage_path(self, storage_client, db_session):
        """测试存储路径生成"""
        from app.services.file_upload import FileUploadService
        from app.models.document import DocumentType

        service = FileUploadService(storage=storage_client, db_session=db_session)

        path = service._generate_storage_path(
            project_id=1,
            doc_type=DocumentType.DOCUMENT,
            filename="test.pdf",
            file_hash="abcd1234" * 8
        )

        # 检查路径格式
        assert path.startswith("projects/1/document/")
        assert "test.pdf" in path
        assert "abcd1234" in path

    @pytest.mark.integration
    @pytest.mark.storage
    @pytest.mark.database
    def test_upload_file_complete(self, storage_client, db_session, temp_file):
        """测试完整上传流程"""
        from app.services.file_upload import FileUploadService

        service = FileUploadService(storage=storage_client, db_session=db_session)

        # 准备测试文件
        with open(temp_file, 'rb') as f:
            document = service.upload_file(
                file=f,
                filename="test.txt",
                project_id=1,
                mime_type="text/plain",
                user_id="user_123"
            )

        # 验证文档记录
        assert document.id is not None
        assert document.name == "test.txt"
        assert document.project_id == 1
        assert document.uploaded_by == "user_123"

        # 验证文件已上传到存储
        bucket, object_name = document.storage_path.split("/", 1)
        exists = storage_client.file_exists(bucket, object_name)
        assert exists is True

    @pytest.mark.integration
    @pytest.mark.database
    def test_check_duplicate(self, storage_client, db_session, temp_file):
        """测试重复文件检测"""
        from app.services.file_upload import FileUploadService

        service = FileUploadService(storage=storage_client, db_session=db_session)

        # 第一次上传
        with open(temp_file, 'rb') as f:
            doc1 = service.upload_file(
                file=f,
                filename="test.txt",
                project_id=1,
                mime_type="text/plain"
            )

        # 第二次上传相同文件
        with open(temp_file, 'rb') as f:
            doc2 = service.upload_file(
                file=f,
                filename="test.txt",
                project_id=1,
                mime_type="text/plain"
            )

        # 应该返回相同的文档
        assert doc1.id == doc2.id


class TestFileClassifier:
    """文件分类器测试"""

    @pytest.mark.unit
    def test_classify_by_extension(self):
        """测试扩展名分类"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        result = FileClassifier.classify(filename="test.pdf")

        assert result["type"] == DocumentType.DOCUMENT
        assert result["confidence"] > 0
        assert "extension" in result["method"]

    @pytest.mark.unit
    def test_classify_by_mime_type(self):
        """测试MIME类型分类"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        result = FileClassifier.classify(
            filename="test.unknown",
            mime_type="application/pdf"
        )

        assert result["type"] == DocumentType.DOCUMENT
        assert result["confidence"] > 0.8

    @pytest.mark.unit
    def test_classify_image(self):
        """测试图片分类"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        result = FileClassifier.classify(
            filename="photo.jpg",
            mime_type="image/jpeg"
        )

        assert result["type"] == DocumentType.IMAGE
        assert result["confidence"] > 0.8

    @pytest.mark.unit
    def test_classify_audio(self):
        """测试音频分类"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        result = FileClassifier.classify(
            filename="song.mp3",
            mime_type="audio/mpeg"
        )

        assert result["type"] == DocumentType.AUDIO
        assert result["confidence"] > 0.8

    @pytest.mark.unit
    def test_classify_video(self):
        """测试视频分类"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        result = FileClassifier.classify(
            filename="video.mp4",
            mime_type="video/mp4"
        )

        assert result["type"] == DocumentType.VIDEO
        assert result["confidence"] > 0.8

    @pytest.mark.unit
    def test_classify_table(self):
        """测试表格分类"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        result = FileClassifier.classify(
            filename="data.xlsx",
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        assert result["type"] == DocumentType.TABLE
        assert result["confidence"] > 0.8

    @pytest.mark.unit
    def test_classify_unsupported(self):
        """测试不支持的文件"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        result = FileClassifier.classify(
            filename="test.xyz",
            mime_type="application/xyz"
        )

        assert result["type"] == DocumentType.OTHER
        assert result["confidence"] == 0.0

    @pytest.mark.unit
    def test_is_supported(self):
        """测试文件支持检查"""
        from app.services.file_classifier import FileClassifier

        # 支持的文件
        assert FileClassifier.is_supported("test.pdf", "application/pdf") is True
        assert FileClassifier.is_supported("test.jpg", "image/jpeg") is True

        # 不支持的文件
        assert FileClassifier.is_supported("test.xyz", "application/xyz") is False

    @pytest.mark.unit
    def test_aggregate_results_consistent(self):
        """测试结果聚合 - 一致结果"""
        from app.services.file_classifier import FileClassifier
        from app.models.document import DocumentType

        # 模拟多个一致的结果
        results = [
            {"type": DocumentType.DOCUMENT, "confidence": 0.7, "method": "extension", "details": {}},
            {"type": DocumentType.DOCUMENT, "confidence": 0.9, "method": "mime_type", "details": {}},
        ]

        final = FileClassifier._aggregate_results(results, "test.pdf")

        assert final["type"] == DocumentType.DOCUMENT
        # 一致结果应该提高置信度
        assert final["confidence"] > 0.9


@pytest.mark.integration
class TestDocumentAPI:
    """文档API测试"""

    def test_upload_document_api(self, client, db_session, temp_file):
        """测试上传文档API"""
        with open(temp_file, 'rb') as f:
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.txt", f, "text/plain")},
                data={"project_id": 1}
            )

        assert response.status_code == 200

        data = response.json()
        AssertHelper.assert_response_success(data)

        # 验证响应数据
        doc_data = data["data"]
        assert "id" in doc_data
        assert doc_data["name"] == "test.txt"
        assert doc_data["type"] == "document"

    def test_get_document_api(self, client, db_session):
        """测试获取文档API"""
        from tests.utils import DBHelper

        # 创建测试文档
        doc = DBHelper.create_test_document(db_session, name="test.pdf")

        # 调用API
        response = client.get(f"/api/v1/documents/{doc.id}")

        assert response.status_code == 200

        data = response.json()
        AssertHelper.assert_response_success(data)

        doc_data = data["data"]
        assert doc_data["id"] == doc.id
        assert doc_data["name"] == "test.pdf"

    def test_list_documents_api(self, client, db_session):
        """测试文档列表API"""
        from tests.utils import DBHelper

        # 创建多个测试文档
        for i in range(5):
            DBHelper.create_test_document(db_session, project_id=1)

        # 调用API
        response = client.get(
            "/api/v1/documents",
            params={"project_id": 1, "page": 1, "page_size": 10}
        )

        assert response.status_code == 200

        data = response.json()
        AssertHelper.assert_paginated_response(data)

        assert len(data["data"]) == 5

    def test_classify_file_api(self, client):
        """测试文件分类API"""
        response = client.post(
            "/api/v1/documents/classify",
            data={
                "filename": "test.pdf",
                "mime_type": "application/pdf"
            }
        )

        assert response.status_code == 200

        data = response.json()
        AssertHelper.assert_response_success(data)

        result = data["data"]
        assert result["type"] == "document"
        assert result["confidence"] > 0.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
