#!/usr/bin/env python3
"""诊断路由注册问题"""

print("="*80)
print("🔍 诊断统一模块的router prefix配置")
print("="*80)

# 检查每个统一模块的router定义
unified_modules = [
    'src/app/api/unified_knowledge_graph.py',
    'src/app/api/unified_documents.py',
    'src/app/api/unified_rag.py',
    'src/app/api/unified_chat.py',
    'src/app/api/unified_analysis.py',
    'src/app/api/unified_projects.py',
    'src/app/api/unified_skills.py',
    'src/app/api/unified_reports.py',
    'src/app/api/unified_tools.py',
]

print("\n检查各模块的APIRouter定义:")
for module_path in unified_modules:
    with open(module_path, 'r') as f:
        lines = f.readlines()
        
    module_name = module_path.split('/')[-1].replace('.py', '')
    
    # 查找router定义
    for i, line in enumerate(lines[:30], 1):  # 只看前30行
        if 'APIRouter' in line and 'router =' in line:
            print(f"\n{module_name}:")
            print(f"  第{i}行: {line.strip()}")
            
            # 检查prefix
            if 'prefix=' in line:
                import re
                prefix_match = re.search(r'prefix=["\']([^"\']+)["\']', line)
                if prefix_match:
                    prefix = prefix_match.group(1)
                    print(f"  ✓ prefix: {prefix}")
                else:
                    print(f"  ⚠️  prefix格式异常")
            else:
                print(f"  ❌ 没有设置prefix!")
            break

# 检查main.py中如何注册这些模块
print("\n" + "="*80)
print("🔍 检查main.py中的注册方式")
print("="*80)

with open('src/app/main.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

print("\n查找统一模块的注册语句:")
import re

for i, line in enumerate(lines, 1):
    if 'unified_' in line and 'include_router' in line:
        print(f"\n第{i}行: {line.strip()}")
        
        # 查看前后几行的上下文
        if i > 1:
            print(f"  上文: {lines[i-2].strip()}")
        if i < len(lines):
            print(f"  下文: {lines[i].strip() if i < len(lines) else ''}")

print("\n" + "="*80)
print("💡 问题诊断")
print("="*80)

print("\n可能的问题:")
print("1. 统一模块的router已经有prefix='/api/xxx'")
print("2. main.py中注册时又加了prefix")
print("3. 导致实际路径变成 /api/xxx/api/xxx")
print("4. 前端无法访问这些端点")

print("\n或者:")
print("1. FastAPI的路由统计方法有问题")
print("2. 实际端点已注册但统计脚本没有正确识别")

