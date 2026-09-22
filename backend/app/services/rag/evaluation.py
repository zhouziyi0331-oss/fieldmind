"""
RAG系统评测框架

提供完整的评测体系：固定测试集、四项核心指标、版本对比
"""
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import logging
from pathlib import Path
import numpy as np
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """指标类型"""
    ACCURACY = "accuracy"
    RECALL = "recall"
    CITATION_ACCURACY = "citation_accuracy"
    COMPLETENESS = "completeness"


@dataclass
class TestCase:
    """测试用例"""
    id: str
    question: str
    expected_answer: str
    relevant_doc_ids: List[str]  # 正确答案应该引用的文档ID
    aspects: List[str]  # 答案应该覆盖的要点
    metadata: Dict[str, Any] = field(default_factory=dict)
    category: str = "general"  # 问题分类
    difficulty: str = "medium"  # easy/medium/hard

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class PredictionResult:
    """预测结果"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]  # [{"doc_id": "...", "score": 0.85, "content": "..."}]
    retrieved_doc_ids: List[str]
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationMetrics:
    """评测指标"""
    accuracy: float  # 答案准确率 (0-1)
    recall: float  # 文档召回率 (0-1)
    citation_accuracy: float  # 引用正确率 (0-1)
    completeness: float  # 回答完整度 (0-1)

    # 额外统计
    precision: float = 0.0  # 检索精确率
    f1_score: float = 0.0  # F1分数
    mrr: float = 0.0  # Mean Reciprocal Rank

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def overall_score(self) -> float:
        """综合得分 (加权平均)"""
        weights = {
            "accuracy": 0.30,
            "recall": 0.25,
            "citation_accuracy": 0.25,
            "completeness": 0.20
        }
        return (
            self.accuracy * weights["accuracy"] +
            self.recall * weights["recall"] +
            self.citation_accuracy * weights["citation_accuracy"] +
            self.completeness * weights["completeness"]
        )


@dataclass
class EvaluationResult:
    """单个测试用例的评测结果"""
    test_case_id: str
    question: str
    expected_answer: str
    predicted_answer: str
    metrics: EvaluationMetrics
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "test_case_id": self.test_case_id,
            "question": self.question,
            "expected_answer": self.expected_answer,
            "predicted_answer": self.predicted_answer,
            "metrics": self.metrics.to_dict(),
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class EvaluationReport:
    """评测报告"""
    version: str
    timestamp: datetime
    total_cases: int
    results: List[EvaluationResult]
    aggregate_metrics: EvaluationMetrics
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "total_cases": self.total_cases,
            "aggregate_metrics": self.aggregate_metrics.to_dict(),
            "overall_score": self.aggregate_metrics.overall_score(),
            "results": [r.to_dict() for r in self.results],
            "metadata": self.metadata
        }

    def save_to_file(self, filepath: Path):
        """保存到文件"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Evaluation report saved to {filepath}")


