"""
音频处理器
音频转文本（ASR - Automatic Speech Recognition）
"""

import os
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingException
from app.core.errors import ErrorCode


class AudioProcessor:
    """音频处理器"""

    @staticmethod
    def process(file_path: str) -> Dict[str, Any]:
        """
        处理音频文件

        Args:
            file_path: 音频文件路径

        Returns:
            Dict: 处理结果
                {
                    "text": str,              # 识别的文本
                    "language": str,          # 语言
                    "duration": float,        # 时长（秒）
                    "metadata": dict,         # 元数据
                }
        """
        logger.info(f"处理音频: {file_path}")

        try:
            # 1. 提取元数据
            metadata = AudioProcessor._extract_metadata(file_path)

            # 2. 语音识别
            asr_result = ASREngine.transcribe(file_path)

            return {
                "text": asr_result["text"],
                "language": asr_result.get("language", "unknown"),
                "duration": metadata.get("duration", 0),
                "metadata": metadata,
                "word_count": len(asr_result["text"].split()),
            }

        except Exception as e:
            logger.error(f"音频处理失败: {e}", file_path=file_path)
            raise DocumentProcessingException(
                error_code=ErrorCode.DOCUMENT_PROCESSING_FAILED,
                message=f"Failed to process audio: {str(e)}"
            )

    @staticmethod
    def _extract_metadata(file_path: str) -> Dict[str, Any]:
        """
        提取音频元数据

        Args:
            file_path: 音频路径

        Returns:
            Dict: 元数据
        """
        try:
            import subprocess
            import json

            # 使用 ffprobe 获取音频信息
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                info = json.loads(result.stdout)

                format_info = info.get('format', {})
                stream_info = info.get('streams', [{}])[0]

                return {
                    "duration": float(format_info.get('duration', 0)),
                    "bit_rate": format_info.get('bit_rate'),
                    "format": format_info.get('format_name'),
                    "codec": stream_info.get('codec_name'),
                    "sample_rate": stream_info.get('sample_rate'),
                    "channels": stream_info.get('channels'),
                }

        except Exception as e:
            logger.warning(f"无法提取音频元数据: {e}")

        return {}


class ASREngine:
    """语音识别引擎"""

    @staticmethod
    def transcribe(file_path: str) -> Dict[str, Any]:
        """
        语音转文本

        Args:
            file_path: 音频文件路径

        Returns:
            Dict: 识别结果
        """
        # 尝试使用 Whisper
        try:
            return WhisperASR.transcribe(file_path)
        except ImportError:
            logger.warning("Whisper 未安装，音频 ASR 不可用")
            return {
                "text": "",
                "language": "unknown",
                "method": "unavailable",
                "status": "unavailable",
            }


class WhisperASR:
    """OpenAI Whisper ASR"""

    _model = None

    @staticmethod
    def transcribe(file_path: str) -> Dict[str, Any]:
        """
        使用 Whisper 进行语音识别

        Args:
            file_path: 音频文件路径

        Returns:
            Dict: 识别结果
        """
        import whisper

        # 延迟加载模型
        if WhisperASR._model is None:
            model_size = os.getenv("WHISPER_MODEL", "base")
            logger.info(f"加载 Whisper 模型: {model_size}")
            WhisperASR._model = whisper.load_model(model_size)

        # 执行识别
        result = WhisperASR._model.transcribe(
            file_path,
            language=None,  # 自动检测语言
            task="transcribe"
        )

        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "method": "whisper"
        }
