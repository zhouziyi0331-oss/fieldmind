"""
数据分析API - 基于SQL聚合的真实数据分析
不是向量检索，而是结构化查询

核心原则：
1. 所有统计数字来自SQL的COUNT/SUM/AVG
2. 禁止LLM自行推算数字
3. 如果SQL查询无结果，返回"无相关数据"而非编造
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.structured_insight import StructuredInsight, TopicStatistics, EntityStatistics
from app.models.project import ProjectDocument
from app.schemas.response import success_response, error_response

router = APIRouter(tags=["数据分析"])


@router.get("/projects/{project_id}/topic-distribution/")
def get_topic_distribution(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取主题分布 - 基于SQL COUNT

    返回格式：
    {
        "project_id": 1,
        "topics": [
            {"topic": "食", "count": 45, "percentage": 35.7},
            {"topic": "衣", "count": 23, "percentage": 18.3},
            ...
        ],
        "total": 126
    }
    """
    try:
        # SQL聚合查询
        stats = db.query(
            TopicStatistics.topic,
            TopicStatistics.count
        ).filter(
            TopicStatistics.project_id == project_id
        ).order_by(
            desc(TopicStatistics.count)
        ).all()

        if not stats:
            return success_response(
                data={
                    "project_id": project_id,
                    "topics": [],
                    "total": 0
                },
                message="无相关数据"
            )

        total = sum(s.count for s in stats)

        topics = [
            {
                "topic": s.topic,
                "count": s.count,
                "percentage": round(s.count / total * 100, 2)
            }
            for s in stats
        ]

        return success_response(
            data={
                "project_id": project_id,
                "topics": topics,
                "total": total
            }
        )

    except Exception as e:
        return error_response(
            code="QUERY_FAILED",
            message=f"查询失败: {str(e)}"
        )


