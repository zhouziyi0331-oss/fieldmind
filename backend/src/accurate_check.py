import os
import sys

# 检查各模块的实际情况
checks = {
    "Hermes 治理引擎": [
        "app/core/hermes.py",
        "app/core/hermes_governance.py",
        "app/core/hermes_governance_examples.py",
        "app/services/hermes_learning_engine.py",
    ],
    "Workbench 工作舱": [
        "app/core/workbench_services.py",
        "app/api/v1/workbench.py",
    ],
    "契约系统": [
        "app/contracts.py",
    ],
    "双通道处理": [
        "app/services/document_processing_pipeline.py",
        "app/services/document_processing_pipeline_v2.py",
        "app/services/document_processing_pipeline_complete.py",
        "app/services/optimized_document_pipeline.py",
        "app/processors/document_pipeline.py",
    ],
    "数据治理": [
        "app/orchestration/data_governance_orchestrator.py",
        "app/models/governance.py",
        "app/core/governance/configuration.py",
        "app/core/governance/compliance.py",
        "app/core/governance/enterprise_hermes.py",
    ],
    "自学习系统": [
        "app/services/learning_service.py",
        "app/models/background_learning.py",
        "app/api/v1/learning.py",
        "app/api/v1/background_learning.py",
    ],
    "Pipeline 状态": [
        "app/models/pipeline_state.py",
        "app/services/pipeline_status.py",
    ]
}

print("=" * 60)
print("FieldMind 核心模块真实完成度检测")
print("=" * 60)
print()

total_exists = 0
total_files = 0

for module, files in checks.items():
    exists = 0
    file_sizes = []
    
    for f in files:
        total_files += 1
        if os.path.exists(f):
            exists += 1
            total_exists += 1
            size = os.path.getsize(f)
            file_sizes.append((f, size))
    
    percentage = (exists / len(files)) * 100 if files else 0
    
    print(f"【{module}】")
    print(f"  完成度: {percentage:.0f}% ({exists}/{len(files)})")
    
    if file_sizes:
        print(f"  已存在文件:")
        for fname, size in file_sizes:
            print(f"    ✓ {fname.split('/')[-1]} ({size/1024:.1f} KB)")
    
    if exists < len(files):
        print(f"  缺失文件:")
        for f in files:
            if not os.path.exists(f):
                print(f"    ✗ {f.split('/')[-1]}")
    
    print()

print("=" * 60)
print(f"总体统计: {total_exists}/{total_files} 文件存在")
print(f"整体完成度: {(total_exists/total_files)*100:.0f}%")
print("=" * 60)
