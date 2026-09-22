"""
FieldMind 数据库迁移工具
用于执行数据库迁移脚本
"""
import os
import sys
from pathlib import Path
from typing import List
from datetime import datetime

# MySQL 迁移是可选运维入口，SQLite 主应用不应因未安装 mysql-connector 启动失败。
Error = Exception


class MigrationManager:
    """数据库迁移管理器"""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.migrations_dir = Path(__file__).parent.parent / "migrations"

    def connect(self):
        """连接数据库"""
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            print(f"✅ 成功连接到数据库: {self.database}")
            return True
        except ImportError:
            print("❌ 未安装 mysql-connector-python，无法执行 MySQL 迁移")
            return False
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ 数据库连接已关闭")

    def create_migrations_table(self):
        """创建迁移记录表"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    version VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(200) NOT NULL,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_version (version)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            self.connection.commit()
            print("✅ 迁移记录表已创建")
        except Error as e:
            print(f"❌ 创建迁移记录表失败: {e}")
            raise
        finally:
            cursor.close()

    def get_executed_migrations(self) -> List[str]:
        """获取已执行的迁移版本列表"""
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        except Error:
            return []
        finally:
            cursor.close()

    def get_pending_migrations(self) -> List[Path]:
        """获取待执行的迁移文件"""
        executed = set(self.get_executed_migrations())
        all_migrations = sorted(self.migrations_dir.glob("*.sql"))

        pending = []
        for migration_file in all_migrations:
            version = migration_file.stem.split('_')[0]
            if version not in executed:
                pending.append(migration_file)

        return pending

    def execute_migration(self, migration_file: Path) -> bool:
        """执行单个迁移文件"""
        version = migration_file.stem.split('_')[0]
        name = migration_file.stem

        print(f"\n📝 执行迁移: {name}")

        cursor = self.connection.cursor()
        try:
            # 读取SQL文件
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # 分割SQL语句（按分号分割，但忽略注释中的分号）
            statements = self._split_sql_statements(sql_content)

            # 执行每条SQL语句
            for i, statement in enumerate(statements, 1):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        print(f"  ✓ 执行语句 {i}/{len(statements)}")
                    except Error as e:
                        print(f"  ✗ 语句 {i} 执行失败: {e}")
                        print(f"  SQL: {statement[:100]}...")
                        raise

            # 记录迁移
            cursor.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (%s, %s)",
                (version, name)
            )

            self.connection.commit()
            print(f"✅ 迁移 {name} 执行成功")
            return True

        except Error as e:
            self.connection.rollback()
            print(f"❌ 迁移 {name} 执行失败: {e}")
            return False
        finally:
            cursor.close()

    def _split_sql_statements(self, sql_content: str) -> List[str]:
        """分割SQL语句"""
        statements = []
        current_statement = []
        in_delimiter = False

        for line in sql_content.split('\n'):
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('--'):
                continue

            # 处理DELIMITER语句
            if line.upper().startswith('DELIMITER'):
                in_delimiter = not in_delimiter
                continue

            current_statement.append(line)

            # 检查语句结束
            if (not in_delimiter and line.endswith(';')) or \
               (in_delimiter and line.upper() == 'END'):
                statements.append(' '.join(current_statement))
                current_statement = []

        # 添加最后一个语句（如果有）
        if current_statement:
            statements.append(' '.join(current_statement))

        return statements

    def migrate(self):
        """执行所有待执行的迁移"""
        print("\n" + "=" * 60)
        print("FieldMind 数据库迁移")
        print("=" * 60)

        if not self.connect():
            return False

        try:
            # 创建迁移记录表
            self.create_migrations_table()

            # 获取待执行的迁移
            pending = self.get_pending_migrations()

            if not pending:
                print("\n✅ 没有待执行的迁移")
                return True

            print(f"\n📋 发现 {len(pending)} 个待执行的迁移:")
            for migration_file in pending:
                print(f"  - {migration_file.name}")

            # 执行迁移
            success_count = 0
            for migration_file in pending:
                if self.execute_migration(migration_file):
                    success_count += 1
                else:
                    print(f"\n❌ 迁移中断")
                    return False

            print("\n" + "=" * 60)
            print(f"✅ 成功执行 {success_count}/{len(pending)} 个迁移")
            print("=" * 60)
            return True

        finally:
            self.disconnect()

    def rollback(self, steps: int = 1):
        """回滚迁移（暂未实现）"""
        print("⚠️  回滚功能暂未实现")
        print("提示：请手动执行回滚SQL或恢复数据库备份")

    def status(self):
        """查看迁移状态"""
        print("\n" + "=" * 60)
        print("数据库迁移状态")
        print("=" * 60)

        if not self.connect():
            return

        try:
            self.create_migrations_table()
            executed = self.get_executed_migrations()
            pending = self.get_pending_migrations()

            print(f"\n✅ 已执行的迁移 ({len(executed)}):")
            for version in executed:
                print(f"  - {version}")

            print(f"\n⏳ 待执行的迁移 ({len(pending)}):")
            for migration_file in pending:
                print(f"  - {migration_file.name}")

            print("\n" + "=" * 60)

        finally:
            self.disconnect()


def main():
    """主函数"""
    # 从环境变量读取数据库配置
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "fieldmind"),
    }

    manager = MigrationManager(**config)

    # 解析命令行参数
    if len(sys.argv) < 2:
        print("用法:")
        print("  python migrate.py migrate   # 执行所有待执行的迁移")
        print("  python migrate.py status    # 查看迁移状态")
        print("  python migrate.py rollback  # 回滚迁移（暂未实现）")
        sys.exit(1)

    command = sys.argv[1]

    if command == "migrate":
        success = manager.migrate()
        sys.exit(0 if success else 1)
    elif command == "status":
        manager.status()
    elif command == "rollback":
        steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        manager.rollback(steps)
    else:
        print(f"❌ 未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
