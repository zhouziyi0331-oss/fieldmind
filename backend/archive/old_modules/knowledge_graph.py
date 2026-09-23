"""
知识图谱 API - 链路十一：实体提取与知识图谱构建
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.models.project import ProjectDocument, Project
from app.models.entity import Entity, EntityRelation
from app.models.timeline import TimelineEvent
from app.services.knowledge_graph_service import get_knowledge_graph_service
from app.services.knowledge_graph_builder import get_knowledge_graph_builder
from app.schemas.response import success_response, error_response

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
    aliases: Optional[List[str]] = None
    properties: Optional[dict] = None
    description: Optional[str] = None
    confidence: float = 0.0
    mention_count: int = 0
    document_ids: Optional[List[int]] = None


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
        builder = get_knowledge_graph_builder(db)

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

            return success_response(
                data=total_stats,
                message=f"处理完成：{total_stats['documents_processed']} 个文档"
            )
        else:
            # 处理项目所有文档
            stats = builder.build_from_project(request.project_id, request.force_rebuild)

            return success_response(
                data=stats,
                message=f"项目知识图谱构建完成：{stats['documents_processed']} 个文档"
            )

    except Exception as e:
        logger.error(f"构建知识图谱失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"构建失败: {str(e)}")


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

    # 查询实体。实体通过 document_ids 和 metadata.project_ids 关联项目。
    query = db.query(Entity).filter(Entity.document_ids.isnot(None))

    if entity_type:
        query = query.filter(Entity.entity_type == entity_type)

    if search:
        query = query.filter(Entity.name.like(f"%{search}%"))

    # 按提及次数排序；项目过滤在 Python 中完成，兼容 SQLite JSON。
    entities = query.order_by(Entity.mention_count.desc()).all()
    relevant_entities = []
    for ent in entities:
        metadata = ent.metadata_json or {}
        if (
            project_id in set(metadata.get("project_ids") or [])
            or set(ent.document_ids or []).intersection(doc_ids)
        ):
            relevant_entities.append(ent)
        if len(relevant_entities) >= limit:
            break

    return relevant_entities


@router.get("/entities/{entity_id}", response_model=EntityResponse)
async def get_entity_detail(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """获取实体详情"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")

    return entity


@router.get("/visualize")
async def get_graph_visualization(
    project_id: Optional[int] = None,
    entity_id: Optional[str] = None,
    limit: int = Query(100, ge=10, le=500),
    db: Session = Depends(get_db)
):
    """
    获取知识图谱可视化数据（前端兼容格式）

    返回格式:
    {
        "status": "success",
        "nodes": [{"id": "entity_123", "label": "费孝通", "type": "person", ...}],
        "edges": [{"id": "edge_1", "source": "entity_123", "target": "entity_456", "type": "studied", ...}],
    }
    """
    try:
        builder = get_knowledge_graph_builder(db)
        graph_data = builder.get_graph_visualization_data(project_id, limit)

        # 转换节点格式以匹配前端期望
        nodes = []
        for node in graph_data["nodes"]:
            nodes.append({
                "id": str(node.get("entity_id", node["id"])),  # 使用 entity_id 作为字符串 ID
                "label": node["label"],
                "type": node.get("group", "unknown"),  # group -> type
                "properties": {
                    "mention_count": str(node.get("value", 0)),
                    "title": node.get("title", "")
                }
            })

        # 转换边格式以匹配前端期望
        edges = []
        # 创建 ID 到 entity_id 的映射
        id_to_entity = {node["id"]: str(node.get("entity_id", node["id"])) for node in graph_data["nodes"]}

        for edge in graph_data["edges"]:
            source_id = id_to_entity.get(edge.get("from"), str(edge.get("from")))
            target_id = id_to_entity.get(edge.get("to"), str(edge.get("to")))
            edges.append({
                "id": str(edge.get("id", f"{source_id}_{target_id}")),
                "source": source_id,  # from -> source
                "target": target_id,  # to -> target
                "type": edge.get("label", "related"),  # label -> type
                "properties": {
                    "width": str(edge.get("width", 1))
                }
            })

        return success_response(
            data={
                "nodes": nodes,
                "edges": edges
            }
        )
    except Exception as e:
        logger.error(f"获取可视化数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


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
        return success_response(
            data={
                "total_entities": 0,
                "entity_types": {},
                "total_timeline_events": 0,
                "documents_processed": 0
            }
        )

    # 统计实体：只统计当前项目真实关联的实体。
    all_entities = db.query(Entity).filter(Entity.document_ids.isnot(None)).all()
    project_entities = [
        ent for ent in all_entities
        if (
            project_id in set((ent.metadata_json or {}).get("project_ids") or [])
            or set(ent.document_ids or []).intersection(doc_ids)
        )
    ]

    # 按类型统计
    entity_types = {}
    for ent in project_entities:
        entity_types[ent.type] = entity_types.get(ent.type, 0) + 1

    # 统计时间线事件
    timeline_count = 0
    if doc_ids:
        for event in db.query(TimelineEvent).all():
            event_document_ids = set(event.document_ids or [])
            if event_document_ids.intersection(doc_ids):
                timeline_count += 1

    # 已处理文档数
    processed_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.entities.isnot(None)
    ).count()

    return success_response(
        data={
            "total_entities": len(project_entities),
            "entity_types": entity_types,
            "total_timeline_events": timeline_count,
            "documents_processed": processed_docs,
            "total_documents": len(doc_ids)
        }
    )


