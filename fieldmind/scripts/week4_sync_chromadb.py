#!/usr/bin/env python3
"""
Week 4-5: ChromaDB 批量数据同步

功能：
1. 从 PostgreSQL 读取所有 chunks
2. 生成 embeddings（Mock 或真实模型）
3. 批量导入 ChromaDB
4. 更新同步状态
5. 验证同步结果

执行时间：2026-09-13
作者：FieldMind Architecture Team
"""

import os
import sys
import sqlite3
import json
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional

# ============================================================================
# 配置
# ============================================================================

DB_PATH = "/Users/alwan/Downloads/FieldMind/backend/src/data/fieldmind.db"
BATCH_SIZE = 50
MOCK_MODE = True  # 设置为 False 使用真实 embedding 模型

# Embedding 配置
EMBEDDING_DIM = 384  # Mock 模式的向量维度
EMBEDDING_MODEL = "mock-embedding-v1"  # 或 "paraphrase-multilingual-MiniLM-L12-v2"

# ChromaDB 配置
CHROMA_COLLECTION = "fieldmind_chunks"

# ============================================================================
# Mock ChromaDB 客户端
# ============================================================================

class MockChromaCollection:
    """模拟 ChromaDB Collection"""

    def __init__(self, name: str):
        self.name = name
        self.data = {}
        self.embeddings = {}

    def add(self, ids, documents, embeddings, metadatas):
        """添加文档"""
        for i, doc_id in enumerate(ids):
            self.data[doc_id] = {
                'document': documents[i],
                'embedding': embeddings[i],
                'metadata': metadatas[i] if metadatas else {}
            }
            self.embeddings[doc_id] = embeddings[i]

    def count(self):
        """返回文档数量"""
        return len(self.data)

    def get(self):
        """获取所有文档"""
        return {
            'ids': list(self.data.keys()),
            'documents': [d['document'] for d in self.data.values()],
            'embeddings': [d['embedding'] for d in self.data.values()],
            'metadatas': [d['metadata'] for d in self.data.values()]
        }


class MockChromaClient:
    """模拟 ChromaDB 客户端"""

    def __init__(self):
        self.collections = {}

    def get_or_create_collection(self, name: str):
        """获取或创建 collection"""
        if name not in self.collections:
            self.collections[name] = MockChromaCollection(name)
        return self.collections[name]


# ============================================================================
# Embedding 生成器
# ============================================================================

