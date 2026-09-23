#!/usr/bin/env python3
"""分析分析模块的端点"""
import re
from pathlib import Path

analysis_modules = [
    "src/app/api/creative_analysis.py",
    "src/app/api/business_analysis.py",
    "src/app/api/analytics.py",
]

print("="*80)
print("分析模块分析")
print("="*80)

total_endpoints = 0
all_endpoints = {}

for module_path in analysis_modules:
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
    for ep in endpoints[:15]:
        print(f"   {ep}")
    if len(endpoints) > 15:
        print(f"   ... 还有 {len(endpoints)-15} 个端点")

print(f"\n" + "="*80)
print(f"总计: {total_endpoints} 个端点")
print("="*80)

# 分析功能重复
print("\n功能分类:")
categories = {
    "文创分析": [],
    "业态分析": [],
    "数据聚合": [],
    "统计": [],
    "其他": []
}

for module, endpoints in all_endpoints.items():
    for ep in endpoints:
        path = ep.split()[1].lower()
        if 'creative' in module.lower():
            categories["文创分析"].append((module, ep))
        elif 'business' in module.lower():
            categories["业态分析"].append((module, ep))
        elif 'aggregate' in path or 'summary' in path:
            categories["数据聚合"].append((module, ep))
        elif 'stat' in path or 'count' in path:
            categories["统计"].append((module, ep))
        else:
            categories["其他"].append((module, ep))

for cat, items in categories.items():
    if items:
        print(f"\n{cat} ({len(items)}个):")
        for module, ep in items[:5]:
            print(f"   {module:30} {ep}")
        if len(items) > 5:
            print(f"   ... 还有 {len(items)-5} 个")

