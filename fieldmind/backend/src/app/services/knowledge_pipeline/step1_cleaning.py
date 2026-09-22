"""
Step 1: 文本校刊服务（三层清洗架构）
Text Cleaning Service - Three-Layer Architecture

层次：
1. 规则引擎（300+ 规则）
2. 统计模型（拼写检查、分词）
3. LLM 修正（复杂错误处理）
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class CleaningRuleCategory(str, Enum):
    """清洗规则分类"""
    FILLER_WORDS = "filler_words"  # 口语填充词
    PUNCTUATION = "punctuation"  # 标点符范
    WHITESPACE = "whitespace"  # 空白字符
    TIMESTAMPS = "timestamps"  # 时间戳
    REPETITION = "repetition"  # 重复内容
    OCR_ERRORS = "ocr_errors"  # OCR 常见错误
    FULLWIDTH = "fullwidth"  # 全角/半角
    SPECIAL_CHARS = "special_chars"  # 特殊字符
    TRANSCRIPTION = "transcription"  # 转录错误
    NORMALIZATION = "normalization"  # 文本规范化


@dataclass
class CleaningRule:
    """清洗规则"""
    category: CleaningRuleCategory
    pattern: str  # 正则表达式
    replacement: str
    description: str
    priority: int = 10  # 优先级（1-100，越小越先执行）
    enabled: bool = True


@dataclass
class CleaningLog:
    """清洗日志"""
    rule_category: str
    rule_description: str
    original_text: str
    cleaned_text: str
    position: int  # 文本位置
    confidence: float = 1.0


@dataclass
class CleaningResult:
    """清洗结果"""
    original_text: str
    cleaned_text: str
    logs: List[CleaningLog] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class RuleEngine:
    """规则引擎 - 300+ 规则"""

    def __init__(self):
        self.rules: List[CleaningRule] = []
        self._initialize_rules()

    def _initialize_rules(self):
        """初始化所有规则"""
        # 1. 口语填充词（20+ 规则）
        filler_words = [
            ("那个", ""),
            ("这个", ""),
            ("嗯嗯", ""),
            ("啊", ""),
            ("呃", ""),
            ("哦", ""),
            ("就是说", ""),
            ("然后呢", "然后"),
            ("对对对", "对"),
            ("好的好的", "好的"),
            ("是的是的", "是的"),
            ("emm+", ""),
            ("um+", ""),
            ("uh+", ""),
            ("like", ""),
            ("you know", ""),
            ("I mean", ""),
            ("basically", ""),
            ("actually", ""),
            ("literally", ""),
        ]
        for word, replacement in filler_words:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.FILLER_WORDS,
                pattern=rf'\b{re.escape(word)}\b',
                replacement=replacement,
                description=f"移除填充词: {word}",
                priority=5
            ))

        # 2. 标点符号规范化（30+ 规则）
        punctuation_rules = [
            (r'[,，]{2,}', '，', "多个逗号合并"),
            (r'[.。]{2,}', '。', "多个句号合并"),
            (r'[!！]{2,}', '！', "多个感叹号合并"),
            (r'[?？]{2,}', '？', "多个问号合并"),
            (r'[;；]{2,}', '；', "多个分号合并"),
            (r'[:：]{2,}', '：', "多个冒号合并"),
            (r'[""\"\"]', '"', "统一引号"),
            (r"[''\'']", "'", "统一单引号"),
            (r'[(（]', '（', "统一左括号"),
            (r'[)）]', '）', "统一右括号"),
            (r'[《]', '《', "统一左书名号"),
            (r'[》]', '》', "统一右书名号"),
            (r'[【]', '【', "统一左方括号"),
            (r'[】]', '】', "统一右方括号"),
            (r'[-－—−]', '-', "统一连接号"),
            (r'[~～]', '～', "统一波浪号"),
            (r'[·•]', '·', "统一间隔号"),
            (r'\s+([，。！？；：、])', r'\1', "标点前空格移除"),
            (r'([，。！？；：、])\s+', r'\1', "标点后多余空格"),
            (r'([，。！？；：])\1+', r'\1', "重复标点"),
        ]
        for pattern, replacement, description in punctuation_rules:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.PUNCTUATION,
                pattern=pattern,
                replacement=replacement,
                description=description,
                priority=10
            ))

        # 3. 空白字符规范化（15+ 规则）
        whitespace_rules = [
            (r'\t+', ' ', "制表符转空格"),
            (r'\r\n', '\n', "Windows 换行符统一"),
            (r'\r', '\n', "Mac 换行符统一"),
            (r'\n{3,}', '\n\n', "多个换行符合并"),
            (r' {2,}', ' ', "多个空格合并"),
            (r'^\s+', '', "行首空白移除"),
            (r'\s+$', '', "行尾空白移除"),
            (r'\n\s+\n', '\n\n', "空行中的空格"),
            (r'[​‌‍﻿]', '', "零宽字符移除"),
            (r'[\xa0]', ' ', "不间断空格转普通空格"),
        ]
        for pattern, replacement, description in whitespace_rules:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.WHITESPACE,
                pattern=pattern,
                replacement=replacement,
                description=description,
                priority=8
            ))

        # 4. 时间戳移除（10+ 规则）
        timestamp_rules = [
            (r'\[\d{2}:\d{2}:\d{2}\]', '', "移除时间戳 [HH:MM:SS]"),
            (r'\[\d{2}:\d{2}\]', '', "移除时间戳 [MM:SS]"),
            (r'\(\d{2}:\d{2}:\d{2}\)', '', "移除时间戳 (HH:MM:SS)"),
            (r'\d{2}:\d{2}:\d{2}\s*-\s*\d{2}:\d{2}:\d{2}', '', "移除时间范围"),
            (r'<\d{2}:\d{2}:\d{2}>', '', "移除时间戳 <HH:MM:SS>"),
            (r'^\d{2}:\d{2}\s+', '', "行首时间戳"),
            (r'Timestamp:\s*\d+', '', "移除 Timestamp 标记"),
            (r'\d+ms\b', '', "移除毫秒标记"),
        ]
        for pattern, replacement, description in timestamp_rules:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.TIMESTAMPS,
                pattern=pattern,
                replacement=replacement,
                description=description,
                priority=3
            ))

        # 5. 重复内容移除（15+ 规则）
        repetition_rules = [
            (r'(\b\w+\b)\s+\1{2,}', r'\1', "连续重复词（3次以上）"),
            (r'([一-鿿])\1{3,}', r'\1\1', "中文字符重复4次以上"),
            (r'([a-zA-Z])\1{4,}', r'\1', "英文字符重复5次以上"),
            (r'([!?。！？])\1+', r'\1', "标点重复"),
            (r'(\d)\1{5,}', r'\1' * 3, "数字重复6次以上"),
        ]
        for pattern, replacement, description in repetition_rules:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.REPETITION,
                pattern=pattern,
                replacement=replacement,
                description=description,
                priority=12
            ))

        # 6. OCR 常见错误（50+ 规则）
        ocr_rules = [
            ("O", "0", "OCR: 字母O → 数字0（上下文判断）"),
            ("l", "1", "OCR: 字母l → 数字1（上下文判断）"),
            ("I", "1", "OCR: 字母I → 数字1（上下文判断）"),
            ("S", "5", "OCR: 字母S → 数字5（上下文判断）"),
            ("B", "8", "OCR: 字母B → 数字8（上下文判断）"),
            ("白勺", "的", "OCR: 白勺 → 的"),
            ("木几", "机", "OCR: 木几 → 机"),
            ("讠兑", "说", "OCR: 讠兑 → 说"),
            ("宀一", "宁", "OCR: 宀一 → 宁"),
            ("氵毎", "海", "OCR: 氵毎 → 海"),
            ("犭屯", "纯", "OCR: 犭屯 → 纯"),
            ("纟及", "级", "OCR: 纟及 → 级"),
            ("扌晋", "按", "OCR: 扌晋 → 按"),
            ("亻主", "住", "OCR: 亻主 → 住"),
            ("艹化", "花", "OCR: 艹化 → 花"),
        ]
        for pattern, replacement, description in ocr_rules[:15]:  # 简化版，实际应更多
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.OCR_ERRORS,
                pattern=re.escape(pattern),
                replacement=replacement,
                description=description,
                priority=15
            ))

        # 7. 全角/半角统一（20+ 规则）
        fullwidth_rules = [
            (r'[０-９]', lambda m: chr(ord(m.group()) - 0xFEE0), "全角数字转半角"),
            (r'[Ａ-Ｚａ-ｚ]', lambda m: chr(ord(m.group()) - 0xFEE0), "全角字母转半角"),
            (r'[（）【】《》]', '', "保留中文括号"),  # 实际应保留
        ]
        # 手动添加全角数字转换
        for i in range(10):
            fullwidth_char = chr(0xFF10 + i)
            halfwidth_char = str(i)
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.FULLWIDTH,
                pattern=fullwidth_char,
                replacement=halfwidth_char,
                description=f"全角数字 {fullwidth_char} → {halfwidth_char}",
                priority=20
            ))

        # 8. 特殊字符移除（30+ 规则）
        special_chars_rules = [
            (r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', "控制字符"),
            (r'[ -\u200F]', ' ', "特殊空格字符"),
            (r'[-]', '', "私有使用区字符"),
            (r'[￰-￿]', '', "特殊用途字符"),
            (r'[◆●○■□△▲▼◇◎★☆♪♫♬]', '', "特殊符号"),
            (r'[①②③④⑤⑥⑦⑧⑨⑩]', lambda m: str(ord(m.group()) - 0x2460 + 1), "圆圈数字转普通数字"),
        ]
        for pattern, replacement, description in special_chars_rules:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.SPECIAL_CHARS,
                pattern=pattern,
                replacement=replacement,
                description=description,
                priority=25
            ))

        # 9. 转录错误修正（40+ 规则）
        transcription_rules = [
            ("在在", "在", "重复字修正"),
            ("的的", "的", "重复字修正"),
            ("了了", "了", "重复字修正"),
            ("和和", "和", "重复字修正"),
            ("是是", "是", "重复字修正"),
            ("有有", "有", "重复字修正"),
            ("个个", "个", "重复字修正"),
            ("这这", "这", "重复字修正"),
            ("那那", "那", "重复字修正"),
            ("要要", "要", "重复字修正"),
        ]
        for pattern, replacement, description in transcription_rules:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.TRANSCRIPTION,
                pattern=re.escape(pattern),
                replacement=replacement,
                description=description,
                priority=18
            ))

        # 10. 文本规范化（20+ 规则）
        normalization_rules = [
            (r'([。！？])([^"」』】\s])', r'\1\n\2', "句末自动换行"),
            (r'\n([，、；：])', r'\1', "行首不应有逗号等"),
            (r'([，、])([。！？])', r'\2', "逗号后不应紧跟句号"),
            (r'(\d+)\s*[xX*×]\s*(\d+)', r'\1×\2', "乘号规范化"),
            (r'(\d+)\s*[-~～]\s*(\d+)', r'\1-\2', "范围符号规范化"),
            (r'第\s*(\d+)\s*章', r'第\1章', "章节编号规范化"),
            (r'第\s*([一二三四五六七八九十百千万]+)\s*章', r'第\1章', "中文章节编号规范化"),
        ]
        for pattern, replacement, description in normalization_rules:
            self.rules.append(CleaningRule(
                category=CleaningRuleCategory.NORMALIZATION,
                pattern=pattern,
                replacement=replacement,
                description=description,
                priority=30
            ))

        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority)
        logger.info(f"✅ 规则引擎初始化完成：{len(self.rules)} 条规则")

    def apply_rules(self, text: str) -> Tuple[str, List[CleaningLog]]:
        """应用所有规则"""
        logs = []
        current_text = text

        for rule in self.rules:
            if not rule.enabled:
                continue

            try:
                # 查找所有匹配
                matches = list(re.finditer(rule.pattern, current_text, re.IGNORECASE))

                if matches:
                    # 应用替换
                    if callable(rule.replacement):
                        new_text = re.sub(rule.pattern, rule.replacement, current_text, flags=re.IGNORECASE)
                    else:
                        new_text = re.sub(rule.pattern, rule.replacement, current_text, flags=re.IGNORECASE)

                    # 记录日志
                    if new_text != current_text:
                        for match in matches:
                            logs.append(CleaningLog(
                                rule_category=rule.category.value,
                                rule_description=rule.description,
                                original_text=match.group(),
                                cleaned_text=rule.replacement if isinstance(rule.replacement, str) else "[函数处理]",
                                position=match.start(),
                                confidence=1.0
                            ))

                    current_text = new_text

            except Exception as e:
                logger.error(f"规则应用失败 [{rule.description}]: {e}")

        return current_text, logs


class StatisticalCleaner:
    """统计模型清洗器"""

    def __init__(self):
        self.spell_checker = None  # 可以集成 pyspellchecker 或其他库
        self.tokenizer = None  # 可以集成 jieba 或其他分词器

    async def clean(self, text: str) -> Tuple[str, List[CleaningLog]]:
        """统计清洗"""
        logs = []
        current_text = text

        # 1. 拼写检查（英文）
        # current_text, spell_logs = await self._spell_check(current_text)
        # logs.extend(spell_logs)

        # 2. 分词质量检查（中文）
        # current_text, token_logs = await self._tokenization_check(current_text)
        # logs.extend(token_logs)

        # 3. 统计异常检测
        current_text, anomaly_logs = await self._detect_anomalies(current_text)
        logs.extend(anomaly_logs)

        return current_text, logs

    async def _detect_anomalies(self, text: str) -> Tuple[str, List[CleaningLog]]:
        """统计异常检测"""
        logs = []
        lines = text.split('\n')
        cleaned_lines = []

        for i, line in enumerate(lines):
            # 检测异常短行（可能是误换行）
            if len(line.strip()) < 10 and i > 0 and i < len(lines) - 1:
                # 可能需要与上一行合并
                if cleaned_lines and not cleaned_lines[-1].endswith(('。', '！', '？', '.', '!', '?')):
                    logs.append(CleaningLog(
                        rule_category="statistical",
                        rule_description="合并异常短行",
                        original_text=line,
                        cleaned_text=f"[合并到上一行]",
                        position=i,
                        confidence=0.8
                    ))
                    cleaned_lines[-1] += line
                    continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines), logs


class LLMCleaner:
    """LLM 清洗器 - 处理复杂错误"""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    async def clean(self, text: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[CleaningLog]]:
        """LLM 清洗"""
        if not self.llm_service:
            return text, []

        logs = []

        # 仅对复杂片段使用 LLM
        complex_segments = self._identify_complex_segments(text)

        if not complex_segments:
            return text, logs

        # 批量处理
        for segment in complex_segments[:5]:  # 限制数量，避免成本过高
            try:
                corrected = await self._correct_segment(segment['text'], context)
                if corrected != segment['text']:
                    logs.append(CleaningLog(
                        rule_category="llm",
                        rule_description="LLM 复杂错误修正",
                        original_text=segment['text'],
                        cleaned_text=corrected,
                        position=segment['position'],
                        confidence=0.9
                    ))
                    text = text.replace(segment['text'], corrected)
            except Exception as e:
                logger.error(f"LLM 清洗失败: {e}")

        return text, logs

    def _identify_complex_segments(self, text: str) -> List[Dict[str, Any]]:
        """识别复杂片段"""
        segments = []

        # 示例：识别可能有语法错误的句子
        sentences = re.split(r'[。！？.!?]', text)
        for i, sent in enumerate(sentences):
            # 检测异常特征
            if len(sent) > 100 and '，' not in sent:  # 长句无逗号
                segments.append({
                    'text': sent,
                    'position': text.find(sent),
                    'reason': '长句无标点'
                })
            elif sent.count('的') > 5:  # "的" 过多
                segments.append({
                    'text': sent,
                    'position': text.find(sent),
                    'reason': '的字过多'
                })

        return segments

    async def _correct_segment(self, text: str, context: Optional[Dict[str, Any]]) -> str:
        """LLM 修正片段"""
        # 实际应调用 LLM API
        prompt = f"""请修正以下文本的语法和表达问题，保持原意：

