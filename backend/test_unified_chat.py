#!/usr/bin/env python3
"""测试统一聊天对话模块"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("测试统一聊天对话模块")
print("="*80)

try:
    print("\n1. 导入应用...")
    from app.main import app
    print("   ✅ 应用导入成功")
    
    print("\n2. 检查统一聊天对话路由...")
    routes = list(app.routes)
    
    # 查找 /api/chat 开头的路由
    chat_routes = [r for r in routes if hasattr(r, 'path') and r.path.startswith('/api/chat')]
    
    print(f"   找到 {len(chat_routes)} 个聊天相关路由")
    
    # 分组统计
    new_chat = [r for r in chat_routes if hasattr(r, 'path') and r.path.startswith('/api/chat') and 'old' not in r.path]
    old_chat = [r for r in chat_routes if hasattr(r, 'path') and 'old' in r.path]
    
    print(f"\n3. 版本统计:")
    print(f"   ✅ 新版统一聊天端点: {len(new_chat)}")
    print(f"   ⚠️  旧版聊天端点: {len(old_chat)}")
    
    # 显示新版端点
    if new_chat:
        print(f"\n4. 新版统一聊天端点示例:")
        for route in new_chat[:10]:
            if hasattr(route, 'methods'):
                methods = ','.join(route.methods) if route.methods else 'ANY'
                print(f"      {methods:15} {route.path}")
        if len(new_chat) > 10:
            print(f"      ... 还有 {len(new_chat)-10} 个端点")
    
    print("\n✅ 测试完成!")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
