#!/usr/bin/env python3
"""
批量错误处理迁移脚本
自动将HTTPException替换为自定义异常
"""

import os
import re

def migrate_file(filepath):
    """迁移单个文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes = []

    # 1. 更新imports
    if 'from fastapi import' in content and 'HTTPException' in content:
        # 移除HTTPException导入
        content = re.sub(
            r'from fastapi import ([^)]*?)HTTPException,?\s*',
            r'from fastapi import \1',
            content
        )
        content = re.sub(
            r'from fastapi import ([^)]*?),\s*HTTPException',
            r'from fastapi import \1',
            content
        )

        # 添加自定义异常导入
        if 'from app.core.exceptions import' not in content:
            # 在database import后添加
            content = re.sub(
                r'(from app\.core\.database import [^\n]+\n)',
                r'\1from app.core.exceptions import (\n    ResourceNotFoundException,\n    DatabaseException,\n    ValidationException,\n    FileException,\n    AIServiceException,\n    ErrorCode\n)\n',
                content
            )

        changes.append("更新imports")

    # 2. 替换常见的404错误
    patterns_404 = [
        (r'raise HTTPException\(status_code=404, detail="([^"]+)不存在"\)',
         lambda m: f'raise ResourceNotFoundException("{guess_resource_type(m.group(1))}", {guess_resource_id(m.group(1))})'),
        (r'raise HTTPException\(status_code=404, detail=f?"Document not found"\)',
         r'raise ResourceNotFoundException("Document", document_id)'),
        (r'raise HTTPException\(status_code=404, detail=f?"Session not found"\)',
         r'raise ResourceNotFoundException("Session", session_id)'),
        (r'raise HTTPException\(status_code=404, detail=f?"Project not found"\)',
         r'raise ResourceNotFoundException("Project", project_id)'),
    ]

    for pattern, replacement in patterns_404:
        if isinstance(replacement, str):
            new_content = re.sub(pattern, replacement, content)
        else:
            new_content = re.sub(pattern, replacement, content)

        if new_content != content:
            changes.append(f"替换404错误: {pattern[:50]}...")
            content = new_content

    # 3. 替换500错误
    content = re.sub(
        r'raise HTTPException\(status_code=500, detail=f?"([^"]*数据库[^"]*)"\)',
        r'raise DatabaseException(message="\1", operation="unknown")',
        content
    )
    content = re.sub(
        r'raise HTTPException\(status_code=500, detail=str\(e\)\)',
        r'raise DatabaseException(message=str(e), operation="unknown", cause=e)',
        content
    )
    content = re.sub(
        r'raise HTTPException\(status_code=500, detail=f"([^"]+失败)[^"]*{str\(e\)}"\)',
        r'raise DatabaseException(message=f"\1: {str(e)}", operation="unknown", cause=e)',
        content
    )

    # 4. 移除except HTTPException: raise
    content = re.sub(
        r'\s+except HTTPException:\s+raise\s+',
        '\n    ',
        content
    )

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, changes

    return False, []

def guess_resource_type(chinese_name):
    """根据中文名猜测资源类型"""
    mapping = {
        '项目': 'Project',
        '文档': 'Document',
        '会话': 'Session',
        '对话': 'ChatSession',
        '知识脉络': 'Context',
        '实体': 'Entity',
        '关系': 'Relation',
        '记忆': 'Memory',
        '技能': 'Skill',
        '工作流': 'Workflow',
    }
    for cn, en in mapping.items():
        if cn in chinese_name:
            return en
    return 'Resource'

def guess_resource_id(chinese_name):
    """根据中文名猜测ID变量名"""
    mapping = {
        '项目': 'project_id',
        '文档': 'document_id',
        '会话': 'session_id',
        '对话': 'session_id',
        '知识脉络': 'context_id',
        '实体': 'entity_id',
        '关系': 'relation_id',
        '记忆': 'memory_id',
        '技能': 'skill_id',
        '工作流': 'workflow_id',
    }
    for cn, var in mapping.items():
        if cn in chinese_name:
            return var
    return 'resource_id'

if __name__ == '__main__':
    # 要迁移的文件列表（排除已迁移的）
    files_to_migrate = [
        'app/api/enhanced_chat.py',
        'app/api/citations.py',
        'app/api/memory.py',
        'app/api/knowledge_graph.py',
        'app/api/v1/skills.py',
        'app/api/workflows.py',
        'app/api/skill_config.py',
        'app/api/keyword_search.py',
        'app/api/business_analysis.py',
        'app/api/creative_analysis.py',
    ]

    print("=" * 60)
    print("批量错误处理迁移")
    print("=" * 60)
    print()

    migrated = []
    failed = []

    for filepath in files_to_migrate:
        if not os.path.exists(filepath):
            print(f"⚠️  文件不存在: {filepath}")
            continue

        try:
            modified, changes = migrate_file(filepath)
            if modified:
                print(f"✅ {os.path.basename(filepath)}")
                for change in changes:
                    print(f"   - {change}")
                migrated.append(filepath)
            else:
                print(f"⏭️  {os.path.basename(filepath)} (无需更改)")
        except Exception as e:
            print(f"❌ {os.path.basename(filepath)}: {e}")
            failed.append((filepath, e))

    print()
    print("=" * 60)
    print(f"迁移完成: {len(migrated)}个文件")
    if failed:
        print(f"失败: {len(failed)}个文件")
    print("=" * 60)
