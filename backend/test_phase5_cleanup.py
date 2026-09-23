#!/usr/bin/env python3
"""测试阶段5清理后的应用"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("阶段5清理后测试")
print("="*80)

try:
    print("\n1. 尝试导入应用...")
    from app.main import app
    print("   ✅ 应用导入成功")
    
    print("\n2. 统计路由...")
    routes = list(app.routes)
    all_endpoints = [r for r in routes if hasattr(r, 'path') and hasattr(r, 'methods')]
    
    # 统一模块端点
    unified_prefixes = ['/api/kg', '/api/documents', '/api/rag', '/api/chat', 
                       '/api/analysis', '/api/projects', '/api/skills', 
                       '/api/reports', '/api/tools']
    
    unified_endpoints = [r for r in all_endpoints 
                        if any(r.path.startswith(p) for p in unified_prefixes)]
    
    # 其他端点
    other_endpoints = [r for r in all_endpoints 
                      if not any(r.path.startswith(p) for p in unified_prefixes)]
    
    print(f"\n📊 路由统计:")
    print(f"   总端点数: {len(all_endpoints)}")
    print(f"   统一模块端点: {len(unified_endpoints)}")
    print(f"   其他端点: {len(other_endpoints)}")
    
    print(f"\n📈 优化效果:")
    print(f"   起点: 894个端点")
    print(f"   当前: {len(all_endpoints)}个端点")
    print(f"   目标: 420个端点")
    print(f"   已减少: {894-len(all_endpoints)}个")
    print(f"   完成度: {(894-len(all_endpoints))/(894-420)*100:.1f}%")
    
    print(f"\n✅ 测试完成！")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
