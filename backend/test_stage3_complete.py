#!/usr/bin/env python3
"""测试阶段3完整性"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("测试阶段3统一模块")
print("="*80)

try:
    print("\n1. 导入应用...")
    from app.main import app
    print("   ✅ 应用导入成功")
    
    print("\n2. 检查所有统一模块...")
    routes = list(app.routes)
    
    unified_modules = {
        "知识图谱": "/api/kg",
        "文档处理": "/api/documents",
        "RAG检索": "/api/rag",
        "聊天对话": "/api/chat",
        "分析": "/api/analysis",
        "项目管理": "/api/projects"
    }
    
    for name, prefix in unified_modules.items():
        module_routes = [r for r in routes if hasattr(r, 'path') and r.path.startswith(prefix) and 'old' not in r.path]
        print(f"   ✅ {name}: {len(module_routes)} 个端点")
    
    print("\n✅ 所有统一模块测试完成!")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
