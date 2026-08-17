"""
🔪 破茧三刀 - 动态发现API

专门从project_documents的动态发现字段读取数据：
- extracted_entities (第二刀：实体识别+消歧)
- auto_clusters (第一刀：BERTopic主题发现)
- data_profile (第三刀：数据画像)

特点：
1. 零硬编码 - 所有数据来自动态发现
2. 零预设 - 不使用固定分类、词表、模板
3. 文档隔离 - 每个文档的发现结果独立存储
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.models.project import ProjectDocument, Project
from app.core.exceptions import ResourceNotFoundException

router = APIRouter(tags=["dynamic-discovery"])
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class DynamicTopicResponse(BaseModel):
    """动态发现的主题"""
    cluster_id: int
    auto_name: str
    keywords: List[str]
    doc_count: int
    representativeness: float


class DynamicEntityResponse(BaseModel):
    """动态发现的实体"""
    canonical_name: str
    aliases: List[str]
    entity_type: str
    mention_count: int
    confidence: float
    contexts: List[str]


class DataDimensionResponse(BaseModel):
    """数据画像维度"""
    dimension_name: str
    keywords: List[str]
    coverage: float
    priority: Optional[float] = None


class DocumentDiscoveryResponse(BaseModel):
    """单个文档的动态发现结果"""
    document_id: int
    filename: str
    status: str

    # 第一刀：主题发现
    topics: List[DynamicTopicResponse]
    topic_count: int

    # 第二刀：实体识别
    entities: List[DynamicEntityResponse]
    entity_count: int

    # 第三刀：数据画像
    dimensions: List[DataDimensionResponse]
    dimension_count: int


class ProjectDiscoverySummaryResponse(BaseModel):
    """项目级别的动态发现汇总"""
    project_id: int
    project_name: str

    total_documents: int
    processed_documents: int

    # 汇总统计
    total_topics: int
    total_entities: int
    total_dimensions: int

    # 文档列表
    documents: List[DocumentDiscoveryResponse]


# ==================== API Endpoints ====================

@router.get("/documents/{document_id}", response_model=DocumentDiscoveryResponse)
async def get_document_discovery(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个文档的动态发现结果

    从project_documents表的三个JSON字段读取：
    - auto_clusters: BERTopic发现的主题
    - extracted_entities: 实体识别+消歧结果
    - data_profile: 数据画像

    示例：
    GET /dynamic-discovery/documents/1

    返回该文档自动发现的主题、实体、维度
    （内容完全取决于文档本身，无任何硬编码）
    """
    doc = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id
    ).first()

    if not doc:
        raise ResourceNotFoundException(resource_type="Document", resource_id=document_id)

    # 读取动态发现结果
    topics_data = doc.auto_clusters or []
    entities_data = doc.extracted_entities or []
    profile_data = doc.data_profile or {}

    # 转换为响应格式
    topics = [
        DynamicTopicResponse(**topic)
        for topic in topics_data
    ] if topics_data else []

    entities = [
        DynamicEntityResponse(**entity)
        for entity in entities_data
    ] if entities_data else []

    dimensions_data = profile_data.get('discovered_dimensions', [])
    dimensions = [
        DataDimensionResponse(**dim)
        for dim in dimensions_data
    ] if dimensions_data else []

    return DocumentDiscoveryResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
        topics=topics,
        topic_count=len(topics),
        entities=entities,
        entity_count=len(entities),
        dimensions=dimensions,
        dimension_count=len(dimensions)
    )


