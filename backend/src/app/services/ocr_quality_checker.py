"""
OCR质量检查器 - 自动检测和评估OCR结果质量
支持质量评分、错误检测、自动修正建议
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import re
from collections import Counter
import numpy as np

logger = logging.getLogger(__name__)


class QualityIssue:
    """质量问题"""

    def __init__(
        self,
        issue_type: str,
        severity: str,  # low/medium/high
        description: str,
        location: Optional[Dict] = None,
        suggestion: Optional[str] = None
    ):
        self.issue_type = issue_type
        self.severity = severity
        self.description = description
        self.location = location
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "location": self.location,
            "suggestion": self.suggestion
        }


class OCRQualityReport:
    """OCR质量报告"""
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.overall_score: float = 0.0  # 0-100
        self.confidence_score: float = 0.0
        self.text_quality_score: float = 0.0
        self.layout_score: float = 0.0
        self.issues: List[QualityIssue] = []
        self.statistics: Dict[str, Any] = {}
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": round(self.overall_score, 2),
            "confidence_score": round(self.confidence_score, 2),
            "text_quality_score": round(self.text_quality_score, 2),
            "layout_score": round(self.layout_score, 2),
            "issues": [issue.to_dict() for issue in self.issues],
            "issue_count": len(self.issues),
            "high_severity_count": sum(1 for i in self.issues if i.severity == "high"),
            "statistics": self.statistics,
            "recommendations": self.recommendations,
            "quality_grade": self._get_grade()
        }

    def _get_grade(self) -> str:
        """获取质量等级"""
        if self.overall_score >= 90:
            return "优秀"
        elif self.overall_score >= 75:
            return "良好"
        elif self.overall_score >= 60:
            return "中等"
        elif self.overall_score >= 40:
            return "较差"
        else:
            return "差"


class OCRQualityChecker:
    """OCR质量检查器"""

    def __init__(
        self,
        min_confidence_threshold: float = 0.7,
        min_text_length: int = 10,
        check_chinese: bool = True
    ):
        """
        Args:
            min_confidence_threshold: 最小置信度阈值
            min_text_length: 最小文本长度（字符数）
            check_chinese: 是否启用中文特定检查
        """
        self.min_confidence = min_confidence_threshold
        self.min_text_length = min_text_length
        self.check_chinese = check_chinese

        # 常见OCR错误模式
        self.common_errors = {
            "0": ["O", "o"],  # 数字0易混淆
            "1": ["l", "I", "|"],  # 数字1易混淆
            "8": ["B"],
            "5": ["S"],
            "O": ["0"],
            "l": ["1", "I"],
            "I": ["1", "l"],
        }

        # 中文常见错误
        self.chinese_confusions = {
            "己": "已",
            "已": "己",
            "未": "末",
            "末": "未",
            "土": "士",
            "士": "土",
        }

    def check_ocr_result(self, ocr_result) -> OCRQualityReport:
        """
        检查OCR结果质量

        Args:
            ocr_result: OCRResult对象

        Returns:
            OCRQualityReport对象
        """
        report = OCRQualityReport()

        # 1. 置信度检查
        confidence_score, confidence_issues = self._check_confidence(ocr_result)
        report.confidence_score = confidence_score
        report.issues.extend(confidence_issues)

        # 2. 文本质量检查
        text_score, text_issues = self._check_text_quality(ocr_result)
        report.text_quality_score = text_score
        report.issues.extend(text_issues)

        # 3. 布局检查
        layout_score, layout_issues = self._check_layout(ocr_result)
        report.layout_score = layout_score
        report.issues.extend(layout_issues)

        # 4. 计算综合分数
        report.overall_score = (
            confidence_score * 0.4 +
            text_score * 0.4 +
            layout_score * 0.2
        )

        # 5. 生成统计信息
        report.statistics = self._generate_statistics(ocr_result, report)

        # 6. 生成建议
        report.recommendations = self._generate_recommendations(report)

        logger.info(
            f"📊 OCR质量检查完成: 总分{report.overall_score:.1f}, "
            f"等级{report._get_grade()}, {len(report.issues)}个问题"
        )

        return report

    def _check_confidence(self, ocr_result) -> Tuple[float, List[QualityIssue]]:
        """检查置信度"""
        issues = []

        if not ocr_result.text_blocks:
            issues.append(QualityIssue(
                issue_type="no_text",
                severity="high",
                description="未检测到任何文本",
                suggestion="检查图像质量，确保有清晰的文字"
            ))
            return 0.0, issues

        # 平均置信度
        avg_confidence = ocr_result.confidence

        # 低置信度文本块
        low_conf_blocks = [
            b for b in ocr_result.text_blocks
            if b.get("confidence", 1.0) < self.min_confidence
        ]

        if low_conf_blocks:
            low_conf_ratio = len(low_conf_blocks) / len(ocr_result.text_blocks)

            severity = "high" if low_conf_ratio > 0.3 else "medium" if low_conf_ratio > 0.1 else "low"

            issues.append(QualityIssue(
                issue_type="low_confidence",
                severity=severity,
                description=f"{len(low_conf_blocks)}个文本块置信度低于{self.min_confidence:.0%}",
                location={"block_count": len(low_conf_blocks)},
                suggestion="建议提高图像分辨率或改善拍摄条件"
            ))

        # 置信度分数 (0-100)
        score = avg_confidence * 100

        return score, issues

    def _check_text_quality(self, ocr_result) -> Tuple[float, List[QualityIssue]]:
        """检查文本质量"""
        issues = []
        text = ocr_result.text

        if not text or len(text) < self.min_text_length:
            issues.append(QualityIssue(
                issue_type="insufficient_text",
                severity="medium",
                description=f"文本长度过短（{len(text)}字符）",
                suggestion="可能是识别不完整或图像内容过少"
            ))
            return 50.0, issues

        score = 100.0

        # 1. 检查乱码字符
        garbled_ratio = self._check_garbled_chars(text)
        if garbled_ratio > 0.1:
            issues.append(QualityIssue(
                issue_type="garbled_text",
                severity="high",
                description=f"检测到{garbled_ratio:.1%}的乱码字符",
                suggestion="可能是字符编码问题或识别错误"
            ))
            score -= 30

        # 2. 检查连续空格
        excessive_spaces = len(re.findall(r'\s{3,}', text))
        if excessive_spaces > 0:
            issues.append(QualityIssue(
                issue_type="excessive_spaces",
                severity="low",
                description=f"发现{excessive_spaces}处连续空格",
                suggestion="可能需要后处理清理"
            ))
            score -= 5

        # 3. 检查异常字符比例
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9一-龥\s\.,!?;:()（），。！？；：]', text)) / len(text)
        if special_char_ratio > 0.15:
            issues.append(QualityIssue(
                issue_type="excessive_special_chars",
                severity="medium",
                description=f"特殊字符占比{special_char_ratio:.1%}",
                suggestion="可能存在识别错误"
            ))
            score -= 15

        # 4. 检查中文错误（如果启用）
        if self.check_chinese:
            chinese_issues = self._check_chinese_errors(text)
            issues.extend(chinese_issues)
            if chinese_issues:
                score -= len(chinese_issues) * 5

        return max(0.0, score), issues

    def _check_layout(self, ocr_result) -> Tuple[float, List[QualityIssue]]:
        """检查布局质量"""
        issues = []
        score = 100.0

        if not ocr_result.text_blocks:
            return 0.0, issues

        # 1. 检查文本块重叠
        overlaps = self._check_text_overlap(ocr_result.text_blocks)
        if overlaps > 0:
            issues.append(QualityIssue(
                issue_type="text_overlap",
                severity="medium",
                description=f"检测到{overlaps}处文本块重叠",
                suggestion="可能需要调整检测参数"
            ))
            score -= overlaps * 10

        # 2. 检查文本块间距异常
        spacing_issues = self._check_spacing_issues(ocr_result.text_blocks)
        if spacing_issues:
            issues.append(QualityIssue(
                issue_type="spacing_anomaly",
                severity="low",
                description="文本块间距分布不均匀",
                suggestion="可能影响阅读顺序"
            ))
            score -= 10

        # 3. 检查文本方向一致性
        if len(ocr_result.text_blocks) > 5:
            direction_score = self._check_text_direction(ocr_result.text_blocks)
            if direction_score < 0.8:
                issues.append(QualityIssue(
                    issue_type="inconsistent_direction",
                    severity="medium",
                    description="文本方向不一致",
                    suggestion="可能需要启用文字方向分类"
                ))
                score -= 15

        return max(0.0, score), issues

    def _check_garbled_chars(self, text: str) -> float:
        """检查乱码字符比例"""
        # 检测控制字符、未定义字符等
        garbled_count = len(re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f�]', text))
        return garbled_count / len(text) if text else 0.0

    def _check_chinese_errors(self, text: str) -> List[QualityIssue]:
        """检查中文常见错误"""
        issues = []

        for wrong, correct in self.chinese_confusions.items():
            if wrong in text:
                count = text.count(wrong)
                issues.append(QualityIssue(
                    issue_type="chinese_confusion",
                    severity="low",
                    description=f"可能将'{correct}'误识为'{wrong}' ({count}处)",
                    suggestion=f"建议人工检查或替换为'{correct}'"
                ))

        return issues

    def _check_text_overlap(self, text_blocks: List[Dict]) -> int:
        """检查文本块重叠"""
        overlap_count = 0

        for i, block1 in enumerate(text_blocks):
            bbox1 = block1.get("bbox", [])
            if len(bbox1) != 4:
                continue

            x1_min, y1_min = bbox1[0]
            x1_max, y1_max = bbox1[2]

            for block2 in text_blocks[i + 1:]:
                bbox2 = block2.get("bbox", [])
                if len(bbox2) != 4:
                    continue

                x2_min, y2_min = bbox2[0]
                x2_max, y2_max = bbox2[2]

                # 检查重叠
                if not (x1_max < x2_min or x2_max < x1_min or y1_max < y2_min or y2_max < y1_min):
                    overlap_count += 1

        return overlap_count

    def _check_spacing_issues(self, text_blocks: List[Dict]) -> bool:
        """检查间距问题"""
        if len(text_blocks) < 3:
            return False

        # 计算相邻文本块的垂直距离
        distances = []
        sorted_blocks = sorted(text_blocks, key=lambda b: b.get("position", {}).get("y", 0))

        for i in range(len(sorted_blocks) - 1):
            y1 = sorted_blocks[i].get("position", {}).get("y", 0)
            y2 = sorted_blocks[i + 1].get("position", {}).get("y", 0)
            distances.append(abs(y2 - y1))

        if not distances:
            return False

        # 计算标准差
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)

        # 标准差大于均值的50%视为不均匀
        return std_dist > mean_dist * 0.5

    def _check_text_direction(self, text_blocks: List[Dict]) -> float:
        """检查文本方向一致性（返回0-1的一致性分数）"""
        if len(text_blocks) < 2:
            return 1.0

        # 计算文本块的主要方向（水平/垂直）
        horizontal_count = 0
        vertical_count = 0

        for block in text_blocks:
            pos = block.get("position", {})
            width = pos.get("width", 0)
            height = pos.get("height", 0)

            if width > height * 1.5:
                horizontal_count += 1
            elif height > width * 1.5:
                vertical_count += 1

        total = horizontal_count + vertical_count
        if total == 0:
            return 1.0

        # 一致性分数 = 主要方向占比
        return max(horizontal_count, vertical_count) / total

    def _generate_statistics(self, ocr_result, report: OCRQualityReport) -> Dict[str, Any]:
        """生成统计信息"""
        text = ocr_result.text

        return {
            "total_chars": len(text),
            "total_blocks": ocr_result.total_blocks,
            "avg_confidence": round(ocr_result.confidence, 4),
            "min_confidence": round(min([b.get("confidence", 1.0) for b in ocr_result.text_blocks], default=0.0), 4),
            "max_confidence": round(max([b.get("confidence", 0.0) for b in ocr_result.text_blocks], default=0.0), 4),
            "chinese_char_count": len(re.findall(r'[一-龥]', text)),
            "english_char_count": len(re.findall(r'[a-zA-Z]', text)),
            "digit_count": len(re.findall(r'\d', text)),
            "punctuation_count": len(re.findall(r'[,.!?;:，。！？；：]', text)),
            "issue_by_severity": {
                "high": sum(1 for i in report.issues if i.severity == "high"),
                "medium": sum(1 for i in report.issues if i.severity == "medium"),
                "low": sum(1 for i in report.issues if i.severity == "low"),
            }
        }

    def _generate_recommendations(self, report: OCRQualityReport) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 根据分数给出建议
        if report.overall_score < 60:
            recommendations.append("OCR质量较差，建议检查原始图像质量")

        if report.confidence_score < 70:
            recommendations.append("置信度偏低，建议提高图像分辨率或改善光照条件")

        if report.text_quality_score < 70:
            recommendations.append("文本质量问题较多，建议启用后处理或人工校对")

        if report.layout_score < 70:
            recommendations.append("布局识别存在问题，建议调整检测参数")

        # 根据高严重性问题数量
        high_issues = sum(1 for i in report.issues if i.severity == "high")
        if high_issues > 3:
            recommendations.append(f"发现{high_issues}个高严重性问题，强烈建议人工复查")

        # 如果没有明显问题
        if not recommendations:
            recommendations.append("OCR质量良好，可直接使用")

        return recommendations


def check_ocr_quality(ocr_result, **checker_kwargs) -> OCRQualityReport:
    """
    便捷函数：检查OCR质量

    Args:
        ocr_result: OCRResult对象
        **checker_kwargs: OCRQualityChecker初始化参数

    Returns:
        OCRQualityReport对象
    """
    checker = OCRQualityChecker(**checker_kwargs)
    return checker.check_ocr_result(ocr_result)
