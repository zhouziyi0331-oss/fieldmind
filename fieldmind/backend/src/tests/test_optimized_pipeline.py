#!/usr/bin/env python3
"""
测试优化的文档处理管道
"""
import sys
from pathlib import Path
import asyncio
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.optimized_document_pipeline import OptimizedDocumentPipeline
from app.core.database import SessionLocal
from app.models.project import ProjectDocument
import tempfile

print("=" * 80)
print("测试优化的文档处理管道")
print("=" * 80)


async def test_pipeline():
    """测试管道"""

    # 创建测试文档
    print("\n1. 创建测试文档...")

    test_texts = [
        "这是第一个测试文档。包含一些测试内容。用于验证文档处理管道的性能。" * 10,
        "这是第二个测试文档。包含更多的测试内容。用于验证并行处理能力。" * 10,
        "这是第三个测试文档。测试分块和实体提取功能。" * 10,
    ]

    db = SessionLocal()

    try:
        # 创建临时文档
        doc_ids = []
        temp_files = []

        for i, text in enumerate(test_texts):
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False,
                encoding='utf-8'
            )
            temp_file.write(text)
            temp_file.close()
            temp_files.append(temp_file.name)

            # 创建数据库记录
            doc = ProjectDocument(
                project_id=1,
                filename=f"test_doc_{i+1}.txt",
                original_filename=f"test_doc_{i+1}.txt",
                file_path=temp_file.name,
                file_type="text/plain",
                status="pending"
            )
            db.add(doc)
            db.flush()
            doc_ids.append(doc.id)

        db.commit()
        print(f"  ✓ 创建了 {len(doc_ids)} 个测试文档")

        # 2. 测试单个文档处理
        print("\n2. 测试文本提取...")
        pipeline = OptimizedDocumentPipeline()

        result = await pipeline._extract_texts_parallel(
            [doc_ids[0]],
            db,
            None
        )

        print(f"  成功: {result.successful}/{result.total}")
        print(f"  文本长度: {result.results[0]['length']} 字符")

        # 3. 测试批量处理
        print("\n3. 测试批量并行处理...")

        def progress_cb(stage, progress, message):
            print(f"  进度: {stage} - {progress*100:.0f}% - {message}")

        start = time.time()

        batch_result = await pipeline.process_documents_batch(
            doc_ids,
            project_id=1,
            db=db,
            progress_callback=progress_cb
        )

        duration = time.time() - start

        print(f"\n  ✅ 批量处理完成:")
        print(f"    处理文档: {batch_result['documents_processed']}/{batch_result['total_documents']}")
        print(f"    生成分块: {batch_result['total_chunks']}")
        print(f"    提取实体: {batch_result['total_entities']}")
        print(f"    总耗时: {duration:.2f}s")
        print(f"    平均耗时: {batch_result['avg_time_per_doc']:.2f}s/文档")

        # 4. 测试缓存效果
        print("\n4. 测试缓存效果（重复处理）...")

        start = time.time()

        batch_result2 = await pipeline.process_documents_batch(
            doc_ids,
            project_id=1,
            db=db,
            progress_callback=None
        )

        duration2 = time.time() - start

        print(f"  第二次处理耗时: {duration2:.2f}s")
        print(f"  加速比: {duration/duration2:.1f}x")

        # 清理
        print("\n5. 清理测试数据...")
        for doc_id in doc_ids:
            db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).delete()
        db.commit()

        for temp_file in temp_files:
            Path(temp_file).unlink(missing_ok=True)

        print("  ✓ 清理完成")

        pipeline.shutdown()

    finally:
        db.close()


if __name__ == "__main__":
    print("\n开始测试...")
    asyncio.run(test_pipeline())

    print("\n" + "=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)
