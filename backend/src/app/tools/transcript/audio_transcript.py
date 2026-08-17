"""
Audio Transcript Tool - 音频转录工具函数
从 TranscriptAgent 提取的核心功能

职责：
1. 将音频/视频文件转换为文字（使用Whisper）
2. 自动清洗转录文本（去口头禅、合并断句、纠错）
3. 提取量化指标：专业名词、核心人物、特殊事件、文化分类
4. 长音频分段处理（>50MB自动切分）

Author: Extracted from TranscriptAgent
Date: 2026-08-14
"""

from typing import Dict, Any, List, Optional
import logging
import os
import re
from collections import Counter
from pydub import AudioSegment

from app.core.transcription import transcription_service
from app.tools.report.cultural_classifier import cultural_classifier

logger = logging.getLogger(__name__)

# 长音频阈值（50MB）
LONG_AUDIO_THRESHOLD = 50 * 1024 * 1024
# 分段时长（10分钟）
SEGMENT_DURATION_MS = 10 * 60 * 1000

# 口头禅列表
FILLER_WORDS = [
    "嗯", "啊", "呃", "哦", "哎", "唉", "诶",
    "那个", "这个", "就是", "然后",
    "嗯嗯", "啊啊", "呃呃",
]


def transcribe_audio(
    file_path: str,
    file_type: str = 'audio',
    language: str = 'auto',
    enable_metrics: bool = True,
    enable_cleaning: bool = True
) -> Dict[str, Any]:
    """
    转录音频/视频文件为文字

    Args:
        file_path: 音频/视频文件路径
        file_type: 文件类型 ('audio' | 'video')
        language: 语言代码（默认'auto'自动检测）
        enable_metrics: 是否提取量化指标
        enable_cleaning: 是否清洗文本

    Returns:
        {
            'status': 'completed',
            'transcript': {
                'full_text': '清洗后的完整文本',
                'raw_text': '原始转录文本',
                'segments': [...],
                'language': 'zh'
            },
            'metrics': {
                '专业名词': [...],
                '核心人物': [...],
                '特殊事件': [...],
                '文化分类': {...}
            },
            'total': {
                '时长': 2400,
                '原始字数': 3500,
                '清洗后字数': 3200
            }
        }
    """
    if not file_path:
        raise ValueError("file_path 是必需的参数")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 检查文件大小
    file_size = os.path.getsize(file_path)
    file_size_mb = file_size / (1024 * 1024)
    logger.info(f"开始转录文件: {file_path}, 类型: {file_type}, 大小: {file_size_mb:.2f}MB")

    # 如果是视频，先提取音频
    audio_path = file_path
    temp_audio = None
    if file_type in ['video', 'video/mp4', 'video/mov', 'video/avi']:
        logger.info("检测到视频文件，提取音频轨道...")
        audio_path = _extract_audio_from_video(file_path)
        temp_audio = audio_path

    try:
        # 判断是否需要分段处理（大于50MB）
        is_long_audio = file_size > LONG_AUDIO_THRESHOLD

        # 调用Whisper转录
        if is_long_audio:
            logger.info(f"检测到长音频文件（{file_size_mb:.2f}MB），启用分段处理...")
            result = _transcribe_long_audio(
                audio_path,
                language=language if language != 'auto' else None
            )
        else:
            result = transcription_service.transcribe(
                audio_path,
                language=language if language != 'auto' else None
            )

        # 提取结果
        raw_text = result.get('text', '')
        segments = result.get('segments', [])
        detected_language = result.get('language', 'unknown')

        # 计算统计信息
        duration = segments[-1]['end'] if segments else 0.0
        raw_word_count = len(raw_text)

        logger.info(f"转录完成: {raw_word_count}字，时长{duration:.1f}秒")

        # 自动清洗文本
        cleaned_text = raw_text
        if enable_cleaning:
            logger.info("开始自动清洗文本...")
            cleaned_text = clean_transcript(raw_text)
            cleaned_word_count = len(cleaned_text)
            logger.info(f"清洗完成: {raw_word_count} → {cleaned_word_count}字")
        else:
            cleaned_word_count = raw_word_count

        # 构建基础返回结果
        base_result = {
            'status': 'completed',
            'transcript': {
                'full_text': cleaned_text,
                'raw_text': raw_text,
                'segments': segments,
                'language': detected_language
            },
            'total': {
                '时长': duration,
                '原始字数': raw_word_count,
                '清洗后字数': cleaned_word_count
            }
        }

        # 提取量化指标（如果启用）
        if enable_metrics and cleaned_text:
            logger.info("开始提取量化指标...")
            metrics = extract_metrics(cleaned_text, segments=segments)
            base_result['metrics'] = metrics
            logger.info("量化指标提取完成")

        return base_result

    finally:
        # 清理临时音频文件
        if temp_audio and os.path.exists(temp_audio):
            try:
                os.remove(temp_audio)
                logger.info(f"已删除临时音频文件: {temp_audio}")
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")


