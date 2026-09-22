#!/usr/bin/env python3
"""
验证所有 WorkflowEngine 包装类的增强实现
检查每个包装类是否包含完整的任务方法和工作流方法
"""

import os
import re
from pathlib import Path

# 所有包装类文件路径
WRAPPER_FILES = [
    "app/services/quantification/quantifier.py",
    "app/services/text_stats.py",
    "app/services/quantification/emotional_features.py",
    "app/services/quantification/content_features.py",
    "app/services/quantification/style_features.py",
    "app/services/quantification/structural_features.py",
    "app/services/quantification/tfidf_extractor.py",
    "app/services/document_chunker_sources.py",
    "app/services/dlt_pipeline.py",
    "app/services/project_document_upload.py",
    "app/services/analysis/comparison_analyzer.py",
    "app/services/analysis/cluster_analyzer.py",
    "app/services/event_handlers/normalization_handler.py",
    "app/services/skills/community_governance.py",
    "app/services/skills/livelihood_ecology.py",
]


def check_wrapper_class(file_path: str) -> dict:
    """检查单个文件的包装类实现"""
    if not os.path.exists(file_path):
        return {
            "file": file_path,
            "exists": False,
            "has_wrapper": False,
            "has_task_methods": False,
            "has_workflow_methods": False,
            "task_count": 0,
            "workflow_count": 0
        }

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 检查是否有 Wrapper 类
    has_wrapper = bool(re.search(r'class \w+Wrapper:', content))

    # 检查是否有 _task_ 方法
    task_methods = re.findall(r'def (_task_\w+)\(', content)
    has_task_methods = len(task_methods) > 0

    # 检查是否有 _workflow 方法
    workflow_methods = re.findall(r'def (\w+_workflow)\(', content)
    has_workflow_methods = len(workflow_methods) > 0

    return {
        "file": file_path,
        "exists": True,
        "has_wrapper": has_wrapper,
        "has_task_methods": has_task_methods,
        "has_workflow_methods": has_workflow_methods,
        "task_count": len(task_methods),
        "workflow_count": len(workflow_methods),
        "task_methods": task_methods,
        "workflow_methods": workflow_methods
    }


def main():
    """主函数"""
    print("=" * 80)
    print("🔍 验证 WorkflowEngine 包装类增强实现")
    print("=" * 80)
    print()

    results = []
    for file_path in WRAPPER_FILES:
        result = check_wrapper_class(file_path)
        results.append(result)

    # 统计
    total_files = len(results)
    enhanced_files = sum(1 for r in results if r['has_task_methods'] and r['has_workflow_methods'])
    total_task_methods = sum(r['task_count'] for r in results)
    total_workflow_methods = sum(r['workflow_count'] for r in results)

    print(f"📊 统计结果")
    print(f"   总文件数: {total_files}")
    print(f"   已增强文件: {enhanced_files}")
    print(f"   增强率: {enhanced_files/total_files*100:.1f}%")
    print(f"   总任务方法数: {total_task_methods}")
    print(f"   总工作流方法数: {total_workflow_methods}")
    print()

    # 详细结果
    print("=" * 80)
    print("📋 详细结果")
    print("=" * 80)
    print()

    for i, result in enumerate(results, 1):
        file_name = os.path.basename(result['file'])
        status = "✅" if result['has_task_methods'] and result['has_workflow_methods'] else "❌"

        print(f"{i}. {status} {file_name}")
        print(f"   路径: {result['file']}")
        print(f"   包装类: {'是' if result['has_wrapper'] else '否'}")
        print(f"   任务方法: {result['task_count']} 个")
        if result['task_methods']:
            for method in result['task_methods']:
                print(f"      - {method}()")
        print(f"   工作流方法: {result['workflow_count']} 个")
        if result['workflow_methods']:
            for method in result['workflow_methods']:
                print(f"      - {method}()")
        print()

    # 总结
    print("=" * 80)
    print("🎉 验证完成！")
    print("=" * 80)

    if enhanced_files == total_files:
        print("✅ 所有包装类均已完成增强实现！")
        print(f"   - 15 个包装类全部包含任务方法和工作流方法")
        print(f"   - 共实现 {total_task_methods} 个任务方法")
        print(f"   - 共实现 {total_workflow_methods} 个工作流方法")
    else:
        print(f"⚠️  还有 {total_files - enhanced_files} 个文件未完成增强")
        for result in results:
            if not (result['has_task_methods'] and result['has_workflow_methods']):
                print(f"   - {result['file']}")


if __name__ == "__main__":
    main()
