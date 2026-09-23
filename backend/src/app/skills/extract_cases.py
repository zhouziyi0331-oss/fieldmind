"""
提取案例 Skill - 基于关键词匹配
"""
from typing import Dict, Any, List
import re


class ExtractCasesSkill:
    """
    案例提取Skill

    方法论：Keyword Matching + Quality Scoring
    - 识别案例标识词
    - 提取结构化信息（背景、行动、结果）
    - 质量评分
    - 可复用性评估
    """

    METADATA = {
        "name": "extract_cases",
        "version": "1.0.0",
        "type": "pattern_matching",
        "output_type": "案例"
    }

    # 案例标识关键词
    CASE_KEYWORDS = [
        "案例", "例子", "实例", "事例", "故事",
        "经历", "经验", "教训",
        "曾经", "有一次", "那时候",
        "case", "example", "instance", "story"
    ]

    # BAR结构关键词
    BACKGROUND_KEYWORDS = ["背景", "当时", "情况", "环境", "问题"]
    ACTION_KEYWORDS = ["做了", "采取", "实施", "行动", "方法", "措施"]
    RESULT_KEYWORDS = ["结果", "效果", "成果", "收获", "影响", "教训"]

    def __init__(self, db_session):
        self.db = db_session

    def extract(self, chunks: List[Dict[str, Any]],
                entities: List[Dict[str, Any]],
                relations: List[Dict[str, Any]],
                events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行案例提取

        参数:
            chunks: 文本块列表
            entities: 实体列表
            relations: 关系列表
            events: 事件列表

        返回:
            案例列表，每个包含：
            - content: 案例完整描述
            - structure: BAR结构（Background, Action, Result）
            - quality_score: 质量分数
            - reusability: 可复用性评估
            - credibility: 可信度
            - confidence: 置信度
            - source_chunks: 来源块ID列表
        """
        cases = []

        # 遍历每个chunk寻找案例
        for chunk in chunks:
            chunk_id = chunk.get("id")
            text = chunk.get("content", "")

            # 检查是否包含案例关键词
            has_case_keyword = any(kw in text for kw in self.CASE_KEYWORDS)

            if has_case_keyword:
                # 提取BAR结构
                structure = self._extract_bar_structure(text)

                # 计算质量分数
                quality_score = self._calculate_quality_score(text, structure)

                # 评估可复用性
                reusability = self._assess_reusability(structure, quality_score)

                # 只保留质量分数>0.5的案例
                if quality_score > 0.5:
                    case = {
                        "content": text[:500],  # 最多500字符
                        "structure": structure,
                        "quality_score": quality_score,
                        "reusability": reusability,
                        "credibility": 0.7 + (quality_score * 0.2),  # 质量越高越可信
                        "confidence": 0.75,
                        "source_chunks": [chunk_id]
                    }
                    cases.append(case)

        return cases

    def _extract_bar_structure(self, text: str) -> Dict[str, str]:
        """提取BAR结构"""
        structure = {
            "background": "",
            "action": "",
            "result": ""
        }

        # 分句
        sentences = re.split(r'[。！？\n]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 匹配背景
            if any(kw in sentence for kw in self.BACKGROUND_KEYWORDS):
                if not structure["background"]:
                    structure["background"] = sentence

            # 匹配行动
            elif any(kw in sentence for kw in self.ACTION_KEYWORDS):
                if not structure["action"]:
                    structure["action"] = sentence

            # 匹配结果
            elif any(kw in sentence for kw in self.RESULT_KEYWORDS):
                if not structure["result"]:
                    structure["result"] = sentence

        return structure

    def _calculate_quality_score(self, text: str, structure: Dict[str, str]) -> float:
        """计算质量分数"""
        score = 0.0

        # BAR完整性（最高0.6分）
        if structure["background"]:
            score += 0.2
        if structure["action"]:
            score += 0.2
        if structure["result"]:
            score += 0.2

        # 长度适中（最高0.2分）
        length = len(text)
        if 100 <= length <= 500:
            score += 0.2
        elif 50 <= length < 100 or 500 < length <= 1000:
            score += 0.1

        # 具体性（最高0.2分）- 包含数字和具体名词
        has_numbers = bool(re.search(r'\d+', text))
        has_specific_terms = len(text) > 50  # 简化判断

        if has_numbers:
            score += 0.1
        if has_specific_terms:
            score += 0.1

        return min(score, 1.0)

    def _assess_reusability(self, structure: Dict[str, str], quality_score: float) -> str:
        """评估可复用性"""
        if quality_score >= 0.8 and all(structure.values()):
            return "高 - BAR完整且质量优秀"
        elif quality_score >= 0.6:
            return "中 - 结构较完整"
        else:
            return "低 - 信息不足"