def clean_transcript(text: str) -> str:
    """
    自动清洗转录文本

    清洗步骤：
    1. 去除口头禅（嗯、啊、那个等）
    2. 合并断句（去除不必要的换行）
    3. 修正明显错误（连续标点、多余空格）
    4. 保留有意义的停顿标记

    Args:
        text: 原始转录文本

    Returns:
        清洗后的文本
    """
    if not text:
        return text

    cleaned = text

    # 1. 去除口头禅
    for filler in FILLER_WORDS:
        # 匹配独立出现的口头禅（前后有标点或空格）
        pattern = r'(?<=[，。！？、\s])' + re.escape(filler) + r'(?=[，。！？、\s])'
        cleaned = re.sub(pattern, '', cleaned)
        # 匹配句首的口头禅
        pattern = r'^' + re.escape(filler) + r'(?=[，。！？、\s])'
        cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)

    # 2. 合并断句
    lines = cleaned.split('\n')
    merged_lines = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 如果行很短（<10字）且没有句号结尾，合并到buffer
        if len(line) < 10 and not line.endswith(('。', '！', '？')):
            buffer += line
        else:
            if buffer:
                merged_lines.append(buffer + line)
                buffer = ""
            else:
                merged_lines.append(line)

    if buffer:
        merged_lines.append(buffer)

    cleaned = ''.join(merged_lines)

    # 3. 修正明显错误
    cleaned = re.sub(r'([，。！？、])\1+', r'\1', cleaned)  # 去除连续标点
    cleaned = re.sub(r'\s+', ' ', cleaned)  # 去除多余空格
    cleaned = re.sub(r'\s+([，。！？、])', r'\1', cleaned)  # 去除标点前空格
    cleaned = cleaned.strip()

    return cleaned


