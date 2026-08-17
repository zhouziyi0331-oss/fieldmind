"""
TranscriptAgent - 转录专员

⚠️ 已废弃：此Agent将在v2.0中移除，请使用 app.tools.transcript.audio_transcript

职责：
1. 将音频/视频文件转换为文字（使用Whisper）
2. 自动清洗转录文本（去口头禅、合并断句、纠错）
3. 提取量化指标：专业名词、核心人物、特殊事件、文化分类
4. 长音频分段处理（>50MB自动切分）
"""

from typing import Dict, Any, List, Tuple
import logging
import os
import re
from collections import Counter
from pydub import AudioSegment

from app.services.agents.base_agent import AgentBase, AgentRole, AgentTask
from app.core.transcription import transcription_service
from app.services.cultural_classifier import cultural_classifier
from app.utils.deprecation import deprecated

logger = logging.getLogger(__name__)

# 长音频阈值（50MB）
LONG_AUDIO_THRESHOLD = 50 * 1024 * 1024
# 分段时长（10分钟）
SEGMENT_DURATION_MS = 10 * 60 * 1000


@deprecated(
    reason="旧Agent架构已被6-Agent v2替代",
    replacement="app.tools.transcript.audio_transcript",
    version="2.0"
)
class TranscriptAgent(AgentBase):
    """
    转录专员Agent

    能力：
    - 音频转文字（Whisper）
    - 视频提取音频后转文字
    - 支持多种音频格式（mp3, wav, m4a, ogg, flac等）
    - 生成带时间戳的转录文本
    - 自动清洗文本（去口头禅、合并断句）
    - 提取量化指标（专业名词、核心人物、特殊事件、文化分类）
    """

    # 口头禅列表
    FILLER_WORDS = [
        "嗯", "啊", "呃", "哦", "哎", "唉", "诶",
        "那个", "这个", "就是", "然后",
        "嗯嗯", "啊啊", "呃呃",
    ]

    @property
    def role(self) -> AgentRole:
        return AgentRole.TRANSCRIPT

    @property
    def name(self) -> str:
        return "转录专员"

    @property
    def description(self) -> str:
        return "负责将音频和视频文件转换为文字，自动清洗并提取量化指标"

    @property
    def capabilities(self) -> List[str]:
        return [
            "音频转文字（Whisper）",
            "视频音轨提取",
            "多语言支持",
            "时间戳标注",
            "自动文本清洗",
            "专业名词提取",
            "核心人物识别",
            "特殊事件统计",
            "文化分类（衣食住行在地）"
        ]

    def _initialize_tools(self):
        """初始化工具（discovery_engine 将在使用时延迟导入）"""
        self.tools = {
            'transcription_service': transcription_service,
            'cultural_classifier': cultural_classifier,
            # discovery_engine 在 _extract_core_persons() 中延迟导入
        }

    def _execute_task_impl(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行转录任务

        Args:
            task.input_data:
                - file_path: 音频/视频文件路径（必需）
                - file_type: 文件类型（可选）
                - language: 语言代码（可选，默认auto）
                - file_id: 文件ID（可选，用于关联数据库记录）
                - enable_metrics: 是否提取量化指标（默认True）

        Returns:
            {
                'status': 'completed',
                'transcript': {
                    'full_text': '清洗后的完整文本',
                    'raw_text': '原始转录文本',
                    'segments': [...]
                },
                'metrics': {
                    '专业名词': ['布依族', '土地流转', ...],
                    '核心人物': [
                        {'name': '王大爷', 'mentions': 12, 'actions': ['提出保护山歌']}
                    ],
                    '特殊事件': [
                        {'event': '土地流转签约', 'count': 3, 'contexts': [...]}
                    ],
                    '文化分类': {
                        '衣': ['蜡染', '刺绣'],
                        '食': ['糯米', '腊肉'],
                        ...
                    }
                },
                'total': {
                    '时长': 2400,
                    '原始字数': 3500,
                    '清洗后字数': 3200
                }
            }
        """
        file_path = task.input_data.get('file_path')
        file_type = task.input_data.get('file_type', 'audio')
        language = task.input_data.get('language', 'auto')
        file_id = task.input_data.get('file_id')
        enable_metrics = task.input_data.get('enable_metrics', True)

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
        if file_type in ['video', 'video/mp4', 'video/mov', 'video/avi']:
            logger.info("检测到视频文件，提取音频轨道...")
            audio_path = self._extract_audio_from_video(file_path)

        # 判断是否需要分段处理（大于50MB）
        is_long_audio = file_size > LONG_AUDIO_THRESHOLD

        # 调用Whisper转录
        try:
            if is_long_audio:
                logger.info(f"检测到长音频文件（{file_size_mb:.2f}MB），启用分段处理...")
                result = self._transcribe_long_audio(
                    audio_path,
                    language=language if language != 'auto' else None
                )
            else:
                result = self.tools['transcription_service'].transcribe(
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

            # 步骤2：自动清洗文本
            logger.info("开始自动清洗文本...")
            cleaned_text = self._clean_transcript(raw_text)
            cleaned_word_count = len(cleaned_text)
            logger.info(f"清洗完成: {raw_word_count} → {cleaned_word_count}字")

            # 清理临时音频文件（如果是从视频提取的）
            if audio_path != file_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                    logger.info(f"已删除临时音频文件: {audio_path}")
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {e}")

            # 构建基础返回结果
            base_result = {
                'status': 'completed',
                'file_id': file_id,
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

            # 步骤3：提取量化指标（如果启用）
            if enable_metrics and cleaned_text:
                logger.info("开始提取量化指标...")
                metrics = self._extract_metrics(cleaned_text, segments=segments)
                base_result['metrics'] = metrics
                logger.info("量化指标提取完成")

            # 步骤4：自动触发 KnowledgeAgent（如果启用）
            auto_trigger_knowledge = task.input_data.get('auto_trigger_knowledge', True)
            if auto_trigger_knowledge and cleaned_text:
                logger.info("🔄 自动触发 KnowledgeAgent 构建知识图谱...")
                knowledge_result = self._trigger_knowledge_agent(
                    text=cleaned_text,
                    segments=segments,
                    doc_id=file_id or "unknown",
                    existing_entities=metrics.get('核心人物', []) if enable_metrics else [],
                    db_session=task.input_data.get('db_session')
                )
                if knowledge_result:
                    base_result['knowledge_graph'] = knowledge_result
                    logger.info("✅ 知识图谱构建完成")

            return base_result

        except Exception as e:
            # 确保清理临时文件
            if audio_path != file_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError as remove_error:
                    logger.debug(f"临时文件删除失败: {audio_path}, {remove_error}")
                    pass
            raise

    def _clean_transcript(self, text: str) -> str:
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
        for filler in self.FILLER_WORDS:
            # 匹配独立出现的口头禅（前后有标点或空格）
            pattern = r'(?<=[，。！？、\s])' + re.escape(filler) + r'(?=[，。！？、\s])'
            cleaned = re.sub(pattern, '', cleaned)
            # 匹配句首的口头禅
            pattern = r'^' + re.escape(filler) + r'(?=[，。！？、\s])'
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE)

        # 2. 合并断句（去除单独成行的短句）
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
        # 去除连续的标点符号
        cleaned = re.sub(r'([，。！？、])\1+', r'\1', cleaned)
        # 去除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # 去除标点前的空格
        cleaned = re.sub(r'\s+([，。！？、])', r'\1', cleaned)
        # 去除首尾空格
        cleaned = cleaned.strip()

        return cleaned

    def _extract_metrics(self, text: str, segments: List[Dict] = None) -> Dict[str, Any]:
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
        professional_terms = self.tools['cultural_classifier'].extract_professional_terms(text)
        metrics['专业名词'] = professional_terms[:20]  # 最多返回20个

        # 2. 识别核心人物
        core_persons = self._extract_core_persons(text)
        metrics['核心人物'] = core_persons

        # 3. 统计特殊事件（传入segments以支持时间分析）
        special_events = self._extract_special_events(text, segments=segments)
        metrics['特殊事件'] = special_events

        # 4. 文化分类（衣食住行在地）
        cultural_classification = self.tools['cultural_classifier'].classify(text)
        metrics['文化分类'] = cultural_classification

        # 5. 计算置信度评分
        confidence_score = self._calculate_confidence(metrics)
        metrics['置信度'] = confidence_score

        return metrics

    def _extract_core_persons(self, text: str) -> List[Dict[str, Any]]:
        """
        提取核心人物

        Args:
            text: 文本

        Returns:
            [
                {
                    'name': '王大爷',
                    'mentions': 12,
                    'actions': ['提出保护山歌', '组织村民开会']
                }
            ]
        """
        try:
            from app.services.dynamic_discovery import DynamicDiscoveryEngine
            sentences = re.split(r'[。！？\n]', text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
            discovery_engine = DynamicDiscoveryEngine(enable_ner=False)
            entities = discovery_engine.extract_and_merge_entities(
                sentences,
                merge_threshold=0.85
            )
            persons = [e for e in entities if e.get('entity_type') == 'PERSON']
            core_persons = []
            for person in persons[:10]:
                name = person.get('canonical_name') or person.get('name', '')
                mentions = person.get('mention_count', 0)
                actions = self._extract_person_actions(name, sentences)
                core_persons.append({
                    'name': name,
                    'mentions': mentions,
                    'actions': actions[:3]
                })
            return core_persons
        except Exception as e:
            logger.warning(f"核心人物提取失败: {e}")
            return []

    def _extract_person_actions(self, person_name: str, sentences: List[str]) -> List[str]:
        """
        提取人物相关的动作

        Args:
            person_name: 人物名称
            sentences: 句子列表

        Returns:
            动作列表
        """
        actions = []

        # 常见动词列表
        action_verbs = [
            '说', '讲', '提出', '建议', '认为', '表示', '指出',
            '组织', '带领', '负责', '管理', '主持',
            '做', '干', '办', '搞', '弄',
            '修', '建', '造', '种', '养',
            '去', '来', '回', '走', '跑'
        ]

        for sentence in sentences:
            if person_name in sentence:
                # 查找句子中的动词
                for verb in action_verbs:
                    if verb in sentence:
                        # 提取动作短语（人名+动词+宾语）
                        # 简化版：直接截取句子片段
                        start_idx = sentence.find(person_name)
                        fragment = sentence[start_idx:start_idx+30]
                        actions.append(fragment)
                        break

        return list(set(actions))  # 去重

    def _extract_special_events(self, text: str, segments: List[Dict] = None) -> List[Dict[str, Any]]:
        """
        提取特殊事件（文档级别，单段音频内部分析）

        判定标准（满足任一即可）：
        1. 出现频次 >= 2次（单段内）
        2. 讨论覆盖率 >= 30%（占该段时长）
        3. 贯穿性：在前、中、后三个阶段都有提及

        注意：这是单文档级别的初步提取
        项目级别的跨文档合并由 ProjectAnalyzer 完成

        Args:
            text: 文本内容
            segments: 转录片段列表（包含时间戳信息）

        Returns:
            [
                {
                    'event': '土地流转',
                    'count': 5,
                    'coverage': 42.5,  # 讨论覆盖率（%）
                    'time_span': 'throughout',  # 时间跨度：beginning/middle/end/throughout
                    'contexts': ['...', '...'],
                    'timestamps': [12.5, 45.3, ...]  # 出现的时间点
                }
            ]
        """
        # 事件关键词（领域相关）
        event_keywords = [
            # 土地相关
            '土地流转', '流转', '征地', '拆迁', '搬迁', '土地承包',
            # 法律文书
            '签约', '合同', '协议', '文件',
            # 会议活动
            '村民大会', '开会', '讨论', '会议', '座谈',
            # 冲突纠纷
            '纠纷', '冲突', '矛盾', '争议', '问题',
            # 传统文化
            '节日', '庆典', '仪式', '祭祀', '习俗', '传统',
            '山歌', '民歌', '戏曲', '舞蹈', '手工艺',
            '蜡染', '刺绣', '织布', '银饰',
            # 基建项目
            '修路', '建房', '盖楼', '施工', '工程',
            # 人口流动
            '外出打工', '返乡', '进城', '务工',
            # 组织管理
            '选举', '换届', '村委', '干部',
            # 教育传承
            '教学', '培训', '传承', '学习',
            # 商业开发
            '旅游', '开发', '投资', '项目',
        ]

        # 计算文档总时长（用于覆盖率计算）
        total_duration = 0
        if segments:
            try:
                total_duration = max([seg.get('end', 0) for seg in segments])
            except (ValueError, TypeError) as e:
                logger.debug(f"计算总时长失败: {e}")
                total_duration = 0

        # 提取所有事件提及
        event_mentions = []
        sentences = re.split(r'[。！？\n]', text)
        current_time = 0

        # 如果有segments，建立句子到时间戳的映射
        sentence_timestamps = []
        if segments:
            text_length = len(text)
            for seg in segments:
                sentence_timestamps.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '')
                })

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue

            # 估算该句子的时间点
            estimated_time = 0
            if sentence_timestamps:
                # 在segments中找到包含这个句子的片段
                for seg in sentence_timestamps:
                    if sentence in seg['text']:
                        estimated_time = seg['start']
                        break

            for keyword in event_keywords:
                if keyword in sentence:
                    event_mentions.append({
                        'event': keyword,
                        'context': sentence[:80] + ('...' if len(sentence) > 80 else ''),
                        'timestamp': estimated_time,
                        'sentence_index': i
                    })

        # 按事件分组统计
        from collections import defaultdict
        event_groups = defaultdict(list)

        for mention in event_mentions:
            event_groups[mention['event']].append(mention)

        # 计算每个事件的多维度指标
        special_events = []
        sentence_count = len([s for s in sentences if len(s.strip()) >= 5])

        for event, mentions in event_groups.items():
            count = len(mentions)
            timestamps = [m['timestamp'] for m in mentions]
            contexts = [m['context'] for m in mentions]

            # 计算讨论覆盖率（基于句子数）
            unique_sentences = len(set([m['sentence_index'] for m in mentions]))
            coverage = (unique_sentences / sentence_count * 100) if sentence_count > 0 else 0

            # 判断时间跨度（前、中、后）
            time_span = 'single'
            if total_duration > 0 and timestamps:
                min_time = min(timestamps)
                max_time = max(timestamps)

                # 将时长分为三个阶段
                third = total_duration / 3

                has_beginning = any(t < third for t in timestamps)
                has_middle = any(third <= t < 2 * third for t in timestamps)
                has_end = any(t >= 2 * third for t in timestamps)

                stage_count = sum([has_beginning, has_middle, has_end])

                if stage_count >= 3:
                    time_span = 'throughout'  # 贯穿全程
                elif stage_count == 2:
                    time_span = 'distributed'  # 分布式
                else:
                    if has_beginning:
                        time_span = 'beginning'
                    elif has_middle:
                        time_span = 'middle'
                    elif has_end:
                        time_span = 'end'

            # 判定标准（满足任一即可）
            is_special = (
                count >= 2 or                    # 标准1：出现2次以上
                coverage >= 30 or                # 标准2：覆盖率≥30%
                time_span == 'throughout'        # 标准3：贯穿全程
            )

            if is_special:
                special_events.append({
                    'event': event,
                    'count': count,
                    'coverage': round(coverage, 1),
                    'time_span': time_span,
                    'contexts': contexts[:5],  # 最多保留5个上下文
                    'timestamps': timestamps[:5]
                })

        # 按综合重要性排序（频次×0.5 + 覆盖率×0.5）
        special_events.sort(
            key=lambda x: x['count'] * 0.5 + x['coverage'] * 0.5,
            reverse=True
        )

        return special_events[:15]  # 最多返回15个特殊事件

    def _calculate_confidence(self, metrics: Dict[str, Any]) -> float:
        """
        计算置信度评分

        评分标准：
        - 专业名词数量 (0-0.3)
        - 核心人物数量 (0-0.2)
        - 特殊事件数量 (0-0.2)
        - 文化分类覆盖度 (0-0.3)

        Args:
            metrics: 量化指标

        Returns:
            置信度分数 (0-1)
        """
        score = 0.0

        # 1. 专业名词（最多0.3分）
        term_count = len(metrics.get('专业名词', []))
        score += min(term_count / 20, 1.0) * 0.3

        # 2. 核心人物（最多0.2分）
        person_count = len(metrics.get('核心人物', []))
        score += min(person_count / 5, 1.0) * 0.2

        # 3. 特殊事件（最多0.2分）
        event_count = len(metrics.get('特殊事件', []))
        score += min(event_count / 5, 1.0) * 0.2

        # 4. 文化分类覆盖度（最多0.3分）
        cultural_dims = metrics.get('文化分类', {})
        coverage = len(cultural_dims) / 5.0  # 5个维度
        score += coverage * 0.3

        return round(score, 2)

    def _extract_audio_from_video(self, video_path: str) -> str:
        """
        从视频提取音频

        Args:
            video_path: 视频文件路径

        Returns:
            音频文件路径
        """
        from app.services.video_processor import VideoProcessor

        video_processor = VideoProcessor()

        try:
            audio_path = video_processor.extract_audio(video_path)
            logger.info(f"音频提取成功: {audio_path}")
            return audio_path
        except Exception as e:
            logger.error(f"音频提取失败: {e}")
            raise

    def _transcribe_long_audio(
        self,
        audio_path: str,
        language: str = None
    ) -> Dict[str, Any]:
        """
        分段处理长音频文件

        策略：
        1. 将音频按10分钟切分成多个片段
        2. 并行转录每个片段（如果资源允许）
        3. 合并所有片段的转录结果
        4. 调整时间戳以保持连续性

        Args:
            audio_path: 音频文件路径
            language: 语言代码

        Returns:
            合并后的转录结果（格式同 transcribe）
        """
        try:
            logger.info(f"加载长音频文件: {audio_path}")
            audio = AudioSegment.from_file(audio_path)
            total_duration_ms = len(audio)
            total_duration_min = total_duration_ms / 1000 / 60

            logger.info(f"音频总时长: {total_duration_min:.1f}分钟")

            # 计算需要切分的段数
            num_segments = (total_duration_ms + SEGMENT_DURATION_MS - 1) // SEGMENT_DURATION_MS
            logger.info(f"将切分为 {num_segments} 个片段进行处理")

            # 存储所有片段的转录结果
            all_segments = []
            all_text_parts = []
            temp_files = []

            # 逐段处理
            for i in range(num_segments):
                start_ms = i * SEGMENT_DURATION_MS
                end_ms = min((i + 1) * SEGMENT_DURATION_MS, total_duration_ms)

                logger.info(f"处理片段 {i+1}/{num_segments} ({start_ms/1000/60:.1f}-{end_ms/1000/60:.1f}分钟)...")

                # 切分音频片段
                segment_audio = audio[start_ms:end_ms]

                # 保存临时文件
                temp_path = audio_path.replace('.wav', f'_segment_{i}.wav')
                segment_audio.export(temp_path, format='wav')
                temp_files.append(temp_path)

                # 转录该片段
                try:
                    segment_result = self.tools['transcription_service'].transcribe(
                        temp_path,
                        language=language
                    )

                    # 调整时间戳（加上片段起始时间）
                    time_offset = start_ms / 1000.0
                    for seg in segment_result.get('segments', []):
                        seg['start'] += time_offset
                        seg['end'] += time_offset
                        seg['id'] = len(all_segments)
                        all_segments.append(seg)

                    all_text_parts.append(segment_result.get('text', ''))

                    logger.info(f"片段 {i+1}/{num_segments} 转录完成")

                except Exception as e:
                    logger.error(f"片段 {i+1} 转录失败: {e}")
                    # 继续处理其他片段
                    continue

                finally:
                    # 立即清理临时文件
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except OSError as e:
                        logger.debug(f"临时文件删除失败: {temp_path}, {e}")
                        pass

            # 合并结果
            merged_result = {
                'text': ' '.join(all_text_parts),
                'segments': all_segments,
                'language': language or 'zh'
            }

            logger.info(f"长音频转录完成: 共 {len(all_segments)} 个片段")

            return merged_result

        except Exception as e:
            logger.error(f"长音频分段处理失败: {e}")
            # 清理所有临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except OSError as remove_error:
                    logger.debug(f"临时文件删除失败: {temp_file}, {remove_error}")
                    pass
            raise

    def transcribe_file(
        self,
        file_path: str,
        file_type: str = 'audio',
        language: str = 'auto',
        file_id: int = None,
        enable_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        便捷方法：转录文件

        Args:
            file_path: 文件路径
            file_type: 文件类型（'audio' 或 'video'）
            language: 语言代码
            file_id: 文件ID（可选）
            enable_metrics: 是否提取量化指标

        Returns:
            转录结果字典
        """
        import uuid

        task = AgentTask(
            task_id=f"transcript_{uuid.uuid4().hex[:8]}",
            task_type="transcribe_file",
            input_data={
                'file_path': file_path,
                'file_type': file_type,
                'language': language,
                'file_id': file_id,
                'enable_metrics': enable_metrics
            }
        )

        result = self.execute_task(task)

        if not result.success:
            raise Exception(f"转录失败: {result.errors}")

        return result.output_data

    def _trigger_knowledge_agent(
        self,
        text: str,
        segments: List[Dict],
        doc_id: str,
        existing_entities: List[Dict],
        db_session=None
    ) -> Dict[str, Any]:
        """
        自动触发 KnowledgeAgent 构建知识图谱

        Args:
            text: 清洗后的文本
            segments: 带时间戳的segments
            doc_id: 文档ID
            existing_entities: 从metrics提取的核心人物列表
            db_session: 数据库会话（可选）

        Returns:
            知识图谱构建结果
        """
        try:
            # 动态导入 KnowledgeAgent（避免循环依赖）
            from app.services.agents.knowledge_agent import KnowledgeAgent
            import asyncio

            logger.info("   📊 初始化 KnowledgeAgent...")
            knowledge_agent = KnowledgeAgent()

            # 转换 existing_entities 格式（从 metrics 的人物列表）
            formatted_entities = []
            if existing_entities:
                for person in existing_entities:
                    formatted_entities.append({
                        'name': person.get('name', ''),
                        'entity_type': 'PERSON',
                        'mention_count': person.get('mentions', 1),
                        'canonical_name': person.get('name', '')
                    })

            # 构建输入
            task_input = {
                'text': text,
                'segments': segments,
                'doc_id': doc_id,
                'existing_entities': formatted_entities,
                'enable_llm': True,  # 启用 LLM 辅助提取
                'db_session': db_session
            }

            # 执行知识图谱构建（同步方式）
            logger.info("   🔨 开始构建知识图谱...")

            # 如果在异步上下文中，直接await；否则创建新事件循环
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 已在异步上下文中
                    result = asyncio.create_task(knowledge_agent.execute(task_input))
                    # 这里不能直接await，需要返回future或使用其他方式
                    # 简化处理：使用同步包装
                    result = asyncio.run_coroutine_threadsafe(
                        knowledge_agent.execute(task_input),
                        loop
                    ).result(timeout=300)
                else:
                    result = asyncio.run(knowledge_agent.execute(task_input))
            except RuntimeError:
                # 没有事件循环，创建新的
                result = asyncio.run(knowledge_agent.execute(task_input))

            logger.info(f"   ✅ 知识图谱构建完成: {result.get('实体数', 0)}个实体, {result.get('关系数', 0)}个关系")

            return {
                'entities': result.get('实体数', 0),
                'relations': result.get('关系数', 0),
                'co_occurrences': result.get('共现数', 0),
                'communities': result.get('社区数', 0),
                'graph_file': result.get('图谱文件', ''),
                'success': True
            }

        except Exception as e:
            logger.error(f"   ❌ 触发 KnowledgeAgent 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
