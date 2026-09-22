#!/usr/bin/env python3
"""
扫描Python文件，识别缺少类型注解的函数
"""
import os
import ast
import sys
from typing import List, Dict, Tuple
from pathlib import Path


class TypeAnnotationScanner(ast.NodeVisitor):
    """AST访问器，检测函数的类型注解"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
        self.total_functions = 0
        self.annotated_functions = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""
        self.total_functions += 1

        # 跳过特殊方法（__init__, __str__等）
        if node.name.startswith('__') and node.name.endswith('__'):
            self.generic_visit(node)
            return

        # 检查返回类型注解
        has_return_annotation = node.returns is not None

        # 检查参数类型注解（跳过self和cls）
        params_with_annotations = 0
        total_params = 0

        for arg in node.args.args:
            if arg.arg in ('self', 'cls'):
                continue
            total_params += 1
            if arg.annotation is not None:
                params_with_annotations += 1

        # 如果有参数但缺少注解，或者缺少返回类型注解
        has_params = total_params > 0
        missing_param_annotations = has_params and params_with_annotations < total_params
        missing_return_annotation = not has_return_annotation

        if missing_param_annotations or missing_return_annotation:
            issues = []
            if missing_param_annotations:
                issues.append(f"参数注解 {params_with_annotations}/{total_params}")
            if missing_return_annotation:
                issues.append("返回类型")

            self.issues.append({
                'function': node.name,
                'line': node.lineno,
                'missing': issues,
                'has_params': has_params,
                'param_coverage': f"{params_with_annotations}/{total_params}" if has_params else "0/0"
            })
        else:
            self.annotated_functions += 1

        self.generic_visit(node)


def scan_file(filepath: str) -> Dict:
    """扫描单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content, filename=filepath)
        scanner = TypeAnnotationScanner(filepath)
        scanner.visit(tree)

        return {
            'filepath': filepath,
            'total_functions': scanner.total_functions,
            'annotated_functions': scanner.annotated_functions,
            'issues': scanner.issues,
            'coverage': scanner.annotated_functions / scanner.total_functions * 100
                       if scanner.total_functions > 0 else 100
        }
    except Exception as e:
        return {
            'filepath': filepath,
            'error': str(e),
            'total_functions': 0,
            'annotated_functions': 0,
            'issues': [],
            'coverage': 0
        }


def scan_directory(directory: str, patterns: List[str] = None) -> List[Dict]:
    """扫描目录下的所有Python文件"""
    results = []

    if patterns is None:
        patterns = ['api', 'services', 'agents', 'tools']

    for root, dirs, files in os.walk(directory):
        # 跳过__pycache__等
        dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]

        # 优先扫描核心目录
        should_scan = any(pattern in root for pattern in patterns)

        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                filepath = os.path.join(root, file)

                # 如果指定了patterns，只扫描匹配的文件
                if patterns and not should_scan:
                    continue

                result = scan_file(filepath)
                if result['total_functions'] > 0:
                    results.append(result)

    return results


def main():
    project_dir = 'FieldMind/backend/src/app'

    if not os.path.exists(project_dir):
        print(f"❌ 目录不存在: {project_dir}")
        sys.exit(1)

    print("🔍 扫描类型注解...")
    print(f"📂 目录: {project_dir}\n")

    # 扫描核心模块
    results = scan_directory(project_dir, patterns=['api', 'services', 'agents', 'tools'])

    # 按覆盖率排序
    results.sort(key=lambda x: x['coverage'])

    # 统计
    total_files = len(results)
    total_functions = sum(r['total_functions'] for r in results)
    total_annotated = sum(r['annotated_functions'] for r in results)
    overall_coverage = total_annotated / total_functions * 100 if total_functions > 0 else 100

    print(f"📊 总体统计:")
    print(f"  文件数: {total_files}")
    print(f"  函数数: {total_functions}")
    print(f"  已注解: {total_annotated}")
    print(f"  覆盖率: {overall_coverage:.1f}%\n")

    # 输出需要修复的文件（覆盖率 < 80%）
    print("⚠️  需要添加类型注解的文件 (覆盖率 < 80%):\n")

    needs_fix = [r for r in results if r['coverage'] < 80]

    if not needs_fix:
        print("✅ 所有文件类型注解覆盖率都 >= 80%")
    else:
        for result in needs_fix:
            rel_path = result['filepath'].replace(project_dir + '/', '')
            print(f"📄 {rel_path}")
            print(f"   覆盖率: {result['coverage']:.1f}% ({result['annotated_functions']}/{result['total_functions']})")

            # 显示前3个缺少注解的函数
            if result['issues']:
                print(f"   缺少注解的函数:")
                for issue in result['issues'][:3]:
                    print(f"     - {issue['function']}() 行{issue['line']}: {', '.join(issue['missing'])}")
                if len(result['issues']) > 3:
                    print(f"     ... 还有 {len(result['issues']) - 3} 个函数")
            print()

    # 生成详细报告
    with open('TYPE_ANNOTATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write("# 类型注解扫描报告\n\n")
        f.write(f"**扫描时间**: 2026-08-17\n")
        f.write(f"**扫描目录**: `{project_dir}`\n\n")

        f.write("## 总体统计\n\n")
        f.write(f"| 指标 | 数值 |\n")
        f.write(f"|------|------|\n")
        f.write(f"| 文件数 | {total_files} |\n")
        f.write(f"| 函数总数 | {total_functions} |\n")
        f.write(f"| 已完全注解 | {total_annotated} |\n")
        f.write(f"| 覆盖率 | {overall_coverage:.1f}% |\n")
        f.write(f"| 需修复文件 | {len(needs_fix)} |\n\n")

        if needs_fix:
            f.write("## 需要添加类型注解的文件\n\n")
            f.write("按覆盖率从低到高排序：\n\n")

            for i, result in enumerate(needs_fix, 1):
                rel_path = result['filepath'].replace(project_dir + '/', '')
                f.write(f"### {i}. `{rel_path}`\n\n")
                f.write(f"- **覆盖率**: {result['coverage']:.1f}%\n")
                f.write(f"- **函数数**: {result['total_functions']}\n")
                f.write(f"- **已注解**: {result['annotated_functions']}\n")
                f.write(f"- **缺少注解**: {len(result['issues'])}\n\n")

                if result['issues']:
                    f.write("**缺少注解的函数**:\n\n")
                    for issue in result['issues']:
                        f.write(f"- `{issue['function']}()` (行{issue['line']})\n")
                        f.write(f"  - 缺少: {', '.join(issue['missing'])}\n")
                    f.write("\n")
        else:
            f.write("## ✅ 所有文件类型注解覆盖率都很好\n\n")
            f.write("所有核心模块的类型注解覆盖率都 >= 80%\n")

        f.write("\n## 建议\n\n")
        f.write("### 优先级\n\n")
        f.write("1. **P0 - API路由** (`api/`): 直接面向用户，类型安全最重要\n")
        f.write("2. **P1 - 服务层** (`services/`): 核心业务逻辑\n")
        f.write("3. **P2 - Agent层** (`agents/`): 工作流编排\n")
        f.write("4. **P3 - 工具类** (`tools/`): 辅助功能\n\n")

        f.write("### 添加类型注解的好处\n\n")
        f.write("- ✅ IDE自动补全更准确\n")
        f.write("- ✅ 静态类型检查（mypy）可以发现潜在bug\n")
        f.write("- ✅ 代码可读性提升\n")
        f.write("- ✅ 重构更安全\n")

    print(f"📄 详细报告已保存到: TYPE_ANNOTATION_REPORT.md")


if __name__ == '__main__':
    main()