def extract_metrics(text: str, segments: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    提取量化指标

    Args:
        text: 清洗后的文本
        segments: 转录片段列表（包含时间戳信息）

    Returns:
        {
            '专业名词': [...],
            '核心人物': [...],
            '特殊事件': [...],
            '文化分类': {...}
        }
    """
    metrics = {}

    # 1. 提取专业名词
    professional_terms = cultural_classifier.extract_professional_terms(text)
    metrics['专业名词'] = professional_terms[:20]

    # 2. 识别核心人物
    core_persons = _extract_core_persons(text)
    metrics['核心人物'] = core_persons

    # 3. 统计特殊事件
    special_events = _extract_special_events(text, segments=segments)
    metrics['特殊事件'] = special_events

    # 4. 文化分类
    cultural_tags = cultural_classifier.classify(text)
    metrics['文化分类'] = cultural_tags

    return metrics


# ==================== 私有辅助函数 ====================

def _extract_audio_from_video(video_path: str) -> str:
    """从视频中提取音频"""
    from moviepy.editor import VideoFileClip

    audio_path = video_path.rsplit('.', 1)[0] + '_audio.mp3'

    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path, logger=None)
        video.close()
        logger.info(f"音频提取完成: {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"音频提取失败: {e}")
        raise


def _transcribe_long_audio(
    audio_path: str,
    language: Optional[str] = None
) -> Dict[str, Any]:
    """分段处理长音频文件"""
    try:
        audio = AudioSegment.from_file(audio_path)
        total_duration_ms = len(audio)

        # 计算需要分多少段
        num_segments = (total_duration_ms + SEGMENT_DURATION_MS - 1) // SEGMENT_DURATION_MS
        logger.info(f"长音频将分为{num_segments}段处理")

        all_segments = []
        full_text = ""

        for i in range(num_segments):
            start_ms = i * SEGMENT_DURATION_MS
            end_ms = min((i + 1) * SEGMENT_DURATION_MS, total_duration_ms)

            # 提取分段
            segment_audio = audio[start_ms:end_ms]
            segment_path = f"{audio_path}_segment_{i}.mp3"
            segment_audio.export(segment_path, format="mp3")

            logger.info(f"处理第{i+1}/{num_segments}段...")

            # 转录分段
            result = transcription_service.transcribe(segment_path, language=language)

            # 调整时间戳（加上偏移）
            offset_seconds = start_ms / 1000.0
            for seg in result.get('segments', []):
                seg['start'] += offset_seconds
                seg['end'] += offset_seconds
                all_segments.append(seg)

            full_text += result.get('text', '')

            # 清理临时文件
            try:
                os.remove(segment_path)
            except OSError as e:
                logger.debug(f"临时文件删除失败: {segment_path}, {e}")
                pass

        return {
            'text': full_text,
            'segments': all_segments,
            'language': result.get('language', 'unknown')
        }

    except Exception as e:
        logger.error(f"长音频处理失败: {e}")
        raise


def _extract_core_persons(text: str) -> List[Dict[str, Any]]:
    """识别核心人物"""
    try:
        # 延迟导入 discovery_engine
        from app.core.discovery_engine import discovery_engine

        entities = discovery_engine.extract_entities(text)
        persons = [e for e in entities if e.get('type') == 'PERSON']

        # 统计人物提及次数
        person_counter = Counter([p['text'] for p in persons])

        # 构建核心人物列表
        core_persons = []
        for name, count in person_counter.most_common(10):
            # 简单提取动作（查找人名后的动词）
            actions = _extract_person_actions(text, name)
            core_persons.append({
                'name': name,
                'mentions': count,
                'actions': actions[:3]  # 最多3个动作
            })

        return core_persons

    except Exception as e:
        logger.warning(f"核心人物提取失败: {e}")
        return []


def _extract_person_actions(text: str, person_name: str) -> List[str]:
    """提取人物动作"""
    actions = []

    # 简单规则：查找"人名 + 动词"模式
    action_patterns = [
        f'{person_name}提出',
        f'{person_name}建议',
        f'{person_name}说',
        f'{person_name}认为',
        f'{person_name}表示',
    ]

    for pattern in action_patterns:
        if pattern in text:
            # 提取动作后的内容（最多20字）
            idx = text.find(pattern)
            action_text = text[idx:idx+20].replace(person_name, '').strip()
            if action_text:
                actions.append(action_text)

    return actions


def _extract_special_events(
    text: str,
    segments: Optional[List[Dict]] = None
) -> List[Dict[str, Any]]:
    """统计特殊事件"""
    # 特殊事件关键词
    event_keywords = [
        '签约', '流转', '保护', '传承', '发展',
        '建设', '改造', '搬迁', '拆迁', '征收',
        '会议', '讨论', '决定', '通过', '实施'
    ]

    events = []

    for keyword in event_keywords:
        if keyword in text:
            # 统计出现次数
            count = text.count(keyword)

            # 提取上下文（如果有segments）
            contexts = []
            if segments:
                for seg in segments:
                    if keyword in seg.get('text', ''):
                        contexts.append({
                            'text': seg['text'],
                            'time': seg.get('start', 0)
                        })

            events.append({
                'event': keyword,
                'count': count,
                'contexts': contexts[:3]  # 最多3个上下文
            })

    # 按出现次数排序
    events.sort(key=lambda x: x['count'], reverse=True)

    return events[:10]  # 返回前10个
