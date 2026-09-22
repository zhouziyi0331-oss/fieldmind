#!/usr/bin/env python3
"""
创建知识图谱相关表
使用 SQLAlchemy Base.metadata.create_all() 自动建表
"""
import sys
from pathlib import Path

# 添加 src 到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir / "src"))

from app.core.database import engine, Base
from app.models.unified_pipeline import (
    DirtyChannelDocument,
    CleanChannelEntity,
    CleanChannelEvent,
    CleanChannelRelation,
    NineStepPipelineStatus,
    UnifiedProcessingRoute
)
from sqlalchemy import inspect

def main():
    print("=== 知识图谱表自动创建 ===\n")

    # 检查当前状态
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    # 要创建的表
    kg_tables = [
        'dirty_channel_documents',
        'clean_channel_entities',
        'clean_channel_events',
        'clean_channel_relations',
        'nine_step_pipeline_status',
        'unified_processing_routes'
    ]

    print("📋 检查现有表...")
    for table in kg_tables:
        status = "✓ 存在" if table in existing_tables else "× 缺失"
        print(f"  {table}: {status}")

    # 创建所有表
    print("\n🔨 开始创建表...")
    try:
        # 只创建知识图谱相关的表
        Base.metadata.create_all(
            engine,
            tables=[
                DirtyChannelDocument.__table__,
                CleanChannelEntity.__table__,
                CleanChannelEvent.__table__,
                CleanChannelRelation.__table__,
                NineStepPipelineStatus.__table__,
                UnifiedProcessingRoute.__table__
            ],
            checkfirst=True  # 只创建不存在的表
        )
        print("✓ 表创建完成")

    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 验证创建结果
    print("\n✅ 验证创建结果...")
    inspector = inspect(engine)
    new_tables = set(inspector.get_table_names())

    for table in kg_tables:
        if table in new_tables:
            print(f"  ✓ {table}")
            # 显示字段
            columns = inspector.get_columns(table)
            print(f"    字段数: {len(columns)}")
            # 检查 is_manual 和 pipeline_step
            col_names = [col['name'] for col in columns]
            if 'is_manual' in col_names:
                print(f"    ✓ is_manual 字段存在")
            if 'pipeline_step' in col_names:
                print(f"    ✓ pipeline_step 字段存在")
        else:
            print(f"  ❌ {table} 创建失败")

    print("\n🎉 知识图谱表创建完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main())
