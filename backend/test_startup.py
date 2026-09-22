#!/usr/bin/env python3
"""测试服务器启动和新API注册"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("测试服务器启动和API注册")
print("="*80)

try:
    print("\n1. 导入FastAPI应用...")
    from app.main import app
    print("   ✅ 应用导入成功")
    
    print("\n2. 统计注册的路由...")
    routes = list(app.routes)
    print(f"   ✅ 总路由数: {len(routes)}")
    
    # 检查新注册的API
    print("\n3. 检查新注册的API端点...")
    new_apis = {
        "/api/memory": "记忆管理",
        "/api/timeline": "时间线",
        "/api/tables": "表格处理",
        "/api/proposal": "方案生成",
        "/api/photos": "图片管理",
        "/api/v1/super-agents": "超级Agent",
        "/api/agent-pipeline": "Agent流水线",
        "/api/v1/tasks": "任务管理",
        "/api/v1/topic-analysis": "主题分析",
        "/api/v1/sop": "标准作业程序",
        "/api/v1/chunks-quantification": "块量化",
        "/api/v1/dashboard-optimized": "优化Dashboard",
        "/api/export": "导出摘要",
        "/api/file-summaries": "文件摘要",
        "/api/quantification": "数据量化",
        "/api/websocket": "WebSocket通信",
        "/api/monitoring": "系统监控",
    }
    
    found_count = 0
    missing = []
    
    # 获取所有路径
    all_paths = set()
    for route in routes:
        if hasattr(route, 'path'):
            all_paths.add(route.path)
    
    for prefix, name in new_apis.items():
        # 检查是否有以该前缀开头的路由
        found = any(path.startswith(prefix) for path in all_paths)
        if found:
            print(f"   ✅ {name:20} - {prefix}")
            found_count += 1
        else:
            print(f"   ❌ {name:20} - {prefix}")
            missing.append(name)
    
    print(f"\n结果:")
    print(f"   ✅ 成功注册: {found_count}/{len(new_apis)}")
    print(f"   ❌ 未找到: {len(missing)}")
    
    if missing:
        print(f"\n未找到的模块:")
        for m in missing:
            print(f"      - {m}")
    
    print("\n✅ 阶段1测试完成!")
    
except Exception as e:
    print(f"\n❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
