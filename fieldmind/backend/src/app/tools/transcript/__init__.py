"""音频/视频转录工具兼容入口。"""

from typing import Any, Dict


def transcribe_audio(file_path: str, **kwargs) -> Dict[str, Any]:
    """调用统一转录服务并保留时间戳。"""
    from app.core.transcription import transcription_service

    result = transcription_service.transcribe(
        file_path,
        language=kwargs.get("language", "zh"),
    )
    text = result.get("text", "")
    segments = result.get("segments", [])
    return {
        "transcript": {
            "full_text": text,
            "raw_text": text,
            "segments": segments,
            "language": result.get("language", "zh"),
        },
        "total": {
            "时长": max((segment.get("end", 0) for segment in segments), default=0),
            "清洗后字数": len(text),
        },
        "source": "TranscriptionService",
    }


def clean_transcript(text: str) -> str:
    return " ".join((text or "").split())


def extract_metrics(text: str) -> Dict[str, Any]:
    cleaned = clean_transcript(text)
    return {"characters": len(cleaned), "words": len(cleaned.split())}


__all__ = ["transcribe_audio", "clean_transcript", "extract_metrics"]
