"""
统一知识图谱API - 整合所有知识图谱相关功能
合并自: knowledge_graph, knowledge_graph_v3, knowledge_graph_p3,
       knowledge_graph_enhanced, experience_graph, kg_visualization
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse
from app.services.knowledge_graph_builder import build_knowledge_graph

router = APIRouter(prefix="/api/kg", tags=["统一知识图谱"])

# ============================================================================
# 请求/响应模型
# ============================================================================

class KGBuildRequest(BaseModel):
    """知识图谱构建请求"""
    project_id: int = Field(..., description="项目ID")
    document_ids: Optional[List[int]] = Field(default=None, description="文档ID列表，为空则处理全部")
    force_rebuild: bool = Field(default=False, description="是否强制重建")
    extract_relations: bool = Field(default=True, description="是否提取关系")


class NodeCreateRequest(BaseModel):
    """节点创建请求"""
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="节点属性")


class EdgeCreateRequest(BaseModel):
    """边创建请求"""
    source_id: int = Field(..., description="源节点ID")
    target_id: int = Field(..., description="目标节点ID")
    relation: str = Field(..., description="关系类型")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="边属性")


# ============================================================================
# 1. 知识图谱构建
# ============================================================================

@router.post("/build", response_model=ApiResponse, summary="构建知识图谱")
async def build_kg(
    request: Request,
    kg_request: KGBuildRequest,
    db: Session = Depends(get_db)
):
    """
    构建或更新知识图谱

    - 提取实体和关系
    - 构建图谱结构
    - 支持增量更新
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        result = build_knowledge_graph(
            db=db,
            project_id=kg_request.project_id,
            document_ids=kg_request.document_ids,
            force_rebuild=kg_request.force_rebuild
        )

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reset/{project_id}", response_model=ApiResponse, summary="重置知识图谱")
async def reset_kg(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """删除指定项目的所有知识图谱数据"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity, EntityRelation

        # 删除关系
        relations = db.query(EntityRelation).filter(
            EntityRelation.project_id == project_id
        ).delete()

        # 删除实体
        entities = db.query(Entity).filter(
            Entity.project_id == project_id
        ).delete()

        db.commit()

        return success_response(
            data={
                "deleted_entities": entities,
                "deleted_relations": relations
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. 统计与概览
# ============================================================================

@router.get("/statistics", response_model=ApiResponse, summary="知识图谱统计")
async def get_kg_statistics(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取知识图谱统计信息

    - 节点数量
    - 边数量
    - 类型分布
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity, EntityRelation
        from sqlalchemy import func

        # 统计节点
        node_count = db.query(func.count(Entity.id)).filter(
            Entity.project_id == project_id
        ).scalar()

        # 统计边
        edge_count = db.query(func.count(EntityRelation.id)).filter(
            EntityRelation.project_id == project_id
        ).scalar()

        # 类型分布
        type_distribution = {}
        type_stats = db.query(
            Entity.type,
            func.count(Entity.id)
        ).filter(
            Entity.project_id == project_id
        ).group_by(Entity.type).all()

        for entity_type, count in type_stats:
            type_distribution[entity_type] = count

        result = {
            "node_count": node_count,
            "edge_count": edge_count,
            "type_distribution": type_distribution,
            "project_id": project_id
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. 节点操作
# ============================================================================

@router.get("/nodes", response_model=ApiResponse, summary="查询节点列表")
async def get_nodes(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """查询知识图谱中的节点"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity

        query = db.query(Entity).filter(Entity.project_id == project_id)

        if node_type:
            query = query.filter(Entity.type == node_type)

        if keyword:
            query = query.filter(Entity.name.contains(keyword))

        total = query.count()
        nodes = query.offset(offset).limit(limit).all()

        result = {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "properties": node.properties or {},
                    "created_at": node.created_at.isoformat() if node.created_at else None
                }
                for node in nodes
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}", response_model=ApiResponse, summary="获取节点详情")
async def get_node_detail(
    request: Request,
    node_id: int,
    db: Session = Depends(get_db)
):
    """获取单个节点的详细信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity, EntityRelation

        node = db.query(Entity).filter(Entity.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")

        # 获取关系
        outgoing = db.query(EntityRelation).filter(
            EntityRelation.source_id == node_id
        ).all()

        incoming = db.query(EntityRelation).filter(
            EntityRelation.target_id == node_id
        ).all()

        result = {
            "id": node.id,
            "name": node.name,
            "type": node.type,
            "properties": node.properties or {},
            "outgoing_edges": len(outgoing),
            "incoming_edges": len(incoming),
            "created_at": node.created_at.isoformat() if node.created_at else None
        }

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes", response_model=ApiResponse, summary="创建节点")
async def create_node(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    node_data: NodeCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """手动创建知识图谱节点"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity

        node = Entity(
            name=node_data.name,
            type=node_data.type,
            project_id=project_id,
            properties=node_data.properties
        )

        db.add(node)
        db.commit()
        db.refresh(node)

        return success_response(
            data={
                "id": node.id,
                "name": node.name,
                "type": node.type
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/nodes/{node_id}", response_model=ApiResponse, summary="更新节点")
async def update_node(
    request: Request,
    node_id: int,
    node_data: NodeCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """更新节点信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity

        node = db.query(Entity).filter(Entity.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")

        node.name = node_data.name
        node.type = node_data.type
        if node_data.properties:
            node.properties = node_data.properties

        db.commit()
        db.refresh(node)

        return success_response(
            data={"id": node.id, "name": node.name, "type": node.type},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes/{node_id}", response_model=ApiResponse, summary="删除节点")
async def delete_node(
    request: Request,
    node_id: int,
    db: Session = Depends(get_db)
):
    """删除节点及其所有关系"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity, EntityRelation

        # 删除关系
        db.query(EntityRelation).filter(
            (EntityRelation.source_id == node_id) |
            (EntityRelation.target_id == node_id)
        ).delete()

        # 删除节点
        node = db.query(Entity).filter(Entity.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")

        db.delete(node)
        db.commit()

        return success_response(
            data={"deleted_node_id": node_id},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. 边/关系操作
# ============================================================================

@router.get("/edges", response_model=ApiResponse, summary="查询边列表")
async def get_edges(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """查询知识图谱中的边/关系"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import EntityRelation

        query = db.query(EntityRelation).filter(
            EntityRelation.project_id == project_id
        )

        if relation_type:
            query = query.filter(EntityRelation.relation == relation_type)

        total = query.count()
        edges = query.offset(offset).limit(limit).all()

        result = {
            "edges": [
                {
                    "id": edge.id,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "relation": edge.relation,
                    "properties": edge.properties or {}
                }
                for edge in edges
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges", response_model=ApiResponse, summary="创建边")
async def create_edge(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    edge_data: EdgeCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """手动创建知识图谱中的边/关系"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import EntityRelation

        edge = EntityRelation(
            source_id=edge_data.source_id,
            target_id=edge_data.target_id,
            relation=edge_data.relation,
            project_id=project_id,
            properties=edge_data.properties
        )

        db.add(edge)
        db.commit()
        db.refresh(edge)

        return success_response(
            data={
                "id": edge.id,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "relation": edge.relation
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/edges/{edge_id}", response_model=ApiResponse, summary="删除边")
async def delete_edge(
    request: Request,
    edge_id: int,
    db: Session = Depends(get_db)
):
    """删除知识图谱中的边/关系"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import EntityRelation

        edge = db.query(EntityRelation).filter(EntityRelation.id == edge_id).first()
        if not edge:
            raise HTTPException(status_code=404, detail="边不存在")

        db.delete(edge)
        db.commit()

        return success_response(
            data={"deleted_edge_id": edge_id},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. 查询与搜索
# ============================================================================

@router.get("/search", response_model=ApiResponse, summary="搜索知识图谱")
async def search_kg(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    keyword: str = Query(..., description="搜索关键词"),
    search_type: str = Query("all", description="搜索类型: nodes, edges, all"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """在知识图谱中搜索节点和关系"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity, EntityRelation

        result = {"nodes": [], "edges": []}

        if search_type in ["nodes", "all"]:
            nodes = db.query(Entity).filter(
                Entity.project_id == project_id,
                Entity.name.contains(keyword)
            ).limit(limit).all()

            result["nodes"] = [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type
                }
                for node in nodes
            ]

        if search_type in ["edges", "all"]:
            edges = db.query(EntityRelation).filter(
                EntityRelation.project_id == project_id,
                EntityRelation.relation.contains(keyword)
            ).limit(limit).all()

            result["edges"] = [
                {
                    "id": edge.id,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "relation": edge.relation
                }
                for edge in edges
            ]

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subgraph/{node_id}", response_model=ApiResponse, summary="获取子图")
async def get_subgraph(
    request: Request,
    node_id: int,
    depth: int = Query(1, ge=1, le=3, description="遍历深度"),
    db: Session = Depends(get_db)
):
    """获取以指定节点为中心的子图"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity, EntityRelation

        # 简单实现：获取直接邻居
        node = db.query(Entity).filter(Entity.id == node_id).first()
        if not node:
            raise HTTPException(status_code=404, detail="节点不存在")

        # 获取相关边
        edges = db.query(EntityRelation).filter(
            (EntityRelation.source_id == node_id) |
            (EntityRelation.target_id == node_id)
        ).all()

        # 获取邻居节点
        neighbor_ids = set()
        for edge in edges:
            neighbor_ids.add(edge.source_id)
            neighbor_ids.add(edge.target_id)
        neighbor_ids.discard(node_id)

        neighbors = db.query(Entity).filter(
            Entity.id.in_(neighbor_ids)
        ).all()

        result = {
            "center_node": {
                "id": node.id,
                "name": node.name,
                "type": node.type
            },
            "neighbors": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.type
                }
                for n in neighbors
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "relation": e.relation
                }
                for e in edges
            ]
        }

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 6. 可视化数据
# ============================================================================

@router.get("/visualization/{project_id}", response_model=ApiResponse, summary="获取可视化数据")
async def get_visualization_data(
    request: Request,
    project_id: int,
    max_nodes: int = Query(100, ge=10, le=500, description="最大节点数"),
    db: Session = Depends(get_db)
):
    """
    获取用于前端可视化的图谱数据

    返回格式适配常见图可视化库（如ECharts, D3.js等）
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity, EntityRelation

        # 获取节点
        nodes = db.query(Entity).filter(
            Entity.project_id == project_id
        ).limit(max_nodes).all()

        node_ids = {node.id for node in nodes}

        # 获取这些节点之间的边
        edges = db.query(EntityRelation).filter(
            EntityRelation.project_id == project_id,
            EntityRelation.source_id.in_(node_ids),
            EntityRelation.target_id.in_(node_ids)
        ).all()

        result = {
            "nodes": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.type,
                    "category": node.type,  # 用于前端分类
                    "value": 1  # 节点大小
                }
                for node in nodes
            ],
            "edges": [
                {
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "relation": edge.relation,
                    "value": 1  # 边权重
                }
                for edge in edges
            ],
            "categories": list(set(node.type for node in nodes))
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 7. 类型管理
# ============================================================================

@router.get("/types/nodes", response_model=ApiResponse, summary="获取节点类型列表")
async def get_node_types(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """获取项目中所有的节点类型"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import Entity
        from sqlalchemy import func, distinct

        types = db.query(
            Entity.type,
            func.count(Entity.id).label('count')
        ).filter(
            Entity.project_id == project_id
        ).group_by(Entity.type).all()

        result = {
            "types": [
                {"type": t, "count": c}
                for t, c in types
            ]
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types/relations", response_model=ApiResponse, summary="获取关系类型列表")
async def get_relation_types(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """获取项目中所有的关系类型"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.entity import EntityRelation
        from sqlalchemy import func

        types = db.query(
            EntityRelation.relation,
            func.count(EntityRelation.id).label('count')
        ).filter(
            EntityRelation.project_id == project_id
        ).group_by(EntityRelation.relation).all()

        result = {
            "types": [
                {"relation": r, "count": c}
                for r, c in types
            ]
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
