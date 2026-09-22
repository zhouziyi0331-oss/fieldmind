#!/usr/bin/env python3
"""检查每个步骤的产出边界是否清晰"""

import sqlite3
import os

def find_db():
    db_paths = [
        os.path.expanduser("~/Library/Application Support/FieldMind/fieldmind.db"),
        "./user_data/fieldmind.db",
        "./fieldmind.db",
    ]
    for p in db_paths:
        if os.path.exists(p):
            return p
    return None

def check_chunk_boundaries(cursor):
    """检查 chunk 的边界是否合规"""
    issues = []

    try:
        # 检查content长度
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE length(content) < 100 OR length(content) > 2000")
        out_of_range = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total = cursor.fetchone()[0]

        if total > 0:
            pct = out_of_range / total * 100
            if pct > 20:
                issues.append(f"❌ {out_of_range}/{total} ({pct:.0f}%) 的 chunk 长度不在 100-2000 范围内")
            elif pct > 5:
                issues.append(f"⚠️ {out_of_range}/{total} ({pct:.0f}%) 的 chunk 长度异常")
    except Exception as e:
        issues.append(f"检查chunk长度失败: {e}")

    return issues

def check_file_status(cursor):
    """检查文件处理状态"""
    issues = []

    try:
        cursor.execute("SELECT status, COUNT(*) FROM project_documents GROUP BY status")
        statuses = cursor.fetchall()

        print("\n📌 文件处理状态：")
        for status, count in statuses:
            print(f"   {status}: {count} 个")

        # 检查是否有卡住的文件
        cursor.execute("""
            SELECT COUNT(*) FROM project_documents
            WHERE status = 'processing'
            AND created_at < datetime('now', '-1 hour')
        """)
        stuck = cursor.fetchone()[0]
        if stuck > 0:
            issues.append(f"❌ {stuck} 个文件卡在 processing 超过 1 小时")
    except Exception as e:
        issues.append(f"检查文件状态失败: {e}")

    return issues

def main():
    db_path = find_db()
    if not db_path:
        print("❌ 找不到数据库")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 检查边界合规性...\n")
    print("=" * 60)

    print("\n📌 Chunk 边界检查：")
    chunk_issues = check_chunk_boundaries(cursor)
    if chunk_issues:
        for issue in chunk_issues:
            print(f"   {issue}")
    else:
        print("   ✅ Chunk边界正常")

    file_issues = check_file_status(cursor)
    if file_issues:
        for issue in file_issues:
            print(f"   {issue}")

    # 检查embedding维度
    try:
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE embedding IS NOT NULL")
        embedded = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chunks")
        total = cursor.fetchone()[0]

        if total > 0:
            print(f"\n📌 向量化进度：")
            print(f"   {embedded}/{total} ({embedded/total*100:.1f}%) 已向量化")
    except:
        pass

    conn.close()

if __name__ == "__main__":
    main()
