#!/usr/bin/env python3
"""知识图谱构建性能基准测试"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from app.core.database import SessionLocal
from app.models.project import ProjectDocument
from app.services.knowledge_graph_builder import KnowledgeGraphBuilder
from app.services.knowledge_graph_builder_optimized import KnowledgeGraphBuilderOptimized


def benchmark_single_document(doc_id: int, project_id: int, use_optimized: bool = False):
    """测试单文档处理性能"""
    db = SessionLocal()

    try:
        if use_optimized:
            builder = KnowledgeGraphBuilderOptimized(db)
            version = "优化版"
        else:
            builder = KnowledgeGraphBuilder(db)
            version = "原始版"

        print(f"\n{'='*60}")
        print(f"测试版本: {version}")
        print(f"文档ID: {doc_id}, 项目ID: {project_id}")
        print(f"{'='*60}")

        # 获取文档信息
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
        if not doc:
            print(f"❌ 文档 {doc_id} 不存在")
            return None

        text_length = len(doc.text_content) if doc.text_content else 0
        print(f"📄 文档: {doc.filename}")
        print(f"📝 文本长度: {text_length} 字符")

        # 开始计时
        start_time = time.time()

        # 执行构建
        stats = builder.build_from_document(doc_id, project_id)

        # 结束计时
        end_time = time.time()
        elapsed = end_time - start_time

        print(f"\n⏱️  耗时: {elapsed:.2f} 秒")
        print(f"📊 统计:")
        print(f"   - 创建实体: {stats['entities_created']}")
        print(f"   - 更新实体: {stats.get('entities_updated', 0)}")
        print(f"   - 创建关系: {stats['relationships_created']}")
        print(f"   - 时间线事件: {stats['timeline_events']}")

        # 计算性能指标
        total_entities = stats['entities_created'] + stats.get('entities_updated', 0)
        if elapsed > 0:
            entities_per_sec = total_entities / elapsed
            chars_per_sec = text_length / elapsed
            print(f"\n⚡ 性能指标:")
            print(f"   - 处理速度: {entities_per_sec:.2f} 实体/秒")
            print(f"   - 文本处理: {chars_per_sec:.0f} 字符/秒")

        return {
            "version": version,
            "elapsed": elapsed,
            "stats": stats,
            "text_length": text_length,
            "entities_per_sec": entities_per_sec if elapsed > 0 else 0
        }

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


def benchmark_comparison(doc_id: int, project_id: int):
    """对比测试：原始版 vs 优化版"""
    print(f"\n{'#'*60}")
    print(f"# 性能对比测试")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    # 测试原始版
    result_original = benchmark_single_document(doc_id, project_id, use_optimized=False)

    # 测试优化版
    result_optimized = benchmark_single_document(doc_id, project_id, use_optimized=True)

    # 对比结果
    if result_original and result_optimized:
        print(f"\n{'='*60}")
        print(f"📊 对比结果")
        print(f"{'='*60}")

        speedup = result_original['elapsed'] / result_optimized['elapsed']
        time_saved = result_original['elapsed'] - result_optimized['elapsed']
        time_saved_percent = (time_saved / result_original['elapsed']) * 100

        print(f"\n⏱️  耗时对比:")
        print(f"   原始版: {result_original['elapsed']:.2f} 秒")
        print(f"   优化版: {result_optimized['elapsed']:.2f} 秒")
        print(f"   提速: {speedup:.2f}x ({time_saved_percent:.1f}% 更快)")
        print(f"   节省时间: {time_saved:.2f} 秒")

        print(f"\n⚡ 性能提升:")
        orig_eps = result_original['entities_per_sec']
        opt_eps = result_optimized['entities_per_sec']
        print(f"   原始版: {orig_eps:.2f} 实体/秒")
        print(f"   优化版: {opt_eps:.2f} 实体/秒")
        print(f"   提升: {(opt_eps/orig_eps):.2f}x")

        # 判断是否达到目标
        target_speedup = 5.0  # 目标提速5倍
        if speedup >= target_speedup:
            print(f"\n✅ 达到性能目标！(目标: {target_speedup}x, 实际: {speedup:.2f}x)")
        else:
            print(f"\n⚠️  未达到性能目标 (目标: {target_speedup}x, 实际: {speedup:.2f}x)")

        return {
            "original": result_original,
            "optimized": result_optimized,
            "speedup": speedup,
            "time_saved_percent": time_saved_percent
        }

    return None


def list_available_documents():
    """列出可用的测试文档"""
    db = SessionLocal()
    try:
        docs = db.query(ProjectDocument).limit(10).all()

        print(f"\n可用的测试文档:")
        print(f"{'ID':<10} {'项目ID':<10} {'文件名':<40} {'文本长度':<15}")
        print(f"{'-'*80}")

        for doc in docs:
            text_len = len(doc.text_content) if doc.text_content else 0
            filename = doc.filename[:37] + "..." if len(doc.filename) > 40 else doc.filename
            print(f"{doc.id:<10} {doc.project_id:<10} {filename:<40} {text_len:<15}")

        return docs
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="知识图谱构建性能基准测试")
    parser.add_argument("--doc-id", type=int, help="文档ID")
    parser.add_argument("--project-id", type=int, help="项目ID")
    parser.add_argument("--list", action="store_true", help="列出可用文档")
    parser.add_argument("--original", action="store_true", help="仅测试原始版")
    parser.add_argument("--optimized", action="store_true", help="仅测试优化版")

    args = parser.parse_args()

    if args.list:
        list_available_documents()
    elif args.doc_id and args.project_id:
        if args.original:
            benchmark_single_document(args.doc_id, args.project_id, use_optimized=False)
        elif args.optimized:
            benchmark_single_document(args.doc_id, args.project_id, use_optimized=True)
        else:
            # 默认：对比测试
            benchmark_comparison(args.doc_id, args.project_id)
    else:
        # 自动选择第一个可用文档进行测试
        docs = list_available_documents()
        if docs:
            print(f"\n使用第一个文档进行测试...")
            benchmark_comparison(docs[0].id, docs[0].project_id)
        else:
            print(f"\n❌ 没有可用的测试文档")
            print(f"\n用法:")
            print(f"  python3 benchmark_kg_performance.py --list")
            print(f"  python3 benchmark_kg_performance.py --doc-id 1 --project-id 1")
