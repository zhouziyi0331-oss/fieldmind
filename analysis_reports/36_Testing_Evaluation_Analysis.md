# Testing & Evaluation Framework 深度分析报告

**插件名称**: Testing & Evaluation Framework for LLM Applications  
**类别**: 测试和评估系统  
**分析日期**: 2026-08-30

---

## 1. 插件概述

### 核心定位
测试与评估框架为 LLM 应用提供系统化的质量保证体系，包括单元测试、集成测试、性能测试、质量评估等，确保应用的可靠性和准确性。

### 核心特点
- **单元测试**: Assert-based 测试
- **集成测试**: 端到端测试
- **回归测试**: 持续验证
- **性能测试**: 延迟和吞吐量
- **质量评估**: 多维度指标
- **A/B测试**: 对比评估

### 架构设计
```
Testing Framework
├── Test Types (测试类型)
│   ├── Unit Tests
│   ├── Integration Tests
│   ├── Regression Tests
│   └── Performance Tests
├── Evaluation Metrics (评估指标)
│   ├── Accuracy Metrics
│   ├── Quality Metrics
│   ├── Performance Metrics
│   └── Cost Metrics
├── Test Data (测试数据)
│   ├── Test Cases
│   ├── Golden Sets
│   ├── Synthetic Data
│   └── Edge Cases
├── Evaluation Methods (评估方法)
│   ├── Rule-based
│   ├── Model-based
│   ├── Human Evaluation
│   └── LLM-as-Judge
└── Reporting (报告)
    ├── Test Results
    ├── Metrics Dashboard
    ├── Failure Analysis
    └── Recommendations
```

---

## 2. 核心概念

### 2.1 基础测试框架

```python
import unittest
from typing import Callable, List, Dict

class LLMTestCase:
    """LLM 测试用例"""
    
    def __init__(
        self,
        name: str,
        input: str,
        expected_output: str = None,
        expected_contains: List[str] = None,
        evaluator: Callable = None
    ):
        self.name = name
        self.input = input
        self.expected_output = expected_output
        self.expected_contains = expected_contains
        self.evaluator = evaluator
    
    def run(self, llm_function: Callable) -> Dict:
        """运行测试"""
        # 执行
        actual_output = llm_function(self.input)
        
        # 评估
        if self.evaluator:
            passed = self.evaluator(self.input, actual_output, self.expected_output)
        elif self.expected_output:
            passed = actual_output.strip() == self.expected_output.strip()
        elif self.expected_contains:
            passed = all(phrase in actual_output for phrase in self.expected_contains)
        else:
            passed = True  # 仅执行，不评估
        
        return {
            "name": self.name,
            "input": self.input,
            "expected": self.expected_output,
            "actual": actual_output,
            "passed": passed
        }

class LLMTestSuite:
    """LLM 测试套件"""
    
    def __init__(self, name: str):
        self.name = name
        self.test_cases = []
    
    def add_test(self, test_case: LLMTestCase):
        """添加测试用例"""
        self.test_cases.append(test_case)
    
    def run_all(self, llm_function: Callable) -> Dict:
        """运行所有测试"""
        results = []
        
        for test_case in self.test_cases:
            result = test_case.run(llm_function)
            results.append(result)
        
        # 统计
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        
        return {
            "suite": self.name,
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0,
            "results": results
        }

# 使用示例
suite = LLMTestSuite("Sentiment Analysis Tests")

suite.add_test(LLMTestCase(
    name="positive_sentiment",
    input="This product is amazing!",
    expected_output="positive"
))

suite.add_test(LLMTestCase(
    name="negative_sentiment",
    input="Terrible experience, would not recommend.",
    expected_output="negative"
))

# 运行测试
results = suite.run_all(my_sentiment_classifier)
print(f"Pass Rate: {results['pass_rate']:.2%}")
```

### 2.2 评估指标

