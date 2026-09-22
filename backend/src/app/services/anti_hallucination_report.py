"""
反幻觉报告生成器
使用"填空题"模板 + 幻觉检测器

四重锁：
1. ✅ 数据与解读物理隔离 - 只喂facts.json
2. ✅ 填充题代替作文题 - 固定模板
3. ✅ 强制引用坐标 - 每句话带来源
4. ✅ 后置幻觉侦探 - 自动校验数字
"""

import re
import json
from typing import Dict, List, Any, Tuple
from datetime import datetime


class HallucinationDetector:
    """幻觉检测器 - 拦截AI编造的数字"""



    def __init__(self, use_workflow_engine: bool = True):


        """初始化服务"""


        self.use_workflow_engine = use_workflow_engine


        


        if use_workflow_engine:


            from app.services.workflow_engine import WorkflowEngine


            self.workflow_engine = WorkflowEngine(max_workers=4)


    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """提取文本中的所有数字"""
        # 匹配整数和小数
        pattern = r'\d+\.?\d*'
        matches = re.findall(pattern, text)
        return [float(m) for m in matches]

    @staticmethod
    def extract_facts_numbers(facts: Dict) -> set:
        """提取facts中的所有合法数字"""
        numbers = set()

        def recursive_extract(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    recursive_extract(v)
            elif isinstance(obj, list):
                for item in obj:
                    recursive_extract(item)
            elif isinstance(obj, (int, float)):
                numbers.add(float(obj))

        recursive_extract(facts)
        return numbers

    @staticmethod
    def validate_report(report_text: str, facts: Dict) -> Tuple[bool, List[str]]:
        """
        验证报告中的数字是否都来自facts

        返回：(是否通过, 错误列表)
        """
        errors = []

        # 提取报告中的数字
        report_numbers = HallucinationDetector.extract_numbers(report_text)

        # 提取facts中的合法数字
        valid_numbers = HallucinationDetector.extract_facts_numbers(facts)

        # 白名单：这些数字可以出现（日期、常见格式）
        # 允许日期中的数字（年月日时分秒）
        whitelist_patterns = [
            r'202[0-9]',  # 年份
            r'document_\d+',  # 文档ID
            r'\d{1,2}:\d{2}',  # 时间格式
        ]

        # 检查每个数字
        for num in report_numbers:
            # 跳过日期中的常见数字
            if num in [2026, 2025, 2024, 2023]:  # 年份
                continue
            if 1 <= num <= 12:  # 月份
                continue
            if 1 <= num <= 31:  # 日期
                continue
            if 0 <= num <= 59 and '.' in str(num):  # 秒数（小数）
                continue

            # 容忍度：±0.1的误差（处理浮点数精度问题）
            is_valid = any(abs(num - valid) < 0.1 for valid in valid_numbers)

            if not is_valid:
                # 检查是否在document_ID中
                if not re.search(rf'document[_\s]+{int(num)}', report_text):
                    errors.append(f"幻觉数字检测: {num} 不在facts中")

        # 检查是否有未引用的直接引语
        quotes = re.findall(r'"([^"]+)"', report_text)
        for quote in quotes:
            # 检查引号后是否跟着引用标记
            pattern = f'"{re.escape(quote)}"[^（]*（来源：'
            if not re.search(pattern, report_text):
                errors.append(f"缺少引用: \"{quote}\" 后面没有（来源：...）")

        return len(errors) == 0, errors


class AntiHallucinationReportGenerator:
    """反幻觉报告生成器"""

    # 固定的填空题模板
    REPORT_TEMPLATE = """
你是一个数据播报员，不是创作家。
请根据提供的JSON数据，将下面的【报告框架】填充完整。

**严格约束**：
1. 只能使用JSON中提供的数字，禁止计算、推测、估算
2. 如果JSON中没有某个字段，该段落直接跳过
3. 每提到一个具体观点或引语，必须标注（来源：文件名，时间戳）
4. 禁止使用"大约"、"可能"、"估计"等模糊词汇
5. 结论部分限制50字以内，仅归纳数据，禁止推测原因

【提供的JSON数据】
```json
{facts_json}
```

【报告框架 - 请严格按此格式填充】

## 数据概览
本次共分析 [total_docs] 份材料，包含 [total_chunks] 个文本片段，总字数 [total_words] 字。

## 主题热度排名
{category_section}

## 核心人物
{speakers_section}

## 主要地点
{locations_section}

## 典型观点摘录（原文引用）
{evidence_section}

## 数据归纳
基于上述统计数据，[summary]（限50字，仅归纳，禁止推测）

---
生成时间：{generated_at}
数据来源：SQL聚合查询
"""

    @staticmethod
    def build_category_section(facts: Dict) -> str:
        """构建主题排名部分"""
        if not facts.get('category_rank'):
            return "（无主题数据）"

        lines = []
        for i, item in enumerate(facts['category_rank'], 1):
            name = item['name']
            count = item['count']
            percentage = item.get('percentage', 0)
            lines.append(f"{i}. **{name}**: 提及 {count} 次（占比 {percentage}%）")

        return "\n".join(lines)

    @staticmethod
    def build_speakers_section(facts: Dict) -> str:
        """构建人物部分"""
        speakers = facts.get('top_speakers', [])
        if not speakers:
            return "（无人物数据）"

        lines = []
        for i, speaker in enumerate(speakers[:5], 1):
            lines.append(f"{i}. {speaker['name']}: 提及 {speaker['count']} 次")

        return "\n".join(lines)

    @staticmethod
    def build_locations_section(facts: Dict) -> str:
        """构建地点部分"""
        locations = facts.get('top_locations', [])
        if not locations:
            return "（无地点数据）"

        lines = []
        for i, location in enumerate(locations[:5], 1):
            lines.append(f"{i}. {location['name']}: 提及 {location['count']} 次")

        return "\n".join(lines)

    @staticmethod
    def build_evidence_section(facts: Dict) -> str:
        """构建证据摘录部分"""
        evidence = facts.get('evidence_samples', [])
        if not evidence:
            return "（无证据样本）"

        lines = []
        for i, sample in enumerate(evidence[:5], 1):
            text = sample['text']

            # 兼容性：支持source或source_file
            source = sample.get('source') or sample.get('source_file', 'unknown')

            # 支持speaker字段
            speaker = sample.get('speaker')
            if speaker:
                source = f"{source} - {speaker}"

            timestamp = sample.get('timestamp')

            if timestamp is not None:
                time_str = f"{timestamp:.1f}秒"
            else:
                time_str = "无时间戳"

            lines.append(f'{i}. "{text}"（来源：{source}，{time_str}）')

        return "\n".join(lines)

    @staticmethod
    def generate_report_prompt(facts: Dict) -> str:
        """生成填充后的报告Prompt"""

        # 构建各个部分
        category_section = AntiHallucinationReportGenerator.build_category_section(facts)
        speakers_section = AntiHallucinationReportGenerator.build_speakers_section(facts)
        locations_section = AntiHallucinationReportGenerator.build_locations_section(facts)
        evidence_section = AntiHallucinationReportGenerator.build_evidence_section(facts)

        # 填充模板
        prompt = AntiHallucinationReportGenerator.REPORT_TEMPLATE.format(
            facts_json=json.dumps(facts, indent=2, ensure_ascii=False),
            category_section=category_section,
            speakers_section=speakers_section,
            locations_section=locations_section,
            evidence_section=evidence_section,
            generated_at=facts.get('generated_at', datetime.now().isoformat())
        )

        return prompt

    @staticmethod
    def generate_report_direct(facts: Dict) -> str:
        """
        直接生成报告（不调用LLM）
        这是最保险的方案 - 完全基于模板填充
        """

        # 兼容性：支持total_statements或total_chunks
        total_items = facts.get('total_statements') or facts.get('total_chunks', 0)

        # 数据概览
        report = f"""# 数据分析报告

## 数据概览
本次共分析 {facts['total_docs']} 份材料，包含 {total_items} 条结构化陈述，总字数 {facts['total_words']} 字。

数据来源：{facts.get('data_source', 'SQL聚合查询')}

## 主题热度排名
"""

        # 主题排名
        category_section = AntiHallucinationReportGenerator.build_category_section(facts)
        report += category_section + "\n\n"

        # 核心人物
        report += "## 核心人物\n"
        speakers_section = AntiHallucinationReportGenerator.build_speakers_section(facts)
        report += speakers_section + "\n\n"

        # 句子类型分布（如果有）
        if facts.get('sentence_types'):
            report += "## 句子类型分布\n"
            for item in facts['sentence_types']:
                report += f"- {item['type']}: {item['count']} 条\n"
            report += "\n"

        # 典型观点摘录
        report += "## 典型观点摘录（原文引用）\n"
        evidence_section = AntiHallucinationReportGenerator.build_evidence_section(facts)
        report += evidence_section + "\n\n"

        # 数据归纳（最简化版本）
        report += "## 数据归纳\n"
        if facts['category_rank']:
            top_topic = facts['category_rank'][0]
            report += f"基于统计数据，'{top_topic['name']}'是本次调查中提及频次最高的主题，共 {top_topic['count']} 次。"
        else:
            report += "数据量不足，暂无归纳。"

        report += f"\n\n---\n生成时间：{facts['generated_at']}\n数据来源：fact_statements表（SQL聚合查询）"

        return report


if __name__ == "__main__":
    # 测试
    test_facts = {
        "project_id": 1,
        "total_docs": 10,
        "total_chunks": 120,
        "total_words": 12450,
        "category_rank": [
            {"name": "食", "count": 45, "percentage": 35.7},
            {"name": "衣", "count": 23, "percentage": 18.3}
        ],
        "top_speakers": [
            {"name": "王大爷", "count": 15}
        ],
        "top_locations": [],
        "evidence_samples": [
            {
                "text": "杀猪菜是传统美食",
                "source": "document_40",
                "timestamp": 15.2
            }
        ],
        "generated_at": "2026-08-05T15:00:00"
    }

    print("=" * 70)
    print("🔒 反幻觉报告生成测试")
    print("=" * 70)

    # 测试1: 生成报告
    report = AntiHallucinationReportGenerator.generate_report_direct(test_facts)
    print("\n【生成的报告】\n")
    print(report)

    # 测试2: 幻觉检测
    print("\n" + "=" * 70)
    print("🕵️ 幻觉检测测试")
    print("=" * 70)

    # 测试正常报告
    is_valid, errors = HallucinationDetector.validate_report(report, test_facts)
    print(f"\n正常报告验证: {'✅ 通过' if is_valid else '❌ 失败'}")
    if errors:
        for error in errors:
            print(f"  - {error}")

    # 测试幻觉报告
    fake_report = "本次调查中，衣食住行各占25%，共访谈了100位村民。"
    is_valid, errors = HallucinationDetector.validate_report(fake_report, test_facts)
    print(f"\n幻觉报告验证: {'✅ 通过' if is_valid else '❌ 失败（预期）'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
