"""
量化分析API路由

提供量化分析相关的API端点：
1. 统计数据
2. 聚类结果
3. 对比分析结果
4. 词云数据
5. 单个chunk量化数据
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import sqlite3
import json
import logging

from app.schemas.response import success_response, error_response
from app.core.database import get_sqlite_database_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/quantification", tags=["quantification"])


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(get_sqlite_database_path())


class QuantificationStats(BaseModel):
    """量化统计数据模型"""
    total_chunks: int
    total_words: int
    avg_emotion_polarity: float
    avg_subjectivity: float
    emotion_distribution: Dict[str, int]


class ClusterInfo(BaseModel):
    """聚类信息模型"""
    label: int
    count: int
    percentage: float
    keywords: List[str]


class ComparisonResult(BaseModel):
    """对比结果模型"""
    analysis_name: str
    group1_label: str
    group2_label: str
    t_statistic: float
    p_value: float
    significant: bool
    group1_mean: float
    group2_mean: float
    diff: float


@router.get("/stats/{project_id}", response_model=QuantificationStats)
async def get_quantification_stats(project_id: int):
    """
    获取项目量化统计数据

    返回：
    - 总chunk数
    - 总字数
    - 平均情感极性
    - 平均主观性
    - 情绪分布
    """
    try:
        conn = _connect()
        cursor = conn.cursor()

        # 总chunk数和总字数
        cursor.execute("""
            SELECT
                COUNT(*) as total_chunks,
                SUM(word_count) as total_words,
                AVG(emotion_polarity) as avg_emotion,
                AVG(subjectivity) as avg_subjectivity
            FROM document_chunks
            WHERE project_id = ? AND word_count IS NOT NULL
        """, (project_id,))

        row = cursor.fetchone()
        total_chunks = row[0] or 0
        total_words = row[1] or 0
        avg_emotion = row[2] or 0.0
        avg_subjectivity = row[3] or 0.5

        # 情绪分布
        cursor.execute("""
            SELECT emotion_label, COUNT(*) as count
            FROM document_chunks
            WHERE project_id = ? AND emotion_label IS NOT NULL
            GROUP BY emotion_label
        """, (project_id,))

        emotion_distribution = {}
        for row in cursor.fetchall():
            label, count = row
            emotion_distribution[label or '中性'] = count

        conn.close()

        return QuantificationStats(
            total_chunks=total_chunks,
            total_words=int(total_words),
            avg_emotion_polarity=round(avg_emotion, 4),
            avg_subjectivity=round(avg_subjectivity, 4),
            emotion_distribution=emotion_distribution
        )

    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clusters/{project_id}/")
async def get_cluster_results(project_id: int):
    """
    获取聚类结果

    返回：
    - 聚类数量
    - 每个聚类的大小和关键词
    """
    try:
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cluster_label, COUNT(*) as count, cluster_keywords
            FROM cluster_results
            WHERE project_id = ?
            GROUP BY cluster_label
            ORDER BY cluster_label
        """, (project_id,))

        clusters = []
        total_chunks = 0

        for row in cursor.fetchall():
            label, count, keywords_json = row
            keywords = json.loads(keywords_json) if keywords_json else []

            clusters.append({
                'label': label,
                'count': count,
                'keywords': keywords[:5]
            })
            total_chunks += count

        # 计算百分比
        for cluster in clusters:
            cluster['percentage'] = round(
                cluster['count'] / total_chunks * 100, 1
            ) if total_chunks > 0 else 0

        conn.close()

        return success_response(
            data={
                'project_id': project_id,
                'n_clusters': len(clusters),
                'total_chunks': total_chunks,
                'clusters': clusters
            }
        )

    except Exception as e:
        logger.error(f"获取聚类结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparisons/{project_id}/")
