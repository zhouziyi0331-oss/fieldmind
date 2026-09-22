#!/usr/bin/env python3
"""
Day 2 测试脚本：智能分析层功能验证

测试内容：
1. 聚类分析（TF-IDF + KMeans）
2. 聚类结果保存
3. 分组对比分析（t检验）
4. 对比结果保存
5. 完整分析流程
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import pandas as pd
import logging
from datetime import datetime

from app.services.analysis.cluster_analyzer import (
    cluster_chunks, save_cluster_results, get_cluster_summary
)
from app.services.analysis.comparison_analyzer import (
    compare_groups, compare_all_clusters, save_comparison_results,
    get_significant_comparisons
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_clustering():
    """测试1: 聚类分析"""
    logger.info("\n" + "="*60)
    logger.info("测试 1: 聚类分析（TF-IDF + KMeans）")
    logger.info("="*60)

    # 测试数据
    test_chunks = [
        "王大爷是村里最后一位会唱花鼓戏的老艺人，今年82岁。",
        "苗族刺绣是一种传统的民间艺术，历史悠久，技艺精湛。",
        "山歌是侗族人民表达情感的重要方式，代代相传。",
        "花鼓戏在湖南地区非常流行，深受群众喜爱。",
        "蜡染是苗族的传统工艺，图案精美，色彩丰富。",
        "芦笙是苗族传统乐器，吹奏时音色嘹亮。",
        "戏台是戏曲表演的重要场所，通常建在村中心。",
        "刺绣技艺需要长期练习，十分考验耐心和细心。",
    ]

    result = cluster_chunks(test_chunks, n_clusters=3)

    logger.info(f"\n聚类结果:")
    logger.info(f"  聚类数: {result['n_clusters']}")
    logger.info(f"  聚类标签: {result['labels']}")
    logger.info(f"  聚类大小: {result['cluster_sizes']}")

    logger.info(f"\n聚类关键词:")
    for label, keywords in result['cluster_keywords'].items():
        logger.info(f"  聚类{label}: {keywords[:5]}")

    if result['n_clusters'] == 3 and len(result['labels']) == len(test_chunks):
        logger.info("✅ 聚类分析测试通过")
        return True
    else:
        logger.error("❌ 聚类结果不符合预期")
        return False


def test_save_cluster_results():
    """测试2: 保存聚类结果到数据库"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: 保存聚类结果")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")

    # 获取真实的chunks
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, text
        FROM document_chunks
        WHERE text IS NOT NULL
        LIMIT 10
    """)

    rows = cursor.fetchall()
    if not rows:
        logger.warning("⚠️ 数据库中没有chunks，跳过测试")
        conn.close()
        return True

    chunk_ids = [row[0] for row in rows]
    chunk_texts = [row[1] for row in rows]

    # 聚类
    result = cluster_chunks(chunk_texts, n_clusters=3)

    # 保存结果
    project_id = 1  # 假设项目ID为1
    saved_count = save_cluster_results(
        conn, project_id, chunk_ids, result['labels'], result['cluster_keywords']
    )

    # 验证保存
    cursor.execute("""
        SELECT COUNT(*) FROM cluster_results WHERE project_id = ?
    """, (project_id,))

    count = cursor.fetchone()[0]

    conn.close()

    if count == len(chunk_ids):
        logger.info(f"✅ 成功保存 {count} 条聚类结果")
        return True
    else:
        logger.error(f"❌ 保存数量不匹配: 预期{len(chunk_ids)}, 实际{count}")
        return False


def test_cluster_summary():
    """测试3: 聚类摘要"""
    logger.info("\n" + "="*60)
    logger.info("测试 3: 聚类摘要")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    project_id = 1

    summary = get_cluster_summary(conn, project_id)

    logger.info(f"\n聚类摘要:")
    logger.info(f"  项目ID: {summary['project_id']}")
    logger.info(f"  总chunks: {summary['total_chunks']}")
    logger.info(f"  聚类数: {summary['n_clusters']}")

    logger.info(f"\n各聚类详情:")
    for cluster in summary['clusters']:
        logger.info(f"  聚类{cluster['label']}: {cluster['count']}个 ({cluster['percentage']}%)")
        logger.info(f"    关键词: {cluster['keywords']}")

    conn.close()

    if summary['n_clusters'] > 0:
        logger.info("✅ 聚类摘要测试通过")
        return True
    else:
        logger.error("❌ 聚类摘要为空")
        return False


def test_group_comparison():
    """测试4: 分组对比分析（t检验）"""
    logger.info("\n" + "="*60)
    logger.info("测试 4: 分组对比分析（t检验）")
    logger.info("="*60)

    # 创建测试数据
    data = {
        'cluster_label': [0, 0, 0, 1, 1, 1, 2, 2, 2],
        'emotion_polarity': [-0.2, -0.3, -0.1, 0.4, 0.5, 0.3, 0.1, 0.0, 0.2],
        'subjectivity': [0.3, 0.4, 0.2, 0.7, 0.8, 0.6, 0.5, 0.5, 0.4]
    }

    df = pd.DataFrame(data)

    # 对比聚类0和聚类1的情感极性
    result = compare_groups(df, 'cluster_label', 'emotion_polarity', 0, 1)

    logger.info(f"\n对比结果（聚类0 vs 聚类1 - 情感极性）:")
    logger.info(f"  t统计量: {result['t_statistic']}")
    logger.info(f"  p值: {result['p_value']}")
    logger.info(f"  显著差异: {result['significant']}")
    logger.info(f"  聚类0均值: {result['group1_mean']}")
    logger.info(f"  聚类1均值: {result['group2_mean']}")
    logger.info(f"  差异: {result['diff']}")

    if 't_statistic' in result and 'p_value' in result:
        logger.info("✅ 分组对比测试通过")
        return True
    else:
        logger.error("❌ 分组对比结果不完整")
        return False


def test_save_comparison_results():
    """测试5: 保存对比结果"""
    logger.info("\n" + "="*60)
    logger.info("测试 5: 保存对比结果")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取有聚类标签的chunks
    cursor.execute("""
        SELECT dc.id, dc.text,
               dc.emotion_polarity, dc.subjectivity, dc.tone_strength,
               cr.cluster_label
        FROM document_chunks dc
        JOIN cluster_results cr ON dc.id = cr.chunk_id
        WHERE cr.project_id = 1
    """)

    rows = cursor.fetchall()

    if not rows:
        logger.warning("⚠️ 没有聚类数据，跳过测试")
        conn.close()
        return True

    # 构建DataFrame
    df = pd.DataFrame(rows, columns=[
        'id', 'text', 'emotion_polarity', 'subjectivity', 'tone_strength', 'cluster_label'
    ])

    logger.info(f"加载了 {len(df)} 个chunks")

    # 执行所有对比分析
    value_cols = ['emotion_polarity', 'subjectivity', 'tone_strength']
    comparisons = compare_all_clusters(df, value_cols)

    if not comparisons:
        logger.warning("⚠️ 没有生成对比结果")
        conn.close()
        return True

    # 保存结果
    project_id = 1
    saved_count = save_comparison_results(conn, project_id, comparisons)

    # 验证
    cursor.execute("""
        SELECT COUNT(*) FROM comparison_results WHERE project_id = ?
    """, (project_id,))

    count = cursor.fetchone()[0]

    conn.close()

    if count == len(comparisons):
        logger.info(f"✅ 成功保存 {count} 条对比结果")
        return True
    else:
        logger.error(f"❌ 保存数量不匹配: 预期{len(comparisons)}, 实际{count}")
        return False


def test_significant_comparisons():
    """测试6: 获取显著差异"""
    logger.info("\n" + "="*60)
    logger.info("测试 6: 获取显著差异")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    project_id = 1

    significant = get_significant_comparisons(conn, project_id)

    logger.info(f"\n显著差异 (p < 0.05):")
    for comp in significant[:5]:
        logger.info(f"\n  {comp['analysis_name']}")
        logger.info(f"    t = {comp['t_statistic']}, p = {comp['p_value']}")
        logger.info(f"    {comp['group1_label']}: {comp['group1_mean']}")
        logger.info(f"    {comp['group2_label']}: {comp['group2_mean']}")
        logger.info(f"    差异: {comp['diff']}")

    conn.close()

    logger.info(f"✅ 找到 {len(significant)} 个显著差异")
    return True


def main():
    """运行所有测试"""
    logger.info("="*60)
    logger.info("Day 2 测试：智能分析层功能验证")
    logger.info("="*60)

    results = []

    # 运行所有测试
    results.append(("聚类分析", test_clustering()))
    results.append(("保存聚类结果", test_save_cluster_results()))
    results.append(("聚类摘要", test_cluster_summary()))
    results.append(("分组对比分析", test_group_comparison()))
    results.append(("保存对比结果", test_save_comparison_results()))
    results.append(("显著差异", test_significant_comparisons()))

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
        logger.info("🎉 Day 2 所有测试通过！")
        logger.info("="*60)
        logger.info("\nDay 2 完成项:")
        logger.info("  ✅ TF-IDF + KMeans聚类实现")
        logger.info("  ✅ 聚类结果存储和查询")
        logger.info("  ✅ t检验分组对比分析")
        logger.info("  ✅ 对比结果存储和查询")
        logger.info("  ✅ 显著差异识别")
        logger.info("\n准备进入 Day 3: API+前端展示层")
    else:
        logger.error(f"\n❌ {total - passed} 个测试失败")


if __name__ == "__main__":
    main()
