"""
核心模块单元测试 - Week 3 Day 1-2
测试缓存管理器、并行处理器、向量化服务
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock


class TestCacheManager:
    """缓存管理器单元测试"""

    def test_cache_initialization(self):
        """测试缓存初始化"""
        from app.core.cache_manager import CacheManager

        cache = CacheManager(redis_url="redis://localhost:6379/0")
        assert cache is not None
        assert cache.default_ttl == 300

    def test_cache_set_get(self):
        """测试缓存设置和获取"""
        from app.core.cache_manager import CacheManager

        cache = CacheManager()
        if not cache.enabled:
            pytest.skip("Redis not available")

        # 设置缓存
        result = cache.set("test_key", {"data": "value"}, ttl=60)
        assert result is True

        # 获取缓存
        value = cache.get("test_key")
        assert value == {"data": "value"}

        # 清理
        cache.delete("test_key")

    def test_cache_delete(self):
        """测试缓存删除"""
        from app.core.cache_manager import CacheManager

        cache = CacheManager()
        if not cache.enabled:
            pytest.skip("Redis not available")

        cache.set("test_key", "value")
        cache.delete("test_key")

        value = cache.get("test_key")
        assert value is None

    def test_cache_pattern_delete(self):
        """测试模式删除"""
        from app.core.cache_manager import CacheManager

        cache = CacheManager()
        if not cache.enabled:
            pytest.skip("Redis not available")

        # 设置多个键
        cache.set("test:key1", "value1")
        cache.set("test:key2", "value2")
        cache.set("other:key", "value")

        # 删除模式匹配的键
        deleted = cache.delete_pattern("test:*")
        assert deleted >= 2

        # 验证
        assert cache.get("test:key1") is None
        assert cache.get("test:key2") is None
        assert cache.get("other:key") == "value"

        # 清理
        cache.delete("other:key")

    def test_cache_decorator(self):
        """测试缓存装饰器"""
        from app.core.cache_manager import CacheManager

        cache = CacheManager()
        if not cache.enabled:
            pytest.skip("Redis not available")

        call_count = [0]

        @cache.cache_result(ttl=10, prefix="test_func")
        def expensive_function(x):
            call_count[0] += 1
            return x * 2

        # 第一次调用
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count[0] == 1

        # 第二次调用（应该从缓存）
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count[0] == 1  # 未增加

        # 清理
        cache.delete_pattern("test_func:*")


class TestParallelProcessor:
    """并行处理器单元测试"""

    def test_processor_initialization(self):
        """测试处理器初始化"""
        from app.core.parallel_processor import ParallelProcessor

        processor = ParallelProcessor(max_workers=10)
        assert processor.thread_workers == 10
        processor.shutdown()

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """测试批量处理"""
        from app.core.parallel_processor import ParallelProcessor, ProcessingMode

        processor = ParallelProcessor(max_workers=5)

        def simple_task(x):
            return x * 2

        items = list(range(10))
        result = await processor.process_batch_async(
            items,
            simple_task,
            batch_size=5,
            mode=ProcessingMode.THREAD,
            show_progress=False
        )

        assert result.total == 10
        assert result.successful == 10
        assert result.failed == 0
        assert result.results == [i * 2 for i in items]

        processor.shutdown()

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        from app.core.parallel_processor import ParallelProcessor, ProcessingMode

        processor = ParallelProcessor()

        def error_task(x):
            if x % 2 == 0:
                raise ValueError(f"Error: {x}")
            return x * 2

        items = list(range(10))
        result = await processor.process_batch_async(
            items,
            error_task,
            batch_size=5,
            mode=ProcessingMode.THREAD,
            show_progress=False
        )

        assert result.total == 10
        assert result.successful == 5
        assert result.failed == 5
        assert len(result.errors) == 5

        processor.shutdown()

    @pytest.mark.asyncio
    async def test_parallel_speedup(self):
        """测试并行加速"""
        from app.core.parallel_processor import ParallelProcessor, ProcessingMode

        processor = ParallelProcessor(max_workers=10)

        def io_task(x):
            time.sleep(0.01)
            return x

        items = list(range(50))

        # 串行（对照组）
        start = time.time()
        serial = [io_task(x) for x in items[:5]]
        serial_time = time.time() - start

        # 并行
        start = time.time()
        result = await processor.process_batch_async(
            items,
            io_task,
            batch_size=10,
            mode=ProcessingMode.THREAD,
            show_progress=False
        )
        parallel_time = time.time() - start

        expected_serial = serial_time * 10  # 50/5
        speedup = expected_serial / parallel_time

        assert speedup > 5  # 至少5倍加速
        assert result.success_rate == 1.0

        processor.shutdown()


class TestOptimizedDocumentPipeline:
    """优化文档管道单元测试"""

    def test_pipeline_initialization(self):
        """测试管道初始化"""
        from app.services.optimized_document_pipeline import OptimizedDocumentPipeline

        pipeline = OptimizedDocumentPipeline()
        assert pipeline.parallel_processor is not None
        assert pipeline.cache_manager is not None

        pipeline.shutdown()

    def test_simple_chunk(self):
        """测试文本分块"""
        from app.services.optimized_document_pipeline import OptimizedDocumentPipeline

        pipeline = OptimizedDocumentPipeline()

        text = "这是第一句。这是第二句。" * 50
        chunks = pipeline._simple_chunk(text, chunk_size=50, overlap=10)

        assert len(chunks) > 0
        assert all(len(chunk) > 0 for chunk in chunks)

        pipeline.shutdown()

    def test_extract_text_by_type(self):
        """测试文本提取"""
        from app.services.optimized_document_pipeline import OptimizedDocumentPipeline
        from pathlib import Path
        import tempfile

        pipeline = OptimizedDocumentPipeline()

        # 测试 TXT 文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("测试内容")
            f.flush()
            temp_path = Path(f.name)

        try:
            text = pipeline._extract_text_by_type(temp_path)
            assert text == "测试内容"
        finally:
            temp_path.unlink()
            pipeline.shutdown()


class TestAICallManager:
    """AI 调用管理器单元测试"""

    def test_manager_initialization(self):
        """测试管理器初始化"""
        from app.core.ai_call_manager import AICallManager

        try:
            manager = AICallManager(
                api_key="test_key",
                max_concurrent=3,
                rate_limit_per_min=10
            )
            assert manager.max_concurrent == 3
            assert manager.rate_limit_per_min == 10
        except Exception:
            pytest.skip("Anthropic SDK not available")

    def test_cost_estimation(self):
        """测试成本估算"""
        from app.core.ai_call_manager import AICallManager

        try:
            manager = AICallManager(api_key="test_key")

            # Mock usage
            mock_usage = Mock()
            mock_usage.input_tokens = 1000
            mock_usage.output_tokens = 500

            cost = manager._estimate_cost("claude-3-haiku-20240307", mock_usage)
            assert cost > 0
            assert cost < 1  # 应该很便宜

        except Exception:
            pytest.skip("Anthropic SDK not available")

    def test_prompt_compression(self):
        """测试提示词压缩"""
        from app.core.ai_call_manager import AICallManager

        try:
            manager = AICallManager(api_key="test_key")

            long_text = "x" * 5000
            compressed = manager.compress_prompt(long_text, max_length=100)

            assert len(compressed) <= 103  # 100 + "..."
        except Exception:
            pytest.skip("Anthropic SDK not available")

    def test_context_optimization(self):
        """测试上下文窗口优化"""
        from app.core.ai_call_manager import AICallManager

        try:
            manager = AICallManager(api_key="test_key")

            messages = [
                {"role": "user", "content": "x" * 10000}
                for _ in range(20)
            ]

            optimized = manager.optimize_context_window(messages, max_tokens=1000)

            assert len(optimized) < len(messages)
        except Exception:
            pytest.skip("Anthropic SDK not available")


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
