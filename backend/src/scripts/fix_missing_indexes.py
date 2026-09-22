#!/usr/bin/env python3
"""
修复缺失的数据库索引
解决系统健康检查中发现的索引缺失问题
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_session
from sqlalchemy import text, inspect


def check_table_exists(db, table_name):
    """检查表是否存在"""
    inspector = inspect(db.bind)
    return table_name in inspector.get_table_names()


def check_index_exists(db, table_name, column_name):
    """检查索引是否存在"""
    inspector = inspect(db.bind)
    existing_indexes = inspector.get_indexes(table_name)

    for idx in existing_indexes:
        if column_name in idx['column_names']:
            return True
    return False


def create_index(db, table_name, column_name, index_name=None):
    """创建索引"""
    if not index_name:
        index_name = f"idx_{table_name}_{column_name}"

    try:
        # 检查表是否存在
        if not check_table_exists(db, table_name):
            print(f"  ⚠ 表不存在，跳过: {table_name}")
            return False

        # 检查索引是否已存在
        if check_index_exists(db, table_name, column_name):
            print(f"  ✓ 索引已存在: {table_name}.{column_name}")
            return True

        # 创建索引
        sql = f"CREATE INDEX {index_name} ON {table_name} ({column_name})"
        db.execute(text(sql))
        db.commit()
        print(f"  ✓ 创建索引: {table_name}.{column_name}")
        return True

    except Exception as e:
        db.rollback()
        print(f"  ✗ 创建索引失败: {table_name}.{column_name}")
        print(f"    错误: {e}")
        return False


def main():
    print("=" * 60)
    print("修复缺失的数据库索引")
    print("=" * 60)

    db = get_db_session()

    try:
        # 定义需要创建的索引
        indexes_to_create = [
            # 外键索引（提升JOIN性能）
            ("projects", "owner_id"),
            ("workflows", "created_by"),
            ("project_contexts", "parent_id"),

            # 查询优化索引
            ("project_document_assets", "document_id"),
            ("comparison_results", "project_id"),
            ("comparison_results", "created_at"),
        ]

        created_count = 0
        skipped_count = 0
        failed_count = 0

        print(f"\n需要检查的索引: {len(indexes_to_create)} 个\n")

        for table_name, column_name in indexes_to_create:
            result = create_index(db, table_name, column_name)
            if result:
                if check_index_exists(db, table_name, column_name):
                    created_count += 1
                else:
                    skipped_count += 1
            else:
                if check_table_exists(db, table_name):
                    failed_count += 1
                else:
                    skipped_count += 1

        print("\n" + "=" * 60)
        print("索引创建汇总")
        print("=" * 60)
        print(f"  ✓ 成功创建/已存在: {created_count} 个")
        print(f"  ⚠ 跳过（表不存在）: {skipped_count} 个")
        print(f"  ✗ 失败: {failed_count} 个")

        if failed_count == 0:
            print(f"\n✓ 所有索引处理完成")
            return 0
        else:
            print(f"\n✗ 有 {failed_count} 个索引创建失败")
            return 1

    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
