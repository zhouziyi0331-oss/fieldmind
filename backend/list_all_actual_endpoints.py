#!/usr/bin/env python3
"""列出所有实际可访问的端点"""
import sys
sys.path.insert(0, 'src')

print("="*80)
print("📋 列出所有实际可访问的API端点")
print("="*80)

try:
    from app.main import app
    
    # 获取所有路由
    all_endpoints = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            path = route.path
            if path.startswith('/api/'):
                methods = [m for m in route.methods if m not in ['HEAD', 'OPTIONS']]
                if methods:
                    all_endpoints.append({
                        'methods': methods,
                        'path': path,
                        'name': getattr(route, 'name', ''),
                    })
    
    # 按路径分组
    from collections import defaultdict
    grouped = defaultdict(list)
    
    for ep in all_endpoints:
        # 提取模块
        parts = ep['path'].split('/')
        if len(parts) >= 3:
            module = parts[2]  # /api/MODULE/...
            grouped[module].append(ep)
    
    print(f"\n总计: {len(all_endpoints)} 个实际可访问的API端点\n")
    
    for module, endpoints in sorted(grouped.items()):
        print(f"【{module}】 ({len(endpoints)} 个端点)")
        for ep in sorted(endpoints, key=lambda x: x['path']):
            methods_str = ','.join(ep['methods'])
            print(f"  {methods_str:20s} {ep['path']}")
        print()
    
    # 统计统一模块
    unified_modules = ['kg', 'documents', 'rag', 'chat', 'analysis', 'projects', 'skills', 'reports', 'tools']
    unified_count = sum(len(grouped[m]) for m in unified_modules if m in grouped)
    
    print(f"\n统一模块端点总计: {unified_count}")
    print(f"其他端点: {len(all_endpoints) - unified_count}")
    
    print(f"\n" + "="*80)
    print("🎯 真实情况")
    print("="*80)
    print(f"实际可访问端点: {len(all_endpoints)}")
    print(f"代码中定义的端点: 131")
    print(f"差距: {131 - len(all_endpoints)}")
    
    if len(all_endpoints) < 100:
        print(f"\n❌ 严重问题: 大量端点未被正确注册!")
        print(f"   可能原因:")
        print(f"   1. 路由注册代码有问题")
        print(f"   2. 某些模块导入失败")
        print(f"   3. FastAPI配置问题")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

