"""
文档处理任务
异步处理上传的文档
"""

import time
from datetime import datetime
from pathlib import Path
import os
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.core.logging import logger, log_document_processing
from app.core.database import get_db_session
from app.models.document import Document, DocumentStatus
from app.core.exceptions import DocumentNotFoundException


# 兼容旧 API 导入名：app.api.document_processing 仍引用 process_document。
process_document = None


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, document_id: str) -> Dict[str, Any]:
    """
    处理文档的主任务

    Args:
        document_id: 文档ID

    Returns:
        Dict: 处理结果
    """
    start_time = time.time()

    logger.info(f"开始处理文档: {document_id}", task_id=self.request.id)

    db = get_db_session()

    try:
        # 获取文档
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise DocumentNotFoundException(document_id)

        # 更新状态为处理中
        document.status = DocumentStatus.PROCESSING
        db.commit()

        log_document_processing(
            document_id=document_id,
            operation="process",
            status="started"
        )

        # 根据文档类型调度不同的处理任务
        result = None

        if document.type.value == "document":
            # 文档类型：提取文本、分块、生成向量
            result = process_document_content.apply_async(
                args=[document_id],
                queue='processing'
            )

        elif document.type.value == "image":
            # 图片类型：OCR、对象检测
            result = process_image_content.apply_async(
                args=[document_id],
                queue='processing'
            )

        elif document.type.value == "audio":
            # 音频类型：语音识别
            result = process_audio_content.apply_async(
                args=[document_id],
                queue='processing'
            )

        elif document.type.value == "video":
            # 视频类型：帧提取、语音识别
            result = process_video_content.apply_async(
                args=[document_id],
                queue='processing'
            )

        elif document.type.value == "table":
            # 表格类型：数据提取
            result = process_table_content.apply_async(
                args=[document_id],
                queue='processing'
            )

        duration = time.time() - start_time

        log_document_processing(
            document_id=document_id,
            operation="process",
            status="dispatched",
            duration=duration,
            details={"task_id": result.id if result else None}
        )

        return {
            "document_id": document_id,
            "status": "dispatched",
            "task_id": result.id if result else None,
            "duration": duration
        }

    except Exception as e:
        logger.error(f"文档处理失败: {e}", document_id=document_id, task_id=self.request.id)

        # 更新状态为失败
        if document:
            document.status = DocumentStatus.FAILED
            db.commit()

        log_document_processing(
            document_id=document_id,
            operation="process",
            status="failed",
            details={"error": str(e)}
        )

        # 重试
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


process_document = process_document_task


@celery_app.task(bind=True, max_retries=3)
def process_document_content(self, document_id: str) -> Dict[str, Any]:
    """
    处理文档内容（PDF, DOC, TXT等）

    流程：
    1. 下载文件
    2. 提取文本
    3. 文档分块
    4. 生成向量
    5. 存储

    Args:
        document_id: 文档ID

    Returns:
        Dict: 处理结果
    """
    start_time = time.time()

    logger.info(f"处理文档内容: {document_id}", task_id=self.request.id)

    try:
        # 使用完整的处理管线
        from app.processors.document_pipeline import DocumentPipeline
        from app.core.storage import get_storage
        from app.core.vector_store import get_vector_store

        storage = get_storage()
        vector_store = get_vector_store()

        pipeline = DocumentPipeline(
            storage=storage,
            vector_store=vector_store,
            chunk_size=500,
            chunk_overlap=50
        )

        # 执行处理
        result = pipeline.process(document_id)

        return result

    except Exception as e:
        logger.error(f"文档内容处理失败: {e}", document_id=document_id)
        raise self.retry(exc=e, countdown=60)


