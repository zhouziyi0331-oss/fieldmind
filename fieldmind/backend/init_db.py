#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有表并插入初始数据
"""
import sys
from pathlib import Path

# 添加 backend/src 到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.core.database import engine, Base, SessionLocal
from app.models import *
from datetime import datetime
import hashlib

def init_database():
    """初始化数据库"""
    print("开始初始化数据库...")

    # 创建所有表
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表创建完成")

    # 创建默认用户
    db = SessionLocal()
    try:
        # 检查是否已有用户
        existing_user = db.query(User).filter(User.email == "admin@fieldmind.com").first()
        if not existing_user:
            print("创建默认管理员用户...")
            admin_user = User(
                username="admin",
                email="admin@fieldmind.com",
                hashed_password=hashlib.sha256("admin123".encode()).hexdigest(),
                full_name="系统管理员",
                role=UserRole.ADMIN,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.commit()
            print("✓ 默认管理员用户创建完成")
            print("  用户名: admin")
            print("  邮箱: admin@fieldmind.com")
            print("  密码: admin123")
            print("  ⚠️  请登录后立即修改密码!")
        else:
            print("✓ 管理员用户已存在")

    except Exception as e:
        print(f"错误: {e}")
        db.rollback()
    finally:
        db.close()

    print("\n✓ 数据库初始化完成!")

if __name__ == "__main__":
    init_database()