class TestDataset:
    """测试数据集"""

    def __init__(self, dataset_path: Optional[Path] = None):
        """
        初始化测试数据集

        Args:
            dataset_path: 数据集文件路径
        """
        self.test_cases: List[TestCase] = []
        self.dataset_path = dataset_path

        if dataset_path and dataset_path.exists():
            self.load_from_file(dataset_path)

    def add_test_case(self, test_case: TestCase):
        """添加测试用例"""
        self.test_cases.append(test_case)
        logger.info(f"Added test case: {test_case.id}")

    def load_from_file(self, filepath: Path):
        """从文件加载"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.test_cases = [
            TestCase(**case) for case in data.get("test_cases", [])
        ]
        logger.info(f"Loaded {len(self.test_cases)} test cases from {filepath}")

    def save_to_file(self, filepath: Path):
        """保存到文件"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "test_cases": [tc.to_dict() for tc in self.test_cases]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.test_cases)} test cases to {filepath}")

    def get_test_cases(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[TestCase]:
        """获取测试用例"""
        cases = self.test_cases

        if category:
            cases = [tc for tc in cases if tc.category == category]

        if difficulty:
            cases = [tc for tc in cases if tc.difficulty == difficulty]

        return cases

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        categories = {}
        difficulties = {}

        for tc in self.test_cases:
            categories[tc.category] = categories.get(tc.category, 0) + 1
            difficulties[tc.difficulty] = difficulties.get(tc.difficulty, 0) + 1

        return {
            "total_cases": len(self.test_cases),
            "categories": categories,
            "difficulties": difficulties
        }


class MetricsCalculator:
    """指标计算器"""

    @staticmethod
    def calculate_accuracy(
        predicted_answer: str,
        expected_answer: str,
        threshold: float = 0.7
    ) -> float:
        """
        计算答案准确率 (基于文本相似度)

        Args:
            predicted_answer: 预测答案
            expected_answer: 期望答案
            threshold: 相似度阈值

        Returns:
            准确率 (0-1)
        """
        # 使用 SequenceMatcher 计算相似度
        similarity = SequenceMatcher(
            None,
            predicted_answer.lower().strip(),
            expected_answer.lower().strip()
        ).ratio()

        # 也计算关键词重合度
        pred_words = set(predicted_answer.lower().split())
        exp_words = set(expected_answer.lower().split())

        if not exp_words:
            return 0.0

        keyword_overlap = len(pred_words & exp_words) / len(exp_words)

        # 综合得分 (70% 文本相似度 + 30% 关键词重合)
        combined_score = similarity * 0.7 + keyword_overlap * 0.3

        return combined_score

    @staticmethod
    def calculate_recall(
        retrieved_doc_ids: List[str],
        relevant_doc_ids: List[str]
    ) -> float:
        """
        计算文档召回率

        Args:
            retrieved_doc_ids: 检索到的文档ID列表
            relevant_doc_ids: 相关文档ID列表

        Returns:
            召回率 (0-1)
        """
        if not relevant_doc_ids:
            return 1.0  # 没有相关文档时视为完美召回

        retrieved_set = set(retrieved_doc_ids)
        relevant_set = set(relevant_doc_ids)

        recalled = len(retrieved_set & relevant_set)
        return recalled / len(relevant_set)

    @staticmethod
    def calculate_precision(
        retrieved_doc_ids: List[str],
        relevant_doc_ids: List[str]
    ) -> float:
        """
        计算检索精确率

        Args:
            retrieved_doc_ids: 检索到的文档ID列表
            relevant_doc_ids: 相关文档ID列表

        Returns:
            精确率 (0-1)
        """
        if not retrieved_doc_ids:
            return 0.0

        retrieved_set = set(retrieved_doc_ids)
        relevant_set = set(relevant_doc_ids)

        relevant_retrieved = len(retrieved_set & relevant_set)
        return relevant_retrieved / len(retrieved_set)

    @staticmethod
    def calculate_f1_score(precision: float, recall: float) -> float:
        """计算F1分数"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    @staticmethod
    def calculate_citation_accuracy(
        sources: List[Dict[str, Any]],
        relevant_doc_ids: List[str],
        score_threshold: float = 0.7
    ) -> float:
        """
        计算引用正确率

        Args:
            sources: 引用来源列表
            relevant_doc_ids: 相关文档ID列表
            score_threshold: 相似度分数阈值

        Returns:
            引用正确率 (0-1)
        """
        if not sources:
            return 0.0

        # 统计高质量引用中有多少来自相关文档
        high_quality_sources = [
            s for s in sources
            if s.get("score", 0) >= score_threshold
        ]

        if not high_quality_sources:
            return 0.0

        relevant_set = set(relevant_doc_ids)
        correct_citations = sum(
            1 for s in high_quality_sources
            if s.get("doc_id") in relevant_set
        )

        return correct_citations / len(high_quality_sources)

    @staticmethod
    def calculate_completeness(
        predicted_answer: str,
        aspects: List[str],
        threshold: float = 0.5
    ) -> float:
        """
        计算回答完整度

        Args:
            predicted_answer: 预测答案
            aspects: 应该覆盖的要点列表
            threshold: 匹配阈值

        Returns:
            完整度 (0-1)
        """
        if not aspects:
            return 1.0

        answer_lower = predicted_answer.lower()
        covered_aspects = 0

        for aspect in aspects:
            aspect_lower = aspect.lower()
            # 检查要点的关键词是否出现在答案中
            aspect_words = set(aspect_lower.split())
            answer_words = set(answer_lower.split())

            overlap = len(aspect_words & answer_words)
            coverage = overlap / len(aspect_words) if aspect_words else 0

            if coverage >= threshold:
                covered_aspects += 1

        return covered_aspects / len(aspects)

    @staticmethod
    def calculate_mrr(
        retrieved_doc_ids: List[str],
        relevant_doc_ids: List[str]
    ) -> float:
        """
        计算 Mean Reciprocal Rank (MRR)

        Args:
            retrieved_doc_ids: 检索到的文档ID列表 (按排序)
            relevant_doc_ids: 相关文档ID列表

        Returns:
            MRR分数
        """
        relevant_set = set(relevant_doc_ids)

        for rank, doc_id in enumerate(retrieved_doc_ids, 1):
            if doc_id in relevant_set:
                return 1.0 / rank

        return 0.0


class RAGEvaluator:
    """RAG系统评测器"""

    def __init__(
        self,
        test_dataset: TestDataset,
        results_dir: Path = Path("evaluation_results")
    ):
        """
        初始化评测器

        Args:
            test_dataset: 测试数据集
            results_dir: 结果保存目录
        """
        self.test_dataset = test_dataset
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.calculator = MetricsCalculator()

    def evaluate_single(
        self,
        test_case: TestCase,
        prediction: PredictionResult
    ) -> EvaluationResult:
        """
        评测单个测试用例

        Args:
            test_case: 测试用例
            prediction: 预测结果

        Returns:
            评测结果
        """
        # 计算四项核心指标
        accuracy = self.calculator.calculate_accuracy(
            prediction.answer,
            test_case.expected_answer
        )

        recall = self.calculator.calculate_recall(
            prediction.retrieved_doc_ids,
            test_case.relevant_doc_ids
        )

        citation_accuracy = self.calculator.calculate_citation_accuracy(
            prediction.sources,
            test_case.relevant_doc_ids
        )

        completeness = self.calculator.calculate_completeness(
            prediction.answer,
            test_case.aspects
        )

        # 计算额外指标
        precision = self.calculator.calculate_precision(
            prediction.retrieved_doc_ids,
            test_case.relevant_doc_ids
        )

        f1_score = self.calculator.calculate_f1_score(precision, recall)

        mrr = self.calculator.calculate_mrr(
            prediction.retrieved_doc_ids,
            test_case.relevant_doc_ids
        )

        metrics = EvaluationMetrics(
            accuracy=accuracy,
            recall=recall,
            citation_accuracy=citation_accuracy,
            completeness=completeness,
            precision=precision,
            f1_score=f1_score,
            mrr=mrr
        )

        return EvaluationResult(
            test_case_id=test_case.id,
            question=test_case.question,
            expected_answer=test_case.expected_answer,
            predicted_answer=prediction.answer,
            metrics=metrics,
            details={
                "category": test_case.category,
                "difficulty": test_case.difficulty,
                "retrieved_docs": prediction.retrieved_doc_ids,
                "relevant_docs": test_case.relevant_doc_ids,
                "sources": prediction.sources
            }
        )

    def evaluate_batch(
        self,
        predictions: List[Tuple[TestCase, PredictionResult]],
        version: str
    ) -> EvaluationReport:
        """
        批量评测

        Args:
            predictions: (测试用例, 预测结果) 列表
            version: 版本号

        Returns:
            评测报告
        """
        results = []

        for test_case, prediction in predictions:
            result = self.evaluate_single(test_case, prediction)
            results.append(result)
            logger.info(
                f"Evaluated {test_case.id}: "
                f"accuracy={result.metrics.accuracy:.3f}, "
                f"recall={result.metrics.recall:.3f}, "
                f"citation={result.metrics.citation_accuracy:.3f}, "
                f"completeness={result.metrics.completeness:.3f}"
            )

        # 计算聚合指标
        aggregate_metrics = self._calculate_aggregate_metrics(results)

        report = EvaluationReport(
            version=version,
            timestamp=datetime.now(),
            total_cases=len(results),
            results=results,
            aggregate_metrics=aggregate_metrics,
            metadata={
                "dataset_size": len(self.test_dataset.test_cases),
                "dataset_stats": self.test_dataset.get_statistics()
            }
        )

        # 保存报告
        report_path = self.results_dir / f"evaluation_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report.save_to_file(report_path)

        return report

    def _calculate_aggregate_metrics(
        self,
        results: List[EvaluationResult]
    ) -> EvaluationMetrics:
        """计算聚合指标"""
        if not results:
            return EvaluationMetrics(
                accuracy=0.0,
                recall=0.0,
                citation_accuracy=0.0,
                completeness=0.0
            )

        total_accuracy = sum(r.metrics.accuracy for r in results)
        total_recall = sum(r.metrics.recall for r in results)
        total_citation = sum(r.metrics.citation_accuracy for r in results)
        total_completeness = sum(r.metrics.completeness for r in results)
        total_precision = sum(r.metrics.precision for r in results)
        total_f1 = sum(r.metrics.f1_score for r in results)
        total_mrr = sum(r.metrics.mrr for r in results)

        n = len(results)

        return EvaluationMetrics(
            accuracy=total_accuracy / n,
            recall=total_recall / n,
            citation_accuracy=total_citation / n,
            completeness=total_completeness / n,
            precision=total_precision / n,
            f1_score=total_f1 / n,
            mrr=total_mrr / n
        )

    def compare_versions(
        self,
        report1: EvaluationReport,
        report2: EvaluationReport
    ) -> Dict[str, Any]:
        """
        版本对比

        Args:
            report1: 报告1 (基线版本)
            report2: 报告2 (新版本)

        Returns:
            对比结果
        """
        m1 = report1.aggregate_metrics
        m2 = report2.aggregate_metrics

        comparison = {
            "baseline_version": report1.version,
            "new_version": report2.version,
            "baseline_date": report1.timestamp.isoformat(),
            "new_date": report2.timestamp.isoformat(),
            "metrics_comparison": {
                "accuracy": {
                    "baseline": m1.accuracy,
                    "new": m2.accuracy,
                    "change": m2.accuracy - m1.accuracy,
                    "change_percent": ((m2.accuracy - m1.accuracy) / m1.accuracy * 100) if m1.accuracy > 0 else 0
                },
                "recall": {
                    "baseline": m1.recall,
                    "new": m2.recall,
                    "change": m2.recall - m1.recall,
                    "change_percent": ((m2.recall - m1.recall) / m1.recall * 100) if m1.recall > 0 else 0
                },
                "citation_accuracy": {
                    "baseline": m1.citation_accuracy,
                    "new": m2.citation_accuracy,
                    "change": m2.citation_accuracy - m1.citation_accuracy,
                    "change_percent": ((m2.citation_accuracy - m1.citation_accuracy) / m1.citation_accuracy * 100) if m1.citation_accuracy > 0 else 0
                },
                "completeness": {
                    "baseline": m1.completeness,
                    "new": m2.completeness,
                    "change": m2.completeness - m1.completeness,
                    "change_percent": ((m2.completeness - m1.completeness) / m1.completeness * 100) if m1.completeness > 0 else 0
                },
                "overall_score": {
                    "baseline": m1.overall_score(),
                    "new": m2.overall_score(),
                    "change": m2.overall_score() - m1.overall_score(),
                    "change_percent": ((m2.overall_score() - m1.overall_score()) / m1.overall_score() * 100) if m1.overall_score() > 0 else 0
                }
            },
            "regression_detected": m2.overall_score() < m1.overall_score() * 0.95  # 降低超过5%视为回归
        }

        # 保存对比结果
        comparison_path = self.results_dir / f"comparison_{report1.version}_vs_{report2.version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(comparison_path, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)

        logger.info(f"Version comparison saved to {comparison_path}")

        return comparison

    def generate_summary_report(self, report: EvaluationReport) -> str:
        """生成文本摘要报告"""
        m = report.aggregate_metrics

        summary = f"""
╔══════════════════════════════════════════════════════════╗
║           RAG系统评测报告 - {report.version}
╚══════════════════════════════════════════════════════════╝

📊 核心指标
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  准确率 (Accuracy):          {m.accuracy:.2%}  {'✅' if m.accuracy >= 0.8 else '⚠️' if m.accuracy >= 0.6 else '❌'}
  召回率 (Recall):            {m.recall:.2%}  {'✅' if m.recall >= 0.8 else '⚠️' if m.recall >= 0.6 else '❌'}
  引用正确率 (Citation):      {m.citation_accuracy:.2%}  {'✅' if m.citation_accuracy >= 0.8 else '⚠️' if m.citation_accuracy >= 0.6 else '❌'}
  回答完整度 (Completeness):  {m.completeness:.2%}  {'✅' if m.completeness >= 0.8 else '⚠️' if m.completeness >= 0.6 else '❌'}

📈 额外指标
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  精确率 (Precision):         {m.precision:.2%}
  F1分数:                     {m.f1_score:.2%}
  MRR:                        {m.mrr:.3f}

🎯 综合得分: {m.overall_score():.2%}

📋 测试统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  测试用例总数: {report.total_cases}
  评测时间: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

评测报告路径: {self.results_dir}
"""
        return summary
