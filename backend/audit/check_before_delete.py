#!/usr/bin/env python3
"""
完整性验证脚本 - 在删除任何东西之前，确保所有功能都已迁移到主程序
"""
import os
import sqlite3
from pathlib import Path
import json

# 主程序路径
MAIN_PROGRAM = "/Users/alwan/FieldMind"

# 需要检查的备份路径
BACKUP_PATHS = [
    "/Users/alwan/Desktop/FieldMind_Apps",
    "/Users/alwan/.fieldmind",
    "/Users/alwan/Library/Application Support/FieldMind",
]

def find_all_python_files(directory):
    """找出所有Python文件"""
    py_files = []
    for root, dirs, files in os.walk(directory):
        # 跳过虚拟环境
        if 'venv' in root or 'node_modules' in root or '.git' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))
    return py_files

def extract_functions_and_classes(file_path):
    """提取文件中的函数和类定义"""
    import ast
    functions = []
    classes = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
    except:
        pass

    return functions, classes

def check_database_schemas(db_path):
    """检查数据库的所有表和字段"""
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    schemas = {}
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schemas[table_name] = [col[1] for col in columns]

    conn.close()
    return schemas

def compare_directories(main_dir, backup_dir):
    """对比主程序和备份的差异"""
    print(f"\n{'='*80}")
    print(f"对比: {backup_dir}")
    print(f"{'='*80}")

    if not os.path.exists(backup_dir):
        print(f"❌ 目录不存在")
        return {"safe_to_delete": False, "reason": "目录不存在"}

    # 1. 对比Python文件
    main_py_files = find_all_python_files(main_dir)
    backup_py_files = find_all_python_files(backup_dir)

    print(f"\n📄 Python文件对比:")
    print(f"   主程序: {len(main_py_files)} 个")
    print(f"   备份: {len(backup_py_files)} 个")

    # 提取备份中的所有函数和类
    backup_functions = set()
    backup_classes = set()

    for f in backup_py_files:
        funcs, classes = extract_functions_and_classes(f)
        backup_functions.update(funcs)
        backup_classes.update(classes)

    # 提取主程序中的所有函数和类
    main_functions = set()
    main_classes = set()

    for f in main_py_files:
        funcs, classes = extract_functions_and_classes(f)
        main_functions.update(funcs)
        main_classes.update(classes)

    # 找出备份中有但主程序没有的
    missing_functions = backup_functions - main_functions
    missing_classes = backup_classes - main_classes

    if missing_functions:
        print(f"\n⚠️  备份中有 {len(missing_functions)} 个函数在主程序中找不到:")
        for func in list(missing_functions)[:10]:
            print(f"      - {func}")
        if len(missing_functions) > 10:
            print(f"      ... 还有 {len(missing_functions) - 10} 个")

    if missing_classes:
        print(f"\n⚠️  备份中有 {len(missing_classes)} 个类在主程序中找不到:")
        for cls in list(missing_classes)[:10]:
            print(f"      - {cls}")
        if len(missing_classes) > 10:
            print(f"      ... 还有 {len(missing_classes) - 10} 个")

    # 2. 对比数据库
    main_db = os.path.join(main_dir, "backend/fieldmind.db")
    backup_db_paths = [
        os.path.join(backup_dir, "fieldmind.db"),
        os.path.join(backup_dir, "user_data/fieldmind.db"),
    ]

    backup_db = None
    for path in backup_db_paths:
        if os.path.exists(path):
            backup_db = path
            break

    if backup_db:
        print(f"\n📊 数据库对比:")
        main_schema = check_database_schemas(main_db)
        backup_schema = check_database_schemas(backup_db)

        print(f"   主程序表: {len(main_schema)}")
        print(f"   备份表: {len(backup_schema)}")

        missing_tables = set(backup_schema.keys()) - set(main_schema.keys())
        if missing_tables:
            print(f"\n⚠️  备份中有 {len(missing_tables)} 张表在主程序中找不到:")
            for table in missing_tables:
                print(f"      - {table}")

        # 检查表中是否有数据
        if backup_db:
            conn = sqlite3.connect(backup_db)
            cursor = conn.cursor()
            has_data = False

            for table in backup_schema.keys():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"   ⚠️  {table}: {count} 条数据")
                        has_data = True
                except:
                    pass

            conn.close()

            if has_data:
                print(f"\n❌ 备份数据库中有数据，需要先迁移！")
                return {"safe_to_delete": False, "reason": "数据库中有数据"}

    # 3. 检查配置文件
    config_files = ['.env', 'config.json', 'settings.json']
    for config in config_files:
        backup_config = os.path.join(backup_dir, config)
        if os.path.exists(backup_config):
            main_config = os.path.join(main_dir, config)
            if not os.path.exists(main_config):
                print(f"\n⚠️  配置文件 {config} 在备份中存在但主程序中不存在")
                return {"safe_to_delete": False, "reason": f"缺少配置文件 {config}"}

    # 判断是否可以删除
    safe_to_delete = (not missing_functions or len(missing_functions) < 5) and \
                     (not missing_classes or len(missing_classes) < 3) and \
                     not missing_tables

    if safe_to_delete:
        print(f"\n✅ 此备份可以安全删除")
    else:
        print(f"\n❌ 此备份不能删除，需要先迁移功能")

    return {
        "safe_to_delete": safe_to_delete,
        "missing_functions": len(missing_functions),
        "missing_classes": len(missing_classes),
        "missing_tables": len(missing_tables) if missing_tables else 0
    }

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         FieldMind 完整性验证 - 删除前检查                 ║")
    print("╚══════════════════════════════════════════════════════════╝")

    print(f"\n主程序路径: {MAIN_PROGRAM}")

    if not os.path.exists(MAIN_PROGRAM):
        print(f"❌ 主程序路径不存在！")
        return

    # 检查主程序是否有必要的文件
    essential_files = [
        "backend/src/app/main.py",
        "backend/requirements.txt",
    ]

    print(f"\n检查主程序基本文件:")
    for f in essential_files:
        path = os.path.join(MAIN_PROGRAM, f)
        if os.path.exists(path):
            print(f"   ✅ {f}")
        else:
            print(f"   ❌ {f} 不存在！")

    # 对比每个备份
    results = {}
    for backup_path in BACKUP_PATHS:
        result = compare_directories(MAIN_PROGRAM, backup_path)
        results[backup_path] = result

    # 总结
    print(f"\n\n{'='*80}")
    print("📊 删除安全性总结")
    print(f"{'='*80}")

    for path, result in results.items():
        if result.get("safe_to_delete"):
            print(f"\n✅ {path}")
            print(f"   可以安全删除")
        else:
            print(f"\n❌ {path}")
            print(f"   不能删除: {result.get('reason', '有未迁移的功能')}")
            if result.get('missing_functions', 0) > 0:
                print(f"   - 缺少 {result['missing_functions']} 个函数")
            if result.get('missing_classes', 0) > 0:
                print(f"   - 缺少 {result['missing_classes']} 个类")
            if result.get('missing_tables', 0) > 0:
                print(f"   - 缺少 {result['missing_tables']} 张表")

    print(f"\n{'='*80}")
    print("⚠️  建议: 先完成功能迁移，再删除备份")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
