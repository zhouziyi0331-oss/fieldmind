"""
知识图谱 API - 链路十一：实体提取与知识图谱构建
"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.models.project import ProjectDocument, Project
from app.models.entity import Entity
from app.models.timeline import TimelineEvent
from app.tools.knowledge.graph import create_knowledge_graph
from app.core.exceptions import (
    ResourceNotFoundException,
    DatabaseException,
    GraphException
)

router = APIRouter(tags=["knowledge-graph"])
logger = logging.getLogger(__name__)


# ==================== 新增Schema ====================

class BuildGraphRequest(BaseModel):
    """构建知识图谱请求"""
    project_id: int
    document_ids: Optional[List[int]] = None  # 空表示处理所有文档
    force_rebuild: bool = False


class EntityResponse(BaseModel):
    """实体响应"""
    model_config = {"from_attributes": True}

    id: str
    entity_type: str
    name: str
    aliases: Optional[List[str]]
    properties: Optional[dict]
    description: Optional[str]
    confidence: float
    mention_count: int
    document_ids: Optional[List[int]]


# ==================== 新API：构建知识图谱 ====================

@router.post("/build")
async def build_knowledge_graph(
    request: BuildGraphRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    从文档构建知识图谱（链路十一核心功能）

    - 提取实体（人物、地点、组织等）
    - 提取实体关系
    - 提取时间线事件
    - 存储到数据库
    """
    try:
        builder = create_knowledge_graph(db)

        if request.document_ids:
            # 处理指定文档
            total_stats = {
                "documents_processed": 0,
                "entities_created": 0,
                "entities_updated": 0,
                "relationships_created": 0,
                "timeline_events": 0,
                "errors": []
            }

            for doc_id in request.document_ids:
                try:
                    stats = builder.build_from_document(doc_id, request.project_id)
                    total_stats["documents_processed"] += 1
                    total_stats["entities_created"] += stats["entities_created"]
                    total_stats["entities_updated"] += stats.get("entities_updated", 0)
                    total_stats["relationships_created"] += stats["relationships_created"]
                    total_stats["timeline_events"] += stats["timeline_events"]
                except Exception as e:
                    logger.error(f"处理文档 {doc_id} 失败: {e}")
                    total_stats["errors"].append({"document_id": doc_id, "error": str(e)})

            return {
                "status": "completed",
                "message": f"处理完成：{total_stats['documents_processed']} 个文档",
                "stats": total_stats
            }
        else:
            # 处理项目所有文档
            stats = builder.build_from_project(request.project_id, request.force_rebuild)

            return {
                "status": "completed",
                "message": f"项目知识图谱构建完成：{stats['documents_processed']} 个文档",
                "stats": stats
            }

    except Exception as e:
        logger.error(f"构建知识图谱失败: {e}", exc_info=True)
        raise GraphException(message="构建知识图谱失败", operation="build_knowledge_graph", details={"error": str(e)})


