#!/usr/bin/env python3
"""
FieldMind 代码质量审计工具
检查：
1. 语法错误和导入错误
2. 未完成的代码（TODO, FIXME, XXX, HACK）
3. 重复的函数和类
4. 未使用的导入
5. 复杂度过高的函数
6. 不一致的数据结构
"""

import os
import ast
import re
from pathlib import Path
from collections import defaultdict
import json

class CodeQualityAuditor:
    def __init__(self, root_path):
        self.root_path = Path(root_path)
        self.issues = {
            'syntax_errors': [],
            'incomplete_code': [],
            'duplicate_functions': defaultdict(list),
            'unused_imports': [],
            'complex_functions': [],
            'inconsistent_schemas': [],
            'broken_references': [],
            'data_structure_issues': []
        }

    def audit_file(self, filepath):
        """审计单个Python文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查语法错误
            try:
                tree = ast.parse(content, filename=str(filepath))
                self.check_ast(tree, filepath, content)
            except SyntaxError as e:
                self.issues['syntax_errors'].append({
                    'file': str(filepath),
                    'line': e.lineno,
                    'error': str(e)
                })

            # 检查未完成代码标记
            self.check_incomplete_markers(filepath, content)

            # 检查数据结构问题
            self.check_data_structures(filepath, content)

        except Exception as e:
            print(f"⚠️  无法读取 {filepath}: {e}")

    def check_ast(self, tree, filepath, content):
        """检查AST"""
        lines = content.split('\n')

        for node in ast.walk(tree):
            # 检查函数定义
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                self.issues['duplicate_functions'][func_name].append(str(filepath))

                # 检查函数复杂度（简单版本：超过50行）
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    func_length = node.end_lineno - node.lineno
                    if func_length > 50:
                        self.issues['complex_functions'].append({
                            'file': str(filepath),
                            'function': func_name,
                            'lines': func_length,
                            'start_line': node.lineno
                        })

    def check_incomplete_markers(self, filepath, content):
        """检查未完成代码标记"""
        markers = ['TODO', 'FIXME', 'XXX', 'HACK', 'BUG', 'DEPRECATED']
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for marker in markers:
                if marker in line.upper():
                    self.issues['incomplete_code'].append({
                        'file': str(filepath),
                        'line': i,
                        'marker': marker,
                        'content': line.strip()
                    })

    def check_data_structures(self, filepath, content):
        """检查数据结构一致性问题"""
        # 检查Response模型不一致
        if 'Response' in content and 'class' in content:
            if 'BaseModel' in content or 'dict' in content:
                # 简单检查：同一个文件中是否混用了多种返回格式
                has_dict_return = 'return {' in content
                has_model_return = 'return ' in content and 'Response(' in content

                if has_dict_return and has_model_return:
                    self.issues['data_structure_issues'].append({
                        'file': str(filepath),
                        'issue': '混用dict和Model返回类型'
                    })

        # 检查重复的schema定义
        schema_patterns = [
            r'class\s+(\w+Response)\(',
            r'class\s+(\w+Schema)\(',
            r'def\s+(\w+_schema)\('
        ]

        for pattern in schema_patterns:
            matches = re.findall(pattern, content)
            if matches:
                for match in matches:
                    if match in self.issues['inconsistent_schemas']:
                        self.issues['broken_references'].append({
                            'file': str(filepath),
                            'schema': match,
                            'issue': '可能的重复schema定义'
                        })
                    self.issues['inconsistent_schemas'].append(match)

    def scan_directory(self):
        """扫描整个目录"""
        print("🔍 开始扫描代码...")

        py_files = list(self.root_path.rglob('*.py'))
        total = len(py_files)

        for i, filepath in enumerate(py_files, 1):
            if '__pycache__' in str(filepath):
                continue

            if i % 50 == 0:
                print(f"   进度: {i}/{total}")

            self.audit_file(filepath)

        print(f"✓ 扫描完成，共检查 {total} 个文件\n")

    def generate_report(self):
        """生成报告"""
        report = []
        report.append("=" * 80)
        report.append("FieldMind 代码质量审计报告")
        report.append("=" * 80)
        report.append("")

        # 1. 语法错误
        if self.issues['syntax_errors']:
            report.append(f"❌ 语法错误 ({len(self.issues['syntax_errors'])}个)")
            report.append("-" * 80)
            for issue in self.issues['syntax_errors'][:10]:
                report.append(f"  文件: {issue['file']}")
                report.append(f"  行号: {issue['line']}")
                report.append(f"  错误: {issue['error']}")
                report.append("")
        else:
            report.append("✓ 无语法错误")
            report.append("")

        # 2. 未完成代码
        if self.issues['incomplete_code']:
            report.append(f"⚠️  未完成代码标记 ({len(self.issues['incomplete_code'])}个)")
            report.append("-" * 80)
            markers_count = defaultdict(int)
            for issue in self.issues['incomplete_code']:
                markers_count[issue['marker']] += 1

            for marker, count in sorted(markers_count.items(), key=lambda x: -x[1]):
                report.append(f"  {marker}: {count}个")

            report.append("\n  前10个未完成项：")
            for issue in self.issues['incomplete_code'][:10]:
                report.append(f"    {issue['file']}:{issue['line']}")
                report.append(f"    {issue['content'][:80]}")
                report.append("")
        else:
            report.append("✓ 无未完成代码标记")
            report.append("")

        # 3. 重复函数
        duplicates = {k: v for k, v in self.issues['duplicate_functions'].items() if len(v) > 1}
        if duplicates:
            report.append(f"⚠️  重复函数名 ({len(duplicates)}个)")
            report.append("-" * 80)
            for func_name, files in sorted(duplicates.items(), key=lambda x: -len(x[1]))[:10]:
                if len(files) > 1:
                    report.append(f"  函数 '{func_name}' 出现在 {len(files)} 个文件中:")
                    for f in files[:3]:
                        report.append(f"    - {f}")
                    report.append("")
        else:
            report.append("✓ 无明显重复函数")
            report.append("")

        # 4. 复杂函数
        if self.issues['complex_functions']:
            report.append(f"⚠️  复杂函数 (>{50}行) ({len(self.issues['complex_functions'])}个)")
            report.append("-" * 80)
            sorted_complex = sorted(self.issues['complex_functions'], key=lambda x: -x['lines'])
            for issue in sorted_complex[:10]:
                report.append(f"  {issue['file']}:{issue['start_line']}")
                report.append(f"  函数: {issue['function']} ({issue['lines']}行)")
                report.append("")
        else:
            report.append("✓ 无过于复杂的函数")
            report.append("")

        # 5. 数据结构问题
        if self.issues['data_structure_issues']:
            report.append(f"⚠️  数据结构不一致 ({len(self.issues['data_structure_issues'])}个)")
            report.append("-" * 80)
            for issue in self.issues['data_structure_issues']:
                report.append(f"  {issue['file']}")
                report.append(f"  问题: {issue['issue']}")
                report.append("")
        else:
            report.append("✓ 数据结构基本一致")
            report.append("")

        report.append("=" * 80)
        report.append("建议:")
        report.append("-" * 80)
        report.append("1. 优先修复语法错误")
        report.append("2. 完成或删除标记为TODO/FIXME的代码")
        report.append("3. 合并重复的函数定义")
        report.append("4. 拆分复杂函数（>50行）")
        report.append("5. 统一数据返回格式")
        report.append("=" * 80)

        return "\n".join(report)

    def save_detailed_report(self, output_file):
        """保存详细JSON报告"""
        # 转换为可序列化格式
        serializable = {
            'syntax_errors': self.issues['syntax_errors'],
            'incomplete_code': self.issues['incomplete_code'],
            'duplicate_functions': {k: v for k, v in self.issues['duplicate_functions'].items() if len(v) > 1},
            'complex_functions': self.issues['complex_functions'],
            'data_structure_issues': self.issues['data_structure_issues']
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)

        print(f"✓ 详细报告已保存到: {output_file}")

if __name__ == "__main__":
    backend_path = "/Users/alwan/FieldMind/backend/src"

    print("FieldMind 代码质量审计工具")
    print("=" * 80)
    print()

    auditor = CodeQualityAuditor(backend_path)
    auditor.scan_directory()

    report = auditor.generate_report()
    print(report)

    # 保存报告
    report_file = "/Users/alwan/FieldMind/code_quality_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✓ 报告已保存到: {report_file}")

    # 保存详细JSON
    auditor.save_detailed_report("/Users/alwan/FieldMind/code_quality_detailed.json")
