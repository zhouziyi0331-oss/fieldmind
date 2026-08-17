#!/usr/bin/env python3
"""
修复硬编码配置
Fix hardcoded configuration (localhost URLs)
"""

import re
from pathlib import Path
from typing import List, Tuple

class HardcodedConfigFixer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.fixes = []

    def fix_localhost_urls(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """修复硬编码的localhost URL"""
        changes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 常见的localhost URL模式
            patterns = [
                (r'http://localhost:8000', 'os.getenv("API_BASE_URL", "http://localhost:8000")'),
                (r'http://127\.0\.0\.1:8000', 'os.getenv("API_BASE_URL", "http://127.0.0.1:8000")'),
                (r'"localhost"', 'os.getenv("API_HOST", "localhost")'),
                (r'"127\.0\.0\.1"', 'os.getenv("API_HOST", "127.0.0.1")'),
            ]

            new_lines = []
            modified = False
            needs_os_import = False

            for i, line in enumerate(lines):
                original_line = line

                # 跳过注释和文档字符串
                stripped = line.strip()
                if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                    new_lines.append(line)
                    continue

                # 检查是否包含localhost URL
                for pattern, replacement in patterns:
                    if re.search(pattern, line):
                        # 只替换字符串中的URL，不替换注释
                        if '"' in line or "'" in line:
                            old_line = line
                            # 替换为环境变量
                            line = re.sub(
                                f'["\']({pattern})["\']',
                                replacement,
                                line
                            )

                            if line != old_line:
                                changes.append((i + 1, old_line.strip(), line.strip()))
                                modified = True
                                needs_os_import = True
                                break

                new_lines.append(line)

            if modified:
                # 检查是否已有os import
                has_os_import = any('import os' in line for line in new_lines[:20])

                if needs_os_import and not has_os_import:
                    # 在文件开头添加os import
                    insert_pos = 0
                    # 找到第一个非注释、非空行的位置
                    for i, line in enumerate(new_lines):
                        if line.strip() and not line.strip().startswith('#'):
                            if line.strip().startswith('import') or line.strip().startswith('from'):
                                insert_pos = i
                                break

                    if insert_pos > 0:
                        new_lines.insert(insert_pos, 'import os')
                    else:
                        new_lines.insert(0, 'import os')

                    changes.append((1, '', 'Added: import os'))

                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))

            return changes

        except Exception as e:
            print(f"❌ 处理 {file_path} 时出错: {e}")
            return []

    def fix_all(self):
        """修复所有硬编码配置"""
        print("🔍 开始修复硬编码配置...\n")

        # 需要修复的文件列表（从报告中提取）
        files_to_fix = [
            "demo_complete_workflow.py",
            "quick_fix.py",
            "health_check.py",
            "create_analytics_tables.py",
            "init_db.py",
            "fieldmind-backend/app/config.py",
            "fieldmind-backend/app/tasks/rag_tasks.py",
            "fieldmind-backend/app/tasks/document_tasks.py",
            "fieldmind-backend/app/tasks/graph_tasks.py",
            "fieldmind-backend/app/core/config.py",
        ]

        print(f"📝 将修复 {len(files_to_fix)} 个文件\n")

        total_changes = 0

        for file_rel_path in files_to_fix:
            file_path = self.root_dir / file_rel_path

            if not file_path.exists():
                print(f"⚠️  文件不存在: {file_rel_path}")
                continue

            print(f"📄 处理: {file_rel_path}")

            changes = self.fix_localhost_urls(file_path)

            if changes:
                for line_num, old, new in changes:
                    if old:
                        print(f"   ✓ 行 {line_num}: {old[:60]}...")
                        print(f"      → {new[:60]}...")
                    else:
                        print(f"   ✓ {new}")
                total_changes += len(changes)
                self.fixes.append((file_rel_path, changes))
            else:
                print(f"   ℹ️  未发现需要修复的hardcoded配置")

            print()

        print(f"✅ 完成! 总共修复了 {total_changes} 处硬编码配置")

        # 生成修复报告
        self.generate_report()

    def generate_report(self):
        """生成修复报告"""
        report_path = self.root_dir / "HARDCODED_CONFIG_FIX_REPORT.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 硬编码配置修复报告\n\n")
            f.write(f"生成时间: {self._get_timestamp()}\n\n")

            f.write("## 修复摘要\n\n")
            f.write(f"- 总共修复文件: {len(self.fixes)}\n")
            total_changes = sum(len(changes) for _, changes in self.fixes)
            f.write(f"- 总共修复位置: {total_changes}\n\n")

            f.write("## 修复策略\n\n")
            f.write("所有硬编码的localhost URL已被替换为环境变量:\n\n")
            f.write("| 原始值 | 替换为 |\n")
            f.write("|--------|--------|\n")
            f.write("| `http://localhost:8000` | `os.getenv('API_BASE_URL', 'http://localhost:8000')` |\n")
            f.write("| `http://127.0.0.1:8000` | `os.getenv('API_BASE_URL', 'http://127.0.0.1:8000')` |\n")
            f.write("| `'localhost'` | `os.getenv('API_HOST', 'localhost')` |\n")
            f.write("| `'127.0.0.1'` | `os.getenv('API_HOST', '127.0.0.1')` |\n\n")

            if self.fixes:
                f.write("## 详细修复列表\n\n")
                for file_path, changes in self.fixes:
                    f.write(f"### {file_path}\n\n")
                    for line_num, old, new in changes:
                        if old:
                            f.write(f"**行 {line_num}:**\n")
                            f.write(f"```python\n# 修改前\n{old}\n\n# 修改后\n{new}\n```\n\n")
                        else:
                            f.write(f"- {new}\n")
                    f.write("\n")

            f.write("## 环境变量配置\n\n")
            f.write("需要在 `.env` 文件或环境中配置以下变量:\n\n")
            f.write("```bash\n")
            f.write("# API服务器配置\n")
            f.write("API_BASE_URL=http://localhost:8000  # 开发环境\n")
            f.write("# API_BASE_URL=https://api.fieldmind.com  # 生产环境\n\n")
            f.write("API_HOST=localhost  # 开发环境\n")
            f.write("# API_HOST=0.0.0.0  # 生产环境\n")
            f.write("```\n\n")

            f.write("## 后续工作\n\n")
            f.write("1. 在 `.env` 文件中添加相应的环境变量\n")
            f.write("2. 更新部署文档，说明需要的环境变量\n")
            f.write("3. 在生产环境中设置正确的API URL\n")
            f.write("4. 测试所有修改的文件，确保功能正常\n")

        print(f"\n📊 修复报告已生成: {report_path}")

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    fixer = HardcodedConfigFixer("/Users/alwan/FieldMind-Rebuild")
    fixer.fix_all()
