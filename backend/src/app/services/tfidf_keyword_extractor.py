"""
TF-IDF Keyword Extractor - TF-IDF 关键词提取器

功能：
1. 从文本中提取 TF-IDF 关键词
2. 批量处理项目的所有 chunks
3. 存储关键词和权重到数据库
"""

import logging
import jieba
import jieba.analyse
from typing import List, Dict, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import sqlite3
import json

from app.core.database import get_sqlite_database_path

logger = logging.getLogger(__name__)


class TFIDFKeywordExtractor:
    """TF-IDF 关键词提取器"""
    def __init__(self, db_path: Optional[str] = None, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        """
        初始化提取器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or get_sqlite_database_path()

        # 停用词列表（中文常见停用词）
        self.stopwords = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
            '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
            '自己', '这', '那', '里', '来', '个', '他', '她', '它', '们', '得', '地', '为',
            '以', '将', '于', '对', '与', '及', '而', '或', '等', '从', '被', '把', '给',
            '但', '可以', '如果', '因为', '所以', '这样', '那样', '什么', '怎么', '多',
            '还', '比', '最', '更', '非常', '太', '已经', '已', '能', '过', '又', '再'
        ])

        logger.info("TF-IDF Keyword Extractor initialized")

    def extract_keywords_for_chunk(self, chunk_id: int, project_id: int, top_n: int = 5) -> List[Dict]:
        """
        为单个 chunk 提取 TF-IDF 关键词

        Args:
            chunk_id: chunk ID
            project_id: 项目 ID
            top_n: 提取前 N 个关键词

        Returns:
            关键词列表，每个元素包含 keyword, tfidf_score, frequency
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 1. 获取当前 chunk 的文本
            cursor.execute("""
                SELECT text FROM document_chunks WHERE id = ?
            """, (chunk_id,))

            result = cursor.fetchone()
            if not result:
                logger.warning(f"Chunk {chunk_id} not found")
                return []

            chunk_text = result[0]

            # 2. 获取该项目所有 chunk 的文本（作为语料库）
            cursor.execute("""
                SELECT id, text FROM document_chunks WHERE project_id = ?
            """, (project_id,))

            corpus = []
            chunk_id_map = {}
            for row in cursor.fetchall():
                cid, text = row
                corpus.append(text)
                chunk_id_map[len(corpus) - 1] = cid

            if len(corpus) == 0:
                logger.warning(f"No chunks found for project {project_id}")
                return []

            # 3. 使用 TF-IDF 计算
            vectorizer = TfidfVectorizer(
                max_features=100,
                tokenizer=self._tokenize,
                lowercase=False,
                stop_words=None  # 我们在 tokenizer 中处理停用词
            )

            tfidf_matrix = vectorizer.fit_transform(corpus)
            feature_names = vectorizer.get_feature_names_out()

            # 4. 获取当前 chunk 的索引
            current_chunk_index = None
            for idx, cid in chunk_id_map.items():
                if cid == chunk_id:
                    current_chunk_index = idx
                    break

            if current_chunk_index is None:
                logger.warning(f"Chunk {chunk_id} not found in corpus")
                return []

            # 5. 获取当前 chunk 的 TF-IDF 向量
            chunk_tfidf = tfidf_matrix[current_chunk_index].toarray()[0]

            # 6. 提取 Top N 关键词
            top_indices = chunk_tfidf.argsort()[-top_n:][::-1]

            keywords = []
            for idx in top_indices:
                if chunk_tfidf[idx] > 0:
                    keyword = feature_names[idx]
                    tfidf_score = float(chunk_tfidf[idx])

                    # 计算词频
                    frequency = chunk_text.count(keyword)

                    keywords.append({
                        'keyword': keyword,
                        'tfidf_score': tfidf_score,
                        'frequency': frequency
                    })

            return keywords

        except Exception as e:
            logger.error(f"Error extracting keywords for chunk {chunk_id}: {e}", exc_info=True)
            return []

        finally:
            conn.close()

    def _tokenize(self, text: str) -> List[str]:
        """
        分词并过滤停用词

        Args:
            text: 原始文本

        Returns:
            分词后的词列表
        """
        # 使用 jieba 分词
        words = jieba.cut(text)

        # 过滤停用词和单字符
        filtered_words = [
            w for w in words
            if len(w) > 1 and w not in self.stopwords
        ]

        return filtered_words

    def save_keywords_to_db(self, chunk_id: int, keywords: List[Dict]):
        """
        保存关键词到数据库

        Args:
            chunk_id: chunk ID
            keywords: 关键词列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 先删除已有的关键词
            cursor.execute("DELETE FROM chunk_keywords WHERE chunk_id = ?", (chunk_id,))

            # 插入新关键词
            for i, kw in enumerate(keywords):
                is_top = 1 if i < 3 else 0  # 前3个标记为 Top 关键词

                cursor.execute("""
                    INSERT INTO chunk_keywords (chunk_id, keyword, tfidf_score, frequency, is_top)
                    VALUES (?, ?, ?, ?, ?)
                """, (chunk_id, kw['keyword'], kw['tfidf_score'], kw['frequency'], is_top))

            conn.commit()
            logger.info(f"Saved {len(keywords)} keywords for chunk {chunk_id}")

        except Exception as e:
            logger.error(f"Error saving keywords for chunk {chunk_id}: {e}")
            conn.rollback()

        finally:
            conn.close()

    def batch_extract_for_project(self, project_id: int, top_n: int = 5):
        """
        批量提取项目的所有 chunks 的关键词

        Args:
            project_id: 项目 ID
            top_n: 每个 chunk 提取的关键词数量
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 获取项目的所有 chunk IDs
            cursor.execute("""
                SELECT id FROM document_chunks WHERE project_id = ?
            """, (project_id,))

            chunk_ids = [row[0] for row in cursor.fetchall()]

            logger.info(f"Extracting keywords for {len(chunk_ids)} chunks in project {project_id}")

            # 批量提取
            for i, chunk_id in enumerate(chunk_ids):
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(chunk_ids)}")

                keywords = self.extract_keywords_for_chunk(chunk_id, project_id, top_n)
                if keywords:
                    self.save_keywords_to_db(chunk_id, keywords)

            logger.info(f"✅ Completed keyword extraction for project {project_id}")

        except Exception as e:
            logger.error(f"Error in batch extraction for project {project_id}: {e}")

        finally:
            conn.close()

    def get_chunk_keywords(self, chunk_id: int, top_only: bool = False) -> List[Dict]:
        """
        获取 chunk 的关键词

        Args:
            chunk_id: chunk ID
            top_only: 是否只返回 Top 关键词

        Returns:
            关键词列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            if top_only:
                cursor.execute("""
                    SELECT keyword, tfidf_score, frequency
                    FROM chunk_keywords
                    WHERE chunk_id = ? AND is_top = 1
                    ORDER BY tfidf_score DESC
                """, (chunk_id,))
            else:
                cursor.execute("""
                    SELECT keyword, tfidf_score, frequency
                    FROM chunk_keywords
                    WHERE chunk_id = ?
                    ORDER BY tfidf_score DESC
                """, (chunk_id,))

            keywords = []
            for row in cursor.fetchall():
                keywords.append({
                    'keyword': row[0],
                    'tfidf_score': row[1],
                    'frequency': row[2]
                })

            return keywords

        finally:
            conn.close()

    def get_project_top_keywords(self, project_id: int, top_n: int = 50) -> List[Dict]:
        """
        获取项目的 Top N 关键词（聚合所有 chunks）

        Args:
            project_id: 项目 ID
            top_n: 返回前 N 个关键词

        Returns:
            关键词列表（按 TF-IDF 总和排序）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT kw.keyword, SUM(kw.tfidf_score) as total_score, SUM(kw.frequency) as total_freq
                FROM chunk_keywords kw
                JOIN document_chunks c ON kw.chunk_id = c.id
                WHERE c.project_id = ?
                GROUP BY kw.keyword
                ORDER BY total_score DESC
                LIMIT ?
            """, (project_id, top_n))

            keywords = []
            for row in cursor.fetchall():
                keywords.append({
                    'keyword': row[0],
                    'total_tfidf_score': row[1],
                    'total_frequency': row[2]
                })

            return keywords

        finally:
            conn.close()


def create_extractor(db_path: Optional[str] = None) -> TFIDFKeywordExtractor:
    """工厂方法：创建提取器"""
    return TFIDFKeywordExtractor(db_path)
