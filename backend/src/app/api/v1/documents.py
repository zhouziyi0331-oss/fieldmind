"""
文档管理路由 - 支持同步处理
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from typing import List, Dict, Any
import os
import shutil
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.tools.document import UnifiedDocumentPipeline
from app.models.document import Document

# from app.tasks.document_tasks import process_document_chain
# from app.celery_app import celery_app
# 暂时使用同步处理，避免Celery依赖问题

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads/documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: int = 1,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    上传文档 - 完整处理流程（同步）

    自动触发：
    1. 保存文件
    2. 创建document记录
    3. 运行DocumentProcessingPipeline
    4. 返回处理结果
    """
    try:
        # 1. 保存文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. 创建document记录
        document = Document(
            filename=filename,
            original_filename=file.filename,
            file_type="docx" if file.filename.endswith('.docx') else "pdf",
            file_path=file_path,
            file_size=os.path.getsize(file_path)
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # 3. 运行DocumentProcessingPipeline
        pipeline = UnifiedDocumentPipeline()

        result = pipeline.process_document(
            document_id=document.id,
            file_path=file_path,
            project_id=project_id,
            db=db
        )

        # 4. 更新document统计
        if result.get('success'):
            document.chunk_count = result.get('stages', {}).get('chunk', {}).get('total_chunks', 0)
            document.summary = f"已处理，包含{document.chunk_count}个文本块"

        db.commit()

        return {
            "success": True,
            "message": "文档处理完成",
            "document_id": document.id,
            "file_path": file_path,
            "filename": filename,
            "processing_result": {
                "fact_statements_count": result.get('stages', {}).get('fact_extraction', {}).get('facts_count', 0),
                "chunks_stored": result.get('stages', {}).get('index', {}).get('stored_chunks', 0),
                "entities_count": result.get('stages', {}).get('knowledge_graph', {}).get('entities_count', 0),
            },
            "created_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/status/{task_id}")
async def get_processing_status(task_id: str) -> Dict[str, Any]:
    """
    查询文档处理状态
    """
    try:
        task = celery_app.AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "state": task.state,
            "ready": task.ready(),
        }

        if task.ready():
            if task.successful():
                response["result"] = task.result
            else:
                response["error"] = str(task.info)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")


@router.post("/batch-upload")
async def batch_upload_documents(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    """
    批量上传文档 - 每个文档自动触发独立处理流程
    """
    results = []

    for file in files:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # 触发任务
            task = process_document_chain.delay(file_path)

            results.append({
                "success": True,
                "filename": filename,
                "task_id": task.id,
            })

        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e),
            })

    return {
        "total": len(files),
        "success_count": sum(1 for r in results if r["success"]),
        "results": results,
    }


@router.get("/list")
async def list_documents(skip: int = 0, limit: int = 20) -> Dict[str, Any]:
    """
    列出已上传的文档
    """
    try:
        files = []
        for filepath in Path(UPLOAD_DIR).glob("*"):
            if filepath.is_file():
                stat = filepath.stat()
                files.append({
                    "filename": filepath.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "path": str(filepath),
                })

        # 按上传时间倒序排序
        files.sort(key=lambda x: x["created_at"], reverse=True)

        # 分页
        total = len(files)
        paginated = files[skip : skip + limit]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "documents": paginated,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列表查询失败: {str(e)}")


@router.delete("/{filename}")
async def delete_document(filename: str) -> Dict[str, Any]:
    """
    删除文档
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文档不存在")

        os.remove(file_path)

        return {
            "success": True,
            "message": f"文档 {filename} 已删除",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
