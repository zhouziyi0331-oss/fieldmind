"""
优化后的 Dashboard API（带缓存和查询优化）
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.core.database import get_db
from app.services.cache_service import cache, cached, CacheKeys
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectDocument
from app.models.document import Document
from app.schemas.response import success_response

router = APIRouter()


@router.get("/projects/{project_id}/quality")
@cached(ttl=600, key_prefix=CacheKeys.DATA_QUALITY)
async def get_data_quality_metrics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目数据质量指标（带缓存）
    缓存时间：10分钟
    """
    # 使用 SQL 聚合优化查询
    from app.models.structured_insight import StructuredInsight

    quality_stats = db.query(
        func.count(StructuredInsight.id).label('total_insights'),
        func.avg(StructuredInsight.confidence).label('avg_confidence'),
        func.sum(
            func.case(
                (StructuredInsight.confidence >= 0.8, 1),
                else_=0
            )
        ).label('high_quality_count')
    ).filter(
        StructuredInsight.project_id == project_id
    ).first()

    # 计算维度覆盖率
    dimension_coverage = db.query(
        StructuredInsight.dimension,
        func.count(StructuredInsight.id).label('count')
    ).filter(
        StructuredInsight.project_id == project_id
    ).group_by(
        StructuredInsight.dimension
    ).all()

    return success_response(data={
        "total_insights": quality_stats.total_insights or 0,
        "avg_confidence": round(quality_stats.avg_confidence or 0, 2),
        "high_quality_rate": round(
            (quality_stats.high_quality_count or 0) / (quality_stats.total_insights or 1) * 100,
            2
        ),
        "dimension_coverage": [
            {"dimension": dim, "count": count}
            for dim, count in dimension_coverage
        ]
    })


@router.get("/projects/{project_id}/stats")
@cached(ttl=300, key_prefix=CacheKeys.PROJECT_STATS)
async def get_project_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目统计信息（带缓存）
    缓存时间：5分钟
    """
    # 优化：使用单个查询获取所有统计
    from app.models.document_chunk import DocumentChunk
    from app.models.entity import Entity, DocumentEntity
    from app.models.structured_insight import StructuredInsight

    # 文档统计
    doc_stats = db.query(
        func.count(ProjectDocument.id).label('total_docs'),
        func.sum(
            func.case(
                (ProjectDocument.status == 'completed', 1),
                else_=0
            )
        ).label('completed_docs')
    ).filter(
        ProjectDocument.project_id == project_id
    ).first()

    # 分块统计
    chunk_count = db.query(func.count(DocumentChunk.id)).filter(
        DocumentChunk.project_id == project_id
    ).scalar() or 0

    # 实体统计
    entity_count = db.query(func.count(func.distinct(DocumentEntity.entity_id))).join(
        ProjectDocument,
        DocumentEntity.document_id == ProjectDocument.id
    ).filter(
        ProjectDocument.project_id == project_id
    ).scalar() or 0

    # 洞察统计
    insight_count = db.query(func.count(StructuredInsight.id)).filter(
        StructuredInsight.project_id == project_id
    ).scalar() or 0

    return success_response(data={
        "documents": {
            "total": doc_stats.total_docs or 0,
            "completed": doc_stats.completed_docs or 0,
            "processing": (doc_stats.total_docs or 0) - (doc_stats.completed_docs or 0)
        },
        "chunks": chunk_count,
        "entities": entity_count,
        "insights": insight_count,
        "last_updated": datetime.utcnow().isoformat()
    })


@router.get("/projects/{project_id}/knowledge-graph")
@cached(ttl=900, key_prefix=CacheKeys.KNOWLEDGE_GRAPH)
async def get_knowledge_graph_cached(
    project_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取知识图谱数据（带缓存）
    缓存时间：15分钟
    """
    from app.models.entity import Entity, EntityRelation, DocumentEntity
    from app.models.project import ProjectDocument

    # 优化：使用 joinedload 预加载关系，避免 N+1 查询
    entities = db.query(Entity).join(
        DocumentEntity,
        Entity.id == DocumentEntity.entity_id
    ).join(
        ProjectDocument,
        DocumentEntity.document_id == ProjectDocument.id
    ).filter(
        ProjectDocument.project_id == project_id
    ).options(
        joinedload(Entity.outgoing_relations),
        joinedload(Entity.incoming_relations)
    ).limit(limit).all()

    # 构建节点和边
    nodes = []
    edges = []
    entity_ids = set()

    for entity in entities:
        entity_ids.add(entity.id)
        nodes.append({
            "id": entity.id,
            "label": entity.text,
            "type": entity.type,
            "frequency": entity.frequency or 1
        })

        # 添加关系（出边）
        for rel in entity.outgoing_relations:
            if rel.target_entity_id in entity_ids or len(edges) < limit * 2:
                edges.append({
                    "source": rel.source_entity_id,
                    "target": rel.target_entity_id,
                    "type": rel.relation_type,
                    "confidence": rel.confidence or 0.5
                })

    return success_response(data={
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    })


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: Optional[str] = Query(None, description="缓存键模式"),
    current_user: User = Depends(get_current_user)
):
    """
    手动清除缓存
    需要管理员权限
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可清除缓存")

    if pattern:
        count = cache.delete_pattern(pattern)
        return success_response(data={
            "message": f"已清除 {count} 个缓存项",
            "pattern": pattern
        })
    else:
        cache.clear_all()
        return success_response(data={
            "message": "已清除所有缓存"
        })


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user)
):
    """获取缓存统计信息"""
    stats = cache.get_stats()
    health = cache.health_check()

    return success_response(data={
        **stats,
        "health": health
    })
