#!/usr/bin/env python3
"""
架构修复 #3: 处理链路统一化

问题：
- 30个文档的处理结果存在extra_data JSON字段
- 关键词、实体等数据混在JSON中，无法高效查询
- 数据结构不规范

修复：
1. 创建document_processing_results表
2. 从extra_data提取关键词到独立表
3. 保持向后兼容
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
import uuid
from datetime import datetime

def create_processing_results_table():
    """创建处理结果表"""
    print("="*70)
    print("步骤1: 创建document_processing_results表")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查表是否已存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='document_processing_results'
    """)

    if cursor.fetchone():
        print("⚠️ document_processing_results表已存在")
        cursor.execute("SELECT COUNT(*) FROM document_processing_results")
        count = cursor.fetchone()[0]
        print(f"   当前记录数: {count}")
        conn.close()
        return count

    # 创建新表
    cursor.execute("""
        CREATE TABLE document_processing_results (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            processing_type VARCHAR(50) NOT NULL,
            result_data JSON,
            status VARCHAR(20) DEFAULT 'completed',
            created_at DATETIME NOT NULL,
            FOREIGN KEY(document_id) REFERENCES project_documents(id) ON DELETE CASCADE
        )
    """)

    # 创建索引
    cursor.execute("""
        CREATE INDEX ix_processing_document_id ON document_processing_results(document_id)
    """)

    cursor.execute("""
        CREATE INDEX ix_processing_type ON document_processing_results(processing_type)
    """)

    conn.commit()
    conn.close()

    print("✅ document_processing_results表创建完成")
    return 0


def migrate_keywords_from_extra_data():
    """从extra_data迁移关键词"""
    print("\n" + "="*70)
    print("步骤2: 迁移关键词数据")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取所有有extra_data的文档
    cursor.execute("""
        SELECT id, extra_data
        FROM project_documents
        WHERE extra_data IS NOT NULL
          AND extra_data != '{}'
          AND extra_data != 'null'
    """)

    docs = cursor.fetchall()
    print(f"\n找到 {len(docs)} 个有extra_data的文档")

    migrated = 0

    for doc_id, extra_data_str in docs:
        try:
            extra_data = json.loads(extra_data_str)
        except:
            print(f"  ⚠️ 文档 {doc_id} 的extra_data解析失败")
            continue

        # 提取关键词
        keywords = extra_data.get('keywords', [])

        if not keywords:
            continue

        # 检查是否已迁移
        cursor.execute("""
            SELECT id FROM document_processing_results
            WHERE document_id = ? AND processing_type = 'keywords'
        """, (doc_id,))

        if cursor.fetchone():
            continue  # 已迁移

        # 插入处理结果
        result_id = str(uuid.uuid4())
        result_data = json.dumps({'keywords': keywords}, ensure_ascii=False)

        cursor.execute("""
            INSERT INTO document_processing_results
            (id, document_id, processing_type, result_data, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            result_id,
            doc_id,
            'keywords',
            result_data,
            'completed',
            datetime.utcnow()
        ))

        migrated += 1
        print(f"  ✅ 迁移文档 {doc_id} 的 {len(keywords)} 个关键词")

    conn.commit()
    conn.close()

    print(f"\n✅ 迁移了 {migrated} 个文档的关键词")
    return migrated


def verify_data_consistency():
    """验证数据一致性"""
    print("\n" + "="*70)
    print("步骤3: 验证数据一致性")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查迁移后的数据
    cursor.execute("""
        SELECT COUNT(*) FROM document_processing_results
        WHERE processing_type = 'keywords'
    """)
    keyword_results = cursor.fetchone()[0]

    # 检查原始extra_data中有keywords的数量
    cursor.execute("""
        SELECT COUNT(*) FROM project_documents
        WHERE extra_data LIKE '%keywords%'
    """)
    original_keywords = cursor.fetchone()[0]

    print(f"\n原始有关键词的文档: {original_keywords}")
    print(f"已迁移到processing_results: {keyword_results}")

    if keyword_results == original_keywords:
        print("✅ 数据迁移完整")
    else:
        print(f"⚠️ 数据不完全一致")

    # 抽样验证
    cursor.execute("""
        SELECT pd.id, pd.filename, dpr.result_data
        FROM project_documents pd
        JOIN document_processing_results dpr ON pd.id = dpr.document_id
        WHERE dpr.processing_type = 'keywords'
        LIMIT 2
    """)

    samples = cursor.fetchall()

    print("\n数据样本:")
    for doc_id, filename, result_data in samples:
        data = json.loads(result_data)
        keyword_count = len(data.get('keywords', []))
        print(f"  {filename}: {keyword_count}个关键词")

    conn.close()


def generate_processing_summary():
    """生成处理结果摘要"""
    print("\n" + "="*70)
    print("步骤4: 处理结果摘要")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 按类型统计
    cursor.execute("""
        SELECT processing_type, COUNT(*) as count
        FROM document_processing_results
        GROUP BY processing_type
    """)

    types = cursor.fetchall()

    print("\n按类型统计:")
    for processing_type, count in types:
        print(f"  {processing_type}: {count}个文档")

    # 总计
    cursor.execute("SELECT COUNT(*) FROM document_processing_results")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT document_id) FROM document_processing_results")
    doc_count = cursor.fetchone()[0]

    print(f"\n总处理结果: {total}条")
    print(f"关联文档: {doc_count}个")

    conn.close()


if __name__ == "__main__":
    print("="*70)
    print("架构修复 #3: 处理链路统一化")
    print("="*70)

    existing_count = create_processing_results_table()

    if existing_count == 0:
        migrate_keywords_from_extra_data()

    verify_data_consistency()
    generate_processing_summary()

    print("\n" + "="*70)
    print("✅ 架构修复 #3 完成")
    print("="*70)

    print("\n修复文件: scripts/fix_arch_03_unified_processing.py")
    print("验证命令: sqlite3 data/fieldmind.db 'SELECT processing_type, COUNT(*) FROM document_processing_results GROUP BY processing_type;'")
    print("预期输出: keywords等类型的统计")
