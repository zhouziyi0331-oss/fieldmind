#!/usr/bin/env python3
"""
数据库初始化脚本 - 创建所有表（包括citations）
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.database import Base, engine
from app.models import (
    project, user, document, citation, document_relation, entity_alignment
)

def init_database():
    """初始化数据库，创建所有表"""
    print("🔧 开始初始化数据库...")

    try:
        # 导入所有模型（确保已注册）
        print("📦 加载数据模型...")
        print(f"   - Project: {project.Project.__tablename__}")
        print(f"   - User: {user.User.__tablename__}")
        print(f"   - Document: {document.Document.__tablename__}")
        print(f"   - Citation: {citation.Citation.__tablename__}")
        print(f"   - DocumentCitation: {citation.DocumentCitation.__tablename__}")
        print(f"   - DocumentRelation: {document_relation.DocumentRelation.__tablename__}")
        print(f"   - EntityAlignment: {entity_alignment.EntityAlignment.__tablename__}")

        # 创建所有表
        print("\n🏗️  创建数据库表...")
        Base.metadata.create_all(bind=engine)

        print("\n✅ 数据库初始化成功！")
        print("\n📋 已创建的表:")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        for table_name in inspector.get_table_names():
            print(f"   ✓ {table_name}")

    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database()
