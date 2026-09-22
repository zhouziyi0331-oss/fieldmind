#!/usr/bin/env python3
"""
FieldMind 知识蒸馏系统 - 独立数据库初始化
直接创建所有需要的表，无需依赖 alembic 历史
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from sqlalchemy import create_engine, text
from app.core.database import Base, DATABASE_URL
from app.models.distillation import (
    DistillationJob,
    ExtractedKnowledge,
    ExtractedMethod,
    KnowledgeMethodRelation,
    MethodMethodRelation,
    ProductionSnapshot
)

def create_distillation_tables():
    """创建蒸馏系统所需的所有表"""

    print("🗄️  初始化知识蒸馏系统数据库...")
    print("=" * 50)

    # 获取数据库 URL
    db_url = DATABASE_URL
    print(f"数据库: {db_url}")

    # 创建引擎
    engine = create_engine(db_url, echo=True)

    # 创建所有表
    print("\n创建表...")
    Base.metadata.create_all(engine, tables=[
        DistillationJob.__table__,
        ExtractedKnowledge.__table__,
        ExtractedMethod.__table__,
        KnowledgeMethodRelation.__table__,
        MethodMethodRelation.__table__,
        ProductionSnapshot.__table__,
    ])

    # 验证表已创建
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '%distillation%' OR name LIKE '%extracted_%'
            ORDER BY name
        """))

        tables = [row[0] for row in result]

        print("\n✅ 已创建的表:")
        for table in tables:
            print(f"   • {table}")

        if not tables:
            print("\n⚠️  未找到蒸馏系统表！")
            return False

    print("\n" + "=" * 50)
    print("✅ 知识蒸馏系统数据库初始化完成！")
    return True

if __name__ == "__main__":
    try:
        success = create_distillation_tables()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
