#!/usr/bin/env python3
"""第2步调整：批量识别可删除的v1模块"""
import sys
import json
sys.path.insert(0, 'src')

print("="*80)
print("🔍 第2步调整：批量识别可删除的v1模块")
print("="*80)

# 读取端点清单
with open('endpoint_inventory.json', 'r', encoding='utf-8') as f:
    inventory = json.load(f)

# 获取所有v1端点
v1_routes = inventory['categories']['旧版API']['endpoints']

# 按模块分组
from collections import defaultdict
v1_modules = defaultdict(list)

for route in v1_routes:
    path = route['path']
    if '/api/v1/' in path:
        parts = path.split('/')
        if len(parts) >= 4:
            module = parts[3]
            v1_modules[module].append(route)

print(f"\n找到 {len(v1_modules)} 个v1模块:")
print("-"*80)

# 统一模块映射
unified_mapping = {
    'documents': '统一文档处理',
    'rag': '统一RAG检索',
    'chat': '统一聊天对话',
    'analysis': '统一分析',
    'projects': '统一项目管理',
    'skills': '统一技能管理',
    'reports': '统一报告生成',
}

# 分类
can_delete_modules = []
need_review_modules = []

for module, routes in sorted(v1_modules.items(), key=lambda x: len(x[1]), reverse=True):
    count = len(routes)
    
    # 判断是否可以删除
    if module in unified_mapping:
        can_delete_modules.append({
            'module': module,
            'count': count,
            'unified': unified_mapping[module],
            'reason': f'已有{unified_mapping[module]}'
        })
    else:
        need_review_modules.append({
            'module': module,
            'count': count,
            'reason': '需要评估是否保留'
        })

print(f"\n【可立即删除的v1模块】")
print("-"*80)
total_deletable = 0
for m in can_delete_modules:
    print(f"  ❌ v1/{m['module']:30s} {m['count']:3d} 个端点 → {m['unified']}")
    total_deletable += m['count']

print(f"\n  可删除端点总计: {total_deletable} 个")

print(f"\n【需要评估的v1模块】 (前10个)")
print("-"*80)
for m in need_review_modules[:10]:
    print(f"  ⚠️  v1/{m['module']:30s} {m['count']:3d} 个端点")

print(f"\n" + "="*80)
print("💡 第2步调整策略")
print("="*80)

print(f"\n优先级1: 删除明确重复的v1模块")
print(f"  • v1/documents (1个) - 已有统一文档")
print(f"  • v1/chat (3个) - 已有统一聊天")
print(f"  • v1/analysis (0个，已删除) ✅")
print(f"  • v1/reports (3个) - 已有统一报告")
print(f"  • v1/skills (0个) - 已有统一技能")

# 查找这些模块的注册
print(f"\n查找main.py中的注册位置:")
print("-"*80)

with open('src/app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

targets = ['v1/documents', 'v1/reports', 'v1/skills', 'v1/chat']

for target in targets:
    found = False
    for i, line in enumerate(lines, 1):
        if 'include_router' in line and target.replace('/', '') in line.replace('_', '').replace('-', ''):
            print(f"\nv1/{target.split('/')[1]}:")
            print(f"  第{i}行: {line.strip()}")
            found = True
    if not found:
        print(f"\nv1/{target.split('/')[1]}: 未找到注册")

# 保存批量删除列表
batch_delete = {
    'step': '第2步批量删除',
    'modules': can_delete_modules,
    'total_endpoints': total_deletable
}

with open('step2_batch_delete_list.json', 'w', encoding='utf-8') as f:
    json.dump(batch_delete, f, indent=2, ensure_ascii=False)

print(f"\n✅ 批量删除列表已保存到: step2_batch_delete_list.json")

