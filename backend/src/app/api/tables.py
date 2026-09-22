"""表格管理 API：表格文件和文件管理共用 project_documents 主表。"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import success_response, error_response
from app.models.project import ProjectDocument
from app.services.background_tasks import submit_task
from app.services.project_document_upload import upload_project_document
from app.services.table_processor import table_processor

router = APIRouter(tags=["表格管理"])
logger = logging.getLogger(__name__)
TABLE_TYPES = {"csv", "xls", "xlsx"}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        if isinstance(value, float) and value != value:
            return None
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass
    return str(value)


def _extension(document: ProjectDocument) -> str:
    return os.path.splitext(document.original_filename or document.filename)[1].lower().lstrip(".")


def _is_table(document: ProjectDocument) -> bool:
    return _extension(document) in TABLE_TYPES or (document.file_type or "").lower() in TABLE_TYPES


def _display_format(document: ProjectDocument) -> str:
    metadata = (document.extra_data or {}).get("table_metadata") or {}
    return metadata.get("format") or ("CSV" if _extension(document) == "csv" else "Excel")


def _metadata(document: ProjectDocument) -> dict[str, Any]:
    value = (document.extra_data or {}).get("table_metadata")
    return value if isinstance(value, dict) else {}


def _response(document: ProjectDocument) -> dict[str, Any]:
    metadata = _metadata(document)
    columns = metadata.get("columns") or []
    return {
        "id": document.id,
        "project_id": document.project_id,
        "filename": document.original_filename or document.filename,
        "format": _display_format(document),
        "file_size": document.file_size or 0,
        "row_count": int(metadata.get("row_count") or 0),
        "column_count": int(metadata.get("column_count") or len(columns)),
        "columns": [str(column) for column in columns],
        "preview": (metadata.get("preview") or [])[:20],
        "tags": [tag.name for tag in (document.tags or [])],
        "description": metadata.get("description"),
        "uploaded_at": document.created_at,
        "updated_at": document.updated_at or document.created_at,
    }


def _find(db: Session, project_id: int, table_id: int) -> ProjectDocument:
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == table_id,
        ProjectDocument.project_id == project_id,
    ).first()
    if not document or not _is_table(document):
        raise HTTPException(status_code=404, detail="表格不存在")
    return document


@router.get("/projects/{project_id}/tables")
@router.get("/projects/{project_id}/tables/")
async def list_tables(project_id: int, format: Optional[str] = Query(None), db: Session = Depends(get_db)):
    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).order_by(ProjectDocument.created_at.desc()).all()
    tables = [document for document in documents if _is_table(document)]
    if format and format not in {"全部类型", "全部"}:
        tables = [document for document in tables if _display_format(document).lower() == format.lower()]
    return success_response(
        data={
            "tables": [_response(document) for document in tables],
            "total": len(tables)
        }
    )


@router.get("/projects/{project_id}/tables/statistics")
@router.get("/projects/{project_id}/tables/statistics/")
async def table_statistics(project_id: int, db: Session = Depends(get_db)):
    documents = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).all()
    tables = [_response(document) for document in documents if _is_table(document)]
    format_counts: dict[str, int] = {}
    for table in tables:
        format_name = str(table["format"])
        format_counts[format_name] = format_counts.get(format_name, 0) + 1
    return success_response(
        data={
            "total_tables": len(tables),
            "total_rows": sum(table["row_count"] for table in tables),
            "total_size": sum(table["file_size"] for table in tables),
            "format_counts": format_counts
        }
    )


@router.get("/projects/{project_id}/tables/{table_id}")
@router.get("/projects/{project_id}/tables/{table_id}/")
async def get_table(project_id: int, table_id: int, db: Session = Depends(get_db)):
    return _response(_find(db, project_id, table_id))


@router.post("/projects/{project_id}/tables/upload")
@router.post("/projects/{project_id}/tables/upload/")
async def upload_table(
    project_id: int,
    file: UploadFile = File(...),
    format: Optional[str] = Form(None),
    tags: Optional[list[str]] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    filename = os.path.basename(file.filename or "")
    extension = os.path.splitext(filename)[1].lower().lstrip(".")
    if extension not in TABLE_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 CSV、XLS、XLSX 表格")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="表格文件不能为空")

    try:
        document, created = upload_project_document(
            db, project_id=project_id, original_filename=filename, content=content,
            mime_type=file.content_type, metadata={"source_module": "tables"}, status="pending"
        )
        parsed = table_processor.process_file(document.file_path)
        extracted = parsed.get("tables") or []
        metadata = _metadata(document)
        if extracted:
            first = extracted[0]
            rows = _json_safe(first.get("data_json") or [])
            columns = _json_safe(first.get("columns") or [])
            metadata.update({
                "columns": columns,
                "preview": [list(row.values()) for row in rows[:20] if isinstance(row, dict)],
                "row_count": sum(int(item.get("row_count") or 0) for item in extracted),
                "column_count": len(columns),
                "sheet_count": len(extracted),
            })
        metadata.update({
            "format": format or ("CSV" if extension == "csv" else "Excel"),
            "description": description,
        })
        extra_data = dict(document.extra_data or {})
        extra_data["table_metadata"] = _json_safe(metadata)
        document.extra_data = extra_data
        if tags:
            from app.models.project import ProjectDocumentTag
            for tag_name in tags:
                clean_tag = tag_name.strip()
                if clean_tag and not any(tag.name == clean_tag for tag in document.tags):
                    db.add(ProjectDocumentTag(document_id=document.id, name=clean_tag, category="table", source="manual"))
        db.commit()
        db.refresh(document)
        if created:
            submit_task(document.id)
        return _response(document)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("表格上传失败")
        raise HTTPException(status_code=500, detail=f"表格处理失败: {exc}")


@router.delete("/projects/{project_id}/tables/{table_id}")
@router.delete("/projects/{project_id}/tables/{table_id}/")
async def delete_table(project_id: int, table_id: int, db: Session = Depends(get_db)):
    document = _find(db, project_id, table_id)
    if document.file_path and os.path.exists(document.file_path):
        os.remove(document.file_path)
    db.delete(document)
    db.commit()
    return success_response(message="表格已删除")
