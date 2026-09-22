#!/usr/bin/env python3
"""
创建全文搜索索引 - SQLite FTS5

功能：
1. 创建FTS5虚拟表
2. 同步现有chunks数据
3. 支持中文分词
4. 测试全文搜索功能
"""

import sys
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_fts_table(db_path: str = "data/fieldmind.db"):
    """
    创建FTS5全文搜索表

    Args:
        db_path: 数据库路径
    """
    logger.info(f"创建FTS5表: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查FTS表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='document_chunks_fts'
        """)

        if cursor.fetchone():
            logger.info("FTS5表已存在，删除旧表...")
            cursor.execute("DROP TABLE IF EXISTS document_chunks_fts")

        # 创建FTS5虚拟表
        # 使用unicode61分词器（支持中文）
        cursor.execute("""
            CREATE VIRTUAL TABLE document_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                text,
                document_id UNINDEXED,
                tokenize = 'unicode61 remove_diacritics 2'
            )
        """)

        conn.commit()
        logger.info("✅ FTS5表创建成功")

    except Exception as e:
        logger.error(f"❌ 创建FTS5表失败: {e}")
        conn.rollback()

    finally:
        conn.close()


def sync_data_to_fts(db_path: str = "data/fieldmind.db"):
    """
    同步数据到FTS表

    Args:
        db_path: 数据库路径
    """
    logger.info("同步数据到FTS表...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取chunks总数
        cursor.execute("SELECT COUNT(*) FROM document_chunks")
        total_chunks = cursor.fetchone()[0]

        logger.info(f"准备同步 {total_chunks} 个chunks")

        # 插入数据到FTS表
        cursor.execute("""
            INSERT INTO document_chunks_fts (chunk_id, text, document_id)
            SELECT id, text, document_id
            FROM document_chunks
            WHERE text IS NOT NULL AND LENGTH(text) > 0
        """)

        conn.commit()

        # 验证插入结果
        cursor.execute("SELECT COUNT(*) FROM document_chunks_fts")
        fts_count = cursor.fetchone()[0]

        logger.info(f"✅ 同步完成: {fts_count}/{total_chunks} 个chunks")

    except Exception as e:
        logger.error(f"❌ 同步数据失败: {e}")
        conn.rollback()

    finally:
        conn.close()


def test_full_text_search(db_path: str = "data/fieldmind.db"):
    """
    测试全文搜索功能

    Args:
        db_path: 数据库路径
    """
    logger.info("\n" + "="*60)
    logger.info("测试全文搜索")
    logger.info("="*60)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 测试查询
    test_queries = [
        "花鼓戏",
        "刺绣",
        "传承人",
        "苗族",
        "乡村文化"
    ]

    for query in test_queries:
        logger.info(f"\n查询: {query}")

        # FTS5查询语法
        cursor.execute("""
            SELECT
                chunk_id,
                snippet(document_chunks_fts, 1, '<mark>', '</mark>', '...', 30) as snippet,
                rank
            FROM document_chunks_fts
            WHERE document_chunks_fts MATCH ?
            ORDER BY rank
            LIMIT 3
        """, (query,))

        results = cursor.fetchall()

        if results:
            logger.info(f"  找到 {len(results)} 个结果:")
            for i, row in enumerate(results, 1):
                snippet = row['snippet']
                rank = row['rank']
                logger.info(f"    {i}. ID={row['chunk_id']}, Rank={rank:.4f}")
                logger.info(f"       {snippet}")
        else:
            logger.info(f"  未找到结果")

    conn.close()


def create_fts_triggers(db_path: str = "data/fieldmind.db"):
    """
    创建触发器，自动同步FTS表

    Args:
        db_path: 数据库路径
    """
    logger.info("\n创建FTS同步触发器...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 删除旧触发器
        cursor.execute("DROP TRIGGER IF EXISTS chunks_fts_insert")
        cursor.execute("DROP TRIGGER IF EXISTS chunks_fts_update")
        cursor.execute("DROP TRIGGER IF EXISTS chunks_fts_delete")

        # INSERT触发器
        cursor.execute("""
            CREATE TRIGGER chunks_fts_insert AFTER INSERT ON document_chunks
            BEGIN
                INSERT INTO document_chunks_fts (chunk_id, text, document_id)
                VALUES (NEW.id, NEW.text, NEW.document_id);
            END
        """)

        # UPDATE触发器
        cursor.execute("""
            CREATE TRIGGER chunks_fts_update AFTER UPDATE ON document_chunks
            BEGIN
                UPDATE document_chunks_fts
                SET text = NEW.text, document_id = NEW.document_id
                WHERE chunk_id = NEW.id;
            END
        """)

        # DELETE触发器
        cursor.execute("""
            CREATE TRIGGER chunks_fts_delete AFTER DELETE ON document_chunks
            BEGIN
                DELETE FROM document_chunks_fts WHERE chunk_id = OLD.id;
            END
        """)

        conn.commit()
        logger.info("✅ 触发器创建成功")

    except Exception as e:
        logger.error(f"❌ 创建触发器失败: {e}")
        conn.rollback()

    finally:
        conn.close()


def optimize_fts(db_path: str = "data/fieldmind.db"):
    """
    优化FTS索引

    Args:
        db_path: 数据库路径
    """
    logger.info("\n优化FTS索引...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 优化FTS表
        cursor.execute("INSERT INTO document_chunks_fts(document_chunks_fts) VALUES('optimize')")
        conn.commit()
        logger.info("✅ FTS索引优化完成")

    except Exception as e:
        logger.error(f"❌ 优化失败: {e}")
        conn.rollback()

    finally:
        conn.close()


def get_fts_stats(db_path: str = "data/fieldmind.db"):
    """
    获取FTS统计信息

    Args:
        db_path: 数据库路径
    """
    logger.info("\n" + "="*60)
    logger.info("FTS统计信息")
    logger.info("="*60)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 文档数量
        cursor.execute("SELECT COUNT(*) FROM document_chunks_fts")
        doc_count = cursor.fetchone()[0]

        logger.info(f"  索引文档数: {doc_count}")

        # 表大小
        cursor.execute("""
            SELECT
                SUM(pgsize) as size
            FROM dbstat
            WHERE name = 'document_chunks_fts'
        """)
        result = cursor.fetchone()
        if result and result[0]:
            size_kb = result[0] / 1024
            logger.info(f"  索引大小: {size_kb:.2f} KB")

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")

    finally:
        conn.close()


def main():
    """主流程"""
    logger.info("="*60)
    logger.info("SQLite FTS5 全文搜索设置")
    logger.info("="*60)

    db_path = "data/fieldmind.db"

    # 1. 创建FTS表
    create_fts_table(db_path)

    # 2. 同步数据
    sync_data_to_fts(db_path)

    # 3. 创建触发器
    create_fts_triggers(db_path)

    # 4. 优化索引
    optimize_fts(db_path)

    # 5. 获取统计信息
    get_fts_stats(db_path)

    # 6. 测试搜索
    test_full_text_search(db_path)

    logger.info("\n" + "="*60)
    logger.info("✅ FTS5设置完成")
    logger.info("="*60)


if __name__ == "__main__":
    main()
