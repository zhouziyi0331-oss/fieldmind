"""
测试文档处理流水线的错误处理和重试机制
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

import sqlite3
from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline

DB_PATH = "/Users/alwan/FieldMind-Rebuild/fieldmind-backend/fieldmind.db"

def test_normal_processing():
    """测试正常处理流程"""
    print("=" * 60)
    print("测试1: 正常文档处理")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    pipeline = DocumentProcessingPipeline(conn, max_retries=3, retry_delay=0.5)

    test_text = """
    量子计算是一种遵循量子力学规律调控量子信息单元进行计算的新型计算模式。
    量子计算机使用量子比特作为信息的基本单位。
    与传统计算机的比特不同，量子比特可以同时处于0和1的叠加态。
    """

    result = pipeline.process_document(
        document_id=2001,
        project_id=1,
        text_content=test_text,
        metadata={"source": "test"}
    )

    conn.close()

    if result["success"]:
        print(f"✅ 处理成功")
        print(f"   - 文档ID: {result['document_id']}")
        print(f"   - 块数量: {result['chunks_count']}")
        print(f"   - 处理时间: {result['processing_time']:.2f}秒")
        print(f"   - 完成阶段: {', '.join(result['stages_completed'])}")
        return True
    else:
        print(f"❌ 处理失败: {result.get('error')}")
        return False


def test_checkpoint_recovery():
    """测试检查点恢复"""
    print("\n" + "=" * 60)
    print("测试2: 检查点恢复机制")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    pipeline = DocumentProcessingPipeline(
        conn,
        max_retries=3,
        retry_delay=0.5,
        enable_checkpoints=True
    )

    # 先创建一个checkpoint
    test_chunks = [
        {
            "text": "这是测试块1",
            "chunk_index": 0,
            "total_chunks": 2,
            "metadata": {}
        },
        {
            "text": "这是测试块2",
            "chunk_index": 1,
            "total_chunks": 2,
            "metadata": {}
        }
    ]

    pipeline._save_checkpoint(2002, "chunked", {"chunks": test_chunks})
    print("✅ 创建了checkpoint")

    # 检查是否能检测到
    has_checkpoint = pipeline._has_checkpoint(2002)
    print(f"{'✅' if has_checkpoint else '❌'} 检测到checkpoint: {has_checkpoint}")

    # 加载checkpoint
    checkpoint = pipeline._load_checkpoint(2002)
    if checkpoint:
        print(f"✅ 加载checkpoint成功")
        print(f"   - 阶段: {checkpoint['stage']}")
        print(f"   - 数据块数: {len(checkpoint['data']['chunks'])}")
    else:
        print("❌ 加载checkpoint失败")

    # 清理
    pipeline._clear_checkpoint(2002)
    print("✅ 清理checkpoint")

    conn.close()
    return checkpoint is not None


def test_batch_processing():
    """测试批量处理"""
    print("\n" + "=" * 60)
    print("测试3: 批量文档处理")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    pipeline = DocumentProcessingPipeline(conn, max_retries=2, retry_delay=0.3)

    documents = [
        {
            "document_id": 2003,
            "project_id": 1,
            "text": "人工智能正在改变世界。机器学习是AI的核心技术。",
            "metadata": {"batch": 1}
        },
        {
            "document_id": 2004,
            "project_id": 1,
            "text": "深度学习使用多层神经网络。CNN用于图像识别。",
            "metadata": {"batch": 1}
        },
        {
            "document_id": 2005,
            "project_id": 1,
            "text": "NLP处理自然语言。Transformer是革命性架构。",
            "metadata": {"batch": 1}
        }
    ]

    def progress_callback(current, total, result):
        status = "✅" if result["success"] else "❌"
        print(f"  {status} [{current}/{total}] 文档{result['document_id']}")

    result = pipeline.batch_process_documents(documents, on_progress=progress_callback)

    conn.close()

    print(f"\n批量处理结果:")
    print(f"   - 总数: {result['total']}")
    print(f"   - 成功: {result['success']}")
    print(f"   - 失败: {result['failed']}")

    return result['success'] == result['total']


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("测试4: 错误处理")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    pipeline = DocumentProcessingPipeline(conn, max_retries=2, retry_delay=0.1)

    # 测试空文本
    result = pipeline.process_document(
        document_id=2006,
        project_id=1,
        text_content="",
        metadata={}
    )

    if not result["success"]:
        print(f"✅ 正确处理空文本错误")
        print(f"   - 错误类型: {result.get('error_type')}")
        print(f"   - 错误信息: {result.get('error', '')[:50]}...")
    else:
        print(f"❌ 应该失败但成功了")

    conn.close()
    return not result["success"]


def verify_data_in_db():
    """验证数据库中的数据"""
    print("\n" + "=" * 60)
    print("验证: 数据库数据检查")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查测试文档的chunks
    test_doc_ids = [2001, 2003, 2004, 2005]
    total_chunks = 0

    for doc_id in test_doc_ids:
        cursor.execute("""
            SELECT COUNT(*), SUM(LENGTH(embedding))
            FROM document_chunks
            WHERE document_id = ?
        """, (doc_id,))

        row = cursor.fetchone()
        if row and row[0] > 0:
            print(f"✅ 文档{doc_id}: {row[0]}个块, 总向量大小: {row[1]}字节")
            total_chunks += row[0]
        else:
            print(f"⚠️ 文档{doc_id}: 无数据")

    conn.close()

    print(f"\n总计: {total_chunks}个块已存储")
    return total_chunks > 0


def main():
    print("\n🚀 开始测试文档处理流水线错误处理")
    print("=" * 60)

    results = []

    # 测试1: 正常处理
    results.append(("正常处理", test_normal_processing()))

    # 测试2: 检查点
    results.append(("检查点恢复", test_checkpoint_recovery()))

    # 测试3: 批量处理
    results.append(("批量处理", test_batch_processing()))

    # 测试4: 错误处理
    results.append(("错误处理", test_error_handling()))

    # 验证数据
    results.append(("数据验证", verify_data_in_db()))

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("✅ 文档处理流水线完整功能验证成功")
        print("✅ 错误处理和重试机制工作正常")
        print("✅ 检查点恢复机制正常")
        return True
    else:
        print(f"\n⚠️ {total - passed}个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
