#!/usr/bin/env python3
"""测试统一RAG模块"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("测试统一RAG模块")
print("="*80)

try:
    print("\n1. 导入应用...")
    from app.main import app
    print("   ✅ 应用导入成功")
    
    print("\n2. 检查统一RAG路由...")
    routes = list(app.routes)
    
    # 查找 /api/rag 开头的路由
    rag_routes = [r for r in routes if hasattr(r, 'path') and r.path.startswith('/api/rag')]
    
    print(f"   找到 {len(rag_routes)} 个RAG相关路由")
    
    # 显示新版端点
    if rag_routes:
        print(f"\n3. 统一RAG端点:")
        for route in rag_routes[:15]:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                methods = ','.join(route.methods) if route.methods else 'ANY'
                print(f"      {methods:15} {route.path}")
        if len(rag_routes) > 15:
            print(f"      ... 还有 {len(rag_routes)-15} 个端点")
    
    print("\n✅ 测试完成!")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
