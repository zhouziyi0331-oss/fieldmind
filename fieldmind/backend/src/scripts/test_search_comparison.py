#!/usr/bin/env python3
"""
测试全文搜索和向量搜索功能

对比：
1. 全文搜索（FTS5）- 关键词匹配
2. 向量搜索（ChromaDB）- 语义相似度
3. 混合搜索 - 结合两者优势
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.fulltext_search_service import create_fulltext_search_service
from app.services.vector_store_service import create_vector_store
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_fulltext_search(fts_service):
    """测试全文搜索"""
    logger.info("\n" + "="*60)
    logger.info("测试 1: 全文搜索（FTS5）")
    logger.info("="*60)

    test_queries = [
        "花鼓戏",
        "刺绣",
        "传承人",
        "苗族",
        "乡村文化"
    ]

    for query in test_queries:
        logger.info(f"\n查询: {query}")

        # 统计匹配数量
        count = fts_service.count_matches(query)
        logger.info(f"  匹配数量: {count}")

        # 执行搜索
        results = fts_service.search(query, limit=3, highlight=True)

        if results:
            logger.info(f"  搜索结果:")
            for i, result in enumerate(results, 1):
                logger.info(f"    {i}. ID={result['chunk_id']}, Rank={result['rank']:.4f}")
                logger.info(f"       {result['text'][:80]}...")
        else:
            logger.info(f"  未找到结果")


def test_vector_search(vector_store):
    """测试向量搜索"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: 向量搜索（ChromaDB）")
    logger.info("="*60)

    test_queries = [
        "传统戏曲和表演艺术",
        "手工艺品制作技术",
        "民族文化传承保护",
        "少数民族服饰文化",
        "农村传统建筑"
    ]

    for query in test_queries:
        logger.info(f"\n查询: {query}")

        results = vector_store.search(query, n_results=3)

        if results['ids'][0]:
            logger.info(f"  搜索结果:")
            for i, (doc_id, distance, doc) in enumerate(
                zip(results['ids'][0], results['distances'][0], results['documents'][0]),
                1
            ):
                logger.info(f"    {i}. ID={doc_id}, 距离={distance:.4f}")
                logger.info(f"       {doc[:80]}...")
        else:
            logger.info(f"  未找到结果")


def test_hybrid_search(fts_service, vector_store):
    """测试混合搜索"""
    logger.info("\n" + "="*60)
    logger.info("测试 3: 混合搜索（FTS5 + ChromaDB）")
    logger.info("="*60)

    test_cases = [
        {
            "query": "花鼓戏传承",
            "description": "精确关键词 + 语义理解"
        },
        {
            "query": "民族刺绣技艺",
            "description": "专业术语 + 相关概念"
        }
    ]

    for case in test_cases:
        query = case['query']
        desc = case['description']

        logger.info(f"\n查询: {query}")
        logger.info(f"目标: {desc}")

        # 1. 全文搜索
        fts_results = fts_service.search(query, limit=5, highlight=False)
        fts_ids = set(r['chunk_id'] for r in fts_results)

        logger.info(f"\n  全文搜索: {len(fts_results)} 个结果")
        for i, result in enumerate(fts_results[:2], 1):
            logger.info(f"    {i}. ID={result['chunk_id']}")
            logger.info(f"       {result['text'][:60]}...")

        # 2. 向量搜索
        vector_results = vector_store.search(query, n_results=5)
        vector_ids = set(int(id) for id in vector_results['ids'][0])

        logger.info(f"\n  向量搜索: {len(vector_results['ids'][0])} 个结果")
        for i, (doc_id, doc) in enumerate(
            zip(vector_results['ids'][0][:2], vector_results['documents'][0][:2]),
            1
        ):
            logger.info(f"    {i}. ID={doc_id}")
            logger.info(f"       {doc[:60]}...")

        # 3. 混合结果
        common_ids = fts_ids & vector_ids
        all_ids = fts_ids | vector_ids

        logger.info(f"\n  混合结果:")
        logger.info(f"    两者都匹配: {len(common_ids)} 个")
        logger.info(f"    总共匹配: {len(all_ids)} 个")

        if common_ids:
            logger.info(f"    共同ID: {sorted(list(common_ids))}")


def compare_search_methods():
    """对比不同搜索方法的特点"""
    logger.info("\n" + "="*60)
    logger.info("搜索方法对比")
    logger.info("="*60)

    logger.info("""
    1. 全文搜索（FTS5）
       优势：
         - 精确关键词匹配
         - 速度快
         - 支持布尔查询
       劣势：
         - 无法理解语义
         - 需要精确匹配
         - 对同义词不敏感

    2. 向量搜索（ChromaDB）
       优势：
         - 语义相似度匹配
         - 理解上下文
         - 找到概念相关内容
       劣势：
         - 可能不精确
         - 计算成本较高
         - 需要embedding模型

    3. 混合搜索
       优势：
         - 结合两者优势
         - 既精确又智能
         - 覆盖更全面
       劣势：
         - 实现复杂
         - 需要结果融合策略
    """)


def main():
    """主测试流程"""
    logger.info("="*60)
    logger.info("全文搜索 vs 向量搜索测试")
    logger.info("="*60)

    # 初始化服务
    logger.info("\n初始化服务...")
    fts_service = create_fulltext_search_service()
    vector_store = create_vector_store()

    logger.info(f"✅ FTS5服务已就绪")
    logger.info(f"✅ ChromaDB服务已就绪（{vector_store.count()}个文档）")

    # 1. 测试全文搜索
    test_fulltext_search(fts_service)

    # 2. 测试向量搜索
    test_vector_search(vector_store)

    # 3. 测试混合搜索
    test_hybrid_search(fts_service, vector_store)

    # 4. 对比分析
    compare_search_methods()

    logger.info("\n" + "="*60)
    logger.info("✅ 测试完成")
    logger.info("="*60)


if __name__ == "__main__":
    main()
