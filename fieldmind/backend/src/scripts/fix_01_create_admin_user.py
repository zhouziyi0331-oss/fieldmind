#!/usr/bin/env python3
"""
创建初始管理员用户

修复：users表为空导致无法登录系统
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash
import sqlite3

def create_initial_admin():
    """创建初始管理员用户"""
    print("="*60)
    print("创建初始管理员用户")
    print("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查是否已有用户
    cursor.execute("SELECT COUNT(*) FROM users")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0:
        print(f"⚠️ 已有 {existing_count} 个用户，跳过创建")
        conn.close()
        return

    # 创建管理员账号
    admin_id = str(uuid.uuid4())
    email = "admin@fieldmind.local"
    username = "admin"
    password = "fieldmind2024"  # 初始密码，首次登录后应修改
    hashed_password = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (id, email, username, hashed_password, role, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        admin_id,
        email,
        username,
        hashed_password,
        'admin',
        True,
        datetime.utcnow(),
        datetime.utcnow()
    ))

    conn.commit()
    conn.close()

    print(f"✅ 已创建管理员用户")
    print(f"   用户名: {username}")
    print(f"   邮箱: {email}")
    print(f"   初始密码: {password}")
    print(f"   角色: admin")
    print(f"\n⚠️ 首次登录后请立即修改密码")


def verify_user_creation():
    """验证用户创建"""
    print("\n" + "="*60)
    print("验证用户创建")
    print("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, email, role, is_active FROM users")
    users = cursor.fetchall()

    if users:
        print(f"\n当前用户列表（共{len(users)}个）:")
        for username, email, role, is_active in users:
            status = "激活" if is_active else "未激活"
            print(f"  - {username} ({email}) | 角色: {role} | 状态: {status}")
    else:
        print("❌ 用户表仍为空")

    conn.close()


if __name__ == "__main__":
    create_initial_admin()
    verify_user_creation()

    print("\n" + "="*60)
    print("✅ 问题 #1 修复完成")
    print("="*60)
