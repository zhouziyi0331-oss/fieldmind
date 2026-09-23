#!/usr/bin/env python3
"""分析文档处理模块的端点"""
import re
from pathlib import Path

doc_modules = [
    "src/app/api/documents.py",
    "src/app/api/document_processing.py",
    "src/app/api/document_processing_v2.py",
    "src/app/api/document_normalization.py",
    "src/app/api/v1/documents.py",
]

print("="*80)
print("文档处理模块分析")
print("="*80)

total_endpoints = 0
all_endpoints = {}

for module_path in doc_modules:
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
    for ep in endpoints:
        print(f"   {ep}")

print(f"\n" + "="*80)
print(f"总计: {total_endpoints} 个端点")
print("="*80)

# 分析功能重复
print("\n功能分类:")
categories = {
    "上传": [],
    "处理/解析": [],
    "查询/获取": [],
    "更新": [],
    "删除": [],
    "批量操作": [],
    "状态/统计": [],
    "其他": []
}

for module, endpoints in all_endpoints.items():
    for ep in endpoints:
        path = ep.split()[1].lower()
        if 'upload' in path:
            categories["上传"].append((module, ep))
        elif 'process' in path or 'parse' in path or 'extract' in path:
            categories["处理/解析"].append((module, ep))
        elif 'batch' in path:
            categories["批量操作"].append((module, ep))
        elif 'status' in path or 'stat' in path or 'progress' in path:
            categories["状态/统计"].append((module, ep))
        elif ep.startswith('GET'):
            categories["查询/获取"].append((module, ep))
        elif ep.startswith('PUT') or ep.startswith('PATCH'):
            categories["更新"].append((module, ep))
        elif ep.startswith('DELETE'):
            categories["删除"].append((module, ep))
        else:
            categories["其他"].append((module, ep))

for cat, items in categories.items():
    if items:
        print(f"\n{cat} ({len(items)}个):")
        for module, ep in items[:5]:
            print(f"   {module:30} {ep}")
        if len(items) > 5:
            print(f"   ... 还有 {len(items)-5} 个")

