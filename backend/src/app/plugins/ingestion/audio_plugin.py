"""
音频采集插件
"""

from typing import Dict, Any
from app.agents.ingestion_agent import IngestionPlugin
from app.core.logging import logger


class AudioPlugin(IngestionPlugin):
    """音频采集插件（ASR）"""

    @property
    def plugin_name(self) -> str:
        return "AudioPlugin"

    @property
    def supported_formats(self) -> list:
        return ["mp3", "wav", "m4a", "flac", "ogg"]

    def ingest(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """采集音频文件（语音识别）"""
        try:
            # 提取音频元数据
            structured_metadata = self._extract_audio_metadata(file_path)

            # 语音识别
            try:
                from app.core.transcription import transcription_service

                # 定义进度回调
                def progress_callback(progress: int, message: str):
                    logger.info(f"[AudioPlugin] 转录进度: {progress}% - {message}")
                    # 如果有 document_id，可以更新数据库进度
                    if metadata.get("id"):
                        try:
                            from app.core.database import SessionLocal
                            from app.models.project import ProjectDocument
                            db = SessionLocal()
                            doc = db.query(ProjectDocument).filter(
                                ProjectDocument.id == metadata["id"]
                            ).first()
                            if doc:
                                doc.processing_progress = progress
                                db.commit()
                            db.close()
                        except Exception as e:
                            logger.warning(f"更新进度失败: {e}")

                # 调用转录服务（带进度回调）
                result = transcription_service.transcribe(
                    file_path,
                    progress_callback=progress_callback
                )

                text = result["text"].strip()
                extraction_method = "whisper_with_chunking"
                confidence = 0.85
                structured_metadata["detected_language"] = result.get("language", "unknown")
                structured_metadata["chunks_processed"] = result.get("chunks_processed", 1)
                structured_metadata["total_duration"] = result.get("total_duration", 0)
                transcript = result.get("segments", [])

            except ImportError:
                logger.warning("whisper 未安装，音频 ASR 不可用")
                text = ""
                transcript = []
                extraction_method = "unavailable"
                extraction_status = "unavailable"
                confidence = 0.0
            else:
                extraction_status = "success"

            # 统计
            structured_metadata["total_words"] = len(text.replace(" ", ""))
            structured_metadata["total_sentences"] = text.count('。') + text.count('.')
            structured_metadata["language"] = structured_metadata.get("detected_language", "unknown")
            structured_metadata["speaker_count"] = 1  # TODO: 说话人分离

            return {
                "raw_text": text,
                "transcript": transcript,
                "structured_metadata": structured_metadata,
                "content_type": "audio",
                "extraction_method": extraction_method,
                "extraction_status": extraction_status,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"音频采集失败: {e}")
            raise

    def _extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取音频元数据"""
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
                stream_info = info.get('streams', [{}])[0]

                return {
                    "duration": float(format_info.get('duration', 0)),
                    "bit_rate": format_info.get('bit_rate'),
                    "format": format_info.get('format_name'),
                    "codec": stream_info.get('codec_name'),
                    "sample_rate": stream_info.get('sample_rate'),
                    "channels": stream_info.get('channels'),
                }
        except:
            pass

        return {"duration": 0}
