"""
知识图谱API v3 - 链路16：证据链绑定

新增功能：
1. 从文档提取证据链
2. 按衣食住行分类查询
3. 获取实体的所有证据（原话+时间戳）
4. 点击图谱节点 -> 显示证据列表
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.models.entity import Entity
from app.models.entity_evidence import EntityEvidence
from app.models.project import ProjectDocument
from app.services.evidence_extractor import get_evidence_extractor
from app.schemas.response import success_response, error_response

router = APIRouter(tags=["knowledge-graph-v3"])
logger = logging.getLogger(__name__)


# ==================== Schemas ====================

class ExtractEvidencesRequest(BaseModel):
    """提取证据链请求"""
    project_id: int
    document_ids: Optional[List[int]] = None  # 空表示处理所有文档


class EntityWithEvidencesResponse(BaseModel):
    """实体详情（带证据链）"""
    model_config = {"from_attributes": True}

    id: str
    name: str
    entity_type: str
    category: Optional[str]  # 衣食住行分类
    mention_count: int
    confidence: float
    evidences: List[dict]  # 证据列表


class EvidenceResponse(BaseModel):
    """证据响应"""
    model_config = {"from_attributes": True}

    id: str
    entity_id: str
    document_id: int
    chunk_id: str
    text: str
    media_type: Optional[str]
    timestamp_start: Optional[float]
    timestamp_end: Optional[float]
    timestamp_display: Optional[str]
    speaker: Optional[str]
    page_number: Optional[int]
    category: Optional[str]
    confidence: float


# ==================== API Endpoints ====================

@router.post("/extract-evidences")
async def extract_evidences(
    request: ExtractEvidencesRequest,
    db: Session = Depends(get_db)
):
    """
    从文档提取证据链（链路16核心接口）

    处理流程：
    1. 从ChromaDB读取文档的所有chunks
    2. 对每个chunk进行实体识别
    3. 提取包含实体的句子作为证据
    4. 绑定音频时间戳（如果是音频chunk）
    5. 分类到衣食住行等维度
    6. 存储到EntityEvidence表
    """
    try:
        extractor = get_evidence_extractor(db)

        if request.document_ids:
            # 处理指定文档
            total_stats = {
                "documents_processed": 0,
                "chunks_processed": 0,
                "entities_found": 0,
                "evidences_created": 0,
                "errors": []
            }

            for doc_id in request.document_ids:
                try:
                    stats = extractor.extract_from_document(doc_id, request.project_id)
                    total_stats["documents_processed"] += 1
                    total_stats["chunks_processed"] += stats["chunks_processed"]
                    total_stats["entities_found"] += stats["entities_found"]
                    total_stats["evidences_created"] += stats["evidences_created"]
                except Exception as e:
                    logger.error(f"处理文档 {doc_id} 失败: {e}")
                    total_stats["errors"].append({"document_id": doc_id, "error": str(e)})

            return success_response(
                data=total_stats,
                message=f"证据链提取完成：{total_stats['documents_processed']} 个文档"
            )
        else:
            # 处理项目所有文档
            doc_ids = [doc.id for doc in db.query(ProjectDocument.id).filter(
                ProjectDocument.project_id == request.project_id
            ).all()]

            if not doc_ids:
                return {
                    "status": "completed",
                    "message": "项目无文档",
                    "stats": {
                        "documents_processed": 0,
                        "chunks_processed": 0,
                        "entities_found": 0,
                        "evidences_created": 0
                    }
                }

            total_stats = {
                "documents_processed": 0,
                "chunks_processed": 0,
                "entities_found": 0,
                "evidences_created": 0,
                "errors": []
            }

            for doc_id in doc_ids:
                try:
                    stats = extractor.extract_from_document(doc_id, request.project_id)
                    total_stats["documents_processed"] += 1
                    total_stats["chunks_processed"] += stats["chunks_processed"]
                    total_stats["entities_found"] += stats["entities_found"]
                    total_stats["evidences_created"] += stats["evidences_created"]
                except Exception as e:
                    logger.error(f"处理文档 {doc_id} 失败: {e}")
                    total_stats["errors"].append({"document_id": doc_id, "error": str(e)})

            return success_response(
                data=total_stats,
                message=f"项目证据链提取完成：{total_stats['documents_processed']} 个文档"
            )

    except Exception as e:
        logger.error(f"提取证据链失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")


@router.get("/entities/{entity_id}/evidences/")
async def get_entity_evidences(
    entity_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    获取实体的所有证据（链路16核心功能）

    用户点击知识图谱中的节点（如"杀猪菜"），显示：
    - 所有提到"杀猪菜"的访谈原话
    - 精确时间戳（几分几秒）
    - 说话人
    - 来源文件

    示例返回：
    {
      "entity": {"id": "xxx", "name": "杀猪菜", "type": "food"},
      "evidences": [
        {
          "text": "杀猪菜用的肉必须是自家养的土猪",
          "source_file": "访谈老李_20240801.mp3",
          "timestamp_display": "23:45-24:10",
          "speaker": "老李",
          "category": "food"
        }
      ]
    }
    """
    # 获取实体
    entity = db.query(Entity).filter(Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="实体不存在")

    # 获取证据
    extractor = get_evidence_extractor(db)
    evidences = extractor.get_entity_evidences(entity_id, limit)

    # 补充文档信息
    for evidence in evidences:
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == evidence["document_id"]
        ).first()
        if doc:
            evidence["source_file"] = doc.filename
            evidence["document_title"] = doc.title

    return success_response(
        data={
            "entity": {
                "id": entity.id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "mention_count": entity.mention_count,
                "confidence": entity.confidence
            },
            "evidences": evidences,
            "total_count": len(evidences)
        }
    )


