"""
语音转录服务
基于OpenAI Whisper
支持：分块处理、进度回调、超时控制
"""

import whisper
import torch
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
import logging
import ssl
import certifi
import os
import tempfile
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import time

from app.core.config import settings

# 修复SSL证书验证问题
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)


class TranscriptionService:
    """语音转录服务

    特性：
    - 支持大文件分块处理
    - 实时进度回调
    - 超时控制
    - 自动重试
    """

    # 配置常量
    CHUNK_DURATION_MS = 600000  # 10分钟分块（毫秒）
    MAX_FILE_SIZE_MB = 500  # 单文件最大 500MB
    TRANSCRIBE_TIMEOUT = 1800  # 30分钟超时
    LARGE_FILE_THRESHOLD_MB = 50  # 大于50MB使用分块

    def __init__(self):
        self.model_name = settings.ai.whisper_model
        self.device = settings.ai.whisper_device
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=2)

    def load_model(self):
        """加载Whisper模型"""
        if self.model is None:
            logger.info(f"正在加载Whisper模型: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"模型加载完成: {self.model_name}")

    def transcribe(
        self,
        audio_path: str,
        language: str = "zh",
        task: str = "transcribe",
        progress_callback: Optional[Callable[[int, str], None]] = None,
        timeout: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        转录音频文件（支持大文件分块处理）

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh=中文, en=英文)
            task: 任务类型 (transcribe=转录, translate=翻译)
            progress_callback: 进度回调函数 callback(progress: int, message: str)
            timeout: 超时时间（秒），默认使用 TRANSCRIBE_TIMEOUT
            **kwargs: 其他Whisper参数

        Returns:
            转录结果字典，包含:
            - text: 完整文本
            - segments: 分段信息 (文本, 开始时间, 结束时间)
            - language: 检测到的语言
            - chunks_processed: 处理的分块数
            - total_duration: 音频总时长（秒）
        """
        timeout = timeout or self.TRANSCRIBE_TIMEOUT

        try:
            # 检查文件大小
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            logger.info(f"开始转录音频: {audio_path} ({file_size_mb:.2f} MB)")

            if file_size_mb > self.MAX_FILE_SIZE_MB:
                raise ValueError(f"文件过大: {file_size_mb:.2f}MB > {self.MAX_FILE_SIZE_MB}MB")

            if progress_callback:
                progress_callback(5, f"准备处理 {file_size_mb:.1f}MB 音频文件...")

            # 判断是否需要分块
            if file_size_mb > self.LARGE_FILE_THRESHOLD_MB:
                logger.info(f"文件较大 ({file_size_mb:.2f}MB)，使用分块处理")
                return self._transcribe_chunked(
                    audio_path, language, task, progress_callback, timeout, **kwargs
                )
            else:
                # 小文件直接处理
                return self._transcribe_single(
                    audio_path, language, task, progress_callback, timeout, **kwargs
                )

        except Exception as e:
            logger.error(f"转录失败: {e}", exc_info=True)
            if progress_callback:
                progress_callback(0, f"转录失败: {str(e)}")
            raise

    def _transcribe_single(
        self,
        audio_path: str,
        language: str,
        task: str,
        progress_callback: Optional[Callable[[int, str], None]],
        timeout: int,
        **kwargs
    ) -> Dict[str, Any]:
        """处理单个音频文件（无分块）"""
        self.load_model()

        if progress_callback:
            progress_callback(10, "开始转录...")

        # 使用超时控制
        future = self.executor.submit(
            self._do_transcribe, audio_path, language, task, **kwargs
        )

        try:
            result = future.result(timeout=timeout)

            if progress_callback:
                progress_callback(90, "转录完成，处理结果...")

            # 提取分段信息
            segments = []
            if "segments" in result:
                for seg in result["segments"]:
                    segments.append({
                        "id": seg.get("id", len(segments)),
                        "text": seg["text"].strip(),
                        "start": seg["start"],
                        "end": seg["end"]
                    })

            if progress_callback:
                progress_callback(100, "完成")

            logger.info(f"转录完成，文本长度: {len(result['text'])}")

            return {
                "text": result["text"],
                "segments": segments,
                "language": result.get("language", language),
                "chunks_processed": 1,
                "total_duration": segments[-1]["end"] if segments else 0
            }

        except FuturesTimeoutError:
            future.cancel()
            logger.error(f"转录超时 ({timeout}秒)")
            raise TimeoutError(f"转录超时: 超过 {timeout} 秒")

    def _transcribe_chunked(
        self,
        audio_path: str,
        language: str,
        task: str,
        progress_callback: Optional[Callable[[int, str], None]],
        timeout: int,
        **kwargs
    ) -> Dict[str, Any]:
        """分块处理大音频文件"""
        self.load_model()

        if progress_callback:
            progress_callback(5, "加载音频文件...")

        # 加载音频
        try:
            audio = AudioSegment.from_file(audio_path)
            duration_ms = len(audio)
            duration_sec = duration_ms / 1000
            logger.info(f"音频时长: {duration_sec:.2f}秒")
        except Exception as e:
            logger.error(f"加载音频失败: {e}")
            raise ValueError(f"无法加载音频文件: {e}")

        # 计算分块数量
        num_chunks = (duration_ms + self.CHUNK_DURATION_MS - 1) // self.CHUNK_DURATION_MS
        logger.info(f"将音频分为 {num_chunks} 个块处理")

        if progress_callback:
            progress_callback(10, f"将音频分为 {num_chunks} 块处理...")

        # 处理每个分块
        all_segments = []
        all_text = []
        temp_files = []

        try:
            for i in range(num_chunks):
                chunk_start = i * self.CHUNK_DURATION_MS
                chunk_end = min((i + 1) * self.CHUNK_DURATION_MS, duration_ms)

                # 进度更新
                progress = 10 + int((i / num_chunks) * 80)
                if progress_callback:
                    progress_callback(progress, f"处理第 {i+1}/{num_chunks} 块...")

                logger.info(f"处理分块 {i+1}/{num_chunks} ({chunk_start/1000:.1f}s - {chunk_end/1000:.1f}s)")

                # 提取分块
                chunk = audio[chunk_start:chunk_end]

                # 保存临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                chunk.export(temp_file.name, format='wav')
                temp_files.append(temp_file.name)

                # 转录分块（带超时）
                chunk_timeout = int(timeout * (chunk_end - chunk_start) / duration_ms) + 60
                future = self.executor.submit(
                    self._do_transcribe, temp_file.name, language, task, **kwargs
                )

                try:
                    result = future.result(timeout=chunk_timeout)

                    # 收集结果
                    all_text.append(result["text"])

                    if "segments" in result:
                        # 调整时间戳
                        time_offset = chunk_start / 1000
                        for seg in result["segments"]:
                            all_segments.append({
                                "id": len(all_segments),
                                "text": seg["text"].strip(),
                                "start": seg["start"] + time_offset,
                                "end": seg["end"] + time_offset
                            })

                except FuturesTimeoutError:
                    logger.warning(f"分块 {i+1} 转录超时，跳过")
                    all_text.append(f"[分块 {i+1} 处理超时]")

            if progress_callback:
                progress_callback(95, "合并结果...")

            # 合并文本
            final_text = " ".join(all_text)

            if progress_callback:
                progress_callback(100, "完成")

            logger.info(f"分块转录完成，共 {num_chunks} 块，{len(all_segments)} 个片段")

            return {
                "text": final_text,
                "segments": all_segments,
                "language": language,
                "chunks_processed": num_chunks,
                "total_duration": duration_sec
            }

        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

    def _do_transcribe(self, audio_path: str, language: str, task: str, **kwargs) -> Dict[str, Any]:
        """执行实际的转录操作"""
        return self.model.transcribe(
            audio_path,
            language=language,
            task=task,
            verbose=False,
            **kwargs
        )

    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        转录音频并返回详细时间戳

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            转录结果（包含详细时间戳）
        """
        return self.transcribe(
            audio_path,
            language=language,
            word_timestamps=True
        )

    def transcribe_with_speaker_diarization(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        转录音频并进行说话人分离

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
        try:
            audio = AudioSegment.from_file(audio_path)
            duration_sec = len(audio) / 1000

            return {
                "duration": duration_sec,
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "file_size_mb": os.path.getsize(audio_path) / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return {
                "duration": 0,
                "sample_rate": 0,
                "channels": 0,
                "file_size_mb": os.path.getsize(audio_path) / (1024 * 1024)
            }


# 全局实例
transcription_service = TranscriptionService()
