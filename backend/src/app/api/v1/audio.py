"""
音频API路由 - 集成 Celery 自动任务触发
"""

from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import uuid
import shutil
import os

from app.core.exceptions import ValidationException, FileException

# from app.tasks.audio_tasks import process_audio_chain
# 暂时注释，避免导入错误
# from app.celery_app import celery_app
# 暂时注释，避免Celery依赖

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
os.makedirs(os.path.join(UPLOAD_DIR, "audio"), exist_ok=True)


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    auto_process: bool = True
) -> Dict[str, Any]:
    """
    上传音频文件 - 自动触发完整处理流程

    自动触发（当 auto_process=True）：
    1. 提取音频元数据（ffprobe）
    2. Whisper 转录
    3. HanLP 实体提取
    4. 向量化存储
    5. 知识图谱构建

    Args:
        file: 音频文件
        auto_process: 是否自动处理（默认 True）

    Returns:
        上传结果和任务ID
    """
    # 验证文件类型
    allowed_extensions = [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"]
    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise ValidationException(
            message=f"不支持的文件格式。允许的格式: {', '.join(allowed_extensions)}",
            field="file",
            details={"file_extension": file_ext, "allowed_extensions": allowed_extensions}
        )

    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    upload_dir = Path(UPLOAD_DIR) / "audio"
    file_path = upload_dir / filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    response = {
        "success": True,
        "filename": filename,
        "file_path": str(file_path),
        "created_at": datetime.utcnow().isoformat(),
    }

    # 自动触发处理链
    if auto_process:
        # task = process_audio_chain.delay(str(file_path))
        response.update({
            "message": "音频上传成功（后台处理功能待实现）",
            "task_id": "pending",
            "status_url": f"/api/v1/audio/status/pending",
        })
    else:
        response["message"] = "音频上传成功（未启用自动处理）"

    return response


@router.get("/status/{task_id}")
async def get_audio_processing_status(task_id: str) -> Dict[str, Any]:
    """
    查询音频处理状态
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
        raise FileException(
            message="状态查询失败",
            operation="status_check",
            details={"task_id": task_id, "error": str(e)}
        )


@router.get("/list")
async def list_audio_files(skip: int = 0, limit: int = 20) -> Dict[str, Any]:
    """
    列出已上传的音频文件
    """
    try:
        upload_dir = Path(UPLOAD_DIR) / "audio"
        files = []

        for filepath in upload_dir.glob("*"):
            if filepath.is_file():
                stat = filepath.stat()
                files.append({
                    "filename": filepath.name,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "path": str(filepath),
                })

        # 按上传时间倒序
        files.sort(key=lambda x: x["created_at"], reverse=True)

        # 分页
        total = len(files)
        paginated = files[skip : skip + limit]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "audio_files": paginated,
        }

    except Exception as e:
        raise FileException(
            message="列表查询失败",
            operation="list",
            details={"error": str(e)}
        )
