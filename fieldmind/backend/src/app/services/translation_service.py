"""
翻译服务 - 中英文互译
支持自动语言检测和批量翻译
"""

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


class TranslationService:
    """翻译服务 - 主要支持中英文互译"""

    def __init__(self):
        self.name = "TranslationService"
        self.translator = None
        self._load_translator()

    def _load_translator(self):
        """加载翻译引擎"""
        try:
            # 尝试使用Google翻译（googletrans）
            from googletrans import Translator
            self.translator = Translator()
            logger.info("✅ TranslationService: 使用googletrans")
        except ImportError:
            logger.warning("⚠️  googletrans未安装，尝试使用deep_translator")
            try:
                from deep_translator import GoogleTranslator
                self.translator = GoogleTranslator
                logger.info("✅ TranslationService: 使用deep_translator")
            except ImportError:
                logger.warning("⚠️  翻译库未安装，翻译功能将不可用")
                self.translator = None

    def detect_language(self, text: str) -> str:
        """
        检测文本语言

        Returns:
            'zh' (中文) | 'en' (英文) | 'other'
        """
        if not text or len(text.strip()) == 0:
            return "unknown"

        # 统计中文字符
        chinese_chars = len(re.findall(r'[一-鿿]', text))
        total_chars = len(text.strip())

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars

        # 如果中文字符超过30%，认为是中文
        if chinese_ratio > 0.3:
            return "zh"
        # 否则认为是英文
        elif chinese_ratio < 0.1:
            return "en"
        else:
            # 混合文本，按主要语言判断
            return "zh" if chinese_ratio > 0.15 else "en"

    def translate_to_chinese(self, text: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        """
        翻译为中文

        Args:
            text: 原文
            source_lang: 源语言（如果为None，自动检测）

        Returns:
            {
                "translated_text": "翻译后的中文",
                "original_text": "原文",
                "source_language": "en",
                "target_language": "zh",
                "was_translated": True/False
            }
        """
        if not text or len(text.strip()) == 0:
            return {
                "translated_text": "",
                "original_text": text,
                "source_language": "unknown",
                "target_language": "zh",
                "was_translated": False
            }

        # 检测语言
        if source_lang is None:
            source_lang = self.detect_language(text)

        # 如果已经是中文，不需要翻译
        if source_lang == "zh":
            return {
                "translated_text": text,
                "original_text": text,
                "source_language": "zh",
                "target_language": "zh",
                "was_translated": False
            }

        # 执行翻译
        if self.translator is None:
            logger.warning("翻译服务不可用，返回原文")
            return {
                "translated_text": text,
                "original_text": text,
                "source_language": source_lang,
                "target_language": "zh",
                "was_translated": False,
                "error": "翻译服务不可用"
            }

        try:
            # 使用googletrans
            if hasattr(self.translator, 'translate'):
                result = self.translator.translate(text, src=source_lang, dest='zh-cn')
                translated_text = result.text
                detected_lang = result.src
            # 使用deep_translator
            else:
                translator = self.translator(source=source_lang, target='zh-CN')
                translated_text = translator.translate(text)
                detected_lang = source_lang

            logger.info(f"✅ 翻译完成: {source_lang} -> zh ({len(text)} 字符)")

            return {
                "translated_text": translated_text,
                "original_text": text,
                "source_language": detected_lang,
                "target_language": "zh",
                "was_translated": True
            }

        except Exception as e:
            logger.error(f"❌ 翻译失败: {e}")
            return {
                "translated_text": text,
                "original_text": text,
                "source_language": source_lang,
                "target_language": "zh",
                "was_translated": False,
                "error": str(e)
            }

    def translate_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        翻译多个文本段落（批量处理）

        Args:
            segments: [{"text": "...", "source": {...}}, ...]

        Returns:
            翻译后的segments，每个增加了translated_text字段
        """
        translated_segments = []

        for segment in segments:
            text = segment.get("text", "")

            # 翻译
            result = self.translate_to_chinese(text)

            # 添加翻译结果
            new_segment = {
                **segment,
                "translated_text": result["translated_text"],
                "original_text": result["original_text"],
                "was_translated": result["was_translated"],
                "source_language": result["source_language"]
            }

            translated_segments.append(new_segment)

        return translated_segments

    def should_translate(self, text: str) -> bool:
        """
        判断文本是否需要翻译（非中文才需要）

        Returns:
            True: 需要翻译
            False: 不需要翻译（已经是中文）
        """
        lang = self.detect_language(text)
        return lang != "zh"
