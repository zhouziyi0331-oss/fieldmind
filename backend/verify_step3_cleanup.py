#!/usr/bin/env python3
"""验证第3步清理效果"""
import sys
sys.path.insert(0, 'src')

print("="*80)
print("✅ 验证第3步清理效果")
print("="*80)

try:
    from app.main import app
    
    def get_all_routes_from_app(app):
        """获取所有路由"""
        all_routes = []
        
        for route in app.router.routes:
            route_type = type(route).__name__
            
            if route_type == '_IncludedRouter':
                if hasattr(route, 'original_router'):
                    original = route.original_router
                    prefix_from_context = ''
                    if hasattr(route, 'include_context'):
                        prefix_from_context = route.include_context.prefix
                    
                    for subroute in original.routes:
                        if hasattr(subroute, 'path'):
                            full_path = prefix_from_context + subroute.path
                            all_routes.append(full_path)
            
            elif hasattr(route, 'path'):
                all_routes.append(route.path)
        
        return all_routes
    
    # 获取所有路由
    all_routes = get_all_routes_from_app(app)
    api_routes = [r for r in all_routes if '/api/' in r]
    
    print(f"\n✅ 应用成功启动")
    
    # 检查已删除的模块
    deleted_modules = [
        'distillation',
        'hermes',
        'lineage',
        'feeding',
        'api_management',
        'annotation',
        'tagging',
        'sop'
    ]
    
    deleted_found = {}
    for module in deleted_modules:
        matches = [r for r in api_routes if f'/v1/{module}' in r or f'/{module}/' in r]
        if matches:
            deleted_found[module] = matches
    
    print(f"\n检查已删除的模块:")
    if deleted_found:
        print(f"   ⚠️  发现应该被删除的端点仍然存在:")
        for module, routes in deleted_found.items():
            print(f"      {module}: {len(routes)} 个端点")
    else:
        print(f"   ✅ 确认所有目标模块端点已删除")
    
    # 统计
    print(f"\n" + "="*80)
    print(f"📊 清理效果")
    print(f"="*80)
    print(f"第2步后: 761 个端点")
    print(f"第3步后: {len(api_routes)} 个端点")
    print(f"本次减少: {761 - len(api_routes)} 个端点")
    print(f"累计减少: {793 - len(api_routes)} 个端点")
    print(f"剩余目标: {len(api_routes) - 420} 个端点")
    
    # 进度
    reduction = 793 - len(api_routes)
    progress = (reduction / 373) * 100
    print(f"完成进度: {progress:.1f}% ({reduction}/373)")
    
    if len(api_routes) < 761:
        print(f"\n✅ 第3步清理成功！")
        print(f"   已删除 {761 - len(api_routes)} 个端点")
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()

