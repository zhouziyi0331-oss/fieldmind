#!/usr/bin/env python3
"""分析技能管理模块的端点"""
import re
from pathlib import Path

skill_modules = [
    "src/app/api/v1/skills.py",
    "src/app/api/v1/skill_generation.py",
    "src/app/api/v1/skill_optimization.py",
]

print("="*80)
print("技能管理模块分析")
print("="*80)

total_endpoints = 0
all_endpoints = {}

for module_path in skill_modules:
    module_name = Path(module_path).stem
    parent = Path(module_path).parent.name
    full_name = f"{parent}/{module_name}" if parent != "api" else module_name
    
    if not Path(module_path).exists():
        print(f"\n❌ {full_name}: 文件不存在")
        continue
    
    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取端点
    pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)
    
    endpoints = []
    for method, path in matches:
        endpoints.append(f"{method.upper():6} {path}")
    
    all_endpoints[full_name] = endpoints
    total_endpoints += len(endpoints)
    
    print(f"\n📁 {full_name} ({len(endpoints)}个端点)")
    for ep in endpoints[:10]:
        print(f"   {ep}")
    if len(endpoints) > 10:
        print(f"   ... 还有 {len(endpoints)-10} 个端点")

print(f"\n" + "="*80)
print(f"总计: {total_endpoints} 个端点")
print("="*80)

