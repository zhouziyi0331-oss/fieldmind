#!/usr/bin/env python3
"""检查统一模块的实际实现情况"""
from pathlib import Path

print("="*80)
print("统一模块实现情况检查")
print("="*80)

unified_modules = [
    "src/app/api/unified_knowledge_graph.py",
    "src/app/api/unified_documents.py",
    "src/app/api/unified_rag.py",
    "src/app/api/unified_chat.py",
    "src/app/api/unified_analysis.py",
    "src/app/api/unified_projects.py",
    "src/app/api/unified_skills.py",
    "src/app/api/unified_reports.py",
    "src/app/api/unified_tools.py",
]

print("\n📋 检查每个统一模块:")
for module_path in unified_modules:
    path = Path(module_path)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # 统计
            total_lines = len(lines)
            route_count = content.count('@router.')
            has_business_logic = 'def ' in content and route_count > 0
            has_TODO = 'TODO' in content or '待实现' in content
            
            print(f"\n✓ {path.name}")
            print(f"   代码行数: {total_lines}")
            print(f"   端点数量: {route_count}")
            print(f"   业务逻辑: {'✓' if has_business_logic else '✗'}")
            print(f"   待实现: {'✗' if has_TODO else '✓'}")
            
            # 检查是否只是占位符
            if total_lines < 100:
                print(f"   ⚠️  代码量较少，可能只是框架")
            
            # 检查是否有实际的数据库操作
            has_db_ops = 'db.query' in content or 'db.add' in content
            print(f"   数据库操作: {'✓' if has_db_ops else '✗'}")
    else:
        print(f"\n✗ {path.name} - 文件不存在")

print("\n" + "="*80)
print("结论:")
print("="*80)
print("如果统一模块只有框架而没有实际业务逻辑，")
print("那么阶段5确实没有完成：")
print("  1. ✗ 旧模块的业务逻辑未迁移到统一模块")
print("  2. ✗ 统一模块只是空壳")
print("  3. ✗ 需要将备份的旧模块逻辑迁移过来")

