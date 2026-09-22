"""
数据库迁移脚本 - 协作功能（改进版）
支持 SQLite 一次执行一条语句的限制
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from app.core.config import settings

def get_engine():
    """获取数据库引擎"""
    # 使用 database.url 而不是 DATABASE_URL
    db_url = settings.database.url
    return create_engine(db_url, echo=True)

def execute_statements(engine, statements):
    """逐条执行 SQL 语句"""
    with engine.connect() as conn:
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                    print(f"✅ 执行成功: {stmt[:50]}...")
                except Exception as e:
                    print(f"⚠️  跳过 (可能已存在): {str(e)[:100]}")

def upgrade():
    """升级数据库：创建协作相关表"""
    print("\n执行升级...")
    engine = get_engine()

    # project_members 表
    print("\n创建 project_members 表...")
    project_members_statements = [
        """
        CREATE TABLE IF NOT EXISTS project_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role VARCHAR(20) NOT NULL,
            invited_by INTEGER,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            UNIQUE (project_id, user_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON project_members(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON project_members(user_id)"
    ]
    execute_statements(engine, project_members_statements)

    # project_invites 表
    print("\n创建 project_invites 表...")
    project_invites_statements = [
        """
        CREATE TABLE IF NOT EXISTS project_invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            invite_code VARCHAR(100) UNIQUE NOT NULL,
            role VARCHAR(20) NOT NULL,
            created_by INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT 0,
            used_by INTEGER,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_project_invites_code ON project_invites(invite_code)",
        "CREATE INDEX IF NOT EXISTS idx_project_invites_project_id ON project_invites(project_id)"
    ]
    execute_statements(engine, project_invites_statements)

    # project_activity_logs 表
    print("\n创建 project_activity_logs 表...")
    project_activity_logs_statements = [
        """
        CREATE TABLE IF NOT EXISTS project_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            target_type VARCHAR(50),
            target_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_activity_logs_project_id ON project_activity_logs(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON project_activity_logs(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_activity_logs_created_at ON project_activity_logs(created_at)"
    ]
    execute_statements(engine, project_activity_logs_statements)

    print("\n✅ 数据库升级完成！")

def downgrade():
    """降级数据库：删除协作相关表"""
    print("\n执行降级...")
    engine = get_engine()

    downgrade_statements = [
        "DROP TABLE IF EXISTS project_activity_logs",
        "DROP TABLE IF EXISTS project_invites",
        "DROP TABLE IF EXISTS project_members"
    ]

    execute_statements(engine, downgrade_statements)

    print("\n✅ 数据库降级完成！")

def main():
    """主函数"""
    print("=" * 80)
    print("数据库迁移脚本 - 协作功能")
    print("=" * 80)

    if len(sys.argv) > 1:
        action = sys.argv[1].strip().lower()
    else:
        action = input("\n请选择操作 [upgrade/downgrade]: ").strip().lower()

    if action == "upgrade":
        upgrade()
    elif action == "downgrade":
        downgrade()
    else:
        print("❌ 无效的操作。请选择 'upgrade' 或 'downgrade'")
        sys.exit(1)

if __name__ == "__main__":
    main()
