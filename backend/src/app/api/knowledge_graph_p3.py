"""
交互式知识图谱 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from pydantic import BaseModel, Field

from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.knowledge_graph import (
    InteractiveKnowledgeGraph,
    GraphVisualizationService,
    NodeType,
    RelationType
)

router = APIRouter(prefix="/knowledge-graph", tags=["knowledge-graph"])

# 全局图实例（实际应用中应该持久化到数据库）
_graph_instances = {}


def get_graph_instance(project_id: str) -> InteractiveKnowledgeGraph:
    """获取或创建图实例"""
    if project_id not in _graph_instances:
        _graph_instances[project_id] = InteractiveKnowledgeGraph()
    return _graph_instances[project_id]


# Request/Response Models
class CreateNodeRequest(BaseModel):
    node_id: str = Field(..., description="节点 ID")
    label: str = Field(..., description="节点标签")
    node_type: str = Field(..., description="节点类型")
    properties: dict = Field(default_factory=dict, description="节点属性")
    metadata: dict = Field(default_factory=dict, description="元数据")


class UpdateNodeRequest(BaseModel):
    label: Optional[str] = Field(None, description="新标签")
    properties: Optional[dict] = Field(None, description="新属性")
    metadata: Optional[dict] = Field(None, description="新元数据")


class CreateEdgeRequest(BaseModel):
    edge_id: str = Field(..., description="边 ID")
    source_id: str = Field(..., description="源节点 ID")
    target_id: str = Field(..., description="目标节点 ID")
    relation_type: str = Field(..., description="关系类型")
    weight: float = Field(1.0, description="权重")
    properties: dict = Field(default_factory=dict, description="边属性")


@router.post("/projects/{project_id}/nodes")
async def create_node(
    project_id: str,
    request: CreateNodeRequest,
    current_user: User = Depends(get_current_user)
):
    """创建节点"""
    try:
        graph = get_graph_instance(project_id)
        node = graph.add_node(
            node_id=request.node_id,
            label=request.label,
            node_type=NodeType(request.node_type),
            properties=request.properties,
            metadata=request.metadata
        )
        return {"node": node.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/projects/{project_id}/nodes/{node_id}")
async def get_node(
    project_id: str,
    node_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取节点"""
    graph = get_graph_instance(project_id)
    node = graph.get_node(node_id)

    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    return {"node": node.to_dict()}


@router.put("/projects/{project_id}/nodes/{node_id}")
async def update_node(
    project_id: str,
    node_id: str,
    request: UpdateNodeRequest,
    current_user: User = Depends(get_current_user)
):
    """更新节点"""
    graph = get_graph_instance(project_id)
    node = graph.update_node(
        node_id=node_id,
        label=request.label,
        properties=request.properties,
        metadata=request.metadata
    )

    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    return {"node": node.to_dict()}


