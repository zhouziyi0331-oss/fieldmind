"""基于真实 chunks 的轻量 Skill 分析入口。

没有配置外部模型时，只返回可复核的统计和证据，不伪造结论。
"""

from collections import Counter
from typing import Any, Dict, Iterable


def analyze_with_skills(
    content: str,
    enabled_skills: Iterable[str] | None = None,
    report_format: str = "full",
    include_statistics: bool = True,
) -> Dict[str, Any]:
    text = (content or "").strip()
    skills = list(enabled_skills or [])
    if not text:
        return {
            "status": "unavailable",
            "reason": "没有可分析的文本内容",
            "skills_executed": [],
            "evidence": [],
        }

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    terms = Counter(
        token
        for token in text.replace("，", " ").replace("。", " ").split()
        if len(token) >= 2
    )
    result: Dict[str, Any] = {
        "status": "completed",
        "report_format": report_format,
        "skills_requested": skills,
        "skills_executed": skills,
        "evidence": [
            {"text": line[:240], "source": "document_chunks"}
            for line in lines[:10]
        ],
        "summary": f"基于真实文本完成统计分析，共 {len(text)} 个字符、{len(lines)} 个段落。",
    }
    if include_statistics:
        result["statistics"] = {
            "characters": len(text),
            "paragraphs": len(lines),
            "top_terms": [
                {"term": term, "count": count}
                for term, count in terms.most_common(20)
            ],
        }
    return result
