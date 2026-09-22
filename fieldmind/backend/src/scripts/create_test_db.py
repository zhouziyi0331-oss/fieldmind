#!/usr/bin/env python3
"""
快速创建测试数据库和表

用于Phase 5测试
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from app.core.database import Base

# Import all models to register them with Base
import app.models

def create_test_database(db_path="sqlite:///./fieldmind.db"):
    """创建数据库和所有表"""
    print(f"创建数据库: {db_path}")

    engine = create_engine(db_path, echo=True)

    print("\n创建所有表...")
    Base.metadata.create_all(bind=engine)

    print("\n✓ 数据库创建完成")

    # 验证表是否创建
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\n创建的表 ({len(tables)} 个):")
    for table in sorted(tables):
        print(f"  - {table}")

    # 检查Phase 5表
    phase5_tables = ['report_analysis_cache', 'synthesis_results', 'report_layers']
    print("\nPhase 5 表检查:")
    for table in phase5_tables:
        if table in tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} - 缺失!")

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "sqlite:///./fieldmind.db"
    create_test_database(db_path)