```python
from typing import List
import numpy as np

class EvaluationMetrics:
    """评估指标计算"""
    
    @staticmethod
    def exact_match(predictions: List[str], references: List[str]) -> float:
        """精确匹配率"""
        matches = sum(
            p.strip().lower() == r.strip().lower()
            for p, r in zip(predictions, references)
        )
        return matches / len(predictions) if predictions else 0.0
    
    @staticmethod
    def contains_match(predictions: List[str], references: List[str]) -> float:
        """包含匹配率"""
        matches = sum(
            r.lower() in p.lower()
            for p, r in zip(predictions, references)
        )
        return matches / len(predictions) if predictions else 0.0
    
    @staticmethod
    def semantic_similarity(
        predictions: List[str],
        references: List[str],
        model = None
    ) -> float:
        """语义相似度"""
        from sentence_transformers import SentenceTransformer
        
        if model is None:
            model = SentenceTransformer('all-MiniLM-L6-v2')
        
        pred_embeddings = model.encode(predictions)
        ref_embeddings = model.encode(references)
        
        # 计算余弦相似度
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = [
            cosine_similarity([pred], [ref])[0][0]
            for pred, ref in zip(pred_embeddings, ref_embeddings)
        ]
        
        return np.mean(similarities)
    
    @staticmethod
    def bleu_score(predictions: List[str], references: List[str]) -> float:
        """BLEU 分数"""
        from nltk.translate.bleu_score import sentence_bleu
        
        scores = []
        for pred, ref in zip(predictions, references):
            pred_tokens = pred.split()
            ref_tokens = [ref.split()]
            score = sentence_bleu(ref_tokens, pred_tokens)
            scores.append(score)
        
        return np.mean(scores)
    
    @staticmethod
    def rouge_score(predictions: List[str], references: List[str]) -> Dict:
        """ROUGE 分数"""
        from rouge import Rouge
        
        rouge = Rouge()
        scores = rouge.get_scores(predictions, references, avg=True)
        
        return {
            "rouge-1": scores["rouge-1"]["f"],
            "rouge-2": scores["rouge-2"]["f"],
            "rouge-l": scores["rouge-l"]["f"]
        }
    
    @staticmethod
    def perplexity(model, texts: List[str]) -> float:
        """困惑度"""
        import torch
        
        total_loss = 0
        total_tokens = 0
        
        for text in texts:
            inputs = model.tokenizer(text, return_tensors="pt")
            with torch.no_grad():
                outputs = model(**inputs, labels=inputs["input_ids"])
            
            loss = outputs.loss
            num_tokens = inputs["input_ids"].size(1)
            
            total_loss += loss.item() * num_tokens
            total_tokens += num_tokens
        
        avg_loss = total_loss / total_tokens
        perplexity = np.exp(avg_loss)
        
        return perplexity
```

### 2.3 LLM-as-Judge

```python
class LLMJudge:
    """使用 LLM 作为评判"""
    
    def __init__(self, judge_llm):
        self.judge_llm = judge_llm
    
    def evaluate_quality(
        self,
        query: str,
        response: str,
        criteria: List[str] = None
    ) -> Dict:
        """评估质量"""
        
        if criteria is None:
            criteria = [
                "准确性：回答是否准确？",
                "完整性：回答是否完整？",
                "相关性：回答是否相关？",
                "清晰度：回答是否清晰易懂？"
            ]
        
        prompt = f"""
评估以下回答的质量：

问题: {query}

回答: {response}

评估标准:
{chr(10).join(f"{i+1}. {c}" for i, c in enumerate(criteria))}

对每个标准，给出评分（1-5分）和简短理由。

评估:
"""
        
        evaluation = self.judge_llm.complete(prompt, temperature=0.1)
        
        # 解析评估结果
        scores = self._parse_evaluation(evaluation)
        
        return {
            "evaluation": evaluation,
            "scores": scores,
            "average_score": np.mean(list(scores.values()))
        }
    
    def _parse_evaluation(self, evaluation: str) -> Dict[str, float]:
        """解析评估结果"""
        import re
        
        scores = {}
        
        # 简化解析：查找 "X分" 模式
        pattern = r"(\d+)\s*分"
        matches = re.findall(pattern, evaluation)
        
        criteria_names = ["准确性", "完整性", "相关性", "清晰度"]
        
        for i, score in enumerate(matches[:len(criteria_names)]):
            scores[criteria_names[i]] = float(score)
        
        return scores
    
    def compare_responses(
        self,
        query: str,
        response_a: str,
        response_b: str
    ) -> str:
        """比较两个回答"""
        
        prompt = f"""
比较以下两个回答，判断哪个更好：

问题: {query}

回答A: {response_a}

回答B: {response_b}

请选择：
1. A更好
2. B更好
3. 两者相当

选择及理由:
"""
        
        judgment = self.judge_llm.complete(prompt, temperature=0)
        
        return judgment
```

