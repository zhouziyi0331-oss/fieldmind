"""
缩影数据可视化 API
Summary Visualization API

功能：
1. 生成关键词云图数据
2. 生成维度分布图数据
3. 生成时间线数据
4. 生成文档关联网络图数据

前端使用 ECharts/D3.js 渲染
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Dict, Any
import json
import logging
from collections import Counter

from app.core.database import get_db
from app.schemas.response import success_response

router = APIRouter(prefix="/file-summaries/visualize", tags=["Visualize Summaries"])
logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/wordcloud")
async def get_wordcloud_data(
    project_id: int,
    top_n: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取关键词云图数据

    返回格式（ECharts wordCloud）：
    {
        "words": [
            {"name": "山歌", "value": 156},
            {"name": "传承", "value": 89},
            ...
        ]
    }
    """

    try:
        # 查询所有缩影的关键词
        results = db.execute(text("""
            SELECT top_keywords
            FROM file_summaries
            WHERE project_id = :project_id AND status = 'done'
        """), {'project_id': project_id}).fetchall()

        # 聚合关键词频次
        word_freq = Counter()

        for row in results:
            if row[0]:
                keywords = json.loads(row[0])
                for kw in keywords:
                    word = kw.get('word', '')
                    count = kw.get('count', 1)
                    if word:
                        word_freq[word] += count

        # 取 Top N
        top_words = word_freq.most_common(top_n)

        # 转换为 ECharts 格式
        words = [
            {"name": word, "value": count}
            for word, count in top_words
        ]

        logger.info(f"生成词云数据：{len(words)} 个关键词")

        return success_response(data={
            'words': words,
            'total_keywords': len(word_freq),
            'total_documents': len(results)
        })

    except Exception as e:
        logger.error(f"生成词云数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/dimension-distribution")
