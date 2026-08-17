#!/usr/bin/env python3
"""
批量修复剩余的硬编码值
"""

import os
import re
from pathlib import Path

# 定义需要修复的文件和模式
FIXES = {
    "backend/src/health_check.py": [
        (r"sys\.path\.insert\(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend'\)",
         "BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nsys.path.insert(0, BASE_DIR)"),
    ],

    "backend/src/create_analytics_tables.py": [
        (r"sys\.path\.insert\(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend'\)",
         "BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nsys.path.insert(0, BASE_DIR)"),
    ],

    "backend/src/tests/test_all.py": [
        (r"sys\.path\.insert\(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend'\)",
         "BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nsys.path.insert(0, BASE_DIR)"),
    ],

    "backend/src/app/tasks/crawler_tasks.py": [
        (r'script_path = "/Users/alwan/FieldMind-Rebuild/repos/browser-use/run_crawl\.py"',
         'script_path = os.getenv("BROWSER_USE_SCRIPT", "./repos/browser-use/run_crawl.py")'),
    ],

    "backend/src/app/core/monitoring.py": [
        (r"logging\.FileHandler\('/Users/alwan/FieldMind-Rebuild/fieldmind-backend/logs/app\.log'\)",
         'logging.FileHandler(os.getenv("LOG_FILE", "./logs/app.log"))'),
    ],

    "backend/src/app/core/rag_engine.py": [
        (r'chroma_db_path = "/Users/alwan/FieldMind-Rebuild/chroma_db"',
         'chroma_db_path = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")'),
        (r"model_cache = os\.path\.expanduser\('~/\.cache/modelscope/models/AI-ModelScope--bge-small-zh-v1\.5/snapshots/master'\)",
         'model_cache = os.getenv("BGE_MODEL_PATH", os.path.expanduser("~/.cache/modelscope/models/AI-ModelScope--bge-small-zh-v1.5/snapshots/master"))'),
    ],

    "backend/src/fix_timestamp_pipeline.py": [
        (r"sys\.path\.insert\(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend'\)",
         "BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nsys.path.insert(0, BASE_DIR)"),
    ],

    "backend/src/test_timestamp_pipeline.py": [
        (r"sys\.path\.insert\(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend'\)",
         "BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nsys.path.insert(0, BASE_DIR)"),
    ],

    "backend/src/test_enhanced_chat.py": [
        (r"sys\.path\.insert\(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend'\)",
         "BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nsys.path.insert(0, BASE_DIR)"),
    ],
}


def fix_file(file_path: str, replacements: list):
    """修复单个文件"""
    full_path = Path("/Users/alwan/FieldMind") / file_path

    if not full_path.exists():
        print(f"⚠️  文件不存在: {file_path}")
        return False

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        modified = False

        for pattern, replacement in replacements:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
                print(f"  ✓ 替换: {pattern[:50]}...")

        if modified:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复完成: {file_path}")
            return True
        else:
            print(f"  - 无需修改: {file_path}")
            return False

    except Exception as e:
        print(f"❌ 修复失败 {file_path}: {e}")
        return False


def main():
    print("=" * 70)
    print("🔧 批量修复剩余硬编码值")
    print("=" * 70)

    fixed_count = 0
    total_count = len(FIXES)

    for file_path, replacements in FIXES.items():
        print(f"\n📝 处理: {file_path}")
        if fix_file(file_path, replacements):
            fixed_count += 1

    print("\n" + "=" * 70)
    print(f"✅ 完成: {fixed_count}/{total_count} 个文件已修复")
    print("=" * 70)


if __name__ == "__main__":
    main()
