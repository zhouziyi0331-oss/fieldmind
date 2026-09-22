"""
文件缩影 API 路由
File Summaries API Routes

功能：
1. 获取项目的所有缩影（支持搜索和筛选）
2. 获取单个文档的缩影
3. 重新生成文档缩影
4. 获取维度列表（用于筛选）

作者: FieldMind Team
创建时间: 2024-09-14
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import json
import logging

from app.core.database import get_db
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/file-summaries", tags=["File Summaries"])
logger = logging.getLogger(__name__)


@router.get("/projects/{project_id}/summaries")
async def list_summaries(
    project_id: int,
    skip: int = Query(0, ge=0, description="分页偏移量"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    q: Optional[str] = Query(None, description="关键词搜索（使用 FTS5）"),
    dimension: Optional[str] = Query(None, description="维度筛选（如：非遗）"),
    status: Optional[str] = Query(None, description="状态筛选（done/pending/error）"),
    db: Session = Depends(get_db)
):
    """
    获取项目的所有缩影卡片

    支持搜索和筛选：
    - q: 关键词搜索（使用 FTS5 全文搜索）
    - dimension: 维度筛选（如：非遗、民俗、历史）
    - status: 状态筛选（done/pending/error）

    返回格式：
    {
        "success": true,
        "data": {
            "total": 100,
            "summaries": [...],
            "skip": 0,
            "limit": 50
        }
    }
    """

    try:
        logger.info(f"查询项目 {project_id} 的缩影列表: q={q}, dimension={dimension}, status={status}")

        # 构建查询
        if q:
            # 使用 FTS5 全文搜索
            query = text("""
                SELECT s.*, d.original_filename, d.file_type, d.file_size
                FROM file_summaries s
                JOIN file_summaries_fts f ON s.id = f.rowid
                JOIN project_documents d ON s.document_id = d.id
                WHERE f.file_summaries_fts MATCH :q
                  AND s.project_id = :project_id
                  AND (:dimension IS NULL OR s.primary_dimension = :dimension)
                  AND (:status IS NULL OR s.status = :status)
                ORDER BY s.created_at DESC
                LIMIT :limit OFFSET :skip
            """)

            params = {
                'q': q,
                'project_id': project_id,
                'dimension': dimension,
                'status': status,
                'limit': limit,
                'skip': skip
            }
        else:
            # 普通查询
            query = text("""
                SELECT s.*, d.original_filename, d.file_type, d.file_size
                FROM file_summaries s
                JOIN project_documents d ON s.document_id = d.id
                WHERE s.project_id = :project_id
                  AND (:dimension IS NULL OR s.primary_dimension = :dimension)
                  AND (:status IS NULL OR s.status = :status)
                ORDER BY s.created_at DESC
                LIMIT :limit OFFSET :skip
            """)

            params = {
                'project_id': project_id,
                'dimension': dimension,
                'status': status,
                'limit': limit,
                'skip': skip
            }

        results = db.execute(query, params).fetchall()

        # 转换为字典列表
        summaries = []
        for row in results:
            try:
                summaries.append({
                    'id': row[0],
                    'document_id': row[1],
                    'project_id': row[2],
                    'one_line_summary': row[3],
                    'full_summary': row[4],
                    'top_keywords': json.loads(row[5]) if row[5] else [],
                    'top_entities': json.loads(row[6]) if row[6] else [],
                    'top_topics': json.loads(row[7]) if row[7] else [],
                    'top_events': json.loads(row[8]) if row[8] else [],
                    'word_count': row[9],
                    'chunk_count': row[10],
                    'avg_chunk_length': row[11],
                    'emotion_polarity': row[12],
                    'subjectivity': row[13],
                    'primary_dimension': row[14],
                    'secondary_dimensions': json.loads(row[15]) if row[15] else [],
                    'time_start': row[16],
                    'time_end': row[17],
                    'spatial_context': row[18],
                    'related_documents': json.loads(row[19]) if row[19] else [],
                    'status': row[20],
                    'generated_at': row[21],
                    'created_at': row[23],
                    'updated_at': row[24],
                    # 从 JOIN 的 project_documents 表
                    'document_title': row[25],  # original_filename
                    'file_type': row[26],
                    'file_size': row[27]
                })
            except Exception as e:
                logger.warning(f"解析缩影数据失败: {e}")
                continue

        # 查询总数
        count_query = text("""
            SELECT COUNT(*) FROM file_summaries
            WHERE project_id = :project_id
              AND (:dimension IS NULL OR primary_dimension = :dimension)
              AND (:status IS NULL OR status = :status)
        """)
        total = db.execute(count_query, {
            'project_id': project_id,
            'dimension': dimension,
            'status': status
        }).scalar()

        logger.info(f"✅ 查询到 {len(summaries)} 条缩影（总计 {total} 条）")

        return success_response(data={
            'total': total,
            'summaries': summaries,
            'skip': skip,
            'limit': limit
        })

    except Exception as e:
        logger.error(f"查询缩影列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/summary")
async def get_summary(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个文档的缩影

    返回格式：
    {
        "success": true,
        "data": {
            "id": 1,
            "document_id": 123,
            "one_line_summary": "...",
            ...
        }
    }
    """

    try:
        logger.info(f"查询文档 {document_id} 的缩影")

        result = db.execute(text("""
            SELECT s.*, d.original_filename, d.file_type, d.file_size, d.created_at as doc_created_at
            FROM file_summaries s
            JOIN project_documents d ON s.document_id = d.id
            WHERE s.document_id = :document_id
        """), {'document_id': document_id}).fetchone()

        if not result:
            logger.warning(f"文档 {document_id} 的缩影不存在")
            raise HTTPException(status_code=404, detail="Summary not found")

        summary = {
            'id': result[0],
            'document_id': result[1],
            'project_id': result[2],
            'one_line_summary': result[3],
            'full_summary': result[4],
            'top_keywords': json.loads(result[5]) if result[5] else [],
            'top_entities': json.loads(result[6]) if result[6] else [],
            'top_topics': json.loads(result[7]) if result[7] else [],
            'top_events': json.loads(result[8]) if result[8] else [],
            'word_count': result[9],
            'chunk_count': result[10],
            'avg_chunk_length': result[11],
            'emotion_polarity': result[12],
            'subjectivity': result[13],
            'primary_dimension': result[14],
            'secondary_dimensions': json.loads(result[15]) if result[15] else [],
            'time_start': result[16],
            'time_end': result[17],
            'spatial_context': result[18],
            'related_documents': json.loads(result[19]) if result[19] else [],
            'status': result[20],
            'generated_at': result[21],
            'error_message': result[22],
            'created_at': result[23],
            'updated_at': result[24],
            # 文档信息
            'document_title': result[25],
            'file_type': result[26],
            'file_size': result[27],
            'document_created_at': result[28]
        }

        logger.info(f"✅ 查询到文档 {document_id} 的缩影")

        return success_response(data=summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询缩影失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{document_id}/regenerate")
async def regenerate_summary(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    重新生成文档缩影

    场景：
    1. 缩影生成失败后重试
    2. 文档内容更新后重新生成
    3. 用户手动触发重新生成

    返回格式：
    {
        "success": true,
        "data": {
            "message": "缩影重新生成成功",
            "document_id": 123
        }
    }
    """

    try:
        logger.info(f"触发重新生成文档 {document_id} 的缩影")

        # 检查文档是否存在
        from app.models.project import ProjectDocument
        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # 在后台任务中重新生成
        def regenerate_task():
            from app.services.summary_generator import regenerate_summary
            from app.core.database import SessionLocal

            task_db = SessionLocal()
            try:
                regenerate_summary(task_db, document_id)
            except Exception as e:
                logger.error(f"后台重新生成缩影失败: {e}", exc_info=True)
            finally:
                task_db.close()

        background_tasks.add_task(regenerate_task)

        logger.info(f"✅ 已提交重新生成任务: document_id={document_id}")

        return success_response(data={
            'message': '缩影重新生成任务已提交',
            'document_id': document_id
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"触发重新生成失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/dimensions")
async def get_dimensions(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的所有维度（用于筛选）

    返回格式：
    {
        "success": true,
        "data": {
            "dimensions": [
                {"name": "非遗", "count": 15},
                {"name": "民俗", "count": 8},
                ...
            ]
        }
    }
    """

    try:
        logger.info(f"查询项目 {project_id} 的维度列表")

        results = db.execute(text("""
            SELECT DISTINCT primary_dimension, COUNT(*) as count
            FROM file_summaries
            WHERE project_id = :project_id
              AND primary_dimension IS NOT NULL
              AND primary_dimension != '未分类'
            GROUP BY primary_dimension
            ORDER BY count DESC
        """), {'project_id': project_id}).fetchall()

        dimensions = [
            {
                'name': row[0],
                'count': row[1]
            }
            for row in results
        ]

        logger.info(f"✅ 查询到 {len(dimensions)} 个维度")

        return success_response(data={
            'dimensions': dimensions
        })

    except Exception as e:
        logger.error(f"查询维度列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/stats")
async def get_summary_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的缩影统计信息

    返回格式：
    {
        "success": true,
        "data": {
            "total_summaries": 100,
            "status_breakdown": {"done": 95, "pending": 3, "error": 2},
            "avg_word_count": 2500,
            "total_keywords": 300
        }
    }
    """

    try:
        logger.info(f"查询项目 {project_id} 的缩影统计")

        # 总数和状态分布
        status_result = db.execute(text("""
            SELECT status, COUNT(*) as count
            FROM file_summaries
            WHERE project_id = :project_id
            GROUP BY status
        """), {'project_id': project_id}).fetchall()

        status_breakdown = {row[0]: row[1] for row in status_result}
        total_summaries = sum(status_breakdown.values())

        # 平均字数
        avg_result = db.execute(text("""
            SELECT AVG(word_count) as avg_word_count
            FROM file_summaries
            WHERE project_id = :project_id AND status = 'done'
        """), {'project_id': project_id}).fetchone()

        avg_word_count = int(avg_result[0]) if avg_result[0] else 0

        logger.info(f"✅ 项目 {project_id} 缩影统计: 总计 {total_summaries} 条")

        return success_response(data={
            'total_summaries': total_summaries,
            'status_breakdown': status_breakdown,
            'avg_word_count': avg_word_count
        })

    except Exception as e:
        logger.error(f"查询统计信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