@router.delete("/entities/{entity_id}/")
async def delete_entity(
    entity_id: str,
    db: Session = Depends(get_db)
):
    """删除实体"""
    entity = db.query(Entity).filter(Entity.id == entity_id).first()

    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")

    db.delete(entity)
    db.commit()

    return success_response(message=f"实体 {entity.name} 已删除")


# ==================== 旧API：兼容保留 ====================

@router.get("/projects/{project_id}/graph/")
async def get_project_knowledge_graph(
    project_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取项目的知识图谱（旧版，使用v2规则引擎）"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取项目的所有文档
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.status == "completed"
    ).all()

    if not documents:
        return success_response(
            data={
                "nodes": [],
                "edges": [],
                "statistics": {
                    "total_nodes": 0,
                    "total_edges": 0,
                    "node_types": {}
                }
            },
            message="项目暂无已处理的文档"
        )

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
        knowledge_graph_service = get_knowledge_graph_service()

        # 使用新API：从提取的实体构建图谱
        all_entities = []
        all_relations = []

        for doc_dict in doc_dicts:
            text = doc_dict.get('text_content', '')
            if text:
                # 提取实体和关系
                entities, relations = knowledge_graph_service.extract_entities_and_relations(
                    text,
                    document_id=doc_dict['id'],
                    use_llm=False  # 使用规则方法，更快
                )
                all_entities.extend(entities)
                all_relations.extend(relations)

        # 添加到图谱
        knowledge_graph_service.add_entities_and_relations(all_entities, all_relations)

        # 导出图谱数据
        graph = knowledge_graph_service.export_graph_data()
        return graph
    except Exception as e:
        logger.error(f"构建知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=f"构建知识图谱失败: {str(e)}")


@router.get("/projects/{project_id}/keywords/")
async def get_project_keywords(
    project_id: int,
    top_k: int = 50,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取项目的关键词"""
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

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

    # 提取关键词（使用简单的实体频率统计）
    try:
        from collections import Counter
        knowledge_graph_service = get_knowledge_graph_service()

        entity_freq = Counter()
        for doc_dict in doc_dicts:
            text = doc_dict.get('text_content', '')
            if text:
                entities, _ = knowledge_graph_service.extract_entities_and_relations(text, use_llm=False)
                for entity in entities:
                    entity_freq[entity.name] += 1

        # 转换为关键词格式
        keywords = [
            {'keyword': name, 'frequency': freq, 'type': 'entity'}
            for name, freq in entity_freq.most_common(top_k)
        ]
        return keywords
    except Exception as e:
        logger.error(f"提取关键词失败: {e}")
        raise HTTPException(status_code=500, detail=f"提取关键词失败: {str(e)}")


@router.get("/documents/{document_id}/entities/")
async def get_document_entities(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取单个文档的实体"""
    # 获取文档
    document = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not document.text_content:
        return success_response(data={"entities": {}}, message="文档暂无文本内容")

    # 提取实体
    try:
        entities = knowledge_graph_service.extract_entities(document.text_content)
        return success_response(
            data={
                "entities": entities,
                "statistics": {
                    entity_type: len(entity_list)
                    for entity_type, entity_list in entities.items()
                }
            }
        )
    except Exception as e:
        logger.error(f"提取实体失败: {e}")
        raise HTTPException(status_code=500, detail=f"提取实体失败: {str(e)}")