@router.get("/categories/{category}/evidences/")
async def get_category_evidences(
    category: str,
    project_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    按分类查询证据（衣食住行）

    示例：
    - GET /categories/food/evidences?project_id=1
      返回所有"食"分类的证据

    分类：
    - food: 食
    - clothing: 衣
    - housing: 住
    - transportation: 行
    - folk_song: 民歌
    - ritual: 仪式
    - kinship: 亲属
    """
    valid_categories = ["food", "clothing", "housing", "transportation", "folk_song", "ritual", "kinship"]
    if category not in valid_categories:
        raise HTTPException(
            status_code=400,
            detail=f"无效分类，支持的分类: {', '.join(valid_categories)}"
        )

    extractor = get_evidence_extractor(db)
    evidences = extractor.search_evidences_by_category(category, project_id, limit)

    # 补充文档信息
    for evidence in evidences:
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == evidence["document_id"]
        ).first()
        if doc:
            evidence["source_file"] = doc.filename

    return success_response(
        data={
            "category": category,
            "evidences": evidences,
            "total_count": len(evidences)
        }
    )


@router.get("/categories/stats")
async def get_category_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取各分类的统计信息

    返回格式：
    {
      "food": 45,
      "clothing": 12,
      "housing": 23,
      ...
    }
    """
    # 获取项目文档ID
    doc_ids = [doc.id for doc in db.query(ProjectDocument.id).filter(
        ProjectDocument.project_id == project_id
    ).all()]

    if not doc_ids:
        return success_response(data={})

    # 统计各分类的证据数量
    evidences = db.query(EntityEvidence).filter(
        EntityEvidence.document_id.in_(doc_ids),
        EntityEvidence.category.isnot(None)
    ).all()

    stats = {}
    for evidence in evidences:
        category = evidence.category
        stats[category] = stats.get(category, 0) + 1

    return stats


@router.get("/search")
async def search_entities_with_evidences(
    query: str,
    project_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    搜索实体（带证据预览）

    示例：
    - GET /search?query=杀猪菜&project_id=1
      返回包含"杀猪菜"的实体及其部分证据
    """
    # 获取项目文档ID
    doc_ids = [doc.id for doc in db.query(ProjectDocument.id).filter(
        ProjectDocument.project_id == project_id
    ).all()]

    if not doc_ids:
        return success_response(data={"entities": [], "total_count": 0})

    # 搜索实体
    entities = db.query(Entity).filter(
        Entity.name.like(f"%{query}%")
    ).limit(limit).all()

    # 过滤：只返回与项目相关的实体
    result = []
    for entity in entities:
        if entity.document_ids and any(doc_id in doc_ids for doc_id in entity.document_ids):
            # 获取部分证据（最多3条）
            evidences = db.query(EntityEvidence).filter(
                EntityEvidence.entity_id == entity.id
            ).limit(3).all()

            result.append({
                "id": entity.id,
                "name": entity.name,
                "entity_type": entity.entity_type,
                "mention_count": entity.mention_count,
                "confidence": entity.confidence,
                "evidence_preview": [ev.to_dict() for ev in evidences]
            })

    return success_response(
        data={
            "entities": result,
            "total_count": len(result)
        }
    )


@router.delete("/evidences/{evidence_id}/")
async def delete_evidence(
    evidence_id: str,
    db: Session = Depends(get_db)
):
    """删除证据"""
    evidence = db.query(EntityEvidence).filter(EntityEvidence.id == evidence_id).first()

    if not evidence:
        raise HTTPException(status_code=404, detail="证据不存在")

    db.delete(evidence)
    db.commit()

    return success_response(message="证据已删除")
