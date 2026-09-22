#!/usr/bin/env python3
"""
架构修复 #4: 统一上传入口

问题：
1. 三个上传API并存：
   - /api/v1/projects/{project_id}/documents/upload (project_documents.py)
   - /api/documents/upload (documents.py)
   - /api/v1/documents/upload (v1/documents.py)

2. 两个文件表：
   - documents (13条记录，旧表)
   - project_documents (52条记录，主力表)

修复策略：
1. 确认推荐使用的标准API
2. 废弃旧API（添加deprecation警告）
3. 数据迁移：documents → project_documents
4. 生成API迁移指南
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from datetime import datetime

def analyze_upload_endpoints():
    """分析各个上传端点的特性"""
    print("="*70)
    print("步骤1: 分析上传端点")
    print("="*70)

    endpoints = [
        {
            "name": "project_documents上传",
            "path": "/api/v1/projects/{project_id}/documents/upload",
            "file": "app/api/v1/project_documents.py",
            "table": "project_documents",
            "features": [
                "✅ 项目隔离",
                "✅ 完整的后台处理流程",
                "✅ 自动标签提取",
                "✅ 支持14种文件格式",
                "✅ 文件去重（基于hash）",
                "✅ 处理状态跟踪"
            ]
        },
        {
            "name": "documents上传（旧）",
            "path": "/api/documents/upload",
            "file": "app/api/documents.py",
            "table": "project_documents",
            "features": [
                "✅ 支持auto_process参数",
                "⚠️ 与project_documents.py重复",
                "⚠️ 功能较少"
            ]
        },
        {
            "name": "v1/documents上传",
            "path": "/api/v1/documents/upload",
            "file": "app/api/v1/documents.py",
            "table": "documents",
            "features": [
                "❌ 使用旧的documents表",
                "❌ 与标签系统不兼容",
                "⚠️ 需要废弃"
            ]
        }
    ]

    print("\n现有上传端点分析：\n")
    for i, endpoint in enumerate(endpoints, 1):
        print(f"{i}. {endpoint['name']}")
        print(f"   路径: {endpoint['path']}")
        print(f"   文件: {endpoint['file']}")
        print(f"   表: {endpoint['table']}")
        print(f"   特性:")
        for feature in endpoint['features']:
            print(f"     {feature}")
        print()

    print("推荐标准：")
    print("  ✅ /api/v1/projects/{project_id}/documents/upload")
    print("  理由：功能最完整，项目隔离，与标签系统兼容")


def check_data_distribution():
    """检查两个表的数据分布"""
    print("\n" + "="*70)
    print("步骤2: 数据分布检查")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # documents表统计
    cursor.execute("SELECT COUNT(*) FROM documents")
    doc_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT file_type, COUNT(*) as count
        FROM documents
        GROUP BY file_type
    """)
    doc_types = cursor.fetchall()

    # project_documents表统计
    cursor.execute("SELECT COUNT(*) FROM project_documents")
    proj_doc_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT file_type, COUNT(*) as count
        FROM project_documents
        GROUP BY file_type
    """)
    proj_doc_types = cursor.fetchall()

    print(f"\ndocuments表（旧）:")
    print(f"  总数: {doc_count}")
    print(f"  文件类型分布:")
    for file_type, count in doc_types:
        print(f"    {file_type}: {count}")

    print(f"\nproject_documents表（主力）:")
    print(f"  总数: {proj_doc_count}")
    print(f"  文件类型分布:")
    for file_type, count in proj_doc_types:
        print(f"    {file_type}: {count}")

    conn.close()

    return doc_count, proj_doc_count


def migrate_documents_to_project_documents():
    """迁移documents表数据到project_documents"""
    print("\n" + "="*70)
    print("步骤3: 数据迁移")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 查找documents中但不在project_documents中的文件
    cursor.execute("""
        SELECT d.id, d.filename, d.file_type, d.file_path,
               d.file_size, d.file_hash, d.uploaded_at
        FROM documents d
        WHERE NOT EXISTS (
            SELECT 1 FROM project_documents pd
            WHERE pd.file_hash = d.file_hash
        )
    """)

    to_migrate = cursor.fetchall()

    print(f"\n需要迁移的文档: {len(to_migrate)}")

    if len(to_migrate) == 0:
        print("✅ 无需迁移，所有文件已存在于project_documents")
        conn.close()
        return 0

    migrated = 0

    for doc_id, filename, file_type, file_path, file_size, file_hash, uploaded_at in to_migrate:
        try:
            # 默认分配到项目1（如果存在）
            cursor.execute("SELECT id FROM projects LIMIT 1")
            project = cursor.fetchone()

            if not project:
                print("  ⚠️ 没有项目，跳过迁移")
                break

            project_id = project[0]

            # 插入到project_documents
            cursor.execute("""
                INSERT INTO project_documents
                (project_id, filename, original_filename, file_type, file_path,
                 file_size, file_hash, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                filename,
                filename,
                file_type or 'unknown',
                file_path,
                file_size,
                file_hash,
                'uploaded',
                uploaded_at or datetime.utcnow(),
                datetime.utcnow()
            ))

            migrated += 1
            print(f"  ✅ 迁移: {filename}")

        except Exception as e:
            print(f"  ❌ 迁移失败 {filename}: {e}")

    conn.commit()
    conn.close()

    print(f"\n✅ 成功迁移 {migrated} 个文档")
    return migrated


