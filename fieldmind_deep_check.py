#!/usr/bin/env python3
"""
FieldMind深度检查 - 查找所有实际问题
1. 前后端API不匹配
2. 重复的API路由
3. 未使用的导入
4. 调试语句
5. 空的异常处理
6. 硬编码配置
7. TypeScript类型错误
"""

import os
import re
from pathlib import Path
from collections import defaultdict

class FieldMindChecker:
    def __init__(self):
        self.backend_dir = Path("/Users/alwan/FieldMind-Rebuild/fieldmind-backend")
        self.web_dir = Path("/Users/alwan/FieldMind-Rebuild/fieldmind-web")
        self.desktop_dir = Path("/Users/alwan/FieldMind-Rebuild/fieldmind-desktop")

        self.issues = {
            'debug_statements': [],
            'empty_catch': [],
            'hardcoded_config': [],
            'duplicate_routes': [],
            'unused_imports': [],
            'api_mismatches': [],
            'type_errors': []
        }

    def check_backend_routes(self):
        """提取后端所有路由"""
        routes = {}
        api_dir = self.backend_dir / "app" / "api"

        for py_file in api_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')

                # 查找路由定义
                route_patterns = [
                    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
                ]

                for pattern in route_patterns:
                    matches = re.findall(pattern, content)
                    for method, path in matches:
                        route_key = f"{method.upper()} {path}"
                        if route_key in routes:
                            routes[route_key].append(str(py_file.relative_to(self.backend_dir)))
                        else:
                            routes[route_key] = [str(py_file.relative_to(self.backend_dir))]
            except Exception as e:
                pass

        # 查找重复路由
        for route, files in routes.items():
            if len(files) > 1:
                self.issues['duplicate_routes'].append({
                    'route': route,
                    'files': files
                })

        return routes

    def check_frontend_api_calls(self):
        """提取前端所有API调用"""
        api_calls = []

        # 检查api.ts
        api_file = self.web_dir / "src" / "services" / "api.ts"
        if api_file.exists():
            content = api_file.read_text(encoding='utf-8')

            # 查找API路径
            patterns = [
                r'apiClient\.(get|post|put|delete|patch)<[^>]+>\([\'"`]([^\'"`]+)[\'"`]',
                r'apiClient\.(get|post|put|delete|patch)\([\'"`]([^\'"`]+)[\'"`]'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content)
                for method, path in matches:
                    api_calls.append(f"{method.upper()} {path}")

        return api_calls

    def check_debug_statements(self):
        """查找调试语句"""
        # Backend print
        for py_file in self.backend_dir.rglob("*.py"):
            if "test" in str(py_file) or "demo" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    if re.search(r'\bprint\s*\(', line) and not line.strip().startswith('#'):
                        self.issues['debug_statements'].append({
                            'file': str(py_file.relative_to(self.backend_dir)),
                            'line': i,
                            'code': line.strip()[:80]
                        })
            except Exception:
                pass

        # Frontend console.log
        for ts_file in self.web_dir.rglob("*.ts*"):
            try:
                content = ts_file.read_text(encoding='utf-8')
                lines = content.split('\n')

                for i, line in enumerate(lines, 1):
                    if 'console.log' in line and not line.strip().startswith('//'):
                        self.issues['debug_statements'].append({
                            'file': str(ts_file.relative_to(self.web_dir)),
                            'line': i,
                            'code': line.strip()[:80]
                        })
            except Exception:
                pass

    def check_empty_exception_handlers(self):
        """查找空的异常处理"""
        for py_file in self.backend_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding='utf-8')

                # 查找 except: pass 或 except Exception: pass
                if re.search(r'except[^:]*:\s*pass', content):
                    self.issues['empty_catch'].append({
                        'file': str(py_file.relative_to(self.backend_dir)),
                        'type': 'Python empty except'
                    })
            except Exception:
                pass

        for ts_file in self.web_dir.rglob("*.ts*"):
            try:
                content = ts_file.read_text(encoding='utf-8')

                # 查找 catch {} 或 catch() {}
                if re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', content):
                    self.issues['empty_catch'].append({
                        'file': str(ts_file.relative_to(self.web_dir)),
                        'type': 'TypeScript empty catch'
                    })
            except Exception:
                pass

    def check_hardcoded_config(self):
        """查找硬编码配置"""
        patterns = [
            (r'localhost:\d+', 'localhost URL'),
            (r'127\.0\.0\.1:\d+', '127.0.0.1 URL'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'hardcoded API key'),
        ]

        for py_file in self.backend_dir.rglob("*.py"):
            if "test" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')

                for pattern, issue_type in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        self.issues['hardcoded_config'].append({
                            'file': str(py_file.relative_to(self.backend_dir)),
                            'type': issue_type,
                            'count': len(matches)
                        })
                        break
            except Exception:
                pass

    def check_unused_imports(self):
        """查找未使用的导入（简单检查）"""
        for py_file in self.backend_dir.rglob("*.py"):
            if "test" in str(py_file) or "__init__" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')

                unused = []
                for line in lines:
                    # 简单的import检查
                    match = re.match(r'^\s*import\s+(\w+)', line)
                    if match:
                        module = match.group(1)
                        # 检查是否在代码中使用
                        if content.count(module) == 1:  # 只在import行出现
                            unused.append(module)

                if unused:
                    self.issues['unused_imports'].append({
                        'file': str(py_file.relative_to(self.backend_dir)),
                        'imports': unused[:5]  # 只显示前5个
                    })
            except Exception:
                pass

    def check_typescript_any(self):
        """查找TypeScript any类型使用"""
        for ts_file in self.web_dir.rglob("*.ts*"):
            try:
                content = ts_file.read_text(encoding='utf-8')

                any_count = content.count(': any')
                ts_ignore_count = content.count('@ts-ignore')

                if any_count > 5 or ts_ignore_count > 2:
                    self.issues['type_errors'].append({
                        'file': str(ts_file.relative_to(self.web_dir)),
                        'any_count': any_count,
                        'ts_ignore_count': ts_ignore_count
                    })
            except Exception:
                pass

    def run_all_checks(self):
        """运行所有检查"""
        print("开始FieldMind深度检查...\n")

        print("1. 检查后端路由...")
        backend_routes = self.check_backend_routes()
        print(f"   找到 {len(backend_routes)} 个后端路由")

        print("2. 检查前端API调用...")
        frontend_calls = self.check_frontend_api_calls()
        print(f"   找到 {len(frontend_calls)} 个前端API调用")

        print("3. 检查调试语句...")
        self.check_debug_statements()
        print(f"   找到 {len(self.issues['debug_statements'])} 个调试语句")

        print("4. 检查空异常处理...")
        self.check_empty_exception_handlers()
        print(f"   找到 {len(self.issues['empty_catch'])} 个空异常处理")

        print("5. 检查硬编码配置...")
        self.check_hardcoded_config()
        print(f"   找到 {len(self.issues['hardcoded_config'])} 个硬编码配置")

        print("6. 检查未使用的导入...")
        self.check_unused_imports()
        print(f"   找到 {len(self.issues['unused_imports'])} 个文件有未使用导入")

        print("7. 检查TypeScript类型问题...")
        self.check_typescript_any()
        print(f"   找到 {len(self.issues['type_errors'])} 个文件有类型问题")

        print("\n检查完成！\n")

    def generate_report(self):
        """生成报告"""
        report = []
        report.append("=" * 80)
        report.append("FieldMind 深度代码检查报告")
        report.append("=" * 80)
        report.append("")

        # 1. 重复路由
        if self.issues['duplicate_routes']:
            report.append(f"## 1. ⚠️  重复的API路由 ({len(self.issues['duplicate_routes'])} 个)")
            report.append("")
            for item in self.issues['duplicate_routes']:
                report.append(f"路由: {item['route']}")
                for f in item['files']:
                    report.append(f"  - {f}")
                report.append("")
        else:
            report.append("## 1. 重复路由: ✅ 无重复")
            report.append("")

        # 2. 调试语句
        if self.issues['debug_statements']:
            report.append(f"## 2. 调试语句 ({len(self.issues['debug_statements'])} 个)")
            report.append("")
            report.append("需要清理的调试语句：")
            report.append("")

            for item in self.issues['debug_statements'][:30]:
                report.append(f"- {item['file']}:{item['line']}")
                report.append(f"  {item['code']}")
                report.append("")
        else:
            report.append("## 2. 调试语句: ✅ 无问题")
            report.append("")

        # 3. 空异常处理
        if self.issues['empty_catch']:
            report.append(f"## 3. ⚠️  空的异常处理 ({len(self.issues['empty_catch'])} 个)")
            report.append("")
            for item in self.issues['empty_catch'][:20]:
                report.append(f"- {item['file']} ({item['type']})")
            report.append("")
        else:
            report.append("## 3. 空异常处理: ✅ 无问题")
            report.append("")

        # 4. 硬编码配置
        if self.issues['hardcoded_config']:
            report.append(f"## 4. ⚠️  硬编码配置 ({len(self.issues['hardcoded_config'])} 个文件)")
            report.append("")
            for item in self.issues['hardcoded_config'][:20]:
                report.append(f"- {item['file']}")
                report.append(f"  类型: {item['type']} (出现 {item['count']} 次)")
                report.append("")
        else:
            report.append("## 4. 硬编码配置: ✅ 无问题")
            report.append("")

        # 5. 未使用导入
        if self.issues['unused_imports']:
            report.append(f"## 5. 未使用的导入 ({len(self.issues['unused_imports'])} 个文件)")
            report.append("")
            for item in self.issues['unused_imports'][:15]:
                report.append(f"- {item['file']}")
                report.append(f"  未使用: {', '.join(item['imports'])}")
                report.append("")
        else:
            report.append("## 5. 未使用导入: ✅ 无问题")
            report.append("")

        # 6. TypeScript类型问题
        if self.issues['type_errors']:
            report.append(f"## 6. TypeScript类型问题 ({len(self.issues['type_errors'])} 个文件)")
            report.append("")
            for item in self.issues['type_errors'][:15]:
                report.append(f"- {item['file']}")
                report.append(f"  any类型: {item['any_count']} 个, @ts-ignore: {item['ts_ignore_count']} 个")
                report.append("")
        else:
            report.append("## 6. TypeScript类型: ✅ 无问题")
            report.append("")

        # 总结
        report.append("=" * 80)
        report.append("## 统计总结")
        report.append("")
        report.append(f"- 重复路由: {len(self.issues['duplicate_routes'])} 个")
        report.append(f"- 调试语句: {len(self.issues['debug_statements'])} 个")
        report.append(f"- 空异常处理: {len(self.issues['empty_catch'])} 个")
        report.append(f"- 硬编码配置: {len(self.issues['hardcoded_config'])} 个文件")
        report.append(f"- 未使用导入: {len(self.issues['unused_imports'])} 个文件")
        report.append(f"- 类型问题: {len(self.issues['type_errors'])} 个文件")
        report.append("")

        # 优先级建议
        report.append("=" * 80)
        report.append("## 修复优先级")
        report.append("")
        report.append("### 🔴 高优先级（影响功能）")
        report.append("1. 重复的API路由 - 可能导致路由冲突")
        report.append("2. 硬编码配置 - 安全风险和部署问题")
        report.append("3. 空的异常处理 - 隐藏错误，难以调试")
        report.append("")
        report.append("### 🟡 中优先级（影响维护）")
        report.append("4. 调试语句 - 影响性能和日志清洁")
        report.append("5. TypeScript any类型 - 失去类型安全")
        report.append("")
        report.append("### 🟢 低优先级（代码清洁）")
        report.append("6. 未使用的导入 - 不影响功能但增加代码体积")
        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

if __name__ == "__main__":
    checker = FieldMindChecker()
    checker.run_all_checks()
    report = checker.generate_report()
    print(report)

    # 保存报告
    output_file = "/Users/alwan/FieldMind-Rebuild/FIELDMIND_ISSUES_REPORT.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n详细报告已保存到 {output_file}")
