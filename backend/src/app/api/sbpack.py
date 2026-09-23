"""
SBPACK API路由

提供SBPACK包的管理、构建、验收API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.sbpack import SBPACKPackage, KnowledgeItem, SkillItem
from app.services.sbpack_builder import SBPACKBuilder
from app.services.sbpack_validator import SBPACKValidator
from app.services.knowledge_track_extractor import KnowledgeTrackExtractor

router = APIRouter(prefix="/api/sbpack", tags=["SBPACK"])


# ==================== Pydantic模型 ====================

class SBPACKPackageCreate(BaseModel):
    """创建SBPACK包"""
    project_id: int
    package_name: str
    source_title: Optional[str] = None
    source_author: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None


class SBPACKPackageResponse(BaseModel):
    """SBPACK包响应"""
    id: int
    project_id: int
    package_name: str
    version: str
    protocol_version: str
    source_title: Optional[str]
    source_author: Optional[str]
    knowledge_count: int
    skill_count: int
    relation_count: int
    knowledge_frozen: bool
    skill_frozen: bool
    is_built: bool
    is_verified: bool
    verification_status: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeItemResponse(BaseModel):
    """知识点响应"""
    id: int
    knowledge_id: str
    title: str
    knowledge_type: str
    statement: str
    explanation: str
    why_matters: str
    scope: str
    is_frozen: bool

    class Config:
        from_attributes = True


class SkillItemResponse(BaseModel):
    """技能响应"""
    id: int
    skill_id: str
    name: str
    display_name: Optional[str]
    description: str
    is_frozen: bool
    v1_passed: bool
    v2_passed: bool
    v3_passed: bool

    class Config:
        from_attributes = True


class BuildRequest(BaseModel):
    """构建请求"""
    package_id: int


class VerifyRequest(BaseModel):
    """验收请求"""
    sbpack_path: str


class FreezeRequest(BaseModel):
    """冻结请求"""
    package_id: int
    track_type: str  # "knowledge" or "skill"


# ==================== API端点 ====================

@router.post("/packages", response_model=SBPACKPackageResponse)
def create_package(package: SBPACKPackageCreate, db: Session = Depends(get_db)):
    """创建SBPACK包"""
    # 检查项目是否存在
    from app.models.project import Project
    project = db.query(Project).filter(Project.id == package.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 创建SBPACK包
    sbpack = SBPACKPackage(
        project_id=package.project_id,
        package_name=package.package_name,
        source_title=package.source_title,
        source_author=package.source_author,
        source_type=package.source_type,
        source_url=package.source_url
    )

    db.add(sbpack)
    db.commit()
    db.refresh(sbpack)

    return sbpack


@router.get("/packages", response_model=List[SBPACKPackageResponse])
def list_packages(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """列出SBPACK包"""
    query = db.query(SBPACKPackage)

    if project_id:
        query = query.filter(SBPACKPackage.project_id == project_id)

    packages = query.offset(skip).limit(limit).all()
    return packages


@router.get("/packages/{package_id}", response_model=SBPACKPackageResponse)
def get_package(package_id: int, db: Session = Depends(get_db)):
    """获取SBPACK包详情"""
    package = db.query(SBPACKPackage).filter(SBPACKPackage.id == package_id).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    return package


@router.get("/packages/{package_id}/knowledge", response_model=List[KnowledgeItemResponse])
def list_knowledge(package_id: int, db: Session = Depends(get_db)):
    """列出知识点"""
    # 检查包是否存在
    package = db.query(SBPACKPackage).filter(SBPACKPackage.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    knowledge_items = db.query(KnowledgeItem).filter(
        KnowledgeItem.package_id == package_id
    ).all()

    return knowledge_items


@router.get("/packages/{package_id}/skills", response_model=List[SkillItemResponse])
def list_skills(package_id: int, db: Session = Depends(get_db)):
    """列出技能"""
    # 检查包是否存在
    package = db.query(SBPACKPackage).filter(SBPACKPackage.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    skill_items = db.query(SkillItem).filter(
        SkillItem.package_id == package_id
    ).all()

    return skill_items


@router.post("/freeze")
def freeze_track(request: FreezeRequest, db: Session = Depends(get_db)):
    """冻结知识轨或技能轨"""
    package = db.query(SBPACKPackage).filter(SBPACKPackage.id == request.package_id).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    if request.track_type == "knowledge":
        if package.knowledge_frozen:
            raise HTTPException(status_code=400, detail="Knowledge track already frozen")

        # 计算知识轨冻结哈希
        knowledge_items = db.query(KnowledgeItem).filter(
            KnowledgeItem.package_id == request.package_id
        ).all()

        import hashlib
        import json

        freeze_data = {
            "count": len(knowledge_items),
            "items": [
                {
                    "id": item.knowledge_id,
                    "contentHash": item.content_hash
                }
                for item in knowledge_items
            ]
        }

        freeze_hash = hashlib.sha256(
            json.dumps(freeze_data, sort_keys=True).encode()
        ).hexdigest()

        package.knowledge_frozen = True
        package.knowledge_frozen_at = datetime.utcnow()
        package.knowledge_freeze_hash = freeze_hash

        # 冻结所有知识点
        for item in knowledge_items:
            item.is_frozen = True

        db.commit()

        return {
            "success": True,
            "track": "knowledge",
            "freezeHash": freeze_hash,
            "count": len(knowledge_items)
        }

    elif request.track_type == "skill":
        if package.skill_frozen:
            raise HTTPException(status_code=400, detail="Skill track already frozen")

        # 计算技能轨冻结哈希
        skill_items = db.query(SkillItem).filter(
            SkillItem.package_id == request.package_id
        ).all()

        import hashlib
        import json

        freeze_data = {
            "count": len(skill_items),
            "items": [
                {
                    "id": item.skill_id,
                    "canonicalSha256": item.canonical_sha256
                }
                for item in skill_items
            ]
        }

        freeze_hash = hashlib.sha256(
            json.dumps(freeze_data, sort_keys=True).encode()
        ).hexdigest()

        package.skill_frozen = True
        package.skill_frozen_at = datetime.utcnow()
        package.skill_freeze_hash = freeze_hash

        # 冻结所有技能
        for item in skill_items:
            item.is_frozen = True

        db.commit()

        return {
            "success": True,
            "track": "skill",
            "freezeHash": freeze_hash,
            "count": len(skill_items)
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid track type")


@router.post("/build")
def build_sbpack(request: BuildRequest, db: Session = Depends(get_db)):
    """构建SBPACK文件"""
    builder = SBPACKBuilder(db)

    try:
        result = builder.build(request.package_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Build failed: {str(e)}")


@router.post("/verify")
def verify_sbpack(request: VerifyRequest, db: Session = Depends(get_db)):
    """验收SBPACK文件"""
    validator = SBPACKValidator()

    try:
        result = validator.validate(request.sbpack_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/extract/knowledge/{package_id}")
def extract_knowledge(
    package_id: int,
    normalized_text: str,
    db: Session = Depends(get_db)
):
    """提取知识轨"""
    # 检查包是否存在
    package = db.query(SBPACKPackage).filter(SBPACKPackage.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    # 检查是否已冻结
    if package.knowledge_frozen:
        raise HTTPException(status_code=400, detail="Knowledge track already frozen")

    # 加载项目数据
    from app.models.document_chunk import DocumentChunk
    from app.models.entity import Entity

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.project_id == package.project_id
    ).all()

    entities = db.query(Entity).all()  # 简化版，实际需要过滤

    # 准备数据
    chunks_data = [
        {"id": c.id, "content": c.content}
        for c in chunks
    ]

    entities_data = [
        {"id": e.id, "entity_name": e.entity_name, "entity_type": e.entity_type}
        for e in entities
    ]

    # 提取知识点
    extractor = KnowledgeTrackExtractor(db)
    knowledge_items_data = extractor.extract(
        package_id=package_id,
        normalized_text=normalized_text,
        chunks=chunks_data,
        entities=entities_data
    )

    # 保存知识点到数据库
    knowledge_items = []
    for item_data in knowledge_items_data:
        # 计算内容哈希
        import hashlib
        import json

        content_for_hash = {
            "statement": item_data["statement"],
            "explanation": item_data["explanation"],
            "type": item_data["knowledge_type"]
        }
        content_hash = hashlib.sha256(
            json.dumps(content_for_hash, sort_keys=True).encode()
        ).hexdigest()

        item = KnowledgeItem(
            package_id=package_id,
            knowledge_id=item_data["knowledge_id"],
            title=item_data["title"],
            knowledge_type=item_data["knowledge_type"],
            statement=item_data["statement"],
            explanation=item_data["explanation"],
            why_matters=item_data["why_matters"],
            scope=item_data["scope"],
            conditions=item_data.get("conditions", ""),
            boundaries=item_data.get("boundaries", ""),
            counterexamples=item_data.get("counterexamples", ""),
            evidence_refs=item_data["evidence_refs"],
            evidence_quotes=item_data.get("evidence_quotes", []),
            source_certainty=item_data["source_certainty"],
            extraction_certainty=item_data["extraction_certainty"],
            external_verification=item_data["external_verification"],
            attribution=item_data["attribution"],
            inference_type=item_data["inference_type"],
            content_hash=content_hash
        )
        knowledge_items.append(item)

    db.add_all(knowledge_items)

    # 更新包统计
    package.knowledge_count = len(knowledge_items)
    db.commit()

    return {
        "success": True,
        "knowledge_count": len(knowledge_items),
        "types": {}
    }


@router.delete("/packages/{package_id}")
def delete_package(package_id: int, db: Session = Depends(get_db)):
    """删除SBPACK包"""
    package = db.query(SBPACKPackage).filter(SBPACKPackage.id == package_id).first()

    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    db.delete(package)
    db.commit()

    return {"success": True, "message": "Package deleted"}