@router.get("/projects/{project_id}/summary", response_model=ProjectDiscoverySummaryResponse)
async def get_project_discovery_summary(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目级别的动态发现汇总

    遍历项目下所有文档的动态发现结果，汇总统计

    示例：
    GET /dynamic-discovery/projects/1/summary

    返回：
    - 项目下所有文档的发现结果
    - 汇总的主题数、实体数、维度数
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ResourceNotFoundException(resource_type="Project", resource_id=project_id)

    # 获取项目下所有文档
    docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).all()

    total_topics = 0
    total_entities = 0
    total_dimensions = 0
    processed_count = 0

    document_results = []

    for doc in docs:
        topics_data = doc.auto_clusters or []
        entities_data = doc.extracted_entities or []
        profile_data = doc.data_profile or {}
        dimensions_data = profile_data.get('discovered_dimensions', [])

        if doc.status == 'completed' and (topics_data or entities_data):
            processed_count += 1

        total_topics += len(topics_data)
        total_entities += len(entities_data)
        total_dimensions += len(dimensions_data)

        # 转换为响应格式
        topics = [DynamicTopicResponse(**t) for t in topics_data] if topics_data else []
        entities = [DynamicEntityResponse(**e) for e in entities_data] if entities_data else []
        dimensions = [DataDimensionResponse(**d) for d in dimensions_data] if dimensions_data else []

        document_results.append(DocumentDiscoveryResponse(
            document_id=doc.id,
            filename=doc.filename,
            status=doc.status,
            topics=topics,
            topic_count=len(topics),
            entities=entities,
            entity_count=len(entities),
            dimensions=dimensions,
            dimension_count=len(dimensions)
        ))

    return ProjectDiscoverySummaryResponse(
        project_id=project.id,
        project_name=project.name,
        total_documents=len(docs),
        processed_documents=processed_count,
        total_topics=total_topics,
        total_entities=total_entities,
        total_dimensions=total_dimensions,
        documents=document_results
    )


@router.get("/projects/{project_id}/topics")
async def get_all_discovered_topics(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目下所有动态发现的主题

    从所有文档的auto_clusters字段聚合

    返回：所有唯一的主题及其来源文档
    """
    docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.status == 'completed'
    ).all()

    all_topics = {}

    for doc in docs:
        topics = doc.auto_clusters or []
        for topic in topics:
            topic_name = topic.get('auto_name', '')
            if topic_name:
                if topic_name not in all_topics:
                    all_topics[topic_name] = {
                        'topic_name': topic_name,
                        'keywords': topic.get('keywords', []),
                        'source_documents': [],
                        'total_mentions': 0
                    }
                all_topics[topic_name]['source_documents'].append({
                    'document_id': doc.id,
                    'filename': doc.filename,
                    'doc_count': topic.get('doc_count', 0)
                })
                all_topics[topic_name]['total_mentions'] += topic.get('doc_count', 0)

    return {
        'project_id': project_id,
        'topic_count': len(all_topics),
        'topics': list(all_topics.values())
    }


@router.get("/projects/{project_id}/entities")
async def get_all_discovered_entities(
    project_id: int,
    entity_type: Optional[str] = Query(None, description="筛选实体类型：PERSON/LOCATION/ORGANIZATION"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="最小置信度"),
    db: Session = Depends(get_db)
):
    """
    获取项目下所有动态发现的实体

    从所有文档的extracted_entities字段聚合

    支持过滤：
    - entity_type: 实体类型
    - min_confidence: 最小置信度

    返回：所有实体及其来源文档
    """
    docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id,
        ProjectDocument.status == 'completed'
    ).all()

    all_entities = {}

    for doc in docs:
        entities = doc.extracted_entities or []
        for entity in entities:
            name = entity.get('canonical_name', '')
            ent_type = entity.get('entity_type', '')
            confidence = entity.get('confidence', 0.0)

            # 应用过滤条件
            if entity_type and ent_type != entity_type:
                continue
            if confidence < min_confidence:
                continue

            if name:
                if name not in all_entities:
                    all_entities[name] = {
                        'entity_name': name,
                        'entity_type': ent_type,
                        'aliases': entity.get('aliases', []),
                        'source_documents': [],
                        'total_mentions': 0,
                        'avg_confidence': 0.0
                    }

                all_entities[name]['source_documents'].append({
                    'document_id': doc.id,
                    'filename': doc.filename,
                    'mention_count': entity.get('mention_count', 0),
                    'confidence': confidence
                })
                all_entities[name]['total_mentions'] += entity.get('mention_count', 0)

    # 计算平均置信度
    for entity in all_entities.values():
        if entity['source_documents']:
            entity['avg_confidence'] = sum(
                doc['confidence'] for doc in entity['source_documents']
            ) / len(entity['source_documents'])

    return {
        'project_id': project_id,
        'entity_count': len(all_entities),
        'filters': {
            'entity_type': entity_type,
            'min_confidence': min_confidence
        },
        'entities': list(all_entities.values())
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "service": "dynamic-discovery-api",
        "status": "healthy",
        "description": "🔪 破茧三刀 - 零硬编码动态发现系统"
    }
