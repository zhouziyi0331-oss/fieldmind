"""
知识图谱 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter()


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
