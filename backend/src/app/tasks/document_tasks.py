"""
Celery 异步任务 - 文档处理流水线
完整的工作流：上传 → 处理 → 存储 → 通知
"""

from celery import Celery
from sqlalchemy.orm import Session
import os
import json
from pathlib import Path

from app.core.database import SessionLocal
from app.models.project import ProjectDocument, Project
from app.tools.document import UnifiedDocumentConverter
from app.services.video_processor import VideoProcessor
from app.config import settings

# Celery 配置
celery_app = Celery(
    'fieldmind',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

# 配置选项
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
)

# 服务实例
document_converter = UnifiedDocumentConverter()
video_processor = VideoProcessor()


@celery_app.task(name='tasks.process_document', bind=True)
def process_document(self, document_id: int):
    """
    异步处理文档的完整流水线
    清洗 → 切分 → 向量化 → 入库

    处理步骤：
    1. 根据文件类型提取内容
    2. 数据清洗（去除噪音）
    3. 文档切分（200-500字语义块）
    4. 向量化（Sentence-BERT）
    5. 入库索引（存储+建立索引）
    """
    db = SessionLocal()

    try:
        from app.tools.document import UnifiedDocumentPipeline

        doc = db.query(ProjectDocument).filter(ProjectDocument.id == document_id).first()
        if not doc:
            return {"error": "Document not found", "document_id": document_id}

        # 更新状态为处理中
        doc.status = "processing"
        doc.processing_progress = 0
        db.commit()

        # 创建处理流水线
        pipeline = UnifiedDocumentPipeline()

        # 定义进度回调
        def progress_callback(stage, progress, message):
            """更新任务进度"""
            self.update_state(
                state='PROCESSING',
                meta={
                    'stage': stage,
                    'progress': progress,
                    'message': message,
                    'document_id': document_id
                }
            )

            # 更新数据库中的进度
            doc.processing_progress = int(progress * 100)
            db.commit()

        # 执行完整流水线
        result = pipeline.process_document(
            document_id=document_id,
            file_path=doc.file_path,
            project_id=doc.project_id,
            db=db,
            progress_callback=progress_callback
        )

        # 更新项目统计
        update_project_stats(doc.project_id, db)

        return result

    except Exception as e:
        if doc:
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()

        logger.error(f"文档处理失败: {e}", exc_info=True)
        return {"success": False, "error": str(e), "document_id": document_id}
    finally:
        db.close()


def process_video(file_path: str, document_id: int):
    """处理视频文件：提取音频 → 转录"""
    try:
        # 提取音频
        audio_path = video_processor.extract_audio(file_path)

        # 转录（如果有Whisper服务）
        try:
            from app.core.transcription import transcription_service
            result = transcription_service.transcribe(audio_path)
            text = result.get('text', '')
            segments = result.get('segments', [])
        except Exception as e:
            print(f"转录失败: {e}")
            text = ""
            segments = []

        # 清理临时音频文件
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return text, segments
    except Exception as e:
        print(f"处理视频失败: {e}")
        return "", []


def process_audio(file_path: str, document_id: int):
    """处理音频文件：直接转录"""
    try:
        from app.core.transcription import transcription_service
        result = transcription_service.transcribe(file_path)
        text = result.get('text', '')
        segments = result.get('segments', [])
        return text, segments
    except Exception as e:
        print(f"处理音频失败: {e}")
        return "", []


def process_document_file(file_path: str):
    """处理文档文件：转换为文本"""
    try:
        result = document_converter.convert_file(file_path)
        return result.get('text_content', '') if result else None
    except Exception as e:
        print(f"处理文档失败: {e}")
        return None


def save_transcript(document_id: int, transcript: list):
    """保存转录文本到文件"""
    try:
        transcript_dir = Path(settings.UPLOAD_DIR) / "transcripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)

        transcript_file = transcript_dir / f"doc_{document_id}.json"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存转录文件失败: {e}")


def extract_keywords(text: str, top_n: int = 20):
    """提取关键词（简单版，使用jieba）"""
    try:
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=False)
        return keywords
    except Exception as e:
        print(f"提取关键词失败: {e}")
        return []


def update_project_stats(project_id: int, db: Session):
    """更新项目统计信息"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            # 统计文档数量
            doc_count = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id
            ).count()

            # 统计完成的文档数量
            completed_count = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id,
                ProjectDocument.status == "completed"
            ).count()

            # 统计总字数
            total_words = db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project_id
            ).with_entities(
                db.func.sum(ProjectDocument.word_count)
            ).scalar() or 0

            project.document_count = doc_count
            project.total_words = int(total_words)

            db.commit()
    except Exception as e:
        print(f"更新项目统计失败: {e}")


@celery_app.task(name='tasks.batch_process_documents')
def batch_process_documents(document_ids: list):
    """批量处理文档"""
    results = []
    for doc_id in document_ids:
        result = process_document(doc_id)
        results.append(result)
    return results

