#!/usr/bin/env python3
"""深度分析系统真实状态"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🔍 深度分析系统真实状态")
print("="*80)

# 1. 检查路由数量的矛盾
print("\n❓ 发现的矛盾:")
print("   日志显示: '最终路由数: 111'")
print("   但实际统计: 只有16个端点")
print("   原因: FastAPI的routes包含了很多元数据路由")

# 2. 统计实际的API端点
try:
    from app.main import app
    
    api_routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            path = route.path
            # 只统计API路由
            if path.startswith('/api/'):
                for method in route.methods:
                    if method not in ['HEAD', 'OPTIONS']:
                        api_routes.append({
                            'method': method,
                            'path': path,
                        })
    
    print(f"\n📊 实际API端点统计:")
    print(f"   真实API端点数: {len(api_routes)}")
    
    # 按模块分类
    from collections import defaultdict
    module_routes = defaultdict(list)
    
    for route in api_routes:
        path = route['path']
        # 提取模块名
        if '/api/kg' in path:
            module_routes['统一知识图谱'].append(route)
        elif '/api/documents' in path:
            module_routes['统一文档处理'].append(route)
        elif '/api/rag' in path:
            module_routes['统一RAG'].append(route)
        elif '/api/chat' in path:
            module_routes['统一聊天'].append(route)
        elif '/api/analysis' in path:
            module_routes['统一分析'].append(route)
        elif '/api/projects' in path:
            module_routes['统一项目'].append(route)
        elif '/api/skills' in path:
            module_routes['统一技能'].append(route)
        elif '/api/reports' in path:
            module_routes['统一报告'].append(route)
        elif '/api/tools' in path:
            module_routes['统一工具'].append(route)
        else:
            module_routes['其他API'].append(route)
    
    print(f"\n📋 按统一模块分类:")
    total_unified = 0
    for module, routes in sorted(module_routes.items()):
        if '统一' in module:
            print(f"   {module:20s} {len(routes):3d} 端点")
            total_unified += len(routes)
    
    print(f"\n   统一模块总计:         {total_unified:3d} 端点")
    
    other_count = len(module_routes.get('其他API', []))
    print(f"   其他API:              {other_count:3d} 端点")
    
    # 3. 检查main.py中注册的模块
    print(f"\n🔍 检查main.py中的路由注册:")
    
    with open('src/app/main.py', 'r') as f:
        content = f.read()
    
    # 统计注册语句
    import re
    
    # 统计各种注册
    include_router_count = len(re.findall(r'app\.include_router', content))
    unified_count = len(re.findall(r'unified_\w+\.router', content))
    
    print(f"   总注册语句数: {include_router_count}")
    print(f"   统一模块注册: {unified_count}")
    
    # 4. 真实问题诊断
    print(f"\n" + "="*80)
    print("💡 真实问题诊断")
    print("="*80)
    
    print(f"\n问题1: 统一模块路由未实际工作")
    print(f"   预期: 9个统一模块，每个10-20个端点 = 90-180个端点")
    print(f"   实际: 只有{total_unified}个统一模块端点")
    print(f"   原因: 统一模块的router可能没有正确注册或端点定义有问题")
    
    print(f"\n问题2: API端点数量严重不足")
    print(f"   目标: 420个端点")
    print(f"   实际: {len(api_routes)}个端点")
    print(f"   差距: {420 - len(api_routes)}个端点")
    
    print(f"\n问题3: 旧模块虽然删除但功能未真正迁移")
    print(f"   删除了: 25个旧模块文件")
    print(f"   但: 统一模块中的端点数量远远不足")
    print(f"   结论: 端点声明存在但可能没有被正确识别")
    
    # 5. 检查统一模块的router定义
    print(f"\n" + "="*80)
    print("🔍 检查统一模块的router定义")
    print("="*80)
    
    from pathlib import Path
    
    unified_files = [
        'src/app/api/unified_knowledge_graph.py',
        'src/app/api/unified_documents.py',
        'src/app/api/unified_rag.py',
        'src/app/api/unified_chat.py',
        'src/app/api/unified_analysis.py',
        'src/app/api/unified_projects.py',
        'src/app/api/unified_skills.py',
        'src/app/api/unified_reports.py',
        'src/app/api/unified_tools.py',
    ]
    
    print(f"\n检查各统一模块的@router装饰器数量:")
    total_decorators = 0
    for file_path in unified_files:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                content = f.read()
                decorator_count = content.count('@router.')
                total_decorators += decorator_count
                module_name = Path(file_path).stem
                print(f"   {module_name:30s} {decorator_count:3d} 个@router装饰器")
    
    print(f"\n   总计:                           {total_decorators:3d} 个端点定义")
    
    print(f"\n❌ 发现的核心问题:")
    print(f"   1. 代码中定义了{total_decorators}个端点")
    print(f"   2. 但FastAPI只识别到{len(api_routes)}个端点")
    print(f"   3. 差距: {total_decorators - len(api_routes)}个端点未被识别")
    
    print(f"\n可能的原因:")
    print(f"   - 统一模块的router prefix设置有问题")
    print(f"   - main.py中注册时的prefix冲突")
    print(f"   - 某些端点有语法错误导致未加载")
    print(f"   - FastAPI的路由聚合机制问题")

except Exception as e:
    print(f"\n❌ 分析失败: {e}")
    import traceback
    traceback.print_exc()

