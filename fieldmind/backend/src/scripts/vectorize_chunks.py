#!/usr/bin/env python3
"""
向量化脚本 - 将文档chunks导入ChromaDB

功能：
1. 从SQLite读取所有chunks
2. 为每个chunk生成向量（使用ChromaDB的默认embedding）
3. 存储到ChromaDB
4. 验证导入结果
"""

import sys
import sqlite3
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.vector_store_service import create_vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chunks_from_db(db_path: str = "data/fieldmind.db"):
    """
    从SQLite加载所有chunks

    Returns:
        List of (id, text, metadata)
    """
    logger.info(f"从数据库加载chunks: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            dc.id,
            dc.text,
            dc.chunk_index,
            dc.document_id,
            d.filename,
            d.uploaded_by as project_id
        FROM document_chunks dc
        LEFT JOIN documents d ON dc.document_id = d.id
        WHERE dc.text IS NOT NULL AND LENGTH(dc.text) > 10
        ORDER BY dc.id
    """)

    chunks = []
    for row in cursor.fetchall():
        chunks.append({
            'id': str(row['id']),
            'text': row['text'],
            'metadata': {
                'chunk_index': row['chunk_index'],
                'document_id': row['document_id'] or '',
                'document_filename': row['filename'] or '',
                'project_id': str(row['project_id']) if row['project_id'] else ''
            }
        })

    conn.close()

    logger.info(f"✅ 加载了 {len(chunks)} 个chunks")
    return chunks


def import_chunks_to_vector_store(chunks, batch_size: int = 100):
    """
    将chunks导入向量存储

    Args:
        chunks: chunk数据列表
        batch_size: 批次大小
    """
    logger.info(f"开始导入 {len(chunks)} 个chunks到ChromaDB")

    # 创建向量存储服务
    vector_store = create_vector_store()

    # 清空现有数据（可选）
    current_count = vector_store.count()
    if current_count > 0:
        logger.info(f"当前集合已有 {current_count} 个文档")
        user_input = input("是否清空现有数据？(y/n): ")
        if user_input.lower() == 'y':
            vector_store.clear()
            logger.info("✅ 已清空现有数据")

    # 批量导入
    total = len(chunks)
    success_count = 0

    for i in range(0, total, batch_size):
        batch = chunks[i:i + batch_size]

        # 准备批次数据
        ids = [chunk['id'] for chunk in batch]
        documents = [chunk['text'] for chunk in batch]
        metadatas = [chunk['metadata'] for chunk in batch]

        # 添加到向量存储
        success = vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        if success:
            success_count += len(batch)
            logger.info(f"进度: {success_count}/{total} ({success_count*100//total}%)")
        else:
            logger.error(f"批次 {i//batch_size + 1} 导入失败")

    logger.info(f"✅ 导入完成: {success_count}/{total}")

    return vector_store


def verify_import(vector_store):
    """验证导入结果"""
    logger.info("\n" + "="*60)
    logger.info("验证导入结果")
    logger.info("="*60)

    # 统计信息
    info = vector_store.get_collection_info()
    logger.info(f"\n集合信息:")
    logger.info(f"  名称: {info['name']}")
    logger.info(f"  文档数: {info['count']}")
    logger.info(f"  元数据: {info['metadata']}")

    # 测试搜索
    logger.info(f"\n测试语义搜索:")
    test_queries = [
        "花鼓戏传承人",
        "苗族刺绣技艺",
        "乡村文化保护"
    ]

    for query in test_queries:
        logger.info(f"\n查询: {query}")
        results = vector_store.search(query, n_results=3)

        if results['ids'][0]:
            logger.info(f"  找到 {len(results['ids'][0])} 个结果:")
            for i, (doc_id, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                text_preview = results['documents'][0][i][:50]
                logger.info(f"    {i+1}. ID={doc_id}, 距离={distance:.4f}")
                logger.info(f"       {text_preview}...")
        else:
            logger.info(f"  未找到结果")


def main():
    """主流程"""
    logger.info("="*60)
    logger.info("向量化脚本 - 导入chunks到ChromaDB")
    logger.info("="*60)

    # 1. 加载chunks
    chunks = load_chunks_from_db()

    if not chunks:
        logger.error("❌ 没有可导入的chunks")
        return

    # 2. 导入到向量存储
    vector_store = import_chunks_to_vector_store(chunks, batch_size=50)

    # 3. 验证导入
    verify_import(vector_store)

    logger.info("\n" + "="*60)
    logger.info("✅ 向量化完成")
    logger.info("="*60)


if __name__ == "__main__":
    main()