@celery_app.task(bind=True, max_retries=3)
def process_image_content(self, document_id: str) -> Dict[str, Any]:
    """
    处理图片内容

    流程：
    1. 下载图片
    2. OCR文字识别
    3. 对象检测
    4. 生成向量

    Args:
        document_id: 文档ID

    Returns:
        Dict: 处理结果
    """
    start_time = time.time()

    logger.info(f"处理图片内容: {document_id}", task_id=self.request.id)

    db = get_db_session()

    try:
        # 获取文档
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise DocumentNotFoundException(document_id)

        # 下载文件
        from app.core.storage import get_storage
        storage = get_storage()

        bucket, object_name = document.storage_path.split("/", 1)
        temp_dir = Path("/tmp/fieldmind/downloads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / f"{document.id}_{document.name}"

        storage.download_file(bucket, object_name, str(temp_file))

        # 处理图片
        from app.processors.image_processor import ImageProcessor
        result = ImageProcessor.process(str(temp_file))

        # 保存结果（使用文档处理管线的方式）
        from app.processors.text_chunker import TextChunker
        from app.processors.vector_generator import get_vector_generator

        if result["text"]:
            chunker = TextChunker(chunk_size=500, chunk_overlap=50)
            chunks = chunker.chunk(result["text"])

            vector_generator = get_vector_generator()
            embeddings = vector_generator.generate([c.content for c in chunks])

            # 保存到数据库
            from app.models.document_chunk import DocumentChunk
            from app.core.database import generate_id
            from app.core.vector_store import get_vector_store

            vector_store = get_vector_store()

            for i, chunk in enumerate(chunks):
                chunk_id = generate_id("chunk")
                chunk_record = DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=chunk.content,
                    sequence=chunk.sequence,
                    token_count=chunk.token_count,
                    metadata=chunk.metadata
                )
                db.add(chunk_record)

                if i < len(embeddings):
                    vector_store.insert_vector(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        embedding=embeddings[i]
                    )

        # 更新状态
        document.status = DocumentStatus.PROCESSED
        document.processed_at = datetime.utcnow()
        db.commit()

        # 清理临时文件
        os.remove(temp_file)

        duration = time.time() - start_time

        log_document_processing(
            document_id=document_id,
            operation="process_image",
            status="completed",
            duration=duration
        )

        return {
            "document_id": document_id,
            "status": "processed",
            "duration": duration
        }

    except Exception as e:
        logger.error(f"图片处理失败: {e}", document_id=document_id)
        document.status = DocumentStatus.FAILED
        db.commit()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_audio_content(self, document_id: str) -> Dict[str, Any]:
    """
    处理音频内容

    流程：
    1. 下载音频
    2. 语音识别（ASR）
    3. 文本分块
    4. 生成向量

    Args:
        document_id: 文档ID

    Returns:
        Dict: 处理结果
    """
    start_time = time.time()

    logger.info(f"处理音频内容: {document_id}", task_id=self.request.id)

    db = get_db_session()

    try:
        # 获取文档
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise DocumentNotFoundException(document_id)

        # 下载文件
        from app.core.storage import get_storage
        storage = get_storage()

        bucket, object_name = document.storage_path.split("/", 1)
        temp_dir = Path("/tmp/fieldmind/downloads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / f"{document.id}_{document.name}"

        storage.download_file(bucket, object_name, str(temp_file))

        # 处理音频
        from app.processors.audio_processor import AudioProcessor
        result = AudioProcessor.process(str(temp_file))

        # 保存结果（与图片处理相同的方式）
        from app.processors.text_chunker import TextChunker
        from app.processors.vector_generator import get_vector_generator

        if result["text"]:
            chunker = TextChunker(chunk_size=500, chunk_overlap=50)
            chunks = chunker.chunk(result["text"])

            vector_generator = get_vector_generator()
            embeddings = vector_generator.generate([c.content for c in chunks])

            # 保存到数据库
            from app.models.document_chunk import DocumentChunk
            from app.core.database import generate_id
            from app.core.vector_store import get_vector_store

            vector_store = get_vector_store()

            for i, chunk in enumerate(chunks):
                chunk_id = generate_id("chunk")
                chunk_record = DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=chunk.content,
                    sequence=chunk.sequence,
                    token_count=chunk.token_count,
                    metadata=chunk.metadata
                )
                db.add(chunk_record)

                if i < len(embeddings):
                    vector_store.insert_vector(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        embedding=embeddings[i]
                    )

        # 更新状态
        document.status = DocumentStatus.PROCESSED
        document.processed_at = datetime.utcnow()
        db.commit()

        # 清理临时文件
        os.remove(temp_file)

        duration = time.time() - start_time

        log_document_processing(
            document_id=document_id,
            operation="process_audio",
            status="completed",
            duration=duration
        )

        return {
            "document_id": document_id,
            "status": "processed",
            "duration": duration
        }

    except Exception as e:
        logger.error(f"音频处理失败: {e}", document_id=document_id)
        document.status = DocumentStatus.FAILED
        db.commit()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_video_content(self, document_id: str) -> Dict[str, Any]:
    """
    处理视频内容

    流程：
    1. 下载视频
    2. 提取音频轨道
    3. 语音识别
    4. 提取关键帧（可选）
    5. 生成向量

    Args:
        document_id: 文档ID

    Returns:
        Dict: 处理结果
    """
    start_time = time.time()

    logger.info(f"处理视频内容: {document_id}", task_id=self.request.id)

    db = get_db_session()

    try:
        # 获取文档
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise DocumentNotFoundException(document_id)

        # 下载文件
        from app.core.storage import get_storage
        storage = get_storage()

        bucket, object_name = document.storage_path.split("/", 1)
        temp_dir = Path("/tmp/fieldmind/downloads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / f"{document.id}_{document.name}"

        storage.download_file(bucket, object_name, str(temp_file))

        # 处理视频
        from app.processors.video_processor import VideoProcessor
        result = VideoProcessor.process(str(temp_file))

        # 保存结果
        from app.processors.text_chunker import TextChunker
        from app.processors.vector_generator import get_vector_generator

        if result["text"]:
            chunker = TextChunker(chunk_size=500, chunk_overlap=50)
            chunks = chunker.chunk(result["text"])

            vector_generator = get_vector_generator()
            embeddings = vector_generator.generate([c.content for c in chunks])

            # 保存到数据库
            from app.models.document_chunk import DocumentChunk
            from app.core.database import generate_id
            from app.core.vector_store import get_vector_store

            vector_store = get_vector_store()

            for i, chunk in enumerate(chunks):
                chunk_id = generate_id("chunk")
                chunk_record = DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=chunk.content,
                    sequence=chunk.sequence,
                    token_count=chunk.token_count,
                    metadata=chunk.metadata
                )
                db.add(chunk_record)

                if i < len(embeddings):
                    vector_store.insert_vector(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        embedding=embeddings[i]
                    )

        # 更新状态
        document.status = DocumentStatus.PROCESSED
        document.processed_at = datetime.utcnow()
        db.commit()

        # 清理临时文件
        os.remove(temp_file)

        duration = time.time() - start_time

        log_document_processing(
            document_id=document_id,
            operation="process_video",
            status="completed",
            duration=duration
        )

        return {
            "document_id": document_id,
            "status": "processed",
            "duration": duration
        }

    except Exception as e:
        logger.error(f"视频处理失败: {e}", document_id=document_id)
        document.status = DocumentStatus.FAILED
        db.commit()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=3)
