"""
统一的语音转录服务
根据配置自动选择 Whisper 或 FunASR
"""

import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class UnifiedTranscriptionService:
    """统一的语音转录服务"""

    def __init__(self):
        self.engine = settings.ASR_ENGINE
        self.service = None

    def _get_service(self):
        """获取实际的转录服务"""
        if self.service is not None:
            return self.service

        if self.engine == "funasr":
            logger.info("使用 FunASR 引擎")
            from app.core.funasr_service import funasr_service
            self.service = funasr_service
        elif self.engine == "whisper":
            logger.info("使用 Whisper 引擎")
            from app.core.transcription import transcription_service
            self.service = transcription_service
        else:
            logger.warning(f"未知的ASR引擎: {self.engine}，回退到Whisper")
            from app.core.transcription import transcription_service
            self.service = transcription_service

        return self.service

    def transcribe(
        self,
        audio_path: str,
        language: str = "zh",
        **kwargs
    ) -> Dict[str, Any]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh=中文, en=英文)
            **kwargs: 引擎特定参数

        Returns:
            标准化的转录结果:
            {
                "text": str,           # 完整文本
                "language": str,       # 语言
                "segments": [          # 分段
                    {
                        "id": int,
                        "text": str,
                        "start": float,  # 秒
                        "end": float,    # 秒
                        "speaker": str|None
                    }
                ]
            }
        """
        service = self._get_service()

        # FunASR特有参数：热词
        if self.engine == "funasr" and settings.FUNASR_HOTWORDS:
            kwargs['hotwords'] = settings.FUNASR_HOTWORDS

        return service.transcribe(audio_path, language=language, **kwargs)

    def transcribe_with_diarization(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        带说话人分离的转录

        Args:
            audio_path: 音频文件路径
            num_speakers: 说话人数量（可选）

        Returns:
            转录结果 + 说话人标记
        """
        service = self._get_service()

        if hasattr(service, 'transcribe_with_speaker_diarization'):
            return service.transcribe_with_speaker_diarization(audio_path, num_speakers)
        elif hasattr(service, 'transcribe_with_diarization'):
            return service.transcribe_with_diarization(audio_path, num_speakers)
        else:
            logger.warning(f"{self.engine} 不支持说话人分离，返回基础转录")
            return service.transcribe(audio_path)

    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """获取音频文件信息"""
        service = self._get_service()
        return service.get_audio_info(audio_path)


# 全局实例
transcription = UnifiedTranscriptionService()
