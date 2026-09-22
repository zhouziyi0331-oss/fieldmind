#!/usr/bin/env python3
"""
架构修复 #2: 派生文件注册系统

问题：
- 音频转录生成的transcript JSON散落在uploads/transcripts/
- OCR结果没有单独记录
- chunk、向量等派生数据没有统一管理
- 文件管理看不到处理产物

修复：
1. 创建document_artifacts表
2. 扫描现有派生文件并注册
3. 提供查询接口
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
import os
from datetime import datetime
import uuid

def create_document_artifacts_table():
    """创建派生文件表"""
    print("="*70)
    print("步骤1: 创建document_artifacts表")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查表是否已存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='document_artifacts'
    """)

    if cursor.fetchone():
        print("⚠️ document_artifacts表已存在")

        # 检查是否有数据
        cursor.execute("SELECT COUNT(*) FROM document_artifacts")
        count = cursor.fetchone()[0]
        print(f"   当前记录数: {count}")
        conn.close()
        return count

    # 创建新表
    cursor.execute("""
        CREATE TABLE document_artifacts (
            id VARCHAR(36) PRIMARY KEY,
            document_id VARCHAR(36) NOT NULL,
            artifact_type VARCHAR(50) NOT NULL,
            file_path VARCHAR(1000),
            file_size INTEGER,
            mime_type VARCHAR(100),
            metadata JSON,
            status VARCHAR(20) DEFAULT 'completed',
            created_at DATETIME NOT NULL,
            FOREIGN KEY(document_id) REFERENCES project_documents(id) ON DELETE CASCADE
        )
    """)

    # 创建索引
    cursor.execute("""
        CREATE INDEX ix_artifacts_document_id ON document_artifacts(document_id)
    """)

    cursor.execute("""
        CREATE INDEX ix_artifacts_type ON document_artifacts(artifact_type)
    """)

    conn.commit()
    conn.close()

    print("✅ document_artifacts表创建完成")
    print("   字段: id, document_id, artifact_type, file_path, metadata, status")
    return 0


def scan_and_register_transcripts():
    """扫描并注册transcript文件"""
    print("\n" + "="*70)
    print("步骤2: 扫描并注册transcript文件")
    print("="*70)

    transcript_dir = Path("uploads/transcripts")

    if not transcript_dir.exists():
        print(f"⚠️ transcript目录不存在: {transcript_dir}")
        return 0

    # 查找所有transcript JSON文件
    transcript_files = list(transcript_dir.glob("*.json"))
    print(f"\n找到 {len(transcript_files)} 个transcript文件")

    if len(transcript_files) == 0:
        return 0

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    registered = 0

    for transcript_file in transcript_files:
        # 从文件名提取document_id
        # 文件名格式: doc_<uuid>.json 或 transcript_<uuid>.json
        filename = transcript_file.stem

        # 尝试提取UUID
        if filename.startswith("doc_"):
            doc_id = filename[4:]
        elif filename.startswith("transcript_"):
            doc_id = filename[11:]
        else:
            doc_id = filename

        # 验证document是否存在
        cursor.execute("""
            SELECT id FROM project_documents WHERE id = ?
        """, (doc_id,))

        if not cursor.fetchone():
            print(f"  ⚠️ 文档不存在: {doc_id}")
            continue

        # 读取文件元数据
        file_size = transcript_file.stat().st_size

        # 检查是否已注册
        cursor.execute("""
            SELECT id FROM document_artifacts
            WHERE document_id = ? AND artifact_type = 'transcript'
        """, (doc_id,))

        if cursor.fetchone():
            continue  # 已注册，跳过

        # 注册artifact
        artifact_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO document_artifacts
            (id, document_id, artifact_type, file_path, file_size, mime_type, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            artifact_id,
            doc_id,
            'transcript',
            str(transcript_file),
            file_size,
            'application/json',
            'completed',
            datetime.utcnow()
        ))

        registered += 1
        print(f"  ✅ 注册transcript: {transcript_file.name}")

    conn.commit()
    conn.close()

    print(f"\n✅ 注册了 {registered} 个transcript文件")
    return registered


def register_chunk_artifacts():
    """为所有有chunks的文档注册chunk artifact"""
    print("\n" + "="*70)
    print("步骤3: 注册chunk artifacts")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 找出所有有chunks的文档
    cursor.execute("""
        SELECT DISTINCT document_id, COUNT(*) as chunk_count
        FROM document_chunks
        GROUP BY document_id
    """)

    docs_with_chunks = cursor.fetchall()
    print(f"\n找到 {len(docs_with_chunks)} 个有chunks的文档")

    registered = 0

    for doc_id, chunk_count in docs_with_chunks:
        # 检查是否已注册
        cursor.execute("""
            SELECT id FROM document_artifacts
            WHERE document_id = ? AND artifact_type = 'chunks'
        """, (doc_id,))

        if cursor.fetchone():
            continue

        # 注册chunk artifact
        artifact_id = str(uuid.uuid4())
        metadata = json.dumps({"chunk_count": chunk_count})

        cursor.execute("""
            INSERT INTO document_artifacts
            (id, document_id, artifact_type, metadata, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            artifact_id,
            doc_id,
            'chunks',
            metadata,
            'completed',
            datetime.utcnow()
        ))

        registered += 1

    conn.commit()
    conn.close()

    print(f"✅ 注册了 {registered} 个chunk artifacts")
    return registered


def generate_artifact_summary():
    """生成派生文件摘要"""
    print("\n" + "="*70)
    print("步骤4: 派生文件摘要")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 按类型统计
    cursor.execute("""
        SELECT artifact_type, COUNT(*) as count
        FROM document_artifacts
        GROUP BY artifact_type
    """)

    types = cursor.fetchall()

    print("\n按类型统计:")
    for artifact_type, count in types:
        print(f"  {artifact_type}: {count}个")

    # 总计
    cursor.execute("SELECT COUNT(*) FROM document_artifacts")
    total = cursor.fetchone()[0]

    # 关联的文档数
    cursor.execute("SELECT COUNT(DISTINCT document_id) FROM document_artifacts")
    doc_count = cursor.fetchone()[0]

    print(f"\n总派生文件: {total}个")
    print(f"关联文档: {doc_count}个")

    conn.close()


if __name__ == "__main__":
    print("="*70)
    print("架构修复 #2: 派生文件注册系统")
    print("="*70)

    existing_count = create_document_artifacts_table()

    if existing_count == 0:
        # 只在表刚创建时注册
        scan_and_register_transcripts()
        register_chunk_artifacts()

    generate_artifact_summary()

    print("\n" + "="*70)
    print("✅ 架构修复 #2 完成")
    print("="*70)

    print("\n修复文件: scripts/fix_arch_02_artifact_registry.py")
    print("验证命令: sqlite3 data/fieldmind.db 'SELECT artifact_type, COUNT(*) FROM document_artifacts GROUP BY artifact_type;'")
    print("预期输出: transcript, chunks等类型的统计")