async def get_dimension_distribution(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取维度分布图数据

    返回格式（ECharts pie）：
    {
        "dimensions": [
            {"name": "非遗", "value": 45},
            {"name": "民俗", "value": 32},
            ...
        ]
    }
    """

    try:
        # 查询维度分布
        results = db.execute(text("""
            SELECT primary_dimension, COUNT(*) as count
            FROM file_summaries
            WHERE project_id = :project_id
              AND status = 'done'
              AND primary_dimension IS NOT NULL
            GROUP BY primary_dimension
            ORDER BY count DESC
        """), {'project_id': project_id}).fetchall()

        # 转换为 ECharts 格式
        dimensions = [
            {"name": row[0], "value": row[1]}
            for row in results
        ]

        # 计算总数和百分比
        total = sum(d['value'] for d in dimensions)
        for d in dimensions:
            d['percentage'] = round((d['value'] / total) * 100, 1) if total > 0 else 0

        logger.info(f"生成维度分布数据：{len(dimensions)} 个维度")

        return success_response(data={
            'dimensions': dimensions,
            'total_documents': total
        })

    except Exception as e:
        logger.error(f"生成维度分布数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/timeline")
async def get_timeline_data(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取时间线数据

    返回格式：
    {
        "timeline": [
            {"date": "2023-01", "count": 12, "documents": [...]},
            {"date": "2023-02", "count": 8, "documents": [...]},
            ...
        ]
    }
    """

    try:
        # 查询有时间信息的缩影
        results = db.execute(text("""
            SELECT
                s.time_start,
                s.document_id,
                s.one_line_summary,
                d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.project_id = :project_id
              AND s.status = 'done'
              AND s.time_start IS NOT NULL
            ORDER BY s.time_start
        """), {'project_id': project_id}).fetchall()

        # 按月份聚合
        timeline_dict = {}

        for row in results:
            time_start = row[0]
            document_id = row[1]
            summary = row[2]
            filename = row[3]

            # 提取年月（如：2023-01）
            try:
                if len(time_start) >= 7:
                    month_key = time_start[:7]
                else:
                    month_key = time_start

                if month_key not in timeline_dict:
                    timeline_dict[month_key] = {
                        'date': month_key,
                        'count': 0,
                        'documents': []
                    }

                timeline_dict[month_key]['count'] += 1
                timeline_dict[month_key]['documents'].append({
                    'document_id': document_id,
                    'title': filename,
                    'summary': summary
                })

            except Exception as e:
                logger.debug(f"解析时间失败: {time_start}, {e}")
                continue

        # 转换为列表并排序
        timeline = sorted(timeline_dict.values(), key=lambda x: x['date'])

        logger.info(f"生成时间线数据：{len(timeline)} 个时间点")

        return success_response(data={
            'timeline': timeline,
            'total_documents': len(results)
        })

    except Exception as e:
        logger.error(f"生成时间线数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/network")
async def get_network_data(
    project_id: int,
    min_similarity: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    获取文档关联网络图数据

    返回格式（ECharts graph）：
    {
        "nodes": [
            {"id": "1", "name": "王大爷访谈", "symbolSize": 50, "category": 0},
            ...
        ],
        "links": [
            {"source": "1", "target": "2", "value": 0.89},
            ...
        ],
        "categories": [
            {"name": "非遗"},
            {"name": "民俗"},
            ...
        ]
    }
    """

    try:
        # 查询所有缩影
        results = db.execute(text("""
            SELECT
                s.document_id,
                s.one_line_summary,
                s.primary_dimension,
                s.related_documents,
                s.word_count,
                d.original_filename
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.project_id = :project_id AND s.status = 'done'
        """), {'project_id': project_id}).fetchall()

        # 构建节点和边
        nodes = []
        links = []
        categories_set = set()

        # 维度到分类索引的映射
        dimension_to_category = {}

        for row in results:
            doc_id = str(row[0])
            summary = row[1]
            dimension = row[2]
            related_docs = json.loads(row[3]) if row[3] else []
            word_count = row[4]
            filename = row[5]

            # 添加分类
            if dimension and dimension not in dimension_to_category:
                dimension_to_category[dimension] = len(dimension_to_category)
                categories_set.add(dimension)

            # 节点（节点大小根据字数）
            nodes.append({
                'id': doc_id,
                'name': filename[:20] + ('...' if len(filename) > 20 else ''),
                'symbolSize': min(max(word_count / 100, 20), 80),  # 20-80
                'category': dimension_to_category.get(dimension, 0),
                'summary': summary,
                'dimension': dimension
            })

            # 边（关联文档）
            for rel_doc in related_docs:
                similarity = rel_doc.get('similarity', 0)
                if similarity >= min_similarity:
                    links.append({
                        'source': doc_id,
                        'target': str(rel_doc['document_id']),
                        'value': similarity,
                        'lineStyle': {
                            'width': similarity * 3,  # 相似度越高线越粗
                            'opacity': similarity
                        }
                    })

        # 分类列表
        categories = [{'name': dim} for dim in sorted(categories_set)]

        logger.info(f"生成网络图数据：{len(nodes)} 个节点，{len(links)} 条边")

        return success_response(data={
            'nodes': nodes,
            'links': links,
            'categories': categories
        })

    except Exception as e:
        logger.error(f"生成网络图数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/emotion-trend")
async def get_emotion_trend(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取情感趋势数据

    返回格式（ECharts line）：
    {
        "dates": ["2023-01", "2023-02", ...],
        "values": [0.2, -0.1, 0.5, ...]
    }
    """

    try:
        # 查询情感数据（按生成时间排序）
        results = db.execute(text("""
            SELECT
                DATE(generated_at) as date,
                AVG(emotion_polarity) as avg_emotion
            FROM file_summaries
            WHERE project_id = :project_id
              AND status = 'done'
              AND emotion_polarity IS NOT NULL
            GROUP BY DATE(generated_at)
            ORDER BY date
        """), {'project_id': project_id}).fetchall()

        # 转换为 ECharts 格式
        dates = [str(row[0]) for row in results]
        values = [round(float(row[1]), 2) for row in results]

        logger.info(f"生成情感趋势数据：{len(dates)} 个时间点")

        return success_response(data={
            'dates': dates,
            'values': values
        })

    except Exception as e:
        logger.error(f"生成情感趋势数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/stats-overview")
async def get_stats_overview(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取统计概览数据（用于仪表盘）

    返回：
    - 总文档数
    - 维度分布
    - 平均字数
    - 情感分布
    - Top 关键词
    """

    try:
        # 总文档数和平均字数
        basic_stats = db.execute(text("""
            SELECT
                COUNT(*) as total,
                AVG(word_count) as avg_words,
                SUM(word_count) as total_words
            FROM file_summaries
            WHERE project_id = :project_id AND status = 'done'
        """), {'project_id': project_id}).fetchone()

        # 维度分布
        dimension_stats = db.execute(text("""
            SELECT primary_dimension, COUNT(*) as count
            FROM file_summaries
            WHERE project_id = :project_id AND status = 'done'
            GROUP BY primary_dimension
            ORDER BY count DESC
            LIMIT 5
        """), {'project_id': project_id}).fetchall()

        # 情感分布
        emotion_stats = db.execute(text("""
            SELECT
                SUM(CASE WHEN emotion_polarity > 0.2 THEN 1 ELSE 0 END) as positive,
                SUM(CASE WHEN emotion_polarity BETWEEN -0.2 AND 0.2 THEN 1 ELSE 0 END) as neutral,
                SUM(CASE WHEN emotion_polarity < -0.2 THEN 1 ELSE 0 END) as negative
            FROM file_summaries
            WHERE project_id = :project_id
              AND status = 'done'
              AND emotion_polarity IS NOT NULL
        """), {'project_id': project_id}).fetchone()

        # Top 关键词
        keyword_results = db.execute(text("""
            SELECT top_keywords
            FROM file_summaries
            WHERE project_id = :project_id AND status = 'done'
        """), {'project_id': project_id}).fetchall()

        word_freq = Counter()
        for row in keyword_results:
            if row[0]:
                keywords = json.loads(row[0])
                for kw in keywords:
                    word = kw.get('word', '')
                    count = kw.get('count', 1)
                    if word:
                        word_freq[word] += count

        top_keywords = [
            {"word": word, "count": count}
            for word, count in word_freq.most_common(10)
        ]

        return success_response(data={
            'total_documents': basic_stats[0] or 0,
            'avg_word_count': int(basic_stats[1]) if basic_stats[1] else 0,
            'total_words': basic_stats[2] or 0,
            'dimension_distribution': [
                {"name": row[0], "count": row[1]}
                for row in dimension_stats
            ],
            'emotion_distribution': {
                'positive': emotion_stats[0] or 0 if emotion_stats else 0,
                'neutral': emotion_stats[1] or 0 if emotion_stats else 0,
                'negative': emotion_stats[2] or 0 if emotion_stats else 0
            },
            'top_keywords': top_keywords
        })

    except Exception as e:
        logger.error(f"获取统计概览失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
