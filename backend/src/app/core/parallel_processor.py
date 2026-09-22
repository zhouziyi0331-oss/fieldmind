"""
并行处理管理器
提供异步批量处理能力，支持线程池和进程池
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from typing import List, Callable, Any, Optional, Dict
import multiprocessing
import time
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingMode(Enum):
    """处理模式"""
    THREAD = "thread"  # 线程池（IO 密集型）
    PROCESS = "process"  # 进程池（CPU 密集型）
    ASYNC = "async"  # 异步（协程）


@dataclass
class BatchResult:
    """批处理结果"""
    total: int
    successful: int
    failed: int
    results: List[Any]
    errors: List[Dict[str, Any]]
    duration: float

    @property
    def success_rate(self) -> float:
        """成功率"""
        return self.successful / self.total if self.total > 0 else 0.0


class ParallelProcessor:
    """并行处理管理器"""

    def __init__(
        self,
        max_workers: Optional[int] = None,
        thread_workers: Optional[int] = None,
        process_workers: Optional[int] = None
    ):
        """
        初始化并行处理器

        Args:
            max_workers: 默认最大工作线程数
            thread_workers: 线程池大小
            process_workers: 进程池大小
        """
        cpu_count = multiprocessing.cpu_count()

        # 线程池（IO 密集型任务）
        self.thread_workers = thread_workers or (max_workers or cpu_count * 2)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.thread_workers)

        # 进程池（CPU 密集型任务）
        self.process_workers = process_workers or cpu_count
        self.process_pool = ProcessPoolExecutor(max_workers=self.process_workers)

        logger.info(
            f"✅ 并行处理器已初始化 "
            f"(线程池: {self.thread_workers}, 进程池: {self.process_workers})"
        )

    async def process_batch_async(
        self,
        items: List[Any],
        handler: Callable,
        batch_size: int = 10,
        mode: ProcessingMode = ProcessingMode.THREAD,
        show_progress: bool = True
    ) -> BatchResult:
        """
        异步批量处理

        Args:
            items: 待处理项目列表
            handler: 处理函数
            batch_size: 批次大小
            mode: 处理模式
            show_progress: 是否显示进度

        Returns:
            BatchResult
        """
        start_time = time.time()
        total = len(items)
        results = []
        errors = []

        logger.info(f"开始批量处理: {total} 项 (批次大小: {batch_size}, 模式: {mode.value})")

        # 选择执行器
        if mode == ProcessingMode.THREAD:
            pool = self.thread_pool
        elif mode == ProcessingMode.PROCESS:
            pool = self.process_pool
        else:
            pool = None

        # 分批处理
        for i in range(0, total, batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size

            if show_progress:
                logger.info(f"处理批次 {batch_num}/{total_batches} ({len(batch)} 项)")

            if mode == ProcessingMode.ASYNC:
                # 纯异步处理
                batch_results = await self._process_async(batch, handler)
            else:
                # 使用线程池/进程池
                batch_results = await self._process_with_pool(batch, handler, pool)

            # 收集结果和错误
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    errors.append({
                        "index": i + idx,
                        "item": batch[idx],
                        "error": str(result)
                    })
                    results.append(None)
                else:
                    results.append(result)

        duration = time.time() - start_time
        successful = total - len(errors)

        batch_result = BatchResult(
            total=total,
            successful=successful,
            failed=len(errors),
            results=results,
            errors=errors,
            duration=duration
        )

        logger.info(
            f"✅ 批量处理完成: {successful}/{total} 成功 "
            f"(成功率: {batch_result.success_rate:.1%}, 耗时: {duration:.2f}s)"
        )

        return batch_result

    async def _process_async(
        self,
        items: List[Any],
        handler: Callable
    ) -> List[Any]:
        """纯异步处理"""
        tasks = [
            asyncio.create_task(self._safe_call_async(handler, item))
            for item in items
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_with_pool(
        self,
        items: List[Any],
        handler: Callable,
        pool
    ) -> List[Any]:
        """使用线程池/进程池处理"""
        loop = asyncio.get_event_loop()

        futures = [
            loop.run_in_executor(pool, self._safe_call, handler, item)
            for item in items
        ]

        return await asyncio.gather(*futures, return_exceptions=True)

    def _safe_call(self, handler: Callable, item: Any) -> Any:
        """安全调用处理函数（同步）"""
        try:
            return handler(item)
        except Exception as e:
            logger.error(f"处理失败: {e}")
            return e

    async def _safe_call_async(self, handler: Callable, item: Any) -> Any:
        """安全调用处理函数（异步）"""
        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(item)
            else:
                return handler(item)
        except Exception as e:
            logger.error(f"处理失败: {e}")
            return e

    def process_batch_sync(
        self,
        items: List[Any],
        handler: Callable,
        batch_size: int = 10,
        mode: ProcessingMode = ProcessingMode.THREAD
    ) -> BatchResult:
        """
        同步批量处理（阻塞）

        Args:
            items: 待处理项目列表
            handler: 处理函数
            batch_size: 批次大小
            mode: 处理模式

        Returns:
            BatchResult
        """
        # 在新的事件循环中运行异步处理
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self.process_batch_async(items, handler, batch_size, mode)
            )
            return result
        finally:
            loop.close()

    async def map_async(
        self,
        items: List[Any],
        handler: Callable,
        mode: ProcessingMode = ProcessingMode.THREAD
    ) -> List[Any]:
        """
        异步 map 操作

        Args:
            items: 项目列表
            handler: 处理函数
            mode: 处理模式

        Returns:
            结果列表
        """
        result = await self.process_batch_async(
            items,
            handler,
            batch_size=len(items),  # 一次性处理
            mode=mode,
            show_progress=False
        )

        return result.results

    def shutdown(self):
        """关闭处理器"""
        logger.info("关闭并行处理器...")
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        logger.info("✅ 并行处理器已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


# 全局处理器实例
_parallel_processor: Optional[ParallelProcessor] = None


def get_parallel_processor() -> ParallelProcessor:
    """获取全局并行处理器"""
    global _parallel_processor

    if _parallel_processor is None:
        _parallel_processor = ParallelProcessor()

    return _parallel_processor


# 便捷函数
async def parallel_map(
    items: List[Any],
    handler: Callable,
    mode: ProcessingMode = ProcessingMode.THREAD
) -> List[Any]:
    """
    并行 map 函数

    Example:
        results = await parallel_map(
            documents,
            extract_text,
            mode=ProcessingMode.THREAD
        )
    """
    processor = get_parallel_processor()
    return await processor.map_async(items, handler, mode)


async def parallel_process(
    items: List[Any],
    handler: Callable,
    batch_size: int = 10,
    mode: ProcessingMode = ProcessingMode.THREAD
) -> BatchResult:
    """
    并行批量处理函数

    Example:
        result = await parallel_process(
            documents,
            process_document,
            batch_size=5,
            mode=ProcessingMode.THREAD
        )
        print(f"成功率: {result.success_rate:.1%}")
    """
    processor = get_parallel_processor()
    return await processor.process_batch_async(items, handler, batch_size, mode)
