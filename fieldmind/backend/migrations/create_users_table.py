"""
创建用户表迁移脚本
"""
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.core.security import get_password_hash

def upgrade():
    """创建用户表"""
    engine = create_engine(settings.database.url)

    with engine.connect() as conn:
        # 创建用户表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'researcher',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """))

        # 创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
        """))

        # 检查是否已有用户
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()

        # 如果没有用户，创建默认管理员
        if user_count == 0:
            hashed_password = get_password_hash("admin123456")
            conn.execute(text("""
                INSERT INTO users (email, username, hashed_password, role, is_active)
                VALUES (:email, :username, :password, :role, :active)
            """), {
                "email": "admin@fieldmind.com",
                "username": "admin",
                "password": hashed_password,
                "role": "admin",
                "active": True
            })
            print("✅ 创建默认管理员账户: admin / admin123456")

        conn.commit()
        print("✅ 用户表创建完成")

def downgrade():
    """删除用户表"""
    engine = create_engine(settings.database.url)

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS users"))
        conn.commit()
        print("✅ 用户表已删除")

if __name__ == "__main__":
    upgrade()
