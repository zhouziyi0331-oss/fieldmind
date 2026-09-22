#!/usr/bin/env python3
"""
测试编排器事务管理
验证：
1. 正常流程：所有阶段成功，数据正确提交
2. 回滚机制：某个阶段失败，所有数据库操作回滚
3. 会话传递：所有子服务使用同一个会话
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.database import get_db_session
from sqlalchemy import text
from datetime import datetime


def test_transaction_isolation():
    """测试事务隔离性"""
    print("=" * 60)
    print("测试1: 事务隔离性")
    print("=" * 60)

    db = get_db_session()

    try:
        # 记录测试前的lineage_edges数量
        result = db.execute(text("SELECT COUNT(*) FROM lineage_edges")).fetchone()
        count_before = result[0]
        print(f"测试前 lineage_edges 记录数: {count_before}")

        # 模拟编排器的事务：在同一会话中插入多条记录
        print("\n插入3条测试记录...")
        for i in range(3):
            sql = text("""
                INSERT INTO lineage_edges (
                    project_id, source_type, source_id,
                    target_type, target_id, transform_type,
                    transform_description, confidence, created_at
                ) VALUES (
                    :project_id, :source_type, :source_id,
                    :target_type, :target_id, :transform_type,
                    :transform_description, :confidence, :created_at
                )
            """)

            db.execute(sql, {
                "project_id": 9999,
                "source_type": "test_file",
                "source_id": f"test_file_{i}",
                "target_type": "test_chunk",
                "target_id": f"test_chunk_{i}",
                "transform_type": "test_transform",
                "transform_description": "事务管理测试",
                "confidence": 1.0,
                "created_at": datetime.utcnow()
            })

        # 检查未提交前的状态（在当前会话中可见）
        result = db.execute(text(
            "SELECT COUNT(*) FROM lineage_edges WHERE project_id = 9999"
        )).fetchone()
        count_in_transaction = result[0]
        print(f"事务内可见的测试记录数: {count_in_transaction}")

        # 模拟失败：回滚
        print("\n模拟失败场景，执行 rollback...")
        db.rollback()

        # 检查回滚后的状态
        result = db.execute(text(
            "SELECT COUNT(*) FROM lineage_edges WHERE project_id = 9999"
        )).fetchone()
        count_after_rollback = result[0]
        print(f"回滚后的测试记录数: {count_after_rollback}")

        # 验证
        if count_after_rollback == 0:
            print("✓ 回滚成功：所有未提交的记录已撤销")
        else:
            print(f"✗ 回滚失败：仍有 {count_after_rollback} 条记录")
            return False

        # 测试提交场景
        print("\n" + "=" * 60)
        print("测试提交场景...")
        print("=" * 60)

        # 插入并提交
        for i in range(2):
            sql = text("""
                INSERT INTO lineage_edges (
                    project_id, source_type, source_id,
                    target_type, target_id, transform_type,
                    transform_description, confidence, created_at
                ) VALUES (
                    :project_id, :source_type, :source_id,
                    :target_type, :target_id, :transform_type,
                    :transform_description, :confidence, :created_at
                )
            """)

            db.execute(sql, {
                "project_id": 9999,
                "source_type": "test_file",
                "source_id": f"commit_test_{i}",
                "target_type": "test_chunk",
                "target_id": f"commit_chunk_{i}",
                "transform_type": "test_transform",
                "transform_description": "提交测试",
                "confidence": 1.0,
                "created_at": datetime.utcnow()
            })

        db.commit()
        print("已提交2条记录")

        # 验证提交
        result = db.execute(text(
            "SELECT COUNT(*) FROM lineage_edges WHERE project_id = 9999"
        )).fetchone()
        count_after_commit = result[0]
        print(f"提交后的测试记录数: {count_after_commit}")

        if count_after_commit == 2:
            print("✓ 提交成功：记录已持久化")
        else:
            print(f"✗ 提交异常：预期2条，实际 {count_after_commit} 条")
            return False

        # 清理测试数据
        print("\n清理测试数据...")
        db.execute(text("DELETE FROM lineage_edges WHERE project_id = 9999"))
        db.commit()
        print("✓ 测试数据已清理")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


def test_service_with_db_parameter():
    """测试服务方法的db参数传递"""
    print("\n" + "=" * 60)
    print("测试2: 服务方法db参数传递")
    print("=" * 60)

    from app.services.lineage_tracker import LineageTracker
    from app.services.metric_calculator import MetricCalculator

    db = get_db_session()

    try:
        # 测试LineageTracker.record_lineage()
        print("\n测试 LineageTracker.record_lineage() 使用传入的db...")

        # 使用传入的db（不会自动commit）
        LineageTracker.record_lineage(
            project_id=9999,
            source_type="test",
            source_id="test_source",
            target_type="test",
            target_id="test_target",
            transform_type="test",
            db=db  # 传入db
        )

        # 检查（事务内可见）
        result = db.execute(text(
            "SELECT COUNT(*) FROM lineage_edges WHERE project_id = 9999"
        )).fetchone()
        count_before_commit = result[0]
        print(f"  提交前记录数: {count_before_commit}")

        # 回滚
        db.rollback()

        # 再次检查
        result = db.execute(text(
            "SELECT COUNT(*) FROM lineage_edges WHERE project_id = 9999"
        )).fetchone()
        count_after_rollback = result[0]
        print(f"  回滚后记录数: {count_after_rollback}")

        if count_after_rollback == 0:
            print("✓ LineageTracker 正确支持事务传递")
        else:
            print("✗ LineageTracker 事务传递失败")
            return False

        # 测试不传db的情况（独立事务）
        print("\n测试 LineageTracker.record_lineage() 不传db（独立事务）...")
        LineageTracker.record_lineage(
            project_id=9999,
            source_type="test",
            source_id="test_source_2",
            target_type="test",
            target_id="test_target_2",
            transform_type="test"
            # 不传db，应该自动创建并commit
        )

        # 用新会话检查（独立事务已提交）
        db2 = get_db_session()
        result = db2.execute(text(
            "SELECT COUNT(*) FROM lineage_edges WHERE project_id = 9999"
        )).fetchone()
        count_independent = result[0]
        db2.close()

        print(f"  独立事务记录数: {count_independent}")

        if count_independent == 1:
            print("✓ LineageTracker 独立调用正常工作")
        else:
            print("✗ LineageTracker 独立调用失败")
            return False

        # 清理
        db.execute(text("DELETE FROM lineage_edges WHERE project_id = 9999"))
        db.commit()
        print("✓ 测试数据已清理")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


def test_orchestrator_transaction():
    """测试编排器的统一事务管理"""
    print("\n" + "=" * 60)
    print("测试3: 编排器统一事务管理")
    print("=" * 60)

    # 检查编排器方法签名
    from app.orchestration.data_governance_orchestrator import DataGovernanceOrchestrator
    import inspect

    orchestrator = DataGovernanceOrchestrator()

    # 检查process_file方法
    print("\n检查 process_file() 方法...")
    source = inspect.getsource(orchestrator.process_file)

    checks = {
        "创建db会话": "db = get_db_session()" in source,
        "提交事务": "db.commit()" in source,
        "回滚事务": "db.rollback()" in source,
        "关闭会话": "db.close()" in source,
        "finally块": "finally:" in source
    }

    for check, passed in checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")

    if not all(checks.values()):
        print("✗ process_file() 缺少必要的事务管理代码")
        return False

    # 检查_stage_quality方法
    print("\n检查 _stage_quality() 方法...")
    source = inspect.getsource(orchestrator._stage_quality)

    # 移除所有空格和换行符来检查方法签名
    source_compact = source.replace(" ", "").replace("\n", "")

    quality_checks = {
        "接受db参数": "def_stage_quality(self,file_id:str,project_id:int,db)" in source_compact,
        "不创建新会话": "db = get_db_session()" not in source,
        "不独立commit": "db.commit()" not in source,
        "不独立rollback": "db.rollback()" not in source,
        "不独立close": "db.close()" not in source
    }

    for check, passed in quality_checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")

    if not all(quality_checks.values()):
        print("✗ _stage_quality() 仍有独立事务管理")
        return False

    # 检查_stage_lineage方法
    print("\n检查 _stage_lineage() 方法...")
    source = inspect.getsource(orchestrator._stage_lineage)

    lineage_checks = {
        "接受db参数": "db=None" in source or "db=" in source,
        "传递db给LineageTracker": "db=db" in source
    }

    for check, passed in lineage_checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")

    if not all(lineage_checks.values()):
        print("✗ _stage_lineage() 未正确传递db参数")
        return False

    # 检查_stage_metrics方法
    print("\n检查 _stage_metrics() 方法...")
    source = inspect.getsource(orchestrator._stage_metrics)

    metrics_checks = {
        "接受db参数": "db=None" in source or "db=" in source,
        "传递db给calculator": "db=db" in source
    }

    for check, passed in metrics_checks.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")

    if not all(metrics_checks.values()):
        print("✗ _stage_metrics() 未正确传递db参数")
        return False

    print("\n✓ 编排器事务管理结构正确")
    return True


def main():
    """运行所有测试"""
    print("开始事务管理测试")
    print("=" * 60)

    tests = [
        ("事务隔离性测试", test_transaction_isolation),
        ("服务db参数传递测试", test_service_with_db_parameter),
        ("编排器事务管理测试", test_orchestrator_transaction)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 执行异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")

    total = len(results)
    passed = sum(1 for _, r in results if r)

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n✓ 所有事务管理测试通过！")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
