"""
完整测试文档处理流水线
"""
import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.services.document_processing_pipeline import DocumentProcessingPipeline
from app.core.database import SessionLocal
import tempfile
from pathlib import Path

print("=" * 60)
print("测试完整文档处理流水线（使用TF-IDF向量化）")
print("=" * 60)

# 创建数据库会话
db = SessionLocal()

try:
    # 创建临时测试文件
    test_content = """
田野调查方法研究

第一章：研究背景
田野调查是社会科学研究的重要方法。本研究旨在探讨现代田野调查的方法论创新。

第二章：数据收集
我们采用了参与式观察、深度访谈和问卷调查等多种数据收集方法。

第三章：分析框架
基于扎根理论，我们构建了一个多层次的分析框架，包括开放编码、主轴编码和选择性编码。

第四章：研究发现
研究发现，数字技术的应用显著提升了田野调查的效率和数据质量。

第五章：结论与建议
本研究为未来的田野调查提供了方法论指导，建议研究者充分利用数字工具。
    """.strip()

    temp_file = Path(tempfile.mktemp(suffix=".txt"))
    temp_file.write_text(test_content, encoding='utf-8')

    print(f"\n【测试文档】")
    print(f"   文件: {temp_file}")
    print(f"   大小: {len(test_content)} 字符")

    # 初始化流水线
    print(f"\n【步骤1】初始化文档处理流水线...")
    pipeline = DocumentProcessingPipeline()
    print(f"✅ 流水线初始化成功")

    # 处理文档
    print(f"\n【步骤2】处理文档...")
    result = pipeline.process_document(
        document_id=999,
        file_path=str(temp_file),
        project_id=1,
        db=db
    )

    if result['success']:
        print(f"✅ 文档处理成功")
        print(f"   文档ID: {result['document_id']}")
        print(f"   Chunks数量: {result['chunks_count']}")
        print(f"   向量化模型: {result.get('vectorization_model', 'unknown')}")
        print(f"   处理时间: {result['processing_time']:.2f}秒")

        # 检查chunks详情
        if 'chunks' in result:
            print(f"\n【Chunks详情】")
            for i, chunk in enumerate(result['chunks'][:3]):  # 只显示前3个
                print(f"   Chunk {i+1}:")
                print(f"      文本: {chunk['text'][:50]}...")
                print(f"      长度: {chunk['text_length']}")
                if 'embedding' in chunk and chunk['embedding']:
                    print(f"      向量维度: {len(chunk['embedding'])}")
                    print(f"      向量模型: {chunk.get('embedding_model', 'unknown')}")

        # 验证向量化质量
        if result['chunks_count'] > 0:
            print(f"\n【步骤3】验证向量化质量...")
            import numpy as np

            chunks_with_embedding = [c for c in result.get('chunks', []) if c.get('embedding')]
            if chunks_with_embedding:
                embeddings = [c['embedding'] for c in chunks_with_embedding]
                norms = [np.linalg.norm(e) for e in embeddings]

                print(f"✅ 向量化验证")
                print(f"   有效向量数: {len(embeddings)}")
                print(f"   向量维度: {len(embeddings[0])}")
                print(f"   范数范围: [{min(norms):.4f}, {max(norms):.4f}]")

                # 计算相似度矩阵（前5个chunk）
                if len(embeddings) >= 3:
                    print(f"\n【相似度矩阵】（前3个chunks）")
                    for i in range(min(3, len(embeddings))):
                        for j in range(min(3, len(embeddings))):
                            sim = np.dot(embeddings[i], embeddings[j])
                            print(f"   Chunk{i+1} vs Chunk{j+1}: {sim:.4f}")
            else:
                print(f"❌ 没有有效的向量")

        print(f"\n✅ 文档处理流水线测试通过")

    else:
        print(f"❌ 文档处理失败")
        print(f"   错误: {result.get('error', 'unknown')}")

    # 清理
    temp_file.unlink()

finally:
    db.close()

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
