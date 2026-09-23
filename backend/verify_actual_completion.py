#!/usr/bin/env python3
"""验证阶段5的实际完成情况"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("阶段5实际完成情况验证")
print("="*80)

try:
    from app.main import app
    
    # 获取所有路由
    routes = [r for r in app.routes if hasattr(r, 'path') and hasattr(r, 'methods')]
    
    print(f"\n📊 当前系统状态:")
    print(f"   总路由数: {len(routes)}")
    
    # 分类统计
    unified_routes = [r for r in routes if any(p in r.path for p in ['/api/kg', '/api/documents', '/api/rag', '/api/chat', '/api/analysis', '/api/projects', '/api/skills', '/api/reports', '/api/tools'])]
    old_routes = [r for r in routes if '-old' in r.path or 'v1' in r.path]
    other_routes = [r for r in routes if r not in unified_routes and r not in old_routes]
    
    print(f"   统一模块路由: {len(unified_routes)}")
    print(f"   旧版/v1路由: {len(old_routes)}")
    print(f"   其他路由: {len(other_routes)}")
    
    print(f"\n❌ 问题分析:")
    print(f"   1. 统一模块只有 {len(unified_routes)} 个路由")
    print(f"   2. 还有 {len(old_routes)} 个旧版路由存在")
    print(f"   3. 统一模块可能只是空壳，没有实际业务逻辑")
    
    # 检查统一模块是否有实际端点
    print(f"\n🔍 检查统一模块实际端点:")
    for prefix in ['/api/kg', '/api/documents', '/api/rag', '/api/chat', '/api/analysis', '/api/projects', '/api/skills', '/api/reports', '/api/tools']:
        module_routes = [r for r in routes if r.path.startswith(prefix)]
        print(f"   {prefix}: {len(module_routes)} 个端点")
        if len(module_routes) > 0:
            for r in module_routes[:3]:  # 只显示前3个
                methods = ','.join(r.methods) if hasattr(r, 'methods') else 'N/A'
                print(f"      - {methods} {r.path}")
    
    print(f"\n⚠️  实际情况:")
    print(f"   ✗ 旧模块文件已删除")
    print(f"   ✗ 但统一模块可能只是框架，没有实际业务逻辑")
    print(f"   ✗ 真实的业务端点数量很少")
    print(f"   ✗ 需要将旧模块的业务逻辑迁移到统一模块中")
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()

