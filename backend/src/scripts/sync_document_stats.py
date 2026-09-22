#!/usr/bin/env python3
"""
同步documents表的统计字段

修复问题：
- documents.chunk_count = 0
- documents.word_count = 0

解决方案：
从document_chunks表聚合真实数据并更新documents表
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def sync_document_stats():
    """同步documents表统计字段"""
    logger.info("="*60)
    logger.info("同步documents表统计字段")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取所有documents
    cursor.execute("SELECT id FROM documents")
    doc_ids = [row[0] for row in cursor.fetchall()]

    logger.info(f"\n找到 {len(doc_ids)} 个文档需要更新")

    updated_count = 0

    for doc_id in doc_ids:
        # 统计该文档的chunks数量和总字数
        cursor.execute("""
            SELECT
                COUNT(*) as chunk_count,
                COALESCE(SUM(word_count), 0) as total_words
            FROM document_chunks
            WHERE document_id = ?
        """, (doc_id,))

        row = cursor.fetchone()
        chunk_count, total_words = row

        # 更新documents表
        cursor.execute("""
            UPDATE documents
            SET chunk_count = ?,
                word_count = ?
            WHERE id = ?
        """, (chunk_count, total_words, doc_id))

        if chunk_count > 0:
            logger.info(f"  更新文档 {doc_id[:8]}... : {chunk_count}个chunks, {total_words}字")
            updated_count += 1

    conn.commit()
    conn.close()

    logger.info(f"\n✅ 已更新 {updated_count} 个文档的统计字段")


def verify_sync():
    """验证同步结果"""
    logger.info("\n" + "="*60)
    logger.info("验证同步结果")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查是否还有未同步的
    cursor.execute("""
        SELECT COUNT(*) FROM documents
        WHERE chunk_count = 0 AND id IN (
            SELECT DISTINCT document_id FROM document_chunks
        )
    """)

    not_synced = cursor.fetchone()[0]

    if not_synced > 0:
        logger.error(f"❌ 仍有 {not_synced} 个文档未同步")
    else:
        logger.info("✅ 所有文档已同步")

    # 显示前3个文档的统计
    cursor.execute("""
        SELECT filename, chunk_count, word_count
        FROM documents
        WHERE chunk_count > 0
        LIMIT 3
    """)

    logger.info("\n前3个文档统计:")
    for row in cursor.fetchall():
        filename, chunk_count, word_count = row
        logger.info(f"  {filename}: {chunk_count}个chunks, {word_count}字")

    conn.close()


if __name__ == "__main__":
    sync_document_stats()
    verify_sync()

    logger.info("\n" + "="*60)
    logger.info("✅ 同步完成")
    logger.info("="*60)