### 2.4 回归测试

```python
import json
from datetime import datetime

class RegressionTestManager:
    """回归测试管理器"""
    
    def __init__(self, baseline_file: str):
        self.baseline_file = baseline_file
        self.baseline = self._load_baseline()
    
    def _load_baseline(self) -> Dict:
        """加载基线"""
        try:
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_baseline(self):
        """保存基线"""
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baseline, f, indent=2)
    
    def run_regression_tests(
        self,
        test_suite: LLMTestSuite,
        llm_function: Callable,
        tolerance: float = 0.05
    ) -> Dict:
        """运行回归测试"""
        
        # 运行当前测试
        current_results = test_suite.run_all(llm_function)
        
        # 获取基线
        baseline_pass_rate = self.baseline.get(test_suite.name, {}).get("pass_rate", 0)
        
        # 比较
        current_pass_rate = current_results["pass_rate"]
        regression_detected = current_pass_rate < baseline_pass_rate - tolerance
        
        # 更新基线（如果更好或首次运行）
        if test_suite.name not in self.baseline or current_pass_rate >= baseline_pass_rate:
            self.baseline[test_suite.name] = {
                "pass_rate": current_pass_rate,
                "timestamp": datetime.utcnow().isoformat(),
                "results": current_results["results"]
            }
            self._save_baseline()
        
        return {
            "current_pass_rate": current_pass_rate,
            "baseline_pass_rate": baseline_pass_rate,
            "regression_detected": regression_detected,
            "delta": current_pass_rate - baseline_pass_rate,
            "results": current_results
        }
```

### 2.5 性能测试

```python
import time
from statistics import mean, stdev

class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.results = []
    
    def measure_latency(
        self,
        func: Callable,
        inputs: List,
        warmup: int = 3,
        iterations: int = 10
    ) -> Dict:
        """测量延迟"""
        
        # 预热
        for _ in range(warmup):
            func(inputs[0])
        
        # 测量
        latencies = []
        
        for _ in range(iterations):
            for input_data in inputs:
                start = time.time()
                func(input_data)
                latency = (time.time() - start) * 1000  # 毫秒
                latencies.append(latency)
        
        return {
            "mean": mean(latencies),
            "std": stdev(latencies) if len(latencies) > 1 else 0,
            "min": min(latencies),
            "max": max(latencies),
            "p50": np.percentile(latencies, 50),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99)
        }
    
    def measure_throughput(
        self,
        func: Callable,
        inputs: List,
        duration: int = 60
    ) -> float:
        """测量吞吐量（请求/秒）"""
        
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < duration:
            for input_data in inputs:
                func(input_data)
                count += 1
                
                if time.time() - start_time >= duration:
                    break
        
        elapsed = time.time() - start_time
        throughput = count / elapsed
        
        return throughput
    
    def stress_test(
        self,
        func: Callable,
        inputs: List,
        concurrent_requests: int = 10,
        duration: int = 60
    ) -> Dict:
        """压力测试"""
        import concurrent.futures
        
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "latencies": []
        }
        
        def worker():
            for input_data in inputs:
                start = time.time()
                try:
                    func(input_data)
                    latency = (time.time() - start) * 1000
                    results["latencies"].append(latency)
                    results["successful_requests"] += 1
                except Exception as e:
                    results["failed_requests"] += 1
                
                results["total_requests"] += 1
        
        # 并发执行
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = []
            
            while time.time() - start_time < duration:
                future = executor.submit(worker)
                futures.append(future)
            
            # 等待完成
            concurrent.futures.wait(futures)
        
        # 计算统计
        if results["latencies"]:
            results["mean_latency"] = mean(results["latencies"])
            results["p95_latency"] = np.percentile(results["latencies"], 95)
        
        results["success_rate"] = (
            results["successful_requests"] / results["total_requests"]
            if results["total_requests"] > 0 else 0
        )
        
        return results
```

---

## 3. 核心算法

### 3.1 自动化测试生成

