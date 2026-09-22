"""视频处理服务 - 提取音频并转录"""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.core.transcription import transcription_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoProcessor:
    """视频处理服务"""

    def __init__(self):
        self.temp_dir = Path(settings.storage.upload_dir) / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        从视频中提取音频

        Args:
            video_path: 视频文件路径
            output_path: 输出音频路径（可选）

        Returns:
            音频文件路径
        """
        if output_path is None:
            video_file = Path(video_path)
            output_path = str(self.temp_dir / f"{video_file.stem}_audio.wav")

        try:
            # 使用ffmpeg提取音频
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # 不处理视频
                '-acodec', 'pcm_s16le',  # 转换为WAV格式
                '-ar', '16000',  # 采样率16kHz（Whisper推荐）
                '-ac', '1',  # 单声道
                '-y',  # 覆盖已存在的文件
                output_path
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"音频提取成功: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"音频提取失败: {e.stderr}")
            raise Exception(f"音频提取失败: {e.stderr}")

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息字典
        """
        try:
            command = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )

            import json
            info = json.loads(result.stdout)

            # 提取关键信息
            format_info = info.get('format', {})
            video_stream = next(
                (s for s in info.get('streams', []) if s.get('codec_type') == 'video'),
                {}
            )
            audio_stream = next(
                (s for s in info.get('streams', []) if s.get('codec_type') == 'audio'),
                {}
            )

            return {
                'duration': float(format_info.get('duration', 0)),
                'size': int(format_info.get('size', 0)),
                'format': format_info.get('format_name', ''),
                'video_codec': video_stream.get('codec_name', ''),
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                'audio_codec': audio_stream.get('codec_name', ''),
                'audio_sample_rate': audio_stream.get('sample_rate', ''),
                'has_audio': bool(audio_stream),
                'has_video': bool(video_stream)
            }

        except Exception as e:
            logger.error(f"获取视频信息失败: {str(e)}")
            return {}

    def process_video(
        self,
        video_path: str,
        language: str = "zh",
        cleanup_audio: bool = True
    ) -> Dict[str, Any]:
        """
        完整处理视频：提取音频 + 转录

        Args:
            video_path: 视频文件路径
            language: 语言代码
            cleanup_audio: 是否清理临时音频文件

        Returns:
            处理结果
        """
        logger.info(f"开始处理视频: {video_path}")

        # 1. 获取视频信息
        video_info = self.get_video_info(video_path)

        if not video_info.get('has_audio'):
            raise Exception("视频文件不包含音频轨道")

        # 2. 提取音频
        audio_path = self.extract_audio(video_path)

        # 3. 转录音频
        transcription = transcription_service.transcribe(
            audio_path=audio_path,
            language=language
        )

        # 4. 清理临时文件
        if cleanup_audio and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"清理临时音频文件: {audio_path}")
            except Exception as e:
                logger.warning(f"清理音频文件失败: {str(e)}")

        # 5. 返回结果
        return {
            'video_info': video_info,
            'transcription': transcription,
            'text': transcription['text'],
            'language': transcription['language'],
            'segments': transcription['segments'],
            'audio_extracted': True
        }

    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for file in self.temp_dir.glob("*_audio.wav"):
                file.unlink()
            logger.info("临时文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {str(e)}")


# 全局实例
video_processor = VideoProcessor()
