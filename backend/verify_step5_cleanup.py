#!/usr/bin/env python3
"""验证第5步清理效果"""
import sys
sys.path.insert(0, 'src')

print("="*80)
print("✅ 验证第5步清理效果")
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
    
    # 检查v1端点
    v1_routes = [r for r in api_routes if '/v1/' in r]
    
    print(f"\n剩余v1端点:")
    print(f"   总数: {len(v1_routes)} 个")
    if len(v1_routes) > 0:
        print(f"   前10个:")
        for r in v1_routes[:10]:
            print(f"      {r}")
    
    # 统计
    print(f"\n" + "="*80)
    print(f"📊 清理效果")
    print(f"="*80)
    print(f"第4步后: 635 个端点")
    print(f"第5步后: {len(api_routes)} 个端点")
    print(f"本次减少: {635 - len(api_routes)} 个端点")
    print(f"累计减少: {793 - len(api_routes)} 个端点")
    print(f"剩余目标: {len(api_routes) - 420} 个端点")
    
    # 进度
    reduction = 793 - len(api_routes)
    progress = (reduction / 373) * 100
    print(f"完成进度: {progress:.1f}% ({reduction}/373)")
    
    # 检查是否达到目标
    if len(api_routes) <= 420:
        print(f"\n🎉🎉🎉 恭喜！已达到420个端点目标！")
    elif len(api_routes) < 500:
        print(f"\n🎉 已突破500端点大关！")
    
    if progress >= 50:
        print(f"🎉 进度已超过50%！")
    
    if len(api_routes) < 635:
        print(f"\n✅ 第5步清理成功！")
        print(f"   已删除 {635 - len(api_routes)} 个端点")
    
    # 分析剩余端点
    print(f"\n" + "="*80)
    print(f"📋 剩余端点分析")
    print(f"="*80)
    print(f"统一模块: ~138个")
    print(f"剩余v1端点: {len(v1_routes)}个")
    print(f"其他端点: {len(api_routes) - 138 - len(v1_routes)}个")
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()

