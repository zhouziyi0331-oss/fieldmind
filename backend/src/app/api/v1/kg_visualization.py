"""
知识图谱可视化API
提供9步骤管道到知识图谱的可视化接口
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.unified_kg_builder import UnifiedKnowledgeGraphBuilder

router = APIRouter(prefix="/api/v1/knowledge-graph", tags=["knowledge-graph"])


@router.get("/document/{dirty_doc_id}")
async def get_document_knowledge_graph(
    dirty_doc_id: int,
    include_steps: Optional[str] = Query(None, description="包含的步骤，逗号分隔，如: 3,4,5"),
    db: Session = Depends(get_db)
):
    """
    获取文档的知识图谱

    从9步骤统一管道构建可视化知识图谱

    **参数说明**:
    - dirty_doc_id: 脏数据文档ID
    - include_steps: 可选，包含哪些步骤的输出（1-9），如 "3,4,5"

    **返回格式**:
    ```json
    {
        "nodes": [
            {
                "id": "entity_1",
                "name": "张三",
                "type": "PERSON",
                "is_core": true,
                "layer": 1,
                "x": 150.5,
                "y": 200.3,
                ...
            }
        ],
        "edges": [
            {
                "id": "relation_1",
                "source": "entity_1",
                "target": "entity_2",
                "relation_type": "工作于",
                "weight": 0.9
            }
        ],
        "statistics": {
            "total_nodes": 10,
            "total_edges": 15,
            "core_nodes": 3,
            "node_type_stats": {"PERSON": 4, "ORG": 3},
            "average_degree": 3.0
        },
        "metadata": {
            "dirty_doc_id": 1,
            "source_type": "video",
            "pipeline_current_step": 7
        }
    }
    ```
    """
    try:
        # 解析include_steps
        steps = None
        if include_steps:
            steps = [int(s.strip()) for s in include_steps.split(",")]

        builder = UnifiedKnowledgeGraphBuilder(db)
        graph_data = await builder.build_graph_from_pipeline(dirty_doc_id, include_steps=steps)

        return graph_data

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"构建知识图谱失败: {str(e)}")


@router.get("/document/{dirty_doc_id}/snapshot")
async def create_knowledge_graph_snapshot(
    dirty_doc_id: int,
    name: str = Query(..., description="快照名称"),
    description: Optional[str] = Query(None, description="快照描述"),
    db: Session = Depends(get_db)
):
    """
    创建知识图谱快照

    保存当前知识图谱的完整状态，用于版本管理和后续对比

    **用途**:
    - 记录不同时间点的知识图谱状态
    - 对比管道不同步骤的输出效果
    - 导出用于其他系统
    """
    try:
        builder = UnifiedKnowledgeGraphBuilder(db)
        snapshot = await builder.create_snapshot(dirty_doc_id, name, description)

        return {
            "success": True,
            "snapshot": snapshot
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建快照失败: {str(e)}")


@router.get("/compare")
async def compare_knowledge_graphs(
    doc1: int = Query(..., description="第一个文档的ID"),
    doc2: int = Query(..., description="第二个文档的ID"),
    db: Session = Depends(get_db)
):
    """
    比较两个文档的知识图谱

    分析两个文档的知识图谱之间的异同

    **返回**:
    - 共同节点和边
    - 各自独有的节点和边
    - 相似度评分

    **应用场景**:
    - 对比不同数据源的相关性
    - 发现重复或矛盾的信息
    - 合并多个数据源
    """
    try:
        builder = UnifiedKnowledgeGraphBuilder(db)
        comparison = await builder.compare_graphs(doc1, doc2)

        return comparison

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"比较图谱失败: {str(e)}")


@router.get("/document/{dirty_doc_id}/stats")
async def get_graph_statistics(
    dirty_doc_id: int,
    db: Session = Depends(get_db)
):
    """
    获取知识图谱统计信息（不返回完整图谱数据）

    适合用于仪表板展示，快速获取图谱概况
    """
    try:
        builder = UnifiedKnowledgeGraphBuilder(db)
        graph_data = await builder.build_graph_from_pipeline(dirty_doc_id)

        return {
            "statistics": graph_data["statistics"],
            "metadata": graph_data["metadata"]
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


@router.get("/document/{dirty_doc_id}/layers")
async def get_graph_by_layer(
    dirty_doc_id: int,
    layer: int = Query(..., description="层级：1=核心，2=次要，3=细节"),
    db: Session = Depends(get_db)
):
    """
    按层级获取知识图谱

    返回指定层级的节点和边，用于分层可视化

    **层级说明**:
    - Layer 1: 核心节点（核心事件、核心实体）
    - Layer 2: 次要节点（一般实体、次要事件）
    - Layer 3: 细节节点（属性、补充信息）
    """
    try:
        if layer not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="层级必须是 1, 2, 或 3")

        builder = UnifiedKnowledgeGraphBuilder(db)
        graph_data = await builder.build_graph_from_pipeline(dirty_doc_id)

        # 过滤指定层级的节点
        filtered_nodes = [n for n in graph_data["nodes"] if n.get("layer") == layer]
        node_ids = set(n["id"] for n in filtered_nodes)

        # 过滤相关的边
        filtered_edges = [
            e for e in graph_data["edges"]
            if e.get("source") in node_ids and e.get("target") in node_ids
        ]

        return {
            "layer": layer,
            "nodes": filtered_nodes,
            "edges": filtered_edges,
            "count": {
                "nodes": len(filtered_nodes),
                "edges": len(filtered_edges)
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分层图谱失败: {str(e)}")


@router.get("/document/{dirty_doc_id}/export")
async def export_knowledge_graph(
    dirty_doc_id: int,
    format: str = Query("json", description="导出格式: json, graphml, cypher"),
    db: Session = Depends(get_db)
):
    """
    导出知识图谱为不同格式

    **支持格式**:
    - json: 标准JSON格式（默认）
    - graphml: GraphML格式（用于Gephi、Cytoscape等工具）
    - cypher: Neo4j Cypher导入语句
    """
    try:
        builder = UnifiedKnowledgeGraphBuilder(db)
        graph_data = await builder.build_graph_from_pipeline(dirty_doc_id)

        if format == "json":
            return graph_data

        elif format == "graphml":
            # 生成GraphML格式
            graphml = _convert_to_graphml(graph_data)
            return {"format": "graphml", "data": graphml}

        elif format == "cypher":
            # 生成Cypher语句
            cypher = _convert_to_cypher(graph_data)
            return {"format": "cypher", "statements": cypher}

        else:
            raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出图谱失败: {str(e)}")


def _convert_to_graphml(graph_data: dict) -> str:
    """将图谱数据转换为GraphML格式"""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
    lines.append('  <graph id="G" edgedefault="directed">')

    # 节点
    for node in graph_data["nodes"]:
        lines.append(f'    <node id="{node["id"]}">')
        lines.append(f'      <data key="name">{node["name"]}</data>')
        lines.append(f'      <data key="type">{node["type"]}</data>')
        lines.append('    </node>')

    # 边
    for edge in graph_data["edges"]:
        lines.append(f'    <edge source="{edge["source"]}" target="{edge["target"]}">')
        lines.append(f'      <data key="relation">{edge["relation_type"]}</data>')
        lines.append('    </edge>')

    lines.append('  </graph>')
    lines.append('</graphml>')

    return "\n".join(lines)


def _convert_to_cypher(graph_data: dict) -> List[str]:
    """将图谱数据转换为Neo4j Cypher语句"""
    statements = []

    # 创建节点
    for node in graph_data["nodes"]:
        props = f"name: '{node['name']}', type: '{node['type']}', layer: {node.get('layer', 2)}"
        statements.append(
            f"CREATE (n:{node['type']} {{id: '{node['id']}', {props}}})"
        )

    # 创建关系
    for edge in graph_data["edges"]:
        statements.append(
            f"MATCH (a {{id: '{edge['source']}'}}), (b {{id: '{edge['target']}'}}) "
            f"CREATE (a)-[r:{edge['relation_type']}]->(b)"
        )

    return statements
