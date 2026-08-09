"""
FunASR语音转录服务
专为中文优化的语音识别，支持说话人分离
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class FunASRService:
    """FunASR语音转录服务"""

    def __init__(self):
        self.model = None
        self.vad_model = None
        self.punc_model = None
        self.spk_model = None  # 说话人分离模型

    def load_models(self):
        """加载FunASR模型"""
        if self.model is not None:
            return

        try:
            from funasr import AutoModel

            logger.info("正在加载FunASR模型...")

            # 主识别模型（Paraformer-large）- 中文效果最好
            # 简化配置：只加载ASR模型，不加载标点和VAD（避免依赖问题）
            self.model = AutoModel(
                model="paraformer-zh",
                # vad_model="fsmn-vad",      # 暂时禁用
                # punc_model="ct-punc",      # 暂时禁用（有bug）
                # spk_model="cam++",         # 说话人分离，可选
                disable_update=True,         # 禁用自动更新检查
            )

            logger.info("✅ FunASR模型加载完成")

        except Exception as e:
            logger.error(f"❌ FunASR模型加载失败: {e}")
            raise

    def transcribe(
        self,
        audio_path: str,
        language: str = "zh",
        hotwords: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        转录音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言代码 (zh=中文)
            hotwords: 热词，提升特定词汇识别准确率，格式: "词1 词2 词3"
            **kwargs: 其他参数

        Returns:
            转录结果字典:
            - text: 完整文本
            - segments: 分段信息 [{text, start, end, speaker}]
            - language: 语言
        """
        self.load_models()

        logger.info(f"🎤 开始FunASR转录: {audio_path}")

        try:
            # 执行转录
            result = self.model.generate(
                input=audio_path,
                batch_size_s=300,  # 批处理大小
                hotword=hotwords,  # 热词
            )

            # 解析结果
            if not result or len(result) == 0:
                logger.warning("转录结果为空")
                return {
                    "text": "",
                    "language": language,
                    "segments": []
                }

            # FunASR返回格式: [{"text": "...", "timestamp": [[start, end], ...]}]
            raw_result = result[0]

            full_text = raw_result.get("text", "")
            timestamps = raw_result.get("timestamp", [])

            # 构建segments
            segments = []
            if timestamps:
                sentences = full_text.split("。")  # 按句子分割

                for idx, (start_ms, end_ms) in enumerate(timestamps):
                    if idx < len(sentences):
                        text = sentences[idx].strip()
                        if text:
                            segments.append({
                                "id": idx,
                                "text": text,
                                "start": start_ms / 1000.0,  # 转换为秒
                                "end": end_ms / 1000.0,
                                "speaker": None  # 暂不支持说话人分离
                            })
            else:
                # 如果没有时间戳，创建单个segment
                segments.append({
                    "id": 0,
                    "text": full_text,
                    "start": 0.0,
                    "end": 0.0,
                    "speaker": None
                })

            transcription = {
                "text": full_text,
                "language": language,
                "segments": segments,
            }

            logger.info(f"✅ FunASR转录完成，共 {len(segments)} 个片段")
            return transcription

        except Exception as e:
            logger.error(f"❌ FunASR转录失败: {e}")
            raise

    def transcribe_with_speaker_diarization(
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
        # TODO: 集成CAM++说话人分离模型
        logger.warning("说话人分离功能尚未实现，返回基础转录")
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
            import librosa

            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)

            return {
                "duration": duration,
                "sample_rate": sr,
                "channels": 1 if y.ndim == 1 else y.shape[0],
            }
        except Exception as e:
            logger.error(f"获取音频信息失败: {e}")
            return {
                "duration": 0,
                "sample_rate": 0,
                "channels": 0,
            }


# 全局实例
funasr_service = FunASRService()
