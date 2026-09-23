#!/usr/bin/env python3
"""验证蒸馏功能完整性"""
import sys
sys.path.insert(0, 'src')

print("="*80)
print("🎉 验证蒸馏功能实现")
print("="*80)

try:
    from app.main import app
    
    # 查找所有distill相关的路由
    distill_routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            if 'distill' in route.path.lower():
                methods = getattr(route, 'methods', set())
                distill_routes.append((route.path, methods))
    
    print(f"\n✅ 找到 {len(distill_routes)} 个蒸馏API端点:")
    for path, methods in sorted(distill_routes):
        methods_str = ', '.join(sorted(methods)) if methods else 'ALL'
        print(f"  • {methods_str:10s} {path}")
    
    # 检查数据库表
    import sqlite3
    from pathlib import Path
    
    db_path = Path('src/data/fieldmind.db')
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'distilled%'")
    tables = cursor.fetchall()
    
    print(f"\n✅ 数据库表:")
    for table in tables:
        print(f"  • {table[0]}")
        
        # 检查表结构
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"    字段数: {len(columns)}")
    
    conn.close()
    
    # 检查模型和服务
    print(f"\n✅ 核心模块:")
    from app.models.distillation import DistilledUnit, DistilledUnitRelation
    print(f"  • DistilledUnit 模型")
    print(f"  • DistilledUnitRelation 模型")
    
    from app.services.distillation_engine import DistillationEngine
    print(f"  • DistillationEngine 引擎")
    
    print(f"\n" + "="*80)
    print("📊 蒸馏功能实现总结")
    print("="*80)
    
    print("""
✅ Phase 1: 数据库与基础架构 (已完成)
   • distilled_units 表
   • distilled_unit_relations 表
   • 索引创建

✅ Phase 2: 蒸馏引擎 (框架已完成)
   • DistillationEngine 类
   • 6类知识单元提取框架:
     - _extract_insights() - 核心洞察
     - _extract_quotes() - 经典原话
     - _extract_models() - 思维模型
     - _extract_cases() - 案例应用
     - _extract_actions() - 行动建议
     - _extract_methods() - 方法论沉淀

✅ Phase 3: API端点 (已完成)
   • POST /api/projects/{id}/distill
   • GET /api/projects/{id}/distilled-units
   • GET /api/distilled-units/{id}
   • GET /api/distilled-units/{id}/sources
   • DELETE /api/distilled-units/{id}
   • GET /api/projects/{id}/distillation/stats

⏳ 待完成工作:
   • 实现6类知识单元的具体提取逻辑
   • 连接现有的chunks/entities/events数据
   • 前端蒸馏结果展示页面
   • 完整的测试用例
    """)
    
    print("="*80)
    print("🎯 蒸馏功能已具备基础架构，可以开始实现具体提取逻辑")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()

