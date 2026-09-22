"""
统一查询 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Query, Depends, Request

from app.schemas.response import success_response, ApiResponse
from app.services.unified_search import search, get_entity_graph


router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=ApiResponse)
async def unified_search(
    request: Request,
    q: str = Query(..., description="查询文本", min_length=1, max_length=200),
    project_id: int = Query(..., description="项目ID", ge=1),
    type: str = Query(
        "hybrid",
        description="搜索类型",
        enum=["keyword", "semantic", "hybrid", "entity"]
    ),
    top_k: int = Query(10, description="返回结果数", ge=1, le=100)
):
    """
    统一搜索接口

    支持4种搜索类型:
    - keyword: 关键词全文搜索
    - semantic: 语义向量检索
    - hybrid: 混合检索（推荐）
    - entity: 实体查询

    示例:
    - /search?q=山歌&project_id=1&type=hybrid
    - /search?q=十八洞村&project_id=1&type=entity
    """
    request_id = getattr(request.state, "request_id", None)

    result = search(
        query=q,
        project_id=project_id,
        search_type=type,
        top_k=top_k
    )

    return success_response(
        data=result,
        request_id=request_id
    )


@router.get("/entity/{entity_name}/graph", response_model=ApiResponse)
async def get_entity_relations(
    entity_name: str,
    project_id: int,
    request: Request
):
    """
    获取实体关系图谱

    返回指定实体的所有关系（入边和出边）

    示例:
    - /search/entity/十八洞村/graph?project_id=1
    """
    request_id = getattr(request.state, "request_id", None)

    result = get_entity_graph(entity_name, project_id)

    return success_response(
        data=result,
        request_id=request_id
    )
