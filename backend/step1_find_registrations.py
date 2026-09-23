#!/usr/bin/env python3
"""查找main.py中需要注释的注册代码"""

print("="*80)
print("🔍 查找需要注释的注册代码")
print("="*80)

# 读取main.py
with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找v1相关的注册
modules_to_remove = ['documents', 'analysis', 'reports', 'chat-enhancement']

registrations_found = []

for i, line in enumerate(lines, 1):
    if 'include_router' in line:
        for module in modules_to_remove:
            # 查找v1模块的注册
            if f'v1/{module}' in line or f'v1_{module}' in line.replace('-', '_') or module in line:
                if '/api/v1/' in line or 'v1.' in line:
                    registrations_found.append({
                        'line_num': i,
                        'line': line.strip(),
                        'module': module
                    })

print(f"\n找到 {len(registrations_found)} 个需要注释的注册:")
print("-"*80)

for reg in registrations_found:
    print(f"\n第{reg['line_num']}行: {reg['module']}")
    print(f"  {reg['line']}")

# 显示上下文
print(f"\n" + "="*80)
print("📋 具体位置和上下文")
print("="*80)

for reg in registrations_found[:5]:  # 显示前5个
    line_num = reg['line_num']
    print(f"\n第{line_num}行附近:")
    # 显示前后3行
    start = max(0, line_num - 3)
    end = min(len(lines), line_num + 2)
    for i in range(start, end):
        marker = ">>> " if i == line_num - 1 else "    "
        print(f"{marker}{i+1:4d}: {lines[i].rstrip()}")

