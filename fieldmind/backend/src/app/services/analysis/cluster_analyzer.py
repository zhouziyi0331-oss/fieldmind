"""
聚类分析器

基于TF-IDF + KMeans实现文本聚类：
1. 提取TF-IDF特征向量
2. KMeans聚类
3. 提取每个聚类的代表性关键词
4. 保存聚类结果到数据库
"""

import numpy as np
import logging
import jieba
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def cluster_chunks(chunks: List[str], n_clusters: int = 3) -> Dict[str, Any]:
    """
    基于TF-IDF + KMeans聚类

    Args:
        chunks: 文本列表
        n_clusters: 聚类数量

    Returns:
        {
            'labels': [0, 1, 2, ...],  # 每个chunk的聚类标签
            'cluster_keywords': {0: ['词1', '词2'], ...},  # 每个聚类的关键词
            'n_clusters': 3,
            'cluster_sizes': [10, 15, 8]  # 每个聚类的大小
        }
    """
    if not chunks or len(chunks) < n_clusters:
        logger.warning(f"chunks数量({len(chunks)})少于聚类数({n_clusters})")
        return {
            'labels': list(range(len(chunks))),
            'cluster_keywords': {},
            'n_clusters': 0,
            'cluster_sizes': []
        }

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans

        # 使用jieba分词器
        def jieba_tokenizer(text):
            return list(jieba.cut(text))

        # 1. 提取TF-IDF特征
        logger.info("提取TF-IDF特征...")
        vectorizer = TfidfVectorizer(
            max_features=500,
            tokenizer=jieba_tokenizer,
            lowercase=False,
            token_pattern=None
        )

        X = vectorizer.fit_transform(chunks)
        feature_names = vectorizer.get_feature_names_out()

        # 2. KMeans聚类
        logger.info(f"执行KMeans聚类（k={n_clusters}）...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        # 3. 提取每个聚类的关键词
        logger.info("提取聚类关键词...")
        cluster_keywords = {}
        cluster_sizes = []

        for i in range(n_clusters):
            # 聚类中心
            center = kmeans.cluster_centers_[i]

            # Top-10关键词
            top_indices = np.argsort(center)[::-1][:10]
            keywords = [
                feature_names[idx] for idx in top_indices
                if idx < len(feature_names) and center[idx] > 0
            ]
            cluster_keywords[i] = keywords

            # 聚类大小
            cluster_size = np.sum(labels == i)
            cluster_sizes.append(int(cluster_size))

        logger.info(f"✅ 聚类完成，聚类大小: {cluster_sizes}")

        return {
            'labels': labels.tolist(),
            'cluster_keywords': cluster_keywords,
            'n_clusters': n_clusters,
            'cluster_sizes': cluster_sizes
        }

    except ImportError:
        logger.error("sklearn未安装，无法执行聚类")
        return {
            'labels': [0] * len(chunks),
            'cluster_keywords': {0: []},
            'n_clusters': 1,
            'cluster_sizes': [len(chunks)]
        }

    except Exception as e:
        logger.error(f"聚类失败: {e}")
        return {
            'labels': list(range(len(chunks))),
            'cluster_keywords': {},
            'n_clusters': 0,
            'cluster_sizes': []
        }


def save_cluster_results(
    conn,
    project_id: int,
    chunk_ids: List[int],
    labels: List[int],
    cluster_keywords: Dict[int, List[str]]
) -> int:
    """
    保存聚类结果到数据库

    Args:
        conn: 数据库连接
        project_id: 项目ID
        chunk_ids: chunk ID列表
        labels: 聚类标签列表
        cluster_keywords: 聚类关键词字典

    Returns:
        保存的记录数
    """
    import json

    cursor = conn.cursor()
    saved_count = 0

    try:
        # 清空该项目的旧聚类结果
        cursor.execute("""
            DELETE FROM cluster_results WHERE project_id = ?
        """, (project_id,))

        # 插入新结果
        for chunk_id, label in zip(chunk_ids, labels):
            keywords_json = json.dumps(
                cluster_keywords.get(label, []),
                ensure_ascii=False
            )

            cursor.execute("""
                INSERT INTO cluster_results
                (project_id, chunk_id, cluster_label, cluster_keywords, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                project_id,
                chunk_id,
                label,
                keywords_json,
                datetime.utcnow().isoformat()
            ))

            saved_count += 1

        conn.commit()
        logger.info(f"✅ 保存了 {saved_count} 条聚类结果")
        return saved_count

    except Exception as e:
        logger.error(f"保存聚类结果失败: {e}")
        conn.rollback()
        return 0


def get_cluster_summary(conn, project_id: int) -> Dict[str, Any]:
    """
    获取项目的聚类摘要

    Args:
        conn: 数据库连接
        project_id: 项目ID

    Returns:
        聚类摘要信息
    """
    import json

    cursor = conn.cursor()

    try:
        # 获取聚类分布
        cursor.execute("""
            SELECT cluster_label, COUNT(*) as count, cluster_keywords
            FROM cluster_results
            WHERE project_id = ?
            GROUP BY cluster_label
            ORDER BY cluster_label
        """, (project_id,))

        clusters = []
        for row in cursor.fetchall():
            label, count, keywords_json = row
            keywords = json.loads(keywords_json) if keywords_json else []

            clusters.append({
                'label': label,
                'count': count,
                'keywords': keywords[:5]  # 只显示前5个关键词
            })

        total_chunks = sum(c['count'] for c in clusters)

        # 计算百分比
        for cluster in clusters:
            cluster['percentage'] = round(cluster['count'] / total_chunks * 100, 1) if total_chunks > 0 else 0

        return {
            'project_id': project_id,
            'total_chunks': total_chunks,
            'n_clusters': len(clusters),
            'clusters': clusters
        }

    except Exception as e:
        logger.error(f"获取聚类摘要失败: {e}")
        return {
            'project_id': project_id,
            'total_chunks': 0,
            'n_clusters': 0,
            'clusters': []
        }
