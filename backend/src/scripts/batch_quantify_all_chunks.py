#!/usr/bin/env python3
"""
批量量化所有chunks

对数据库中所有chunks执行量化分析，填充所有量化字段
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
import logging
from app.services.quantification.quantifier import batch_quantify_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("="*60)
    logger.info("批量量化所有chunks")
    logger.info("="*60)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 获取所有需要量化的chunks
    cursor.execute("""
        SELECT id, text
        FROM document_chunks
        WHERE text IS NOT NULL AND text != ''
    """)

    chunks_data = [{'id': row[0], 'text': row[1]} for row in cursor.fetchall()]

    logger.info(f"找到 {len(chunks_data)} 个chunks需要量化")

    if not chunks_data:
        logger.warning("没有chunks需要量化")
        conn.close()
        return

    # 批量量化
    results = batch_quantify_chunks(chunks_data)

    logger.info(f"\n开始写入数据库...")

    # 写入数据库
    success_count = 0
    for result in results:
        chunk_id = result['chunk_id']
        features = result['features']

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

            success_count += 1

            if success_count % 10 == 0:
                logger.info(f"  已更新 {success_count}/{len(results)} 个chunks")

        except Exception as e:
            logger.error(f"更新chunk {chunk_id} 失败: {e}")

    conn.commit()
    conn.close()

    logger.info(f"\n✅ 批量量化完成")
    logger.info(f"   成功: {success_count}/{len(chunks_data)}")


if __name__ == "__main__":
    main()
