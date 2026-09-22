#!/usr/bin/env python3
"""
FieldMind 系统完整验证和清理脚本
执行阶段2-4的所有任务
"""
import os
import sys
import sqlite3
from pathlib import Path
import shutil
import json

PROJECT_ROOT = Path("/Users/alwan/FieldMind")
BACKEND_ROOT = PROJECT_ROOT / "backend"

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def verify_database():
    """验证数据库完整性"""
    print_section("验证数据库")

    db_path = BACKEND_ROOT / "fieldmind.db"
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查表数量
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
    table_count = cursor.fetchone()[0]
    print(f"✅ 数据库表数量: {table_count}")

    # 检查关键表
    expected_tables = [
        'projects', 'project_documents', 'chunks', 'entities',
        'evaluation_test_cases', 'evaluation_runs', 'agent_traces',
        'knowledge_sources'
    ]

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}

    missing_tables = [t for t in expected_tables if t not in existing_tables]

    if missing_tables:
        print(f"⚠️  缺少表: {', '.join(missing_tables)}")
    else:
        print(f"✅ 所有关键表都存在")

    # 检查knowledge_sources数据
    cursor.execute("SELECT COUNT(*) FROM knowledge_sources")
    source_count = cursor.fetchone()[0]
    print(f"✅ 知识来源分级: {source_count} 级")

    conn.close()
    return True

def check_backup_safety():
    """检查备份目录的安全性"""
    print_section("检查备份目录安全性")

    # 可以安全删除的备份（纯应用包）
    safe_to_delete = [
        "/Users/alwan/Desktop/FieldMind_Apps/FieldMind.app",
        "/Users/alwan/Desktop/FieldMind_Apps/FieldMind_backup_20260910_184203.app",
        "/Users/alwan/Desktop/FieldMind_Apps/FieldMind_backup_20260910_190538.app",
    ]

    # 需要检查的目录
    need_check = [
        "/Users/alwan/.fieldmind",
        "/Users/alwan/Library/Application Support/FieldMind",
    ]

    print("📁 可以安全删除的备份（.app应用包）:")
    total_size = 0
    for path in safe_to_delete:
        if os.path.exists(path):
            size = get_dir_size(path)
            total_size += size
            print(f"   ✅ {path} ({format_size(size)})")
        else:
            print(f"   ⚠️  {path} (不存在)")

    print(f"\n   总计可释放空间: {format_size(total_size)}")

    print("\n📁 需要检查后才能删除:")
    for path in need_check:
        if os.path.exists(path):
            size = get_dir_size(path)
            print(f"   ⚠️  {path} ({format_size(size)})")

            # 检查是否有数据库
            db_files = list(Path(path).rglob("*.db"))
            if db_files:
                print(f"       包含 {len(db_files)} 个数据库文件")
                for db in db_files[:3]:
                    db_size = os.path.getsize(db)
                    if db_size > 0:
                        print(f"       - {db.name}: {format_size(db_size)} (有数据)")
        else:
            print(f"   ✅ {path} (不存在)")

    return safe_to_delete

def get_dir_size(path):
    """获取目录大小"""
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_dir_size(entry.path)
    except:
        pass
    return total

def format_size(bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f}{unit}"
        bytes /= 1024
    return f"{bytes:.1f}TB"

def analyze_api_duplication():
    """分析API重复和未使用的路由"""
    print_section("分析API端点")

    # 统计路由
    os.chdir(BACKEND_ROOT)
    import subprocess

    result = subprocess.run([
        'python3', '-c',
        """
import sys
sys.path.insert(0, 'src')
from app.main import app
routes = {}
for route in app.routes:
    if hasattr(route, 'path'):
        path = route.path
        methods = getattr(route, 'methods', {'GET'})
        for method in methods:
            key = f"{method} {path}"
            if key not in routes:
                routes[key] = []
            routes[key].append(route.name or 'anonymous')

print(f"总路由数: {len(routes)}")

# 找出重复的路径
duplicates = {}
for key, handlers in routes.items():
    if len(handlers) > 1:
        duplicates[key] = handlers

if duplicates:
    print(f"\\n发现 {len(duplicates)} 个重复路由:")
    for route, handlers in list(duplicates.items())[:10]:
        print(f"  - {route}: {len(handlers)} 个处理器")
"""
    ], capture_output=True, text=True)

    print(result.stdout)

    if result.returncode != 0:
        print(f"⚠️  分析失败: {result.stderr[:200]}")

def clean_unused_code():
    """清理未使用的代码"""
    print_section("清理未使用代码")

    # 查找所有TODO和FIXME
    os.chdir(PROJECT_ROOT)
    result = os.popen('grep -r "TODO\\|FIXME" --include="*.py" backend/src 2>/dev/null | wc -l').read()
    todo_count = int(result.strip())

    print(f"📝 发现 {todo_count} 个 TODO/FIXME 标记")

    # 查找裸except
    result = os.popen('grep -r "except:" --include="*.py" backend/src 2>/dev/null | wc -l').read()
    except_count = int(result.strip())

    print(f"⚠️  发现 {except_count} 个裸 except（建议改进）")

def execute_cleanup(safe_to_delete, dry_run=True):
    """执行清理"""
    print_section("执行清理")

    if dry_run:
        print("🔍 DRY RUN 模式 - 仅显示将要删除的内容\n")

    deleted_size = 0
    for path in safe_to_delete:
        if os.path.exists(path):
            size = get_dir_size(path)
            if dry_run:
                print(f"将删除: {path} ({format_size(size)})")
            else:
                try:
                    shutil.rmtree(path)
                    deleted_size += size
                    print(f"✅ 已删除: {path} ({format_size(size)})")
                except Exception as e:
                    print(f"❌ 删除失败: {path} - {e}")

    if dry_run:
        print(f"\n预计释放空间: {format_size(sum(get_dir_size(p) for p in safe_to_delete if os.path.exists(p)))}")
    else:
        print(f"\n✅ 已释放空间: {format_size(deleted_size)}")

def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         FieldMind 系统验证和清理 - 阶段2-4                        ║
╚══════════════════════════════════════════════════════════════════╝
""")

    # 阶段2: 验证数据库
    if not verify_database():
        print("❌ 数据库验证失败，停止执行")
        return

    # 检查备份安全性
    safe_to_delete = check_backup_safety()

    # 分析API
    analyze_api_duplication()

    # 清理未使用代码
    clean_unused_code()

    # 执行清理（DRY RUN）
    execute_cleanup(safe_to_delete, dry_run=True)

    print("""
╔══════════════════════════════════════════════════════════════════╗
║  验证完成                                                         ║
╚══════════════════════════════════════════════════════════════════╝

下一步:
1. 如果确认无误，运行: python3 audit/complete_cleanup.py --execute
2. 这将真正删除备份文件并释放空间

⚠️  确保主程序运行正常后再执行清理！
    """)

if __name__ == "__main__":
    main()
