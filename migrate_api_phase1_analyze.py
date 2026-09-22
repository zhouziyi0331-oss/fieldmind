#!/usr/bin/env python3
"""
API响应格式统一工具 - 第一阶段
完整、深度地将所有API迁移到统一格式

步骤：
1. 分析每个API文件的当前返回格式
2. 生成迁移代码
3. 备份原文件
4. 应用迁移
5. 验证迁移结果
"""

import os
import re
import ast
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import shutil

class APIResponseMigrator:
    def __init__(self, backend_path: str):
        self.backend_path = Path(backend_path)
        self.migration_plan = []
        self.backup_dir = self.backend_path.parent / f"backup_before_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def analyze_and_plan(self):
        """分析所有API文件并制定迁移计划"""
        print("=" * 100)
        print("第一阶段：API响应格式统一 - 分析和规划")
        print("=" * 100)
        print()

        # 查找所有API文件
        api_files = []
        for pattern in ['app/api/**/*.py', 'app/api/v1/**/*.py', 'app/api/routes/**/*.py']:
            api_files.extend(self.backend_path.glob(pattern))

        # 过滤
        api_files = [f for f in set(api_files)
                    if '__pycache__' not in str(f)
                    and '__init__' not in str(f)
                    and f.stat().st_size > 0]

        print(f"📁 找到 {len(api_files)} 个API文件需要检查\n")

        for i, filepath in enumerate(sorted(api_files), 1):
            print(f"分析 [{i}/{len(api_files)}]: {filepath.name}")
            self.analyze_file(filepath)

        print(f"\n✓ 分析完成")
        print(f"  需要迁移的文件: {len(self.migration_plan)}")

    def analyze_file(self, filepath: Path):
        """分析单个API文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查是否已经使用统一格式
            uses_unified = self.check_unified_format(content)

            if uses_unified:
                print(f"  ✓ 已使用统一格式")
                return

            # 查找所有端点
            endpoints = self.find_endpoints(content, filepath)

            if endpoints:
                self.migration_plan.append({
                    'file': filepath,
                    'relative_path': filepath.relative_to(self.backend_path),
                    'endpoints': endpoints,
                    'needs_import': 'from app.schemas.response import' not in content
                })
                print(f"  ⚠️  需要迁移 {len(endpoints)} 个端点")
            else:
                print(f"  - 无需迁移")

        except Exception as e:
            print(f"  ✗ 分析出错: {e}")

    def check_unified_format(self, content: str) -> bool:
        """检查是否已使用统一格式"""
        # 检查是否导入了统一响应
        has_import = (
            'from app.schemas.response import' in content or
            'from ...schemas.response import' in content or
            'from ..schemas.response import' in content
        )

        # 检查是否使用了响应函数
        uses_response = (
            'success_response(' in content or
            'error_response(' in content or
            'paginated_response(' in content
        )

        return has_import and uses_response

    def find_endpoints(self, content: str, filepath: Path) -> List[Dict]:
        """查找文件中的所有端点"""
        endpoints = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # 查找路由装饰器
            route_match = re.search(
                r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                line
            )

            if route_match:
                method = route_match.group(1).upper()
                path = route_match.group(2)

                # 查找函数定义
                func_name = None
                func_start = i

                for j in range(i+1, min(i+10, len(lines))):
                    func_match = re.search(r'(?:async\s+)?def\s+(\w+)\s*\(', lines[j])
                    if func_match:
                        func_name = func_match.group(1)
                        func_start = j
                        break

                if func_name:
                    # 分析函数体
                    func_end = self.find_function_end(lines, func_start)
                    func_body = '\n'.join(lines[func_start:func_end])

                    # 检测返回类型
                    return_analysis = self.analyze_return_statements(func_body)

                    endpoints.append({
                        'method': method,
                        'path': path,
                        'function': func_name,
                        'line_start': func_start + 1,
                        'line_end': func_end + 1,
                        'return_analysis': return_analysis,
                        'needs_migration': not return_analysis['uses_unified']
                    })

        return [e for e in endpoints if e['needs_migration']]

    def find_function_end(self, lines: List[str], start_idx: int) -> int:
        """查找函数结束位置"""
        if start_idx >= len(lines):
            return len(lines)

        # 查找函数定义行
        def_line = lines[start_idx]
        base_indent = len(def_line) - len(def_line.lstrip())

        # 从函数体开始查找
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]

            # 跳过空行和注释
            if not line.strip() or line.strip().startswith('#'):
                continue

            current_indent = len(line) - len(line.lstrip())

            # 如果缩进回到或小于函数定义级别，说明函数结束
            if current_indent <= base_indent and line.strip():
                return i

        return len(lines)

    def analyze_return_statements(self, func_body: str) -> Dict[str, Any]:
        """分析函数的返回语句"""
        analysis = {
            'uses_unified': False,
            'has_dict_return': False,
            'has_jsonable_encoder': False,
            'has_jsonresponse': False,
            'return_patterns': []
        }

        # 检查是否使用统一格式
        if 'success_response(' in func_body or 'error_response(' in func_body or 'paginated_response(' in func_body:
            analysis['uses_unified'] = True
            return analysis

        # 检查其他返回模式
        if 'return {' in func_body:
            analysis['has_dict_return'] = True

            # 提取返回的字典键
            dict_returns = re.findall(r'return\s*\{([^}]+)\}', func_body, re.DOTALL)
            for ret in dict_returns:
                keys = re.findall(r'["\'](\w+)["\']:', ret)
                analysis['return_patterns'].append(keys)

        if 'JSONResponse(' in func_body:
            analysis['has_jsonresponse'] = True

        if 'jsonable_encoder(' in func_body:
            analysis['has_jsonable_encoder'] = True

        return analysis

    def generate_migration_report(self):
        """生成详细的迁移报告"""
        report = []
        report.append("=" * 100)
        report.append("API响应格式统一 - 迁移计划报告")
        report.append("=" * 100)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 统计
        total_files = len(self.migration_plan)
        total_endpoints = sum(len(item['endpoints']) for item in self.migration_plan)

        report.append("📊 统计信息")
        report.append("-" * 100)
        report.append(f"需要迁移的文件数: {total_files}")
        report.append(f"需要迁移的端点数: {total_endpoints}")
        report.append("")

        # 按文件列出详细信息
        report.append("📋 详细迁移清单")
        report.append("-" * 100)
        report.append("")

        for i, item in enumerate(self.migration_plan, 1):
            report.append(f"{i}. {item['relative_path']}")
            report.append(f"   端点数: {len(item['endpoints'])}")
            report.append(f"   需要添加导入: {'是' if item['needs_import'] else '否'}")
            report.append("")

            for endpoint in item['endpoints']:
                report.append(f"   • {endpoint['method']} {endpoint['path']}")
                report.append(f"     函数: {endpoint['function']} (行 {endpoint['line_start']}-{endpoint['line_end']})")

                analysis = endpoint['return_analysis']
                if analysis['has_dict_return']:
                    report.append(f"     返回类型: Dict")
                    if analysis['return_patterns']:
                        keys = analysis['return_patterns'][0]
                        report.append(f"     返回键: {', '.join(keys)}")

                report.append("")

        report.append("=" * 100)
        report.append("下一步:")
        report.append("-" * 100)
        report.append("1. 审查此迁移计划")
        report.append("2. 确认无误后，执行备份")
        report.append("3. 执行迁移")
        report.append("4. 运行测试验证")
        report.append("=" * 100)

        return "\n".join(report)

    def save_migration_plan(self, output_file: str):
        """保存迁移计划为JSON"""
        plan_data = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(self.migration_plan),
            'total_endpoints': sum(len(item['endpoints']) for item in self.migration_plan),
            'files': [
                {
                    'path': str(item['relative_path']),
                    'needs_import': item['needs_import'],
                    'endpoints': [
                        {
                            'method': e['method'],
                            'path': e['path'],
                            'function': e['function'],
                            'line_start': e['line_start'],
                            'line_end': e['line_end'],
                            'return_analysis': e['return_analysis']
                        }
                        for e in item['endpoints']
                    ]
                }
                for item in self.migration_plan
            ]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)

        print(f"✓ 迁移计划已保存: {output_file}")

if __name__ == "__main__":
    backend_path = "/Users/alwan/FieldMind/backend/src"

    print("\n")
    print("╔" + "=" * 98 + "╗")
    print("║" + " " * 30 + "API响应格式统一工具 - 第一阶段" + " " * 37 + "║")
    print("║" + " " * 35 + "分析和规划" + " " * 52 + "║")
    print("╚" + "=" * 98 + "╝")
    print("\n")

    migrator = APIResponseMigrator(backend_path)
    migrator.analyze_and_plan()

    print("\n")
    report = migrator.generate_migration_report()
    print(report)

    # 保存报告
    report_file = "/Users/alwan/FieldMind/migration_plan_phase1.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✓ 迁移报告已保存: {report_file}")

    # 保存详细计划
    plan_file = "/Users/alwan/FieldMind/migration_plan_phase1.json"
    migrator.save_migration_plan(plan_file)

    print("\n" + "=" * 100)
    print("请审查迁移计划，确认无误后运行下一个脚本执行迁移")
    print("=" * 100)
