"""
🧠 数据联邦API - 全局对象和关联查询接口

提供：
1. 对象血缘查询
2. 关系发现和查询
3. 多模态时间戳对齐
4. 智能推荐
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.data_federation_service import DataFederationService
from app.services.relation_discovery import RelationDiscoveryEngine
from app.services.multimodal_alignment import MultimodalAlignmentService
from app.services.correlation_recommender import CorrelationRecommender


router = APIRouter()


# ==================== Pydantic模型 ====================

class ObjectLineageResponse(BaseModel):
    """对象血缘响应"""
    current: Dict[str, Any]
    ancestors: List[Dict[str, Any]]
    descendants: List[Dict[str, Any]]


class ObjectFullDataResponse(BaseModel):
    """对象完整数据响应"""
    fid: str
    type: str
    metadata: Dict[str, Any]
    storage: Dict[str, Any]
    full_data: Optional[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    lineage: Dict[str, Any]


class RelationDiscoveryRequest(BaseModel):
    """关系发现请求"""
    object_fid: str
    project_id: int


class TimelineContentResponse(BaseModel):
    """时间轴内容响应"""
    current_time: float
    facts: List[Dict[str, Any]]
    entities: List[str]
    entity_fids: List[str]
    events: List[str]
    keywords: List[str]


class RecommendationResponse(BaseModel):
    """推荐响应"""
    fid: str
    type: str
    title: str
    reason: str
    confidence: float
    path: List[str]
    depth: int


# ==================== 对象查询 ====================

@router.get("/objects/{fid}/lineage", response_model=ObjectLineageResponse)
async def get_object_lineage(
    fid: str,
    db: Session = Depends(get_db)
):
    """获取对象的完整血缘链"""
    service = DataFederationService(db)
    lineage = service.get_lineage(fid)

    if "error" in lineage:
        raise HTTPException(status_code=404, detail=lineage["error"])

    return lineage


@router.get("/objects/{fid}", response_model=ObjectFullDataResponse)
async def get_object_full_data(
    fid: str,
    db: Session = Depends(get_db)
):
    """获取对象的完整数据（跨库查询）"""
    service = DataFederationService(db)
    data = service.get_object_full_data(fid)

    if not data:
        raise HTTPException(status_code=404, detail="对象不存在")

    return data


@router.get("/projects/{project_id}/objects")
async def list_project_objects(
    project_id: int,
    object_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db)
):
    """列出项目中的所有对象"""
    service = DataFederationService(db)

    if object_type:
        objects = service.find_objects_by_type(project_id, object_type, limit)
    else:
        from app.models.federation import FieldMindObject
        objects = db.query(FieldMindObject).filter(
            FieldMindObject.project_id == project_id
        ).limit(limit).all()

    return {
        "total": len(objects),
        "objects": [
            {
                "fid": obj.fid,
                "type": obj.object_type,
                "metadata": obj.object_metadata,
                "created_at": obj.created_at.isoformat()
            }
            for obj in objects
        ]
    }


# ==================== 关系发现 ====================

@router.post("/relations/discover")
async def discover_relations(
    request: RelationDiscoveryRequest,
    db: Session = Depends(get_db)
):
    """为对象发现所有潜在关联"""
    engine = RelationDiscoveryEngine(db)
    relations = engine.discover_all_relations(request.object_fid)

    return {
        "object_fid": request.object_fid,
        "discovered_relations": len(relations),
        "relations": relations
    }


@router.post("/projects/{project_id}/relations/discover-all")
async def discover_project_relations(
    project_id: int,
    batch_size: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """为项目中的所有实体和事件发现关系"""
    engine = RelationDiscoveryEngine(db)
    new_relations = engine.discover_project_relations(project_id, batch_size)

    return {
        "project_id": project_id,
        "new_relations_created": new_relations,
        "message": f"成功为项目发现并创建了 {new_relations} 条新关系"
    }


@router.get("/objects/{fid}/relations")
async def get_object_relations(
    fid: str,
    relation_type: Optional[str] = Query(None),
    direction: str = Query("both", regex="^(from|to|both)$"),
    db: Session = Depends(get_db)
):
    """获取对象的所有关系"""
    service = DataFederationService(db)
    relations = service.get_relations(fid, relation_type, direction)

    return {
        "fid": fid,
        "total_relations": len(relations),
        "relations": [
            {
                "id": r.id,
                "from_fid": r.from_fid,
                "to_fid": r.to_fid,
                "relation_type": r.relation_type,
                "confidence": r.confidence,
                "evidence_fids": r.evidence_fids,
                "relation_data": r.relation_data
            }
            for r in relations
        ]
    }


# ==================== 多模态对齐 ====================

@router.post("/documents/{document_id}/align-timestamps")
async def align_timestamps(
    document_id: int,
    project_id: int,
    db: Session = Depends(get_db)
):
    """为文档的所有fact补全时间戳"""
    service = MultimodalAlignmentService(db)
    aligned = service.align_facts_with_timestamps(project_id, document_id)

    return {
        "document_id": document_id,
        "aligned_facts": aligned,
        "message": f"成功为 {aligned} 条事实补全时间戳"
    }


@router.get("/documents/{document_id}/content-at-time", response_model=TimelineContentResponse)
async def get_content_at_time(
    document_id: int,
    project_id: int,
    current_sec: float,
    window_sec: float = Query(2.0, ge=0.5, le=10.0),
    db: Session = Depends(get_db)
):
    """获取指定时间点附近的所有内容（用于播放器实时高亮）"""
    service = MultimodalAlignmentService(db)
    content = service.get_content_at_time(project_id, document_id, current_sec, window_sec)

    return content


@router.get("/entities/{entity_name}/timeline")
async def get_entity_timeline(
    entity_name: str,
    project_id: int,
    document_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取实体在时间轴上的所有出现点"""
    service = MultimodalAlignmentService(db)
    timeline = service.get_entity_timeline(project_id, entity_name, document_id)

    return {
        "entity_name": entity_name,
        "total_occurrences": len(timeline),
        "timeline": timeline
    }


