"""
知识图谱 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter()


# ==================== Pydantic 模型 ====================
class ManualEntityCreate(BaseModel):
    entity_name: str
    entity_type: str
    importance_score: Optional[float] = 0.8
    properties: Optional[Dict[str, Any]] = None


class ManualEventCreate(BaseModel):
    event_title: str
    event_summary: Optional[str] = None
    event_5w1h: Optional[Dict[str, Any]] = None


class ManualRelationCreate(BaseModel):
    source_id: int
    target_id: int
    relation_type: str
    confidence: Optional[float] = 0.9
    properties: Optional[Dict[str, Any]] = None


@router.get("/knowledge-graph/{project_id}", response_model=ApiResponse)
async def get_knowledge_graph(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    获取项目知识图谱

    返回节点和边的数据，用于前端 D3.js 可视化

    返回格式：
    {
        "nodes": [
            {
                "id": "文化",
                "label": "文化",
                "type": "dimension",
                "count": 45,
                "size": 90
            }
        ],
        "edges": [
            {
                "source": "文化",
                "target": "文化::非遗保护",
                "type": "contains",
                "weight": 1.0
            }
        ],
        "statistics": {
            "total_nodes": 50,
            "total_edges": 30,
            ...
        }
    }
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.knowledge_graph_service import build_knowledge_graph

        graph_data = build_knowledge_graph(db, project_id)

        return success_response(
            data=graph_data,
            request_id=request_id,
            message=f"知识图谱加载成功"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-graph/{project_id}/node/{node_id}", response_model=ApiResponse)
async def get_node_details(
    request: Request,
    project_id: int,
    node_id: str,
    db: Session = Depends(get_db),
):
    """
    获取知识图谱节点详情

    返回该节点的：
    - 支撑材料（chunks）
    - 关键词列表
    - 关联节点
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.chunk import Chunk

        # 解析节点 ID
        if "::" in node_id:
            # 子维度节点
            parts = node_id.split("::")
            if len(parts) == 2:
                category, sub_category = parts
                chunks = db.query(Chunk).filter(
                    Chunk.project_id == project_id,
                    Chunk.dimension_category == category,
                    Chunk.dimension_sub_category == sub_category
                ).limit(10).all()
            else:
                chunks = []
        else:
            # 大维度节点
            chunks = db.query(Chunk).filter(
                Chunk.project_id == project_id,
                Chunk.dimension_category == node_id
            ).limit(10).all()

        # 构建支撑材料列表
        materials = [
            {
                "id": chunk.id,
                "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "document_id": chunk.document_id,
                "sentiment": chunk.sentiment_polarity,
            }
            for chunk in chunks
        ]

        return success_response(
            data={
                "node_id": node_id,
                "materials": materials,
                "total_chunks": len(chunks)
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-graph/{project_id}/rebuild", response_model=ApiResponse)
async def rebuild_knowledge_graph(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    重建项目知识图谱

    触发关键词提取和图谱构建
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.services.keyword_extraction import keyword_extraction_service
        from app.services.knowledge_graph_service import build_knowledge_graph
        from app.models.chunk import Chunk

        # 1. 获取所有 chunks
        chunks = db.query(Chunk).filter(Chunk.project_id == project_id).all()

        if not chunks:
            raise HTTPException(status_code=400, detail="项目没有可用的文本数据")

        # 2. 提取关键词
        all_text = "\n".join([chunk.content for chunk in chunks if chunk.content])
        keywords = keyword_extraction_service.extract_keywords(all_text, top_k=50)

        # 3. 构建知识图谱
        graph_data = build_knowledge_graph(db, project_id)

        return success_response(
            data={
                "keywords_extracted": len(keywords),
                "nodes_created": graph_data["statistics"]["total_nodes"],
                "edges_created": graph_data["statistics"]["total_edges"],
            },
            request_id=request_id,
            message="知识图谱重建成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 手动添加节点和关系 API ====================

@router.post("/knowledge-graph/document/{dirty_doc_id}/manual/entity", response_model=ApiResponse)
async def add_manual_entity(
    request: Request,
    dirty_doc_id: int,
    data: ManualEntityCreate,
    db: Session = Depends(get_db),
):
    """
    手动添加实体节点到知识图谱

    参数：
    - entity_name: 实体名称
    - entity_type: 实体类型（PERSON, ORGANIZATION, LOCATION, CONCEPT等）
    - importance_score: 重要性评分（0-1）
    - properties: 自定义属性字典
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.clean_channel import CleanChannelEntity
        from app.models.dirty_channel import DirtyChannelDocument

        # 验证文档是否存在
        doc = db.query(DirtyChannelDocument).filter(
            DirtyChannelDocument.id == dirty_doc_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 创建实体节点
        entity = CleanChannelEntity(
            dirty_doc_id=dirty_doc_id,
            entity_name=data.entity_name,
            entity_type=data.entity_type,
            importance_score=data.importance_score,
            properties=data.properties or {},
            pipeline_step=0,  # 0表示手动添加
            is_manual=True,   # 标记为手动添加
        )

        db.add(entity)
        db.commit()
        db.refresh(entity)

        return success_response(
            data={
                "entity_id": entity.id,
                "entity_name": entity.entity_name,
                "entity_type": entity.entity_type,
            },
            request_id=request_id,
            message="实体节点添加成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加实体节点失败: {str(e)}")


@router.post("/knowledge-graph/document/{dirty_doc_id}/manual/event", response_model=ApiResponse)
async def add_manual_event(
    request: Request,
    dirty_doc_id: int,
    data: ManualEventCreate,
    db: Session = Depends(get_db),
):
    """
    手动添加事件节点到知识图谱

    参数：
    - event_title: 事件标题
    - event_summary: 事件摘要
    - event_5w1h: 5W1H信息字典（what, when, where, who, why, how）
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.clean_channel import CleanChannelEvent
        from app.models.dirty_channel import DirtyChannelDocument

        # 验证文档是否存在
        doc = db.query(DirtyChannelDocument).filter(
            DirtyChannelDocument.id == dirty_doc_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 创建事件节点
        event = CleanChannelEvent(
            dirty_doc_id=dirty_doc_id,
            event_title=data.event_title,
            event_summary=data.event_summary or "",
            event_5w1h=data.event_5w1h or {},
            pipeline_step=0,  # 0表示手动添加
            is_manual=True,   # 标记为手动添加
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return success_response(
            data={
                "event_id": event.id,
                "event_title": event.event_title,
            },
            request_id=request_id,
            message="事件节点添加成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加事件节点失败: {str(e)}")


@router.post("/knowledge-graph/document/{dirty_doc_id}/manual/relation", response_model=ApiResponse)
async def add_manual_relation(
    request: Request,
    dirty_doc_id: int,
    data: ManualRelationCreate,
    db: Session = Depends(get_db),
):
    """
    手动添加关系边到知识图谱

    参数：
    - source_id: 源节点ID（实体或事件的ID）
    - target_id: 目标节点ID（实体或事件的ID）
    - relation_type: 关系类型（IS_A, PART_OF, PARTICIPATES_IN等）
    - confidence: 置信度（0-1）
    - properties: 自定义属性字典
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.clean_channel import CleanChannelRelation, CleanChannelEntity
        from app.models.dirty_channel import DirtyChannelDocument

        # 验证文档是否存在
        doc = db.query(DirtyChannelDocument).filter(
            DirtyChannelDocument.id == dirty_doc_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 验证源节点和目标节点是否存在
        source_entity = db.query(CleanChannelEntity).filter(
            CleanChannelEntity.id == data.source_id,
            CleanChannelEntity.dirty_doc_id == dirty_doc_id
        ).first()

        target_entity = db.query(CleanChannelEntity).filter(
            CleanChannelEntity.id == data.target_id,
            CleanChannelEntity.dirty_doc_id == dirty_doc_id
        ).first()

        if not source_entity:
            raise HTTPException(status_code=404, detail=f"源节点ID {data.source_id} 不存在")

        if not target_entity:
            raise HTTPException(status_code=404, detail=f"目标节点ID {data.target_id} 不存在")

        # 检查关系是否已存在
        existing_relation = db.query(CleanChannelRelation).filter(
            CleanChannelRelation.dirty_doc_id == dirty_doc_id,
            CleanChannelRelation.source_entity_id == data.source_id,
            CleanChannelRelation.target_entity_id == data.target_id,
            CleanChannelRelation.relation_type == data.relation_type
        ).first()

        if existing_relation:
            raise HTTPException(status_code=400, detail="该关系已存在")

        # 创建关系
        relation = CleanChannelRelation(
            dirty_doc_id=dirty_doc_id,
            source_entity_id=data.source_id,
            target_entity_id=data.target_id,
            relation_type=data.relation_type,
            confidence=data.confidence,
            properties=data.properties or {},
            pipeline_step=0,  # 0表示手动添加
            is_manual=True,   # 标记为手动添加
        )

        db.add(relation)
        db.commit()
        db.refresh(relation)

        return success_response(
            data={
                "relation_id": relation.id,
                "source": source_entity.entity_name,
                "target": target_entity.entity_name,
                "relation_type": relation.relation_type,
            },
            request_id=request_id,
            message="关系添加成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加关系失败: {str(e)}")


@router.delete("/knowledge-graph/document/{dirty_doc_id}/node/{node_type}/{node_id}", response_model=ApiResponse)
async def delete_node(
    request: Request,
    dirty_doc_id: int,
    node_type: str,
    node_id: int,
    db: Session = Depends(get_db),
):
    """
    删除节点（实体或事件）

    参数：
    - node_type: 节点类型（entity 或 event）
    - node_id: 节点ID
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.clean_channel import CleanChannelEntity, CleanChannelEvent, CleanChannelRelation

        if node_type == "entity":
            node = db.query(CleanChannelEntity).filter(
                CleanChannelEntity.id == node_id,
                CleanChannelEntity.dirty_doc_id == dirty_doc_id
            ).first()

            if not node:
                raise HTTPException(status_code=404, detail="实体节点不存在")

            # 删除相关的关系
            db.query(CleanChannelRelation).filter(
                (CleanChannelRelation.source_entity_id == node_id) |
                (CleanChannelRelation.target_entity_id == node_id)
            ).delete()

            db.delete(node)

        elif node_type == "event":
            node = db.query(CleanChannelEvent).filter(
                CleanChannelEvent.id == node_id,
                CleanChannelEvent.dirty_doc_id == dirty_doc_id
            ).first()

            if not node:
                raise HTTPException(status_code=404, detail="事件节点不存在")

            db.delete(node)

        else:
            raise HTTPException(status_code=400, detail="无效的节点类型，必须是 'entity' 或 'event'")

        db.commit()

        return success_response(
            data={"node_id": node_id, "node_type": node_type},
            request_id=request_id,
            message=f"{node_type}节点删除成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除节点失败: {str(e)}")


@router.put("/knowledge-graph/document/{dirty_doc_id}/node/{node_type}/{node_id}", response_model=ApiResponse)
async def update_node(
    request: Request,
    dirty_doc_id: int,
    node_type: str,
    node_id: int,
    data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
):
    """
    更新节点信息（实体或事件）

    参数：
    - node_type: 节点类型（entity 或 event）
    - node_id: 节点ID
    - data: 要更新的字段字典
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.clean_channel import CleanChannelEntity, CleanChannelEvent

        if node_type == "entity":
            node = db.query(CleanChannelEntity).filter(
                CleanChannelEntity.id == node_id,
                CleanChannelEntity.dirty_doc_id == dirty_doc_id
            ).first()

            if not node:
                raise HTTPException(status_code=404, detail="实体节点不存在")

            # 更新允许的字段
            allowed_fields = ['entity_name', 'entity_type', 'importance_score', 'properties']
            for field, value in data.items():
                if field in allowed_fields:
                    setattr(node, field, value)

        elif node_type == "event":
            node = db.query(CleanChannelEvent).filter(
                CleanChannelEvent.id == node_id,
                CleanChannelEvent.dirty_doc_id == dirty_doc_id
            ).first()

            if not node:
                raise HTTPException(status_code=404, detail="事件节点不存在")

            # 更新允许的字段
            allowed_fields = ['event_title', 'event_summary', 'event_5w1h']
            for field, value in data.items():
                if field in allowed_fields:
                    setattr(node, field, value)

        else:
            raise HTTPException(status_code=400, detail="无效的节点类型，必须是 'entity' 或 'event'")

        db.commit()
        db.refresh(node)

        return success_response(
            data={"node_id": node_id, "node_type": node_type},
            request_id=request_id,
            message=f"{node_type}节点更新成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新节点失败: {str(e)}")