@router.get("/entities", response_model=List[EntityResponse])
async def get_entities(
    project_id: int,
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    获取实体列表（从数据库读取真实数据）

    - project_id: 项目ID（必填）
    - entity_type: 过滤实体类型
    - search: 搜索关键词（匹配name）
    - limit: 返回数量
    """
    # 获取项目的所有文档ID
    doc_ids = [doc.id for doc in db.query(ProjectDocument.id).filter(
        ProjectDocument.project_id == project_id
    ).all()]

    if not doc_ids:
        return []

    # 查询实体
    query = db.query(Entity).filter(Entity.document_ids.isnot(None))

    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)

    if search:
        query = query.filter(Entity.name.like(f"%{search}%"))

    # 按提及次数排序
    query = query.order_by(Entity.mention_count.desc())

    entities = query.limit(limit).all()

    # 过滤：只返回与项目相关的实体
    relevant_entities = []
    for ent in entities:
        if ent.document_ids and any(doc_id in doc_ids for doc_id in ent.document_ids):
            relevant_entities.append(ent)

    return relevant_entities


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity_detail(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """获取实体详情"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()

    if not entity:
        raise ResourceNotFoundException("Entity", entity_id)

    return entity


@router.get("/visualize")
async def get_graph_visualization(
    project_id: int,
    limit: int = Query(100, ge=10, le=500),
    db: Session = Depends(get_db)
):
    """
    获取知识图谱可视化数据（vis-network格式）

    返回格式:
    {
        "nodes": [{"id": 0, "label": "费孝通", "group": "person", ...}],
        "edges": [{"from": 0, "to": 1, "label": "studied", ...}],
        "stats": {"node_count": 50, "edge_count": 80}
    }
    """
    try:
        builder = create_knowledge_graph(db)
        graph_data = builder.get_graph_visualization_data(project_id, limit)

        return {
            "status": "success",
            "nodes": graph_data["nodes"],
            "edges": graph_data["edges"],
            "stats": {
                "node_count": len(graph_data["nodes"]),
                "edge_count": len(graph_data["edges"])
            }
        }
    except Exception as e:
        logger.error(f"获取可视化数据失败: {e}", exc_info=True)
        raise GraphException(message="获取可视化数据失败", operation="get_graph_visualization", details={"error": str(e)})


@router.get("/stats")
async def get_knowledge_graph_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识图谱统计信息
    """
    # 获取项目文档ID
    doc_ids = [doc.id for doc in db.query(ProjectDocument.id).filter(
        ProjectDocument.project_id == project_id
    ).all()]

    if not doc_ids:
        return {
            "total_entities": 0,
            "entity_types": {},
            "total_timeline_events": 0,
            "documents_processed": 0
        }

    # 统计实体
    all_entities = db.query(Entity).filter(Entity.document_ids.isnot(None)).all()

    # 过滤项目相关实体
    project_entities = [
        ent for ent in all_entities
        if ent.document_ids and any(doc_id in doc_ids for doc_id in ent.document_ids)
    ]

    # 按类型统计
    entity_types = {}
    for ent in project_entities:
        entity_types[ent.entity_type] = entity_types.get(ent.entity_type, 0) + 1

    # 统计时间线事件
    timeline_count = db.query(TimelineEvent).filter(
        TimelineEvent.document_ids.in_(doc_ids) if doc_ids else False
    ).count()

    # 已处理文档数
    processed_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.entities.isnot(None)
    ).count()

    return {
        "total_entities": len(project_entities),
        "entity_types": entity_types,
        "total_timeline_events": timeline_count,
        "documents_processed": processed_docs,
        "total_documents": len(doc_ids)
    }


@router.delete("/entities/{entity_id}")
async def delete_entity(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """删除实体"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()

    if not entity:
        raise ResourceNotFoundException("Entity", entity_id)

    db.delete(entity)
    db.commit()

    return {"message": f"实体 {entity.name} 已删除"}


# ==================== 旧API：兼容保留 ====================

@router.get("/projects/{project_id}/graph")
async def get_project_knowledge_graph(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取项目的知识图谱（旧版，使用v2规则引擎）"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ResourceNotFoundException("Project", project_id)

    # 获取项目的所有文档
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.status == "completed"
    ).all()

    if not documents:
        return {
            "nodes": [],
            "edges": [],
            "statistics": {
                "total_nodes": 0,
                "total_edges": 0,
                "node_types": {}
            },
            "message": "项目暂无已处理的文档"
        }

    # 转换为字典格式
    doc_dicts = []
    for doc in documents:
        doc_dicts.append({
            'id': doc.id,
            'text_content': doc.text_content or '',
            'file_name': doc.filename,
        })

    # 构建知识图谱
    try:
        graph = create_knowledge_graph().build_graph_from_documents(doc_dicts)
        return graph
    except Exception as e:
        logger.error(f"构建知识图谱失败: {e}")
        raise GraphException(message="构建知识图谱失败", operation="build_graph_from_documents", details={"error": str(e)})


@router.get("/projects/{project_id}/keywords")
async def get_project_keywords(
    project_id: int,
    top_k: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取项目的关键词"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ResourceNotFoundException("Project", project_id)

    # 获取项目的所有文档
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.status == "completed"
    ).all()

    if not documents:
        return []

    # 转换为字典列表格式
    doc_dicts = []
    for doc in documents:
        doc_dicts.append({
            'id': doc.id,
            'text_content': doc.text_content,
            'content': doc.text_content or ''
        })

    # 提取关键词
    try:
        keywords = create_knowledge_graph().extract_keywords(doc_dicts, top_k)
        return keywords
    except Exception as e:
        logger.error(f"提取关键词失败: {e}")
        raise GraphException(message="提取关键词失败", operation="extract_keywords", details={"error": str(e)})


@router.get("/documents/{document_id}/entities")
async def get_document_entities(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取单个文档的实体"""
    # 获取文档
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise ResourceNotFoundException("Document", document_id)

    if not document.text_content:
        return {"entities": {}, "message": "文档暂无文本内容"}

    # 提取实体
    try:
        entities = create_knowledge_graph().extract_entities(document.text_content)
        return {
            "entities": entities,
            "statistics": {
                entity_type: len(entity_list)
                for entity_type, entity_list in entities.items()
            }
        }
    except Exception as e:
        logger.error(f"提取实体失败: {e}")
        raise GraphException(message="提取实体失败", operation="extract_entities", details={"error": str(e)})
