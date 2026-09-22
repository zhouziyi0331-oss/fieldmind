"""
可视化API路由
提供数据可视化生成接口
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from app.schemas.response import success_response, error_response
import logging

from app.services.visualization_service import get_visualization_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic模型
class PlotlyBarRequest(BaseModel):
    data: Dict[str, List]
    x_key: str
    y_key: str
    title: str = "Bar Chart"


class PlotlyLineRequest(BaseModel):
    data: Dict[str, List]
    x_key: str
    y_keys: List[str]
    title: str = "Line Chart"


class PlotlyScatter3DRequest(BaseModel):
    data: Dict[str, List]
    x_key: str
    y_key: str
    z_key: str
    color_key: Optional[str] = None
    title: str = "3D Scatter Plot"


class PyechartsPieRequest(BaseModel):
    data: List[List]
    title: str = "饼图"


class PyechartsGraphRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    links: List[Dict[str, Any]]
    title: str = "关系图"


class NetworkXKGRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    title: str = "Knowledge Graph"


class WordCloudRequest(BaseModel):
    text: Optional[str] = None
    word_freq: Optional[Dict[str, float]] = None
    width: int = 800
    height: int = 600
    background_color: str = "white"
    colormap: str = "viridis"
    font_path: Optional[str] = None


class DocumentStatsRequest(BaseModel):
    word_freq: Optional[Dict[str, float]] = None
    entities: Optional[List[Dict[str, Any]]] = None


class KnowledgeGraphRequest(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


@router.get("/health")
async def health_check():
    """
    健康检查
    """
    try:
        viz_service = get_visualization_service()
        health = viz_service.health_check()

        return success_response(
            data={
                "status": "healthy" if health['available'] else "unavailable",
                "tools": health
            }
        )
    except Exception as e:
        logger.error(f"❌ 可视化服务健康检查失败: {e}")
        return error_response(
            code="HEALTH_CHECK_FAILED",
            message=str(e)
        )


@router.post("/plotly/bar")
async def create_plotly_bar(request: PlotlyBarRequest):
    """
    创建Plotly柱状图

    Request Body:
    {
        "data": {"categories": ["A", "B", "C"], "values": [10, 20, 15]},
        "x_key": "categories",
        "y_key": "values",
        "title": "My Bar Chart"
    }
    """
    try:
        viz_service = get_visualization_service()
        html = viz_service.plotly_bar_chart(
            data=request.data,
            x_key=request.x_key,
            y_key=request.y_key,
            title=request.title
        )

        if html:
            return success_response(data={"html": html})
        else:
            return error_response(
                code="CHART_GENERATION_FAILED",
                message="图表生成失败"
            )
    except Exception as e:
        logger.error(f"❌ 柱状图生成失败: {e}")
        return error_response(
            code="BAR_CHART_FAILED",
            message=str(e)
        )


@router.post("/plotly/line")
async def create_plotly_line(request: PlotlyLineRequest):
    """
    创建Plotly折线图

    Request Body:
    {
        "data": {"time": [1, 2, 3], "series1": [10, 20, 15], "series2": [5, 15, 25]},
        "x_key": "time",
        "y_keys": ["series1", "series2"],
        "title": "Multi-line Chart"
    }
    """
    try:
        viz_service = get_visualization_service()
        html = viz_service.plotly_line_chart(
            data=request.data,
            x_key=request.x_key,
            y_keys=request.y_keys,
            title=request.title
        )

        if html:
            return success_response(data={"html": html})
        else:
            return error_response(
                code="CHART_GENERATION_FAILED",
                message="图表生成失败"
            )
    except Exception as e:
        logger.error(f"❌ 折线图生成失败: {e}")
        return error_response(
            code="LINE_CHART_FAILED",
            message=str(e)
        )


@router.post("/plotly/scatter3d")
async def create_plotly_scatter3d(request: PlotlyScatter3DRequest):
    """
    创建Plotly 3D散点图

    Request Body:
    {
        "data": {"x": [1,2,3], "y": [4,5,6], "z": [7,8,9], "color": [1,2,3]},
        "x_key": "x",
        "y_key": "y",
        "z_key": "z",
        "color_key": "color",
        "title": "3D Visualization"
    }
    """
    try:
        viz_service = get_visualization_service()
        html = viz_service.plotly_scatter_3d(
            data=request.data,
            x_key=request.x_key,
            y_key=request.y_key,
            z_key=request.z_key,
            color_key=request.color_key,
            title=request.title
        )

        if html:
            return success_response(data={"html": html})
        else:
            return error_response(
                code="CHART_GENERATION_FAILED",
                message="图表生成失败"
            )
    except Exception as e:
        logger.error(f"❌ 3D散点图生成失败: {e}")
        return error_response(
            code="SCATTER_3D_FAILED",
            message=str(e)
        )


@router.post("/pyecharts/pie")
async def create_pyecharts_pie(request: PyechartsPieRequest):
    """
    创建pyecharts饼图

    Request Body:
    {
        "data": [["类别A", 35], ["类别B", 25], ["类别C", 40]],
        "title": "分布饼图"
    }
    """
    try:
        viz_service = get_visualization_service()

        # 转换为tuple列表
        data_tuples = [tuple(item) for item in request.data]

        html = viz_service.pyecharts_pie_chart(
            data=data_tuples,
            title=request.title
        )

        if html:
            return success_response(data={"html": html})
        else:
            return error_response(
                code="CHART_GENERATION_FAILED",
                message="图表生成失败"
            )
    except Exception as e:
        logger.error(f"❌ 饼图生成失败: {e}")
        return error_response(
            code="PIE_CHART_FAILED",
            message=str(e)
        )


@router.post("/pyecharts/graph")
async def create_pyecharts_graph(request: PyechartsGraphRequest):
    """
    创建pyecharts关系图

    Request Body:
    {
        "nodes": [
            {"name": "节点1", "symbolSize": 20},
            {"name": "节点2", "symbolSize": 15}
        ],
        "links": [
            {"source": "节点1", "target": "节点2"}
        ],
        "title": "知识关系图"
    }
    """
    try:
        viz_service = get_visualization_service()
        html = viz_service.pyecharts_graph(
            nodes=request.nodes,
            links=request.links,
            title=request.title
        )

        if html:
            return success_response(data={"html": html})
        else:
            return error_response(
                code="CHART_GENERATION_FAILED",
                message="图表生成失败"
            )
    except Exception as e:
        logger.error(f"❌ 关系图生成失败: {e}")
        return error_response(
            code="GRAPH_CHART_FAILED",
            message=str(e)
        )


@router.post("/networkx/knowledge-graph")
async def create_networkx_kg(request: NetworkXKGRequest):
    """
    创建NetworkX知识图谱

    Request Body:
    {
        "nodes": [
            {"id": "A", "label": "Node A", "group": 1},
            {"id": "B", "label": "Node B", "group": 2}
        ],
        "edges": [
            {"source": "A", "target": "B", "label": "relates to"}
        ],
        "title": "Knowledge Graph"
    }
    """
    try:
        viz_service = get_visualization_service()
        html = viz_service.networkx_knowledge_graph(
            nodes=request.nodes,
            edges=request.edges,
            title=request.title
        )

        if html:
            return success_response(data={"html": html})
        else:
            return error_response(
                code="CHART_GENERATION_FAILED",
                message="图表生成失败"
            )
    except Exception as e:
        logger.error(f"❌ 知识图谱生成失败: {e}")
        return error_response(
            code="KNOWLEDGE_GRAPH_FAILED",
            message=str(e)
        )


@router.post("/wordcloud")
async def create_wordcloud(request: WordCloudRequest):
    """
    生成词云图

    Request Body:
    {
        "text": "可选：原始文本",
        "word_freq": {"词1": 10, "词2": 20},
        "width": 800,
        "height": 600,
        "background_color": "white",
        "colormap": "viridis",
        "font_path": "/path/to/chinese/font.ttf"
    }
    """
    try:
        if not request.text and not request.word_freq:
            return error_response(
                code="INVALID_REQUEST",
                message="必须提供text或word_freq"
            )

        viz_service = get_visualization_service()
        img_base64 = viz_service.generate_wordcloud(
            text=request.text,
            word_freq=request.word_freq,
            width=request.width,
            height=request.height,
            background_color=request.background_color,
            colormap=request.colormap,
            font_path=request.font_path
        )

        if img_base64:
            return success_response(data={"image": img_base64})
        else:
            return error_response(
                code="WORDCLOUD_GENERATION_FAILED",
                message="词云生成失败"
            )
    except Exception as e:
        logger.error(f"❌ 词云生成失败: {e}")
        return error_response(
            code="WORDCLOUD_FAILED",
            message=str(e)
        )


@router.post("/document-stats")
async def create_document_stats_viz(request: DocumentStatsRequest):
    """
    为文档统计创建综合可视化

    Request Body:
    {
        "word_freq": {"word1": 10, "word2": 20, ...},
        "entities": [{"text": "实体1", "type": "PER"}, ...]
    }

    Returns:
    {
        "success": true,
        "visualizations": {
            "word_freq_bar": "<html>...",
            "wordcloud": "data:image/png;base64,...",
            "entity_pie": "<html>..."
        }
    }
    """
    try:
        viz_service = get_visualization_service()
        doc_stats = {}
        if request.word_freq:
            doc_stats['word_freq'] = request.word_freq
        if request.entities:
            doc_stats['entities'] = request.entities

        result = viz_service.create_document_stats_viz(doc_stats)

        return success_response(
            data={"visualizations": result}
        )
    except Exception as e:
        logger.error(f"❌ 文档统计可视化失败: {e}")
        return error_response(
            code="DOCUMENT_STATS_VIZ_FAILED",
            message=str(e)
        )


@router.post("/knowledge-graph")
async def create_knowledge_graph_viz(request: KnowledgeGraphRequest):
    """
    为知识图谱数据创建可视化

    Request Body:
    {
        "nodes": [...],
        "edges": [...]
    }
    """
    try:
        viz_service = get_visualization_service()
        kg_data = {
            'nodes': request.nodes,
            'edges': request.edges
        }
        html = viz_service.create_knowledge_graph_viz(kg_data)

        if html:
            return success_response(data={"html": html})
        else:
            return error_response(
                code="KG_VIZ_FAILED",
                message="知识图谱可视化失败"
            )
    except Exception as e:
        logger.error(f"❌ 知识图谱可视化失败: {e}")
        return error_response(
            code="KNOWLEDGE_GRAPH_VIZ_FAILED",
            message=str(e)
        )
