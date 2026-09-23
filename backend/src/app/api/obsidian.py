"""
Obsidian API路由

提供Obsidian导出功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.services.obsidian_exporter import ObsidianExporter

router = APIRouter(prefix="/api/obsidian", tags=["Obsidian"])


class ExportResponse(BaseModel):
    """导出响应"""
    success: bool
    export_dir: str
    zip_path: str
    knowledge_count: int
    skill_count: int


@router.post("/export/{package_id}", response_model=ExportResponse)
async def export_to_obsidian(package_id: int, db: Session = Depends(get_db)):
    """
    导出SBPACK为Obsidian格式

    功能：
    - 生成Markdown笔记（知识点和技能）
    - 创建Obsidian插件
    - 打包为可导入的vault
    """
    try:
        exporter = ObsidianExporter(db)
        result = exporter.export(package_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/download/{package_id}")
async def download_obsidian_vault(package_id: int, db: Session = Depends(get_db)):
    """
    下载Obsidian vault ZIP文件
    """
    from fastapi.responses import FileResponse
    from pathlib import Path

    try:
        exporter = ObsidianExporter(db)
        # 获取导出路径
        # TODO: 实现文件路径缓存
        export_path = Path(f"./obsidian_export/package_{package_id}_obsidian_vault.zip")

        if not export_path.exists():
            raise HTTPException(status_code=404, detail="Export file not found. Please export first.")

        return FileResponse(
            path=str(export_path),
            filename=export_path.name,
            media_type='application/zip'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
