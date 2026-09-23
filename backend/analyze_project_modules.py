#!/usr/bin/env python3
"""分析项目管理模块的端点"""
import re
from pathlib import Path

project_modules = [
    "src/app/api/v1/projects.py",
    "src/app/api/v1/project_documents.py",
]

print("="*80)
print("项目管理模块分析")
print("="*80)

total_endpoints = 0
all_endpoints = {}

for module_path in project_modules:
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
    "项目管理": [],
    "文档管理": [],
    "其他": []
}

for module, endpoints in all_endpoints.items():
    for ep in endpoints:
        path = ep.split()[1].lower()
        if 'document' in path:
            categories["文档管理"].append((module, ep))
        elif 'project' in path or ep.startswith('GET    /') or ep.startswith('POST   /'):
            categories["项目管理"].append((module, ep))
        else:
            categories["其他"].append((module, ep))

for cat, items in categories.items():
    if items:
        print(f"\n{cat} ({len(items)}个):")
        for module, ep in items[:10]:
            print(f"   {module:30} {ep}")
        if len(items) > 10:
            print(f"   ... 还有 {len(items)-10} 个")

