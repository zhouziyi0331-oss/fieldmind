#!/usr/bin/env python3
"""检查常见代码错误和 bug"""

import os
import re
import ast
from pathlib import Path

PROJECT_ROOT = Path(".")

def check_python_syntax():
    """检查 Python 语法错误"""
    errors = []
    for f in PROJECT_ROOT.rglob("*.py"):
        if 'venv' in str(f) or '.git' in str(f):
            continue
        try:
            ast.parse(f.read_text(encoding='utf-8', errors='ignore'))
        except SyntaxError as e:
            errors.append(f"{f}:{e.lineno} - {e.msg}")
    return errors

def check_common_bugs():
    """检查常见 bug 模式"""
    issues = []

    for f in PROJECT_ROOT.rglob("*.py"):
        if 'venv' in str(f) or '.git' in str(f):
            continue

        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')

            for i, line in enumerate(lines, 1):
                # 裸 except
                if re.match(r'\s*except\s*:', line):
                    issues.append(f"{f}:{i} - 裸 except（应指定异常类型）")

                # 可变默认参数
                if re.search(r'def\s+\w+\([^)]*=\s*(\[\]|\{\})', line):
                    issues.append(f"{f}:{i} - 可变默认参数（应使用 None）")

                # 硬编码密码
                if re.search(r'(password|secret|api_key)\s*=\s*[\'"][^\'"]+[\'"]', line, re.I):
                    issues.append(f"{f}:{i} - 可能的硬编码密钥")
        except:
            pass

    return issues

def check_todo_fixme():
    """检查未完成的 TODO/FIXME"""
    todos = []
    for ext in ['*.py', '*.js', '*.html']:
        for f in PROJECT_ROOT.rglob(ext):
            if 'venv' in str(f) or '.git' in str(f) or 'node_modules' in str(f):
                continue
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                for i, line in enumerate(content.split('\n'), 1):
                    if re.search(r'(TODO|FIXME|XXX|HACK)', line, re.I):
                        todos.append(f"{f}:{i} - {line.strip()[:80]}")
            except:
                pass
    return todos

def main():
    print("🔍 检查代码 bug...\n")
    print("=" * 60)

    print("\n📌 Python 语法错误：")
    syntax_errors = check_python_syntax()
    if syntax_errors:
        for e in syntax_errors[:20]:
            print(f"   ❌ {e}")
        if len(syntax_errors) > 20:
            print(f"   ... 还有 {len(syntax_errors) - 20} 个")
    else:
        print("   ✅ 无语法错误")

    print("\n📌 常见 bug 模式：")
    bugs = check_common_bugs()
    if bugs:
        for b in bugs[:20]:
            print(f"   ⚠️ {b}")
        if len(bugs) > 20:
            print(f"   ... 还有 {len(bugs) - 20} 个")
    else:
        print("   ✅ 未发现常见 bug")

    print("\n📌 未完成的 TODO/FIXME：")
    todos = check_todo_fixme()
    if todos:
        for t in todos[:20]:
            print(f"   📝 {t}")
        if len(todos) > 20:
            print(f"   ... 还有 {len(todos) - 20} 个")
        print(f"\n   共 {len(todos)} 个")
    else:
        print("   ✅ 无未完成标记")

if __name__ == "__main__":
    main()
