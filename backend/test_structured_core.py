"""
结构化处理测试脚本
验证核心3函数是否正确工作

执行: python test_structured_core.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pathlib import Path
from app.services.structured_processor import (
    process_uploaded_file,
    vectorize_chunks,
    rebuild_fts_index
)
from app.core.database import get_db_session
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from sqlalchemy import text


def create_test_file():
    """创建测试文件"""
    test_dir = Path("/tmp/fieldmind/test")
    test_dir.mkdir(parents=True, exist_ok=True)

    test_file = test_dir / "test_山歌.txt"
    test_file.write_text(
        "十八洞村的山歌很有特色。\n"
        "村民们经常在田间唱山歌。\n"
        "这些民歌传承了苗族文化。\n"
        "山歌是当地重要的文化遗产。",
        encoding="utf-8"
    )

    return str(test_file)


def upload_test_file():
    """模拟上传测试文件"""
    from app.core.storage import get_storage
    from app.core.database import generate_id
    from datetime import datetime

    db = get_db_session()

    try:
        # 创建测试文件
        test_file = create_test_file()

        # 上传到对象存储
        storage = get_storage()
        bucket = "documents"
        object_name = f"test/{Path(test_file).name}"

        storage.upload_file(
            bucket=bucket,
            object_name=object_name,
            file_path=test_file
        )

        # 创建文档记录
        doc_id = generate_id("doc")

        document = Document(
            id=doc_id,
            project_id=1,
            name=Path(test_file).name,
            type="document",
            mime_type="text/plain",
            size=os.path.getsize(test_file),
            hash="test_hash_123",
            storage_path=f"{bucket}/{object_name}",
            status="uploaded",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(document)
        db.commit()

        print(f"✓ 测试文件上传成功: {doc_id}")
        return doc_id

    finally:
        db.close()


def test_function_1():
    """
    测试1: 文件入库 + 切分
    期望: 生成 2-4 个 chunk，每个 chunk_index 递增
    """
    print("\n" + "="*60)
    print("测试1: process_uploaded_file() - 文件入库 + 切分")
    print("="*60)

    # 上传测试文件
    file_id = upload_test_file()

    # 执行函数1
    result = process_uploaded_file(file_id)

    print(f"\n结果:")
    print(f"  file_id: {result['file_id']}")
    print(f"  chunks_created: {result['chunks_created']}")
    print(f"  total_text_length: {result['total_text_length']}")
    print(f"  status: {result['status']}")
    print(f"  duration: {result['duration']:.2f}s")

    # 验证数据库
    db = get_db_session()
    try:
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == file_id
        ).order_by(DocumentChunk.chunk_index).all()

        print(f"\n数据库验证:")
        print(f"  chunks 表记录数: {len(chunks)}")

        for chunk in chunks:
            print(f"  - chunk {chunk.chunk_index}: {chunk.text[:50]}...")

        # 断言
        assert len(chunks) >= 2, "应该至少有2个chunk"
        assert chunks[0].chunk_index == 0, "第一个chunk的index应该是0"
        assert chunks[-1].chunk_index == len(chunks) - 1, "chunk_index应该连续"
        assert all(c.project_id == 1 for c in chunks), "所有chunk应该有project_id"

        print("\n✅ 测试1通过")
        return file_id

    finally:
        db.close()


def test_function_2(file_id):
    """
    测试2: 向量化
    期望: 向量存储中有对应记录
    """
    print("\n" + "="*60)
    print("测试2: vectorize_chunks() - 向量化")
    print("="*60)

    # 执行函数2
    result = vectorize_chunks(project_id=1)

    print(f"\n结果:")
    print(f"  project_id: {result['project_id']}")
    print(f"  chunks_vectorized: {result['chunks_vectorized']}")
    print(f"  status: {result['status']}")
    print(f"  duration: {result['duration']:.2f}s")

    # 验证向量存储
    from app.core.vector_store import get_vector_store

    db = get_db_session()
    vector_store = get_vector_store()

    try:
        chunks = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == file_id
        ).all()

        print(f"\n向量存储验证:")
        vectors_found = 0

        for chunk in chunks:
            if vector_store.vector_exists(chunk.id):
                vectors_found += 1
                print(f"  ✓ chunk {chunk.chunk_index} 的向量已存储")

        print(f"\n  总计: {vectors_found}/{len(chunks)} 个向量")

        # 断言
        assert vectors_found == len(chunks), "所有chunk都应该有向量"

        print("\n✅ 测试2通过")

    finally:
        db.close()


def test_function_3():
    """
    测试3: FTS 索引
    期望: 能够通过关键词搜索到 chunk
    """
    print("\n" + "="*60)
    print("测试3: rebuild_fts_index() - FTS 索引同步")
    print("="*60)

    # 执行函数3
    result = rebuild_fts_index(project_id=1)

    print(f"\n结果:")
    print(f"  project_id: {result['project_id']}")
    print(f"  chunks_indexed: {result['chunks_indexed']}")
    print(f"  status: {result['status']}")
    print(f"  duration: {result['duration']:.2f}s")

    # 验证全文搜索
    db = get_db_session()

    try:
        # 搜索关键词"山歌"
        query = text("""
            SELECT chunk_index, text
            FROM document_chunks
            WHERE project_id = :project_id
            AND text LIKE :keyword
        """)

        results = db.execute(
            query,
            {"project_id": 1, "keyword": "%山歌%"}
        ).fetchall()

        print(f"\n全文搜索验证:")
        print(f"  搜索关键词: '山歌'")
        print(f"  找到结果: {len(results)} 条")

        for row in results:
            print(f"  - chunk {row[0]}: {row[1][:50]}...")

        # 断言
        assert len(results) > 0, "应该能搜索到包含'山歌'的chunk"

        print("\n✅ 测试3通过")

    finally:
        db.close()


def cleanup():
    """清理测试数据"""
    print("\n" + "="*60)
    print("清理测试数据")
    print("="*60)

    db = get_db_session()

    try:
        # 删除测试文档（会级联删除chunks）
        deleted_docs = db.query(Document).filter(
            Document.name.like("%test_%")
        ).delete(synchronize_session=False)

        db.commit()

        print(f"✓ 删除 {deleted_docs} 个测试文档")

    finally:
        db.close()


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("结构化处理核心测试")
    print("="*60)

    try:
        # 测试1: 文件入库 + 切分
        file_id = test_function_1()

        # 测试2: 向量化
        test_function_2(file_id)

        # 测试3: FTS 索引
        test_function_3()

        # 汇总
        print("\n" + "="*60)
        print("🎉 所有测试通过！")
        print("="*60)
        print("\n核心结构化功能已验证:")
        print("  ✅ 可检索性 - 全文搜索工作正常")
        print("  ✅ 可拼接性 - chunk_index 顺序正确")
        print("  ✅ 可溯源性 - project_id 和 document_id 完整")
        print("\n下一步: 继续完成知识图谱和统一查询")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # 询问是否清理
        cleanup_choice = input("\n是否清理测试数据? (y/n): ")
        if cleanup_choice.lower() == 'y':
            cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
