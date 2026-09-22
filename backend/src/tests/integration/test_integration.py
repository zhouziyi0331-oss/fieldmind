"""
集成测试 - Week 3 Day 5-7
测试完整工作流、多模块协作、数据流
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
from sqlalchemy.orm import Session


class TestDocumentProcessingIntegration:
    """文档处理集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_document_pipeline(self, db_session: Session):
        """测试完整文档处理管道"""
        from app.services.optimized_document_pipeline import OptimizedDocumentPipeline
        from app.models.project import ProjectDocument

        # 创建测试文档
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        ) as f:
            test_content = "这是一个测试文档。" * 50
            f.write(test_content)
            temp_path = f.name

        try:
            # 创建数据库记录
            doc = ProjectDocument(
                project_id=1,
                filename="test_integration.txt",
                original_filename="test_integration.txt",
                file_path=temp_path,
                file_type="text/plain",
                status="pending"
            )
            db_session.add(doc)
            db_session.commit()

            # 执行完整管道
            pipeline = OptimizedDocumentPipeline()

            result = await pipeline.process_documents_batch(
                document_ids=[doc.id],
                project_id=1,
                db_session=db_session
            )

            # 验证结果
            assert result["success"] is True
            assert result["documents_processed"] == 1
            assert result["total_chunks"] > 0

            # 验证数据库状态
            db_session.refresh(doc)
            assert doc.status == "completed"

            pipeline.shutdown()

        finally:
            # 清理
            Path(temp_path).unlink(missing_ok=True)
            db_session.query(ProjectDocument).filter(
                ProjectDocument.id == doc.id
            ).delete()
            db_session.commit()

    @pytest.mark.integration
    def test_database_cache_integration(self, db_session: Session):
        """测试数据库和缓存集成"""
        from app.models.project import Project
        from app.core.cache_manager import get_cache_manager

        cache = get_cache_manager()
        if not cache.enabled:
            pytest.skip("Redis not available")

        # 查询项目
        project = db_session.query(Project).first()
        if not project:
            pytest.skip("No project in database")

        # 缓存项目数据
        cache_key = f"project:{project.id}"
        cache.set(cache_key, {
            "id": project.id,
            "name": project.name
        }, ttl=60)

        # 验证缓存
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert cached_data["id"] == project.id

        # 清理
        cache.delete(cache_key)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_parallel_document_processing(self, db_session: Session):
        """测试并行文档处理"""
        from app.services.optimized_document_pipeline import OptimizedDocumentPipeline
        from app.models.project import ProjectDocument
        import time

        # 创建多个测试文档
        doc_ids = []
        temp_files = []

        for i in range(5):
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(f"测试文档 {i+1}。" * 20)
                temp_files.append(f.name)

            doc = ProjectDocument(
                project_id=1,
                filename=f"test_parallel_{i+1}.txt",
                original_filename=f"test_parallel_{i+1}.txt",
                file_path=temp_files[-1],
                file_type="text/plain",
                status="pending"
            )
            db_session.add(doc)
            db_session.flush()
            doc_ids.append(doc.id)

        db_session.commit()

        try:
            # 测试并行处理
            pipeline = OptimizedDocumentPipeline()

            start = time.time()
            result = await pipeline.process_documents_batch(
                document_ids=doc_ids,
                project_id=1,
                db_session=db_session
            )
            duration = time.time() - start

            # 验证结果
            assert result["success"] is True
            assert result["documents_processed"] == 5
            assert duration < 5  # 应该很快完成

            pipeline.shutdown()

        finally:
            # 清理
            for temp_file in temp_files:
                Path(temp_file).unlink(missing_ok=True)

            for doc_id in doc_ids:
                db_session.query(ProjectDocument).filter(
                    ProjectDocument.id == doc_id
                ).delete()
            db_session.commit()


class TestCacheIntegration:
    """缓存集成测试"""

    @pytest.mark.integration
    def test_cache_with_database_queries(self, db_session: Session):
        """测试缓存与数据库查询集成"""
        from app.models.project import Project
        from app.core.cache_manager import cached
        import time

        cache_manager = pytest.importorskip("app.core.cache_manager").get_cache_manager()
        if not cache_manager.enabled:
            pytest.skip("Redis not available")

        call_count = [0]

        @cached(ttl=60, prefix="test_db_query")
        def get_projects(limit: int):
            call_count[0] += 1
            projects = db_session.query(Project).limit(limit).all()
            return [(p.id, p.name) for p in projects]

        # 第一次调用
        start = time.time()
        result1 = get_projects(5)
        time1 = time.time() - start

        # 第二次调用（从缓存）
        start = time.time()
        result2 = get_projects(5)
        time2 = time.time() - start

        # 验证
        assert result1 == result2
        assert call_count[0] == 1  # 只调用了一次
        assert time2 < time1  # 缓存更快

        # 清理
        cache_manager.delete_pattern("test_db_query:*")


class TestErrorHandlingIntegration:
    """错误处理集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_exception_handling_in_pipeline(self):
        """测试管道中的异常处理"""
        from app.services.optimized_document_pipeline import OptimizedDocumentPipeline
        from app.core.database import SessionLocal

        db = SessionLocal()
        pipeline = OptimizedDocumentPipeline()

        try:
            # 使用不存在的文档ID
            result = await pipeline.process_documents_batch(
                document_ids=[999999],
                project_id=1,
                db_session=db
            )

            # 应该处理错误而不是崩溃
            assert "errors" in result or result.get("documents_processed", 0) == 0

        finally:
            pipeline.shutdown()
            db.close()

    @pytest.mark.integration
    def test_custom_exception_handling(self):
        """测试自定义异常处理"""
        from app.core.exceptions import (
            NotFoundException,
            ValidationException,
            DocumentProcessingException
        )

        # 测试异常创建和转换
        exc1 = NotFoundException("Document", 123)
        assert exc1.error_code.value == "1002"
        assert "123" in exc1.message

        exc2 = ValidationException("Invalid input", {"field": "name"})
        assert exc2.error_code.value == "1001"
        assert exc2.details["field"] == "name"

        exc3 = DocumentProcessingException("Parse error", document_id=456)
        assert exc3.error_code.value == "3000"
        assert exc3.details["document_id"] == 456


# ==================== Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """数据库会话 fixture"""
    from app.core.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def temp_directory():
    """临时目录 fixture"""
    import tempfile
    import shutil

    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "integration"])
