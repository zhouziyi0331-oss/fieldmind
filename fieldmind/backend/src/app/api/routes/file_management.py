"""
文件管理API - 展示原始稿和汇总稿
支持：
1. 查看项目下所有上传的文件
2. 查看单个文件的转译结果（原始稿）
3. 查看项目的汇总稿
4. 溯源查询（点击查看来源）
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.core.hermes import hermes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/file-management", tags=["文件管理"])


# ==================== 请求/响应模型 ====================

class FileItem(BaseModel):
    """文件条目"""
    file_id: str
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    uploaded_at: str
    status: str  # pending, processing, completed, failed
    packet_id: Optional[str] = None


class TranscriptResponse(BaseModel):
    """转译结果"""
    file_id: str
    file_name: str
    file_type: str
    original_content: str  # 原始内容（如果翻译了）
    translated_content: str  # 翻译后的内容
    was_translated: bool
    original_language: str
    sources: List[dict]  # 溯源信息
    metadata: dict
    metrics: dict


class MergedResponse(BaseModel):
    """汇总稿"""
    project_id: int
    total_files: int
    total_sentences: int
    merged_content: str  # 所有文件汇总的内容
    file_list: List[dict]  # 包含的文件列表
    sources: List[dict]  # 所有溯源信息


class SourceQueryResponse(BaseModel):
    """溯源查询结果"""
    sentence: str
    sentence_index: int
    source: dict  # 来源信息
    citation: str  # 格式化的引用


# ==================== API端点 ====================

@router.get("/projects/{project_id}/files", response_model=List[FileItem])
async def list_project_files(
    project_id: int,
    status: Optional[str] = Query(None, description="筛选状态: pending, processing, completed, failed"),
    db: Session = Depends(get_db)
):
    """
    获取项目下所有上传的文件列表

    显示：
    - 文件名、类型、大小
    - 上传时间
    - 处理状态
    - 可点击查看详情
    """
    try:
        # 从Hermes获取项目的所有packets
        project_status = hermes.get_project_status(project_id)

        files = []
        for packet_id, packet_info in project_status.get("packets", {}).items():
            packet = hermes.packets.get(packet_id)
            if not packet:
                continue

            # 过滤状态
            if status and packet.status.value != status:
                continue

            # 获取文件信息
            data = packet.data
            metadata = packet.metadata

            files.append(FileItem(
                file_id=packet_id,
                file_name=metadata.get("file_name", "未知文件"),
                file_path=data.get("file_path", ""),
                file_type=metadata.get("file_type", "unknown"),
                file_size=metadata.get("file_size", 0),
                uploaded_at=packet.created_at.isoformat(),
                status=packet.status.value,
                packet_id=packet_id
            ))

        logger.info(f"✅ 获取项目 {project_id} 的文件列表: {len(files)} 个文件")
        return files

    except Exception as e:
        logger.error(f"❌ 获取文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}/transcript", response_model=TranscriptResponse)
async def get_file_transcript(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个文件的转译结果（原始稿）

    显示：
    - 原文（如果翻译了）
    - 译文
    - 溯源信息（每句话的来源）
    - 可点击溯源查看详细出处
    """
    try:
        # 获取packet
        packet = hermes.packets.get(file_id)
        if not packet:
            raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

        # 获取处理结果
        data = packet.data
        metadata = packet.metadata

        # 提取内容
        raw_content = data.get("raw_content", "")
        original_content = metadata.get("original_content", raw_content)
        sources = metadata.get("sources", [])
        translated = metadata.get("translated", False)
        original_language = metadata.get("original_language", "unknown")

        # 构建响应
        response = TranscriptResponse(
            file_id=file_id,
            file_name=metadata.get("file_name", "未知文件"),
            file_type=metadata.get("file_type", "unknown"),
            original_content=original_content,
            translated_content=raw_content,
            was_translated=translated,
            original_language=original_language,
            sources=sources,
            metadata=metadata,
            metrics=metadata.get("metrics", {})
        )

        logger.info(f"✅ 获取文件 {file_id} 的转译结果: {len(sources)} 条溯源")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取转译结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/merged", response_model=MergedResponse)
