#!/usr/bin/env python3
"""
API响应格式统一工具 - 第二阶段
执行深度迁移，将所有API转换为统一格式

步骤：
1. 创建完整备份
2. 逐个文件执行迁移
3. 转换返回语句
4. 添加导入语句
5. 验证语法正确性
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import ast

class APIResponseMigrationExecutor:
    def __init__(self, backend_path: str, plan_file: str):
        self.backend_path = Path(backend_path)
        self.plan_file = plan_file
        self.migration_plan = None
        self.backup_dir = None
        self.results = {
            'success': [],
            'failed': [],
            'skipped': []
        }

    def load_migration_plan(self):
        """加载迁移计划"""
        print("📋 加载迁移计划...")
        with open(self.plan_file, 'r', encoding='utf-8') as f:
            self.migration_plan = json.load(f)

        print(f"  文件数: {self.migration_plan['total_files']}")
        print(f"  端点数: {self.migration_plan['total_endpoints']}")
        print()

    def create_backup(self):
        """创建完整备份"""
        print("💾 创建备份...")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.backend_path.parent / f"backup_api_migration_{timestamp}"

        # 备份整个 app 目录
        app_dir = self.backend_path / "app"
        backup_app_dir = self.backup_dir / "app"

        shutil.copytree(app_dir, backup_app_dir)

        print(f"  ✓ 备份完成: {self.backup_dir}")
        print(f"  如果迁移出现问题，可以从此恢复")
        print()

    def execute_migration(self):
        """执行迁移"""
        print("=" * 100)
        print("🚀 开始执行迁移")
        print("=" * 100)
        print()

        total_files = len(self.migration_plan['files'])

        for i, file_plan in enumerate(self.migration_plan['files'], 1):
            filepath = self.backend_path / file_plan['path']

            print(f"[{i}/{total_files}] 迁移: {file_plan['path']}")

            try:
                self.migrate_file(filepath, file_plan)
                self.results['success'].append(str(filepath))
                print(f"  ✓ 完成")
            except Exception as e:
                self.results['failed'].append({
                    'file': str(filepath),
                    'error': str(e)
                })
                print(f"  ✗ 失败: {e}")

            print()

    def migrate_file(self, filepath: Path, file_plan: Dict):
        """迁移单个文件"""
        # 读取原文件
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()

        lines = original_content.split('\n')
        modified_lines = lines.copy()

        # 1. 添加导入语句（如果需要）
        if file_plan['needs_import']:
            modified_lines = self.add_imports(modified_lines)

        # 2. 迁移每个端点
        for endpoint in file_plan['endpoints']:
            modified_lines = self.migrate_endpoint(
                modified_lines,
                endpoint,
                filepath
            )

        # 3. 验证语法
        new_content = '\n'.join(modified_lines)
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            raise Exception(f"迁移后语法错误: {e}")

        # 4. 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    def add_imports(self, lines: List[str]) -> List[str]:
        """添加统一响应格式的导入"""
        # 查找导入语句的插入位置
        insert_pos = 0

        # 跳过文件开头的注释和docstring
        in_docstring = False
        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检测docstring
            if '"""' in stripped or "'''" in stripped:
                in_docstring = not in_docstring
                continue

            if in_docstring:
                continue

            # 找到第一个导入语句
            if stripped.startswith('from ') or stripped.startswith('import '):
                insert_pos = i
                break

        # 查找最后一个导入语句
        last_import = insert_pos
        for i in range(insert_pos, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith('from ') or stripped.startswith('import '):
                last_import = i
            elif stripped and not stripped.startswith('#'):
                break

        # 插入新的导入
        import_statement = "from app.schemas.response import success_response, error_response, paginated_response"

        # 检查是否已存在
        if not any(import_statement in line for line in lines):
            lines.insert(last_import + 1, import_statement)

        return lines

    def migrate_endpoint(
        self,
        lines: List[str],
        endpoint: Dict,
        filepath: Path
    ) -> List[str]:
        """迁移单个端点"""
        start_line = endpoint['line_start'] - 1  # 转为0索引
        end_line = endpoint['line_end'] - 1

        if start_line >= len(lines) or end_line >= len(lines):
            return lines

        # 分析返回语句
        analysis = endpoint['return_analysis']

        if not analysis['has_dict_return']:
            # 没有dict返回，可能已经迁移过或是其他类型
            return lines

        # 找到所有返回语句并替换
        func_lines = lines[start_line:end_line + 1]
        modified_func = self.transform_return_statements(func_lines, analysis)

        # 替换原函数
        lines[start_line:end_line + 1] = modified_func

        return lines

    def transform_return_statements(
        self,
        func_lines: List[str],
        analysis: Dict
    ) -> List[str]:
        """转换返回语句为统一格式"""
        modified_lines = []
        i = 0

        while i < len(func_lines):
            line = func_lines[i]
            stripped = line.strip()

            # 检测返回语句
            if stripped.startswith('return {') or (stripped.startswith('return') and '{' in line):
                # 提取完整的返回语句（可能跨多行）
                return_block, lines_consumed = self.extract_return_block(func_lines, i)

                # 转换返回语句
                transformed = self.transform_dict_return(return_block, line)

                modified_lines.append(transformed)
                i += lines_consumed
            else:
                modified_lines.append(line)
                i += 1

        return modified_lines

    def extract_return_block(
        self,
        lines: List[str],
        start_idx: int
    ) -> Tuple[str, int]:
        """提取完整的返回语句块（处理多行dict）"""
        block = lines[start_idx]
        lines_consumed = 1

        # 如果返回语句在一行内完成
        if block.count('{') == block.count('}'):
            return block, lines_consumed

        # 否则，继续读取直到括号匹配
        open_braces = block.count('{') - block.count('}')

        for i in range(start_idx + 1, len(lines)):
            next_line = lines[i]
            block += '\n' + next_line
            lines_consumed += 1

            open_braces += next_line.count('{') - next_line.count('}')

            if open_braces == 0:
                break

        return block, lines_consumed

    def transform_dict_return(self, return_statement: str, original_line: str) -> str:
        """将dict返回转换为统一格式"""
        # 获取缩进
        indent = len(original_line) - len(original_line.lstrip())
        indent_str = ' ' * indent

        # 提取返回的dict内容
        dict_match = re.search(r'return\s+(\{.+\})', return_statement, re.DOTALL)
        if not dict_match:
            return return_statement

        dict_content = dict_match.group(1)

        # 分析dict的键
        try:
            # 尝试解析dict来提取键值
            dict_eval = eval(dict_content, {"__builtins__": {}}, {})
            keys = list(dict_eval.keys()) if isinstance(dict_eval, dict) else []
        except:
            # 如果无法解析，使用正则提取键
            keys = re.findall(r'["\'](\w+)["\']:', dict_content)

        # 根据键判断是什么类型的响应
        has_pagination = any(k in keys for k in ['total', 'page', 'page_size', 'has_next'])
        has_data = 'data' in keys
        has_error = 'error' in keys or 'success' in keys

        # 生成新的返回语句
        if has_pagination and has_data:
            # 分页响应
            # 提取data, total, page, page_size
            data_value = self.extract_value(dict_content, 'data')
            total_value = self.extract_value(dict_content, 'total')
            page_value = self.extract_value(dict_content, 'page', '1')
            page_size_value = self.extract_value(dict_content, 'page_size', '20')

            return f"{indent_str}return paginated_response(\n" \
                   f"{indent_str}    data={data_value},\n" \
                   f"{indent_str}    page={page_value},\n" \
                   f"{indent_str}    page_size={page_size_value},\n" \
                   f"{indent_str}    total={total_value}\n" \
                   f"{indent_str})"

        elif has_error or (not has_data and 'message' in keys):
            # 错误响应
            message_value = self.extract_value(dict_content, 'message', '"Error"')
            code_value = self.extract_value(dict_content, 'code', '"ERROR"')

            return f"{indent_str}return error_response(\n" \
                   f"{indent_str}    code={code_value},\n" \
                   f"{indent_str}    message={message_value}\n" \
                   f"{indent_str})"

        else:
            # 普通成功响应
            if has_data:
                data_value = self.extract_value(dict_content, 'data')
            else:
                # 整个dict就是data
                data_value = dict_content

            message_value = self.extract_value(dict_content, 'message', 'None')

            if message_value != 'None':
                return f"{indent_str}return success_response(\n" \
                       f"{indent_str}    data={data_value},\n" \
                       f"{indent_str}    message={message_value}\n" \
                       f"{indent_str})"
            else:
                return f"{indent_str}return success_response(data={data_value})"

    def extract_value(self, dict_str: str, key: str, default: str = 'None') -> str:
        """从dict字符串中提取某个键的值"""
        # 尝试多种模式匹配
        patterns = [
            rf'["\']?{key}["\']?\s*:\s*(.+?)(?:,|\}})',  # "key": value, 或 key: value}
            rf'["\']?{key}["\']?\s*:\s*(.+?)$',  # 行尾
        ]

        for pattern in patterns:
            match = re.search(pattern, dict_str, re.MULTILINE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # 清理可能的尾部字符
                value = value.rstrip(',').strip()
                return value

        return default

    def generate_report(self):
        """生成迁移报告"""
        report = []
        report.append("=" * 100)
        report.append("API响应格式统一 - 迁移执行报告")
        report.append("=" * 100)
        report.append(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("📊 迁移结果")
        report.append("-" * 100)
        report.append(f"成功: {len(self.results['success'])} 个文件")
        report.append(f"失败: {len(self.results['failed'])} 个文件")
        report.append(f"跳过: {len(self.results['skipped'])} 个文件")
        report.append("")

        if self.results['failed']:
            report.append("❌ 失败的文件:")
            report.append("-" * 100)
            for item in self.results['failed']:
                report.append(f"  {item['file']}")
                report.append(f"  错误: {item['error']}")
                report.append("")

        report.append("=" * 100)
        report.append(f"✓ 备份位置: {self.backup_dir}")
        report.append("下一步: 运行测试验证迁移结果")
        report.append("=" * 100)

        return "\n".join(report)

if __name__ == "__main__":
    backend_path = "/Users/alwan/FieldMind/backend/src"
    plan_file = "/Users/alwan/FieldMind/migration_plan_phase1.json"

    print("\n")
    print("╔" + "=" * 98 + "╗")
    print("║" + " " * 30 + "API响应格式统一工具 - 第二阶段" + " " * 37 + "║")
    print("║" + " " * 37 + "执行迁移" + " " * 52 + "║")
    print("╚" + "=" * 98 + "╝")
    print("\n")

    executor = APIResponseMigrationExecutor(backend_path, plan_file)

    # 加载计划
    executor.load_migration_plan()

    # 创建备份
    executor.create_backup()

    # 询问确认
    print("⚠️  警告: 即将修改 62 个文件，共 387 个端点")
    print("   已创建完整备份，可以随时恢复")
    print()
    response = input("确认执行迁移? (yes/no): ")

    if response.lower() != 'yes':
        print("\n❌ 已取消迁移")
        exit(0)

    print()

    # 执行迁移
    executor.execute_migration()

    # 生成报告
    print()
    report = executor.generate_report()
    print(report)

    # 保存报告
    report_file = "/Users/alwan/FieldMind/migration_execution_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✓ 报告已保存: {report_file}")
