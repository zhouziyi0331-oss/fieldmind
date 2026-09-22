"""
知识查询 API 路由
Knowledge Query API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, and_
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.knowledge import (
    KnowledgeEntity,
    KnowledgeRelation,
    KnowledgeEvent,
    KnowledgeUnit,
    KnowledgeOntology,
    InferenceFinding,
    KnowledgeConflict,
    WikiPage,
    ReaderView
)
from pydantic import BaseModel

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


# ==================== Schemas ====================

class EntityResponse(BaseModel):
    """实体响应"""
    id: str
    name: str
    type: str
    aliases: List[str]
    confidence: float
    importance: float
    mention_count: int
    created_at: str


class RelationResponse(BaseModel):
    """关系响应"""
    id: str
    type: str
    source_entity_id: str
    target_entity_id: str
    source_name: str
    target_name: str
    confidence: float
    evidence: List[str]


class EventResponse(BaseModel):
    """事件响应"""
    id: str
    type: str
    trigger: str
    who: List[str]
    what: str
    when: List[str]
    where: List[str]
    why: str
    how: str
    confidence: float
    importance: float


# ==================== 实体 API ====================

@router.get("/entities", response_model=List[EntityResponse])
async def list_entities(
    project_id: str = Query(..., description="项目ID"),
    entity_type: Optional[str] = Query(None, description="实体类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出实体
    """
    stmt = select(KnowledgeEntity).where(KnowledgeEntity.project_id == project_id)

    if entity_type:
        stmt = stmt.where(KnowledgeEntity.type == entity_type)

    if search:
        stmt = stmt.where(
            or_(
                KnowledgeEntity.name.ilike(f"%{search}%"),
                KnowledgeEntity.aliases.contains([search])
            )
        )

    stmt = stmt.order_by(KnowledgeEntity.importance.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    entities = result.scalars().all()

    return [
        EntityResponse(
            id=e.id,
            name=e.name,
            type=e.type,
            aliases=e.aliases or [],
            confidence=e.confidence,
            importance=e.importance,
            mention_count=e.mention_count,
            created_at=e.created_at.isoformat()
        )
        for e in entities
    ]


@router.get("/entities/{entity_id}")
async def get_entity_detail(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取实体详情（包含关系和事件）
    """
    # 获取实体
    stmt = select(KnowledgeEntity).where(KnowledgeEntity.id == entity_id)
    result = await db.execute(stmt)
    entity = result.scalar_one_or_none()

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # 获取相关关系（作为源）
    stmt = select(KnowledgeRelation).where(KnowledgeRelation.source_entity_id == entity_id)
    result = await db.execute(stmt)
    source_relations = result.scalars().all()

    # 获取相关关系（作为目标）
    stmt = select(KnowledgeRelation).where(KnowledgeRelation.target_entity_id == entity_id)
    result = await db.execute(stmt)
    target_relations = result.scalars().all()

    # 获取参与的事件
    stmt = select(KnowledgeEvent).where(
        KnowledgeEvent.who.contains([entity.name])
    )
    result = await db.execute(stmt)
    events = result.scalars().all()

    return {
        "entity": {
            "id": entity.id,
            "name": entity.name,
            "type": entity.type,
            "aliases": entity.aliases or [],
            "attributes": entity.attributes or {},
            "confidence": entity.confidence,
            "importance": entity.importance,
            "mention_count": entity.mention_count,
            "metadata": entity.metadata or {}
        },
        "source_relations": [
            {
                "id": r.id,
                "type": r.type,
                "target_entity_id": r.target_entity_id,
                "confidence": r.confidence
            }
            for r in source_relations
        ],
        "target_relations": [
            {
                "id": r.id,
                "type": r.type,
                "source_entity_id": r.source_entity_id,
                "confidence": r.confidence
            }
            for r in target_relations
        ],
        "events": [
            {
                "id": e.id,
                "type": e.type,
                "trigger": e.trigger,
                "what": e.what
            }
            for e in events
        ]
    }


# ==================== 关系 API ====================

@router.get("/relations", response_model=List[RelationResponse])
async def list_relations(
    project_id: str = Query(..., description="项目ID"),
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    entity_id: Optional[str] = Query(None, description="关联实体ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出关系
    """
    stmt = select(KnowledgeRelation).where(KnowledgeRelation.project_id == project_id)

    if relation_type:
        stmt = stmt.where(KnowledgeRelation.type == relation_type)

    if entity_id:
        stmt = stmt.where(
            or_(
                KnowledgeRelation.source_entity_id == entity_id,
                KnowledgeRelation.target_entity_id == entity_id
            )
        )

    stmt = stmt.order_by(KnowledgeRelation.confidence.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    relations = result.scalars().all()

    # 获取实体名称
    entity_ids = set()
    for r in relations:
        entity_ids.add(r.source_entity_id)
        entity_ids.add(r.target_entity_id)

    stmt = select(KnowledgeEntity).where(KnowledgeEntity.id.in_(entity_ids))
    result = await db.execute(stmt)
    entities = {e.id: e.name for e in result.scalars().all()}

    return [
        RelationResponse(
            id=r.id,
            type=r.type,
            source_entity_id=r.source_entity_id,
            target_entity_id=r.target_entity_id,
            source_name=entities.get(r.source_entity_id, "Unknown"),
            target_name=entities.get(r.target_entity_id, "Unknown"),
            confidence=r.confidence,
            evidence=r.evidence or []
        )
        for r in relations
    ]


# ==================== 事件 API ====================

@router.get("/events", response_model=List[EventResponse])
async def list_events(
    project_id: str = Query(..., description="项目ID"),
    event_type: Optional[str] = Query(None, description="事件类型过滤"),
    participant: Optional[str] = Query(None, description="参与者过滤"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出事件
    """
    stmt = select(KnowledgeEvent).where(KnowledgeEvent.project_id == project_id)

    if event_type:
        stmt = stmt.where(KnowledgeEvent.type == event_type)

    if participant:
        stmt = stmt.where(KnowledgeEvent.who.contains([participant]))

    stmt = stmt.order_by(KnowledgeEvent.importance.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    events = result.scalars().all()

    return [
        EventResponse(
            id=e.id,
            type=e.type,
            trigger=e.trigger,
            who=e.who or [],
            what=e.what or "",
            when=e.when or [],
            where=e.where or [],
            why=e.why or "",
            how=e.how or "",
            confidence=e.confidence,
            importance=e.importance
        )
        for e in events
    ]


# ==================== 知识单元 API ====================

@router.get("/units")
async def list_knowledge_units(
    project_id: str = Query(..., description="项目ID"),
    unit_type: Optional[str] = Query(None, description="单元类型过滤"),
    tag: Optional[str] = Query(None, description="标签过滤"),
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出知识单元
    """
    stmt = select(KnowledgeUnit).where(KnowledgeUnit.project_id == project_id)

    if unit_type:
        stmt = stmt.where(KnowledgeUnit.type == unit_type)

    if tag:
        stmt = stmt.where(KnowledgeUnit.tags.contains([tag]))

    stmt = stmt.where(KnowledgeUnit.importance >= min_importance)
    stmt = stmt.order_by(KnowledgeUnit.importance.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    units = result.scalars().all()

    return [
        {
            "id": u.id,
            "type": u.type,
            "title": u.title,
            "content": u.content,
            "importance": u.importance,
            "confidence": u.confidence,
            "completeness": u.completeness,
            "tags": u.tags or [],
            "source": u.source
        }
        for u in units
    ]


# ==================== 搜索 API ====================

@router.get("/search")
async def search_knowledge(
    project_id: str = Query(..., description="项目ID"),
    query: str = Query(..., min_length=1, description="搜索查询"),
    search_entities: bool = Query(True),
    search_events: bool = Query(True),
    search_units: bool = Query(True),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    全局搜索（实体、事件、知识单元）
    """
    results = {
        "entities": [],
        "events": [],
        "knowledge_units": []
    }

    # 搜索实体
    if search_entities:
        stmt = select(KnowledgeEntity).where(
            and_(
                KnowledgeEntity.project_id == project_id,
                or_(
                    KnowledgeEntity.name.ilike(f"%{query}%"),
                    KnowledgeEntity.aliases.contains([query])
                )
            )
        ).limit(limit)

        result = await db.execute(stmt)
        entities = result.scalars().all()
        results["entities"] = [
            {
                "id": e.id,
                "name": e.name,
                "type": e.type,
                "importance": e.importance
            }
            for e in entities
        ]

    # 搜索事件
    if search_events:
        stmt = select(KnowledgeEvent).where(
            and_(
                KnowledgeEvent.project_id == project_id,
                or_(
                    KnowledgeEvent.trigger.ilike(f"%{query}%"),
                    KnowledgeEvent.what.ilike(f"%{query}%")
                )
            )
        ).limit(limit)

        result = await db.execute(stmt)
        events = result.scalars().all()
        results["events"] = [
            {
                "id": e.id,
                "trigger": e.trigger,
                "type": e.type,
                "what": e.what[:100] + "..." if len(e.what) > 100 else e.what
            }
            for e in events
        ]

    # 搜索知识单元
    if search_units:
        stmt = select(KnowledgeUnit).where(
            and_(
                KnowledgeUnit.project_id == project_id,
                or_(
                    KnowledgeUnit.title.ilike(f"%{query}%"),
                    KnowledgeUnit.content.ilike(f"%{query}%")
                )
            )
        ).limit(limit)

        result = await db.execute(stmt)
        units = result.scalars().all()
        results["knowledge_units"] = [
            {
                "id": u.id,
                "title": u.title,
                "type": u.type,
                "content": u.content[:100] + "..." if len(u.content) > 100 else u.content
            }
            for u in units
        ]

    return results


# ==================== 本体 API ====================

@router.get("/ontology/{project_id}")
async def get_ontology(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目本体
    """
    stmt = select(KnowledgeOntology).where(
        KnowledgeOntology.project_id == project_id
    ).order_by(KnowledgeOntology.created_at.desc())

    result = await db.execute(stmt)
    ontology = result.scalar_one_or_none()

    if not ontology:
        raise HTTPException(status_code=404, detail="Ontology not found")

    return {
        "id": ontology.id,
        "name": ontology.name,
        "version": ontology.version,
        "concept_count": ontology.concept_count,
        "relation_type_count": ontology.relation_type_count,
        "axiom_count": ontology.axiom_count,
        "metadata": ontology.metadata or {},
        "created_at": ontology.created_at.isoformat()
    }


@router.get("/ontology/{project_id}/owl")
async def download_owl(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载本体 OWL 文件
    """
    from fastapi.responses import Response

    stmt = select(KnowledgeOntology).where(
        KnowledgeOntology.project_id == project_id
    ).order_by(KnowledgeOntology.created_at.desc())

    result = await db.execute(stmt)
    ontology = result.scalar_one_or_none()

    if not ontology or not ontology.owl_xml:
        raise HTTPException(status_code=404, detail="OWL file not found")

    return Response(
        content=ontology.owl_xml,
        media_type="application/rdf+xml",
        headers={
            "Content-Disposition": f"attachment; filename={ontology.name}.owl"
        }
    )


# ==================== 推理和冲突 API ====================

@router.get("/inferences/{project_id}")
async def list_inferences(
    project_id: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出推理发现
    """
    stmt = select(InferenceFinding).where(
        InferenceFinding.project_id == project_id
    ).order_by(InferenceFinding.confidence.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    findings = result.scalars().all()

    return [
        {
            "id": f.id,
            "type": f.type,
            "conclusion": {
                "predicate": f.conclusion_predicate,
                "subject": f.conclusion_subject,
                "object": f.conclusion_object
            },
            "rule_description": f.rule_description,
            "confidence": f.confidence,
            "reasoning_steps": f.reasoning_steps or []
        }
        for f in findings
    ]


@router.get("/conflicts/{project_id}")
async def list_conflicts(
    project_id: str,
    status: Optional[str] = Query(None, description="冲突状态过滤"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出知识冲突
    """
    stmt = select(KnowledgeConflict).where(
        KnowledgeConflict.project_id == project_id
    )

    if status:
        stmt = stmt.where(KnowledgeConflict.status == status)

    stmt = stmt.order_by(KnowledgeConflict.severity.desc())
    stmt = stmt.limit(limit).offset(offset)

    result = await db.execute(stmt)
    conflicts = result.scalars().all()

    return [
        {
            "id": c.id,
            "type": c.type,
            "description": c.description,
            "severity": c.severity,
            "status": c.status,
            "resolution": c.resolution,
            "created_at": c.created_at.isoformat()
        }
        for c in conflicts
    ]
