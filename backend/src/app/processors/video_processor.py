"""
视频处理器
视频内容提取：帧提取 + 音频提取 + OCR + ASR
"""

import os
import subprocess
from typing import Dict, Any, List
from pathlib import Path

from app.core.logging import logger
from app.core.exceptions import DocumentProcessingException
from app.core.errors import ErrorCode


class VideoProcessor:
    """视频处理器"""

    @staticmethod
    def process(file_path: str, frame_interval: int = 30) -> Dict[str, Any]:
        """
        处理视频文件

        Args:
            file_path: 视频文件路径
            frame_interval: 帧提取间隔（秒）

        Returns:
            Dict: 处理结果
                {
                    "text": str,              # 综合文本（字幕+语音）
                    "frames": int,            # 提取的帧数
                    "duration": float,        # 时长（秒）
                    "metadata": dict,         # 元数据
                }
        """
        logger.info(f"处理视频: {file_path}")

        try:
            # 1. 提取元数据
            metadata = VideoProcessor._extract_metadata(file_path)

            # 2. 提取音频
            audio_path = VideoProcessor._extract_audio(file_path)

            # 3. 语音识别
            audio_text = ""
            if audio_path and os.path.exists(audio_path):
                from app.processors.audio_processor import ASREngine
                asr_result = ASREngine.transcribe(audio_path)
                audio_text = asr_result["text"]
                os.remove(audio_path)  # 清理临时文件

            # 4. 提取关键帧（可选）
            # frames = VideoProcessor._extract_frames(file_path, frame_interval)
            # frame_texts = []
            # for frame in frames:
            #     # OCR 识别帧中的文字
            #     pass

            # 综合文本
            combined_text = audio_text

            return {
                "text": combined_text,
                "frames": 0,  # 实际提取的帧数
                "duration": metadata.get("duration", 0),
                "metadata": metadata,
                "word_count": len(combined_text.split()),
            }

        except Exception as e:
            logger.error(f"视频处理失败: {e}", file_path=file_path)
            raise DocumentProcessingException(
                error_code=ErrorCode.DOCUMENT_PROCESSING_FAILED,
                message=f"Failed to process video: {str(e)}"
            )

    @staticmethod
    def _extract_metadata(file_path: str) -> Dict[str, Any]:
        """
        提取视频元数据

        Args:
            file_path: 视频路径

        Returns:
            Dict: 元数据
        """
        try:
            import json

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
                video_stream = next(
                    (s for s in info.get('streams', []) if s.get('codec_type') == 'video'),
                    {}
                )

                return {
                    "duration": float(format_info.get('duration', 0)),
                    "bit_rate": format_info.get('bit_rate'),
                    "format": format_info.get('format_name'),
                    "video_codec": video_stream.get('codec_name'),
                    "width": video_stream.get('width'),
                    "height": video_stream.get('height'),
                    "fps": eval(video_stream.get('r_frame_rate', '0/1')),
                }

        except Exception as e:
            logger.warning(f"无法提取视频元数据: {e}")

        return {}

    @staticmethod
    def _extract_audio(file_path: str) -> str:
        """
        从视频中提取音频

        Args:
            file_path: 视频路径

        Returns:
            str: 音频文件路径
        """
        try:
            # 创建临时目录
            temp_dir = Path("/tmp/fieldmind/audio")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 生成音频文件路径
            audio_path = temp_dir / f"{Path(file_path).stem}.mp3"

            # 使用 ffmpeg 提取音频
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-vn',  # 不包含视频
                '-acodec', 'libmp3lame',
                '-q:a', '2',  # 音频质量
                '-y',  # 覆盖已存在的文件
                str(audio_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                return str(audio_path)
            else:
                logger.warning(f"音频提取失败: {result.stderr}")
                return ""

        except Exception as e:
            logger.error(f"提取音频失败: {e}")
            return ""

    @staticmethod
    def _extract_frames(
        file_path: str,
        interval: int = 30
    ) -> List[str]:
        """
        提取视频关键帧

        Args:
            file_path: 视频路径
            interval: 提取间隔（秒）

        Returns:
            List[str]: 帧图片路径列表
        """
        try:
            # 创建临时目录
            temp_dir = Path("/tmp/fieldmind/frames")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 使用 ffmpeg 提取帧
            output_pattern = temp_dir / f"{Path(file_path).stem}_%04d.jpg"

            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-vf', f'fps=1/{interval}',  # 每 N 秒提取一帧
                '-y',
                str(output_pattern)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                # 获取所有生成的帧
                frames = list(temp_dir.glob(f"{Path(file_path).stem}_*.jpg"))
                return [str(f) for f in frames]
            else:
                logger.warning(f"帧提取失败: {result.stderr}")
                return []

        except Exception as e:
            logger.error(f"提取帧失败: {e}")
            return []
