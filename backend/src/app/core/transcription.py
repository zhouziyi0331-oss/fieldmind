"""
语音转录服务
基于OpenAI Whisper
"""

import whisper
import torch
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import ssl
import certifi

from app.config import settings

# 修复SSL证书验证问题
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)


class TranscriptionService:
    """语音转录服务"""

    def __init__(self):
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        self.model = None

    def load_model(self):
        """加载Whisper模型"""
        if self.model is None:
            logger.info(f"正在加载Whisper模型: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info("模型加载完成")

    def transcribe(
        self,
        audio_path: str,
        language: str = "zh",
        task: str = "transcribe",
        **kwargs
    ) -> Dict[str, Any]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh=中文, en=英文)
            task: 任务类型 (transcribe=转录, translate=翻译)
            **kwargs: 其他Whisper参数

        Returns:
            转录结果字典，包含:
            - text: 完整文本
            - segments: 分段信息 (文本, 开始时间, 结束时间)
            - language: 检测到的语言
        """
        self.load_model()

        logger.info(f"开始转录: {audio_path}")

        # 执行转录
        result = self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=False,
            **kwargs
        )

        # 提取关键信息
        transcription = {
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "segments": [
                {
                    "id": seg["id"],
                    "text": seg["text"].strip(),
                    "start": seg["start"],
                    "end": seg["end"],
                }
                for seg in result["segments"]
            ],
        }

        logger.info(f"转录完成，共 {len(transcription['segments'])} 个片段")

        return transcription

    def transcribe_with_diarization(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        带说话人分离的转录（需要pyannote.audio）

        Args:
            audio_path: 音频文件路径
            num_speakers: 说话人数量（可选）

        Returns:
            转录结果 + 说话人标记
        """
        # TODO: 集成pyannote.audio进行说话人分离
        # 这里先返回基础转录
        return self.transcribe(audio_path)

    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        获取音频文件信息

        Args:
            audio_path: 音频文件路径

        Returns:
            音频信息字典
        """
        import librosa

        # 加载音频
        y, sr = librosa.load(audio_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)

        return {
            "duration": duration,
            "sample_rate": sr,
            "channels": 1 if y.ndim == 1 else y.shape[0],
        }


# 全局实例
transcription_service = TranscriptionService()
