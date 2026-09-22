"""
Week 3 - Day 1-2: ChromaDB 同步服务
订阅 chunk 事件，自动同步到 ChromaDB
"""

import sqlite3
from typing import Dict, List, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class ChromaDBSyncService:
    """
    ChromaDB 同步服务

    功能：
    1. 订阅 chunk.created/updated/deleted 事件
    2. 同步数据到 ChromaDB
    3. 支持全量重建
    """
    def __init__(self, db_path: str,
                 collection_name: str = "chunks",
                 use_mock: bool = False, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化同步服务

        Args:
            db_path: SQLite 数据库路径
            collection_name: ChromaDB 集合名称
            use_mock: 是否使用模拟模式
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.use_mock = use_mock
        self.sync_stats = {
            "chunks_synced": 0,
            "chunks_deleted": 0,
            "errors": 0
        }

        if not use_mock:
            try:
                import chromadb
                self.client = chromadb.Client()
                self.collection = self.client.get_or_create_collection(collection_name)
                logger.info(f"已连接到 ChromaDB 集合: {collection_name}")
            except ImportError:
                logger.warning("chromadb 包未安装，使用模拟模式")
                self.use_mock = True
                self.client = None
                self.collection = None
        else:
            self.client = None
            self.collection = None
            logger.info("使用 ChromaDB 模拟模式")

    def register_event_handlers(self, event_bus):
        """注册事件处理器"""
        from app.core.event_bus import Event

        @event_bus.on("chunk.created")
        def on_chunk_created(event: Event):
            self.sync_chunk_create(event.data)

        @event_bus.on("chunk.updated")
        def on_chunk_updated(event: Event):
            self.sync_chunk_update(event.data)

        @event_bus.on("chunk.deleted")
        def on_chunk_deleted(event: Event):
            self.sync_chunk_delete(event.data)

        logger.info("已注册 ChromaDB 同步事件处理器")

    def sync_chunk_create(self, data: Dict) -> bool:
        """同步 chunk 创建事件"""
        try:
            chunk_id = data.get("chunk_id") or data.get("id")
            text = data.get("text", "")

            logger.info(f"同步 chunk 创建到 ChromaDB: {chunk_id}")

            # 生成 embedding（模拟）
            embedding = self._generate_embedding(text)

            # 准备元数据
            metadata = {
                "document_id": data.get("document_id", ""),
                "chunk_index": data.get("chunk_index", 0),
            }

            # 添加可选字段
            for key in ["speaker", "dimension_category", "emotion_polarity"]:
                if key in data:
                    metadata[key] = data[key]

            if self.use_mock:
                logger.debug(f"[MOCK] 添加 chunk: {chunk_id}, text_length={len(text)}")
            else:
                self.collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[metadata]
                )

            # 更新同步状态
            self._update_sync_status(chunk_id)

            self.sync_stats["chunks_synced"] += 1
            return True

        except Exception as e:
            logger.error(f"同步 chunk 创建失败: {e}")
            self.sync_stats["errors"] += 1
            return False

    def sync_chunk_update(self, data: Dict) -> bool:
        """同步 chunk 更新事件（删除旧的，添加新的）"""
        try:
            chunk_id = data.get("chunk_id") or data.get("id")
            logger.info(f"同步 chunk 更新到 ChromaDB: {chunk_id}")

            # 先删除
            self.sync_chunk_delete({"chunk_id": chunk_id})

            # 再创建
            self.sync_chunk_create(data)

            return True

        except Exception as e:
            logger.error(f"同步 chunk 更新失败: {e}")
            self.sync_stats["errors"] += 1
            return False

    def sync_chunk_delete(self, data: Dict) -> bool:
        """同步 chunk 删除事件"""
        try:
            chunk_id = data.get("chunk_id") or data.get("id")
            logger.info(f"同步 chunk 删除到 ChromaDB: {chunk_id}")

            if self.use_mock:
                logger.debug(f"[MOCK] 删除 chunk: {chunk_id}")
            else:
                try:
                    self.collection.delete(ids=[chunk_id])
                except:
                    # 如果不存在，忽略错误
                    pass

            self.sync_stats["chunks_deleted"] += 1
            return True

        except Exception as e:
            logger.error(f"同步 chunk 删除失败: {e}")
            self.sync_stats["errors"] += 1
            return False

    def _generate_embedding(self, text: str) -> List[float]:
        """
        生成文本的 embedding

        实际使用时应该调用真实的 embedding 模型
        这里用随机向量模拟
        """
        if self.use_mock:
            # 模拟：返回固定维度的随机向量
            return np.random.rand(384).tolist()
        else:
            # TODO: 集成真实的 embedding 模型
            # 例如: return openai.Embedding.create(input=text)["data"][0]["embedding"]
            return np.random.rand(384).tolist()

    def _update_sync_status(self, chunk_id: str):
        """更新 SQLite 中的同步状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 检查字段是否存在
            cursor.execute("PRAGMA table_info(document_chunks)")
            columns = [col[1] for col in cursor.fetchall()]

            if "synced_to_chromadb" in columns:
                cursor.execute("""
                    UPDATE document_chunks
                    SET synced_to_chromadb = 1,
                        chromadb_synced_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (chunk_id,))
                conn.commit()

            conn.close()

        except Exception as e:
            logger.debug(f"更新同步状态: {e}")

    def rebuild_from_postgres(self, batch_size: int = 100) -> Dict:
        """
        从 PostgreSQL/SQLite 完全重建 ChromaDB

        Args:
            batch_size: 批量处理大小

        Returns:
            重建统计信息
        """
        logger.info("开始从 SQLite 重建 ChromaDB...")

        stats = {
            "chunks_rebuilt": 0,
            "total_chunks": 0,
            "errors": []
        }

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 1. 清空 ChromaDB
            logger.info("步骤 1: 清空 ChromaDB")
            if not self.use_mock:
                try:
                    self.client.delete_collection(self.collection_name)
                    self.collection = self.client.create_collection(self.collection_name)
                except:
                    pass
            else:
                logger.debug("[MOCK] 清空集合")

            # 2. 查询所有 chunks
            logger.info("步骤 2: 查询所有 chunks")
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            stats["total_chunks"] = cursor.fetchone()[0]
            logger.info(f"找到 {stats['total_chunks']} 个 chunk")

            # 3. 批量处理
            offset = 0
            while True:
                cursor.execute("""
                    SELECT id, text, document_id, chunk_index
                    FROM document_chunks
                    ORDER BY created_at
                    LIMIT ? OFFSET ?
                """, (batch_size, offset))

                chunks = cursor.fetchall()
                if not chunks:
                    break

                logger.info(f"处理批次: {offset} - {offset + len(chunks)}")

                for chunk in chunks:
                    chunk_id, text, document_id, chunk_index = chunk

                    success = self.sync_chunk_create({
                        "chunk_id": chunk_id or str(chunk_id),
                        "id": chunk_id,
                        "text": text or "",
                        "document_id": document_id or "",
                        "chunk_index": chunk_index or 0
                    })

                    if success:
                        stats["chunks_rebuilt"] += 1

                offset += batch_size

            conn.close()

            logger.info(f"✅ ChromaDB 重建完成: {stats['chunks_rebuilt']}/{stats['total_chunks']} 个 chunk")

        except Exception as e:
            logger.error(f"重建失败: {e}")
            stats["errors"].append(str(e))

        return stats

    def search_similar(self, query_text: str, n_results: int = 10) -> List[Dict]:
        """
        搜索相似的 chunks

        Args:
            query_text: 查询文本
            n_results: 返回结果数量

        Returns:
            相似的 chunks 列表
        """
        if self.use_mock:
            logger.debug(f"[MOCK] 搜索相似: {query_text[:50]}...")
            return []

        query_embedding = self._generate_embedding(query_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return results

    def get_stats(self) -> Dict:
        """获取同步统计信息"""
        return self.sync_stats.copy()


# ===== 测试代码 =====

def test_chromadb_sync():
    """测试 ChromaDB 同步服务"""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from app.core.event_bus import get_event_bus

    print("=" * 60)
    print("测试 ChromaDB 同步服务")
    print("=" * 60)

    # 创建事件总线
    event_bus = get_event_bus()

    # 创建同步服务（模拟模式）
    db_path = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
    sync_service = ChromaDBSyncService(db_path, use_mock=True)

    # 注册事件处理器
    sync_service.register_event_handlers(event_bus)

    # 测试 chunk 创建
    print("\n测试 1: Chunk 创建事件")
    event_bus.publish("chunk.created", {
        "chunk_id": "chk_test123456",
        "text": "这是一个测试文本，用于验证 ChromaDB 同步功能。",
        "document_id": "doc_test123",
        "chunk_index": 0,
        "speaker": "测试者",
        "dimension_category": "测试"
    }, source="test")

    # 测试 chunk 更新
    print("\n测试 2: Chunk 更新事件")
    event_bus.publish("chunk.updated", {
        "chunk_id": "chk_test123456",
        "text": "这是更新后的文本。",
        "document_id": "doc_test123",
        "chunk_index": 0
    }, source="test")

    # 测试 chunk 删除
    print("\n测试 3: Chunk 删除事件")
    event_bus.publish("chunk.deleted", {
        "chunk_id": "chk_test123456"
    }, source="test")

    # 等待异步处理
    import time
    time.sleep(0.5)

    # 显示统计
    print("\n同步统计:")
    stats = sync_service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ ChromaDB 同步服务测试完成")


def test_rebuild():
    """测试完全重建"""
    print("\n" + "=" * 60)
    print("测试 ChromaDB 完全重建")
    print("=" * 60)

    db_path = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
    sync_service = ChromaDBSyncService(db_path, use_mock=True)

    # 执行重建（小批量测试）
    stats = sync_service.rebuild_from_postgres(batch_size=50)

    print("\n重建统计:")
    for key, value in stats.items():
        if key != "errors":
            print(f"  {key}: {value}")

    if stats["errors"]:
        print(f"  错误: {stats['errors']}")

    print("\n✅ 重建测试完成")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_chromadb_sync()
    test_rebuild()