@router.get("/projects/{project_id}/top-entities/")
def get_top_entities(
    project_id: int,
    entity_type: str = Query("person", description="实体类型: person/location"),
    top_k: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取Top实体（人物/地点） - 基于SQL COUNT

    返回格式：
    {
        "entity_type": "person",
        "entities": [
            {"name": "王大爷", "count": 15},
            {"name": "李婶", "count": 12},
            ...
        ]
    }
    """
    try:
        stats = db.query(
            EntityStatistics.entity_name,
            EntityStatistics.count
        ).filter(
            EntityStatistics.project_id == project_id,
            EntityStatistics.entity_type == entity_type
        ).order_by(
            desc(EntityStatistics.count)
        ).limit(top_k).all()

        if not stats:
            return success_response(
                data={
                    "entity_type": entity_type,
                    "entities": [],
                    "total": 0
                },
                message="无相关数据"
            )

        entities = [
            {"name": s.entity_name, "count": s.count}
            for s in stats
        ]

        return success_response(
            data={
                "entity_type": entity_type,
                "entities": entities,
                "total": len(entities)
            }
        )

    except Exception as e:
        return error_response(
            code="QUERY_FAILED",
            message=f"查询失败: {str(e)}"
        )


@router.get("/projects/{project_id}/word-count-stats/")
def get_word_count_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取字数统计 - 基于SQL SUM/AVG
    """
    try:
        result = db.query(
            func.sum(StructuredInsight.word_count).label('total_words'),
            func.avg(StructuredInsight.word_count).label('avg_words'),
            func.count(StructuredInsight.id).label('total_chunks')
        ).filter(
            StructuredInsight.project_id == project_id
        ).first()

        if not result or result.total_words is None:
            return success_response(
                data={
                    "total_words": 0,
                    "avg_words_per_chunk": 0,
                    "total_chunks": 0
                },
                message="无相关数据"
            )

        return success_response(
            data={
                "total_words": int(result.total_words),
                "avg_words_per_chunk": round(float(result.avg_words), 2),
                "total_chunks": result.total_chunks
            }
        )

    except Exception as e:
        return error_response(
            code="QUERY_FAILED",
            message=f"查询失败: {str(e)}"
        )


@router.get("/projects/{project_id}/timeline-distribution/")
def get_timeline_distribution(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取时间线分布 - 基于SQL GROUP BY
    按文档和时间段统计
    """
    try:
        # 查询所有有时间戳的记录
        records = db.query(
            StructuredInsight.document_id,
            StructuredInsight.start_time,
            StructuredInsight.topics
        ).filter(
            StructuredInsight.project_id == project_id,
            StructuredInsight.start_time.isnot(None)
        ).order_by(
            StructuredInsight.document_id,
            StructuredInsight.start_time
        ).all()

        if not records:
            return success_response(
                data={
                    "documents": [],
                    "total_documents": 0
                },
                message="无时间戳数据"
            )

        # 按文档分组
        doc_timeline = {}
        for record in records:
            doc_id = record.document_id
            if doc_id not in doc_timeline:
                doc_timeline[doc_id] = []

            doc_timeline[doc_id].append({
                "time": round(record.start_time, 2),
                "topics": record.topics.split(',') if record.topics else []
            })

        return success_response(
            data={
                "documents": [
                    {
                        "document_id": doc_id,
                        "timeline": timeline
                    }
                    for doc_id, timeline in doc_timeline.items()
                ],
                "total_documents": len(doc_timeline)
            }
        )

    except Exception as e:
        return error_response(
            code="QUERY_FAILED",
            message=f"查询失败: {str(e)}"
        )


@router.post("/projects/{project_id}/generate-report/")
def generate_report(
    project_id: int,
    report_type: str = Query("overview", description="报告类型: overview/topic/entity"),
    db: Session = Depends(get_db)
):
    """
    生成分析报告 - 反幻觉版本

    核心流程：
    1. 生成facts.json（纯数据，无修饰）
    2. 基于模板直接生成报告（不调用LLM）
    3. 幻觉检测（如果调用了LLM）
    4. 验证通过才返回
    """
    try:
        logger.info(f"📊 生成报告 - 项目{project_id}")

        # 步骤1: 生成事实锚点
        from app.services.facts_anchor import FactsAnchorGenerator
        from app.services.anti_hallucination_report import (
            AntiHallucinationReportGenerator,
            HallucinationDetector
        )

        generator = FactsAnchorGenerator(db)
        facts = generator.generate_facts(project_id)

        # 验证facts有效性
        if not generator.validate_facts(facts):
            return success_response(
                data=None,
                message="该项目尚无结构化数据，无法生成报告。建议：请先上传并处理文档"
            )

        if facts['total_chunks'] == 0:
            return success_response(
                data=None,
                message="该项目尚无结构化数据，无法生成报告。建议：请先上传并处理文档"
            )

        # 步骤2: 生成报告（完全基于模板，最安全）
        logger.info(f"📝 生成报告（模板填充模式）")
        report_text = AntiHallucinationReportGenerator.generate_report_direct(facts)

        # 步骤3: 幻觉检测（即使是模板生成的也检测一遍）
        logger.info(f"🕵️ 执行幻觉检测")
        is_valid, errors = HallucinationDetector.validate_report(report_text, facts)

        if not is_valid:
            # 幻觉拦截 - 返回错误
            logger.error(f"❌ 幻觉检测失败: {errors}")
            return error_response(
                code="HALLUCINATION_DETECTED",
                message="系统检测到生成内容偏离数据源",
                details={
                    "errors": errors,
                    "suggestion": "请尝试缩小提问范围或检查数据总量"
                }
            )

        logger.info(f"✅ 幻觉检测通过")

        # 步骤4: 返回报告
        return success_response(
            data={
                "report": {
                    "type": report_type,
                    "generated_at": facts['generated_at'],
                    "text": report_text,
                    "facts": facts,  # 同时返回原始数据，供前端验证
                    "validation": {
                        "passed": True,
                        "method": "template-based",  # 表明是模板生成，不是LLM
                        "errors": []
                    }
                },
                "metadata": {
                    "total_docs": facts['total_docs'],
                    "total_chunks": facts['total_chunks'],
                    "total_words": facts['total_words']
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"❌ 生成报告失败: {e}")
        logger.error(traceback.format_exc())
        return error_response(
            code="REPORT_GENERATION_FAILED",
            message=f"生成报告失败: {str(e)}"
        )


# 添加logger
import logging
logger = logging.getLogger(__name__)
