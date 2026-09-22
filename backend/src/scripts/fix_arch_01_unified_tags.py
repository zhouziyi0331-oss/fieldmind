#!/usr/bin/env python3
"""
架构修复 #1: 统一文件标签系统

问题：
- document_tags表关联documents（旧表，13条记录）
- 实际使用project_documents（新表，52条记录）
- 标签系统完全断联

修复：
1. 创建project_document_tags表
2. 迁移已有标签数据
3. 添加索引
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from datetime import datetime

def create_project_document_tags_table():
    """创建project_document_tags表"""
    print("="*70)
    print("步骤1: 创建project_document_tags表")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查表是否已存在
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='project_document_tags'
    """)

    if cursor.fetchone():
        print("⚠️ project_document_tags表已存在，跳过创建")
        conn.close()
        return

    # 创建新表
    cursor.execute("""
        CREATE TABLE project_document_tags (
            project_document_id VARCHAR(50) NOT NULL,
            tag_id BIGINT NOT NULL,
            confidence FLOAT,
            created_by VARCHAR(50),
            created_at DATETIME NOT NULL,
            PRIMARY KEY (project_document_id, tag_id),
            FOREIGN KEY(project_document_id) REFERENCES project_documents(id) ON DELETE CASCADE,
            FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)

    # 创建索引
    cursor.execute("""
        CREATE INDEX ix_project_document_tags_tag_id
        ON project_document_tags(tag_id)
    """)

    cursor.execute("""
        CREATE INDEX ix_project_document_tags_confidence
        ON project_document_tags(confidence)
    """)

    conn.commit()
    conn.close()

    print("✅ project_document_tags表创建完成")
    print("   - 外键关联: project_documents.id")
    print("   - 索引: tag_id, confidence")


def migrate_existing_tags():
    """迁移已有标签数据（如果有）"""
    print("\n" + "="*70)
    print("步骤2: 迁移已有标签数据")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查document_tags是否有数据
    cursor.execute("SELECT COUNT(*) FROM document_tags")
    old_count = cursor.fetchone()[0]

    if old_count == 0:
        print("⚠️ document_tags表为空，无需迁移")
        conn.close()
        return

    # 尝试迁移（匹配filename）
    cursor.execute("""
        SELECT dt.document_id, dt.tag_id, dt.confidence, dt.created_by, dt.created_at
        FROM document_tags dt
        JOIN documents d ON dt.document_id = d.id
    """)

    old_tags = cursor.fetchall()
    migrated = 0

    for doc_id, tag_id, confidence, created_by, created_at in old_tags:
        # 查找对应的project_document
        cursor.execute("""
            SELECT pd.id FROM project_documents pd
            JOIN documents d ON pd.filename = d.filename
            WHERE d.id = ?
        """, (doc_id,))

        result = cursor.fetchone()
        if result:
            project_doc_id = result[0]

            try:
                cursor.execute("""
                    INSERT INTO project_document_tags
                    (project_document_id, tag_id, confidence, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (project_doc_id, tag_id, confidence, created_by, created_at))
                migrated += 1
            except:
                pass  # 跳过重复记录

    conn.commit()
    conn.close()

    print(f"✅ 迁移完成：{migrated}/{old_count} 条标签记录")


def verify_table_structure():
    """验证表结构"""
    print("\n" + "="*70)
    print("步骤3: 验证表结构")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 检查表结构
    cursor.execute("PRAGMA table_info(project_document_tags)")
    columns = cursor.fetchall()

    print("\nproject_document_tags表结构:")
    for col in columns:
        col_id, name, col_type, not_null, default, pk = col
        print(f"  {name}: {col_type} {'NOT NULL' if not_null else ''} {'PRIMARY KEY' if pk else ''}")

    # 检查索引
    cursor.execute("PRAGMA index_list(project_document_tags)")
    indexes = cursor.fetchall()

    print("\n索引:")
    for idx in indexes:
        print(f"  - {idx[1]}")

    conn.close()


def create_unified_upload_endpoint_doc():
    """生成统一上传端点文档"""
    print("\n" + "="*70)
    print("步骤4: 生成统一上传端点文档")
    print("="*70)

    doc = """
# 统一文件上传API文档

## 推荐使用（唯一标准）

**POST /api/v1/projects/{project_id}/documents/upload**

- 文件表: project_documents
- 标签表: project_document_tags
- 支持: 所有文件类型
- 特性: 项目隔离、完整元数据

## 已废弃（不推荐）

~~POST /api/documents/upload~~
~~POST /api/v1/documents/upload~~

- 使用旧的documents表
- 标签系统不兼容
- 将在未来版本移除

## 前端调用示例

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(`/api/v1/projects/${projectId}/documents/upload`, {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log('文档ID:', result.id);
```

## 标签添加示例

```python
# 上传文件后自动提取标签
document_id = upload_result['id']

# 添加标签关联
cursor.execute('''
    INSERT INTO project_document_tags
    (project_document_id, tag_id, confidence, created_at)
    VALUES (?, ?, ?, ?)
''', (document_id, tag_id, 0.95, datetime.utcnow()))
```
"""

    Path("docs/UNIFIED_UPLOAD_API.md").write_text(doc)
    print("✅ 文档已生成: docs/UNIFIED_UPLOAD_API.md")


if __name__ == "__main__":
    print("="*70)
    print("架构修复 #1: 统一文件标签系统")
    print("="*70)

    create_project_document_tags_table()
    migrate_existing_tags()
    verify_table_structure()
    create_unified_upload_endpoint_doc()

    print("\n" + "="*70)
    print("✅ 架构修复 #1 完成")
    print("="*70)
    print("\n下一步:")
    print("  1. 更新前端调用统一API")
    print("  2. 在project_documents.py中添加自动标签提取")
    print("  3. 废弃旧的documents/upload端点")