async def get_comparison_results(
    project_id: int,
    significant_only: bool = Query(False, description="只返回显著差异")
):
    """
    获取分组对比结果

    参数：
    - significant_only: 只返回有显著差异的结果

    返回：
    - 所有对比分析结果
    """
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT *
            FROM comparison_results
            WHERE project_id = ?
        """

        if significant_only:
            query += " AND significant = 1"

        query += " ORDER BY p_value ASC"

        cursor.execute(query, (project_id,))

        results = []
        for row in cursor.fetchall():
            results.append({
                'analysis_name': row['analysis_name'],
                'group1_label': row['group1_label'],
                'group2_label': row['group2_label'],
                't_statistic': row['t_statistic'],
                'p_value': row['p_value'],
                'significant': bool(row['significant']),
                'group1_mean': row['group1_mean'],
                'group2_mean': row['group2_mean'],
                'diff': row['diff']
            })

        conn.close()

        return success_response(
            data={
                'project_id': project_id,
                'count': len(results),
                'comparisons': results
            }
        )

    except Exception as e:
        logger.error(f"获取对比结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wordcloud/{project_id}/")
async def get_wordcloud_data(
    project_id: int,
    top_k: int = Query(50, ge=10, le=200, description="返回Top-K词")
):
    """
    获取TF-IDF词云数据

    返回：
    - 词频统计（用于词云）
    """
    try:
        conn = _connect()
        cursor = conn.cursor()

        # 获取所有chunks的TF-IDF关键词
        cursor.execute("""
            SELECT tfidf_keywords
            FROM document_chunks
            WHERE project_id = ? AND tfidf_keywords IS NOT NULL
        """, (project_id,))

        from collections import Counter
        word_counter = Counter()

        for row in cursor.fetchall():
            keywords_json = row[0]
            if keywords_json:
                try:
                    keywords = json.loads(keywords_json)
                    word_counter.update(keywords)
                except:
                    pass

        conn.close()

        # 获取Top-K
        top_words = word_counter.most_common(top_k)

        return success_response(
            data={
                'project_id': project_id,
                'words': [
                    {'word': word, 'weight': count}
                    for word, count in top_words
                ]
            }
        )

    except Exception as e:
        logger.error(f"获取词云数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunk/{chunk_id}/")
async def get_chunk_quantification(chunk_id: int):
    """
    获取单个chunk的所有量化指标

    返回：
    - chunk的全部量化特征
    """
    try:
        conn = _connect()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, text,
                word_count, sentence_count, paragraph_count,
                avg_word_length, avg_sentence_length,
                emotion_polarity, emotion_intensity, emotion_label,
                subjectivity, objectivity, tone_strength,
                exclamation_count, modal_verb_count,
                emotion_word_density, keyword_density,
                tfidf_keywords, cluster_label
            FROM document_chunks
            WHERE id = ?
        """, (chunk_id,))

        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Chunk not found")

        conn.close()

        return success_response(
            data={
                'chunk_id': row['id'],
                'text': row['text'][:200] + '...' if len(row['text'] or '') > 200 else row['text'],
                'structural': {
                    'word_count': row['word_count'],
                    'sentence_count': row['sentence_count'],
                    'paragraph_count': row['paragraph_count'],
                    'avg_word_length': row['avg_word_length'],
                    'avg_sentence_length': row['avg_sentence_length']
                },
                'emotional': {
                    'polarity': row['emotion_polarity'],
                    'intensity': row['emotion_intensity'],
                    'label': row['emotion_label']
                },
                'style': {
                    'subjectivity': row['subjectivity'],
                    'objectivity': row['objectivity'],
                    'tone_strength': row['tone_strength'],
                    'exclamation_count': row['exclamation_count'],
                    'modal_verb_count': row['modal_verb_count']
                },
                'content': {
                    'emotion_word_density': row['emotion_word_density'],
                    'keyword_density': row['keyword_density'],
                    'tfidf_keywords': json.loads(row['tfidf_keywords']) if row['tfidf_keywords'] else []
                },
                'cluster_label': row['cluster_label']
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取chunk量化数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
