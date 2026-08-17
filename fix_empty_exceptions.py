#!/usr/bin/env python3
"""
修复空的异常处理器
Fix empty exception handlers that hide errors
"""

import re
from pathlib import Path
from typing import List, Tuple

class EmptyExceptionFixer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.fixes = []

    def fix_python_empty_except(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """修复Python文件中的空except块"""
        changes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # 查找 except: pass 模式
            pattern = r'except.*:\s*pass\s*(?:#.*)?$'

            new_lines = []
            modified = False
            i = 0

            while i < len(lines):
                line = lines[i]

                # 检查是否是空except
                if re.search(pattern, line):
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent

                    # 替换为带日志的异常处理
                    old_line = line
                    new_lines.append(f'{indent_str}except Exception as e:')
                    new_lines.append(f'{indent_str}    logger.warning(f"异常被忽略: {{e}}")')
                    new_lines.append(f'{indent_str}    pass  # TODO: 添加适当的错误处理')

                    changes.append((i + 1, old_line.strip(), 'Added logging for ignored exception'))
                    modified = True
                else:
                    new_lines.append(line)

                i += 1

            if modified:
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))

            return changes

        except Exception as e:
            print(f"❌ 处理 {file_path} 时出错: {e}")
            return []

    def fix_typescript_empty_catch(self, file_path: Path) -> List[Tuple[int, str, str]]:
        """修复TypeScript文件中的空catch块"""
        changes = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            new_lines = []
            modified = False
            i = 0

            while i < len(lines):
                line = lines[i]

                # 检查 } catch { 或 } catch (e) { 后面只有 }
                if 'catch' in line and '{' in line:
                    # 找到catch块的结束
                    indent = len(line) - len(line.lstrip())
                    indent_str = ' ' * indent

                    # 检查下一行是否直接是 }
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line == '}' or next_line.startswith('}'):
                            # 这是一个空catch块
                            old_line = line

                            # 确保catch有参数
                            if 'catch {' in line:
                                line = line.replace('catch {', 'catch (error) {')
                            elif 'catch(' in line and ')' not in line:
                                # 处理多行的情况
                                pass

                            new_lines.append(line)
                            new_lines.append(f'{indent_str}  console.warn("异常被忽略:", error);')
                            new_lines.append(f'{indent_str}  // TODO: 添加适当的错误处理')

                            changes.append((i + 1, old_line.strip(), 'Added logging for ignored exception'))
                            modified = True
                            i += 1  # 跳过原来的空}行
                            continue

                new_lines.append(line)
                i += 1

            if modified:
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))

            return changes

        except Exception as e:
            print(f"❌ 处理 {file_path} 时出错: {e}")
            return []

    def fix_all(self):
        """修复所有空的异常处理"""
        print("🔍 开始修复空的异常处理器...\n")

        # 从报告中读取需要修复的文件
        report_file = self.root_dir / "FIELDMIND_ISSUES_REPORT.md"

        if not report_file.exists():
            print("❌ 找不到问题报告文件")
            return

        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取空异常处理器的文件路径
        in_section = False
        files_to_fix = []

        for line in content.split('\n'):
            if '### 3. 空的异常处理器' in line:
                in_section = True
                continue

            if in_section:
                if line.startswith('###'):
                    break

                # 提取文件路径 (格式: - fieldmind-backend/...)
                if line.strip().startswith('- '):
                    parts = line.split('行 ')[0].strip('- ').strip()
                    if parts:
                        files_to_fix.append(parts)

        if not files_to_fix:
            print("✅ 没有发现需要修复的空异常处理器")
            return

        print(f"📝 找到 {len(files_to_fix)} 个文件需要修复\n")

        total_changes = 0

        for file_rel_path in files_to_fix:
            file_path = self.root_dir / file_rel_path

            if not file_path.exists():
                print(f"⚠️  文件不存在: {file_rel_path}")
                continue

            print(f"📄 处理: {file_rel_path}")

            changes = []
            if file_path.suffix == '.py':
                changes = self.fix_python_empty_except(file_path)
            elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
                changes = self.fix_typescript_empty_catch(file_path)

            if changes:
                for line_num, old, description in changes:
                    print(f"   ✓ 行 {line_num}: {description}")
                    total_changes += 1
                self.fixes.append((file_rel_path, changes))
            else:
                print(f"   ⚠️  没有发现可自动修复的模式")

        print(f"\n✅ 完成! 总共修复了 {total_changes} 处空异常处理")

        # 生成修复报告
        self.generate_report()

    def generate_report(self):
        """生成修复报告"""
        report_path = self.root_dir / "EMPTY_EXCEPTION_FIX_REPORT.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 空异常处理器修复报告\n\n")
            f.write(f"生成时间: {self._get_timestamp()}\n\n")

            f.write("## 修复摘要\n\n")
            f.write(f"- 总共修复文件: {len(self.fixes)}\n")
            total_changes = sum(len(changes) for _, changes in self.fixes)
            f.write(f"- 总共修复位置: {total_changes}\n\n")

            f.write("## 修复内容\n\n")
            f.write("所有空的异常处理器已被替换为:\n\n")
            f.write("**Python:**\n")
            f.write("```python\n")
            f.write("except Exception as e:\n")
            f.write("    logger.warning(f\"异常被忽略: {e}\")\n")
            f.write("    pass  # TODO: 添加适当的错误处理\n")
            f.write("```\n\n")

            f.write("**TypeScript/JavaScript:**\n")
            f.write("```typescript\n")
            f.write("catch (error) {\n")
            f.write("  console.warn(\"异常被忽略:\", error);\n")
            f.write("  // TODO: 添加适当的错误处理\n")
            f.write("}\n")
            f.write("```\n\n")

            if self.fixes:
                f.write("## 详细修复列表\n\n")
                for file_path, changes in self.fixes:
                    f.write(f"### {file_path}\n\n")
                    for line_num, old, desc in changes:
                        f.write(f"- 行 {line_num}: {desc}\n")
                    f.write("\n")

            f.write("## 后续工作\n\n")
            f.write("1. 检查每个 TODO 注释\n")
            f.write("2. 为每个异常添加适当的错误处理逻辑\n")
            f.write("3. 考虑是否需要向用户显示错误消息\n")
            f.write("4. 确保日志记录配置正确\n")

        print(f"\n📊 修复报告已生成: {report_path}")

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    fixer = EmptyExceptionFixer("/Users/alwan/FieldMind-Rebuild")
    fixer.fix_all()
