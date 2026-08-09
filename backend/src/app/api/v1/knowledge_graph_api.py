"""
知识图谱API端点
提供图谱构建、查询和可视化接口
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["知识图谱"])


class GraphStatsResponse(BaseModel):
    """图谱统计响应"""
    node_count: int
    edge_count: int
    entity_types: dict
    relation_types: dict
    density: float
    is_connected: bool


class EntityQueryRequest(BaseModel):
    """实体查询请求"""
    entity_name: str
    max_depth: int = 2


class GraphDataResponse(BaseModel):
    """图谱数据响应"""
    nodes: List[dict]
    edges: List[dict]
    stats: dict


@router.get("/stats", response_model=GraphStatsResponse)
async def get_graph_stats():
    """
    获取知识图谱统计信息

    返回:
    - 节点数量
    - 边数量
    - 实体类型分布
    - 关系类型分布
    - 图谱密度
    """
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service

        kg = get_knowledge_graph_service()
        stats = kg.get_statistics()

        return stats

    except Exception as e:
        logger.error(f"获取图谱统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data", response_model=GraphDataResponse)
async def get_graph_data():
    """
    获取完整图谱数据

    用于前端可视化展示
    """
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service

        kg = get_knowledge_graph_service()
        data = kg.get_graph_data()

        return data

    except Exception as e:
        logger.error(f"获取图谱数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/related")
async def query_related_entities(request: EntityQueryRequest):
    """
    查询相关实体

    Args:
        entity_name: 实体名称
        max_depth: 最大深度（默认2）

    返回:
        相关实体列表
    """
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service

        kg = get_knowledge_graph_service()
        related = kg.query_related_entities(request.entity_name, request.max_depth)

        return {
            'entity': request.entity_name,
            'related': related,
            'count': len(related)
        }

    except Exception as e:
        logger.error(f"查询相关实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build/{document_id}")
async def build_graph_for_document(document_id: int):
    """
    为指定文档构建知识图谱

    Args:
        document_id: 文档ID

    返回:
        构建结果
    """
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service
        from app.core.database import SessionLocal
        from sqlalchemy import text

        kg = get_knowledge_graph_service()
        db = SessionLocal()

        # 获取文档内容
        result = db.execute(
            text("SELECT text_content FROM documents WHERE id = :id"),
            {"id": document_id}
        ).fetchone()

        if not result or not result[0]:
            raise HTTPException(status_code=404, detail="文档不存在或无内容")

        text_content = result[0]

        # 提取实体和关系
        entities, relations = kg.extract_entities_and_relations(text_content, document_id)

        # 添加到图谱
        kg.add_entities_and_relations(entities, relations)

        db.close()

        return {
            'success': True,
            'document_id': document_id,
            'entities_extracted': len(entities),
            'relations_extracted': len(relations),
            'message': '知识图谱构建成功'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"构建知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebuild")
async def rebuild_entire_graph():
    """
    重新构建完整知识图谱

    处理所有已完成的文档，重新提取实体和关系
    """
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service
        from app.core.database import SessionLocal
        from sqlalchemy import text

        kg = get_knowledge_graph_service()
        db = SessionLocal()

        # 获取所有completed的文档
        results = db.execute(
            text("SELECT id, text_content FROM documents WHERE status = 'completed' AND text_content IS NOT NULL")
        ).fetchall()

        total_entities = 0
        total_relations = 0

        for doc_id, text_content in results:
            try:
                entities, relations = kg.extract_entities_and_relations(text_content, doc_id)
                kg.add_entities_and_relations(entities, relations)

                total_entities += len(entities)
                total_relations += len(relations)

            except Exception as e:
                logger.error(f"处理文档 {doc_id} 失败: {e}")
                continue

        db.close()

        return {
            'success': True,
            'documents_processed': len(results),
            'total_entities': total_entities,
            'total_relations': total_relations,
            'graph_stats': kg.get_statistics()
        }

    except Exception as e:
        logger.error(f"重建知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/html")
async def export_visualization():
    """
    导出知识图谱可视化HTML

    返回可访问的HTML文件路径
    """
    try:
        from app.services.knowledge_graph_service import get_knowledge_graph_service
        import os

        kg = get_knowledge_graph_service()

        # 导出路径
        output_dir = "/Users/alwan/FieldMind-Rebuild/fieldmind-backend/static"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "knowledge_graph.html")
        kg.export_for_visualization(output_path)

        return {
            'success': True,
            'file_path': output_path,
            'url': '/static/knowledge_graph.html',
            'message': '可视化导出成功'
        }

    except Exception as e:
        logger.error(f"导出可视化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
