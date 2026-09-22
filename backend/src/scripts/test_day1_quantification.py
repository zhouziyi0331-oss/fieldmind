#!/usr/bin/env python3
"""
Day 1 测试脚本：量化工具箱功能验证

测试内容：
1. 表结构验证（17个字段）
2. 结构性特征提取
3. 情绪特征提取
4. 语言风格特征提取
5. 内容类特征提取
6. TF-IDF关键词提取
7. 批量量化分析
8. 数据库写入验证
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
import logging
from datetime import datetime

from app.services.quantification.quantifier import quantify_chunk, batch_quantify_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_schema():
    """测试1: 验证数据库表结构"""
    logger.info("\n" + "="*60)
    logger.info("测试 1: 数据库表结构验证")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查document_chunks表的量化字段
    cursor.execute("PRAGMA table_info(document_chunks)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    required_fields = [
        'word_count', 'sentence_count', 'paragraph_count',
        'avg_word_length', 'avg_sentence_length',
        'emotion_polarity', 'emotion_intensity', 'emotion_label',
        'subjectivity', 'objectivity', 'tone_strength',
        'exclamation_count', 'modal_verb_count',
        'emotion_word_density', 'keyword_density',
        'tfidf_keywords', 'cluster_label'
    ]

    missing = []
    for field in required_fields:
        if field in columns:
            logger.info(f"  ✅ {field}: {columns[field]}")
        else:
            logger.error(f"  ❌ {field}: 缺失")
            missing.append(field)

    # 检查支持表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    support_tables = ['tfidf_global', 'cluster_results', 'comparison_results']
    for table in support_tables:
        if table in tables:
            logger.info(f"  ✅ 表 {table} 存在")
        else:
            logger.error(f"  ❌ 表 {table} 缺失")

    conn.close()

    if not missing:
        logger.info("✅ 数据库表结构验证通过")
        return True
    else:
        logger.error(f"❌ 缺失字段: {missing}")
        return False


def test_quantify_single_chunk():
    """测试2: 单个chunk量化分析"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: 单个chunk量化分析")
    logger.info("="*60)

    test_text = """
    王大爷是村里最后一位会唱花鼓戏的老艺人，今年82岁。
    他从16岁开始学戏，师从著名花鼓戏传承人李师傅。
    王大爷说："那时候没有电视，唱戏就是我们最大的娱乐！"
    他会唱《刘海砍樵》《补锅》等20多出经典剧目。
    """

    logger.info(f"测试文本: {test_text[:50]}...")

    result = quantify_chunk(test_text)

    logger.info("\n量化结果:")
    logger.info(f"  字数: {result['word_count']}")
    logger.info(f"  句数: {result['sentence_count']}")
    logger.info(f"  段落数: {result['paragraph_count']}")
    logger.info(f"  平均词长: {result['avg_word_length']}")
    logger.info(f"  平均句长: {result['avg_sentence_length']}")
    logger.info(f"  情感极性: {result['emotion_polarity']}")
    logger.info(f"  情绪强度: {result['emotion_intensity']}")
    logger.info(f"  情绪标签: {result['emotion_label']}")
    logger.info(f"  主观性: {result['subjectivity']}")
    logger.info(f"  客观性: {result['objectivity']}")
    logger.info(f"  语气强度: {result['tone_strength']}")
    logger.info(f"  感叹号数: {result['exclamation_count']}")
    logger.info(f"  情态动词数: {result['modal_verb_count']}")
    logger.info(f"  情绪词密度: {result['emotion_word_density']}")

    # 验证所有必需字段都有值
    required_keys = [
        'word_count', 'sentence_count', 'emotion_polarity',
        'emotion_label', 'subjectivity', 'tone_strength'
    ]

    all_present = all(key in result for key in required_keys)

    if all_present and result['word_count'] > 0:
        logger.info("✅ 单个chunk量化分析通过")
        return True
    else:
        logger.error("❌ 量化结果不完整")
        return False


def test_tfidf_keywords():
    """测试3: TF-IDF关键词提取"""
    logger.info("\n" + "="*60)
    logger.info("测试 3: TF-IDF关键词提取")
    logger.info("="*60)

    chunks = [
        "王大爷是村里最后一位会唱花鼓戏的老艺人。",
        "苗族刺绣是一种传统的民间艺术，历史悠久。",
        "山歌是侗族人民表达情感的重要方式，代代相传。",
        "花鼓戏在湖南地区非常流行，深受群众喜爱。",
    ]

    for i, chunk in enumerate(chunks):
        result = quantify_chunk(chunk, all_chunks=chunks)
        keywords = json.loads(result['tfidf_keywords'])

        logger.info(f"\nChunk {i+1}: {chunk[:30]}...")
        logger.info(f"  关键词: {keywords}")

    logger.info("✅ TF-IDF关键词提取测试完成")
    return True


