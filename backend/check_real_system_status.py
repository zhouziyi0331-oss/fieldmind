#!/usr/bin/env python3
"""检查系统的真实状态"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🔍 检查系统真实状态")
print("="*80)

try:
    from app.main import app
    from collections import defaultdict
    
    # 获取所有路由
    all_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            for method in route.methods:
                if method not in ['HEAD', 'OPTIONS']:
                    all_routes.append({
                        'method': method,
                        'path': route.path,
                        'name': route.name if hasattr(route, 'name') else 'unknown'
                    })
    
    print(f"\n📊 当前系统端点统计:")
    print(f"   总端点数: {len(all_routes)}")
    
    # 按路径前缀分类
    prefix_counts = defaultdict(int)
    for route in all_routes:
        path = route['path']
        if path.startswith('/api/'):
            parts = path.split('/')
            if len(parts) >= 3:
                prefix = '/' + '/'.join(parts[1:3])
                prefix_counts[prefix] += 1
    
    print(f"\n📋 按API前缀分类:")
    for prefix, count in sorted(prefix_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {prefix:40s} {count:3d} 端点")
    
    print(f"\n🎯 原始目标回顾:")
    print(f"   起点: 894个端点")
    print(f"   目标: 420个端点 (减少50%)")
    print(f"   当前: {len(all_routes)}个端点")
    
    if len(all_routes) > 420:
        reduction_needed = len(all_routes) - 420
        print(f"\n⚠️  问题:")
        print(f"   还需要减少: {reduction_needed}个端点")
        print(f"   当前仅减少: {894 - len(all_routes)}个端点")
        print(f"   完成度: {(894 - len(all_routes)) / (894 - 420) * 100:.1f}%")
    else:
        print(f"\n✅ 已达到目标!")
    
    # 检查未注册模块
    print(f"\n🔍 检查API模块文件:")
    from pathlib import Path
    
    api_dir = Path("src/app/api")
    api_files = list(api_dir.glob("*.py"))
    v1_files = list(api_dir.glob("v1/*.py"))
    
    print(f"   API目录文件数: {len(api_files)}")
    print(f"   v1目录文件数: {len(v1_files)}")
    print(f"   总API模块: {len(api_files) + len(v1_files)}")
    
    # 统计统一模块
    unified_files = [f for f in api_files if 'unified_' in f.name]
    print(f"\n✨ 统一模块: {len(unified_files)}个")
    for f in unified_files:
        print(f"   - {f.name}")
    
    print(f"\n❓ 真实情况评估:")
    print(f"   1. 端点数量: {len(all_routes)} (目标420)")
    print(f"   2. 是否达标: {'❌ 未达标' if len(all_routes) > 420 else '✅ 达标'}")
    print(f"   3. 覆盖率: 需要检查main.py中的实际注册情况")
    
except Exception as e:
    print(f"\n❌ 检查失败: {e}")
    import traceback
    traceback.print_exc()