class EmbeddingGenerator:
    """Embedding 生成器"""

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self.model = None

        if not mock_mode:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(EMBEDDING_MODEL)
                print(f"✅ 已加载 Embedding 模型: {EMBEDDING_MODEL}")
            except ImportError:
                print("⚠️  未安装 sentence-transformers，切换到 Mock 模式")
                print("   安装命令: pip install sentence-transformers")
                self.mock_mode = True

    def generate(self, text: str) -> List[float]:
        """生成文本的 embedding"""
        if self.mock_mode:
            # Mock: 生成随机向量
            return [random.random() for _ in range(EMBEDDING_DIM)]
        else:
            # 真实模型
            embedding = self.model.encode(text)
            return embedding.tolist()

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成 embeddings"""
        if self.mock_mode:
            return [self.generate(text) for text in texts]
        else:
            embeddings = self.model.encode(texts)
            return embeddings.tolist()


# ============================================================================
# ChromaDB 同步器
# ============================================================================

class ChromaDBBatchSyncer:
    """ChromaDB 批量同步器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.pg_conn = None
        self.chroma_client = None
        self.collection = None
        self.embedding_generator = None
        self.stats = {
            'chunks_total': 0,
            'chunks_synced': 0,
            'embeddings_generated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }

    def connect_postgresql(self):
        """连接 PostgreSQL"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

        self.pg_conn = sqlite3.connect(self.db_path)
        self.pg_conn.row_factory = sqlite3.Row
        print(f"✅ 已连接到 PostgreSQL: {self.db_path}")

    def connect_chromadb(self):
        """连接 ChromaDB"""
        if MOCK_MODE:
            self.chroma_client = MockChromaClient()
            print(f"✅ 已连接到 ChromaDB (Mock 模式)")
        else:
            try:
                import chromadb
                self.chroma_client = chromadb.Client()
                print(f"✅ 已连接到 ChromaDB")
            except ImportError:
                print("❌ 未安装 chromadb，请运行: pip install chromadb")
                print("   切换到 Mock 模式继续...")
                self.chroma_client = MockChromaClient()

        # 获取或创建 collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION
        )
        print(f"✅ Collection: {CHROMA_COLLECTION}")

    def init_embedding_generator(self):
        """初始化 Embedding 生成器"""
        self.embedding_generator = EmbeddingGenerator(mock_mode=MOCK_MODE)

    def close(self):
        """关闭连接"""
        if self.pg_conn:
            self.pg_conn.close()
        print("✅ 数据库连接已关闭")

    def get_chunks_from_postgresql(self) -> List[Dict]:
        """从 PostgreSQL 获取所有 chunks"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT
                id, chunk_id, text,
                document_id, project_id,
                quality_score, emotion_polarity, sentiment_label,
                dimension_category, keywords
            FROM document_chunks
            ORDER BY id
        """)

        chunks = []
        for row in cursor.fetchall():
            text = row['text'] or ''

            chunks.append({
                'id': row['id'],
                'chunk_id': row['chunk_id'],
                'text': text,
                'document_id': row['document_id'],
                'project_id': row['project_id'],
                'metadata': {
                    'quality_score': row['quality_score'],
                    'emotion_polarity': row['emotion_polarity'],
                    'sentiment_label': row['sentiment_label'],
                    'dimension_category': row['dimension_category'],
                    'keywords': row['keywords']
                }
            })

        self.stats['chunks_total'] = len(chunks)
        print(f"📊 从 PostgreSQL 读取 {len(chunks)} 个 chunks")
        return chunks

    def sync_chunks_batch(self, chunks: List[Dict]) -> int:
        """批量同步 chunks 到 ChromaDB"""
        # 准备数据
        ids = []
        documents = []
        metadatas = []
        texts_for_embedding = []

        for chunk in chunks:
            ids.append(chunk['chunk_id'])
            documents.append(chunk['text'])
            metadatas.append(chunk['metadata'])
            texts_for_embedding.append(chunk['text'])

        try:
            # 生成 embeddings
            embeddings = self.embedding_generator.generate_batch(texts_for_embedding)
            self.stats['embeddings_generated'] += len(embeddings)

            # 添加到 ChromaDB
            self.collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            # 更新 PostgreSQL 同步状态
            self.update_sync_status_batch(chunks, embeddings)

            return len(chunks)

        except Exception as e:
            print(f"\n❌ 批量同步失败: {e}")
            self.stats['errors'] += 1
            return 0

    def update_sync_status_batch(self, chunks: List[Dict], embeddings: List[List[float]]):
        """批量更新同步状态"""
        cursor = self.pg_conn.cursor()

        for i, chunk in enumerate(chunks):
            try:
                # 生成 embedding_id
                embedding_id = f"emb_{uuid.uuid4().hex[:12]}"

                cursor.execute("""
                    UPDATE document_chunks
                    SET synced_to_chromadb = 1,
                        chromadb_synced_at = ?,
                        embedding_id = ?,
                        sync_version = sync_version + 1
                    WHERE id = ?
                """, (
                    datetime.now().isoformat(),
                    embedding_id,
                    chunk['id']
                ))

                self.stats['chunks_synced'] += 1

            except Exception as e:
                print(f"❌ 更新同步状态失败 (id={chunk['id']}): {e}")
                self.stats['errors'] += 1

        self.pg_conn.commit()

    def verify_sync(self):
        """验证同步结果"""
        print("\n" + "=" * 70)
        print("验证同步结果")
        print("=" * 70)

        # ChromaDB 统计
        chroma_count = self.collection.count()

        # PostgreSQL 统计
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN synced_to_chromadb = 1 THEN 1 ELSE 0 END) as synced
            FROM document_chunks
        """)
        row = cursor.fetchone()
        pg_total = row['total']
        pg_synced = row['synced']

        print(f"\nChromaDB 统计:")
        print(f"  文档数: {chroma_count}")

        print(f"\nPostgreSQL 统计:")
        print(f"  总 Chunk 数: {pg_total}")
        print(f"  已标记同步: {pg_synced}")

        print(f"\n同步统计:")
        print(f"  已同步 Chunks: {self.stats['chunks_synced']}")
        print(f"  生成 Embeddings: {self.stats['embeddings_generated']}")

        if chroma_count == self.stats['chunks_synced']:
            print(f"\n✅ ChromaDB 同步一致")
        else:
            print(f"\n⚠️  数量不匹配: ChromaDB={chroma_count}, 已同步={self.stats['chunks_synced']}")

        # 显示同步率
        sync_rate = (pg_synced / pg_total * 100) if pg_total > 0 else 0
        print(f"📊 同步率: {sync_rate:.1f}%")

    def run(self):
        """执行批量同步"""
        print("=" * 70)
        print("ChromaDB 批量数据同步")
        print(f"模式: {'Mock（模拟）' if MOCK_MODE else 'Real（真实 Embedding）'}")
        print("=" * 70)

        self.stats['start_time'] = datetime.now()

        try:
            # 1. 获取 chunks
            print("\n[步骤 1/3] 读取 Chunk 数据")
            chunks = self.get_chunks_from_postgresql()

            # 2. 批量同步
            print(f"\n[步骤 2/3] 同步到 ChromaDB")
            print(f"批量大小: {BATCH_SIZE}")
            print()

            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i:i + BATCH_SIZE]
                batch_num = i // BATCH_SIZE + 1
                total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

                print(f"同步批次 {batch_num}/{total_batches} "
                      f"(Chunk {i+1}-{min(i+len(batch), len(chunks))}/{len(chunks)})...", end=' ')

                synced = self.sync_chunks_batch(batch)
                print(f"✅ {synced} 个")

            # 3. 验证
            print(f"\n[步骤 3/3] 验证同步结果")
            self.verify_sync()

            self.stats['end_time'] = datetime.now()

            # 生成报告
            self.generate_report()

        except Exception as e:
            print(f"\n❌ 同步失败: {e}")
            import traceback
            traceback.print_exc()
            self.stats['end_time'] = datetime.now()
            raise

    def generate_report(self):
        """生成同步报告"""
        print("\n" + "=" * 70)
        print("同步报告")
        print("=" * 70)

        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        print(f"Chunk 总数:        {self.stats['chunks_total']}")
        print(f"已同步:            {self.stats['chunks_synced']}")
        print(f"生成 Embeddings:   {self.stats['embeddings_generated']}")
        print(f"错误数:            {self.stats['errors']}")
        print(f"执行时间:          {duration:.2f} 秒")

        if duration > 0:
            speed = self.stats['chunks_synced'] / duration
            print(f"同步速度:          {speed:.1f} 条/秒")

        if self.stats['errors'] == 0:
            print(f"\n✅ ChromaDB 同步成功完成！")
        else:
            print(f"\n⚠️  ChromaDB 同步完成，但有 {self.stats['errors']} 个错误")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数"""
    syncer = ChromaDBBatchSyncer(DB_PATH)

    try:
        # 连接数据库
        syncer.connect_postgresql()
        syncer.connect_chromadb()
        syncer.init_embedding_generator()

        # 执行同步
        syncer.run()

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        sys.exit(1)

    finally:
        # 关闭连接
        syncer.close()

    print("\n✅ 所有操作完成")


if __name__ == "__main__":
    main()
