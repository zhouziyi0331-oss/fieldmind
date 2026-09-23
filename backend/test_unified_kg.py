#!/usr/bin/env python3
"""测试统一知识图谱模块"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("测试统一知识图谱模块")
print("="*80)

try:
    print("\n1. 导入应用...")
    from app.main import app
    print("   ✅ 应用导入成功")
    
    print("\n2. 检查统一知识图谱路由...")
    routes = list(app.routes)
    
    # 查找 /api/kg 开头的路由
    kg_routes = [r for r in routes if hasattr(r, 'path') and r.path.startswith('/api/kg')]
    
    print(f"   找到 {len(kg_routes)} 个知识图谱相关路由:")
    
    # 按前缀分组
    by_prefix = {}
    for route in kg_routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            prefix = route.path.split('/')[2] if len(route.path.split('/')) > 2 else 'root'
            if prefix not in by_prefix:
                by_prefix[prefix] = []
            methods = ','.join(route.methods) if route.methods else 'ANY'
            by_prefix[prefix].append(f"{methods:15} {route.path}")
    
    for prefix, paths in sorted(by_prefix.items()):
        print(f"\n   📁 /api/{prefix}/ ({len(paths)}个端点)")
        for path in paths[:5]:
            print(f"      {path}")
        if len(paths) > 5:
            print(f"      ... 还有 {len(paths)-5} 个端点")
    
    # 统计新旧版本
    new_kg = len([r for r in kg_routes if '/kg/' in r.path or r.path == '/api/kg' or '/kg-' not in r.path])
    old_kg = len([r for r in kg_routes if 'old' in r.path or '-v' in r.path])
    
    print(f"\n3. 版本统计:")
    print(f"   ✅ 新版统一KG端点: ~{new_kg}")
    print(f"   ⚠️  旧版KG端点: ~{old_kg}")
    
    print("\n✅ 测试完成!")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
