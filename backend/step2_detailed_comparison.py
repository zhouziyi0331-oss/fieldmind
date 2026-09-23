#!/usr/bin/env python3
"""详细对比v1/projects和统一项目管理的端点"""
import sys
import json
sys.path.insert(0, 'src')

print("="*80)
print("📋 详细对比v1/projects和统一项目管理")
print("="*80)

# 读取分析结果
with open('step2_v1_projects_analysis.json', 'r', encoding='utf-8') as f:
    analysis = json.load(f)

with open('endpoint_inventory.json', 'r', encoding='utf-8') as f:
    inventory = json.load(f)

# 获取统一项目管理的端点
unified_routes = inventory['categories']['统一模块']['endpoints']
unified_projects = [r for r in unified_routes if '/api/projects' in r['path']]

print(f"\n统一项目管理模块的端点 ({len(unified_projects)}个):")
print("-"*80)
for r in unified_projects:
    print(f"  {r['methods']:15s} {r['path']}")

# 分析v1/projects中的端点
print(f"\n" + "="*80)
print("🔍 v1/projects端点分析")
print("="*80)

# 读取v1/projects的所有端点
v1_all = []
for action in analysis['actions']:
    v1_all.extend(action['routes'])

# 分类
can_delete = []  # 可以直接删除（功能已在统一模块）
need_migrate = []  # 需要迁移到统一模块
keep = []  # 需要保留的特殊功能

print(f"\n分析 {len(v1_all)} 个v1/projects端点:")

for route in v1_all:
    path = route['path']
    
    # 基本CRUD - 统一模块已有
    if (path.endswith('/projects') or path.endswith('/projects/') or 
        '/api/v1/projects/{project_id}' == path):
        can_delete.append({**route, 'reason': '基本CRUD已在统一模块'})
    
    # 成员管理 - 可能需要迁移
    elif '/members' in path:
        need_migrate.append({**route, 'reason': '成员管理功能需要迁移'})
    
    # 文档相关 - 已有统一文档模块
    elif '/documents' in path and 'recommendation' not in path:
        can_delete.append({**route, 'reason': '文档功能已在统一文档模块'})
    
    # 上下文管理 - 统一模块已有
    elif '/contexts' in path:
        can_delete.append({**route, 'reason': '上下文管理已在统一模块'})
    
    # 统计信息 - 可以整合
    elif '/stats' in path or '/statistics' in path:
        can_delete.append({**route, 'reason': '统计功能可整合到统一模块'})
    
    # 特殊功能 - 需要评估
    elif any(keyword in path for keyword in ['/analyze', '/workflow', '/distill', '/export']):
        keep.append({**route, 'reason': '特殊功能，需要评估是否迁移'})
    
    else:
        keep.append({**route, 'reason': '其他功能，需要评估'})

print(f"\n分类结果:")
print(f"  ✅ 可以直接删除: {len(can_delete)} 个")
print(f"  🔄 需要先迁移: {len(need_migrate)} 个")
print(f"  ⚠️  需要评估: {len(keep)} 个")

# 显示可删除的端点
print(f"\n【可以直接删除的端点】 ({len(can_delete)}个)")
print("-"*80)
for r in can_delete[:10]:
    print(f"  ❌ {r['methods']:15s} {r['path']}")
    print(f"     原因: {r['reason']}")
if len(can_delete) > 10:
    print(f"  ... 还有 {len(can_delete) - 10} 个")

# 显示需要迁移的端点
print(f"\n【需要先迁移的端点】 ({len(need_migrate)}个)")
print("-"*80)
for r in need_migrate[:5]:
    print(f"  🔄 {r['methods']:15s} {r['path']}")
    print(f"     原因: {r['reason']}")
if len(need_migrate) > 5:
    print(f"  ... 还有 {len(need_migrate) - 5} 个")

# 显示需要评估的端点
print(f"\n【需要评估的端点】 ({len(keep)}个)")
print("-"*80)
for r in keep[:10]:
    print(f"  ⚠️  {r['methods']:15s} {r['path']}")
    print(f"     原因: {r['reason']}")
if len(keep) > 10:
    print(f"  ... 还有 {len(keep) - 10} 个")

# 保存决策
decision = {
    'can_delete': can_delete,
    'need_migrate': need_migrate,
    'keep': keep
}

with open('step2_deletion_decision.json', 'w', encoding='utf-8') as f:
    json.dump(decision, f, indent=2, ensure_ascii=False)

print(f"\n" + "="*80)
print("💡 建议")
print("="*80)
print(f"\n立即可删除: {len(can_delete)} 个端点")
print(f"  预计减少端点数: {len(can_delete)}")
print(f"  执行时间: 10-15分钟")
print(f"\n成员管理功能: 需要先补充到unified_projects模块")
print(f"  需要迁移: {len(need_migrate)} 个端点")
print(f"  预计工作时间: 1-2小时")
print(f"\n特殊功能: 需要逐个评估")
print(f"  需要评估: {len(keep)} 个端点")
print(f"  建议: 暂时保留，后续阶段处理")

print(f"\n✅ 决策结果已保存到: step2_deletion_decision.json")

