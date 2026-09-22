#!/usr/bin/env python3
"""
配置属性迁移脚本
从扁平配置 (app.config) 迁移到分层配置 (app.core.config)
"""
import re
import sys
from pathlib import Path

# 映射规则: 旧属性 -> 新属性
MAPPING = {
    r'settings\.DATABASE_URL': 'settings.database.url',
    r'settings\.OPENAI_API_KEY': 'settings.ai.openai_api_key',
    r'settings\.ANTHROPIC_API_KEY': 'settings.ai.anthropic_api_key',
    r'settings\.NEO4J_URI': 'settings.neo4j.uri',
    r'settings\.NEO4J_USER': 'settings.neo4j.user',
    r'settings\.NEO4J_PASSWORD': 'settings.neo4j.password',
    r'settings\.REDIS_HOST': 'settings.redis.host',
    r'settings\.REDIS_PORT': 'settings.redis.port',
    r'settings\.REDIS_DB': 'settings.redis.db',
    r'settings\.WHISPER_MODEL': 'settings.ai.whisper_model',
    r'settings\.WHISPER_DEVICE': 'settings.ai.whisper_device',
    r'settings\.EMBEDDING_MODEL': 'settings.ai.embedding_model',
    r'settings\.UPLOAD_DIR': 'settings.storage.upload_dir',
    r'settings\.RAGFLOW_API_URL': 'settings.ai.ragflow_api_url',
    r'settings\.RAGFLOW_API_KEY': 'settings.ai.ragflow_api_key',
    r'settings\.CHROMADB_HOST': 'settings.chromadb.host',
    r'settings\.CHROMADB_PORT': 'settings.chromadb.port',
}

def migrate_file(file_path: Path) -> int:
    """迁移单个文件，返回替换次数"""
    if not file_path.exists():
        return 0

    content = file_path.read_text(encoding='utf-8')
    original_content = content
    count = 0

    for old_pattern, new_attr in MAPPING.items():
        content, n = re.subn(old_pattern, new_attr, content)
        count += n

    if content != original_content:
        file_path.write_text(content, encoding='utf-8')

    return count

def main():
    files_to_migrate = [
        'app/core/database.py',
        'app/core/transcription.py',
        'app/core/knowledge_graph.py',
        'app/core/rag_engine.py',
        'app/core/unified_transcription.py',
        'app/tasks/document_tasks.py',
        'app/services/vectorization_service.py',
        'app/services/background_tasks.py',
        'app/services/ragflow_service.py',
        'app/services/video_processor.py',
        'app/services/neo4j_adapter.py',
        'app/services/vectorization_service_v2.py',
        'app/services/keyword_search_service.py',
        'app/services/cognee_service.py',
    ]

    total_changes = 0
    for file_rel in files_to_migrate:
        file_path = Path(file_rel)
        count = migrate_file(file_path)
        if count > 0:
            print(f"✅ {file_rel}: {count} 处替换")
            total_changes += count
        else:
            print(f"⏭️  {file_rel}: 无需修改")

    print(f"\n📊 总计: {total_changes} 处配置属性已迁移")
    return 0 if total_changes > 0 else 1

if __name__ == '__main__':
    sys.exit(main())