def process_table_content(self, document_id: str) -> Dict[str, Any]:
    """
    处理表格内容

    流程：
    1. 下载表格文件
    2. 解析表格数据
    3. 数据结构化
    4. 生成向量

    Args:
        document_id: 文档ID

    Returns:
        Dict: 处理结果
    """
    start_time = time.time()

    logger.info(f"处理表格内容: {document_id}", task_id=self.request.id)

    db = get_db_session()

    try:
        # 获取文档
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            raise DocumentNotFoundException(document_id)

        # 下载文件
        from app.core.storage import get_storage
        storage = get_storage()

        bucket, object_name = document.storage_path.split("/", 1)
        temp_dir = Path("/tmp/fieldmind/downloads")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_dir / f"{document.id}_{document.name}"

        storage.download_file(bucket, object_name, str(temp_file))

        # 处理表格
        from app.processors.table_processor import TableProcessor
        result = TableProcessor.process(str(temp_file), document.mime_type)

        # 保存结果
        from app.processors.text_chunker import TextChunker
        from app.processors.vector_generator import get_vector_generator

        if result["text"]:
            chunker = TextChunker(chunk_size=500, chunk_overlap=50)
            chunks = chunker.chunk(result["text"])

            vector_generator = get_vector_generator()
            embeddings = vector_generator.generate([c.content for c in chunks])

            # 保存到数据库
            from app.models.document_chunk import DocumentChunk
            from app.core.database import generate_id
            from app.core.vector_store import get_vector_store

            vector_store = get_vector_store()

            for i, chunk in enumerate(chunks):
                chunk_id = generate_id("chunk")
                chunk_record = DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    content=chunk.content,
                    sequence=chunk.sequence,
                    token_count=chunk.token_count,
                    metadata=chunk.metadata
                )
                db.add(chunk_record)

                if i < len(embeddings):
                    vector_store.insert_vector(
                        document_id=document_id,
                        chunk_id=chunk_id,
                        embedding=embeddings[i]
                    )

        # 更新状态
        document.status = DocumentStatus.PROCESSED
        document.processed_at = datetime.utcnow()
        db.commit()

        # 清理临时文件
        os.remove(temp_file)

        duration = time.time() - start_time

        log_document_processing(
            document_id=document_id,
            operation="process_table",
            status="completed",
            duration=duration
        )

        return {
            "document_id": document_id,
            "status": "processed",
            "duration": duration
        }

    except Exception as e:
        logger.error(f"表格处理失败: {e}", document_id=document_id)
        document.status = DocumentStatus.FAILED
        db.commit()
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(bind=True)
def cleanup_failed_tasks(self):
    """
    清理失败的任务

    定期任务，清理超过N天的失败文档
    """
    from datetime import timedelta

    logger.info("开始清理失败任务", task_id=self.request.id)

    db = get_db_session()

    try:
        # 查找7天前失败的文档
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        failed_docs = db.query(Document).filter(
            Document.status == DocumentStatus.FAILED,
            Document.updated_at < cutoff_date
        ).all()

        logger.info(f"找到 {len(failed_docs)} 个失败文档需要清理")

        # 这里可以选择删除或标记
        # 暂时只记录日志
        for doc in failed_docs:
            logger.info(f"失败文档: {doc.id}, 更新时间: {doc.updated_at}")

        return {
            "cleaned": len(failed_docs),
            "status": "completed"
        }

    finally:
        db.close()
