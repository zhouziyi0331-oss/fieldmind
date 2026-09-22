"""
音频处理服务 - 长音频切片 + 转录 + 汇总
支持大文件（100MB+, 1-2小时）的高效处理
🔥 WorkflowEngine集成 - 阶段1
"""

import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path
import subprocess
import tempfile
import os
from app.services.workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    音频处理器 - 切片、转录、汇总一体化
    🔥 支持WorkflowEngine DAG执行
    """

    def __init__(self, use_workflow_engine: bool = True):
        self.name = "AudioProcessor"
        self.chunk_duration = 300  # 5分钟一片（秒）
        self.whisper_service = None
        self.use_workflow_engine = use_workflow_engine  # 🔥 新增

        # 🔥 初始化WorkflowEngine
        if use_workflow_engine:
            self.workflow_engine = WorkflowEngine(max_workers=4)

    def _load_whisper(self):
        """延迟加载Whisper服务"""
        if self.whisper_service is None:
            try:
                from app.services.whisper_service import WhisperService
                self.whisper_service = WhisperService()
                logger.info("✅ Whisper服务加载成功")
            except Exception as e:
                logger.warning(f"⚠️  Whisper服务加载失败: {e}")

    def get_audio_duration(self, file_path: str) -> float:
        """
        获取音频时长（秒）
        使用ffprobe
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            logger.warning(f"⚠️  无法获取音频时长: {e}")
            return 0.0

    def should_split(self, duration: float) -> bool:
        """
        判断是否需要切片

        规则：超过30分钟（1800秒）的音频需要切片
        """
        return duration > 1800  # 30分钟

    def split_audio(self, file_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """
        切片长音频

        Args:
            file_path: 原始音频文件路径
            output_dir: 输出目录

        Returns:
            [
                {
                    "chunk_path": "/path/to/chunk_0.mp3",
                    "start_time": 0.0,
                    "end_time": 300.0,
                    "duration": 300.0,
                    "chunk_index": 0
                },
                ...
            ]
        """
        logger.info(f"🔪 开始切片音频: {file_path}")

        try:
            duration = self.get_audio_duration(file_path)
            logger.info(f"   音频总时长: {self._format_duration(duration)}")

            if duration == 0:
                raise ValueError("无法获取音频时长")

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            # 计算切片数量
            chunk_count = int(duration / self.chunk_duration) + 1
            logger.info(f"   将切分为 {chunk_count} 个片段（每片{self.chunk_duration}秒）")

            chunks = []
            file_ext = Path(file_path).suffix

            for i in range(chunk_count):
                start_time = i * self.chunk_duration
                end_time = min((i + 1) * self.chunk_duration, duration)
                chunk_duration = end_time - start_time

                # 输出文件名
                chunk_path = os.path.join(output_dir, f"chunk_{i:03d}{file_ext}")

                # 使用ffmpeg切片
                cmd = [
                    'ffmpeg',
                    '-i', file_path,
                    '-ss', str(start_time),
                    '-t', str(chunk_duration),
                    '-acodec', 'copy',  # 不重新编码，速度快
                    '-y',  # 覆盖已存在的文件
                    chunk_path
                ]

                subprocess.run(cmd, capture_output=True, check=True)

                chunks.append({
                    "chunk_path": chunk_path,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": chunk_duration,
                    "chunk_index": i,
                    "formatted_start": self._format_duration(start_time),
                    "formatted_end": self._format_duration(end_time)
                })

                logger.info(f"   ✅ 片段 {i+1}/{chunk_count}: {self._format_duration(start_time)} - {self._format_duration(end_time)}")

            logger.info(f"✅ 切片完成: {len(chunks)} 个片段")
            return chunks

        except Exception as e:
            logger.error(f"❌ 切片失败: {e}")
            raise

    def transcribe_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        转录单个音频片段

        Returns:
            {
                "chunk_index": 0,
                "text": "转录文本",
                "start_time": 0.0,
                "end_time": 300.0,
                "formatted_timestamp": "[00:00:00 - 00:05:00]",
                "segments": [...],  # Whisper的详细片段
                "language": "zh"
            }
        """
        self._load_whisper()

        logger.info(f"🎤 转录片段 {chunk['chunk_index']}: {chunk['formatted_start']} - {chunk['formatted_end']}")

        try:
            if self.whisper_service:
                result = self.whisper_service.transcribe(chunk["chunk_path"])
                text = result.get("text", "")
                segments = result.get("segments", [])
                language = result.get("language", "unknown")

                # 调整segments的时间戳（加上片段起始时间）
                adjusted_segments = []
                for seg in segments:
                    adjusted_seg = {
                        **seg,
                        "start": seg.get("start", 0) + chunk["start_time"],
                        "end": seg.get("end", 0) + chunk["start_time"]
                    }
                    adjusted_segments.append(adjusted_seg)

            else:
                # Fallback
                text = f"[片段 {chunk['chunk_index']} - 需要Whisper服务]"
                adjusted_segments = []
                language = "unknown"

            logger.info(f"   ✅ 转录完成: {len(text)} 字符")

            return {
                "chunk_index": chunk["chunk_index"],
                "text": text,
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "formatted_timestamp": f"[{chunk['formatted_start']} - {chunk['formatted_end']}]",
                "segments": adjusted_segments,
                "language": language
            }

        except Exception as e:
            logger.error(f"❌ 转录失败: {e}")
            return {
                "chunk_index": chunk["chunk_index"],
                "text": "",
                "start_time": chunk["start_time"],
                "end_time": chunk["end_time"],
                "formatted_timestamp": f"[{chunk['formatted_start']} - {chunk['formatted_end']}]",
                "segments": [],
                "language": "unknown",
                "error": str(e)
            }

    def merge_transcriptions(self, transcriptions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并所有转录结果

        Args:
            transcriptions: 按chunk_index排序的转录结果列表

        Returns:
            {
                "full_text": "完整文本",
                "chunks": [
                    {
                        "text": "这是第一段",
                        "timestamp": "[00:00:00 - 00:05:00]",
                        "start_time": 0.0,
                        "end_time": 300.0
                    },
                    ...
                ],
                "segments": [...],  # 所有详细片段（带时间戳）
                "total_duration": 3600.0,
                "language": "zh"
            }
        """
        logger.info(f"🔗 合并 {len(transcriptions)} 个转录结果")

        # 按chunk_index排序
        sorted_trans = sorted(transcriptions, key=lambda x: x["chunk_index"])

        # 合并文本
        full_text_parts = []
        chunks = []
        all_segments = []

        for trans in sorted_trans:
            # 添加时间戳标记
            chunk_text = f"{trans['formatted_timestamp']}\n{trans['text']}\n"
            full_text_parts.append(chunk_text)

            # 保存chunk信息
            chunks.append({
                "text": trans["text"],
                "timestamp": trans["formatted_timestamp"],
                "start_time": trans["start_time"],
                "end_time": trans["end_time"]
            })

            # 合并segments
            all_segments.extend(trans.get("segments", []))

        full_text = "\n".join(full_text_parts)

        # 检测主要语言
        languages = [t.get("language", "unknown") for t in sorted_trans]
        main_language = max(set(languages), key=languages.count) if languages else "unknown"

        # 计算总时长
        total_duration = sorted_trans[-1]["end_time"] if sorted_trans else 0.0

        logger.info(f"✅ 合并完成: {len(full_text)} 字符, 时长 {self._format_duration(total_duration)}")

        return {
            "full_text": full_text,
            "chunks": chunks,
            "segments": all_segments,
            "total_duration": total_duration,
            "formatted_duration": self._format_duration(total_duration),
            "language": main_language,
            "chunk_count": len(sorted_trans)
        }

    def process_audio(self, file_path: str, use_workflow_engine: bool = None) -> Dict[str, Any]:
        """
        完整音频处理流程：检测时长 -> 切片（如需要）-> 转录 -> 合并
        🔥 支持WorkflowEngine DAG执行

        Args:
            file_path: 音频文件路径
            use_workflow_engine: 是否使用WorkflowEngine（默认使用初始化配置）

        Returns:
            {
                "text": "完整转录文本",
                "chunks": [...],  # 如果切片了
                "segments": [...],  # 详细时间戳
                "metadata": {
                    "duration": 3600.0,
                    "was_split": True/False,
                    "chunk_count": 12,
                    "language": "zh"
                }
            }
        """
        if use_workflow_engine is None:
            use_workflow_engine = self.use_workflow_engine

        if use_workflow_engine:
            return self._process_with_workflow_engine(file_path)
        else:
            return self._process_traditional(file_path)

    def _process_with_workflow_engine(self, file_path: str) -> Dict[str, Any]:
        """
        🔥 使用WorkflowEngine处理音频（DAG模式）
        """
        logger.info(f"🔥 [WorkflowEngine] 开始处理音频: {file_path}")

        # 创建工作流
        workflow = self.workflow_engine.create_workflow(
            name=f"audio_processing_{Path(file_path).stem}",
            description=f"音频处理流水线 - {file_path}"
        )

        # 🔥 Task 1: 获取音频时长
        self.workflow_engine.add_task(
            workflow,
            name="duration",
            func=self._task_get_duration,
            kwargs={'file_path': file_path},
            dependencies=[]
        )

        # 🔥 Task 2: 判断是否需要切片
        self.workflow_engine.add_task(
            workflow,
            name="check_split",
            func=self._task_check_split,
            kwargs={'duration': '$duration.duration'},
            dependencies=["duration"]
        )

        # 🔥 Task 3: 切片音频（条件执行）
        self.workflow_engine.add_task(
            workflow,
            name="split",
            func=self._task_split_audio,
            kwargs={
                'file_path': file_path,
                'need_split': '$check_split.need_split',
                'duration': '$duration.duration'
            },
            dependencies=["duration", "check_split"]
        )

        # 🔥 Task 4: 转录音频
        self.workflow_engine.add_task(
            workflow,
            name="transcribe",
            func=self._task_transcribe_audio,
            kwargs={
                'file_path': file_path,
                'chunks': '$split.chunks',
                'need_split': '$check_split.need_split'
            },
            dependencies=["split", "check_split"]
        )

        # 🔥 Task 5: 合并结果
        self.workflow_engine.add_task(
            workflow,
            name="finalize",
            func=self._task_finalize_audio,
            kwargs={
                'transcriptions': '$transcribe.transcriptions',
                'duration': '$duration.duration',
                'need_split': '$check_split.need_split'
            },
            dependencies=["transcribe", "duration", "check_split"]
        )

        # 执行工作流
        results = self.workflow_engine.execute(workflow)

        logger.info(f"✅ [WorkflowEngine] 音频处理完成: {file_path}")
        return results['finalize']

    def _process_traditional(self, file_path: str) -> Dict[str, Any]:
        """
        传统顺序处理模式（向后兼容）
        """
        logger.info(f"📝 [传统模式] 开始处理音频: {file_path}")

        try:
            # 1. 获取时长
            duration = self.get_audio_duration(file_path)
            logger.info(f"   音频时长: {self._format_duration(duration)}")

            # 2. 判断是否需要切片
            need_split = self.should_split(duration)

            if need_split:
                logger.info(f"   ⚠️  音频较长（{self._format_duration(duration)}），启动切片处理")

                # 创建临时目录
                with tempfile.TemporaryDirectory() as temp_dir:
                    # 切片
                    chunks = self.split_audio(file_path, temp_dir)

                    # 并行转录所有片段（这里简化为顺序，实际可用ThreadPool）
                    transcriptions = []
                    for chunk in chunks:
                        trans = self.transcribe_chunk(chunk)
                        transcriptions.append(trans)

                    # 合并
                    merged = self.merge_transcriptions(transcriptions)

                    return {
                        "text": merged["full_text"],
                        "chunks": merged["chunks"],
                        "segments": merged["segments"],
                        "metadata": {
                            "duration": duration,
                            "formatted_duration": self._format_duration(duration),
                            "was_split": True,
                            "chunk_count": len(chunks),
                            "language": merged["language"]
                        }
                    }

            else:
                logger.info("   直接转录（无需切片）")

                # 直接转录
                self._load_whisper()
                if self.whisper_service:
                    result = self.whisper_service.transcribe(file_path)
                    text = result.get("text", "")
                    segments = result.get("segments", [])
                    language = result.get("language", "unknown")
                else:
                    text = "[需要Whisper服务]"
                    segments = []
                    language = "unknown"

                return {
                    "text": text,
                    "chunks": [],
                    "segments": segments,
                    "metadata": {
                        "duration": duration,
                        "formatted_duration": self._format_duration(duration),
                        "was_split": False,
                        "chunk_count": 1,
                        "language": language
                    }
                }

        except Exception as e:
            logger.error(f"❌ 音频处理失败: {e}")
            raise

    # ========================================
    # 🔥 WorkflowEngine Task Functions
    # ========================================

    def _task_get_duration(self, file_path: str, _context: dict) -> dict:
        """
        🔥 Task 1: 获取音频时长
        """
        logger.info(f"  [Task] duration: 获取音频时长")

        duration = self.get_audio_duration(file_path)

        logger.info(f"  ✅ duration: {self._format_duration(duration)}")
        return {
            'duration': duration,
            'formatted': self._format_duration(duration)
        }

    def _task_check_split(self, duration: float, _context: dict) -> dict:
        """
        🔥 Task 2: 判断是否需要切片
        """
        logger.info(f"  [Task] check_split: 判断是否需要切片")

        need_split = self.should_split(duration)

        logger.info(f"  ✅ check_split: {'需要切片' if need_split else '无需切片'}")
        return {
            'need_split': need_split,
            'threshold': 1800
        }

    def _task_split_audio(self, file_path: str, need_split: bool, duration: float, _context: dict) -> dict:
        """
        🔥 Task 3: 切片音频（条件执行）
        """
        logger.info(f"  [Task] split: 切片音频")

        if not need_split:
            logger.info(f"  ✅ split: 跳过切片")
            return {
                'chunks': [],
                'skipped': True
            }

        # 创建临时目录
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='audio_chunks_')
        _context['temp_dir'] = temp_dir  # 保存到context供清理

        chunks = self.split_audio(file_path, temp_dir)

        logger.info(f"  ✅ split: 切片完成，共 {len(chunks)} 个片段")
        return {
            'chunks': chunks,
            'temp_dir': temp_dir,
            'skipped': False
        }

    def _task_transcribe_audio(self, file_path: str, chunks: list, need_split: bool, _context: dict) -> dict:
        """
        🔥 Task 4: 转录音频
        """
        logger.info(f"  [Task] transcribe: 转录音频")

        if need_split and chunks:
            # 切片模式：转录所有片段
            transcriptions = []
            for chunk in chunks:
                trans = self.transcribe_chunk(chunk)
                transcriptions.append(trans)

            logger.info(f"  ✅ transcribe: 转录完成，共 {len(transcriptions)} 个片段")
            return {
                'transcriptions': transcriptions,
                'mode': 'split'
            }
        else:
            # 直接转录模式
            self._load_whisper()
            if self.whisper_service:
                result = self.whisper_service.transcribe(file_path)
                text = result.get("text", "")
                segments = result.get("segments", [])
                language = result.get("language", "unknown")
            else:
                text = "[需要Whisper服务]"
                segments = []
                language = "unknown"

            transcriptions = [{
                "chunk_index": 0,
                "text": text,
                "start_time": 0.0,
                "end_time": 0.0,
                "formatted_timestamp": "",
                "segments": segments,
                "language": language
            }]

            logger.info(f"  ✅ transcribe: 转录完成，共 {len(text)} 字符")
            return {
                'transcriptions': transcriptions,
                'mode': 'direct'
            }

    def _task_finalize_audio(self, transcriptions: list, duration: float, need_split: bool, _context: dict) -> dict:
        """
        🔥 Task 5: 合并结果
        """
        logger.info(f"  [Task] finalize: 汇总结果")

        if need_split and len(transcriptions) > 1:
            # 合并多个转录结果
            merged = self.merge_transcriptions(transcriptions)

            result = {
                "text": merged["full_text"],
                "chunks": merged["chunks"],
                "segments": merged["segments"],
                "metadata": {
                    "duration": duration,
                    "formatted_duration": self._format_duration(duration),
                    "was_split": True,
                    "chunk_count": len(transcriptions),
                    "language": merged["language"]
                }
            }
        else:
            # 单个转录结果
            trans = transcriptions[0]
            result = {
                "text": trans["text"],
                "chunks": [],
                "segments": trans.get("segments", []),
                "metadata": {
                    "duration": duration,
                    "formatted_duration": self._format_duration(duration),
                    "was_split": False,
                    "chunk_count": 1,
                    "language": trans.get("language", "unknown")
                }
            }

        # 清理临时目录
        if 'temp_dir' in _context:
            import shutil
            try:
                shutil.rmtree(_context['temp_dir'])
                logger.info(f"  🗑️  清理临时目录: {_context['temp_dir']}")
            except Exception as e:
                logger.warning(f"  ⚠️  清理临时目录失败: {e}")

        logger.info(f"  ✅ finalize: 汇总完成")
        return result

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """格式化时长为 HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