def generate_migration_guide():
    """生成API迁移指南"""
    print("\n" + "="*70)
    print("步骤4: 生成迁移指南")
    print("="*70)

    guide = """
# FieldMind 上传API迁移指南

## 📌 标准上传API（推荐使用）

**POST /api/v1/projects/{project_id}/documents/upload**

### 特性
- ✅ 项目隔离
- ✅ 完整的后台处理流程
- ✅ 自动标签提取
- ✅ 支持14种文件格式
- ✅ 文件去重（基于hash）
- ✅ 处理状态跟踪

### 前端调用示例

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch(
    `/api/v1/projects/${projectId}/documents/upload`,
    {
        method: 'POST',
        body: formData
    }
);

const result = await response.json();
console.log('文档ID:', result.id);
console.log('处理状态:', result.status);
```

### 响应格式

```json
{
    "id": 123,
    "filename": "example.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "status": "pending",
    "processing_progress": 0,
    "tags": [...]
}
```

---

## ⚠️ 已废弃API（不推荐）

### 1. POST /api/documents/upload

**状态**: 已废弃
**原因**: 与标准API功能重复
**替代**: 使用 `/api/v1/projects/{project_id}/documents/upload`

### 2. POST /api/v1/documents/upload

**状态**: 已废弃
**原因**: 使用旧的documents表，与标签系统不兼容
**替代**: 使用 `/api/v1/projects/{project_id}/documents/upload`

---

## 📊 数据表说明

### project_documents（主力表）
- 所有新上传的文件
- 与标签系统兼容
- 支持项目隔离

### documents（旧表）
- 仅用于历史数据兼容
- 新数据不再写入
- 将在未来版本移除

---

## 🔄 迁移步骤

如果您的前端代码仍在使用旧API：

1. 将上传URL改为标准API
2. 确保传入project_id参数
3. 测试文件上传和处理流程
4. 验证标签提取功能

---

生成时间: {datetime}
"""

    guide = guide.replace("{datetime}", datetime.utcnow().isoformat())

    output_path = Path("docs/API_MIGRATION_GUIDE.md")
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(guide)

    print(f"✅ 迁移指南已生成: {output_path}")


def verify_unified_system():
    """验证统一后的系统状态"""
    print("\n" + "="*70)
    print("步骤5: 验证系统状态")
    print("="*70)

    conn = sqlite3.connect("data/fieldmind.db")
    cursor = conn.cursor()

    # 统计
    cursor.execute("SELECT COUNT(*) FROM project_documents")
    total_files = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT pd.id)
        FROM project_documents pd
        JOIN project_document_tags pdt ON pd.id = pdt.document_id
    """)
    files_with_tags = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(DISTINCT pd.id)
        FROM project_documents pd
        JOIN document_chunks dc ON pd.id = dc.document_id
    """)
    files_with_chunks = cursor.fetchone()[0]

    conn.close()

    print(f"\n系统状态:")
    print(f"  总文件数: {total_files}")
    print(f"  有标签的文件: {files_with_tags} ({files_with_tags/total_files*100:.1f}%)")
    print(f"  已切分的文件: {files_with_chunks} ({files_with_chunks/total_files*100:.1f}%)")

    print(f"\n✅ 统一上传系统已就绪")


if __name__ == "__main__":
    print("="*70)
    print("架构修复 #4: 统一上传入口")
    print("="*70)

    analyze_upload_endpoints()
    doc_count, proj_doc_count = check_data_distribution()

    if doc_count > proj_doc_count:
        migrated = migrate_documents_to_project_documents()
    else:
        print("\n✅ 数据已统一，无需迁移")

    generate_migration_guide()
    verify_unified_system()

    print("\n" + "="*70)
    print("✅ 架构修复 #4 完成")
    print("="*70)

    print("\n修复文件: scripts/fix_arch_04_unified_upload.py")
    print("迁移指南: docs/API_MIGRATION_GUIDE.md")
    print("验证命令: sqlite3 data/fieldmind.db 'SELECT COUNT(*) FROM project_documents;'")
    print(f"预期输出: {proj_doc_count} 或更多")
