#!/usr/bin/env python3
"""正确统计FastAPI端点"""
import sys
sys.path.insert(0, 'src')

print("="*80)
print("正确统计FastAPI端点数量")
print("="*80)

try:
    from app.main import app
    
    # 方法1: 直接统计routes
    print("\n方法1: 统计app.routes")
    all_routes = list(app.routes)
    print(f"  总routes数: {len(all_routes)}")
    
    # 方法2: 统计router中的routes
    print("\n方法2: 统计app.router.routes")
    if hasattr(app, 'router'):
        router_routes = list(app.router.routes)
        print(f"  router.routes数: {len(router_routes)}")
        
        # 统计API路由
        api_routes = []
        for route in router_routes:
            if hasattr(route, 'path'):
                path = route.path
                if path.startswith('/api/'):
                    if hasattr(route, 'methods'):
                        api_routes.append(route)
        
        print(f"  API routes数: {len(api_routes)}")
        
        # 按prefix分组
        from collections import defaultdict
        grouped = defaultdict(list)
        
        for route in api_routes:
            path = route.path
            parts = path.split('/')
            if len(parts) >= 3:
                prefix = parts[2]  # /api/PREFIX/...
                grouped[prefix].append(route)
        
        print(f"\n按模块分组:")
        for prefix, routes in sorted(grouped.items()):
            print(f"  {prefix:20s} {len(routes):3d} 个端点")
        
        print(f"\n总计API端点: {len(api_routes)}")
        
        # 检查统一模块
        unified_prefixes = ['kg', 'documents', 'rag', 'chat', 'analysis', 'projects', 'skills', 'reports', 'tools']
        unified_total = sum(len(grouped.get(p, [])) for p in unified_prefixes)
        print(f"统一模块端点: {unified_total}")
        
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

