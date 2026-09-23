#!/usr/bin/env python3
"""分析知识图谱模块的端点"""
import re
from pathlib import Path

kg_modules = [
    "src/app/api/knowledge_graph.py",
    "src/app/api/knowledge_graph_v3.py",
    "src/app/api/knowledge_graph_p3.py",
    "src/app/api/v1/knowledge_graph.py",
    "src/app/api/v1/knowledge_graph_api.py",
    "src/app/api/v1/knowledge_graph_enhanced.py",
    "src/app/api/v1/experience_graph.py",
    "src/app/api/v1/kg_visualization.py",
]

print("="*80)
print("知识图谱模块分析")
print("="*80)

total_endpoints = 0
all_endpoints = {}

for module_path in kg_modules:
    module_name = Path(module_path).stem
    
    if not Path(module_path).exists():
        print(f"\n❌ {module_name}: 文件不存在")
        continue
    
    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取端点
    pattern = r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)
    
    endpoints = []
    for method, path in matches:
        endpoints.append(f"{method.upper():6} {path}")
    
    all_endpoints[module_name] = endpoints
    total_endpoints += len(endpoints)
    
    print(f"\n📁 {module_name} ({len(endpoints)}个端点)")
    for ep in endpoints[:5]:
        print(f"   {ep}")
    if len(endpoints) > 5:
        print(f"   ... 还有 {len(endpoints)-5} 个端点")

print(f"\n" + "="*80)
print(f"总计: {total_endpoints} 个端点")
print("="*80)

# 分析功能重复
print("\n功能分类:")
categories = {
    "构建/重建": [],
    "查询": [],
    "统计": [],
    "可视化": [],
    "实体操作": [],
    "关系操作": [],
    "其他": []
}

for module, endpoints in all_endpoints.items():
    for ep in endpoints:
        path = ep.split()[1]
        if 'build' in path or 'rebuild' in path or 'construct' in path:
            categories["构建/重建"].append((module, ep))
        elif 'stat' in path or 'summary' in path:
            categories["统计"].append((module, ep))
        elif 'visual' in path or 'graph' in path:
            categories["可视化"].append((module, ep))
        elif 'entities' in path or 'entity' in path or 'node' in path:
            categories["实体操作"].append((module, ep))
        elif 'relation' in path or 'edge' in path:
            categories["关系操作"].append((module, ep))
        elif 'query' in path or 'search' in path:
            categories["查询"].append((module, ep))
        else:
            categories["其他"].append((module, ep))

for cat, items in categories.items():
    if items:
        print(f"\n{cat} ({len(items)}个):")
        for module, ep in items[:3]:
            print(f"   {module:30} {ep}")
        if len(items) > 3:
            print(f"   ... 还有 {len(items)-3} 个")