```python
def generate_test_cases(
    function_description: str,
    num_cases: int = 10,
    llm = None
) -> List[LLMTestCase]:
    """
    自动生成测试用例
    
    使用 LLM 生成测试输入和预期输出
    """
    prompt = f"""
为以下功能生成 {num_cases} 个测试用例：

功能描述: {function_description}

每个测试用例应包含：
1. 测试名称
2. 输入
3. 预期输出

格式:
测试1:
名称: ...
输入: ...
预期: ...

生成测试用例:
"""
    
    response = llm.complete(prompt, temperature=0.7)
    
    # 解析测试用例
    test_cases = parse_test_cases(response)
    
    return test_cases

def parse_test_cases(response: str) -> List[LLMTestCase]:
    """解析测试用例"""
    test_cases = []
    
    # 简化解析逻辑
    current_test = {}
    
    for line in response.split('\n'):
        line = line.strip()
        
        if line.startswith('名称:'):
            if current_test:
                test_cases.append(LLMTestCase(**current_test))
            current_test = {"name": line.split(':', 1)[1].strip()}
        
        elif line.startswith('输入:'):
            current_test["input"] = line.split(':', 1)[1].strip()
        
        elif line.startswith('预期:'):
            current_test["expected_output"] = line.split(':', 1)[1].strip()
    
    if current_test:
        test_cases.append(LLMTestCase(**current_test))
    
    return test_cases

# 时间复杂度: O(n) - n为生成的测试用例数
```

### 3.2 对抗性测试生成

```python
def generate_adversarial_tests(
    base_input: str,
    num_variations: int = 5,
    llm = None
) -> List[str]:
    """
    生成对抗性测试
    
    创建边界情况和异常输入
    """
    prompt = f"""
基于以下输入，生成 {num_variations} 个对抗性测试输入：

原始输入: {base_input}

生成变体应包括：
- 边界情况
- 异常输入
- 模糊/歧义输入
- 对抗性输入

变体:
1.
"""
    
    response = llm.complete(prompt, temperature=0.8)
    
    # 解析变体
    variations = []
    for line in response.split('\n'):
        line = line.strip()
        if line and line[0].isdigit():
            variation = line.split('.', 1)[1].strip()
            variations.append(variation)
    
    return variations

# 时间复杂度: O(1) - LLM调用
```

---

## 4. 可复用组件清单

| 组件 | 功能 | 复用优先级 |
|------|------|-----------|
| Test Suite | 测试套件框架 | ⭐⭐⭐⭐⭐ |
| Evaluation Metrics | 评估指标库 | ⭐⭐⭐⭐⭐ |
| LLM-as-Judge | LLM评判器 | ⭐⭐⭐⭐⭐ |
| Regression Tester | 回归测试 | ⭐⭐⭐⭐⭐ |
| Performance Tester | 性能测试 | ⭐⭐⭐⭐⭐ |
| Test Generator | 自动测试生成 | ⭐⭐⭐⭐ |
| Adversarial Tester | 对抗性测试 | ⭐⭐⭐⭐ |
| Semantic Similarity | 语义相似度 | ⭐⭐⭐⭐⭐ |
| BLEU/ROUGE | 文本评估指标 | ⭐⭐⭐⭐ |
| Stress Tester | 压力测试 | ⭐⭐⭐⭐ |

---

## 5. 核心学习

### 关键概念
1. **LLM测试框架** - 专门的测试结构
2. **多维度评估** - 准确性、质量、性能
3. **LLM-as-Judge** - 使用LLM评估
4. **回归测试** - 持续验证
5. **性能基准** - 延迟和吞吐量

### 核心算法
1. 语义相似度评估
2. LLM评判算法
3. 自动化测试生成
4. 回归检测算法
5. 性能测试方法

### 对 FieldMind 的价值
- ⭐⭐⭐⭐⭐ 测试框架
- ⭐⭐⭐⭐⭐ 评估指标体系
- ⭐⭐⭐⭐⭐ LLM评判
- ⭐⭐⭐⭐⭐ 回归测试
- ⭐⭐⭐⭐⭐ 性能测试

---

**分析完成时间**: 2026-08-30  
**已完成插件数**: 36/40 (90%)  
**剩余**: 4个插件