async def get_project_merged(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的汇总稿

    显示：
    - 所有文件汇总的完整内容
    - 包含的文件列表
    - 所有溯源信息（合并）
    - 可以看到整体内容，也可以追溯到具体来源
    """
    try:
        # 获取项目状态
        project_status = hermes.get_project_status(project_id)

        # 收集所有已完成的packets
        all_content_parts = []
        all_sources = []
        file_list = []

        for packet_id, packet_info in project_status.get("packets", {}).items():
            packet = hermes.packets.get(packet_id)
            if not packet or packet.status.value != "completed":
                continue

            # 获取内容
            data = packet.data
            metadata = packet.metadata

            raw_content = data.get("raw_content", "")
            sources = metadata.get("sources", [])

            # 添加文件标记
            file_name = metadata.get("file_name", "未知文件")
            all_content_parts.append(f"\n\n=== 文件: {file_name} ===\n\n")
            all_content_parts.append(raw_content)

            # 合并溯源（重新编号）
            base_index = len(all_sources)
            for source in sources:
                all_sources.append({
                    **source,
                    "sentence_index": base_index + source.get("sentence_index", 0),
                    "file_id": packet_id
                })

            # 记录文件信息
            file_list.append({
                "file_id": packet_id,
                "file_name": file_name,
                "file_type": metadata.get("file_type", "unknown"),
                "sentence_count": len(sources),
                "processed_at": packet.updated_at.isoformat()
            })

        # 合并内容
        merged_content = "".join(all_content_parts)

        response = MergedResponse(
            project_id=project_id,
            total_files=len(file_list),
            total_sentences=len(all_sources),
            merged_content=merged_content,
            file_list=file_list,
            sources=all_sources
        )

        logger.info(f"✅ 获取项目 {project_id} 汇总稿: {len(file_list)} 个文件, {len(all_sources)} 条溯源")
        return response

    except Exception as e:
        logger.error(f"❌ 获取汇总稿失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/{sentence_index}", response_model=SourceQueryResponse)
async def query_source(
    sentence_index: int,
    file_id: Optional[str] = Query(None, description="文件ID（如果是单文件查询）"),
    project_id: Optional[int] = Query(None, description="项目ID（如果是汇总稿查询）"),
    db: Session = Depends(get_db)
):
    """
    溯源查询 - 根据句子索引查找来源

    用户点击某句话时，显示：
    - 这句话的完整内容
    - 来源：哪个文件、第几页、第几段、第几句
    - 或者：时间戳（音频/视频）
    - 格式化的引用文本
    """
    try:
        sources = []

        # 单文件查询
        if file_id:
            packet = hermes.packets.get(file_id)
            if not packet:
                raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

            sources = packet.metadata.get("sources", [])

        # 项目汇总查询
        elif project_id:
            # 获取项目汇总
            merged = await get_project_merged(project_id, db)
            sources = merged.sources

        else:
            raise HTTPException(status_code=400, detail="必须提供 file_id 或 project_id")

        # 查找对应的句子
        target_source = None
        for source in sources:
            if source.get("sentence_index") == sentence_index:
                target_source = source
                break

        if not target_source:
            raise HTTPException(status_code=404, detail=f"未找到句子索引 {sentence_index}")

        # 格式化引用
        from app.services.source_tracker import SourceTracker
        tracker = SourceTracker()
        citation = tracker.format_citation(target_source.get("source", {}))

        response = SourceQueryResponse(
            sentence=target_source.get("sentence", ""),
            sentence_index=sentence_index,
            source=target_source.get("source", {}),
            citation=citation
        )

        logger.info(f"✅ 溯源查询: 句子 {sentence_index} -> {citation}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 溯源查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/files/{file_id}/")
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    删除文件及其处理结果
    """
    try:
        # 从Hermes中删除packet
        if file_id in hermes.packets:
            del hermes.packets[file_id]
            logger.info(f"✅ 删除文件: {file_id}")
            return {"success": True, "message": f"文件 {file_id} 已删除"}
        else:
            raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}/download/")
async def download_original_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    下载原始文件
    """
    from fastapi.responses import FileResponse

    try:
        packet = hermes.packets.get(file_id)
        if not packet:
            raise HTTPException(status_code=404, detail=f"文件 {file_id} 不存在")

        file_path = packet.data.get("file_path", "")
        if not file_path:
            raise HTTPException(status_code=404, detail="文件路径不存在")

        import os
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件已被删除")

        file_name = packet.metadata.get("file_name", "download")

        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type='application/octet-stream'
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 下载文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
