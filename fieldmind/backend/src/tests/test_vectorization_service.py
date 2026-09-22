#!/usr/bin/env python3
"""
测试优化的向量化服务
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.optimized_vectorization_service import OptimizedVectorizationService

print("=" * 80)
print("测试优化的向量化服务")
print("=" * 80)

# 创建测试文本
test_texts = [
    "这是第一个测试文档。",
    "这是第二个测试文档，包含更多内容。",
    "田野调查是社会学研究的重要方法。",
    "知识管理系统可以帮助研究人员整理数据。",
    "人工智能技术在数据分析中的应用越来越广泛。"
] * 20  # 100个文本

print(f"\n准备向量化 {len(test_texts)} 个文本...\n")

# 1. 测试基本向量化
print("1. 测试批量向量化...")
service = OptimizedVectorizationService(
    model_path="./models/bge-large-zh-v1.5",
    batch_size=32,
    use_gpu=True
)

start = time.time()
embeddings = service.vectorize_batch(test_texts, show_progress=True)
duration = time.time() - start

print(f"\n  ✅ 向量化完成:")
print(f"    文本数量: {len(test_texts)}")
print(f"    向量维度: {embeddings.shape}")
print(f"    总耗时: {duration:.2f}s")
print(f"    速度: {len(test_texts)/duration:.1f} 文本/秒")

# 2. 测试内存使用
print("\n2. 内存使用情况...")
memory = service.get_memory_usage()
print(f"  CPU 内存: {memory['cpu_memory_mb']:.2f} MB")
if 'gpu_memory_allocated_mb' in memory:
    print(f"  GPU 内存: {memory['gpu_memory_allocated_mb']:.2f} MB")

# 3. 性能基准测试
print("\n3. 性能基准测试...")
benchmark_texts = test_texts[:64]
benchmark_results = service.benchmark(benchmark_texts)

print(f"  设备: {benchmark_results['device']}")
print(f"  批次大小性能测试:")
for batch_name, result in benchmark_results['batch_size_tests'].items():
    print(f"    {batch_name}: {result['speed']:.1f} 文本/秒")

print("\n" + "=" * 80)
print("✅ 测试完成！")
print("=" * 80)