@router.delete("/projects/{project_id}/nodes/{node_id}")
async def delete_node(
    project_id: str,
    node_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除节点"""
    graph = get_graph_instance(project_id)
    success = graph.remove_node(node_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    return {"message": "Node deleted successfully"}


@router.post("/projects/{project_id}/edges")
async def create_edge(
    project_id: str,
    request: CreateEdgeRequest,
    current_user: User = Depends(get_current_user)
):
    """创建边"""
    try:
        graph = get_graph_instance(project_id)
        edge = graph.add_edge(
            edge_id=request.edge_id,
            source_id=request.source_id,
            target_id=request.target_id,
            relation_type=RelationType(request.relation_type),
            weight=request.weight,
            properties=request.properties
        )

        if not edge:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create edge"
            )

        return {"edge": edge.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/projects/{project_id}/edges/{edge_id}")
async def delete_edge(
    project_id: str,
    edge_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除边"""
    graph = get_graph_instance(project_id)
    success = graph.remove_edge(edge_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Edge not found")

    return {"message": "Edge deleted successfully"}


@router.get("/projects/{project_id}/visualization")
async def get_visualization(
    project_id: str,
    center_node_id: Optional[str] = Query(None, description="中心节点 ID"),
    depth: int = Query(2, ge=1, le=5, description="深度"),
    max_nodes: int = Query(100, ge=10, le=500, description="最大节点数"),
    layout: str = Query("force", description="布局算法 (force/circular/hierarchical)"),
    current_user: User = Depends(get_current_user)
):
    """
    获取图谱可视化数据

    支持三种布局算法：
    - force: 力导向布局
    - circular: 圆形布局
    - hierarchical: 层次布局
    """
    graph = get_graph_instance(project_id)
    viz_service = GraphVisualizationService(graph)

    data = viz_service.generate_visualization_data(
        center_node_id=center_node_id,
        depth=depth,
        max_nodes=max_nodes,
        layout=layout
    )

    return data


@router.get("/projects/{project_id}/nodes/{node_id}/details")
async def get_node_details(
    project_id: str,
    node_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取节点详细信息"""
    graph = get_graph_instance(project_id)
    viz_service = GraphVisualizationService(graph)

    details = viz_service.get_node_details(node_id)
    if not details:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    return details


@router.get("/projects/{project_id}/nodes/{node_id}/neighbors")
async def get_neighbors(
    project_id: str,
    node_id: str,
    direction: str = Query("both", description="方向 (outgoing/incoming/both)"),
    relation_type: Optional[str] = Query(None, description="关系类型过滤"),
    current_user: User = Depends(get_current_user)
):
    """获取邻居节点"""
    graph = get_graph_instance(project_id)

    relation = RelationType(relation_type) if relation_type else None
    neighbors = graph.get_neighbors(node_id, direction, relation)

    return {
        "neighbors": [n.to_dict() for n in neighbors],
        "count": len(neighbors)
    }


@router.get("/projects/{project_id}/search")
async def search_nodes(
    project_id: str,
    query: str = Query(..., min_length=1, description="搜索查询"),
    node_type: Optional[str] = Query(None, description="节点类型过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_current_user)
):
    """搜索节点"""
    graph = get_graph_instance(project_id)
    viz_service = GraphVisualizationService(graph)

    results = viz_service.search_nodes(query, node_type, limit)

    return {
        "results": results,
        "count": len(results)
    }


@router.get("/projects/{project_id}/path")
async def find_path(
    project_id: str,
    start_id: str = Query(..., description="起始节点 ID"),
    end_id: str = Query(..., description="目标节点 ID"),
    current_user: User = Depends(get_current_user)
):
    """查找两个节点之间的最短路径"""
    graph = get_graph_instance(project_id)
    viz_service = GraphVisualizationService(graph)

    path = viz_service.get_shortest_path(start_id, end_id)
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No path found between nodes"
        )

    return path


@router.get("/projects/{project_id}/statistics")
async def get_statistics(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取图谱统计信息"""
    graph = get_graph_instance(project_id)
    return graph.get_statistics()


@router.get("/projects/{project_id}/export")
async def export_graph(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """导出整个图谱"""
    graph = get_graph_instance(project_id)
    return graph.export_graph()


@router.post("/projects/{project_id}/import")
async def import_graph(
    project_id: str,
    graph_data: dict,
    current_user: User = Depends(get_current_user)
):
    """导入图谱数据"""
    graph = get_graph_instance(project_id)
    success = graph.import_graph(graph_data)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to import graph data"
        )

    return {"message": "Graph imported successfully"}


@router.get("/types/nodes")
async def get_node_types(current_user: User = Depends(get_current_user)):
    """获取所有节点类型"""
    return {
        "node_types": [t.value for t in NodeType]
    }


@router.get("/types/relations")
async def get_relation_types(current_user: User = Depends(get_current_user)):
    """获取所有关系类型"""
    return {
        "relation_types": [t.value for t in RelationType]
    }
