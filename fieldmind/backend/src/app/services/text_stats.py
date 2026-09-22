"""统一文本统计工具。"""

from __future__ import annotations

import regex as re
import jieba


def count_words(text: str) -> int:
    """对中英混合文本做更稳的词/字计数。"""
    if not text:
        return 0
    cleaned = text.strip()
    if not cleaned:
        return 0

    has_chinese = bool(re.search(r"\p{IsHan}", cleaned))
    has_latin = bool(re.search(r"[A-Za-z]", cleaned))

    if has_chinese and not has_latin:
        tokens = [token.strip() for token in jieba.cut(cleaned) if token.strip()]
        return len(tokens) if tokens else len(cleaned)

    tokens = re.findall(r"\p{IsHan}+|[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", cleaned)
    return len(tokens) if tokens else len(cleaned.split())

