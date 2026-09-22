"""
后台任务处理器（重构版）
将超长复杂函数拆分为职责单一的模块
"""

from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session
import os
import json
from pathlib import Path
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

from app.core.database import SessionLocal
from app.models.project import (
    ProjectDocument,
    Project,
    ProjectDocumentAsset,
    ProjectDocumentTag,
)
from app.config import settings

logger = logging.getLogger(__name__)

# 线程池
executor = ThreadPoolExecutor(max_workers=2)
_task_lock = threading.Lock()
_active_tasks = {}

_document_converter = None
_video_processor = None


def _get_document_converter():
    global _document_converter
    if _document_converter is None:
        from app.services.document_converter import DocumentConverter

        _document_converter = DocumentConverter()
    return _document_converter


def _get_video_processor():
    global _video_processor
    if _video_processor is None:
        from app.services.video_processor import VideoProcessor

        _video_processor = VideoProcessor()
    return _video_processor


# ===== 链路追踪 =====
import time


def trace_step(step_name: str, document_id: int, details: str = ""):
    """链路追踪日志"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[TRACE][Doc {document_id}] {step_name}"
    if details:
        log_msg += f" | {details}"
    log_msg += f" | {timestamp}"
    logger.info(log_msg)


# ===== 文档处理步骤拆分 =====


class DocumentProcessor:
    """文档处理器 - 封装所有处理逻辑"""

    def __init__(self, db: Session, document_id: int):
        self.db = db
        self.document_id = document_id
        self.doc: Optional[ProjectDocument] = None
        self.content: Optional[str] = None
        self.transcript: Optional[list] = None
        self.extraction_info: Dict[str, Any] = {}
        self.sources: list = []

    def load_document(self) -> bool:
        """加载文档"""
        trace_step("0. 任务启动", self.document_id, "后台线程开始执行")

        self.doc = (
            self.db.query(ProjectDocument)
            .filter(ProjectDocument.id == self.document_id)
            .first()
        )

        if not self.doc:
            logger.error(f"文档 {self.document_id} 不存在")
            return False

        trace_step(
            "1. 入站登记",
            self.document_id,
            f"文件类型={self.doc.file_type}, 大小={self.doc.file_size}字节",
        )
        return True

    def update_status(self, status: str, error_message: str = None):
        """更新文档状态"""
        self.doc.status = status
        if error_message:
            self.doc.error_message = error_message
        self.db.commit()

        notify_frontend(
            self.doc.project_id,
            self.document_id,
            status,
            {"step": status, "message": error_message or f"状态更新: {status}"},
        )

    def extract_content(self) -> bool:
        """提取文档内容"""
        trace_step("2. 内容萃取", self.document_id, f"文件类型={self.doc.file_type}")

        try:
            from app.agents.ingestion_agent import get_ingestion_agent

            ingestion_agent = get_ingestion_agent()
            ingestion_result = ingestion_agent.ingest_file(
                file_path=self.doc.file_path,
                filename=self.doc.original_filename,
                mime_type=self.doc.mime_type or "application/octet-stream",
                file_metadata={
                    "id": self.document_id,
                    "project_id": self.doc.project_id,
                },
            )

            self.content = ingestion_result.get("raw_text") or None
            self.transcript = ingestion_result.get("transcript") or None
            self.extraction_info = ingestion_result.get("extraction_info", {})
            extraction_metadata = ingestion_result.get("structured_metadata", {})
            self.sources = ingestion_result.get("sources") or []

            # 保存提取元数据
            self._save_extraction_metadata(extraction_metadata)

            trace_step(
                "2. 内容萃取完成",
                self.document_id,
                f"插件={self.extraction_info.get('plugin')}, "
                f"文本长度={len(self.content) if self.content else 0}, "
                f"sources数={len(self.sources)}",
            )

            return self._validate_extraction()

        except Exception as e:
            logger.error(f"内容提取失败: {e}", exc_info=True)
            self._handle_extraction_error(str(e))
            return False

    def _save_extraction_metadata(self, extraction_metadata: dict):
        """保存提取元数据"""
        _upsert_asset(
            self.db,
            document_id=self.document_id,
            asset_type="extraction_metadata",
            content=json.dumps(
                {
                    "file_type": self.extraction_info.get("file_type"),
                    "structured_metadata": extraction_metadata,
                    "extraction_info": self.extraction_info,
                    "sources_count": len(self.sources),
                },
                ensure_ascii=False,
                default=str,
            ),
            metadata={
                "plugin": self.extraction_info.get("plugin"),
                "method": self.extraction_info.get("method"),
                "status": self.extraction_info.get("status"),
                "has_sources": len(self.sources) > 0,
            },
            status=self.extraction_info.get("status", "completed"),
        )
        self.db.commit()

    def _validate_extraction(self) -> bool:
        """验证提取结果"""
        extraction_status = self.extraction_info.get("status")

        if not self.content:
            error_msg = self.extraction_info.get("error") or "未提取到可分析文本"

            self.doc.extra_data = {
                **dict(self.doc.extra_data or {}),
                "extraction_status": extraction_status or "empty",
                "extraction_error": error_msg,
            }

            if extraction_status == "failed":
                self.update_status("failed", error_msg)
            else:
                self.update_status(
                    "review_needed", "未提取到可分析文本，需要检查解析插件或文件内容"
                )

            return False

        return True

    def _handle_extraction_error(self, error: str):
        """处理提取错误"""
        extraction_info = {
            "plugin": "IngestionAgent",
            "method": "failed",
            "status": "failed",
            "error": error,
        }
        _upsert_asset(
            self.db,
            document_id=self.document_id,
            asset_type="extraction_metadata",
            content=json.dumps(extraction_info, ensure_ascii=False),
            metadata=extraction_info,
            status="failed",
        )
        self.db.commit()

    def save_content(self):
        """保存提取的内容"""
        if not self.content:
            return

        # 更新文档信息
        extra_data = dict(self.doc.extra_data or {})
        extra_data["extraction_status"] = "success"
        extra_data["extraction_method"] = self.extraction_info.get("method")
        extra_data.pop("extraction_error", None)

        self.doc.extra_data = extra_data
        self.doc.error_message = None
        self.doc.text_content = self.content

        # 统计字数
        from app.services.text_stats import count_words

        self.doc.word_count = count_words(self.content)

        # 保存为 asset
        _upsert_asset(
            self.db,
            document_id=self.document_id,
            asset_type="extracted_text",
            content=self.content,
            metadata={"word_count": self.doc.word_count, "source": "background_tasks"},
        )
        self.db.commit()

        logger.info(f"文档 {self.document_id} 提取了 {self.doc.word_count} 个词")

        notify_frontend(
            self.doc.project_id,
            self.document_id,
            "processing",
            {
                "step": "content_extracted",
                "message": f"提取了{len(self.content)}字符",
                "word_count": self.doc.word_count,
                "char_count": len(self.content),
            },
        )

        # 新增：自动触发文本切分和量化
        try:
            self.chunk_and_quantify()
        except Exception as e:
            logger.error(f"文档 {self.document_id} 切分和量化失败: {e}", exc_info=True)

    def save_transcript(self):
        """保存转写文本"""
        if not self.transcript:
            return

        transcript_path = save_transcript(self.document_id, self.transcript)

        extra_data = dict(self.doc.extra_data or {})
        extra_data["has_transcript"] = True
        extra_data["transcript"] = self.transcript
        self.doc.extra_data = extra_data

        _upsert_asset(
            self.db,
            document_id=self.document_id,
            asset_type="transcript",
            content=json.dumps(self.transcript, ensure_ascii=False),
            storage_path=str(transcript_path) if transcript_path else None,
            metadata={"segments": len(self.transcript)},
        )
        self.db.commit()

        logger.info(
            f"文档 {self.document_id} 保存了转写文本，segments={len(self.transcript)}"
        )

    def extract_keywords(self):
        """提取关键词"""
        if not self.content:
            return

        trace_step("3. 关键词提取", self.document_id, "开始jieba分词")

        keywords = extract_keywords(self.content)

        extra_data = dict(self.doc.extra_data or {})
        extra_data["keywords"] = keywords[:50]
        self.doc.extra_data = extra_data

        _sync_tags_from_keywords(self.db, self.doc, keywords[:20])
        self.db.commit()

        logger.info(f"文档 {self.document_id} 提取了 {len(keywords)} 个关键词")
        trace_step(
            "3. 关键词提取完成", self.document_id, f"提取{len(keywords)}个关键词"
        )

        notify_frontend(
            self.doc.project_id,
            self.document_id,
            "processing",
            {
                "step": "keywords_extracted",
                "message": f"提取了{len(keywords)}个关键词",
                "keywords_count": len(keywords),
            },
        )

    def run_deep_processing(self):
        """运行深度处理流程"""
        if not self.content:
            return

        trace_step("4. 深度处理", self.document_id, "调用完整Pipeline")

        try:
            from app.services.document_processing_pipeline_complete import (
                DocumentProcessingPipelineComplete,
            )

            pipeline = DocumentProcessingPipelineComplete(self.db)
            pipeline_result = pipeline.process_document(
                document_id=self.document_id,
                content=self.content,
                project_id=self.doc.project_id,
                metadata={
                    "filename": self.doc.original_filename,
                    "file_type": self.doc.file_type,
                    "transcript": (
                        self.doc.extra_data.get("transcript")
                        if self.doc.extra_data
                        else None
                    ),
                },
            )

            # 保存深度处理结果
            self._save_pipeline_results(pipeline_result)

            trace_step(
                "4. 深度处理完成",
                self.document_id,
                f"状态={pipeline_result.get('status')}",
            )

        except Exception as e:
            logger.error(f"深度处理失败: {e}", exc_info=True)
            trace_step("4. 深度处理失败", self.document_id, f"错误={str(e)}")

    def chunk_and_quantify(self):
        """
        文本切分和量化
        新增方法：集成 chunking_service 和 text_quantification_service
        """
        if not self.content:
            logger.warning(f"文档 {self.document_id} 没有内容，跳过切分")
            return

        try:
            # 1. 文本切分
            from app.services.chunking_service import chunking_service

            notify_frontend(
                self.doc.project_id,
                self.document_id,
                "processing",
                {
                    "step": "chunking",
                    "message": "正在切分文本...",
                },
            )

            chunk_count = chunking_service.create_chunks_from_document(
                db=self.db,
                document_id=self.document_id,
                text=self.content,
                project_id=self.doc.project_id
            )

            logger.info(f"文档 {self.document_id} 创建了 {chunk_count} 个 chunks")

            # 2. 文本量化
            from app.services.text_quantification import text_quantification_service

            notify_frontend(
                self.doc.project_id,
                self.document_id,
                "processing",
                {
                    "step": "quantification",
                    "message": "正在计算量化指标...",
                },
            )

            quantified_count = text_quantification_service.quantify_and_update_chunks(
                db=self.db,
                document_id=self.document_id
            )

            logger.info(f"文档 {self.document_id} 的 {quantified_count} 个 chunks 已量化")

            # 3. 更新文档状态
            extra_data = dict(self.doc.extra_data or {})
            extra_data["chunking_completed"] = True
            extra_data["chunks_count"] = chunk_count
            extra_data["quantification_completed"] = True
            self.doc.extra_data = extra_data
            self.db.commit()

            notify_frontend(
                self.doc.project_id,
                self.document_id,
                "processing",
                {
                    "step": "chunking_quantification_completed",
                    "message": f"切分和量化完成（{chunk_count} 个 chunks）",
                    "chunks_count": chunk_count,
                },
            )

        except Exception as e:
            logger.error(f"文档 {self.document_id} 切分和量化失败: {e}", exc_info=True)
            notify_frontend(
                self.doc.project_id,
                self.document_id,
                "error",
                {
                    "step": "chunking_quantification_failed",
                    "message": f"切分和量化失败: {str(e)}",
                },
            )

    def _save_pipeline_results(self, pipeline_result: dict):
        """保存深度处理结果"""
        extra_data = dict(self.doc.extra_data or {})
        extra_data["pipeline_completed"] = True
        extra_data["pipeline_status"] = pipeline_result.get("status")

        if pipeline_result.get("chunks"):
            extra_data["chunks_count"] = len(pipeline_result["chunks"])

        self.doc.extra_data = extra_data
        self.db.commit()

        notify_frontend(
            self.doc.project_id,
            self.document_id,
            "processing",
            {
                "step": "pipeline_completed",
                "message": "深度处理完成",
                "status": pipeline_result.get("status"),
            },
        )

    def generate_summary(self):
        """生成文档缩影（新增步骤）"""
        if not self.content:
            logger.warning(f"文档 {self.document_id} 没有内容，跳过缩影生成")
            return

        trace_step("5. 缩影生成", self.document_id, "基于现有数据生成知识缩影")

        try:
            from app.services.summary_generator import FileSummaryGenerator, save_summary

            notify_frontend(
                self.doc.project_id,
                self.document_id,
                "processing",
                {
                    "step": "summary_generation",
                    "message": "正在生成文档缩影...",
                },
            )

            # 生成缩影
            generator = FileSummaryGenerator(self.db)
            summary_data = generator.generate_summary(self.document_id)

            # 保存到数据库
            save_summary(self.db, summary_data)

            trace_step(
                "5. 缩影生成完成",
                self.document_id,
                f"摘要={summary_data['one_line_summary'][:50]}..."
            )

            notify_frontend(
                self.doc.project_id,
                self.document_id,
                "processing",
                {
                    "step": "summary_generated",
                    "message": "文档缩影已生成",
                    "summary": summary_data['one_line_summary']
                },
            )

        except Exception as e:
            logger.error(f"缩影生成失败: {e}", exc_info=True)
            trace_step("5. 缩影生成失败", self.document_id, f"错误={str(e)}")

            # 缩影生成失败不阻断整个流程，继续完成文档处理
            notify_frontend(
                self.doc.project_id,
                self.document_id,
                "processing",
                {
                    "step": "summary_generation_failed",
                    "message": f"缩影生成失败: {str(e)}",
                },
            )

    def finalize(self):
        """完成处理"""
        self.doc.status = "completed"
        self.doc.error_message = None
        self.db.commit()

        trace_step("9. 完成", self.document_id, "文档处理完毕")

        notify_frontend(
            self.doc.project_id,
            self.document_id,
            "completed",
            {
                "step": "completed",
                "message": "文档处理完成",
                "word_count": self.doc.word_count,
            },
        )

        logger.info(f"✅ 文档 {self.document_id} 处理完成")


# ===== 主入口函数（重构后）=====


def process_document_async(document_id: int):
    """
    在后台线程中处理文档（集成统一管道协调器版本）

    新架构：
    1. 前期处理（内容提取、保存）仍使用 DocumentProcessor
    2. 知识处理（九步流水线、缩影生成）使用 UnifiedPipelineCoordinator
    3. 实现完整的数据流：脏数据 → 契约验证 → 知识流水线 → 事件发布 → 缩影生成
    """
    db = SessionLocal()
    processor = DocumentProcessor(db, document_id)

    try:
        # ========== 第一阶段：内容提取和基础处理 ==========

        # 步骤 1: 加载文档
        if not processor.load_document():
            return

        # 步骤 2: 更新状态为处理中
        processor.update_status("processing")

        # 步骤 3: 提取内容（脏数据通道）
        if not processor.extract_content():
            return

        # 步骤 4: 保存内容
        processor.save_content()

        # 步骤 5: 保存转写（如果有）
        processor.save_transcript()

        # 步骤 6: 提取关键词
        processor.extract_keywords()

        trace_step(
            "7. 前期处理完成",
            document_id,
            "内容提取完成，准备进入统一管道"
        )

        # ========== 第二阶段：统一管道协调器处理 ==========
        # 包含：数据契约验证 → 九步知识流水线 → 事件发布 → 自动缩影生成

        trace_step(
            "8. 启动统一管道协调器",
            document_id,
            "契约验证 → 知识流水线 → 事件总线"
        )

        from app.services.unified_pipeline_coordinator import UnifiedPipelineCoordinator

        coordinator = UnifiedPipelineCoordinator(db)
        unified_result = coordinator.process_document(document_id)

        if unified_result['success']:
            logger.info(
                f"✅ 统一管道处理成功 - 文档 {document_id}, "
                f"耗时 {unified_result['elapsed_time']}秒"
            )

            trace_step(
                "8. 统一管道完成",
                document_id,
                f"状态=成功, 耗时={unified_result['elapsed_time']}秒"
            )

            # 保存统一管道的执行结果
            processor.doc.extra_data = processor.doc.extra_data or {}
            processor.doc.extra_data['unified_pipeline'] = {
                'status': 'completed',
                'elapsed_time': unified_result['elapsed_time'],
                'stages': unified_result['stages'],
                'completed_at': datetime.utcnow().isoformat()
            }
            db.commit()

            notify_frontend(
                processor.doc.project_id,
                document_id,
                "processing",
                {
                    "step": "unified_pipeline_completed",
                    "message": "统一管道处理完成（包含九步流水线和缩影生成）",
                    "elapsed_time": unified_result['elapsed_time']
                },
            )

        else:
            # 统一管道失败，记录详细错误
            error_msg = unified_result.get('error', '未知错误')
            failed_stage = unified_result.get('stage', 'unknown')

            logger.error(
                f"❌ 统一管道处理失败 - 文档 {document_id}, "
                f"失败阶段: {failed_stage}, 错误: {error_msg}"
            )

            trace_step(
                "8. 统一管道失败",
                document_id,
                f"阶段={failed_stage}, 错误={error_msg}"
            )

            # 保存失败信息
            processor.doc.extra_data = processor.doc.extra_data or {}
            processor.doc.extra_data['unified_pipeline'] = {
                'status': 'failed',
                'failed_stage': failed_stage,
                'error': error_msg,
                'failed_at': datetime.utcnow().isoformat()
            }
            db.commit()

            notify_frontend(
                processor.doc.project_id,
                document_id,
                "error",
                {
                    "step": "unified_pipeline_failed",
                    "message": f"统一管道失败: {error_msg}",
                    "failed_stage": failed_stage
                },
            )

            # 注意：统一管道失败不应该终止整个文档处理
            # 文档基本信息已保存，只是知识提取部分失败
            logger.warning(
                f"⚠️ 文档 {document_id} 基础处理完成，但知识流水线失败，"
                f"文档仍标记为 completed（可后续重试知识提取）"
            )

        # ========== 第三阶段：完成处理 ==========

        # 步骤 9: 完成
        processor.finalize()

    except Exception as e:
        logger.error(f"文档处理失败: {e}", exc_info=True)
        trace_step("ERROR", document_id, f"致命错误: {str(e)}")

        if processor.doc:
            processor.update_status("failed", str(e))

    finally:
        db.close()


# ===== 辅助函数（保持不变）=====


def notify_frontend(project_id: int, document_id: int, status: str, data: dict):
    """通知前端（占位符）"""
    # TODO: 实现 WebSocket 推送
    pass


def extract_keywords(content: str) -> list:
    """提取关键词（占位符）"""
    # TODO: 实现关键词提取
    return []


def _sync_tags_from_keywords(db: Session, doc: ProjectDocument, keywords: list):
    """同步关键词到标签（占位符）"""
    pass


def _upsert_asset(
    db: Session,
    document_id: int,
    asset_type: str,
    content: str,
    metadata: dict = None,
    storage_path: str = None,
    status: str = "completed",
):
    """插入或更新 Asset（占位符）"""
    pass


def save_transcript(document_id: int, transcript: list) -> Path:
    """保存转写文本（占位符）"""
    return None


# ===== 保持原有的提交任务接口 =====


def submit_document_task(document_id: int) -> str:
    """提交文档处理任务"""
    task_id = f"doc_{document_id}_{int(time.time())}"

    with _task_lock:
        _active_tasks[task_id] = {
            "document_id": document_id,
            "status": "pending",
            "submitted_at": datetime.now(),
        }

    executor.submit(process_document_async, document_id)
    logger.info(f"✅ 文档处理任务已提交: task_id={task_id}, document_id={document_id}")
    return task_id


def submit_task(task_func, *args, **kwargs):
    """
    提交通用后台任务

    Args:
        task_func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        Future 对象
    """
    return executor.submit(task_func, *args, **kwargs)

    logger.info(f"已提交文档处理任务: {task_id}")
    return task_id
