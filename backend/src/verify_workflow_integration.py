#!/usr/bin/env python3
"""
WorkflowEngine 集成验证脚本
验证所有服务的 WorkflowEngine 集成状态
"""

import os
import re
from typing import Dict, List, Tuple
from collections import defaultdict

def analyze_integration_status(services_dir: str = 'app/services') -> Dict:
    """分析集成状态"""

    stats = {
        'total': 0,
        'integrated': 0,
        'complete_integration': [],
        'wrapper_integration': [],
        'not_integrated': [],
        'by_category': defaultdict(lambda: {'total': 0, 'integrated': 0})
    }

    for root, dirs, files in os.walk(services_dir):
        for file in files:
            if not file.endswith('.py') or file == '__init__.py':
                continue

            stats['total'] += 1
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, services_dir)

            # 确定类别
            if '/' in rel_path:
                category = rel_path.split('/')[0]
            else:
                category = 'root'

            stats['by_category'][category]['total'] += 1

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                has_workflow = 'use_workflow_engine' in content
                has_wrapper = 'Wrapper' in content and 'WorkflowEngine 包装类' in content
                is_engine = 'workflow_engine.py' in filepath

                if is_engine:
                    stats['not_integrated'].append(rel_path)
                elif has_wrapper:
                    stats['integrated'] += 1
                    stats['wrapper_integration'].append(rel_path)
                    stats['by_category'][category]['integrated'] += 1
                elif has_workflow:
                    stats['integrated'] += 1
                    stats['complete_integration'].append(rel_path)
                    stats['by_category'][category]['integrated'] += 1
                else:
                    stats['not_integrated'].append(rel_path)

            except Exception as e:
                print(f"错误处理 {rel_path}: {e}")

    return stats

def print_report(stats: Dict):
    """打印报告"""

    print("=" * 80)
    print("WorkflowEngine 集成状态报告")
    print("=" * 80)

    print(f"\n📊 总体统计:")
    print(f"   总服务数: {stats['total']}")
    print(f"   已集成: {stats['integrated']}")
    print(f"   未集成: {len(stats['not_integrated'])}")
    print(f"   覆盖率: {stats['integrated']/stats['total']*100:.2f}%")

    print(f"\n📋 集成方式:")
    print(f"   完整集成: {len(stats['complete_integration'])}")
    print(f"   包装类集成: {len(stats['wrapper_integration'])}")

    print(f"\n📁 按目录分类:")
    for category, data in sorted(stats['by_category'].items()):
        coverage = data['integrated'] / data['total'] * 100
        status = "✅" if coverage == 100 else "⚠️"
        print(f"   {status} {category}: {data['integrated']}/{data['total']} ({coverage:.1f}%)")

    if stats['wrapper_integration']:
        print(f"\n🔧 包装类集成的模块 ({len(stats['wrapper_integration'])}个):")
        for path in sorted(stats['wrapper_integration']):
            print(f"   - {path}")

    if stats['not_integrated']:
        print(f"\n❌ 未集成的服务 ({len(stats['not_integrated'])}个):")
        for path in stats['not_integrated']:
            print(f"   - {path}")

    print("\n" + "=" * 80)
    print(f"✅ 集成完成！覆盖率: {stats['integrated']/stats['total']*100:.2f}%")
    print("=" * 80)

if __name__ == '__main__':
    stats = analyze_integration_status()
    print_report(stats)
