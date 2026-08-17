"""
音频处理任务 - Whisper 转录 + HanLP 处理
"""
from celery import chain
from app.celery_app import celery_app
from typing import Dict, Any
import subprocess
import os
from pathlib import Path
from datetime import datetime
import json


@celery_app.task(name="app.tasks.audio_tasks.extract_audio_metadata")
def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """
    提取音频元数据（使用 ffprobe）
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)

        format_info = metadata.get("format", {})
        streams = metadata.get("streams", [])
        audio_stream = next((s for s in streams if s["codec_type"] == "audio"), {})

        return {
            "success": True,
            "file_path": file_path,
            "duration": float(format_info.get("duration", 0)),
            "size": int(format_info.get("size", 0)),
            "codec": audio_stream.get("codec_name", "unknown"),
            "sample_rate": int(audio_stream.get("sample_rate", 0)),
            "channels": int(audio_stream.get("channels", 0)),
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Metadata extraction failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.audio_tasks.transcribe_audio", rate_limit="5/m")
def transcribe_audio(file_path: str) -> Dict[str, Any]:
    """
    使用 Whisper 转录音频
    支持本地模型（零成本）或 OpenAI API
    """
    try:
        # 检查使用本地还是 API
        use_local = os.getenv("WHISPER_USE_LOCAL", "true").lower() == "true"

        if use_local:
            # 本地 Whisper
            import whisper
            model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
            model = whisper.load_model(model_size)

            # 转录
            result = model.transcribe(
                file_path,
                language="zh",  # 默认中文，可自动检测
                task="transcribe",
                verbose=False,
            )

            transcription = result["text"]
            language = result["language"]
            segments = result.get("segments", [])

        else:
            # OpenAI Whisper API
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")

            with open(file_path, "rb") as audio_file:
                result = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language="zh"
                )

            transcription = result["text"]
            language = "zh"
            segments = []

        return {
            "success": True,
            "file_path": file_path,
            "transcription": transcription,
            "language": language,
            "segments": segments,
            "word_count": len(transcription),
            "transcribed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Transcription failed: {str(e)}",
        }


@celery_app.task(name="app.tasks.audio_tasks.process_audio_chain")
def process_audio_chain(file_path: str, project_id: int = None) -> Dict[str, Any]:
    """
    完整音频处理链（链路15重写版）：
    1. 提取元数据
    2. Whisper 转录（保留segments）
    3. 以segment为单位分块入库（保留时间戳）

    ⚠️ 核心改动：不再合并segments为纯文本，每个segment独立存储
    """
    from app.services.audio_chunker import get_audio_chunker
    from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend
    from app.schemas.document_metadata import DocumentMetadata, DocumentType, SourceLevel

    # 步骤 1: 提取元数据
    metadata = extract_audio_metadata(file_path)

    # 步骤 2: 转录
    transcription_result = transcribe_audio(file_path)

    if not transcription_result.get("success"):
        return {
            "success": False,
            "error": "Transcription failed",
            "details": transcription_result,
        }

    # ========== 关键改动：使用segments而非合并文本 ==========
    segments = transcription_result.get("segments", [])

    if not segments:
        # 如果没有segments（可能是API模式），回退到纯文本
        return {
            "success": False,
            "error": "No segments available - please use local Whisper model",
            "details": "API mode does not return segments with timestamps"
        }

    # 步骤 3: 创建文档元数据
    filename = Path(file_path).stem
    document_id = abs(hash(file_path)) % 1000000  # 生成临时ID

    document_metadata = DocumentMetadata(
        document_id=document_id,
        source_file=filename + Path(file_path).suffix,
        document_type=DocumentType.AUDIO,
        source_level=SourceLevel.RAW_MATERIAL,
        project_id=project_id,
        language=transcription_result.get("language", "zh"),
        custom_fields={
            "duration": metadata.get("duration", 0),
            "codec": metadata.get("codec", "unknown")
        }
    )

    # 步骤 4: 使用AudioChunker分块（保留时间戳）
    audio_chunker = get_audio_chunker()
    chunks = audio_chunker.chunk_audio_segments(segments, document_metadata)

    logger.info(f"✅ 音频分块完成: {len(chunks)} segments")

    # 步骤 5: 向量化并存储
    vectorizer = get_vectorization_service_v2()
    vectorization_result = vectorizer.vectorize_chunks(chunks)

    return {
        "success": True,
        "file_path": file_path,
        "audio_metadata": metadata,
        "transcription": {
            "full_text": transcription_result["transcription"],
            "language": transcription_result["language"],
            "segment_count": len(segments),
            "word_count": transcription_result["word_count"]
        },
        "processing": {
            "total_chunks": len(chunks),
            "stored_chunks": vectorization_result.get("stored_count", 0),
            "failed_chunks": vectorization_result.get("failed_count", 0)
        },
        "completed_at": datetime.utcnow().isoformat(),
    }
