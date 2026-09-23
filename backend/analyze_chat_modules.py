#!/usr/bin/env python3
"""分析聊天对话模块的端点"""
import re
from pathlib import Path

chat_modules = [
    "src/app/api/chat.py",
    "src/app/api/v1/enhanced_chat.py",
    "src/app/api/v1/project_chat.py",
    "src/app/api/conversation_memory.py",
    "src/app/api/v1/conversation.py",
]

print("="*80)
print("聊天对话模块分析")
print("="*80)

total_endpoints = 0
all_endpoints = {}

for module_path in chat_modules:
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

# 分析功能重复
print("\n功能分类:")
categories = {
    "基础对话": [],
    "项目对话": [],
    "会话管理": [],
    "历史记录": [],
    "其他": []
}

for module, endpoints in all_endpoints.items():
    for ep in endpoints:
        path = ep.split()[1].lower()
        if 'project' in path:
            categories["项目对话"].append((module, ep))
        elif 'session' in path or 'conversation' in path:
            categories["会话管理"].append((module, ep))
        elif 'history' in path or 'messages' in path:
            categories["历史记录"].append((module, ep))
        elif 'chat' in path or 'send' in path or 'message' in path:
            categories["基础对话"].append((module, ep))
        else:
            categories["其他"].append((module, ep))

for cat, items in categories.items():
    if items:
        print(f"\n{cat} ({len(items)}个):")
        for module, ep in items[:5]:
            print(f"   {module:30} {ep}")
        if len(items) > 5:
            print(f"   ... 还有 {len(items)-5} 个")