@router.get("/entities/{entity_name}/profile")
async def get_entity_profile(
    entity_name: str,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取实体的完整画像（跨文档）"""
    service = MultimodalAlignmentService(db)
    profile = service.get_entity_full_profile(project_id, entity_name)

    return profile


@router.get("/events/{event_summary}/profile")
async def get_event_profile(
    event_summary: str,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取事件的完整画像"""
    service = MultimodalAlignmentService(db)
    profile = service.get_event_full_profile(project_id, event_summary)

    return profile


@router.get("/documents/{document_id}/timestamp-validation")
async def validate_timestamps(
    document_id: int,
    project_id: int,
    db: Session = Depends(get_db)
):
    """验证文档的时间戳覆盖率"""
    service = MultimodalAlignmentService(db)
    validation = service.validate_timestamp_coverage(project_id, document_id)

    return validation


# ==================== 智能推荐 ====================

@router.get("/objects/{fid}/recommend", response_model=List[RecommendationResponse])
async def get_recommendations(
    fid: str,
    max_recommendations: int = Query(5, le=20),
    min_confidence: float = Query(0.6, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """获取与当前对象相关的推荐内容"""
    recommender = CorrelationRecommender(db)
    recommendations = recommender.recommend(fid, max_recommendations=max_recommendations, min_confidence=min_confidence)

    return recommendations


@router.get("/projects/{project_id}/hot-connections")
async def get_hot_connections(
    project_id: int,
    top_n: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """发现项目中的热点连接"""
    recommender = CorrelationRecommender(db)
    hot_connections = recommender.discover_hot_connections(project_id, top_n)

    return {
        "project_id": project_id,
        "hot_connections": hot_connections
    }
