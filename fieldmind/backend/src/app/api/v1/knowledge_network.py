"""
知识脉络API端点
提供知识网络可视化、脉络聚合和关联分析接口
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, distinct

from app.core.database import get_db
from app.models.document_chunk import DocumentChunk
from app.models.entity import Entity, EntityRelation
from app.models.project import Project, ProjectDocument
from app.schemas.response import success_response
from collections import defaultdict
import json

router = APIRouter()


# ==================== 辅助函数 ====================

from app.services.knowledge_enhancement_service import KnowledgeEnhancementService


# ==================== 辅助函数 ====================

def extract_keywords_from_chunks(chunks: List[DocumentChunk], top_n: int = 10) -> List[Dict[str, Any]]:
    """从chunks中提取关键词频次"""
    keyword_freq = defaultdict(int)

    for chunk in chunks:
        # 从 domain_tags 提取关键词
        if chunk.domain_tags:
            tags = chunk.domain_tags if isinstance(chunk.domain_tags, list) else []
            for tag in tags:
                if isinstance(tag, str):
                    keyword_freq[tag] += 1
                elif isinstance(tag, dict) and 'keywords' in tag:
                    for kw in tag.get('keywords', []):
                        keyword_freq[kw] += 1

        # 从 key_entities 提取
        if chunk.key_entities:
            entities = chunk.key_entities if isinstance(chunk.key_entities, list) else []
            for entity in entities:
                if isinstance(entity, dict):
                    name = entity.get('name') or entity.get('text', '')
                    if name:
                        keyword_freq[name] += 1

    # 按频次排序
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    return [{"keyword": kw, "frequency": freq} for kw, freq in sorted_keywords[:top_n]]


def calculate_dimension_category(chunk: DocumentChunk, enhancement_service: KnowledgeEnhancementService = None) -> str:
    """计算大脉络类型（使用增强服务）"""
    # 如果已有标签，直接使用
    if chunk.domain_tags and isinstance(chunk.domain_tags, list) and len(chunk.domain_tags) > 0:
        first_tag = chunk.domain_tags[0]
        if isinstance(first_tag, dict) and 'category' in first_tag:
            return first_tag['category']

    # 如果有 primary_domain，使用它
    if chunk.primary_domain:
        return chunk.primary_domain

    # 否则使用增强服务进行分类
    if enhancement_service and chunk.text:
        dimension, _, _ = enhancement_service.classify_dimension(chunk.text)
        return dimension

    return "其他"


def calculate_dimension_sub_category(chunk: DocumentChunk, enhancement_service: KnowledgeEnhancementService = None) -> str:
    """计算子脉络（使用增强服务）"""
    # 如果已有标签，直接使用
    if chunk.domain_tags and isinstance(chunk.domain_tags, list) and len(chunk.domain_tags) > 0:
        first_tag = chunk.domain_tags[0]
        if isinstance(first_tag, dict):
            subcategory = first_tag.get('subcategory') or first_tag.get('sub_subcategory', '')
            if subcategory:
                return subcategory

    # 从 spatial_context 或 temporal_context 提取
    if chunk.spatial_context:
        return chunk.spatial_context

    # 使用增强服务进行分类
    if enhancement_service and chunk.text:
        _, subcategory, _ = enhancement_service.classify_dimension(chunk.text)
        return subcategory

    return "未分类"


# ==================== API端点 ====================

@router.get("/projects/{project_id}/knowledge-network")
async def get_knowledge_network(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db)
):
    """
    获取知识脉络网络全景

    返回：
    - 统计数据：大脉络数、子脉络数、支撑材料数、关键词数
    - 节点列表：每个脉络的详细信息
    - 边列表：脉络间的关联关系
    """
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 初始化增强服务
    enhancement_service = KnowledgeEnhancementService(db)

    # 获取所有chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.project_id == project_id
    ).all()

    # 如果没有chunks，创建示例数据
    if not chunks:
        created_count = enhancement_service.create_sample_chunks_if_empty(project_id)
        if created_count > 0:
            # 重新查询
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.project_id == project_id
            ).all()

    if not chunks:
        return success_response(data={
            "statistics": {
                "dimension_count": 0,
                "sub_dimension_count": 0,
                "material_count": 0,
                "keyword_count": 0
            },
            "nodes": [],
            "edges": []
        })

    # 构建脉络聚合
    dimension_data = defaultdict(lambda: {
        "name": "",
        "category": "",
        "material_count": 0,
        "chunk_count": 0,
        "keywords": defaultdict(int),
        "sub_dimensions": defaultdict(lambda: {
            "name": "",
            "chunk_count": 0,
            "document_ids": set()
        }),
        "document_ids": set(),
        "time_range": {"earliest": None, "latest": None}
    })

    # 遍历chunks，聚合数据
    for chunk in chunks:
        dim_category = calculate_dimension_category(chunk, enhancement_service)
        sub_category = calculate_dimension_sub_category(chunk, enhancement_service)

        dim_data = dimension_data[dim_category]
        dim_data["name"] = dim_category
        dim_data["category"] = dim_category
        dim_data["chunk_count"] += 1
        dim_data["document_ids"].add(chunk.document_id)

        # 子脉络
        sub_data = dim_data["sub_dimensions"][sub_category]
        sub_data["name"] = sub_category
        sub_data["chunk_count"] += 1
        sub_data["document_ids"].add(chunk.document_id)

        # 时间范围
        if chunk.created_at:
            if not dim_data["time_range"]["earliest"] or chunk.created_at < dim_data["time_range"]["earliest"]:
                dim_data["time_range"]["earliest"] = chunk.created_at
            if not dim_data["time_range"]["latest"] or chunk.created_at > dim_data["time_range"]["latest"]:
                dim_data["time_range"]["latest"] = chunk.created_at

        # 提取关键词
        if chunk.key_entities:
            entities = chunk.key_entities if isinstance(chunk.key_entities, list) else []
            for entity in entities:
                if isinstance(entity, dict):
                    name = entity.get('name') or entity.get('text', '')
                    if name:
                        dim_data["keywords"][name] += 1

    # 更新 material_count
    for dim_name, dim_data in dimension_data.items():
        dim_data["material_count"] = len(dim_data["document_ids"])

    # 构建节点列表
    nodes = []
    node_id = 0
    dimension_to_id = {}

    for dim_name, dim_data in dimension_data.items():
        node_id += 1
        dimension_to_id[dim_name] = node_id

        # 颜色映射
        color_map = {
            "文化传承": "#FF6B6B",
            "经济结构": "#4ECDC4",
            "社会组织": "#45B7D1",
            "政策支持": "#FFA07A",
            "在地业态": "#98D8C8",
            "历史脉络": "#C7CEEA",
            "其他": "#CCCCCC"
        }

        nodes.append({
            "id": node_id,
            "name": dim_name,
            "type": "dimension",
            "category": dim_data["category"],
            "material_count": dim_data["material_count"],
            "chunk_count": dim_data["chunk_count"],
            "keyword_count": len(dim_data["keywords"]),
            "sub_dimension_count": len(dim_data["sub_dimensions"]),
            "color": color_map.get(dim_name, "#CCCCCC"),
            "size": min(100 + dim_data["material_count"] * 10, 300)
        })

    # 构建边列表（基于文档交叉）
    edges = []
    dimensions = list(dimension_data.keys())

    for i, dim1 in enumerate(dimensions):
        for dim2 in dimensions[i+1:]:
            # 计算交叉文档数
            docs1 = dimension_data[dim1]["document_ids"]
            docs2 = dimension_data[dim2]["document_ids"]
            cross_docs = docs1 & docs2

            # 至少3个交叉文档才建立边
            if len(cross_docs) >= 3:
                edges.append({
                    "source": dimension_to_id[dim1],
                    "target": dimension_to_id[dim2],
                    "weight": len(cross_docs),
                    "label": f"{len(cross_docs)}份材料"
                })

    # 统计数据
    total_keywords = sum(len(d["keywords"]) for d in dimension_data.values())
    total_sub_dimensions = sum(len(d["sub_dimensions"]) for d in dimension_data.values())
    total_documents = len(set(chunk.document_id for chunk in chunks))

    return success_response(data={
        "statistics": {
            "dimension_count": len(dimension_data),
            "sub_dimension_count": total_sub_dimensions,
            "material_count": total_documents,
            "keyword_count": total_keywords
        },
        "nodes": nodes,
        "edges": edges
    })


@router.get("/projects/{project_id}/knowledge-network/nodes/{node_id}")
async def get_node_detail(
    project_id: int = Path(..., description="项目ID"),
    node_id: int = Path(..., description="节点ID"),
    db: Session = Depends(get_db)
):
    """
    获取脉络节点详情

    返回：
    - 脉络基本信息
    - 关键词列表（按频次排序）
    - 子脉络列表
    - 关联脉络
    - 支撑材料列表
    - 核心议题
    """
    # 先获取网络数据，找到对应节点
    network_response = await get_knowledge_network(project_id, db)
    network_data = network_response["data"]

    # 找到目标节点
    target_node = None
    for node in network_data["nodes"]:
        if node["id"] == node_id:
            target_node = node
            break

    if not target_node:
        raise HTTPException(status_code=404, detail="节点不存在")

    # 获取该脉络的所有chunks
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.project_id == project_id
    ).all()

    # 筛选出属于该脉络的chunks
    dimension_chunks = [
        chunk for chunk in chunks
        if calculate_dimension_category(chunk) == target_node["name"]
    ]

    # 提取关键词（Top 10）
    keywords = extract_keywords_from_chunks(dimension_chunks, top_n=10)

    # 提取子脉络
    sub_dimensions = defaultdict(lambda: {"name": "", "material_count": 0, "keyword_count": 0, "chunk_ids": []})
    for chunk in dimension_chunks:
        sub_cat = calculate_dimension_sub_category(chunk)
        sub_data = sub_dimensions[sub_cat]
        sub_data["name"] = sub_cat
        sub_data["chunk_ids"].append(chunk.id)

    # 统计每个子脉络的材料数
    for sub_name, sub_data in sub_dimensions.items():
        chunk_ids = sub_data["chunk_ids"]
        doc_ids = set(
            db.query(DocumentChunk.document_id)
            .filter(DocumentChunk.id.in_(chunk_ids))
            .distinct()
            .all()
        )
        sub_data["material_count"] = len(doc_ids)
        # 关键词数量（从这些chunks中提取）
        sub_chunks = [c for c in dimension_chunks if c.id in chunk_ids]
        sub_keywords = extract_keywords_from_chunks(sub_chunks, top_n=100)
        sub_data["keyword_count"] = len(sub_keywords)

    sub_dimension_list = [
        {
            "name": name,
            "material_count": data["material_count"],
            "keyword_count": data["keyword_count"]
        }
        for name, data in sub_dimensions.items()
    ]

    # 关联脉络（从edges中找）
    related_dimensions = []
    for edge in network_data["edges"]:
        if edge["source"] == node_id:
            related_node = next((n for n in network_data["nodes"] if n["id"] == edge["target"]), None)
            if related_node:
                related_dimensions.append({
                    "name": related_node["name"],
                    "cross_material_count": edge["weight"]
                })
        elif edge["target"] == node_id:
            related_node = next((n for n in network_data["nodes"] if n["id"] == edge["source"]), None)
            if related_node:
                related_dimensions.append({
                    "name": related_node["name"],
                    "cross_material_count": edge["weight"]
                })

    # 支撑材料列表
    doc_ids = list(set(chunk.document_id for chunk in dimension_chunks))
    materials = db.query(ProjectDocument).filter(
        ProjectDocument.id.in_(doc_ids)
    ).limit(10).all()

    material_list = [
        {
            "id": doc.id,
            "title": doc.title or doc.filename,
            "filename": doc.filename,
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        }
        for doc in materials
    ]

    # 核心议题（从chunks的summary或key_entities中提取）
    core_issues = []
    issue_freq = defaultdict(int)
    for chunk in dimension_chunks[:20]:  # 只看前20个chunk
        if chunk.chunk_summary:
            issue_freq[chunk.chunk_summary] += 1

    sorted_issues = sorted(issue_freq.items(), key=lambda x: x[1], reverse=True)
    core_issues = [issue for issue, freq in sorted_issues[:3]]

    return success_response(data={
        "dimension_name": target_node["name"],
        "category": target_node["category"],
        "material_count": target_node["material_count"],
        "chunk_count": target_node["chunk_count"],
        "keyword_count": target_node["keyword_count"],
        "keywords": keywords,
        "sub_dimensions": sub_dimension_list,
        "related_dimensions": related_dimensions,
        "materials": material_list,
        "core_issues": core_issues
    })
