"""
Topic Clustering Service - 主题聚类服务

功能：
1. 使用 KMeans 对 chunks 进行无监督聚类
2. 自动发现主题（不需要预先定义标签）
3. 为每个聚类提取 Top 关键词作为主题标签
4. 可选：将聚类映射到业务维度
"""

import logging
import sqlite3
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import jieba

from app.core.database import get_sqlite_database_path

logger = logging.getLogger(__name__)


class TopicClusteringService:
    """主题聚类服务"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化聚类服务

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or get_sqlite_database_path()

        # 停用词
        self.stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '来', '个', '他', '她', '它', '们', '得', '地', '为',
            '以', '将', '于', '对', '与', '及', '而', '或', '等', '从', '被', '把', '给',
            '但', '可以', '如果', '因为', '所以', '这样', '那样', '什么', '怎么', '多',
            '还', '比', '最', '更', '非常', '太', '已经', '已', '能', '过', '又', '再'
        ])

        # 业务维度关键词
        self.dimension_keywords = {
            '衣': ['衣', '服装', '服饰', '穿戴', '刺绣', '织布', '染色', '蜡染', '蓝染', '衣料', '布匹'],
            '食': ['食', '吃', '饭', '米', '糯', '酒', '茶', '菜', '耕种', '收获', '粮食', '作物'],
            '住': ['住', '房', '屋', '家', '宅', '村', '寨', '楼', '木结构', '吊脚楼', '瓦房'],
            '行': ['行', '路', '交通', '外出', '打工', '运输', '车', '徒步', '山路', '桥梁'],
            '民俗': ['民俗', '节日', '节庆', '六月六', '三月三', '婚俗', '丧葬', '祭祀', '祖先'],
            '非遗': ['非遗', '传承', '手艺', '技艺', '山歌', '民歌', '舞蹈', '工艺', '传承人'],
            '物质文化遗产': ['遗产', '古迹', '遗址', '建筑', '文物', '碑刻', '祠堂', '庙宇'],
            '政策': ['政策', '文件', '规定', '补贴', '扶贫', '乡村振兴', '搬迁', '安置'],
            '历史': ['历史', '以前', '过去', '曾经', '解放', '土改', '大集体', '改革开放']
        }

        logger.info("Topic Clustering Service initialized")

    def _tokenize(self, text: str) -> List[str]:
        """分词并过滤停用词"""
        words = jieba.cut(text)
        return [w for w in words if len(w) > 1 and w not in self.stopwords]

    def auto_cluster_chunks(
        self,
        project_id: int,
        n_clusters: Optional[int] = None,
        auto_determine_k: bool = True
    ) -> Dict:
        """
        对项目的 chunks 进行自动聚类

        Args:
            project_id: 项目 ID
            n_clusters: 聚类数量（如果为 None 且 auto_determine_k=True，则自动确定）
            auto_determine_k: 是否自动确定聚类数量

        Returns:
            {
                'n_clusters': int,
                'clusters': [...],
                'silhouette_score': float
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 1. 获取项目的所有 chunks
            cursor.execute("""
                SELECT id, text FROM document_chunks WHERE project_id = ?
            """, (project_id,))

            chunks = cursor.fetchall()
            if len(chunks) < 3:
                logger.warning(f"Not enough chunks for clustering: {len(chunks)}")
                return {
                    'n_clusters': 0,
                    'clusters': [],
                    'error': 'Not enough chunks (minimum 3 required)'
                }

            chunk_ids = [c[0] for c in chunks]
            texts = [c[1] for c in chunks]

            logger.info(f"Clustering {len(chunks)} chunks for project {project_id}")

            # 2. TF-IDF 向量化
            vectorizer = TfidfVectorizer(
                max_features=200,
                tokenizer=self._tokenize,
                lowercase=False
            )

            X = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()

            # 3. 确定聚类数量
            if n_clusters is None and auto_determine_k:
                n_clusters = self._determine_optimal_k(X, max_k=min(10, len(chunks) // 2))
                logger.info(f"Auto-determined optimal k: {n_clusters}")
            elif n_clusters is None:
                n_clusters = min(5, len(chunks) // 3)
                logger.info(f"Using default k: {n_clusters}")

            # 4. KMeans 聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)

            # 5. 计算轮廓系数
            if n_clusters > 1 and len(chunks) > n_clusters:
                silhouette = silhouette_score(X, cluster_labels)
            else:
                silhouette = 0.0

            logger.info(f"Clustering completed with silhouette score: {silhouette:.3f}")

            # 6. 为每个聚类提取 Top 关键词
            clusters = []
            for cluster_id in range(n_clusters):
                # 获取该聚类的所有 chunk indices
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_chunk_ids = [chunk_ids[i] for i in cluster_indices]

                # 计算该聚类的关键词
                cluster_center = kmeans.cluster_centers_[cluster_id]
                top_indices = cluster_center.argsort()[-10:][::-1]
                top_keywords = [feature_names[i] for i in top_indices if cluster_center[i] > 0]

                # 生成聚类标签（用前3个关键词）
                cluster_label = '/'.join(top_keywords[:3])

                # 映射到业务维度（可选）
                dimension = self._map_cluster_to_dimension(top_keywords)

                clusters.append({
                    'cluster_id': int(cluster_id),
                    'cluster_label': cluster_label,
                    'chunk_ids': cluster_chunk_ids,
                    'top_keywords': top_keywords,
                    'chunk_count': len(cluster_chunk_ids),
                    'mapped_dimension': dimension
                })

            # 7. 保存到数据库
            self._save_clusters_to_db(project_id, clusters)

            # 8. 更新 chunks 表的 cluster_id
            for cluster in clusters:
                for chunk_id in cluster['chunk_ids']:
                    cursor.execute("""
                        UPDATE document_chunks SET cluster_id = ? WHERE id = ?
                    """, (cluster['cluster_id'], chunk_id))

            conn.commit()

            return {
                'n_clusters': n_clusters,
                'clusters': clusters,
                'silhouette_score': float(silhouette)
            }

        except Exception as e:
            logger.error(f"Error clustering chunks for project {project_id}: {e}", exc_info=True)
            conn.rollback()
            return {
                'n_clusters': 0,
                'clusters': [],
                'error': str(e)
            }

        finally:
            conn.close()

    def _determine_optimal_k(self, X, min_k: int = 2, max_k: int = 10) -> int:
        """
        使用肘部法则自动确定最佳聚类数量

        Args:
            X: TF-IDF 矩阵
            min_k: 最小聚类数
            max_k: 最大聚类数

        Returns:
            最佳聚类数
        """
        inertias = []
        K_range = range(min_k, max_k + 1)

        for k in K_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            kmeans.fit(X)
            inertias.append(kmeans.inertia_)

        # 简单策略：选择中间值
        # 更复杂的策略可以计算拐点
        optimal_k = K_range[len(K_range) // 2]

        logger.info(f"Inertias: {inertias}")
        logger.info(f"Selected k: {optimal_k}")

        return optimal_k

    def _map_cluster_to_dimension(self, cluster_keywords: List[str]) -> Optional[str]:
        """
        将聚类映射到业务维度

        Args:
            cluster_keywords: 聚类的 Top 关键词

        Returns:
            最佳匹配的业务维度，如果无匹配返回 None
        """
        best_dimension = None
        best_score = 0

        for dimension, keywords in self.dimension_keywords.items():
            # 计算关键词重叠度
            overlap = len(set(cluster_keywords) & set(keywords))
            score = overlap / len(keywords) if len(keywords) > 0 else 0

            if score > best_score:
                best_score = score
                best_dimension = dimension

        # 只有当重叠度 > 0 才返回维度
        if best_score > 0:
            return best_dimension
        else:
            return None

    def _save_clusters_to_db(self, project_id: int, clusters: List[Dict]):
        """
        保存聚类结果到数据库

        Args:
            project_id: 项目 ID
            clusters: 聚类列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 删除该项目的旧聚类结果
            cursor.execute("DELETE FROM topic_clusters WHERE project_id = ?", (project_id,))

            # 插入新聚类结果
            for cluster in clusters:
                cursor.execute("""
                    INSERT INTO topic_clusters (
                        project_id, cluster_id, cluster_label,
                        chunk_ids, top_keywords, chunk_count
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    cluster['cluster_id'],
                    cluster['cluster_label'],
                    json.dumps(cluster['chunk_ids']),
                    json.dumps(cluster['top_keywords'], ensure_ascii=False),
                    cluster['chunk_count']
                ))

            conn.commit()
            logger.info(f"Saved {len(clusters)} clusters for project {project_id}")

        except Exception as e:
            logger.error(f"Error saving clusters: {e}")
            conn.rollback()

        finally:
            conn.close()

    def get_project_clusters(self, project_id: int) -> List[Dict]:
        """
        获取项目的聚类结果

        Args:
            project_id: 项目 ID

        Returns:
            聚类列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT cluster_id, cluster_label, chunk_ids, top_keywords, chunk_count, created_at
                FROM topic_clusters
                WHERE project_id = ?
                ORDER BY cluster_id
            """, (project_id,))

            clusters = []
            for row in cursor.fetchall():
                clusters.append({
                    'cluster_id': row[0],
                    'cluster_label': row[1],
                    'chunk_ids': json.loads(row[2]),
                    'top_keywords': json.loads(row[3]),
                    'chunk_count': row[4],
                    'created_at': row[5]
                })

            return clusters

        finally:
            conn.close()

    def get_cluster_chunks(self, project_id: int, cluster_id: int) -> List[Dict]:
        """
        获取某个聚类的所有 chunks

        Args:
            project_id: 项目 ID
            cluster_id: 聚类 ID

        Returns:
            chunk 列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, text, dimension_category
                FROM document_chunks
                WHERE project_id = ? AND cluster_id = ?
            """, (project_id, cluster_id))

            chunks = []
            for row in cursor.fetchall():
                chunks.append({
                    'chunk_id': row[0],
                    'text': row[1],
                    'dimension_category': row[2]
                })

            return chunks

        finally:
            conn.close()


def create_clustering_service(db_path: Optional[str] = None) -> TopicClusteringService:
    """工厂方法：创建聚类服务"""
    return TopicClusteringService(db_path)
