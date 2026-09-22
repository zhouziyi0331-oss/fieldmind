"""
性能基准测试套件 - Week 2 Day 5-7
完整的性能测试：数据库、缓存、并行处理、向量化
"""
import time
import asyncio
from typing import Dict, Any, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        """初始化基准测试"""
        self.results = {}
        logger.info("✅ 性能基准测试已初始化")

    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """运行所有基准测试"""
        logger.info("🚀 开始运行完整性能基准测试...")

        results = {
            "database": await self.benchmark_database(),
            "cache": await self.benchmark_cache(),
            "parallel_processing": await self.benchmark_parallel(),
            "vectorization": await self.benchmark_vectorization(),
        }

        self.results = results
        return results

    async def benchmark_database(self) -> Dict[str, Any]:
        """数据库性能测试"""
        logger.info("📊 测试数据库性能...")

        from app.core.database import SessionLocal
        from app.models.project import Project

        db = SessionLocal()
        results = {}

        try:
            # 1. 简单查询
            start = time.time()
            projects = db.query(Project).limit(10).all()
            results["simple_query"] = time.time() - start

            # 2. 带索引的查询
            start = time.time()
            project = db.query(Project).filter(Project.id == 1).first()
            results["indexed_query"] = time.time() - start

            # 3. 复杂查询
            start = time.time()
            projects = db.query(Project).order_by(Project.created_at.desc()).limit(20).all()
            results["complex_query"] = time.time() - start

        finally:
            db.close()

        logger.info(f"✅ 数据库测试完成: 平均 {sum(results.values())/len(results)*1000:.2f}ms")
        return results

    async def benchmark_cache(self) -> Dict[str, Any]:
        """缓存性能测试"""
        logger.info("💾 测试缓存性能...")

        from app.core.cache_manager import get_cache_manager

        cache = get_cache_manager()
        results = {}

        if not cache.enabled:
            logger.warning("⚠️ 缓存未启用，跳过测试")
            return {"enabled": False}

        # 1. 写入测试
        test_data = {"key": "value", "data": [1, 2, 3, 4, 5] * 100}
        start = time.time()
        for i in range(100):
            cache.set(f"bench_key_{i}", test_data, ttl=60)
        results["write_100_items"] = time.time() - start

        # 2. 读取测试
        start = time.time()
        for i in range(100):
            cache.get(f"bench_key_{i}")
        results["read_100_items"] = time.time() - start

        # 3. 缓存命中测试
        hits = 0
        start = time.time()
        for i in range(100):
            if cache.get(f"bench_key_{i}"):
                hits += 1
        results["hit_rate"] = hits / 100

        # 清理
        cache.delete_pattern("bench_key_*")

        logger.info(f"✅ 缓存测试完成: 命中率 {results['hit_rate']:.1%}")
        return results

    async def benchmark_parallel(self) -> Dict[str, Any]:
        """并行处理性能测试"""
        logger.info("⚡ 测试并行处理性能...")

        from app.core.parallel_processor import ParallelProcessor, ProcessingMode

        processor = ParallelProcessor(max_workers=20)
        results = {}

        # 模拟任务
        def io_task(x):
            time.sleep(0.01)
            return x * 2

        items = list(range(100))

        # 1. 串行处理（对照组）
        start = time.time()
        serial_results = [io_task(x) for x in items[:20]]
        results["serial_20_items"] = time.time() - start

        # 2. 并行处理
        start = time.time()
        parallel_result = await processor.process_batch_async(
            items,
            io_task,
            batch_size=20,
            mode=ProcessingMode.THREAD,
            show_progress=False
        )
        results["parallel_100_items"] = time.time() - start

        # 3. 计算加速比
        if results["serial_20_items"] > 0:
            expected_serial = results["serial_20_items"] * 5  # 100/20
            results["speedup"] = expected_serial / results["parallel_100_items"]

        processor.shutdown()

        logger.info(f"✅ 并行处理测试完成: 加速 {results.get('speedup', 0):.1f}x")
        return results

    async def benchmark_vectorization(self) -> Dict[str, Any]:
        """向量化性能测试"""
        logger.info("🧮 测试向量化性能...")

        try:
            from app.services.optimized_vectorization_service import OptimizedVectorizationService

            service = OptimizedVectorizationService(
                model_path="./models/bge-large-zh-v1.5",
                batch_size=32,
                use_gpu=True
            )

            results = {}

            # 测试文本
            test_texts = [
                "这是一个测试文本" * 5
            ] * 50

            # 1. 向量化速度
            start = time.time()
            embeddings = service.vectorize_batch(test_texts, show_progress=False)
            duration = time.time() - start

            results["vectorize_50_texts"] = duration
            results["speed_texts_per_sec"] = len(test_texts) / duration
            results["embedding_dim"] = embeddings.shape[1]

            # 2. 内存使用
            memory = service.get_memory_usage()
            results["memory_mb"] = memory.get("cpu_memory_mb", 0)

            logger.info(f"✅ 向量化测试完成: {results['speed_texts_per_sec']:.1f} 文本/秒")
            return results

        except Exception as e:
            logger.warning(f"⚠️ 向量化测试失败: {e}")
            return {"error": str(e)}

    def generate_report(self) -> str:
        """生成性能报告"""
        if not self.results:
            return "未运行测试"

        report = []
        report.append("=" * 80)
        report.append("性能基准测试报告")
        report.append("=" * 80)

        # 数据库
        if "database" in self.results:
            db = self.results["database"]
            report.append("\n📊 数据库性能:")
            for key, value in db.items():
                report.append(f"  {key}: {value*1000:.2f}ms")

        # 缓存
        if "cache" in self.results:
            cache = self.results["cache"]
            if cache.get("enabled", True):
                report.append("\n💾 缓存性能:")
                for key, value in cache.items():
                    if key == "hit_rate":
                        report.append(f"  {key}: {value:.1%}")
                    else:
                        report.append(f"  {key}: {value:.3f}s")

        # 并行处理
        if "parallel_processing" in self.results:
            parallel = self.results["parallel_processing"]
            report.append("\n⚡ 并行处理性能:")
            for key, value in parallel.items():
                if key == "speedup":
                    report.append(f"  {key}: {value:.1f}x")
                else:
                    report.append(f"  {key}: {value:.3f}s")

        # 向量化
        if "vectorization" in self.results:
            vec = self.results["vectorization"]
            if "error" not in vec:
                report.append("\n🧮 向量化性能:")
                for key, value in vec.items():
                    if key == "speed_texts_per_sec":
                        report.append(f"  {key}: {value:.1f}")
                    elif key == "embedding_dim":
                        report.append(f"  {key}: {value}")
                    else:
                        report.append(f"  {key}: {value:.3f}")

        report.append("\n" + "=" * 80)

        return "\n".join(report)

    def save_report(self, filepath: str = "performance_report.txt"):
        """保存报告到文件"""
        report = self.generate_report()
        Path(filepath).write_text(report, encoding="utf-8")
        logger.info(f"✅ 报告已保存: {filepath}")


async def run_benchmarks():
    """运行基准测试"""
    benchmark = PerformanceBenchmark()
    await benchmark.run_all_benchmarks()

    report = benchmark.generate_report()
    print(report)

    benchmark.save_report("./performance_benchmark_report.txt")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")

    print("\n🚀 开始性能基准测试...\n")
    asyncio.run(run_benchmarks())
    print("\n✅ 测试完成！")
