"""
视频处理服务 - 提取音频并转录
🔥 WorkflowEngine集成 - 阶段1
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.core.transcription import transcription_service
from app.core.config import settings
from app.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    视频处理服务
    🔥 支持WorkflowEngine DAG执行
    """

    def __init__(self, use_workflow_engine: bool = True):
        self.temp_dir = Path(settings.storage.upload_dir) / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.use_workflow_engine = use_workflow_engine  # 🔥 新增

        # 🔥 初始化WorkflowEngine
        if use_workflow_engine:
            self.workflow_engine = WorkflowEngine(max_workers=3)

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
        cleanup_audio: bool = True,
        use_workflow_engine: bool = None
    ) -> Dict[str, Any]:
        """
        完整处理视频：提取音频 + 转录
        🔥 支持WorkflowEngine DAG执行

        Args:
            video_path: 视频文件路径
            language: 语言代码
            cleanup_audio: 是否清理临时音频文件
            use_workflow_engine: 是否使用WorkflowEngine（默认使用初始化配置）

        Returns:
            处理结果
        """
        if use_workflow_engine is None:
            use_workflow_engine = self.use_workflow_engine

        if use_workflow_engine:
            return self._process_with_workflow_engine(
                video_path=video_path,
                language=language,
                cleanup_audio=cleanup_audio
            )
        else:
            return self._process_traditional(
                video_path=video_path,
                language=language,
                cleanup_audio=cleanup_audio
            )

    def _process_with_workflow_engine(
        self,
        video_path: str,
        language: str,
        cleanup_audio: bool
    ) -> Dict[str, Any]:
        """
        🔥 使用WorkflowEngine处理视频（DAG模式）
        """
        logger.info(f"🔥 [WorkflowEngine] 开始处理视频: {video_path}")

        # 创建工作流
        workflow = self.workflow_engine.create_workflow(
            name=f"video_processing_{Path(video_path).stem}",
            description=f"视频处理流水线 - {video_path}"
        )

        # 🔥 Task 1: 获取视频信息
        self.workflow_engine.add_task(
            workflow,
            name="video_info",
            func=self._task_get_video_info,
            kwargs={'video_path': video_path},
            dependencies=[]
        )

        # 🔥 Task 2: 提取音频
        self.workflow_engine.add_task(
            workflow,
            name="extract_audio",
            func=self._task_extract_audio,
            kwargs={
                'video_path': video_path,
                'has_audio': '$video_info.has_audio'
            },
            dependencies=["video_info"]
        )

        # 🔥 Task 3: 转录音频
        self.workflow_engine.add_task(
            workflow,
            name="transcribe",
            func=self._task_transcribe_audio,
            kwargs={
                'audio_path': '$extract_audio.audio_path',
                'language': language
            },
            dependencies=["extract_audio"]
        )

        # 🔥 Task 4: 清理临时文件
        self.workflow_engine.add_task(
            workflow,
            name="cleanup",
            func=self._task_cleanup_audio,
            kwargs={
                'audio_path': '$extract_audio.audio_path',
                'cleanup_audio': cleanup_audio
            },
            dependencies=["transcribe"]
        )

        # 🔥 Task 5: 汇总结果
        self.workflow_engine.add_task(
            workflow,
            name="finalize",
            func=self._task_finalize_video,
            kwargs={
                'video_info': '$video_info',
                'transcription': '$transcribe.transcription'
            },
            dependencies=["video_info", "transcribe", "cleanup"]
        )

        # 执行工作流
        results = self.workflow_engine.execute(workflow)

        logger.info(f"✅ [WorkflowEngine] 视频处理完成: {video_path}")
        return results['finalize']

    def _process_traditional(
        self,
        video_path: str,
        language: str,
        cleanup_audio: bool
    ) -> Dict[str, Any]:
        """
        传统顺序处理模式（向后兼容）
        """
        logger.info(f"📝 [传统模式] 开始处理视频: {video_path}")

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

    # ========================================
    # 🔥 WorkflowEngine Task Functions
    # ========================================

    def _task_get_video_info(self, video_path: str, _context: dict) -> dict:
        """
        🔥 Task 1: 获取视频信息
        """
        logger.info(f"  [Task] video_info: 获取视频信息")

        video_info = self.get_video_info(video_path)

        if not video_info:
            raise Exception("无法获取视频信息")

        logger.info(f"  ✅ video_info: 时长 {video_info.get('duration', 0):.2f}s, "
                   f"音频: {'有' if video_info.get('has_audio') else '无'}")

        return video_info

    def _task_extract_audio(self, video_path: str, has_audio: bool, _context: dict) -> dict:
        """
        🔥 Task 2: 提取音频
        """
        logger.info(f"  [Task] extract_audio: 提取音频")

        if not has_audio:
            raise Exception("视频文件不包含音频轨道")

        audio_path = self.extract_audio(video_path)

        logger.info(f"  ✅ extract_audio: {audio_path}")
        return {
            'audio_path': audio_path,
            'success': True
        }

    def _task_transcribe_audio(self, audio_path: str, language: str, _context: dict) -> dict:
        """
        🔥 Task 3: 转录音频
        """
        logger.info(f"  [Task] transcribe: 转录音频")

        transcription = transcription_service.transcribe(
            audio_path=audio_path,
            language=language
        )

        text_length = len(transcription.get('text', ''))
        logger.info(f"  ✅ transcribe: 转录完成，共 {text_length} 字符")

        return {
            'transcription': transcription,
            'text_length': text_length
        }

    def _task_cleanup_audio(self, audio_path: str, cleanup_audio: bool, _context: dict) -> dict:
        """
        🔥 Task 4: 清理临时音频文件
        """
        logger.info(f"  [Task] cleanup: 清理临时文件")

        if cleanup_audio and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"  ✅ cleanup: 已删除 {audio_path}")
                return {'cleaned': True, 'path': audio_path}
            except Exception as e:
                logger.warning(f"  ⚠️  cleanup: 清理失败 - {e}")
                return {'cleaned': False, 'error': str(e)}
        else:
            logger.info(f"  ✅ cleanup: 跳过清理")
            return {'cleaned': False, 'skipped': True}

    def _task_finalize_video(self, video_info: dict, transcription: dict, _context: dict) -> dict:
        """
        🔥 Task 5: 汇总结果
        """
        logger.info(f"  [Task] finalize: 汇总结果")

        result = {
            'video_info': video_info,
            'transcription': transcription,
            'text': transcription['text'],
            'language': transcription['language'],
            'segments': transcription['segments'],
            'audio_extracted': True
        }

        logger.info(f"  ✅ finalize: 结果汇总完成")
        return result

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
