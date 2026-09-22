"""
Document Chunks Quantification API - 文本块量化指标 API

提供量化指标的查询和统计功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.core.database import get_db
from sqlalchemy import text
from app.schemas.response import success_response, error_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chunks", tags=["chunks"])


@router.get("/{chunk_id}/metrics/")
async def get_chunk_metrics(
    chunk_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个chunk的量化指标

    返回7个量化指标：
    - word_count: 字数
    - sentence_count: 句数
    - exclamation_count: 感叹号数量
    - emotion_polarity: 情感极性（-1到1）
    - subjectivity: 主观性（0到1）
    - emotion_word_density: 情绪词密度
    - avg_word_length: 平均词长
    """
    try:
        query = text("""
            SELECT
                chunk_id,
                text,
                word_count,
                sentence_count,
                exclamation_count,
                emotion_polarity,
                subjectivity,
                emotion_word_density,
                avg_word_length
            FROM document_chunks
            WHERE chunk_id = :chunk_id
        """)

        result = db.execute(query, {'chunk_id': chunk_id}).fetchone()

        if not result:
            return error_response(
                code="CHUNK_NOT_FOUND",
                message="Chunk not found"
            )

        return success_response(
            data={
                'chunk_id': result[0],
                'text': result[1],
                'metrics': {
                    'word_count': result[2],
                    'sentence_count': result[3],
                    'exclamation_count': result[4],
                    'emotion_polarity': result[5],
                    'subjectivity': result[6],
                    'emotion_word_density': result[7],
                    'avg_word_length': result[8]
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chunk metrics: {e}")
        return error_response(
            code="GET_METRICS_FAILED",
            message=str(e)
        )


@router.get("/document/{document_id}/metrics/")
async def get_document_chunks_metrics(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档所有chunks的量化指标
    """
    try:
        query = text("""
            SELECT
                chunk_id,
                chunk_index,
                text,
                word_count,
                sentence_count,
                exclamation_count,
                emotion_polarity,
                subjectivity,
                emotion_word_density,
                avg_word_length
            FROM document_chunks
            WHERE document_id = :document_id
            ORDER BY chunk_index
        """)

        results = db.execute(query, {'document_id': document_id}).fetchall()

        if not results:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found or no chunks"
            )

        chunks = []
        for row in results:
            chunks.append({
                'chunk_id': row[0],
                'chunk_index': row[1],
                'text': row[2][:100] + '...' if len(row[2]) > 100 else row[2],  # 预览
                'metrics': {
                    'word_count': row[3],
                    'sentence_count': row[4],
                    'exclamation_count': row[5],
                    'emotion_polarity': row[6],
                    'subjectivity': row[7],
                    'emotion_word_density': row[8],
                    'avg_word_length': row[9]
                }
            })

        return success_response(
            data={
                'document_id': document_id,
                'total_chunks': len(chunks),
                'chunks': chunks
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunks metrics: {e}")
        return error_response(
            code="GET_DOCUMENT_METRICS_FAILED",
            message=str(e)
        )


@router.get("/document/{document_id}/metrics/summary/")
async def get_document_metrics_summary(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档的量化指标统计摘要

    返回平均值、最大值、最小值等统计数据
    """
    try:
        query = text("""
            SELECT
                COUNT(*) as total_chunks,
                AVG(word_count) as avg_word_count,
                AVG(sentence_count) as avg_sentence_count,
                SUM(exclamation_count) as total_exclamations,
                AVG(emotion_polarity) as avg_emotion,
                MIN(emotion_polarity) as min_emotion,
                MAX(emotion_polarity) as max_emotion,
                AVG(subjectivity) as avg_subjectivity,
                AVG(emotion_word_density) as avg_emotion_density,
                AVG(avg_word_length) as avg_word_len
            FROM document_chunks
            WHERE document_id = :document_id
        """)

        result = db.execute(query, {'document_id': document_id}).fetchone()

        if not result or result[0] == 0:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found or no chunks"
            )

        return success_response(
            data={
                'document_id': document_id,
                'summary': {
                    'total_chunks': result[0],
                    'avg_word_count': round(result[1], 2) if result[1] else 0,
                    'avg_sentence_count': round(result[2], 2) if result[2] else 0,
                    'total_exclamations': result[3] or 0,
                    'emotion': {
                        'average': round(result[4], 3) if result[4] else 0,
                        'min': round(result[5], 3) if result[5] else 0,
                        'max': round(result[6], 3) if result[6] else 0,
                        'range': round(result[6] - result[5], 3) if result[5] and result[6] else 0
                    },
                    'avg_subjectivity': round(result[7], 3) if result[7] else 0,
                    'avg_emotion_density': round(result[8], 4) if result[8] else 0,
                    'avg_word_length': round(result[9], 2) if result[9] else 0
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document metrics summary: {e}")
        return error_response(
            code="GET_SUMMARY_FAILED",
            message=str(e)
        )


@router.get("/document/{document_id}/emotion-distribution/")
async def get_emotion_distribution(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    获取文档的情感分布

    将chunk分为：负面、中性、正面三类
    """
    try:
        query = text("""
            SELECT
                CASE
                    WHEN emotion_polarity < -0.3 THEN 'negative'
                    WHEN emotion_polarity > 0.3 THEN 'positive'
                    ELSE 'neutral'
                END as emotion_category,
                COUNT(*) as count
            FROM document_chunks
            WHERE document_id = :document_id
            GROUP BY emotion_category
        """)

        results = db.execute(query, {'document_id': document_id}).fetchall()

        if not results:
            return error_response(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found"
            )

        distribution = {
            'negative': 0,
            'neutral': 0,
            'positive': 0
        }

        for row in results:
            distribution[row[0]] = row[1]

        total = sum(distribution.values())

        return success_response(
            data={
                'document_id': document_id,
                'distribution': distribution,
                'percentages': {
                    'negative': round(distribution['negative'] / total * 100, 1) if total > 0 else 0,
                    'neutral': round(distribution['neutral'] / total * 100, 1) if total > 0 else 0,
                    'positive': round(distribution['positive'] / total * 100, 1) if total > 0 else 0
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting emotion distribution: {e}")
        return error_response(
            code="GET_DISTRIBUTION_FAILED",
            message=str(e)
        )


@router.get("/search")
async def search_chunks_by_metrics(
    document_id: Optional[str] = None,
    emotion_min: Optional[float] = Query(None, ge=-1, le=1),
    emotion_max: Optional[float] = Query(None, ge=-1, le=1),
    subjectivity_min: Optional[float] = Query(None, ge=0, le=1),
    subjectivity_max: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    按量化指标搜索chunks

    参数：
    - emotion_min: 最小情感极性
    - emotion_max: 最大情感极性
    - subjectivity_min: 最小主观性
    - subjectivity_max: 最大主观性
    """
    try:
        conditions = []
        params = {}

        if document_id:
            conditions.append("document_id = :document_id")
            params['document_id'] = document_id

        if emotion_min is not None:
            conditions.append("emotion_polarity >= :emotion_min")
            params['emotion_min'] = emotion_min

        if emotion_max is not None:
            conditions.append("emotion_polarity <= :emotion_max")
            params['emotion_max'] = emotion_max

        if subjectivity_min is not None:
            conditions.append("subjectivity >= :subjectivity_min")
            params['subjectivity_min'] = subjectivity_min

        if subjectivity_max is not None:
            conditions.append("subjectivity <= :subjectivity_max")
            params['subjectivity_max'] = subjectivity_max

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query_text = f"""
            SELECT
                chunk_id,
                document_id,
                text,
                emotion_polarity,
                subjectivity,
                word_count
            FROM document_chunks
            WHERE {where_clause}
            ORDER BY chunk_index
            LIMIT :limit
        """

        params['limit'] = limit

        results = db.execute(text(query_text), params).fetchall()

        chunks = []
        for row in results:
            chunks.append({
                'chunk_id': row[0],
                'document_id': row[1],
                'text': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                'emotion_polarity': round(row[3], 3) if row[3] else None,
                'subjectivity': round(row[4], 3) if row[4] else None,
                'word_count': row[5]
            })

        return success_response(
            data={
                'total_results': len(chunks),
                'chunks': chunks,
                'filters': {
                    'emotion_min': emotion_min,
                    'emotion_max': emotion_max,
                    'subjectivity_min': subjectivity_min,
                    'subjectivity_max': subjectivity_max
                }
            }
        )

    except Exception as e:
        logger.error(f"Error searching chunks by metrics: {e}")
        return error_response(
            code="SEARCH_CHUNKS_FAILED",
            message=str(e)
        )
