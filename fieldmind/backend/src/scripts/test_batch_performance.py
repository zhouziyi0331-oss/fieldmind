#!/usr/bin/env python3
"""
批量操作性能测试
验证 record_lineage_batch 比循环调用 record_lineage 性能更好
"""

import sys
import time
from pathlib import Path
import os

# 关闭日志JSON输出，避免干扰测试结果
os.environ['LOG_FORMAT'] = 'simple'
os.environ['CONSOLE_OUTPUT'] = 'false'

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_session
from app.services.lineage_tracker import LineageTracker
from sqlalchemy import text


def setup_test_environment():
    """准备测试环境"""
    db = get_db_session()
    try:
        # 清理测试数据
        db.execute(text("DELETE FROM lineage_edges WHERE source_id LIKE 'test_%'"))
        db.commit()
        print("✓ 测试环境准备完成\n")
    finally:
        db.close()


def test_single_record_performance(chunk_count: int = 100):
    """测试逐条记录性能（旧方法 - N+1查询）"""
    print(f"测试1: 逐条记录 {chunk_count} 条血缘关系")
    print("=" * 60)

    db = get_db_session()
    try:
        start_time = time.time()

        # 模拟旧的循环插入方式
        for i in range(chunk_count):
            LineageTracker.record_lineage(
                project_id=999,
                source_type="file",
                source_id="test_file_single",
                target_type="chunk",
                target_id=f"test_chunk_{i}",
                transform_type="extract",
                transform_description="测试分块",
                db=db
            )

        db.commit()
        elapsed_time = time.time() - start_time

        print(f"  插入 {chunk_count} 条记录")
        print(f"  耗时: {elapsed_time:.3f} 秒")
        print(f"  平均: {(elapsed_time/chunk_count)*1000:.2f} 毫秒/条")
        print(f"  数据库调用次数: {chunk_count} 次 INSERT")

        return elapsed_time

    finally:
        db.close()


def test_batch_record_performance(chunk_count: int = 100):
    """测试批量记录性能（新方法 - 批量操作）"""
    print(f"\n测试2: 批量记录 {chunk_count} 条血缘关系")
    print("=" * 60)

    db = get_db_session()
    try:
        start_time = time.time()

        # 使用新的批量插入方式
        chunk_ids = [f"test_chunk_batch_{i}" for i in range(chunk_count)]
        LineageTracker.record_lineage_batch(
            project_id=999,
            source_type="file",
            source_id="test_file_batch",
            target_type="chunk",
            target_ids=chunk_ids,
            transform_type="extract",
            transform_description="测试分块",
            db=db
        )

        db.commit()
        elapsed_time = time.time() - start_time

        print(f"  插入 {chunk_count} 条记录")
        print(f"  耗时: {elapsed_time:.3f} 秒")
        print(f"  平均: {(elapsed_time/chunk_count)*1000:.2f} 毫秒/条")
        print(f"  数据库调用次数: 1 次 executemany")

        return elapsed_time

    finally:
        db.close()


def verify_data_correctness():
    """验证数据正确性"""
    print(f"\n测试3: 验证数据正确性")
    print("=" * 60)

    db = get_db_session()
    try:
        # 验证逐条插入的数据
        result1 = db.execute(text("""
            SELECT COUNT(*) FROM lineage_edges
            WHERE source_id = 'test_file_single'
        """)).scalar()

        # 验证批量插入的数据
        result2 = db.execute(text("""
            SELECT COUNT(*) FROM lineage_edges
            WHERE source_id = 'test_file_batch'
        """)).scalar()

        print(f"  逐条插入记录数: {result1}")
        print(f"  批量插入记录数: {result2}")

        if result1 > 0 and result2 > 0 and result1 == result2:
            print(f"  ✓ 数据完整性验证通过")
            return True
        else:
            print(f"  ✗ 数据完整性验证失败")
            return False

    finally:
        db.close()


def cleanup_test_data():
    """清理测试数据"""
    db = get_db_session()
    try:
        db.execute(text("DELETE FROM lineage_edges WHERE source_id LIKE 'test_%'"))
        db.commit()
        print(f"\n✓ 测试数据清理完成")
    finally:
        db.close()


def main():
    print("=" * 60)
    print("批量操作性能测试")
    print("验证 N+1 查询优化效果")
    print("=" * 60)
    print()

    try:
        # 准备环境
        setup_test_environment()

        # 测试数量
        test_count = 100

        # 运行性能测试
        time_single = test_single_record_performance(test_count)
        time_batch = test_batch_record_performance(test_count)

        # 验证数据
        data_valid = verify_data_correctness()

        # 性能对比
        print(f"\n" + "=" * 60)
        print("性能对比汇总")
        print("=" * 60)
        print(f"  逐条插入耗时: {time_single:.3f} 秒")
        print(f"  批量插入耗时: {time_batch:.3f} 秒")

        if time_batch > 0:
            speedup = time_single / time_batch
            improvement = ((time_single - time_batch) / time_single) * 100
            print(f"  性能提升: {speedup:.1f}x 倍")
            print(f"  时间节省: {improvement:.1f}%")

        print()

        # 最终结论
        if data_valid and time_batch < time_single:
            print("=" * 60)
            print("✓ 批量优化测试通过")
            print("=" * 60)
            print(f"  ✓ 数据正确性: 通过")
            print(f"  ✓ 性能优化: 批量操作明显更快")
            print(f"  ✓ N+1查询问题: 已解决")
            print()
            return 0
        else:
            print("=" * 60)
            print("✗ 测试失败")
            print("=" * 60)
            return 1

    except Exception as e:
        print(f"\n✗ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # 清理测试数据
        cleanup_test_data()


if __name__ == "__main__":
    sys.exit(main())
