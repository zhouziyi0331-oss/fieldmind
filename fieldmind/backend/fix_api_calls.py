#!/usr/bin/env python3
"""修复API调用"""
import re
import os

files_to_fix = [
    'src/app/services/document_processing_pipeline_v2.py',
    'src/app/services/skill_sandbox.py',
    'src/app/services/source_traceback_service.py',
    'src/app/services/long_memory_service.py',
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        print(f"⏭️  跳过不存在的文件: {filepath}")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 替换 VectorizationService() 实例化
    content = re.sub(
        r'VectorizationService\(\)',
        'UnifiedVectorizationEngine(engine=VectorEngine.BGE_LARGE, storage=StorageBackend.DUAL)',
        content
    )
    
    # 替换 get_vectorization_service_v2() 调用
    content = re.sub(
        r'get_vectorization_service_v2\(\)',
        'UnifiedVectorizationEngine(engine=VectorEngine.BGE_LARGE, storage=StorageBackend.CHROMADB_ONLY)',
        content
    )
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已修复: {filepath}")
    else:
        print(f"⏭️  无需修改: {filepath}")

print("\n完成!")
