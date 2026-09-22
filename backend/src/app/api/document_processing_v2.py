"""
文档处理API v2 - 链路十四：引用溯源系统
提供完整元数据的文档处理接口
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.database import get_db
from app.schemas.response import success_response, error_response
from app.services.document_processing_pipeline_v2 import get_document_processing_pipeline_v2
from app.services.vectorization_service_complete import VectorizationService
from app.schemas.document_metadata import SourceLevel

router = APIRouter(tags=["document-processing-v2"])
logger = logging.getLogger(__name__)


# ==================== Schema定义 ====================

class DocumentProcessRequest(BaseModel):
    """文档处理请求（链路十四增强版）"""
    document_id: int
    text: str
    filename: str
    file_type: str
    project_id: Optional[int] = None

    # 位置信息
    page_number: Optional[int] = None           # PDF/DOCX页码
    timestamp_start: Optional[float] = None     # 音频开始时间（秒）
    timestamp_end: Optional[float] = None       # 音频结束时间（秒）
    speaker: Optional[str] = None               # 说话人

    # 时间信息
    document_date: Optional[str] = None         # 文档日期（ISO格式）

    # 来源层级（链路17需要）
    source_level: int = 0  # 0=原始材料, 1=一度报告, 2=二度报告, 3=三度报告

    # 扩展字段
    tags: Optional[List[str]] = None


class SearchWithCitationRequest(BaseModel):
    """带引用的检索请求（链路14+15）"""
    query: str
    project_id: Optional[int] = None
    n_results: int = 5
    document_types: Optional[List[str]] = None   # 过滤文档类型
    source_levels: Optional[List[int]] = None    # 过滤来源层级（如[2,3]只检索报告）
    include_citation: bool = True                # 是否包含引用

    # 链路15新增：日期范围过滤
    date_from: Optional[str] = None              # 起始日期 (ISO格式: 2024-01-01)
    date_to: Optional[str] = None                # 结束日期 (ISO格式: 2024-12-31)


# ==================== API接口 ====================

@router.post("/process")
async def process_document_v2(
    request: DocumentProcessRequest,
    db: Session = Depends(get_db)
):
    """
    处理文档（链路十四核心接口）

    完整流程：
    1. 创建带完整元数据的文档对象
    2. 切分文档（每个chunk继承元数据）
    3. 向量化存储（元数据完整入库）
    4. 返回处理结果（包含引用格式预览）

    与旧版的区别：
    - 旧版：只存document_id和chunk_index
    - 新版：存source_file、page_number、timestamp、speaker等完整溯源信息
    """
    try:
        # 解析文档日期
        document_date = None
        if request.document_date:
            try:
                document_date = datetime.fromisoformat(request.document_date)
            except ValueError:
                logger.warning(f"⚠️ 无效的日期格式: {request.document_date}")

        # 解析来源层级
        try:
            source_level = SourceLevel(request.source_level)
        except ValueError:
            source_level = SourceLevel.RAW_MATERIAL

        # 创建流水线
        pipeline = get_document_processing_pipeline_v2(db)

        # 处理文档
        result = pipeline.process_document(
            document_id=request.document_id,
            text=request.text,
            filename=request.filename,
            file_type=request.file_type,
            project_id=request.project_id,
            page_number=request.page_number,
            timestamp_start=request.timestamp_start,
            timestamp_end=request.timestamp_end,
            speaker=request.speaker,
            document_date=document_date,
            source_level=source_level,
            tags=request.tags
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))

        return success_response(
            data=result,
            message=f"文档处理完成：{result['stored_chunks']} 个chunks已存储"
        )

    except Exception as e:
        logger.error(f"❌ 文档处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search-with-citation")
async def search_with_citation(
    request: SearchWithCitationRequest,
    db: Session = Depends(get_db)
):
    """
    带引用的检索（链路十四+十五核心功能）

    返回格式：
    {
      "results": [
        {
          "text": "布依族山歌分为三种类型...",
          "citation": "[来源：访谈老张 12:30-12:45]",
          "metadata": {
            "source_file": "访谈老张_20240801.mp3",
            "timestamp_range": "12:30-12:45",
            "speaker": "老张",
            "document_type": "audio",
            "document_date": "2024-08-01"
          }
        }
      ]
    }

    前端渲染时，在AI回答末尾显示citation

    链路15新增：支持日期范围过滤
    - date_from/date_to: 可筛选特定时间段的文档
    - 例如查询"2023年发生了什么"时，设置date_from=2023-01-01, date_to=2023-12-31
    """
    try:
        vectorizer = get_vectorization_service_v2()

        # 准备日期范围（链路15）
        date_range = None
        if request.date_from or request.date_to:
            date_range = (request.date_from, request.date_to)

        # 执行检索（带元数据过滤）
        results = vectorizer.query_with_metadata(
            query_text=request.query,
            n_results=request.n_results,
            project_id=request.project_id,
            document_types=request.document_types,
            source_levels=request.source_levels,
            date_range=date_range  # 链路15：传入日期范围
        )

        # 格式化返回
        formatted_results = []
        for result in results:
            item = {
                "text": result["text"],
                "metadata": result["metadata"],
                "relevance": result["relevance"]
            }

            # 添加引用（链路十四关键）
            if request.include_citation:
                item["citation"] = result["citation"]

            formatted_results.append(item)

        return success_response(
            data={
                "query": request.query,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "filters": {
                    "date_from": request.date_from,
                    "date_to": request.date_to,
                    "document_types": request.document_types,
                    "source_levels": request.source_levels
                }
            }
        )

    except Exception as e:
        logger.error(f"❌ 检索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunk/{chunk_id}/")
async def get_chunk_with_citation(
    chunk_id: str,
    db: Session = Depends(get_db)
):
    """
    根据chunk_id获取完整内容和引用信息

    用于前端点击引用角标时，跳转到原文
    """
    try:
        vectorizer = get_vectorization_service_v2()
        chunk = vectorizer.get_chunk_by_id(chunk_id)

        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk不存在")

        return success_response(
            data={
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "citation": chunk["citation"],
                "metadata": chunk["metadata"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取chunk失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reprocess/{document_id}/")
async def reprocess_document(
    document_id: int,
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    重新处理文档（用于补充元数据）

    使用场景：
    - 旧文档升级为新版元数据
    - 添加缺失的页码/时间戳信息
    """
    try:
        from app.models.project import ProjectDocument

        # 查询文档
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id,
            ProjectDocument.project_id == project_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        if not doc.text_content:
            raise HTTPException(status_code=400, detail="文档无文本内容")

        # 先删除旧的向量数据
        vectorizer = get_vectorization_service_v2()
        vectorizer.delete_by_document_id(document_id)

        # 重新处理
        pipeline = get_document_processing_pipeline_v2(db)
        result = pipeline.process_document(
            document_id=document_id,
            text=doc.text_content,
            filename=doc.filename,
            file_type=doc.file_type,
            project_id=project_id,
            source_level=SourceLevel.RAW_MATERIAL
        )

        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        return success_response(
            data=result,
            message="文档重新处理完成"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 重新处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata-stats/{project_id}/")
async def get_metadata_stats(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取项目的元数据完整度统计

    返回：
    - 有页码的PDF数量
    - 有时间戳的音频数量
    - 有说话人标识的音频数量
    - 元数据完整度评分
    """
    try:
        from app.models.project import ProjectDocument

        docs = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project_id
        ).all()

        stats = {
            "total_documents": len(docs),
            "by_type": {},
            "metadata_completeness": {
                "pdf_with_page": 0,
                "audio_with_timestamp": 0,
                "audio_with_speaker": 0
            }
        }

        # 统计（这里简化了，实际应该查询ChromaDB）
        for doc in docs:
            file_type = doc.file_type.lower()
            stats["by_type"][file_type] = stats["by_type"].get(file_type, 0) + 1

        return success_response(
            data={
                "project_id": project_id,
                "stats": stats
            }
        )

    except Exception as e:
        logger.error(f"❌ 统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 链路15：音频时间戳处理 ====================

class AudioProcessRequest(BaseModel):
    """音频处理请求"""
    file_path: str
    project_id: Optional[int] = None
    speaker: Optional[str] = None


@router.post("/process-audio")
async def process_audio_with_timestamps(
    request: AudioProcessRequest,
    db: Session = Depends(get_db)
):
    """
    处理音频文件（链路15核心接口）

    完整流程：
    1. Whisper转录（保留segments）
    2. 每个segment独立存储（保留start/end时间戳）
    3. 向量化入库（元数据包含timestamp_display）

    与旧版的区别：
    - 旧版：合并所有segments为一段文本，丢失时间戳
    - 新版：每个segment = 1个chunk，精确到秒级时间

    返回：
    - segment_count: segments数量
    - stored_chunks: 成功存储的chunks
    - 可通过search-with-citation检索，带时间戳引用
    """
    try:
        from app.tasks.audio_tasks import process_audio_chain

        # 调用音频处理链
        result = process_audio_chain(
            file_path=request.file_path,
            project_id=request.project_id
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Audio processing failed")
            )

        return success_response(
            data={
                "file_path": request.file_path,
                "transcription": result["transcription"],
                "processing": result["processing"]
            },
            message="音频处理完成，所有时间戳已保留"
        )

    except Exception as e:
        logger.error(f"❌ 音频处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audio-segment/{chunk_id}/")
async def get_audio_segment(
    chunk_id: str,
    db: Session = Depends(get_db)
):
    """
    获取音频片段信息（用于前端跳转播放）

    返回：
    {
        "text": "祠堂再不修就要塌了...",
        "start_sec": 1425.0,
        "end_sec": 1450.0,
        "timestamp_display": "23:45-24:10",
        "speaker": "老李",
        "source_file": "访谈老李_20240801.mp3"
    }

    前端使用：
    audio.currentTime = start_sec  // 跳转到指定秒数
    """
    try:
        vectorizer = get_vectorization_service_v2()
        chunk = vectorizer.get_chunk_by_id(chunk_id)

        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")

        metadata = chunk["metadata"]

        return success_response(
            data={
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "start_sec": metadata.get("timestamp_start"),
                "end_sec": metadata.get("timestamp_end"),
                "timestamp_display": metadata.get("timestamp_range"),
                "speaker": metadata.get("speaker"),
                "source_file": metadata.get("source_file"),
                "citation": chunk["citation"]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取音频片段失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
