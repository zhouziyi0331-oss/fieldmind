#!/usr/bin/env python3
"""调试routes的详细信息"""
import sys
sys.path.insert(0, 'src')

from app.api import unified_knowledge_graph

print("="*80)
print("调试统一知识图谱router的routes详情")
print("="*80)

router = unified_knowledge_graph.router

print(f"\nrouter.routes数量: {len(router.routes)}")
print(f"router.prefix: {router.prefix}")

print("\n前5个routes的详细信息:")
for i, route in enumerate(router.routes[:5]):
    print(f"\n第{i+1}个route:")
    print(f"  类型: {type(route)}")
    print(f"  对象: {route}")
    
    if hasattr(route, 'path'):
        print(f"  path: {route.path}")
    else:
        print(f"  ❌ 没有path属性!")
        
    if hasattr(route, 'methods'):
        print(f"  methods: {route.methods}")
    else:
        print(f"  ❌ 没有methods属性!")
        
    if hasattr(route, 'endpoint'):
        print(f"  endpoint: {route.endpoint}")
    
    # 列出所有属性
    attrs = [a for a in dir(route) if not a.startswith('_')]
    print(f"  属性: {', '.join(attrs[:10])}")

print("\n" + "="*80)
print("可能的问题:")
print("="*80)
print("如果route对象不是APIRoute类型，FastAPI可能无法识别")

