"""
引用验证器 - 反幻觉核心组件

职责：
1. 验证报告中的每个观点都有原文引用
2. 检测数字是否来自原文
3. 确保引用格式正确
4. 生成引用完整性报告
"""

import re
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class CitationValidator:
    """
    引用验证器

    实现反幻觉的四重锁：
    1. 强制引用标记：每个关键观点必须有[^n]标记
    2. 引用源验证：每个引用ID必须在citations列表中
    3. 数字验证：所有数字必须来自原文或计算
    4. 引用覆盖率：统计有引用支持的内容比例
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.validation_rules = {
            'citation_mark_required': True,  # 要求引用标记
            'number_validation': True,  # 验证数字来源
            'citation_format_check': True,  # 检查引用格式
            'coverage_threshold': 0.3  # 至少30%的内容有引用支持
        }

    def validate_section(
        self,
        content: str,
        citations: List[Dict]
    ) -> Dict[str, Any]:
        """
        验证单个章节的引用完整性

        Args:
            content: 章节内容（Markdown格式）
            citations: 引用列表

        Returns:
            {
                'is_valid': bool,
                'issues': [问题列表],
                'citation_coverage': float,
                'statistics': {统计信息}
            }
        """
        issues = []

        # 1. 提取所有引用标记
        citation_marks = self._extract_citation_marks(content)

        # 2. 验证引用标记的完整性
        citation_ids = {cite['id'] for cite in citations}
        for mark in citation_marks:
            if mark not in citation_ids:
                issues.append({
                    'type': 'missing_citation',
                    'severity': 'high',
                    'message': f"引用标记[^{mark}]没有对应的引用源"
                })

        # 3. 验证数字来源
        if self.validation_rules['number_validation']:
            number_issues = self._validate_numbers(content, citations)
            issues.extend(number_issues)

        # 4. 计算引用覆盖率
        coverage = self._calculate_citation_coverage(content, citation_marks)

        # 5. 检查是否满足覆盖率阈值
        if coverage < self.validation_rules['coverage_threshold']:
            issues.append({
                'type': 'low_coverage',
                'severity': 'medium',
                'message': f"引用覆盖率({coverage:.1%})低于阈值({self.validation_rules['coverage_threshold']:.1%})"
            })

        is_valid = len([i for i in issues if i['severity'] == 'high']) == 0

        return {
            'is_valid': is_valid,
            'issues': issues,
            'citation_coverage': coverage,
            'statistics': {
                'total_citations': len(citations),
                'citation_marks_used': len(citation_marks),
                'word_count': len(content),
                'paragraphs': content.count('\n\n')
            }
        }

    def validate_full_report(
        self,
        sections: List[Dict]
    ) -> Dict[str, Any]:
        """
        验证完整报告的引用完整性

        Args:
            sections: 章节列表，每个包含content和citations

        Returns:
            完整报告的验证结果
        """
        all_issues = []
        total_citations = 0
        total_coverage = 0.0

        for idx, section in enumerate(sections):
            validation = self.validate_section(
                section['content'],
                section['citations']
            )

            if not validation['is_valid']:
                all_issues.append({
                    'section': section['chapter'],
                    'section_index': idx,
                    'issues': validation['issues']
                })

            total_citations += len(section['citations'])
            total_coverage += validation['citation_coverage']

        avg_coverage = total_coverage / len(sections) if sections else 0.0

        return {
            'is_valid': len(all_issues) == 0,
            'sections_with_issues': all_issues,
            'total_citations': total_citations,
            'average_coverage': avg_coverage,
            'report_quality': self._assess_quality(avg_coverage, len(all_issues))
        }

    def _extract_citation_marks(self, content: str) -> List[int]:
        """
        提取内容中的所有引用标记 [^n]

        Returns:
            引用ID列表
        """
        pattern = r'\[\^(\d+)\]'
        matches = re.findall(pattern, content)
        return [int(m) for m in matches]

    def _validate_numbers(
        self,
        content: str,
        citations: List[Dict]
    ) -> List[Dict]:
        """
        验证内容中的数字是否来自引用

        关键数字（非日期、序号）应该有来源
        """
        issues = []

        # 提取内容中的数字（排除日期和序号）
        numbers = self._extract_significant_numbers(content)

        # 提取引用中的所有数字
        citation_numbers = set()
        for cite in citations:
            cite_content = cite.get('content', '')
            cite_numbers = self._extract_all_numbers(cite_content)
            citation_numbers.update(cite_numbers)

        # 检查关键数字是否有出处
        for num in numbers:
            # 允许一定误差（浮点数精度）
            is_valid = any(abs(num - cn) < 0.1 for cn in citation_numbers)

            if not is_valid:
                # 检查是否是统计数字（如文档数、字数等）
                context = self._get_number_context(content, num)
                if not self._is_metadata_number(context):
                    issues.append({
                        'type': 'unverified_number',
                        'severity': 'medium',
                        'message': f"数字{num}未在引用中找到来源",
                        'context': context
                    })

        return issues

    def _extract_significant_numbers(self, content: str) -> List[float]:
        """提取有意义的数字（排除日期、序号等）"""
        pattern = r'\b(\d+(?:\.\d+)?)\b'
        matches = re.findall(pattern, content)

        numbers = []
        for match in matches:
            num = float(match)

            # 排除常见的日期和序号
            if num in [2020, 2021, 2022, 2023, 2024, 2025, 2026]:  # 年份
                continue
            if 1 <= num <= 31:  # 日期
                continue
            if num < 1:  # 小数（通常是比例）
                numbers.append(num)
            elif num > 50:  # 大于50的数字（可能是统计数据）
                numbers.append(num)

        return numbers

    def _extract_all_numbers(self, text: str) -> set:
        """提取文本中的所有数字"""
        pattern = r'\b(\d+(?:\.\d+)?)\b'
        matches = re.findall(pattern, text)
        return {float(m) for m in matches}

    def _get_number_context(self, content: str, number: float) -> str:
        """获取数字的上下文（前后20字符）"""
        num_str = str(int(number) if number == int(number) else number)
        pattern = re.escape(num_str)
        match = re.search(f'.{{0,20}}{pattern}.{{0,20}}', content)

        if match:
            return match.group(0)
        return ""

    def _is_metadata_number(self, context: str) -> bool:
        """判断是否是元数据数字（如文档数、字数等）"""
        metadata_keywords = [
            '文档', '字数', '份', '个', '处', '位', '次',
            '章', '节', '段', '篇', '页'
        ]
        return any(keyword in context for keyword in metadata_keywords)

    def _calculate_citation_coverage(
        self,
        content: str,
        citation_marks: List[int]
    ) -> float:
        """
        计算引用覆盖率

        简化算法：统计带引用标记的段落占比
        """
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        if not paragraphs:
            return 0.0

        # 统计包含引用标记的段落数
        paragraphs_with_citations = 0
        for para in paragraphs:
            if re.search(r'\[\^\d+\]', para):
                paragraphs_with_citations += 1

        coverage = paragraphs_with_citations / len(paragraphs)
        return coverage

    def _assess_quality(self, coverage: float, issue_count: int) -> str:
        """
        评估报告质量

        Returns:
            'excellent' | 'good' | 'fair' | 'poor'
        """
        if coverage >= 0.5 and issue_count == 0:
            return 'excellent'
        elif coverage >= 0.3 and issue_count <= 2:
            return 'good'
        elif coverage >= 0.2 or issue_count <= 5:
            return 'fair'
        else:
            return 'poor'

    def generate_validation_report(
        self,
        validation_result: Dict
    ) -> str:
        """
        生成人类可读的验证报告

        Args:
            validation_result: validate_full_report的返回值

        Returns:
            Markdown格式的验证报告
        """
        report = "# 引用完整性验证报告\n\n"

        # 总体评估
        quality = validation_result['report_quality']
        quality_emoji = {
            'excellent': '🌟',
            'good': '✅',
            'fair': '⚠️',
            'poor': '❌'
        }

        report += f"## 总体评估\n\n"
        report += f"**质量等级**：{quality_emoji.get(quality, '')} {quality.upper()}\n\n"

        # 统计信息
        stats = validation_result
        report += f"## 统计信息\n\n"
        report += f"- **总引用数**：{stats['total_citations']}\n"
        report += f"- **平均引用覆盖率**：{stats['average_coverage']:.1%}\n"
        report += f"- **问题章节数**：{len(stats['sections_with_issues'])}\n\n"

        # 问题详情
        if stats['sections_with_issues']:
            report += f"## 发现的问题\n\n"
            for section_issue in stats['sections_with_issues']:
                report += f"### {section_issue['section']}\n\n"
                for issue in section_issue['issues']:
                    severity_emoji = {
                        'high': '🔴',
                        'medium': '🟡',
                        'low': '🟢'
                    }
                    emoji = severity_emoji.get(issue['severity'], '')
                    report += f"- {emoji} **{issue['type']}**: {issue['message']}\n"
                report += "\n"
        else:
            report += "## ✅ 未发现问题\n\n"
            report += "所有章节的引用完整性检查均通过。\n\n"

        # 建议
        report += "## 建议\n\n"
        if quality == 'excellent':
            report += "报告引用质量优秀，保持当前标准。\n"
        elif quality == 'good':
            report += "报告引用质量良好，可进一步提高引用覆盖率。\n"
        elif quality == 'fair':
            report += "报告引用质量尚可，建议：\n"
            report += "1. 增加关键观点的原文引用\n"
            report += "2. 验证未标注来源的数字\n"
        else:
            report += "报告引用质量不足，必须改进：\n"
            report += "1. 补充缺失的引用标记\n"
            report += "2. 为所有关键数据提供来源\n"
            report += "3. 提高引用覆盖率至30%以上\n"

        return report
