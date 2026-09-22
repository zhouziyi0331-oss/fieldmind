#!/usr/bin/env python3
"""分析API覆盖率和未注册的模块"""
import re
from pathlib import Path

# 读取main.py
with open('src/app/main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

# 找到所有include_router调用
registered_patterns = re.findall(r'app\.include_router\(([^,\)]+)', main_content)
registered_modules = set()
for pattern in registered_patterns:
    # 提取模块名（去掉.router）
    module = pattern.strip().replace('.router', '').split('.')[-1]
    registered_modules.add(module)

# 扫描所有API文件
api_files = []
for file in Path("src/app/api").rglob("*.py"):
    if file.name not in ["__init__.py"]:
        # 检查是否有router定义
        content = file.read_text(encoding='utf-8')
        if 'APIRouter' in content or '@router.' in content:
            api_files.append(file)

# 提取模块名
all_modules = set()
for file in api_files:
    module_name = file.stem  # 文件名（不含扩展名）
    all_modules.add(module_name)

# 找出未注册的模块
unregistered = all_modules - registered_modules

print("="*80)
print("API注册情况分析")
print("="*80)
print(f"\n📊 总览:")
print(f"   - API文件总数: {len(api_files)}")
print(f"   - 已注册模块: {len(registered_modules)}")
print(f"   - 未注册模块: {len(unregistered)}")
print(f"   - 注册率: {len(registered_modules)/len(all_modules)*100:.1f}%")

print(f"\n❌ 未注册的API模块 ({len(unregistered)}个):")
for i, module in enumerate(sorted(unregistered)[:30], 1):
    print(f"   {i}. {module}")
if len(unregistered) > 30:
    print(f"   ... 还有 {len(unregistered)-30} 个")

# 找出重要但未注册的
important_keywords = ['graph', 'rag', 'search', 'analysis', 'agent', 'workflow', 'document']
important_missing = []
for module in unregistered:
    for keyword in important_keywords:
        if keyword in module.lower():
            important_missing.append(module)
            break

print(f"\n⚠️  重要但未注册的模块 ({len(important_missing)}个):")
for module in sorted(important_missing):
    print(f"   - {module}")

