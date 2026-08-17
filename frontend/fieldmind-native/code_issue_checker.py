#!/usr/bin/env python3
"""
检查前端代码中的潜在问题：
1. 硬编码数据（demoList, mockData等）
2. 未使用设计系统的颜色/字体/间距
3. 缺少错误处理
4. 缺少加载状态
5. 潜在的类型错误
"""
import re
import os
from pathlib import Path
from collections import defaultdict

class CodeIssueChecker:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.issues = defaultdict(list)

    def check_file(self, file_path):
        """检查单个文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')

        relative_path = file_path.relative_to(self.base_dir)

        # 1. 检查硬编码数据
        self._check_hardcoded_data(relative_path, content, lines)

        # 2. 检查未使用设计系统
        self._check_design_tokens(relative_path, content, lines)

        # 3. 检查错误处理
        self._check_error_handling(relative_path, content, lines)

        # 4. 检查加载状态
        self._check_loading_states(relative_path, content, lines)

        # 5. 检查API调用
        self._check_api_calls(relative_path, content, lines)

    def _check_hardcoded_data(self, file_path, content, lines):
        """检查硬编码数据"""
        patterns = [
            (r'\.demoList', '使用硬编码的demoList'),
            (r'\.mockData', '使用硬编码的mockData'),
            (r'\.sampleData', '使用硬编码的sampleData'),
            (r'static let demo\s*=', '定义硬编码的demo数据'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    self.issues[file_path].append({
                        'line': i,
                        'type': '硬编码数据',
                        'message': message,
                        'code': line.strip()
                    })

    def _check_design_tokens(self, file_path, content, lines):
        """检查是否使用设计系统"""
        # 检查直接使用系统颜色
        system_colors = [
            (r'Color\.red\b(?!\.)', '使用系统颜色Color.red，应使用.fmError'),
            (r'Color\.green\b(?!\.)', '使用系统颜色Color.green，应使用.fmSuccess'),
            (r'Color\.blue\b(?!\.)', '使用系统颜色Color.blue，应使用.fmBlue'),
            (r'Color\.orange\b(?!\.)', '使用系统颜色Color.orange，应使用.fmOrange'),
            (r'Color\.purple\b(?!\.)', '使用系统颜色Color.purple，应使用.fmPurple'),
            (r'Color\.yellow\b(?!\.)', '使用系统颜色Color.yellow，应使用.fmYellow'),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, message in system_colors:
                if re.search(pattern, line):
                    self.issues[file_path].append({
                        'line': i,
                        'type': '设计系统',
                        'message': message,
                        'code': line.strip()
                    })

        # 检查硬编码的字体大小
        if re.search(r'\.font\(.system\(size:\s*\d+', content):
            for i, line in enumerate(lines, 1):
                if re.search(r'\.font\(.system\(size:\s*\d+', line):
                    self.issues[file_path].append({
                        'line': i,
                        'type': '设计系统',
                        'message': '硬编码字体大小，应使用Typography设计令牌',
                        'code': line.strip()
                    })

    def _check_error_handling(self, file_path, content, lines):
        """检查错误处理"""
        # 查找异步函数但没有错误处理
        has_async = re.search(r'func\s+\w+.*async', content)
        has_try_catch = re.search(r'do\s*\{.*\}\s*catch', content, re.DOTALL)

        if has_async and not has_try_catch:
            self.issues[file_path].append({
                'line': 0,
                'type': '错误处理',
                'message': '存在async函数但缺少try-catch错误处理',
                'code': ''
            })

    def _check_loading_states(self, file_path, content, lines):
        """检查加载状态"""
        has_state = re.search(r'@State.*isLoading', content)
        has_async = re.search(r'func\s+\w+.*async', content) or re.search(r'Task\s*\{', content)

        if has_async and not has_state:
            self.issues[file_path].append({
                'line': 0,
                'type': '加载状态',
                'message': '存在异步操作但未定义isLoading状态',
                'code': ''
            })

    def _check_api_calls(self, file_path, content, lines):
        """检查API调用"""
        # 检查是否有URLSession或网络请求但没有使用APIClient
        has_urlsession = re.search(r'URLSession', content)
        has_api_client = re.search(r'APIClient|Service', content)

        if has_urlsession and not has_api_client:
            self.issues[file_path].append({
                'line': 0,
                'type': 'API调用',
                'message': '直接使用URLSession，应使用APIClient或Service层',
                'code': ''
            })

    def check_all_files(self):
        """检查所有Swift文件"""
        swift_files = list(self.base_dir.glob('Sources/**/*.swift'))

        for file_path in swift_files:
            self.check_file(file_path)

        return self.issues

    def generate_report(self):
        """生成报告"""
        if not self.issues:
            print("✅ 未发现问题")
            return

        print("=" * 80)
        print("前端代码问题检查报告")
        print("=" * 80)

        # 按问题类型统计
        stats = defaultdict(int)
        for file_path, issues_list in self.issues.items():
            for issue in issues_list:
                stats[issue['type']] += 1

        print(f"\n总计发现 {sum(stats.values())} 个问题，分布在 {len(self.issues)} 个文件中\n")

        print("问题类型统计：")
        for issue_type, count in sorted(stats.items(), key=lambda x: -x[1]):
            print(f"  - {issue_type}: {count} 处")

        print("\n" + "=" * 80)
        print("详细问题列表")
        print("=" * 80)

        # 按文件输出问题
        for file_path, issues_list in sorted(self.issues.items()):
            print(f"\n📄 {file_path} ({len(issues_list)} 个问题)")
            print("-" * 80)

            # 按类型分组
            by_type = defaultdict(list)
            for issue in issues_list:
                by_type[issue['type']].append(issue)

            for issue_type, type_issues in sorted(by_type.items()):
                print(f"\n  【{issue_type}】 {len(type_issues)} 处")
                for issue in type_issues[:5]:  # 每个类型最多显示5个
                    if issue['line'] > 0:
                        print(f"    行 {issue['line']}: {issue['message']}")
                        if issue['code']:
                            print(f"      代码: {issue['code'][:80]}")
                    else:
                        print(f"    {issue['message']}")

                if len(type_issues) > 5:
                    print(f"    ... 还有 {len(type_issues) - 5} 处")

if __name__ == '__main__':
    checker = CodeIssueChecker('.')
    checker.check_all_files()
    checker.generate_report()
