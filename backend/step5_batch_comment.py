#!/usr/bin/env python3
"""第5步：批量注释v1模块注册"""
import json

print("="*80)
print("🔧 第5步：批量注释v1模块注册")
print("="*80)

# 读取激进计划
with open('step5_aggressive_plan.json', 'r', encoding='utf-8') as f:
    plan = json.load(f)

registrations = plan['registrations']

print(f"\n准备注释 {len(registrations)} 个v1模块注册")

# 读取main.py
with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 标记需要注释的行
lines_to_comment = set([r['line'] for r in registrations])

# 创建新内容
new_lines = []
commented_count = 0

for i, line in enumerate(lines, 1):
    if i in lines_to_comment:
        # 如果这行还没被注释
        if not line.strip().startswith('#'):
            # 添加注释标记
            indent = len(line) - len(line.lstrip())
            new_line = ' ' * indent + '# ⚠️ [阶段5清理-第5步] v1模块批量清理\n'
            new_line += ' ' * indent + '# ' + line.lstrip()
            new_lines.append(new_line)
            commented_count += 1
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

# 写回文件
with open('src/app/main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\n✅ 已注释 {commented_count} 行v1模块注册")
print(f"✅ 文件已更新: src/app/main.py")

print(f"\n接下来将测试应用是否能正常启动...")

