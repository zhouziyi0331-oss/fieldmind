#!/usr/bin/env python3
"""系统性验证所有9个统一模块"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from module_comparison_framework import extract_endpoints, compare_modules, print_comparison_report

# 定义所有9个模块的对应关系
modules_mapping = [
    {
        'name': '知识图谱',
        'unified': 'src/app/api/unified_knowledge_graph.py',
        'old': [
            'archive/old_modules/knowledge_graph.py',
            'archive/old_modules/knowledge_graph_v3.py',
        ]
    },
    {
        'name': '文档处理',
        'unified': 'src/app/api/unified_documents.py',
        'old': [
            'archive/old_modules/documents.py',
            'archive/old_modules/document_processing.py',
        ]
    },
    {
        'name': 'RAG检索',
        'unified': 'src/app/api/unified_rag.py',
        'old': [
            'archive/old_modules/rag.py',
            'archive/old_modules/deep_rag.py',
            'archive/old_modules/chat_rag.py',
            'archive/old_modules/rag_p3.py',
            'archive/old_modules/hierarchical_retrieval.py',
        ]
    },
    {
        'name': '聊天对话',
        'unified': 'src/app/api/unified_chat.py',
        'old': [
            'archive/old_modules/chat.py',
            'archive/old_modules/enhanced_chat.py',
            'archive/old_modules/conversation.py',
            'archive/old_modules/conversation_memory.py',
            'archive/old_modules/project_chat.py',
        ]
    },
    {
        'name': '分析',
        'unified': 'src/app/api/unified_analysis.py',
        'old': [
            'archive/old_modules/creative_analysis.py',
            'archive/old_modules/business_analysis.py',
            'archive/old_modules/analytics.py',
        ]
    },
    {
        'name': '项目管理',
        'unified': 'src/app/api/unified_projects.py',
        'old': [
            'archive/old_modules/projects.py',
            'archive/old_modules/project_documents.py',
        ]
    },
    {
        'name': '技能管理',
        'unified': 'src/app/api/unified_skills.py',
        'old': [
            'archive/old_modules/skills.py',
            'archive/old_modules/skill_generation.py',
            'archive/old_modules/skill_optimization.py',
        ]
    },
    {
        'name': '报告生成',
        'unified': 'src/app/api/unified_reports.py',
        'old': [
            'archive/old_modules/reports.py',
        ]
    },
    {
        'name': '工具',
        'unified': 'src/app/api/unified_tools.py',
        'old': [
            'archive/old_modules/ocr.py',
            'archive/old_modules/export_summaries.py',
        ]
    },
]

print("="*80)
print("🔍 系统性验证所有统一模块")
print("="*80)

total_old_endpoints = 0
total_unified_endpoints = 0
total_missing = 0
total_matched = 0

summary = []

for i, mapping in enumerate(modules_mapping, 1):
    print(f"\n{'='*80}")
    print(f"模块 {i}/9: {mapping['name']}")
    print('='*80)
    
    unified_module = Path(mapping['unified'])
    old_modules = [Path(p) for p in mapping['old']]
    
    # 执行对比
    result = compare_modules(old_modules, unified_module)
    
    # 简化输出
    print(f"\n📦 旧模块: {', '.join([p.name for p in old_modules])}")
    print(f"📈 端点统计:")
    print(f"   旧模块端点: {len(result['old_endpoints'])}")
    print(f"   统一模块端点: {len(result['unified_endpoints'])}")
    print(f"   匹配端点: {len(result['matched_endpoints'])}")
    print(f"   缺失端点: {len(result['missing_endpoints'])}")
    
    if result['missing_endpoints']:
        print(f"\n⚠️  缺失的端点:")
        for ep in result['missing_endpoints'][:5]:  # 只显示前5个
            print(f"   ❌ {ep.method} {ep.path}")
        if len(result['missing_endpoints']) > 5:
            print(f"   ... 还有 {len(result['missing_endpoints']) - 5} 个")
    
    # 计算覆盖率
    coverage = 0
    if len(result['old_endpoints']) > 0:
        coverage = (len(result['matched_endpoints']) / len(result['old_endpoints'])) * 100
    
    status = "✅" if coverage >= 80 else "⚠️" if coverage >= 50 else "❌"
    print(f"\n{status} 覆盖率: {coverage:.1f}%")
    
    # 累计统计
    total_old_endpoints += len(result['old_endpoints'])
    total_unified_endpoints += len(result['unified_endpoints'])
    total_missing += len(result['missing_endpoints'])
    total_matched += len(result['matched_endpoints'])
    
    summary.append({
        'name': mapping['name'],
        'old': len(result['old_endpoints']),
        'unified': len(result['unified_endpoints']),
        'matched': len(result['matched_endpoints']),
        'missing': len(result['missing_endpoints']),
        'coverage': coverage,
        'status': status
    })

# 打印总结
print("\n" + "="*80)
print("📊 验证总结")
print("="*80)

print(f"\n{'模块':<12} {'旧端点':<8} {'新端点':<8} {'匹配':<6} {'缺失':<6} {'覆盖率':<8} {'状态':<4}")
print("-" * 80)
for s in summary:
    print(f"{s['name']:<12} {s['old']:<8} {s['unified']:<8} {s['matched']:<6} {s['missing']:<6} {s['coverage']:<7.1f}% {s['status']:<4}")

print("-" * 80)
print(f"{'总计':<12} {total_old_endpoints:<8} {total_unified_endpoints:<8} {total_matched:<6} {total_missing:<6}")

overall_coverage = (total_matched / total_old_endpoints * 100) if total_old_endpoints > 0 else 0
print(f"\n整体覆盖率: {overall_coverage:.1f}%")

if overall_coverage >= 80:
    print("✅ 整体状态: 优秀")
elif overall_coverage >= 60:
    print("⚠️  整体状态: 良好，需要补充部分功能")
else:
    print("❌ 整体状态: 需要大量补充")

print("\n" + "="*80)
print("🎯 下一步行动")
print("="*80)

needs_work = [s for s in summary if s['missing'] > 0]
if needs_work:
    print(f"\n需要补充功能的模块 ({len(needs_work)}个):")
    for s in needs_work:
        print(f"   {s['status']} {s['name']}: 缺失 {s['missing']} 个端点")
else:
    print("\n✅ 所有模块验证完成！")

