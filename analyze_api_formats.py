#!/usr/bin/env python3
"""
深度分析所有API的返回格式
找出所有不一致的模式，为统一格式做准备
"""

import os
import re
import ast
from pathlib import Path
from collections import defaultdict
import json

class APIResponseAnalyzer:
    def __init__(self, backend_path):
        self.backend_path = Path(backend_path)
        self.api_patterns = {
            'dict_return': defaultdict(list),  # 返回 dict
            'model_return': defaultdict(list),  # 返回 Pydantic Model
            'mixed_return': defaultdict(list),  # 混合返回
            'response_schemas': defaultdict(list),  # 定义的Response Schema
            'endpoint_details': []  # 详细的端点信息
        }

    def analyze_file(self, filepath):
        """深度分析单个API文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            relative_path = filepath.relative_to(self.backend_path)

            # 跳过非API文件
            if 'api' not in str(relative_path):
                return

            # 分析这个文件
            self.analyze_returns(filepath, content, relative_path)
            self.analyze_schemas(filepath, content, relative_path)
            self.analyze_endpoints(filepath, content, relative_path)

        except Exception as e:
            pass

    def analyze_returns(self, filepath, content, relative_path):
        """分析返回语句"""
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            # 检测 return 语句
            if 'return ' in line and not line.strip().startswith('#'):
                line_stripped = line.strip()

                # Dict 返回
                if 'return {' in line_stripped:
                    self.api_patterns['dict_return'][str(relative_path)].append({
                        'line': i,
                        'content': line_stripped[:100]
                    })

                # Model 返回 (ResponseModel, BaseResponse, 等)
                elif re.search(r'return\s+\w+Response\(', line_stripped) or \
                     re.search(r'return\s+\w+Model\(', line_stripped):
                    self.api_patterns['model_return'][str(relative_path)].append({
                        'line': i,
                        'content': line_stripped[:100]
                    })

    def analyze_schemas(self, filepath, content, relative_path):
        """分析定义的Response Schema"""
        # 查找 class XXXResponse 定义
        schema_pattern = r'class\s+(\w+Response)\(.*?\):'
        matches = re.finditer(schema_pattern, content)

        for match in matches:
            schema_name = match.group(1)
            self.api_patterns['response_schemas'][str(relative_path)].append(schema_name)

    def analyze_endpoints(self, filepath, content, relative_path):
        """深度分析端点定义"""
        # 查找路由装饰器
        route_patterns = [
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        ]

        lines = content.split('\n')

        for i, line in enumerate(lines):
            for pattern in route_patterns:
                match = re.search(pattern, line)
                if match:
                    method = match.group(1).upper()
                    path = match.group(2)

                    # 找到函数定义（下一行或下几行）
                    func_name = None
                    return_type = None

                    for j in range(i+1, min(i+5, len(lines))):
                        func_match = re.search(r'def\s+(\w+)\(', lines[j])
                        if func_match:
                            func_name = func_match.group(1)
                            break

                    # 分析这个函数的返回类型
                    if func_name:
                        func_start = i
                        func_end = self.find_function_end(lines, i+1)
                        func_body = '\n'.join(lines[func_start:func_end])

                        # 检测返回类型
                        has_dict_return = 'return {' in func_body
                        has_model_return = bool(re.search(r'return\s+\w+Response\(', func_body))

                        if has_dict_return and has_model_return:
                            return_type = 'mixed'
                        elif has_dict_return:
                            return_type = 'dict'
                        elif has_model_return:
                            return_type = 'model'
                        else:
                            return_type = 'unknown'

                        self.api_patterns['endpoint_details'].append({
                            'file': str(relative_path),
                            'method': method,
                            'path': path,
                            'function': func_name,
                            'return_type': return_type,
                            'line': i + 1
                        })

    def find_function_end(self, lines, start_idx):
        """找到函数结束位置（简单版本：找到下一个非缩进行）"""
        if start_idx >= len(lines):
            return len(lines)

        # 获取函数体的缩进级别
        func_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip() == '':
                continue

            current_indent = len(line) - len(line.lstrip())

            # 如果缩进回到函数级别或更少，说明函数结束
            if current_indent <= func_indent and line.strip():
                return i

        return len(lines)

    def scan(self):
        """扫描所有API文件"""
        print("🔍 深度分析所有API文件...")

        api_files = []
        for pattern in ['**/api/**/*.py', '**/routes/**/*.py']:
            api_files.extend(self.backend_path.glob(pattern))

        # 去重并过滤
        api_files = [f for f in set(api_files)
                    if '__pycache__' not in str(f) and 'venv' not in str(f)]

        total = len(api_files)
        print(f"   找到 {total} 个API文件\n")

        for i, filepath in enumerate(api_files, 1):
            if i % 10 == 0:
                print(f"   进度: {i}/{total}")
            self.analyze_file(filepath)

        print(f"\n✓ 分析完成\n")

    def generate_report(self):
        """生成详细报告"""
        report = []
        report.append("=" * 100)
        report.append("API 返回格式深度分析报告")
        report.append("=" * 100)
        report.append("")

        # 1. 按返回类型分类的端点
        report.append("📊 端点返回类型统计")
        report.append("-" * 100)

        type_counts = defaultdict(int)
        for endpoint in self.api_patterns['endpoint_details']:
            type_counts[endpoint['return_type']] += 1

        for return_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            report.append(f"  {return_type.upper()}: {count} 个端点")
        report.append("")

        # 2. 混合返回类型的端点（最需要修复）
        mixed_endpoints = [e for e in self.api_patterns['endpoint_details']
                          if e['return_type'] == 'mixed']

        if mixed_endpoints:
            report.append("⚠️  混合返回类型的端点（最需要修复）")
            report.append("-" * 100)
            for endpoint in mixed_endpoints[:20]:
                report.append(f"  {endpoint['method']} {endpoint['path']}")
                report.append(f"  文件: {endpoint['file']}:{endpoint['line']}")
                report.append(f"  函数: {endpoint['function']}")
                report.append("")

        # 3. 纯Dict返回的端点
        dict_endpoints = [e for e in self.api_patterns['endpoint_details']
                         if e['return_type'] == 'dict']

        report.append(f"📋 纯Dict返回的端点 ({len(dict_endpoints)}个)")
        report.append("-" * 100)

        # 按文件分组
        by_file = defaultdict(list)
        for endpoint in dict_endpoints:
            by_file[endpoint['file']].append(endpoint)

        for file, endpoints in sorted(by_file.items(), key=lambda x: -len(x[1]))[:10]:
            report.append(f"\n  文件: {file} ({len(endpoints)}个端点)")
            for endpoint in endpoints[:5]:
                report.append(f"    {endpoint['method']} {endpoint['path']} - {endpoint['function']}")

        report.append("")

        # 4. 已定义的Response Schema
        report.append(f"📝 已定义的Response Schema")
        report.append("-" * 100)

        all_schemas = set()
        for file, schemas in self.api_patterns['response_schemas'].items():
            all_schemas.update(schemas)

        for schema in sorted(all_schemas)[:20]:
            report.append(f"  - {schema}")

        report.append(f"\n  总计: {len(all_schemas)} 个不同的Schema")
        report.append("")

        # 5. 返回格式模式分析
        report.append("🔍 常见返回格式模式")
        report.append("-" * 100)

        patterns = self.analyze_return_patterns()
        for pattern, count in sorted(patterns.items(), key=lambda x: -x[1])[:10]:
            report.append(f"  {pattern}: {count}次")

        report.append("")
        report.append("=" * 100)

        return "\n".join(report)

    def analyze_return_patterns(self):
        """分析返回格式的常见模式"""
        patterns = defaultdict(int)

        for file, returns in self.api_patterns['dict_return'].items():
            for ret in returns:
                content = ret['content']

                # 检测常见模式
                if '"data"' in content or "'data'" in content:
                    patterns['{"data": ...}'] += 1
                if '"success"' in content or "'success'" in content:
                    patterns['{"success": ...}'] += 1
                if '"message"' in content or "'message'" in content:
                    patterns['{"message": ...}'] += 1
                if '"total"' in content or "'total'" in content:
                    patterns['{"total": ..., pagination}'] += 1

        return patterns

    def save_detailed_json(self, output_file):
        """保存详细的JSON报告"""
        data = {
            'endpoint_details': self.api_patterns['endpoint_details'],
            'summary': {
                'total_endpoints': len(self.api_patterns['endpoint_details']),
                'dict_returns': len([e for e in self.api_patterns['endpoint_details'] if e['return_type'] == 'dict']),
                'model_returns': len([e for e in self.api_patterns['endpoint_details'] if e['return_type'] == 'model']),
                'mixed_returns': len([e for e in self.api_patterns['endpoint_details'] if e['return_type'] == 'mixed']),
            },
            'response_schemas': dict(self.api_patterns['response_schemas'])
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ 详细JSON报告已保存: {output_file}")

if __name__ == "__main__":
    backend_path = Path("/Users/alwan/FieldMind/backend/src")

    print("API返回格式深度分析工具")
    print("=" * 100)
    print()

    analyzer = APIResponseAnalyzer(backend_path)
    analyzer.scan()

    report = analyzer.generate_report()
    print(report)

    # 保存报告
    report_file = "/Users/alwan/FieldMind/api_format_analysis.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✓ 报告已保存: {report_file}")

    # 保存详细JSON
    analyzer.save_detailed_json("/Users/alwan/FieldMind/api_format_detailed.json")
