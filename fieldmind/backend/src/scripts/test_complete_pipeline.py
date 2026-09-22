#!/usr/bin/env python3
"""
完整链路测试：文件上传→切分→量化→写入数据库

验证每一步是否真正执行并写入数据
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_complete_pipeline():
    """测试完整处理链路"""
    logger.info("="*60)
    logger.info("【任务3】完整链路测试")
    logger.info("="*60)

    db_path = "data/fieldmind.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 步骤1: 检查documents表
    logger.info("\n步骤1: 检查documents表")
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]
    logger.info(f"✅ 文件已接收，共 {doc_count} 个文档")

    # 步骤2: 检查document_chunks表
    logger.info("\n步骤2: 检查document_chunks表")
    cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE text IS NOT NULL")
    chunk_count = cursor.fetchone()[0]
    logger.info(f"✅ 切分完成，共 {chunk_count} 个chunks")

    # 步骤3: 检查量化字段
    logger.info("\n步骤3: 检查量化字段")
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(word_count) as has_word_count,
            SUM(word_count) as total_words
        FROM document_chunks
        WHERE text IS NOT NULL
    """)
    row = cursor.fetchone()
    total, has_wc, total_words = row

    if has_wc == total:
        logger.info(f"✅ 量化完成，word_count已写入 ({total}/{total})")
        logger.info(f"   总字数: {total_words}")
    else:
        logger.error(f"❌ 量化未完成，仅 {has_wc}/{total} 有word_count")

    # 步骤4: 检查TF-IDF关键词
    logger.info("\n步骤4: 检查TF-IDF关键词")
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks
        WHERE tfidf_keywords IS NOT NULL AND tfidf_keywords != '[]'
    """)
    tfidf_count = cursor.fetchone()[0]

    if tfidf_count > 0:
        logger.info(f"✅ TF-IDF完成，{tfidf_count} 个chunks有关键词")

        # 显示示例
        cursor.execute("""
            SELECT id, tfidf_keywords
            FROM document_chunks
            WHERE tfidf_keywords IS NOT NULL AND tfidf_keywords != '[]'
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            chunk_id, keywords_json = row
            keywords = json.loads(keywords_json)
            logger.info(f"   示例(chunk {chunk_id}): {keywords[:5]}")
    else:
        logger.error(f"❌ TF-IDF未完成，所有chunks的tfidf_keywords为空")

    # 步骤5: 检查聚类
    logger.info("\n步骤5: 检查聚类")
    cursor.execute("SELECT COUNT(*) FROM cluster_results")
    cluster_count = cursor.fetchone()[0]

    if cluster_count > 0:
        logger.info(f"✅ 聚类完成，{cluster_count} 个chunks已分类")

        # 显示聚类分布
        cursor.execute("""
            SELECT cluster_label, COUNT(*) as count
            FROM cluster_results
            WHERE project_id = 1
            GROUP BY cluster_label
        """)
        for row in cursor.fetchall():
            label, count = row
            logger.info(f"   聚类{label}: {count}个")
    else:
        logger.error(f"❌ 聚类未完成，cluster_results表为空")

    # 步骤6: 检查向量化（如果有）
    logger.info("\n步骤6: 检查向量化")
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks
        WHERE embedding_vector IS NOT NULL
    """)
    vector_count = cursor.fetchone()[0]

    if vector_count > 0:
        logger.info(f"✅ 向量化完成，{vector_count} 个chunks有embedding")
    else:
        logger.info(f"⚠️ 向量化未执行（可选功能）")

    # 步骤7: 检查TF-IDF全局表
    logger.info("\n步骤7: 检查TF-IDF全局词权重")
    cursor.execute("SELECT COUNT(*) FROM tfidf_global WHERE project_id = 1")
    global_tfidf_count = cursor.fetchone()[0]

    if global_tfidf_count > 0:
        logger.info(f"✅ TF-IDF全局表已填充，{global_tfidf_count} 个词")
    else:
        logger.error(f"❌ TF-IDF全局表为空")

    conn.close()

    # 总结
    logger.info("\n" + "="*60)
    logger.info("链路测试总结")
    logger.info("="*60)

    checks = [
        ("文件接收", doc_count > 0),
        ("文本切分", chunk_count > 0),
        ("字段量化", has_wc == total),
        ("TF-IDF关键词", tfidf_count > 0),
        ("聚类分析", cluster_count > 0),
        ("全局词权重", global_tfidf_count > 0),
    ]

    passed = sum(1 for _, result in checks if result)
    total_checks = len(checks)

    for name, result in checks:
        icon = "✅" if result else "❌"
        logger.info(f"  {icon} {name}")

    logger.info(f"\n通过: {passed}/{total_checks}")

    if passed == total_checks:
        logger.info("\n🎉 完整链路测试通过！所有步骤都已正确执行")
    else:
        logger.error(f"\n❌ {total_checks - passed} 个步骤失败，需要修复")


def show_sample_data():
    """显示样本数据"""
    logger.info("\n" + "="*60)
    logger.info("样本数据展示")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 显示1个chunk的完整数据
    cursor.execute("""
        SELECT
            id,
            text,
            word_count,
            emotion_polarity,
            emotion_label,
            subjectivity,
            cluster_label,
            tfidf_keywords
        FROM document_chunks
        WHERE text IS NOT NULL
        LIMIT 1
    """)

    row = cursor.fetchone()
    if row:
        chunk_id, text, wc, emotion, emotion_label, subj, cluster, tfidf = row

        logger.info(f"\nChunk ID: {chunk_id}")
        logger.info(f"文本: {text[:100]}...")
        logger.info(f"字数: {wc}")
        logger.info(f"情感极性: {emotion} ({emotion_label})")
        logger.info(f"主观性: {subj}")
        logger.info(f"聚类标签: {cluster}")
        if tfidf:
            keywords = json.loads(tfidf)
            logger.info(f"关键词: {keywords[:5]}")

    conn.close()


if __name__ == "__main__":
    test_complete_pipeline()
    show_sample_data()
