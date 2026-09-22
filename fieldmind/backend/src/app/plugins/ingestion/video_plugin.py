"""
视频采集插件
"""

from typing import Dict, Any
from fractions import Fraction
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class VideoPlugin(IngestionPlugin):
    """视频采集插件（提取音频 + ASR）"""

    @property
    def plugin_name(self) -> str:
        return "VideoPlugin"

    @property
    def supported_formats(self) -> list:
        return ["mp4", "avi", "mov", "mkv", "webm"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集视频文件（提取音频轨 + 语音识别）"""
        try:
            # 提取视频元数据
            structured_metadata = self._extract_video_metadata(file_path)

            # 提取音频轨
            audio_path = self._extract_audio(file_path)

            # 语音识别
            if audio_path:
                try:
                    from app.core.transcription import transcription_service
                    result = transcription_service.transcribe(audio_path)
                    text = result["text"].strip()
                    extraction_method = "ffmpeg+shared_transcription_service"
                    confidence = 0.8
                    structured_metadata["detected_language"] = result.get("language", "unknown")
                    transcript = result.get("segments", [])
                except ImportError:
                    logger.warning("whisper 未安装，视频音频转写不可用")
                    text = ""
                    transcript = []
                    extraction_method = "unavailable"
                    extraction_status = "unavailable"
                    confidence = 0.0
                else:
                    extraction_status = "success"
            else:
                text = ""
                transcript = []
                extraction_method = "no_audio"
                extraction_status = "empty"
                confidence = 0.0

            # 统计
            structured_metadata["total_words"] = len(text.replace(" ", ""))
            structured_metadata["total_sentences"] = text.count('。') + text.count('.')
            structured_metadata["language"] = structured_metadata.get("detected_language", "unknown")

            return {
                "raw_text": text,
                "transcript": transcript,
                "structured_metadata": structured_metadata,
                "content_type": "video",
                "extraction_method": extraction_method,
                "extraction_status": extraction_status,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"视频采集失败: {e}")
            raise

    def _extract_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取视频元数据"""
        try:
            import subprocess
            import json

            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                info = json.loads(result.stdout)
                format_info = info.get('format', {})
                video_stream = next(
                    (s for s in info.get('streams', []) if s.get('codec_type') == 'video'),
                    {}
                )

                return {
                    "duration": float(format_info.get('duration', 0)),
                    "format": format_info.get('format_name'),
                    "video_codec": video_stream.get('codec_name'),
                    "width": video_stream.get('width'),
                    "height": video_stream.get('height'),
                    "fps": float(Fraction(video_stream.get('r_frame_rate', '0/1')))
                    if video_stream.get('r_frame_rate') else 0,
                }
        except:
            pass

        return {"duration": 0}

    def _extract_audio(self, file_path: str) -> str:
        """从视频提取音频"""
        try:
            import subprocess
            from pathlib import Path

            temp_dir = Path("/tmp/fieldmind/audio")
            temp_dir.mkdir(parents=True, exist_ok=True)
            audio_path = temp_dir / f"{Path(file_path).stem}.mp3"

            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-vn',
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                '-y',
                str(audio_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                return str(audio_path)
        except:
            pass

        return ""
