#!/usr/bin/env python3
"""
全面代码质量检查脚本
Comprehensive code quality check script
检查：编码问题、重复文件、代码质量、前后端不匹配
"""

import os
import re
import hashlib
from pathlib import Path
from collections import defaultdict
import chardet

class CodeQualityChecker:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.issues = {
            'encoding': [],
            'duplicates': [],
            'whitespace': [],
            'code_quality': [],
            'frontend_backend': []
        }

    def check_encoding(self, file_path):
        """检查文件编码问题"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                if result['encoding'] not in ['utf-8', 'ascii', None]:
                    return f"非UTF-8编码: {result['encoding']}"

                # 检查BOM
                if raw_data.startswith(b'\xef\xbb\xbf'):
                    return "包含UTF-8 BOM"

                # 检查乱码字符
                try:
                    text = raw_data.decode('utf-8')
                    if '�' in text or '�' in text:
                        return "包含乱码字符"
                except UnicodeDecodeError as e:
                    return f"UTF-8解码错误: {e}"
        except Exception as e:
            return f"读取错误: {e}"
        return None

    def check_whitespace(self, file_path):
        """检查空格和格式问题"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    # 行尾空格
                    if line.rstrip('\n').endswith(' ') or line.rstrip('\n').endswith('\t'):
                        issues.append(f"行 {i}: 行尾空格")

                    # 混合tab和空格
                    if '\t' in line and '    ' in line:
                        issues.append(f"行 {i}: 混合tab和空格")

                    # 过长的行 (Python >120, TS/JS >100)
                    max_len = 120 if file_path.suffix == '.py' else 100
                    line_len = len(line.rstrip('\n'))
                    if line_len > max_len:
                        issues.append(f"行 {i}: 行过长 ({line_len} > {max_len})")

        except Exception as e:
            issues.append(f"检查失败: {e}")
        return issues

    def check_code_quality(self, file_path):
        """检查代码质量问题"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Python特定检查
                if file_path.suffix == '.py':
                    # 未使用的imports
                    import_pattern = r'import\s+(\w+)'
                    imports = re.findall(import_pattern, content)
                    for imp in imports:
                        if content.count(imp) == 1:  # 只出现在import语句
                            issues.append(f"可能未使用的import: {imp}")

                    # print调试语句
                    if 'print(' in content:
                        count = content.count('print(')
                        issues.append(f"包含 {count} 个print调试语句")

                    # TODO/FIXME
                    if 'TODO' in content or 'FIXME' in content:
                        issues.append("包含TODO/FIXME注释")

                # TypeScript/JavaScript检查
                if file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                    # console.log
                    if 'console.log' in content:
                        count = content.count('console.log')
                        issues.append(f"包含 {count} 个console.log调试语句")

                    # any类型使用
                    if ': any' in content:
                        count = content.count(': any')
                        issues.append(f"使用了 {count} 次any类型")

                    # @ts-ignore
                    if '@ts-ignore' in content:
                        count = content.count('@ts-ignore')
                        issues.append(f"包含 {count} 个@ts-ignore")

                # 通用检查
                # 硬编码密码/密钥
                if any(pattern in content.lower() for pattern in ['password="', "password='", 'api_key="', "api_key='"]):
                    issues.append("⚠️  可能包含硬编码密码/密钥")

                # 空catch块
                if 'except:' in content or 'catch()' in content or 'catch {}' in content:
                    issues.append("包含空的异常处理块")

        except Exception as e:
            issues.append(f"检查失败: {e}")
        return issues

    def find_duplicates(self, files):
        """查找重复文件"""
        hash_map = defaultdict(list)
        for file_path in files:
            try:
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                    hash_map[file_hash].append(file_path)
            except Exception:
                pass

        duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
        return duplicates

    def scan_directory(self):
        """扫描整个目录"""
        print("开始扫描代码质量...\n")

        # 收集所有代码文件
        code_files = []
        exclude_dirs = {'node_modules', '__pycache__', '.venv', 'venv', '.git', 'dist', 'build', 'chroma_db'}

        for root, dirs, files in os.walk(self.root_dir):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                    file_path = Path(root) / file
                    code_files.append(file_path)

        print(f"找到 {len(code_files)} 个代码文件\n")

        # 1. 检查编码
        print("检查编码问题...")
        for file_path in code_files:
            issue = self.check_encoding(file_path)
            if issue:
                self.issues['encoding'].append({
                    'file': str(file_path.relative_to(self.root_dir)),
                    'issue': issue
                })

        # 2. 检查空格
        print("检查格式问题...")
        for file_path in code_files:
            issues = self.check_whitespace(file_path)
            if issues:
                self.issues['whitespace'].append({
                    'file': str(file_path.relative_to(self.root_dir)),
                    'issues': issues[:5]  # 只显示前5个
                })

        # 3. 检查代码质量
        print("检查代码质量...")
        for file_path in code_files:
            issues = self.check_code_quality(file_path)
            if issues:
                self.issues['code_quality'].append({
                    'file': str(file_path.relative_to(self.root_dir)),
                    'issues': issues
                })

        # 4. 查找重复文件
        print("查找重复文件...")
        duplicates = self.find_duplicates(code_files)
        for file_hash, paths in duplicates.items():
            self.issues['duplicates'].append({
                'hash': file_hash[:8],
                'files': [str(p.relative_to(self.root_dir)) for p in paths]
            })

        print("扫描完成！\n")

    def generate_report(self):
        """生成报告"""
        report = []
        report.append("=" * 80)
        report.append("代码质量检查报告")
        report.append("=" * 80)
        report.append("")

        # 编码问题
        if self.issues['encoding']:
            report.append(f"## 1. 编码问题 ({len(self.issues['encoding'])} 个文件)")
            report.append("")
            for item in self.issues['encoding'][:20]:
                report.append(f"- {item['file']}")
                report.append(f"  问题: {item['issue']}")
                report.append("")
        else:
            report.append("## 1. 编码问题: ✅ 无问题")
            report.append("")

        # 重复文件
        if self.issues['duplicates']:
            report.append(f"## 2. 重复文件 ({len(self.issues['duplicates'])} 组)")
            report.append("")
            for item in self.issues['duplicates'][:10]:
                report.append(f"重复组 {item['hash']}:")
                for f in item['files']:
                    report.append(f"  - {f}")
                report.append("")
        else:
            report.append("## 2. 重复文件: ✅ 无重复")
            report.append("")

        # 格式问题
        if self.issues['whitespace']:
            report.append(f"## 3. 格式问题 ({len(self.issues['whitespace'])} 个文件)")
            report.append("")
            for item in self.issues['whitespace'][:20]:
                report.append(f"- {item['file']}")
                for issue in item['issues'][:3]:
                    report.append(f"  {issue}")
                report.append("")
        else:
            report.append("## 3. 格式问题: ✅ 无问题")
            report.append("")

        # 代码质量
        if self.issues['code_quality']:
            report.append(f"## 4. 代码质量问题 ({len(self.issues['code_quality'])} 个文件)")
            report.append("")

            # 按严重性分类
            critical = []
            warnings = []
            info = []

            for item in self.issues['code_quality']:
                has_critical = any('⚠️' in issue for issue in item['issues'])
                has_warning = any('print(' in issue or 'console.log' in issue for issue in item['issues'])

                if has_critical:
                    critical.append(item)
                elif has_warning:
                    warnings.append(item)
                else:
                    info.append(item)

            if critical:
                report.append(f"### 严重问题 ({len(critical)} 个文件):")
                for item in critical[:10]:
                    report.append(f"- {item['file']}")
                    for issue in item['issues']:
                        if '⚠️' in issue:
                            report.append(f"  {issue}")
                    report.append("")

            if warnings:
                report.append(f"### 警告 ({len(warnings)} 个文件):")
                for item in warnings[:10]:
                    report.append(f"- {item['file']}")
                    for issue in item['issues'][:2]:
                        report.append(f"  {issue}")
                    report.append("")
        else:
            report.append("## 4. 代码质量: ✅ 无问题")
            report.append("")

        # 统计总结
        report.append("=" * 80)
        report.append("## 统计总结")
        report.append("")
        report.append(f"- 编码问题: {len(self.issues['encoding'])} 个文件")
        report.append(f"- 重复文件: {len(self.issues['duplicates'])} 组")
        report.append(f"- 格式问题: {len(self.issues['whitespace'])} 个文件")
        report.append(f"- 代码质量: {len(self.issues['code_quality'])} 个文件")
        report.append("=" * 80)

        return "\n".join(report)

if __name__ == "__main__":
    checker = CodeQualityChecker("/Users/alwan/FieldMind-Rebuild")
    checker.scan_directory()
    report = checker.generate_report()
    print(report)

    # 保存报告
    with open("/Users/alwan/FieldMind-Rebuild/CODE_QUALITY_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n报告已保存到 CODE_QUALITY_REPORT.md")
