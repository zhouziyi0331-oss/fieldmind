#!/usr/bin/env python3
"""分析RAG检索模块的端点"""
import re
from pathlib import Path

rag_modules = [
    "src/app/api/deep_rag.py",
    "src/app/api/chat_rag.py",
    "src/app/api/rag_p3.py",
    "src/app/api/hierarchical_retrieval.py",
    "src/app/api/v1/rag.py",
]

print("="*80)
print("RAG检索模块分析")
print("="*80)

total_endpoints = 0
all_endpoints = {}

for module_path in rag_modules:
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
    "检索/查询": [],
    "对话": [],
    "评测": [],
    "反馈": [],
    "配置": [],
    "其他": []
}

for module, endpoints in all_endpoints.items():
    for ep in endpoints:
        path = ep.split()[1].lower()
        if 'chat' in path or 'conversation' in path:
            categories["对话"].append((module, ep))
        elif 'query' in path or 'search' in path or 'retrieve' in path:
            categories["检索/查询"].append((module, ep))
        elif 'eval' in path or 'test' in path or 'benchmark' in path:
            categories["评测"].append((module, ep))
        elif 'feedback' in path or 'rating' in path:
            categories["反馈"].append((module, ep))
        elif 'config' in path or 'settings' in path:
            categories["配置"].append((module, ep))
        else:
            categories["其他"].append((module, ep))

for cat, items in categories.items():
    if items:
        print(f"\n{cat} ({len(items)}个):")
        for module, ep in items[:5]:
            print(f"   {module:30} {ep}")
        if len(items) > 5:
            print(f"   ... 还有 {len(items)-5} 个")

