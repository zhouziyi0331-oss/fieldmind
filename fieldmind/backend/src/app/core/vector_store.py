"""
向量数据库操作工具类
支持向量存储、检索和管理
"""

import os
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from pgvector.psycopg2 import register_vector


class VectorStore:
    """向量数据库操作类"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        database: str = None,
        user: str = None,
        password: str = None,
        min_conn: int = 1,
        max_conn: int = 10
    ):
        """初始化向量存储连接"""
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = database or os.getenv("POSTGRES_DB", "fieldmind_vectors")
        self.user = user or os.getenv("POSTGRES_USER", "fieldmind")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "fieldmind123")

        # 创建连接池
        try:
            self.pool = SimpleConnectionPool(
                min_conn,
                max_conn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )

            # 注册 pgvector 类型
            conn = self.pool.getconn()
            register_vector(conn)
            self.pool.putconn(conn)

        except Exception as e:
            raise ConnectionError(f"无法连接到 PostgreSQL: {e}")

    def _get_connection(self):
        """从连接池获取连接"""
        return self.pool.getconn()

    def _put_connection(self, conn):
        """归还连接到连接池"""
        self.pool.putconn(conn)

    def insert_vector(
        self,
        document_id: str,
        chunk_id: str,
        embedding: List[float],
        model_name: str = "text-embedding-ada-002"
    ) -> bool:
        """
        插入向量

        Args:
            document_id: 文档ID
            chunk_id: 文档块ID
            embedding: 向量（1536维）
            model_name: 模型名称

        Returns:
            bool: 是否成功
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 转换为 numpy 数组
            embedding_array = np.array(embedding, dtype=np.float32)

            cursor.execute(
                """
                INSERT INTO document_vectors (document_id, chunk_id, embedding, model_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (chunk_id)
                DO UPDATE SET
                    embedding = EXCLUDED.embedding,
                    model_name = EXCLUDED.model_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (document_id, chunk_id, embedding_array, model_name)
            )

            conn.commit()
            cursor.close()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"插入向量失败: {e}")
            return False

        finally:
            if conn:
                self._put_connection(conn)

    def batch_insert_vectors(
        self,
        vectors: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        批量插入向量

        Args:
            vectors: 向量列表，每项包含 document_id, chunk_id, embedding, model_name

        Returns:
            Tuple[int, int]: (成功数量, 失败数量)
        """
        conn = None
        success_count = 0
        fail_count = 0

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            for vec in vectors:
                try:
                    embedding_array = np.array(vec["embedding"], dtype=np.float32)

                    cursor.execute(
                        """
                        INSERT INTO document_vectors (document_id, chunk_id, embedding, model_name)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (chunk_id)
                        DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            model_name = EXCLUDED.model_name,
                            updated_at = CURRENT_TIMESTAMP
                        """,
                        (
                            vec["document_id"],
                            vec["chunk_id"],
                            embedding_array,
                            vec.get("model_name", "text-embedding-ada-002")
                        )
                    )
                    success_count += 1

                except Exception as e:
                    print(f"插入向量 {vec.get('chunk_id')} 失败: {e}")
                    fail_count += 1

            conn.commit()
            cursor.close()

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"批量插入失败: {e}")

        finally:
            if conn:
                self._put_connection(conn)

        return success_count, fail_count

    def search_similar_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_id: str = None,
        similarity_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        搜索相似向量

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            document_id: 可选，限制在特定文档内搜索
            similarity_threshold: 相似度阈值（余弦相似度，-1到1）

        Returns:
            List[Dict]: 相似向量列表，包含 chunk_id, document_id, similarity
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query_array = np.array(query_embedding, dtype=np.float32)

            # 构建查询
            if document_id:
                query = """
                    SELECT
                        chunk_id,
                        document_id,
                        model_name,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM document_vectors
                    WHERE document_id = %s
                        AND 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                params = (query_array, document_id, query_array, similarity_threshold, query_array, top_k)
            else:
                query = """
                    SELECT
                        chunk_id,
                        document_id,
                        model_name,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM document_vectors
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                params = (query_array, query_array, similarity_threshold, query_array, top_k)

            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            return [dict(row) for row in results]

        except Exception as e:
            print(f"搜索向量失败: {e}")
            return []

        finally:
            if conn:
                self._put_connection(conn)

    def delete_vector(self, chunk_id: str) -> bool:
        """
        删除指定向量

        Args:
            chunk_id: 文档块ID

        Returns:
            bool: 是否成功
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM document_vectors WHERE chunk_id = %s",
                (chunk_id,)
            )

            conn.commit()
            deleted = cursor.rowcount > 0
            cursor.close()
            return deleted

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"删除向量失败: {e}")
            return False

        finally:
            if conn:
                self._put_connection(conn)

    def delete_document_vectors(self, document_id: str) -> int:
        """
        删除文档的所有向量

        Args:
            document_id: 文档ID

        Returns:
            int: 删除的向量数量
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM document_vectors WHERE document_id = %s",
                (document_id,)
            )

            conn.commit()
            deleted_count = cursor.rowcount
            cursor.close()
            return deleted_count

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"删除文档向量失败: {e}")
            return 0

        finally:
            if conn:
                self._put_connection(conn)

    def get_vector_count(self, document_id: str = None) -> int:
        """
        获取向量数量

        Args:
            document_id: 可选，特定文档的向量数量

        Returns:
            int: 向量数量
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if document_id:
                cursor.execute(
                    "SELECT COUNT(*) FROM document_vectors WHERE document_id = %s",
                    (document_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM document_vectors")

            count = cursor.fetchone()[0]
            cursor.close()
            return count

        except Exception as e:
            print(f"获取向量数量失败: {e}")
            return 0

        finally:
            if conn:
                self._put_connection(conn)

    def vector_exists(self, chunk_id: str) -> bool:
        """
        检查向量是否存在

        Args:
            chunk_id: 文档块ID

        Returns:
            bool: 是否存在
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM document_vectors WHERE chunk_id = %s)",
                (chunk_id,)
            )

            exists = cursor.fetchone()[0]
            cursor.close()
            return exists

        except Exception as e:
            print(f"检查向量存在性失败: {e}")
            return False

        finally:
            if conn:
                self._put_connection(conn)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息

        Returns:
            Dict: 统计信息
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 总向量数
            cursor.execute("SELECT COUNT(*) as total_vectors FROM document_vectors")
            total = cursor.fetchone()["total_vectors"]

            # 文档数
            cursor.execute("SELECT COUNT(DISTINCT document_id) as total_documents FROM document_vectors")
            docs = cursor.fetchone()["total_documents"]

            # 模型分布
            cursor.execute(
                """
                SELECT model_name, COUNT(*) as count
                FROM document_vectors
                GROUP BY model_name
                """
            )
            models = [dict(row) for row in cursor.fetchall()]

            # 数据库大小
            cursor.execute(
                """
                SELECT pg_size_pretty(pg_total_relation_size('document_vectors')) as table_size
                """
            )
            size = cursor.fetchone()["table_size"]

            cursor.close()

            return {
                "total_vectors": total,
                "total_documents": docs,
                "models": models,
                "table_size": size
            }

        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return {}

        finally:
            if conn:
                self._put_connection(conn)

    def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool.closeall()


# 全局单例
_vector_store_instance = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
