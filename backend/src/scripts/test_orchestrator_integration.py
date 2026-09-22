#!/usr/bin/env python3
"""
编排器集成测试
验证批量血缘追踪在真实编排流程中的运行情况
"""

import sys
import os
from pathlib import Path

# 关闭详细日志
os.environ['LOG_FORMAT'] = 'simple'
os.environ['CONSOLE_OUTPUT'] = 'false'

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_session
from app.orchestration.data_governance_orchestrator import DataGovernanceOrchestrator
from sqlalchemy import text


def setup_test_project():
    """创建测试项目"""
    db = get_db_session()
    try:
        # 检查测试项目是否存在
        result = db.execute(text("""
            SELECT id FROM projects
            WHERE name = 'orchestrator_test_project'
        """)).fetchone()

        if result:
            project_id = result[0]
            print(f"✓ 使用现有测试项目 (ID: {project_id})")
        else:
            # 创建测试项目
            db.execute(text("""
                INSERT INTO projects (name, description, owner_id, status, created_at)
                VALUES ('orchestrator_test_project', '编排器集成测试项目', '1', 'active', datetime('now'))
            """))
            db.commit()

            result = db.execute(text("""
                SELECT id FROM projects
                WHERE name = 'orchestrator_test_project'
            """)).fetchone()
            project_id = result[0]
            print(f"✓ 创建测试项目 (ID: {project_id})")

        return project_id

    finally:
        db.close()


def cleanup_test_data(project_id):
    """清理测试数据"""
    db = get_db_session()
    try:
        # 清理血缘记录
        db.execute(text("""
            DELETE FROM lineage_edges WHERE project_id = :project_id
        """), {"project_id": project_id})

        # 清理document_chunks（如果表存在）
        try:
            db.execute(text("""
                DELETE FROM document_chunks WHERE file_id LIKE 'test_file_%'
            """))
        except Exception:
            pass  # 表可能不存在，忽略

        db.commit()
        print("✓ 测试数据清理完成")

    finally:
        db.close()


def test_stage_lineage_batch():
    """测试编排器的批量血缘追踪阶段"""
    print("\n测试1: 编排器批量血缘追踪")
    print("=" * 60)

    project_id = setup_test_project()

    # 先清理旧数据，确保测试环境干净
    cleanup_test_data(project_id)

    # 创建编排器实例（不需要传project_id）
    orchestrator = DataGovernanceOrchestrator()

    # 模拟chunk_ids
    file_id = "test_file_orchestrator_001"
    chunk_ids = [f"chunk_{i}" for i in range(50)]

    print(f"  文件ID: {file_id}")
    print(f"  块数量: {len(chunk_ids)}")

    db = get_db_session()
    try:
        # 调用血缘追踪阶段
        result = orchestrator._stage_lineage(
            file_id=file_id,
            chunk_ids=chunk_ids,
            project_id=project_id,
            db=db
        )

        db.commit()

        print(f"\n  血缘记录结果:")
        print(f"    - 记录数量: {result.get('lineage_recorded', 0)}")
        print(f"    - 追踪块数: {result.get('chunks_tracked', 0)}")

        # 验证数据库中的记录
        count = db.execute(text("""
            SELECT COUNT(*) FROM lineage_edges
            WHERE project_id = :project_id
            AND source_id = :file_id
        """), {"project_id": project_id, "file_id": file_id}).scalar()

        print(f"    - 数据库验证: {count} 条")

        if count == len(chunk_ids):
            print(f"\n  ✓ 批量血缘追踪成功")
            return True
        else:
            print(f"\n  ✗ 数据不一致: 期望 {len(chunk_ids)}，实际 {count}")
            return False

    except Exception as e:
        print(f"\n  ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        cleanup_test_data(project_id)


def test_empty_chunks():
    """测试空chunk_ids列表的处理"""
    print("\n测试2: 空chunk列表处理")
    print("=" * 60)

    project_id = setup_test_project()
    orchestrator = DataGovernanceOrchestrator()

    db = get_db_session()
    try:
        # 测试空列表
        result = orchestrator._stage_lineage(
            file_id="test_empty_file",
            chunk_ids=[],
            project_id=project_id,
            db=db
        )

        print(f"  空列表返回结果: {result}")

        if result.get('lineage_recorded') == 0 and result.get('chunks_tracked') == 0:
            print(f"  ✓ 空列表处理正确")
            return True
        else:
            print(f"  ✗ 空列表处理异常")
            return False

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False
    finally:
        db.close()


def test_transaction_handling():
    """测试事务处理和回滚"""
    print("\n测试3: 事务处理")
    print("=" * 60)

    project_id = setup_test_project()
    orchestrator = DataGovernanceOrchestrator()

    db = get_db_session()
    try:
        # 正常插入
        result = orchestrator._stage_lineage(
            file_id="test_transaction_file",
            chunk_ids=["chunk_1", "chunk_2", "chunk_3"],
            project_id=project_id,
            db=db
        )

        # 不提交，而是回滚
        db.rollback()

        # 验证数据未保存
        count = db.execute(text("""
            SELECT COUNT(*) FROM lineage_edges
            WHERE source_id = 'test_transaction_file'
        """)).scalar()

        print(f"  回滚后记录数: {count}")

        if count == 0:
            print(f"  ✓ 事务回滚正确")
            return True
        else:
            print(f"  ✗ 事务回滚失败，仍有 {count} 条记录")
            return False

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        return False
    finally:
        db.close()


def test_large_batch():
    """测试大批量数据处理"""
    print("\n测试4: 大批量数据处理")
    print("=" * 60)

    project_id = setup_test_project()
    orchestrator = DataGovernanceOrchestrator()

    # 测试500个chunk
    large_chunk_ids = [f"chunk_large_{i}" for i in range(500)]

    print(f"  测试数据量: {len(large_chunk_ids)} 个chunks")

    db = get_db_session()
    try:
        import time
        start = time.time()

        result = orchestrator._stage_lineage(
            file_id="test_large_file",
            chunk_ids=large_chunk_ids,
            project_id=project_id,
            db=db
        )

        db.commit()
        elapsed = time.time() - start

        print(f"  处理时间: {elapsed:.3f} 秒")
        print(f"  平均速度: {len(large_chunk_ids)/elapsed:.0f} 条/秒")

        # 验证
        count = db.execute(text("""
            SELECT COUNT(*) FROM lineage_edges
            WHERE source_id = 'test_large_file'
        """)).scalar()

        print(f"  数据库验证: {count} 条")

        if count == len(large_chunk_ids):
            print(f"  ✓ 大批量处理成功")
            return True
        else:
            print(f"  ✗ 数据不完整")
            return False

    except Exception as e:
        print(f"  ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        cleanup_test_data(project_id)


def main():
    print("=" * 60)
    print("编排器集成测试")
    print("验证批量血缘追踪在实际场景中的表现")
    print("=" * 60)

    results = {
        "批量血缘追踪": test_stage_lineage_batch(),
        "空列表处理": test_empty_chunks(),
        "事务处理": test_transaction_handling(),
        "大批量处理": test_large_batch()
    }

    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")

    passed_count = sum(results.values())
    total_count = len(results)

    print(f"\n总计: {passed_count}/{total_count} 测试通过")

    if passed_count == total_count:
        print("\n✓ 所有集成测试通过")
        return 0
    else:
        print(f"\n✗ {total_count - passed_count} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