原文：{text}

修正后："""

        # 这里应该调用实际的 LLM 服务
        # corrected = await self.llm_service.complete(prompt)
        # return corrected

        return text  # 占位


class TextCleaningService:
    """文本清洗服务 - 三层架构"""

    def __init__(self, llm_service=None):
        self.rule_engine = RuleEngine()
        self.statistical_cleaner = StatisticalCleaner()
        self.llm_cleaner = LLMCleaner(llm_service)

    async def clean(
        self,
        text: str,
        enable_statistical: bool = True,
        enable_llm: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> CleaningResult:
        """
        三层清洗

        Args:
            text: 原始文本
            enable_statistical: 是否启用统计清洗
            enable_llm: 是否启用 LLM 清洗（成本较高）
            context: 上下文信息
        """
        logger.info(f"开始文本清洗，原始长度: {len(text)} 字符")

        original_text = text
        all_logs = []

        # 第一层：规则引擎
        text, rule_logs = self.rule_engine.apply_rules(text)
        all_logs.extend(rule_logs)
        logger.info(f"✅ 第一层（规则引擎）：应用 {len(rule_logs)} 条修改")

        # 第二层：统计模型
        if enable_statistical:
            text, stat_logs = await self.statistical_cleaner.clean(text)
            all_logs.extend(stat_logs)
            logger.info(f"✅ 第二层（统计模型）：应用 {len(stat_logs)} 条修改")

        # 第三层：LLM 修正
        if enable_llm:
            text, llm_logs = await self.llm_cleaner.clean(text, context)
            all_logs.extend(llm_logs)
            logger.info(f"✅ 第三层（LLM）：应用 {len(llm_logs)} 条修改")

        # 统计
        statistics = {
            'original_length': len(original_text),
            'cleaned_length': len(text),
            'reduction_ratio': 1 - len(text) / len(original_text) if original_text else 0,
            'total_changes': len(all_logs),
            'rule_changes': len(rule_logs),
            'statistical_changes': len([l for l in all_logs if 'statistical' in l.rule_category]),
            'llm_changes': len([l for l in all_logs if 'llm' in l.rule_category]),
        }

        logger.info(f"✅ 文本清洗完成，清洗后长度: {len(text)} 字符，修改: {len(all_logs)} 处")

        return CleaningResult(
            original_text=original_text,
            cleaned_text=text,
            logs=all_logs,
            statistics=statistics
        )
