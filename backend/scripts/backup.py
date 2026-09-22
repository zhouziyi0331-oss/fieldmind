"""
数据库备份和恢复工具
支持自动备份、恢复和清理旧备份
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupManager:
    """数据库备份管理器"""

    def __init__(self, backup_dir: str = "./backups", retention_days: int = 30):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

    def backup_sqlite(self, db_path: str) -> Optional[str]:
        """备份 SQLite 数据库"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_sqlite_{timestamp}.db"
            backup_path = self.backup_dir / backup_name

            # 使用 SQLite 的 .backup 命令
            subprocess.run(
                f'sqlite3 {db_path} ".backup {backup_path}"',
                shell=True,
                check=True
            )

            # 压缩备份
            compressed_path = f"{backup_path}.gz"
            subprocess.run(
                f"gzip {backup_path}",
                shell=True,
                check=True
            )

            logger.info(f"✅ SQLite 备份完成: {compressed_path}")
            return compressed_path

        except Exception as e:
            logger.error(f"❌ SQLite 备份失败: {e}")
            return None

    def backup_postgres(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "fieldmind",
        user: str = "fieldmind",
        password: Optional[str] = None
    ) -> Optional[str]:
        """备份 PostgreSQL 数据库"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_postgres_{timestamp}.sql"
            backup_path = self.backup_dir / backup_name

            # 设置密码环境变量
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password

            # 使用 pg_dump
            subprocess.run(
                [
                    "pg_dump",
                    "-h", host,
                    "-p", str(port),
                    "-U", user,
                    "-d", database,
                    "-f", str(backup_path),
                    "--no-owner",
                    "--no-acl",
                ],
                env=env,
                check=True
            )

            # 压缩备份
            subprocess.run(
                f"gzip {backup_path}",
                shell=True,
                check=True
            )

            compressed_path = f"{backup_path}.gz"
            logger.info(f"✅ PostgreSQL 备份完成: {compressed_path}")
            return compressed_path

        except Exception as e:
            logger.error(f"❌ PostgreSQL 备份失败: {e}")
            return None

    def restore_sqlite(self, backup_path: str, target_db: str) -> bool:
        """恢复 SQLite 数据库"""
        try:
            # 解压备份
            if backup_path.endswith('.gz'):
                subprocess.run(f"gunzip -c {backup_path} > temp_backup.db", shell=True, check=True)
                backup_path = "temp_backup.db"

            # 备份当前数据库
            if os.path.exists(target_db):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                os.rename(target_db, f"{target_db}.before_restore_{timestamp}")

            # 恢复
            subprocess.run(f"cp {backup_path} {target_db}", shell=True, check=True)

            logger.info(f"✅ SQLite 恢复完成: {target_db}")
            return True

        except Exception as e:
            logger.error(f"❌ SQLite 恢复失败: {e}")
            return False

    def restore_postgres(
        self,
        backup_path: str,
        host: str = "localhost",
        port: int = 5432,
        database: str = "fieldmind",
        user: str = "fieldmind",
        password: Optional[str] = None
    ) -> bool:
        """恢复 PostgreSQL 数据库"""
        try:
            # 解压备份
            if backup_path.endswith('.gz'):
                subprocess.run(f"gunzip -c {backup_path} > temp_backup.sql", shell=True, check=True)
                backup_path = "temp_backup.sql"

            # 设置密码环境变量
            env = os.environ.copy()
            if password:
                env['PGPASSWORD'] = password

            # 使用 psql 恢复
            subprocess.run(
                [
                    "psql",
                    "-h", host,
                    "-p", str(port),
                    "-U", user,
                    "-d", database,
                    "-f", backup_path,
                ],
                env=env,
                check=True
            )

            logger.info(f"✅ PostgreSQL 恢复完成")
            return True

        except Exception as e:
            logger.error(f"❌ PostgreSQL 恢复失败: {e}")
            return False

    def cleanup_old_backups(self):
        """清理过期的备份文件"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0

            for backup_file in self.backup_dir.glob("backup_*.gz"):
                # 从文件名提取时间戳
                try:
                    timestamp_str = backup_file.stem.split('_')[-2] + backup_file.stem.split('_')[-1]
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

                    if file_date < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.info(f"🗑️  删除过期备份: {backup_file.name}")

                except Exception as e:
                    logger.warning(f"⚠️  无法解析备份文件时间: {backup_file.name}")

            logger.info(f"✅ 清理完成，删除了 {deleted_count} 个过期备份")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ 清理备份失败: {e}")
            return 0

    def list_backups(self):
        """列出所有备份"""
        backups = []
        for backup_file in sorted(self.backup_dir.glob("backup_*.gz"), reverse=True):
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size_mb": round(size_mb, 2),
                "created": datetime.fromtimestamp(backup_file.stat().st_mtime)
            })

        return backups


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="FieldMind 数据库备份工具")
    parser.add_argument("action", choices=["backup", "restore", "list", "cleanup"],
                        help="操作类型")
    parser.add_argument("--db-type", choices=["sqlite", "postgres"], default="sqlite",
                        help="数据库类型")
    parser.add_argument("--db-path", default="./data/fieldmind.db",
                        help="SQLite 数据库路径")
    parser.add_argument("--backup-path", help="备份文件路径（恢复时使用）")
    parser.add_argument("--host", default="localhost", help="PostgreSQL 主机")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL 端口")
    parser.add_argument("--database", default="fieldmind", help="PostgreSQL 数据库名")
    parser.add_argument("--user", default="fieldmind", help="PostgreSQL 用户名")
    parser.add_argument("--password", help="PostgreSQL 密码")

    args = parser.parse_args()

    manager = BackupManager()

    if args.action == "backup":
        if args.db_type == "sqlite":
            manager.backup_sqlite(args.db_path)
        else:
            manager.backup_postgres(
                host=args.host,
                port=args.port,
                database=args.database,
                user=args.user,
                password=args.password
            )

    elif args.action == "restore":
        if not args.backup_path:
            logger.error("❌ 恢复操作需要指定 --backup-path")
            sys.exit(1)

        if args.db_type == "sqlite":
            manager.restore_sqlite(args.backup_path, args.db_path)
        else:
            manager.restore_postgres(
                backup_path=args.backup_path,
                host=args.host,
                port=args.port,
                database=args.database,
                user=args.user,
                password=args.password
            )

    elif args.action == "list":
        backups = manager.list_backups()
        if backups:
            print(f"\n找到 {len(backups)} 个备份:\n")
            for backup in backups:
                print(f"  📦 {backup['name']}")
                print(f"     大小: {backup['size_mb']} MB")
                print(f"     时间: {backup['created']}")
                print()
        else:
            print("没有找到备份文件")

    elif args.action == "cleanup":
        manager.cleanup_old_backups()


if __name__ == "__main__":
    main()