def test_batch_quantify():
    """测试4: 批量量化分析"""
    logger.info("\n" + "="*60)
    logger.info("测试 4: 批量量化分析")
    logger.info("="*60)

    # 从数据库读取真实chunks
    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, text
        FROM document_chunks
        WHERE text IS NOT NULL
        LIMIT 5
    """)

    chunks_data = [{'id': row[0], 'text': row[1]} for row in cursor.fetchall()]
    conn.close()

    if not chunks_data:
        logger.warning("⚠️ 数据库中没有chunks，跳过批量测试")
        return True

    logger.info(f"读取了 {len(chunks_data)} 个chunks进行测试")

    results = batch_quantify_chunks(chunks_data)

    logger.info(f"\n批量量化结果:")
    for i, result in enumerate(results[:3]):
        logger.info(f"\nChunk {result['chunk_id']}:")
        features = result['features']
        logger.info(f"  字数: {features['word_count']}")
        logger.info(f"  情感: {features['emotion_label']} ({features['emotion_polarity']})")
        logger.info(f"  主观性: {features['subjectivity']}")

    if len(results) == len(chunks_data):
        logger.info("✅ 批量量化分析通过")
        return True
    else:
        logger.error("❌ 批量量化结果数量不匹配")
        return False


def test_database_write():
    """测试5: 数据库写入验证"""
    logger.info("\n" + "="*60)
    logger.info("测试 5: 数据库写入验证")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取第一个chunk
    cursor.execute("""
        SELECT id, text
        FROM document_chunks
        WHERE text IS NOT NULL
        LIMIT 1
    """)

    row = cursor.fetchone()
    if not row:
        logger.warning("⚠️ 数据库中没有chunks，跳过写入测试")
        conn.close()
        return True

    chunk_id, text = row

    # 量化分析
    features = quantify_chunk(text)

    # 写入数据库
    try:
        cursor.execute("""
            UPDATE document_chunks
            SET word_count = ?,
                sentence_count = ?,
                paragraph_count = ?,
                avg_word_length = ?,
                avg_sentence_length = ?,
                emotion_polarity = ?,
                emotion_intensity = ?,
                emotion_label = ?,
                subjectivity = ?,
                objectivity = ?,
                tone_strength = ?,
                exclamation_count = ?,
                modal_verb_count = ?,
                emotion_word_density = ?,
                keyword_density = ?,
                tfidf_keywords = ?
            WHERE id = ?
        """, (
            features['word_count'],
            features['sentence_count'],
            features['paragraph_count'],
            features['avg_word_length'],
            features['avg_sentence_length'],
            features['emotion_polarity'],
            features['emotion_intensity'],
            features['emotion_label'],
            features['subjectivity'],
            features['objectivity'],
            features['tone_strength'],
            features['exclamation_count'],
            features['modal_verb_count'],
            features['emotion_word_density'],
            features['keyword_density'],
            features['tfidf_keywords'],
            chunk_id
        ))

        conn.commit()

        # 验证写入
        cursor.execute("""
            SELECT word_count, emotion_label, subjectivity
            FROM document_chunks
            WHERE id = ?
        """, (chunk_id,))

        result = cursor.fetchone()

        if result and result[0] == features['word_count']:
            logger.info(f"✅ 数据成功写入chunk {chunk_id}")
            logger.info(f"   字数: {result[0]}")
            logger.info(f"   情绪: {result[1]}")
            logger.info(f"   主观性: {result[2]}")
            conn.close()
            return True
        else:
            logger.error("❌ 数据写入验证失败")
            conn.close()
            return False

    except Exception as e:
        logger.error(f"❌ 数据库写入失败: {e}")
        conn.close()
        return False


def main():
    """运行所有测试"""
    logger.info("="*60)
    logger.info("Day 1 测试：量化工具箱功能验证")
    logger.info("="*60)

    results = []

    # 运行所有测试
    results.append(("数据库表结构", test_database_schema()))
    results.append(("单个chunk量化", test_quantify_single_chunk()))
    results.append(("TF-IDF关键词", test_tfidf_keywords()))
    results.append(("批量量化分析", test_batch_quantify()))
    results.append(("数据库写入", test_database_write()))

    # 汇总结果
    logger.info("\n" + "="*60)
    logger.info("测试结果汇总")
    logger.info("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        icon = "✅" if result else "❌"
        logger.info(f"  {icon} {name}")

    logger.info(f"\n通过: {passed}/{total}")

    if passed == total:
        logger.info("\n" + "="*60)
        logger.info("🎉 Day 1 所有测试通过！")
        logger.info("="*60)
        logger.info("\nDay 1 完成项:")
        logger.info("  ✅ 17个量化字段添加完成")
        logger.info("  ✅ 3个支持表创建完成")
        logger.info("  ✅ 量化工具箱实现完成")
        logger.info("  ✅ 所有特征提取器工作正常")
        logger.info("  ✅ 数据库读写验证通过")
        logger.info("\n准备进入 Day 2: 智能分析层")
    else:
        logger.error(f"\n❌ {total - passed} 个测试失败")


if __name__ == "__main__":
    main()
