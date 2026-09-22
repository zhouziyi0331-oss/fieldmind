"""
数据库迁移脚本 - 添加协作相关表
创建日期: 2026-09-09
"""

def upgrade():
    """升级数据库"""

    # 1. 创建项目成员表
    print("创建 project_members 表...")

    create_members_table = """
    CREATE TABLE IF NOT EXISTS project_members (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        role VARCHAR(20) NOT NULL,
        invited_by INTEGER,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_project FOREIGN KEY (project_id)
            REFERENCES projects(id) ON DELETE CASCADE,
        CONSTRAINT unique_project_user UNIQUE (project_id, user_id)
    );

    CREATE INDEX idx_project_members_project_id ON project_members(project_id);
    CREATE INDEX idx_project_members_user_id ON project_members(user_id);
    """

    # 2. 创建项目邀请表
    print("创建 project_invites 表...")

    create_invites_table = """
    CREATE TABLE IF NOT EXISTS project_invites (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL,
        invite_code VARCHAR(100) UNIQUE NOT NULL,
        role VARCHAR(20) NOT NULL,
        created_by INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        is_used BOOLEAN DEFAULT FALSE,
        used_by INTEGER,
        used_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_project FOREIGN KEY (project_id)
            REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE INDEX idx_project_invites_code ON project_invites(invite_code);
    CREATE INDEX idx_project_invites_project_id ON project_invites(project_id);
    """

    # 3. 创建项目活动日志表
    print("创建 project_activity_logs 表...")

    create_logs_table = """
    CREATE TABLE IF NOT EXISTS project_activity_logs (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        action VARCHAR(50) NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        CONSTRAINT fk_project FOREIGN KEY (project_id)
            REFERENCES projects(id) ON DELETE CASCADE
    );

    CREATE INDEX idx_activity_logs_project_id ON project_activity_logs(project_id);
    CREATE INDEX idx_activity_logs_user_id ON project_activity_logs(user_id);
    CREATE INDEX idx_activity_logs_created_at ON project_activity_logs(created_at);
    """

    return [
        create_members_table,
        create_invites_table,
        create_logs_table
    ]


def downgrade():
    """回滚数据库"""

    print("删除协作相关表...")

    return [
        "DROP TABLE IF EXISTS project_activity_logs CASCADE;",
        "DROP TABLE IF EXISTS project_invites CASCADE;",
        "DROP TABLE IF EXISTS project_members CASCADE;"
    ]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

    from app.core.database import engine
    from sqlalchemy import text

    print("="*80)
    print("数据库迁移脚本 - 协作功能")
    print("="*80)
    print()

    action = input("请选择操作 [upgrade/downgrade]: ").strip().lower()

    if action == "upgrade":
        print("\n执行升级...")
        sql_statements = upgrade()

        with engine.connect() as conn:
            for sql in sql_statements:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print("✅ 执行成功")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                    conn.rollback()

        print("\n✅ 数据库升级完成！")

    elif action == "downgrade":
        confirm = input("确认要回滚吗？这将删除所有协作数据 [yes/no]: ").strip().lower()

        if confirm == "yes":
            print("\n执行回滚...")
            sql_statements = downgrade()

            with engine.connect() as conn:
                for sql in sql_statements:
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        print("✅ 执行成功")
                    except Exception as e:
                        print(f"❌ 错误: {e}")
                        conn.rollback()

            print("\n✅ 数据库回滚完成！")
        else:
            print("已取消回滚")
    else:
        print("无效的操作")
