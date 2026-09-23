#!/usr/bin/env python3
"""验证第2步清理效果"""
import sys
sys.path.insert(0, 'src')

print("="*80)
print("✅ 验证第2步清理效果")
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
    
    # 检查v1/workflows端点
    workflows_routes = [r for r in api_routes if '/api/v1/workflows' in r]
    
    if workflows_routes:
        print(f"\n⚠️  发现 {len(workflows_routes)} 个v1/workflows端点仍然存在")
        for r in workflows_routes[:5]:
            print(f"   {r}")
    else:
        print(f"\n✅ 确认v1/workflows端点已删除")
    
    # 统计
    print(f"\n" + "="*80)
    print(f"📊 清理效果")
    print(f"="*80)
    print(f"第1步后: 774 个端点")
    print(f"第2步后: {len(api_routes)} 个端点")
    print(f"本次减少: {774 - len(api_routes)} 个端点")
    print(f"累计减少: {793 - len(api_routes)} 个端点")
    print(f"剩余目标: {len(api_routes) - 420} 个端点")
    
    if len(api_routes) < 774:
        print(f"\n✅ 第2步清理成功！")
        print(f"   已删除 {774 - len(api_routes)} 个v1/workflows端点")
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()

