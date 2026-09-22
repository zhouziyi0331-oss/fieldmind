#!/usr/bin/env python3
"""
修复时间戳传递链路的核心问题
问题1: fact_statements重复插入
问题2: 清理无时间戳的旧记录
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:////Users/alwan/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def fix_duplicate_fact_statements():
    """清理重复的fact_statements，保留有时间戳的版本"""

    session = Session()

    print("=" * 60)
    print("修复fact_statements重复问题")
    print("=" * 60)

    # 1. 找出有重复记录的文档
    duplicates = session.execute(text("""
        SELECT document_id, clean_text, COUNT(*) as cnt
        FROM fact_statements
        GROUP BY document_id, clean_text
        HAVING cnt > 1
    """)).fetchall()

    print(f"\n找到 {len(duplicates)} 组重复记录")

    deleted_count = 0

    for doc_id, clean_text, cnt in duplicates:
        # 获取这组重复记录
        records = session.execute(text("""
            SELECT id, start_sec, end_sec, created_at
            FROM fact_statements
            WHERE document_id = :doc_id AND clean_text = :text
            ORDER BY
                CASE WHEN start_sec IS NOT NULL THEN 0 ELSE 1 END,
                created_at DESC
        """), {"doc_id": doc_id, "text": clean_text}).fetchall()

        # 保留第一条（有时间戳或最新的），删除其他
        keep_id = records[0][0]
        delete_ids = [r[0] for r in records[1:]]

        if delete_ids:
            print(f"  Doc {doc_id}: 保留ID={keep_id}, 删除{len(delete_ids)}条重复")
            for del_id in delete_ids:
                session.execute(text("DELETE FROM fact_statements WHERE id = :id"), {"id": del_id})
                deleted_count += 1

    session.commit()
    print(f"\n✅ 共删除 {deleted_count} 条重复记录")

    # 2. 统计修复后的覆盖率
    stats = session.execute(text("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN start_sec IS NOT NULL THEN 1 ELSE 0 END) as with_ts,
            ROUND(AVG(CASE WHEN start_sec IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100, 2) as coverage
        FROM fact_statements
    """)).fetchone()

    print(f"\n修复后时间戳覆盖率: {stats[1]}/{stats[0]} ({stats[2]}%)")

    session.close()

def add_unique_constraint():
    """为fact_statements添加唯一约束，防止未来重复插入"""

    session = Session()

    print("\n" + "=" * 60)
    print("添加唯一约束防止重复")
    print("=" * 60)

    # SQLite不支持ALTER TABLE ADD CONSTRAINT，需要检查是否已有索引
    try:
        # 创建唯一索引
        session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_statements_unique
            ON fact_statements(document_id, clean_text, chunk_index)
        """))
        session.commit()
        print("✅ 已创建唯一索引: idx_fact_statements_unique")
        print("   防止同一文档的同一chunk_index重复插入")
    except Exception as e:
        print(f"⚠️  创建索引失败: {e}")
        session.rollback()

    session.close()

def verify_fix():
    """验证修复效果"""

    session = Session()

    print("\n" + "=" * 60)
    print("验证修复效果")
    print("=" * 60)

    # 检查doc_47
    result = session.execute(text("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN start_sec IS NOT NULL THEN 1 ELSE 0 END) as with_ts
        FROM fact_statements
        WHERE document_id = 47
    """)).fetchone()

    coverage = (result[1] / result[0] * 100) if result[0] > 0 else 0
    print(f"\nDoc 47 (最新测试文档):")
    print(f"  总记录: {result[0]}")
    print(f"  有时间戳: {result[1]}")
    print(f"  覆盖率: {coverage:.1f}%")

    if coverage >= 90:
        print("  ✅ 修复成功！")
    else:
        print("  ⚠️  仍存在问题，需要进一步调查")

    # 全局统计
    global_stats = session.execute(text("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN start_sec IS NOT NULL THEN 1 ELSE 0 END) as with_ts,
            ROUND(AVG(CASE WHEN start_sec IS NOT NULL THEN 1.0 ELSE 0.0 END) * 100, 2) as coverage
        FROM fact_statements
    """)).fetchone()

    print(f"\n全局统计:")
    print(f"  总记录: {global_stats[0]}")
    print(f"  有时间戳: {global_stats[1]} ({global_stats[2]}%)")

    session.close()

if __name__ == '__main__':
    print("开始修复时间戳传递链路...\n")

    # 步骤1: 清理重复记录
    fix_duplicate_fact_statements()

    # 步骤2: 添加唯一约束
    add_unique_constraint()

    # 步骤3: 验证修复效果
    verify_fix()

    print("\n" + "=" * 60)
    print("修复完成！")
    print("=" * 60)
