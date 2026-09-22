"""
代码质量自动审查服务
基于 alibaba/open-code-review 的理念
"""
import ast
import re
from typing import List, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class CodeReviewService:
    """
    代码审查服务

    检查项：
    1. 复杂度检查
    2. 代码风格
    3. 安全漏洞
    4. 最佳实践
    5. 文档完整性
    """
    def __init__(self, use_workflow_engine: bool = True):

        self.use_workflow_engine = use_workflow_engine

        if use_workflow_engine:
            from app.services.workflow_engine import WorkflowEngine
            self.workflow_engine = WorkflowEngine(max_workers=4)
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, List]:
        """加载审查规则"""
        return {
            "complexity": [
                {"name": "函数复杂度", "threshold": 10},
                {"name": "函数长度", "threshold": 50},
                {"name": "类方法数", "threshold": 20},
            ],
            "security": [
                {"pattern": r"eval\(", "message": "避免使用 eval()"},
                {"pattern": r"exec\(", "message": "避免使用 exec()"},
                {"pattern": r"__import__", "message": "避免动态导入"},
                {"pattern": r"pickle\.loads", "message": "pickle 反序列化存在风险"},
            ],
            "best_practices": [
                {"pattern": r"except\s*:", "message": "避免捕获所有异常"},
                {"pattern": r"TODO|FIXME|XXX", "message": "待处理的 TODO"},
                {"pattern": r"print\(", "message": "应使用 logger 而非 print"},
            ],
        }

    def review_file(self, file_path: str) -> Dict[str, Any]:
        """
        审查单个文件

        Returns:
            {
                "file": str,
                "issues": [
                    {
                        "type": "complexity|security|style|docs",
                        "severity": "high|medium|low",
                        "line": int,
                        "message": str
                    }
                ],
                "score": float  # 0-100
            }
        """
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 1. 复杂度检查
            issues.extend(self._check_complexity(content, file_path))

            # 2. 安全检查
            issues.extend(self._check_security(content))

            # 3. 最佳实践检查
            issues.extend(self._check_best_practices(content))

            # 4. 文档检查
            issues.extend(self._check_documentation(content))

            # 计算分数
            score = self._calculate_score(issues, content)

            return {
                "file": file_path,
                "issues": issues,
                "score": score,
                "total_issues": len(issues),
            }

        except Exception as e:
            logger.error(f"审查文件失败 {file_path}: {e}")
            return {
                "file": file_path,
                "error": str(e),
                "issues": [],
                "score": 0,
            }

    def _check_complexity(self, content: str, file_path: str) -> List[Dict]:
        """检查复杂度"""
        issues = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 检查函数复杂度
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:
                        issues.append({
                            "type": "complexity",
                            "severity": "high" if complexity > 20 else "medium",
                            "line": node.lineno,
                            "message": f"函数 '{node.name}' 复杂度过高: {complexity}",
                        })

                    # 检查函数长度
                    length = node.end_lineno - node.lineno if node.end_lineno else 0
                    if length > 50:
                        issues.append({
                            "type": "complexity",
                            "severity": "medium" if length < 100 else "high",
                            "line": node.lineno,
                            "message": f"函数 '{node.name}' 过长: {length} 行",
                        })

                elif isinstance(node, ast.ClassDef):
                    # 检查类方法数
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 20:
                        issues.append({
                            "type": "complexity",
                            "severity": "medium",
                            "line": node.lineno,
                            "message": f"类 '{node.name}' 方法过多: {len(methods)}",
                        })

        except SyntaxError:
            pass

        return issues

    def _calculate_complexity(self, node) -> int:
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _check_security(self, content: str) -> List[Dict]:
        """安全检查"""
        issues = []

        for rule in self.rules["security"]:
            pattern = rule["pattern"]
            message = rule["message"]

            for i, line in enumerate(content.split('\n'), 1):
                if re.search(pattern, line):
                    issues.append({
                        "type": "security",
                        "severity": "high",
                        "line": i,
                        "message": message,
                    })

        return issues

    def _check_best_practices(self, content: str) -> List[Dict]:
        """最佳实践检查"""
        issues = []

        for rule in self.rules["best_practices"]:
            pattern = rule["pattern"]
            message = rule["message"]

            for i, line in enumerate(content.split('\n'), 1):
                if re.search(pattern, line):
                    issues.append({
                        "type": "best_practice",
                        "severity": "low",
                        "line": i,
                        "message": message,
                    })

        return issues

    def _check_documentation(self, content: str) -> List[Dict]:
        """文档检查"""
        issues = []

        try:
            tree = ast.parse(content)

            # 检查模块文档
            if not ast.get_docstring(tree):
                issues.append({
                    "type": "documentation",
                    "severity": "low",
                    "line": 1,
                    "message": "缺少模块文档字符串",
                })

            # 检查函数文档
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node) and not node.name.startswith('_'):
                        issues.append({
                            "type": "documentation",
                            "severity": "low",
                            "line": node.lineno,
                            "message": f"函数 '{node.name}' 缺少文档字符串",
                        })

        except SyntaxError:
            pass

        return issues

    def _calculate_score(self, issues: List[Dict], content: str) -> float:
        """计算代码质量分数"""
        base_score = 100.0

        # 扣分规则
        for issue in issues:
            if issue["severity"] == "high":
                base_score -= 10
            elif issue["severity"] == "medium":
                base_score -= 5
            else:
                base_score -= 2

        # 最低分 0
        return max(0.0, base_score)

    def review_project(self, project_dir: str) -> Dict[str, Any]:
        """
        审查整个项目

        Returns:
            {
                "files": [...],
                "summary": {
                    "total_files": int,
                    "total_issues": int,
                    "avg_score": float,
                    "high_severity": int,
                    "medium_severity": int,
                    "low_severity": int
                }
            }
        """
        project_path = Path(project_dir)
        python_files = list(project_path.rglob("*.py"))

        results = []
        total_issues = 0
        total_score = 0
        severity_counts = {"high": 0, "medium": 0, "low": 0}

        for file_path in python_files:
            if "__pycache__" in str(file_path) or "venv" in str(file_path):
                continue

            result = self.review_file(str(file_path))
            results.append(result)

            total_issues += result.get("total_issues", 0)
            total_score += result.get("score", 0)

            for issue in result.get("issues", []):
                severity_counts[issue["severity"]] += 1

        return {
            "files": results,
            "summary": {
                "total_files": len(results),
                "total_issues": total_issues,
                "avg_score": total_score / len(results) if results else 0,
                "high_severity": severity_counts["high"],
                "medium_severity": severity_counts["medium"],
                "low_severity": severity_counts["low"],
            },
        }

    def generate_report(self, review_result: Dict) -> str:
        """生成审查报告"""
        lines = []
        lines.append("# 代码质量审查报告")
        lines.append("")
        lines.append("## 总览")
        lines.append("")

        summary = review_result["summary"]
        lines.append(f"- 审查文件数: {summary['total_files']}")
        lines.append(f"- 总问题数: {summary['total_issues']}")
        lines.append(f"- 平均分数: {summary['avg_score']:.1f}/100")
        lines.append(f"- 高严重性: {summary['high_severity']}")
        lines.append(f"- 中严重性: {summary['medium_severity']}")
        lines.append(f"- 低严重性: {summary['low_severity']}")
        lines.append("")

        lines.append("## 详细问题")
        lines.append("")

        for file_result in review_result["files"]:
            if file_result.get("issues"):
                lines.append(f"### {file_result['file']}")
                lines.append(f"分数: {file_result['score']:.1f}/100")
                lines.append("")

                for issue in file_result["issues"]:
                    severity_icon = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🔵"
                    }[issue["severity"]]

                    lines.append(
                        f"- {severity_icon} 行 {issue['line']}: "
                        f"{issue['message']} [{issue['type']}]"
                    )

                lines.append("")

        return "\n".join(lines)


# 全局实例
code_review_service = CodeReviewService()
