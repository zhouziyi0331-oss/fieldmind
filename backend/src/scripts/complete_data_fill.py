#!/usr/bin/env python3
"""
完整数据填充脚本

彻底解决所有数据层技术债：
1. 填充所有chunks的cluster_label
2. 填充tfidf_global表（全局词权重）
3. 确保cluster_results完整覆盖所有chunks
4. 重新计算所有comparison_results
5. 验证数据完整性
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import json
import logging
from datetime import datetime
import pandas as pd

from app.services.analysis.cluster_analyzer import cluster_chunks, save_cluster_results
from app.services.analysis.comparison_analyzer import compare_all_clusters, save_comparison_results

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fill_cluster_labels():
    """步骤1: 填充所有chunks的cluster_label"""
    logger.info("\n" + "="*60)
    logger.info("步骤 1: 填充cluster_label字段")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取所有chunks
    cursor.execute("""
        SELECT id, text
        FROM document_chunks
        WHERE text IS NOT NULL AND text != ''
        ORDER BY id
    """)

    rows = cursor.fetchall()
    chunk_ids = [row[0] for row in rows]
    chunk_texts = [row[1] for row in rows]

    logger.info(f"找到 {len(chunk_ids)} 个chunks")

    if len(chunk_ids) < 3:
        logger.warning("Chunks数量不足，无法聚类")
        conn.close()
        return False

    # 执行聚类
    n_clusters = min(3, len(chunk_ids))
    result = cluster_chunks(chunk_texts, n_clusters=n_clusters)

    # 保存到cluster_results表
    project_id = 1
    saved = save_cluster_results(
        conn, project_id, chunk_ids, result['labels'], result['cluster_keywords']
    )

    # 更新document_chunks的cluster_label字段
    for chunk_id, label in zip(chunk_ids, result['labels']):
        cursor.execute("""
            UPDATE document_chunks
            SET cluster_label = ?
            WHERE id = ?
        """, (label, chunk_id))

    conn.commit()

    # 验证
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks WHERE cluster_label IS NOT NULL
    """)
    filled_count = cursor.fetchone()[0]

    conn.close()

    logger.info(f"✅ 已填充 {filled_count} 个chunks的cluster_label")
    return True


def fill_tfidf_global():
    """步骤2: 填充tfidf_global表"""
    logger.info("\n" + "="*60)
    logger.info("步骤 2: 填充tfidf_global表")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取所有chunks的文本
    cursor.execute("""
        SELECT text FROM document_chunks
        WHERE text IS NOT NULL AND text != ''
    """)

    texts = [row[0] for row in cursor.fetchall()]

    if not texts:
        logger.warning("没有文本数据")
        conn.close()
        return False

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import jieba

        def jieba_tokenizer(text):
            return list(jieba.cut(text))

        # 计算TF-IDF
        vectorizer = TfidfVectorizer(
            max_features=500,
            tokenizer=jieba_tokenizer,
            lowercase=False,
            token_pattern=None
        )

        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        # 计算IDF值
        idf_scores = vectorizer.idf_
        total_docs = len(texts)

        # 计算每个词的文档频率
        import numpy as np
        doc_freq = np.asarray((tfidf_matrix > 0).sum(axis=0)).ravel()

        # 清空旧数据
        cursor.execute("DELETE FROM tfidf_global WHERE project_id = 1")

        # 插入新数据
        project_id = 1
        inserted = 0

        for i, term in enumerate(feature_names):
            cursor.execute("""
                INSERT INTO tfidf_global
                (project_id, term, idf_score, total_docs, doc_freq, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                term,
                float(idf_scores[i]),
                total_docs,
                int(doc_freq[i]),
                datetime.utcnow().isoformat()
            ))
            inserted += 1

        conn.commit()
        conn.close()

        logger.info(f"✅ 已插入 {inserted} 条TF-IDF全局词权重")
        return True

    except Exception as e:
        logger.error(f"填充tfidf_global失败: {e}")
        conn.close()
        return False


def recalculate_comparisons():
    """步骤3: 重新计算所有对比分析"""
    logger.info("\n" + "="*60)
    logger.info("步骤 3: 重新计算对比分析")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取所有有聚类标签的chunks及其量化数据
    cursor.execute("""
        SELECT
            dc.id,
            dc.cluster_label,
            dc.emotion_polarity,
            dc.emotion_intensity,
            dc.subjectivity,
            dc.objectivity,
            dc.tone_strength,
            dc.emotion_word_density
        FROM document_chunks dc
        JOIN cluster_results cr ON dc.id = cr.chunk_id
        WHERE cr.project_id = 1
    """)

    rows = cursor.fetchall()

    if not rows:
        logger.warning("没有聚类数据")
        conn.close()
        return False

    # 构建DataFrame
    df = pd.DataFrame(rows, columns=[
        'id', 'cluster_label', 'emotion_polarity', 'emotion_intensity',
        'subjectivity', 'objectivity', 'tone_strength', 'emotion_word_density'
    ])

    logger.info(f"加载了 {len(df)} 个chunks")

    # 执行所有对比分析
    value_cols = [
        'emotion_polarity', 'emotion_intensity',
        'subjectivity', 'objectivity',
        'tone_strength', 'emotion_word_density'
    ]

    comparisons = compare_all_clusters(df, value_cols)

    if not comparisons:
        logger.warning("没有生成对比结果")
        conn.close()
        return False

    # 保存结果
    project_id = 1
    saved = save_comparison_results(conn, project_id, comparisons)

    conn.close()

    logger.info(f"✅ 已保存 {saved} 条对比结果")
    return True


def verify_data_completeness():
    """步骤4: 验证数据完整性"""
    logger.info("\n" + "="*60)
    logger.info("步骤 4: 验证数据完整性")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    issues = []

    # 1. 检查所有chunks是否有量化数据
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks
        WHERE text IS NOT NULL AND (
            word_count IS NULL OR
            emotion_polarity IS NULL OR
            subjectivity IS NULL
        )
    """)
    missing_quantification = cursor.fetchone()[0]
    if missing_quantification > 0:
        issues.append(f"❌ {missing_quantification} 个chunks缺少量化数据")
    else:
        logger.info("✅ 所有chunks都有量化数据")

    # 2. 检查所有chunks是否有聚类标签
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks
        WHERE text IS NOT NULL AND cluster_label IS NULL
    """)
    missing_cluster = cursor.fetchone()[0]
    if missing_cluster > 0:
        issues.append(f"❌ {missing_cluster} 个chunks缺少聚类标签")
    else:
        logger.info("✅ 所有chunks都有聚类标签")

    # 3. 检查cluster_results表
    cursor.execute("""
        SELECT COUNT(*) FROM cluster_results WHERE project_id = 1
    """)
    cluster_results_count = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM document_chunks WHERE text IS NOT NULL
    """)
    total_chunks = cursor.fetchone()[0]

    if cluster_results_count != total_chunks:
        issues.append(f"❌ cluster_results表不完整: {cluster_results_count}/{total_chunks}")
    else:
        logger.info(f"✅ cluster_results表完整 ({cluster_results_count} 条)")

    # 4. 检查tfidf_global表
    cursor.execute("""
        SELECT COUNT(*) FROM tfidf_global WHERE project_id = 1
    """)
    tfidf_count = cursor.fetchone()[0]
    if tfidf_count == 0:
        issues.append(f"❌ tfidf_global表为空")
    else:
        logger.info(f"✅ tfidf_global表有 {tfidf_count} 条记录")

    # 5. 检查comparison_results表
    cursor.execute("""
        SELECT COUNT(*) FROM comparison_results WHERE project_id = 1
    """)
    comparison_count = cursor.fetchone()[0]
    if comparison_count == 0:
        issues.append(f"❌ comparison_results表为空")
    else:
        logger.info(f"✅ comparison_results表有 {comparison_count} 条记录")

    conn.close()

    if issues:
        logger.error("\n发现以下问题:")
        for issue in issues:
            logger.error(f"  {issue}")
        return False
    else:
        logger.info("\n✅ 数据完整性验证通过")
        return True


