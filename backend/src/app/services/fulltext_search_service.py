#!/usr/bin/env python3
"""
全文搜索服务 - 封装SQLite FTS5功能

功能：
1. 初始化FTS5表（使用porter分词器）
2. 全文搜索
3. 高亮显示
4. 混合搜索（结合向量搜索）
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional

from app.core.database import get_sqlite_database_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FullTextSearchService:
    """全文搜索服务"""
    def __init__(self, db_path: Optional[str] = None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化全文搜索服务

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or get_sqlite_database_path()
        self._ensure_fts_table()

    def _ensure_fts_table(self):
        """确保FTS表存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 检查FTS表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='chunks_fts_simple'
            """)

            if not cursor.fetchone():
                logger.info("创建简单FTS表...")

                # 创建简单的FTS5表
                cursor.execute("""
                    CREATE VIRTUAL TABLE chunks_fts_simple USING fts5(
                        chunk_id UNINDEXED,
                        text,
                        content='document_chunks',
                        content_rowid='id'
                    )
                """)

                # 同步数据
                cursor.execute("""
                    INSERT INTO chunks_fts_simple(chunk_id, text)
                    SELECT id, text FROM document_chunks
                """)

                conn.commit()
                logger.info("✅ FTS表创建并同步完成")

        except Exception as e:
            logger.error(f"❌ 确保FTS表失败: {e}")
            conn.rollback()

        finally:
            conn.close()

    def search(
        self,
        query: str,
        limit: int = 10,
        highlight: bool = True
    ) -> List[Dict[str, Any]]:
        """
        全文搜索

        Args:
            query: 搜索查询
            limit: 结果数量
            highlight: 是否高亮显示

        Returns:
            搜索结果列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = []

        try:
            if highlight:
                # 带高亮的搜索
                cursor.execute("""
                    SELECT
                        fts.chunk_id,
                        snippet(chunks_fts_simple, 1, '【', '】', '...', 40) as snippet,
                        rank
                    FROM chunks_fts_simple fts
                    WHERE fts.text MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))
            else:
                # 不带高亮的搜索
                cursor.execute("""
                    SELECT
                        fts.chunk_id,
                        dc.text,
                        rank
                    FROM chunks_fts_simple fts
                    JOIN document_chunks dc ON fts.chunk_id = dc.id
                    WHERE fts.text MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit))

            for row in cursor.fetchall():
                results.append({
                    'chunk_id': row['chunk_id'],
                    'text': row.get('snippet') or row.get('text'),
                    'rank': row['rank']
                })

            logger.info(f"✅ 全文搜索完成: {query}, 找到 {len(results)} 个结果")

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")

        finally:
            conn.close()

        return results

    def search_with_metadata(
        self,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        全文搜索（包含完整元数据）

        Args:
            query: 搜索查询
            limit: 结果数量

        Returns:
            包含元数据的搜索结果
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        results = []

        try:
            cursor.execute("""
                SELECT
                    dc.id,
                    dc.text,
                    dc.chunk_index,
                    dc.document_id,
                    snippet(chunks_fts_simple, 1, '【', '】', '...', 40) as snippet,
                    fts.rank
                FROM chunks_fts_simple fts
                JOIN document_chunks dc ON fts.chunk_id = dc.id
                WHERE fts.text MATCH ?
                ORDER BY fts.rank
                LIMIT ?
            """, (query, limit))

            for row in cursor.fetchall():
                results.append({
                    'chunk_id': row['id'],
                    'text': row['text'],
                    'snippet': row['snippet'],
                    'chunk_index': row['chunk_index'],
                    'document_id': row['document_id'],
                    'rank': row['rank']
                })

            logger.info(f"✅ 搜索完成（含元数据）: {len(results)} 个结果")

        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")

        finally:
            conn.close()

        return results

    def count_matches(self, query: str) -> int:
        """
        统计匹配数量

        Args:
            query: 搜索查询

        Returns:
            匹配数量
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM chunks_fts_simple
                WHERE text MATCH ?
            """, (query,))

            count = cursor.fetchone()[0]
            return count

        except Exception as e:
            logger.error(f"❌ 统计失败: {e}")
            return 0

        finally:
            conn.close()


def create_fulltext_search_service(db_path: Optional[str] = None) -> FullTextSearchService:
    """工厂方法：创建全文搜索服务"""
    return FullTextSearchService(db_path)
