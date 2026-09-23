#!/usr/bin/env python3
"""验证第1步清理效果"""
import sys
sys.path.insert(0, 'src')

print("="*80)
print("✅ 验证第1步清理效果")
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
                            all_routes.append({
                                'path': full_path,
                                'methods': list(subroute.methods) if hasattr(subroute, 'methods') else [],
                            })
            
            elif hasattr(route, 'path'):
                all_routes.append({
                    'path': route.path,
                    'methods': list(route.methods) if hasattr(route, 'methods') else [],
                })
        
        return all_routes
    
    # 获取所有路由
    all_routes = get_all_routes_from_app(app)
    api_routes = [r for r in all_routes if '/api/' in r['path']]
    
    print(f"\n✅ 应用成功启动")
    print(f"   总API端点数: {len(api_routes)}")
    
    # 检查已删除的端点
    deleted_patterns = [
        '/api/v1/chat-enhancement',
        '/api/v1/analysis',
        '/api/v1/topic-analysis'
    ]
    
    found_deleted = []
    for pattern in deleted_patterns:
        matches = [r for r in api_routes if pattern in r['path']]
        if matches:
            found_deleted.extend(matches)
    
    print(f"\n检查已删除的端点:")
    if found_deleted:
        print(f"   ⚠️  发现 {len(found_deleted)} 个应该被删除的端点仍然存在:")
        for r in found_deleted[:5]:
            methods = ','.join(r['methods'])
            print(f"      {methods:15s} {r['path']}")
    else:
        print(f"   ✅ 确认所有目标端点已删除")
    
    # 统计统一模块端点
    unified_count = len([r for r in api_routes if any(p in r['path'] for p in [
        '/api/kg', '/api/documents', '/api/rag', '/api/chat',
        '/api/analysis', '/api/projects', '/api/skills', '/api/reports', '/api/tools'
    ])])
    
    print(f"\n统一模块端点: {unified_count} 个")
    print(f"其他端点: {len(api_routes) - unified_count} 个")
    
    # 对比清理前后
    print(f"\n" + "="*80)
    print(f"📊 清理效果")
    print(f"="*80)
    print(f"清理前: 793 个端点")
    print(f"清理后: {len(api_routes)} 个端点")
    print(f"减少: {793 - len(api_routes)} 个端点")
    
    if len(api_routes) < 793:
        print(f"\n✅ 第1步清理成功！")
        print(f"   已删除 {793 - len(api_routes)} 个重复的v1端点")
    else:
        print(f"\n⚠️  端点数量未减少，可能需要检查")
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()

