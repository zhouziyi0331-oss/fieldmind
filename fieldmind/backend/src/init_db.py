#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有必需的数据库表
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import init_db, SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash


def create_default_admin():
    """创建默认管理员账户"""
    db = SessionLocal()
    try:
        # 检查是否已存在管理员
        existing_admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if existing_admin:
            print(f"✅ 管理员账户已存在: {existing_admin.email}")
            return

        # 创建默认管理员
        admin = User(
            email="admin@fieldmind.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("✅ 默认管理员账户创建成功")
        print("   邮箱: admin@fieldmind.com")
        print("   密码: admin123")
        print("   ⚠️  请立即登录并修改密码！")
    except Exception as e:
        print(f"❌ 创建管理员账户失败: {e}")
        db.rollback()
    finally:
        db.close()


def create_default_industry_categories():
    """创建默认业态类别"""
    from app.models.industry import IndustryCategory

    db = SessionLocal()
    try:
        # 检查是否已存在类别
        existing = db.query(IndustryCategory).first()
        if existing:
            print("✅ 业态类别已存在")
            return

        categories = [
            {
                "category_id": "traditional-agriculture",
                "name": "传统农业",
                "description": "传统农业生产方式和技术"
            },
            {
                "category_id": "modern-agriculture",
                "name": "现代农业",
                "description": "现代化农业技术和管理"
            },
            {
                "category_id": "rural-tourism",
                "name": "乡村旅游",
                "description": "乡村旅游产业发展"
            },
            {
                "category_id": "e-commerce",
                "name": "电商经济",
                "description": "农村电商和数字经济"
            },
            {
                "category_id": "handicraft",
                "name": "手工艺",
                "description": "传统手工艺和文化产业"
            },
            {
                "category_id": "breeding",
                "name": "养殖业",
                "description": "畜牧和水产养殖"
            },
            {
                "category_id": "food-processing",
                "name": "食品加工",
                "description": "农产品加工和食品制造"
            },
        ]

        for cat_data in categories:
            category = IndustryCategory(**cat_data)
            db.add(category)

        db.commit()
        print(f"✅ 创建了 {len(categories)} 个默认业态类别")
    except Exception as e:
        print(f"❌ 创建业态类别失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("FieldMind 数据库初始化")
    print("=" * 60)

    # 1. 创建所有表
    print("\n📦 正在创建数据库表...")
    try:
        init_db()
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
        return

    # 2. 创建默认管理员
    print("\n👤 正在创建默认管理员账户...")
    create_default_admin()

    # 3. 创建默认业态类别
    print("\n🏭 正在创建默认业态类别...")
    create_default_industry_categories()

    print("\n" + "=" * 60)
    print("✅ 数据库初始化完成!")
    print("=" * 60)
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    print("\n下一步:")
    print("1. 启动后端服务: python -m app.main")
    print(f"2. 访问 API 文档: {api_url}/docs")
    print("3. 使用管理员账户登录测试")
    print()


if __name__ == "__main__":
    main()