def generate_data_summary():
    """生成数据摘要报告"""
    logger.info("\n" + "="*60)
    logger.info("数据摘要报告")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 表数据统计
    cursor.execute("""
        SELECT 'documents' as table_name, COUNT(*) as count FROM documents
        UNION ALL SELECT 'document_chunks', COUNT(*) FROM document_chunks
        UNION ALL SELECT 'entities', COUNT(*) FROM entities
        UNION ALL SELECT 'chunk_entities', COUNT(*) FROM chunk_entities
        UNION ALL SELECT 'entity_relations', COUNT(*) FROM entity_relations
        UNION ALL SELECT 'tfidf_global', COUNT(*) FROM tfidf_global
        UNION ALL SELECT 'cluster_results', COUNT(*) FROM cluster_results
        UNION ALL SELECT 'comparison_results', COUNT(*) FROM comparison_results
    """)

    logger.info("\n表数据统计:")
    for row in cursor.fetchall():
        logger.info(f"  {row[0]:<25} {row[1]:>6} 条")

    # 聚类分布
    cursor.execute("""
        SELECT cluster_label, COUNT(*) as count
        FROM cluster_results
        WHERE project_id = 1
        GROUP BY cluster_label
        ORDER BY cluster_label
    """)

    logger.info("\n聚类分布:")
    total = 0
    for row in cursor.fetchall():
        label, count = row
        total += count
        logger.info(f"  聚类{label}: {count} 个")

    logger.info(f"  总计: {total} 个")

    # 显著差异统计
    cursor.execute("""
        SELECT COUNT(*) FROM comparison_results
        WHERE project_id = 1 AND significant = 1
    """)
    significant_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM comparison_results WHERE project_id = 1
    """)
    total_comparisons = cursor.fetchone()[0]

    logger.info("\n对比分析:")
    logger.info(f"  总对比: {total_comparisons}")
    logger.info(f"  显著差异: {significant_count}")

    conn.close()


def main():
    """主流程"""
    logger.info("="*60)
    logger.info("完整数据填充 - 彻底解决技术债")
    logger.info("="*60)

    results = []

    # 执行所有步骤
    results.append(("填充cluster_label", fill_cluster_labels()))
    results.append(("填充tfidf_global", fill_tfidf_global()))
    results.append(("重新计算对比", recalculate_comparisons()))
    results.append(("验证数据完整性", verify_data_completeness()))

    # 汇总
    logger.info("\n" + "="*60)
    logger.info("执行结果汇总")
    logger.info("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        icon = "✅" if result else "❌"
        logger.info(f"  {icon} {name}")

    logger.info(f"\n通过: {passed}/{total}")

    if passed == total:
        generate_data_summary()

        logger.info("\n" + "="*60)
        logger.info("🎉 所有数据层问题已彻底解决！")
        logger.info("="*60)
        logger.info("\n系统状态:")
        logger.info("  ✅ 所有量化字段已填充")
        logger.info("  ✅ 所有聚类标签已分配")
        logger.info("  ✅ TF-IDF全局词权重已计算")
        logger.info("  ✅ 对比分析已完成")
        logger.info("  ✅ 数据完整性验证通过")
        logger.info("\n无技术债，系统可以投入使用！")
    else:
        logger.error(f"\n❌ {total - passed} 个步骤失败")


if __name__ == "__main__":
    main()
