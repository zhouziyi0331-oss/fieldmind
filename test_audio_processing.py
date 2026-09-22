#!/usr/bin/env python3
"""
直接测试音频文件处理
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from app.core.database import SessionLocal
from app.models.project import ProjectDocument
from app.agents.ingestion_agent import get_ingestion_agent
import traceback

print("=" * 80)
print("🎤 音频文件处理测试")
print("=" * 80)

# 获取文档信息
db = SessionLocal()
doc = db.query(ProjectDocument).filter(ProjectDocument.id == 18).first()

if not doc:
    print("❌ 找不到文档 18")
    sys.exit(1)

print(f"\n📄 文档信息:")
print(f"  - ID: {doc.id}")
print(f"  - 文件名: {doc.original_filename}")
print(f"  - 文件路径: {doc.file_path}")
print(f"  - 文件类型: {doc.file_type}")
print(f"  - MIME 类型: {doc.mime_type}")
print(f"  - 文件大小: {doc.file_size / (1024*1024):.2f} MB")
print(f"  - 当前状态: {doc.status}")

print(f"\n🔄 开始处理...")
print("-" * 80)

try:
    # 使用 IngestionAgent 处理文件
    ingestion_agent = get_ingestion_agent()

    print(f"✓ IngestionAgent 已初始化")
    print(f"✓ 开始调用 ingest_file()...")

    result = ingestion_agent.ingest_file(
        file_path=doc.file_path,
        filename=doc.original_filename,
        mime_type=doc.mime_type or "application/octet-stream",
        file_metadata={"id": doc.id, "project_id": doc.project_id}
    )

    print(f"\n✅ 处理成功!")
    print(f"\n📊 结果:")
    print(f"  - 状态: {result.get('status', 'unknown')}")
    print(f"  - 文本长度: {len(result.get('text', ''))} 字符")
    print(f"  - 字数: {result.get('word_count', 0)}")

    if result.get('text'):
        print(f"\n📝 文本内容预览（前 500 字符）:")
        print("-" * 80)
        print(result['text'][:500])
        print("-" * 80)

    if result.get('segments'):
        print(f"\n🎬 分段数: {len(result['segments'])}")
        if len(result['segments']) > 0:
            print(f"  第一段: {result['segments'][0]}")

    # 更新数据库
    doc.status = "completed"
    doc.text_content = result.get('text', '')
    doc.word_count = result.get('word_count', 0)
    db.commit()
    print(f"\n✅ 数据库已更新")

except Exception as e:
    print(f"\n❌ 处理失败: {e}")
    print(f"\n📋 详细错误信息:")
    traceback.print_exc()

    # 更新状态为失败
    doc.status = "failed"
    db.commit()

finally:
    db.close()
    print("\n" + "=" * 80)
    print("测试结束")
    print("=" * 80)
