"""
知识图谱增强API端点
提供新版服务的完整接口：构建、推理、Skills集成、时间线、导出
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import logging
from app.core.logging import logger
from app.schemas.response import success_response, error_response

router = APIRouter(prefix="/knowledge-graph", tags=["知识图谱增强"])


# ========== 请求/响应模型 ==========

class GraphConstructionRequest(BaseModel):
    """图谱构建请求"""
    project_name: str = Field(..., description="项目名称")
    document_ids: Optional[List[int]] = Field(None, description="文档ID列表（为空则处理项目所有文档）")
    mode: str = Field("auto", description="构建模式：strict/auto/loose")


class GraphConstructionResponse(BaseModel):
    """图谱构建响应"""
    success: bool
    nodes_created: int
    edges_created: int
    nodes_merged: int
    quality_distribution: Dict[str, int]
    core_keywords: List[str]
    message: str


class NodeQueryRequest(BaseModel):
    """节点查询请求"""
    node_id: Optional[str] = Field(None, description="节点ID")
    node_name: Optional[str] = Field(None, description="节点名称")
    include_neighborhood: bool = Field(True, description="是否包含邻居节点")
    max_depth: int = Field(2, description="最大深度")


class NodeNeighborhoodResponse(BaseModel):
    """节点邻居响应"""
    center_node: Dict[str, Any]
    neighbors: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    depth: int


class ReasoningRequest(BaseModel):
    """推理请求"""
    reasoning_type: str = Field(..., description="推理类型：transitive/community/centrality")
    params: Dict[str, Any] = Field(default_factory=dict, description="推理参数")


class ReasoningResponse(BaseModel):
    """推理响应"""
    reasoning_type: str
    results: List[Dict[str, Any]]
    count: int
    message: str


class SkillLinkRequest(BaseModel):
    """技能关联请求"""
    skill_id: str
    skill_name: str
    skill_type: str = Field(..., description="思路/书籍/方法/工具/其他")
    target_type: str = Field(..., description="node/document")
    target_ids: List[str]
    reasoning: str = Field("手动关联", description="关联原因")


class SkillQueryRequest(BaseModel):
    """技能查询请求"""
    query_from: str = Field(..., description="skill/node/document")
    id: str
    name: Optional[str] = None


class TripleInteractionResponse(BaseModel):
    """三者互动查询响应"""
    query_from: str
    id: str
    name: str
    related_skills: List[Dict[str, Any]]
    related_nodes: List[Dict[str, Any]]
    related_documents: List[Dict[str, Any]]


class TimelineRequest(BaseModel):
    """时间线请求"""
    project_name: str
    entity_filter: Optional[List[str]] = Field(None, description="实体名称过滤")


class TimelineResponse(BaseModel):
    """时间线响应"""
    events: List[Dict[str, Any]]
    succession_chains: List[Dict[str, Any]]
    timeline_summary: Dict[str, Any]


class ExportRequest(BaseModel):
    """导出请求"""
    project_name: Optional[str] = Field(None, description="项目名称（为空则导出全部）")
    format: str = Field("json", description="导出格式：json/html/cypher")
    include_metrics: bool = Field(True, description="是否包含NetworkX计算的指标")


class CypherQueryRequest(BaseModel):
    """Cypher查询请求（驾驭工程接口）"""
    cypher: str = Field(..., description="Cypher查询语句")
    params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    enhance_with_networkx: bool = Field(True, description="是否用NetworkX增强结果")


# ========== API端点 ==========

@router.post("/construct", response_model=GraphConstructionResponse)
async def construct_graph(request: GraphConstructionRequest):
    """
    构建知识图谱

    流程：
    1. 从数据库获取enriched_chunks
    2. 调用GraphConstructionService.build_graph_from_chunks()
    3. 返回构建统计
    """
    try:
        from app.services.graph_construction_service import get_graph_construction_service
        from app.core.database import SessionLocal
        from sqlalchemy import text

        service = get_graph_construction_service()
        db = SessionLocal()

        # 获取enriched_chunks
        if request.document_ids:
            # 指定文档
            query = text("""
                SELECT ec.* FROM enriched_chunks ec
                WHERE ec.document_id IN :doc_ids
                ORDER BY ec.chunk_index
            """)
            results = db.execute(query, {"doc_ids": tuple(request.document_ids)}).fetchall()
        else:
            # 项目所有文档
            query = text("""
                SELECT ec.* FROM enriched_chunks ec
                JOIN documents d ON ec.document_id = d.id
                WHERE d.project_name = :project_name
                ORDER BY ec.chunk_index
            """)
            results = db.execute(query, {"project_name": request.project_name}).fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="未找到enriched_chunks")

        # 转换为EnrichedChunk对象
        from app.models.chunk import EnrichedChunk
        chunks = []
        for row in results:
            chunk = EnrichedChunk(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                chunk_index=row.chunk_index,
                text=row.text,
                entities=row.entities or [],
                relations=row.relations or [],
                keywords=row.keywords or [],
                summary=row.summary,
                semantic_tags=row.semantic_tags or []
            )
            chunks.append(chunk)

        # 构建图谱
        result = service.build_graph_from_chunks(
            enriched_chunks=chunks,
            project_name=request.project_name,
            mode=request.mode
        )

        db.close()

        return GraphConstructionResponse(
            success=True,
            nodes_created=result.nodes_created,
            edges_created=result.edges_created,
            nodes_merged=result.nodes_merged,
            quality_distribution=result.quality_distribution,
            core_keywords=result.core_keywords,
            message=f"图谱构建成功：{result.nodes_created}节点，{result.edges_created}边"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"构建图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/node", response_model=NodeNeighborhoodResponse)
async def query_node_neighborhood(request: NodeQueryRequest):
    """
    查询节点及其邻居

    用于前端点击节点时展开关系
    """
    try:
        from app.services.graph_reasoning_service import get_graph_reasoning_service

        service = get_graph_reasoning_service()

        # 获取节点邻居
        result = service.get_node_neighborhood(
            node_id=request.node_id,
            node_name=request.node_name,
            max_depth=request.max_depth
        )

        return NodeNeighborhoodResponse(
            center_node=result["center_node"],
            neighbors=result["neighbors"],
            edges=result["edges"],
            depth=result["depth"]
        )

    except Exception as e:
        logger.error(f"查询节点邻居失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reasoning", response_model=ReasoningResponse)
async def perform_reasoning(request: ReasoningRequest):
    """
    图谱推理

    支持的推理类型：
    1. transitive - 传递推理（A→B→C推导A→C）
    2. community - 社区发现（识别家族圈、组织圈）
    3. centrality - 中心性分析（识别核心人物）
    """
    try:
        from app.services.graph_reasoning_service import get_graph_reasoning_service

        service = get_graph_reasoning_service()

        if request.reasoning_type == "transitive":
            # 传递推理
            relation_types = request.params.get("relation_types", ["认识", "合作", "师生"])
            results = service.transitive_reasoning(relation_types=relation_types)

        elif request.reasoning_type == "community":
            # 社区发现
            algorithm = request.params.get("algorithm", "louvain")
            results = service.community_detection(algorithm=algorithm)

        elif request.reasoning_type == "centrality":
            # 中心性分析
            centrality_type = request.params.get("centrality_type", "pagerank")
            top_k = request.params.get("top_k", 10)
            results = service.centrality_analysis(
                centrality_type=centrality_type,
                top_k=top_k
            )

        else:
            raise HTTPException(status_code=400, detail=f"不支持的推理类型: {request.reasoning_type}")

        return ReasoningResponse(
            reasoning_type=request.reasoning_type,
            results=results,
            count=len(results),
            message=f"{request.reasoning_type}推理完成"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图谱推理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/link")
async def link_skill(request: SkillLinkRequest):
    """
    关联技能到节点或文档

    使用场景：
    1. 技能 → 图谱节点：技能"民俗调查方法" → 节点["春节习俗", "婚丧嫁娶"]
    2. 技能 → 文档：技能"口述史理论" → 文档["XX村调研报告.pdf"]
    """
    try:
        from app.services.skills_integration_service import get_skills_integration_service
        from app.services.graph_database_integration_v2 import get_graph_database_integration_v2

        skill_service = get_skills_integration_service()
        graph_service = get_graph_database_integration_v2()

        # 解析技能类型
        from app.services.skills_integration_service import SkillType
        skill_type_map = {
            "思路": SkillType.THOUGHT,
            "书籍": SkillType.BOOK,
            "方法": SkillType.METHOD,
            "工具": SkillType.TOOL,
            "其他": SkillType.OTHER
        }
        skill_type = skill_type_map.get(request.skill_type, SkillType.OTHER)

        if request.target_type == "node":
            # 获取节点对象
            nodes = []
            for node_id in request.target_ids:
                node_data = graph_service.get_node(node_id)
                if node_data:
                    from app.models.graph import GraphNode
                    node = GraphNode(
                        id=node_data["id"],
                        name=node_data["name"],
                        type=node_data["type"],
                        properties=node_data.get("properties", {})
                    )
                    nodes.append(node)

            # 关联技能到节点
            associations = skill_service.link_skill_to_nodes(
                skill_id=request.skill_id,
                skill_name=request.skill_name,
                skill_type=skill_type,
                nodes=nodes,
                reasoning=request.reasoning
            )

        elif request.target_type == "document":
            # 关联技能到文档
            associations = skill_service.link_skill_to_documents(
                skill_id=request.skill_id,
                skill_name=request.skill_name,
                document_ids=request.target_ids,
                reasoning=request.reasoning
            )

        else:
            raise HTTPException(status_code=400, detail=f"不支持的目标类型: {request.target_type}")

        return success_response(
            data={
                "associations_created": len(associations)
            },
            message=f"成功关联技能到{len(associations)}个{request.target_type}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"关联技能失败: {e}")
        return error_response(
            code="LINK_SKILL_FAILED",
            message=str(e)
        )


@router.post("/skills/query", response_model=TripleInteractionResponse)
async def query_triple_interaction(request: SkillQueryRequest):
    """
    三者互动查询：Skills ↔ 图谱 ↔ 文档

    查询方向：
    1. 从技能出发 → 查询关联的节点和文档
    2. 从节点出发 → 查询关联的技能和文档
    3. 从文档出发 → 查询提取的节点和应用的技能
    """
    try:
        from app.services.skills_integration_service import get_skills_integration_service

        service = get_skills_integration_service()

        if request.query_from == "skill":
            result = service.query_from_skill(
                skill_id=request.id,
                skill_name=request.name or ""
            )
        elif request.query_from == "node":
            result = service.query_from_node(
                node_id=request.id,
                node_name=request.name or ""
            )
        elif request.query_from == "document":
            result = service.query_from_document(
                document_id=request.id,
                document_name=request.name or ""
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的查询来源: {request.query_from}")

        return TripleInteractionResponse(
            query_from=result.query_from,
            id=result.id,
            name=result.name,
            related_skills=result.related_skills,
            related_nodes=result.related_nodes,
            related_documents=result.related_documents
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"三者互动查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeline", response_model=TimelineResponse)
async def get_timeline(request: TimelineRequest):
    """
    获取项目时间线

    返回：
    1. 时间事件列表（按时间排序）
    2. 历任继任链（如：历任村支书）
    3. 时间线摘要
    """
    try:
        from app.services.timeline_integration_service import get_timeline_integration_service

        service = get_timeline_integration_service()

        # 获取时间事件
        events = service.get_timeline_events(
            project_name=request.project_name,
            entity_filter=request.entity_filter
        )

        # 获取继任链
        succession_chains = service.get_succession_chains(
            project_name=request.project_name
        )

        # 生成摘要
        timeline_summary = {
            "total_events": len(events),
            "time_range": {
                "start": events[0]["time"] if events else None,
                "end": events[-1]["time"] if events else None
            },
            "succession_chains_count": len(succession_chains)
        }

        return TimelineResponse(
            events=events,
            succession_chains=succession_chains,
            timeline_summary=timeline_summary
        )

    except Exception as e:
        logger.error(f"获取时间线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_graph(request: ExportRequest):
    """
    导出知识图谱

    支持格式：
    1. json - 完整图谱数据（节点+边+元数据）
    2. html - 可视化HTML文件（用于预览）
    3. cypher - Neo4j Cypher导入语句
    """
    try:
        from app.services.graph_construction_service import get_graph_construction_service
        import os
        import json
        from datetime import datetime

        service = get_graph_construction_service()

        # 导出目录
        output_dir = "/Users/alwan/FieldMind/backend/src/static/exports"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_prefix = request.project_name or "all"

        if request.format == "json":
            # 导出JSON
            filename = f"graph_{project_prefix}_{timestamp}.json"
            output_path = os.path.join(output_dir, filename)

            graph_data = service.export_graph_data(
                project_name=request.project_name,
                include_metrics=request.include_metrics
            )

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)

        elif request.format == "html":
            # 导出HTML可视化
            filename = f"graph_{project_prefix}_{timestamp}.html"
            output_path = os.path.join(output_dir, filename)

            service.export_html_visualization(
                output_path=output_path,
                project_name=request.project_name
            )

        elif request.format == "cypher":
            # 导出Cypher语句
            filename = f"graph_{project_prefix}_{timestamp}.cypher"
            output_path = os.path.join(output_dir, filename)

            cypher_statements = service.export_cypher_statements(
                project_name=request.project_name
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(cypher_statements))

        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {request.format}")

        return success_response(
            data={
                "format": request.format,
                "file_path": output_path,
                "file_name": filename,
                "url": f"/static/exports/{filename}"
            },
            message=f"导出成功：{request.format.upper()}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出图谱失败: {e}")
        return error_response(
            code="EXPORT_FAILED",
            message=str(e)
        )


@router.post("/cypher/query")
async def cypher_query(request: CypherQueryRequest):
    """
    执行Cypher查询（驾驭工程接口）

    增强功能：
    1. 执行Neo4j原生Cypher查询
    2. 自动补充NetworkX计算的指标（PageRank等）
    3. 返回增强后的结果

    示例Cypher：
    MATCH (n:Entity)-[r]->(m) WHERE n.is_core_keyword = true RETURN n, r, m
    """
    try:
        from app.services.graph_database_integration_v2 import get_graph_database_integration_v2

        service = get_graph_database_integration_v2()

        results = service.cypher_query_enhanced(
            cypher=request.cypher,
            params=request.params,
            enhance_with_networkx=request.enhance_with_networkx
        )

        return success_response(
            data={
                "cypher": request.cypher,
                "results": results,
                "count": len(results),
                "enhanced": request.enhance_with_networkx
            }
        )

    except Exception as e:
        logger.error(f"Cypher查询失败: {e}")
        return error_response(
            code="CYPHER_QUERY_FAILED",
            message=str(e)
        )


@router.get("/stats")
async def get_graph_statistics():
    """
    获取图谱统计信息

    返回：
    1. 节点/边数量
    2. 质量分布（HIGH/MEDIUM/LOW）
    3. 数据库同步状态
    4. 核心关键词
    """
    try:
        from app.services.graph_construction_service import get_graph_construction_service
        from app.services.graph_database_integration_v2 import get_graph_database_integration_v2

        construction_service = get_graph_construction_service()
        integration_service = get_graph_database_integration_v2()

        # 构建统计
        construction_stats = construction_service.get_statistics()

        # 数据库统计
        integration_stats = integration_service.get_statistics()

        return success_response(
            data={
                "construction": construction_stats,
                "integration": integration_stats
            },
            message="统计信息获取成功"
        )

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return error_response(
            code="GET_STATS_FAILED",
            message=str(e)
        )
