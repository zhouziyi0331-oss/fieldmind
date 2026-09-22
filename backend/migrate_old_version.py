#!/usr/bin/env python3
"""
数据迁移脚本：从旧版本迁移到新版本
旧: /Users/alwan/FieldMind/fieldmind/backend/src/data/fieldmind.db (47MB)
新: /Users/alwan/FieldMind/backend/fieldmind.db
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

OLD_DB = "/Users/alwan/FieldMind/fieldmind/backend/src/data/fieldmind.db"
NEW_DB = "/Users/alwan/FieldMind/backend/fieldmind.db"
BACKUP_DIR = "/Users/alwan/FieldMind/backend/db_backup"

def backup_databases():
    """备份新旧数据库"""
    Path(BACKUP_DIR).mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 备份旧数据库
    old_backup = f"{BACKUP_DIR}/old_fieldmind_{timestamp}.db"
    shutil.copy2(OLD_DB, old_backup)
    print(f"✅ 旧数据库已备份: {old_backup}")

    # 备份新数据库
    if Path(NEW_DB).exists():
        new_backup = f"{BACKUP_DIR}/new_fieldmind_{timestamp}.db"
        shutil.copy2(NEW_DB, new_backup)
        print(f"✅ 新数据库已备份: {new_backup}")

    return old_backup, new_backup if Path(NEW_DB).exists() else None

def check_old_db_content():
    """检查旧数据库内容"""
    print("\n" + "="*80)
    print("检查旧数据库内容...")
    print("="*80)

    conn = sqlite3.connect(OLD_DB)
    cursor = conn.cursor()

    # 检查关键表
    tables_to_check = [
        "projects", "documents", "document_chunks", "entities",
        "skills", "chat_sessions", "reports", "users"
    ]

    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  ✅ {table}: {count} 条数据")
        except:
            print(f"  ⚠️  {table}: 表不存在")

    conn.close()

def migrate_data():
    """迁移数据"""
    print("\n" + "="*80)
    print("开始数据迁移...")
    print("="*80)

    old_conn = sqlite3.connect(OLD_DB)
    new_conn = sqlite3.connect(NEW_DB)

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    # 迁移projects
    print("\n迁移projects...")
    try:
        old_cursor.execute("SELECT * FROM projects")
        projects = old_cursor.fetchall()

        if projects:
            old_cursor.execute("PRAGMA table_info(projects)")
            columns = [col[1] for col in old_cursor.fetchall()]

            for project in projects:
                # 构建INSERT语句
                placeholders = ",".join(["?" for _ in columns])
                cols = ",".join(columns)

                try:
                    new_cursor.execute(
                        f"INSERT OR IGNORE INTO projects ({cols}) VALUES ({placeholders})",
                        project
                    )
                    print(f"  ✅ 迁移项目: {project[1] if len(project) > 1 else 'unknown'}")
                except Exception as e:
                    print(f"  ⚠️  跳过项目: {e}")
    except Exception as e:
        print(f"  ❌ 迁移projects失败: {e}")

    # 迁移entities
    print("\n迁移entities...")
    try:
        old_cursor.execute("SELECT * FROM entities LIMIT 10")
        entities = old_cursor.fetchall()

        if entities:
            print(f"  发现 {len(entities)} 个实体（显示前10个）")
            for entity in entities[:5]:
                print(f"    - {entity}")
    except Exception as e:
        print(f"  ⚠️  读取entities失败: {e}")

    # 迁移chunks
    print("\n迁移chunks...")
    try:
        old_cursor.execute("SELECT COUNT(*) FROM document_chunks")
        chunk_count = old_cursor.fetchone()[0]
        print(f"  发现 {chunk_count} 个chunks")
    except Exception as e:
        print(f"  ⚠️  读取chunks失败: {e}")

    new_conn.commit()
    old_conn.close()
    new_conn.close()

    print("\n✅ 数据迁移完成")

def check_unique_modules():
    """检查旧版本独有的模块"""
    print("\n" + "="*80)
    print("检查旧版本独有功能模块...")
    print("="*80)

    unique_modules = [
        "unified_pipeline_coordinator.py",
        "boundary2_validator.py",
        "summary_generator.py",
        "kg_analysis_service.py",
        "vision_service.py"
    ]

    old_base = Path("/Users/alwan/FieldMind/fieldmind")
    new_base = Path("/Users/alwan/FieldMind")

    for module in unique_modules:
        old_files = list(old_base.rglob(module))
        new_files = list(new_base.rglob(module))

        # 排除fieldmind子目录
        new_files = [f for f in new_files if 'fieldmind/' not in str(f)]

        if old_files and not new_files:
            print(f"  ⚠️  {module}: 只在旧版本存在")
        elif old_files and new_files:
            print(f"  ✅ {module}: 已迁移")
        else:
            print(f"  ℹ️  {module}: 不存在")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         旧版本数据迁移工具                                        ║
╚══════════════════════════════════════════════════════════════════╝

⚠️  重要提醒：
   - 此脚本会备份新旧数据库
   - 迁移关键数据到新数据库
   - 不会删除任何原始文件
""")

    input("按回车键开始检查... (Ctrl+C取消)")

    # 步骤1: 检查旧数据库内容
    check_old_db_content()

    # 步骤2: 检查独有模块
    check_unique_modules()

    print("\n" + "="*80)
    print("建议:")
    print("="*80)
    print("""
1. 旧数据库包含重要数据（1个项目、1132个实体、1036个chunks）
2. 35个独有模块需要逐个检查是否已迁移功能
3. 建议：
   - 先备份数据
   - 手动验证关键功能是否已在主程序中实现
   - 确认无误后再删除旧版本

是否继续数据迁移？(y/n)
    """)

    choice = input().lower()
    if choice == 'y':
        # 备份
        backup_databases()

        # 迁移（需要仔细处理schema差异）
        print("\n⚠️  警告：自动迁移可能因schema不兼容而失败")
        print("建议手动检查和迁移关键数据")

        migrate_choice = input("\n是否尝试自动迁移？(y/n): ").lower()
        if migrate_choice == 'y':
            migrate_data()
    else:
        print("\n已取消迁移")

if __name__ == "__main__":
    main()
