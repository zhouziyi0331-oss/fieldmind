"""
统一项目管理API - 整合所有项目管理相关功能
合并自: v1/projects, v1/project_documents
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.schemas.response import success_response, ApiResponse

router = APIRouter(prefix="/api/projects", tags=["统一项目管理"])

# ============================================================================
# 请求/响应模型
# ============================================================================

class ProjectCreateRequest(BaseModel):
    """项目创建请求"""
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")


class ProjectUpdateRequest(BaseModel):
    """项目更新请求"""
    name: Optional[str] = Field(None, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")


class ContextCreateRequest(BaseModel):
    """上下文创建请求"""
    title: str = Field(..., description="上下文标题")
    content: str = Field(..., description="上下文内容")


# ============================================================================
# 1. 项目CRUD
# ============================================================================

@router.post("", response_model=ApiResponse, summary="创建项目")
async def create_project(
    request: Request,
    project_request: ProjectCreateRequest,
    db: Session = Depends(get_db)
):
    """创建新项目"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import Project

        project = Project(
            name=project_request.name,
            description=project_request.description,
            created_at=datetime.now()
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return success_response(
            data={
                "project_id": project.id,
                "name": project.name,
                "description": project.description
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=ApiResponse, summary="查询项目列表")
async def list_projects(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    archived: bool = Query(False, description="是否包含归档项目"),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import Project

        query = db.query(Project)

        if not archived:
            query = query.filter(Project.archived == False)

        total = query.count()
        projects = query.offset(offset).limit(limit).all()

        result = {
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "archived": p.archived if hasattr(p, 'archived') else False,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in projects
            ],
            "total": total
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ApiResponse, summary="获取项目详情")
async def get_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的详细信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        result = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "archived": project.archived if hasattr(project, 'archived') else False,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if hasattr(project, 'updated_at') and project.updated_at else None
        }

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}", response_model=ApiResponse, summary="更新项目")
async def update_project(
    request: Request,
    project_id: int,
    update_request: ProjectUpdateRequest,
    db: Session = Depends(get_db)
):
    """更新项目信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if update_request.name is not None:
            project.name = update_request.name
        if update_request.description is not None:
            project.description = update_request.description

        if hasattr(project, 'updated_at'):
            project.updated_at = datetime.now()

        db.commit()
        db.refresh(project)

        return success_response(
            data={
                "project_id": project.id,
                "name": project.name,
                "description": project.description
            },
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", response_model=ApiResponse, summary="删除项目")
async def delete_project(
    request: Request,
    project_id: int,
    force: bool = Query(False, description="强制删除（包含所有关联数据）"),
    db: Session = Depends(get_db)
):
    """删除项目"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if force:
            # TODO: 删除关联数据（文档、会话等）
            pass

        db.delete(project)
        db.commit()

        return success_response(
            data={"deleted_project_id": project_id},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2. 项目归档
# ============================================================================

@router.post("/{project_id}/archive", response_model=ApiResponse, summary="归档项目")
async def archive_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """归档项目"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if hasattr(project, 'archived'):
            project.archived = True
            db.commit()

        return success_response(
            data={"project_id": project_id, "archived": True},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/restore", response_model=ApiResponse, summary="恢复项目")
async def restore_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """恢复归档的项目"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import Project

        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        if hasattr(project, 'archived'):
            project.archived = False
            db.commit()

        return success_response(
            data={"project_id": project_id, "archived": False},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. 项目文档管理
# ============================================================================

@router.get("/{project_id}/documents", response_model=ApiResponse, summary="获取项目文档列表")
async def list_project_documents(
    request: Request,
    project_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """获取项目的文档列表"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        query = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        )

        total = query.count()
        documents = query.offset(offset).limit(limit).all()

        result = {
            "project_id": project_id,
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "status": doc.status,
                    "created_at": doc.created_at.isoformat() if doc.created_at else None
                }
                for doc in documents
            ],
            "total": total
        }

        return success_response(data=result, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/documents/upload", response_model=ApiResponse, summary="上传项目文档")
async def upload_project_document(
    request: Request,
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传文档到项目"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument
        import shutil
        from pathlib import Path

        # 保存文件
        upload_dir = Path(f"uploads/project_{project_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / file.filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 创建文档记录
        document = ProjectDocument(
            project_id=project_id,
            filename=file.filename,
            file_path=str(file_path),
            status="uploaded"
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return success_response(
            data={
                "document_id": document.id,
                "filename": document.filename,
                "project_id": project_id
            },
            request_id=request_id
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/documents/{document_id}", response_model=ApiResponse, summary="获取文档详情")
async def get_project_document(
    request: Request,
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """获取项目文档的详细信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id,
            ProjectDocument.project_id == project_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        result = {
            "id": document.id,
            "filename": document.filename,
            "status": document.status,
            "project_id": document.project_id,
            "created_at": document.created_at.isoformat() if document.created_at else None
        }

        return success_response(data=result, request_id=request_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}/documents/{document_id}", response_model=ApiResponse, summary="删除项目文档")
async def delete_project_document(
    request: Request,
    project_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """删除项目中的文档"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument

        document = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id,
            ProjectDocument.project_id == project_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        db.delete(document)
        db.commit()

        return success_response(
            data={"deleted_document_id": document_id},
            request_id=request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 4. 项目上下文管理
# ============================================================================

@router.post("/{project_id}/contexts", response_model=ApiResponse, summary="创建项目上下文")
async def create_context(
    request: Request,
    project_id: int,
    context_request: ContextCreateRequest,
    db: Session = Depends(get_db)
):
    """为项目创建上下文"""
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 实现上下文存储
        context = {
            "context_id": 1,
            "project_id": project_id,
            "title": context_request.title,
            "content": context_request.content
        }

        return success_response(data=context, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/contexts", response_model=ApiResponse, summary="获取项目上下文列表")
async def list_contexts(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的上下文列表"""
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 从数据库获取上下文
        contexts = []

        return success_response(
            data={
                "project_id": project_id,
                "contexts": contexts
            },
            request_id=request_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/contexts/{context_id}", response_model=ApiResponse, summary="获取上下文详情")
async def get_context(
    request: Request,
    project_id: int,
    context_id: int,
    db: Session = Depends(get_db)
):
    """获取项目上下文的详细信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        # TODO: 从数据库获取上下文
        context = {
            "context_id": context_id,
            "project_id": project_id,
            "title": "上下文标题",
            "content": "上下文内容"
        }

        return success_response(data=context, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 5. 项目统计
# ============================================================================

@router.get("/{project_id}/statistics", response_model=ApiResponse, summary="项目统计信息")
async def get_project_statistics(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db)
):
    """获取项目的统计信息"""
    request_id = getattr(request.state, "request_id", None)

    try:
        from app.models.project import ProjectDocument
        from app.models.chat import ChatSession
        from sqlalchemy import func

        # 文档统计
        doc_count = db.query(func.count(ProjectDocument.id)).filter(
            ProjectDocument.project_id == project_id
        ).scalar() or 0

        # 会话统计
        session_count = db.query(func.count(ChatSession.id)).filter(
            ChatSession.project_id == project_id
        ).scalar() or 0

        stats = {
            "project_id": project_id,
            "document_count": doc_count,
            "session_count": session_count
        }

        return success_response(data=stats, request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
