#!/usr/bin/env python3
"""
自动迁移脚本：将旧向量化服务导入替换为新的统一引擎
"""
import os
import re
from pathlib import Path

# 旧服务到新引擎的映射
OLD_IMPORTS = [
    (r'from app\.services\.vectorization_service_complete import VectorizationService',
     'from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend'),

    (r'from app\.services\.vectorization_service_v2 import get_vectorization_service_v2',
     'from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend'),

    (r'from app\.services\.vectorization_service import vectorization_service',
     'from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend'),

    (r'from app\.services\.embedding_service_v2 import.*',
     'from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend'),

    (r'from app\.services\.embedding_service import.*',
     'from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend'),

    (r'from app\.services\.semantic_embedding import.*',
     'from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend'),

    (r'from app\.services\.tfidf_vectorization import.*',
     'from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend'),
]

# DocumentChunk导入迁移
DOCUMENTCHUNK_IMPORTS = [
    (r'from app\.services\.vectorization_service_complete import DocumentChunk',
     'from app.models.document_chunk import DocumentChunk'),
]

# 文件列表
FILES_TO_MIGRATE = [
    'src/app/api/document_processing_v2.py',
    'src/app/api/source_traceback.py',
    'src/app/services/document_processing_pipeline.py',
    'src/app/services/document_processing_pipeline_complete.py',
    'src/app/services/document_processing_pipeline_v2.py',
    'src/app/services/proposal_generator_service.py',
    'src/app/services/skill_sandbox.py',
    'src/app/services/skills/skill_base.py',
    'src/app/services/source_traceback_service.py',
    'src/app/tasks/audio_tasks.py',
    'src/app/tools/document/unified_document_pipeline.py',
    'src/migrate_chunks_table.py',
    'src/test_document_pipeline.py',
    'src/test_end_to_end.py',
    'src/tests/test_all.py',
]


def migrate_file(filepath: str) -> tuple[bool, str]:
    """
    迁移单个文件

    Returns:
        (是否修改, 消息)
    """
    if not os.path.exists(filepath):
        return False, f"文件不存在: {filepath}"

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    modified = False

    # 替换旧导入
    for old_pattern, new_import in OLD_IMPORTS:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_import, content)
            modified = True

    # 替换DocumentChunk导入
    for old_pattern, new_import in DOCUMENTCHUNK_IMPORTS:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_import, content)
            modified = True

    # 检查是否有重复导入
    if modified:
        # 去重：如果新导入已存在，移除重复的
        lines = content.split('\n')
        seen_imports = set()
        new_lines = []

        for line in lines:
            if 'from app.tools.vectorization import' in line:
                if line not in seen_imports:
                    seen_imports.add(line)
                    new_lines.append(line)
            else:
                new_lines.append(line)

        content = '\n'.join(new_lines)

    if modified and content != original_content:
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, f"✅ 已迁移: {filepath}"

    return False, f"⏭️  无需修改: {filepath}"


def main():
    """主函数"""
    print("=" * 70)
    print("向量化服务导入迁移工具")
    print("=" * 70)
    print()

    total = 0
    migrated = 0
    skipped = 0
    errors = 0

    for filepath in FILES_TO_MIGRATE:
        total += 1
        try:
            modified, message = migrate_file(filepath)
            print(message)

            if modified:
                migrated += 1
            else:
                skipped += 1

        except Exception as e:
            errors += 1
            print(f"❌ 错误: {filepath} - {e}")

    print()
    print("=" * 70)
    print(f"迁移完成:")
    print(f"  总文件数: {total}")
    print(f"  已迁移: {migrated}")
    print(f"  跳过: {skipped}")
    print(f"  错误: {errors}")
    print("=" * 70)


if __name__ == '__main__':
    main()
