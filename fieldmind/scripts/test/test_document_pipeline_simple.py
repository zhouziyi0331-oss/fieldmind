"""
简化的文档处理流水线测试 - 不依赖settings
"""
import sys
import os
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

import sqlite3
from datetime import datetime

# 测试参数
DB_PATH = "/Users/alwan/FieldMind-Rebuild/fieldmind-backend/fieldmind.db"
TEST_DOC_ID = 999
TEST_PROJECT_ID = 1

def test_vectorization():
    """测试向量化服务"""
    print("=" * 60)
    print("测试1: 向量化服务")
    print("=" * 60)

    try:
        from app.services.tfidf_vectorization import TfidfVectorizationService

        service = TfidfVectorizationService(embedding_dim=384)

        # 测试文本
        test_chunks = [
            {"text": "这是一段关于人工智能的文本"},
            {"text": "机器学习是AI的重要分支"},
            {"text": "深度学习使用神经网络"},
        ]

        # 向量化
        result = service.vectorize_chunks(test_chunks)

        print(f"✅ 向量化成功")
        print(f"   - 向量数量: {len(result)}")
        if result and 'embedding' in result[0]:
            print(f"   - 向量维度: {len(result[0]['embedding'])}")
            print(f"   - 向量范数: {sum(x**2 for x in result[0]['embedding'])**0.5:.4f}")
        else:
            print(f"   - 结果键: {list(result[0].keys()) if result else 'None'}")

        return True
    except Exception as e:
        print(f"❌ 向量化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chunking():
    """测试文档切分"""
    print("\n" + "=" * 60)
    print("测试2: 文档切分")
    print("=" * 60)

    try:
        from app.services.document_chunker import DocumentChunker

        chunker = DocumentChunker()

        # 测试文本
        test_text = """
        人工智能（Artificial Intelligence, AI）是计算机科学的一个分支。
        它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。

        机器学习是人工智能的核心，是使计算机具有智能的根本途径。
        深度学习则是机器学习研究中的一个新的领域，其动机在于建立、模拟人脑进行分析学习的神经网络。

        自然语言处理是人工智能和语言学领域的分支学科。
        此领域探讨如何处理及运用自然语言。
        """

        chunks = chunker.chunk_document(test_text)

        print(f"✅ 切分成功")
        print(f"   - 切分数量: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3]):
            print(f"   - 块{i}: {len(chunk['text'])}字符")

        return chunks
    except Exception as e:
        print(f"❌ 切分测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_database_insert(chunks):
    """测试数据库插入"""
    print("\n" + "=" * 60)
    print("测试3: 数据库插入")
    print("=" * 60)

    if not chunks:
        print("⚠️ 没有切分数据，跳过")
        return False

    try:
        # 先清理测试数据
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (TEST_DOC_ID,))
        conn.commit()
        print(f"✅ 已清理旧测试数据")

        # 插入新数据
        for i, chunk in enumerate(chunks):
            chunk_id = f"doc{TEST_DOC_ID}_chunk{i}"

            cursor.execute("""
                INSERT INTO document_chunks (
                    chunk_id, document_id, project_id, text, text_length,
                    chunk_index, total_chunks, embedding, embedding_model,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                TEST_DOC_ID,
                TEST_PROJECT_ID,
                chunk['text'],
                len(chunk['text']),
                i,
                len(chunks),
                None,  # embedding稍后添加
                'tfidf-local',
                datetime.utcnow().isoformat()
            ))

        conn.commit()
        print(f"✅ 插入成功: {len(chunks)}个块")

        # 验证
        cursor.execute("SELECT COUNT(*) FROM document_chunks WHERE document_id = ?", (TEST_DOC_ID,))
        count = cursor.fetchone()[0]
        print(f"✅ 验证成功: 数据库中有{count}个块")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库插入失败: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False


def test_full_pipeline():
    """测试完整流水线"""
    print("\n" + "=" * 60)
    print("测试4: 完整流水线（带向量化）")
    print("=" * 60)

    try:
        from app.services.tfidf_vectorization import TfidfVectorizationService
        from app.services.document_chunker import DocumentChunker
        import json

        # 1. 切分
        chunker = DocumentChunker()
        test_text = """
        区块链技术是一种分布式账本技术。
        比特币是区块链技术的第一个成功应用。
        以太坊引入了智能合约的概念。
        去中心化金融（DeFi）正在改变传统金融行业。
        """

        chunks = chunker.chunk_document(test_text)
        print(f"✅ 切分完成: {len(chunks)}个块")

        # 2. 向量化
        vectorizer = TfidfVectorizationService(embedding_dim=384)
        vectorized = vectorizer.vectorize_chunks(chunks)
        print(f"✅ 向量化完成: {len(vectorized)}个向量")

        # 3. 清理旧数据
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_chunks WHERE document_id = ?", (TEST_DOC_ID + 1,))
        conn.commit()

        # 4. 插入带向量的数据
        for i, chunk in enumerate(vectorized):
            chunk_id = f"doc{TEST_DOC_ID + 1}_chunk{i}"

            # 获取向量数据
            embedding_data = chunk.get('embedding', chunk.get('vector', []))

            cursor.execute("""
                INSERT INTO document_chunks (
                    chunk_id, document_id, project_id, text, text_length,
                    chunk_index, total_chunks, embedding, embedding_model,
                    vectorized_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                TEST_DOC_ID + 1,
                TEST_PROJECT_ID,
                chunk['text'],
                len(chunk['text']),
                i,
                len(vectorized),
                json.dumps(embedding_data),  # 存储为JSON
                'tfidf-local',
                datetime.utcnow().isoformat(),
                datetime.utcnow().isoformat()
            ))

        conn.commit()

        # 5. 验证
        cursor.execute("""
            SELECT chunk_id, text_length, LENGTH(embedding) as embedding_size
            FROM document_chunks
            WHERE document_id = ?
        """, (TEST_DOC_ID + 1,))

        results = cursor.fetchall()
        print(f"✅ 完整流水线成功")
        print(f"   - 存储块数: {len(results)}")
        for row in results:
            print(f"   - {row[0]}: {row[1]}字符, 向量大小: {row[2]}字节")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 完整流水线失败: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False


def main():
    print("\n🚀 开始测试文档处理流水线")
    print("=" * 60)

    results = []

    # 测试1: 向量化
    results.append(("向量化服务", test_vectorization()))

    # 测试2: 切分
    chunks = test_chunking()
    results.append(("文档切分", chunks is not None))

    # 测试3: 数据库插入
    if chunks:
        results.append(("数据库插入", test_database_insert(chunks)))
    else:
        results.append(("数据库插入", False))

    # 测试4: 完整流水线
    results.append(("完整流水线", test_full_pipeline()))

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
        print("\n🎉 所有测试通过！文档处理流水线工作正常")
        return True
    else:
        print(f"\n⚠️ {total - passed}个测试失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
