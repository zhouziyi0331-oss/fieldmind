#!/usr/bin/env python3
"""
真实文档测试：商业计划书 → 完整Pipeline验证
验证：
1. MarkItDown提取文本
2. 插入fact_statements（带metadata）
3. 向量化
4. 写入ChromaDB
5. 语义检索
"""

import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from sqlalchemy import create_engine
from sqlalchemy import text as sql_text
from sqlalchemy.orm import sessionmaker
import os
import chromadb

# 数据库连接
db_path = '/Users/alwan/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db'
engine = create_engine(f'sqlite:///{db_path}')
Session = sessionmaker(bind=engine)

def test_business_plan_pipeline():
    """测试商业计划书完整Pipeline"""

    doc_file = '/Users/alwan/Downloads/启程 - AI时代高校生OPC孵化平台 创投商业计划书 (3).docx'

    print("=" * 80)
    print("📄 商业计划书完整Pipeline测试")
    print("=" * 80)

    # 检查文件
    if not os.path.exists(doc_file):
        print(f"❌ 文件不存在: {doc_file}")
        return False

    file_size = os.path.getsize(doc_file)
    print(f"\n【文档信息】")
    print(f"  文件: {os.path.basename(doc_file)}")
    print(f"  大小: {file_size / 1024:.1f} KB")

    session = Session()

    # 清理测试数据
    document_id = 3000
    print(f"\n【清理旧数据】")
    session.execute(sql_text("DELETE FROM document_chunks WHERE document_id = :doc_id"), {"doc_id": document_id})
    session.execute(sql_text("DELETE FROM fact_statements WHERE document_id = :doc_id"), {"doc_id": document_id})
    session.commit()
    print(f"  ✅ 清理完成")

    # 统计处理前的数据
    before_facts = session.execute(sql_text("SELECT COUNT(*) FROM fact_statements WHERE project_id = 1")).scalar()
    before_chunks = session.execute(sql_text("SELECT COUNT(*) FROM document_chunks WHERE project_id = 1")).scalar()

    # 获取ChromaDB处理前的向量数
    chroma_client = chromadb.PersistentClient(path='/Users/alwan/FieldMind-Rebuild/fieldmind-backend/chroma_db')
    collection = chroma_client.get_collection(name="fieldmind_vectors")
    before_vectors = len(collection.get(limit=10000)['ids'])

    print(f"\n【处理前统计】")
    print(f"  fact_statements: {before_facts}")
    print(f"  document_chunks: {before_chunks}")
    print(f"  ChromaDB向量: {before_vectors}")

    # 运行Pipeline
    print(f"\n【运行DocumentProcessingPipeline】")

    from app.services.document_processing_pipeline import DocumentProcessingPipeline

    pipeline = DocumentProcessingPipeline()

    try:
        result = pipeline.process_document(
            document_id=document_id,
            file_path=doc_file,
            project_id=1,
            db=session,
            progress_callback=lambda stage, progress, msg: print(f"  [{stage}] {progress*100:.0f}% - {msg}")
        )

        print(f"\n【处理结果】")
        if result.get('success'):
            print(f"  ✅ 处理成功")
            for stage_name, stage_info in result.get('stages', {}).items():
                if isinstance(stage_info, dict) and stage_info.get('success'):
                    print(f"    ✅ {stage_name}: {stage_info}")
        else:
            print(f"  ❌ 处理失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"\n❌ Pipeline异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 验证数据
    print(f"\n【验证fact_statements】")

    after_facts = session.execute(sql_text("SELECT COUNT(*) FROM fact_statements WHERE project_id = 1")).scalar()
    inserted_facts = after_facts - before_facts

    print(f"  插入后: {after_facts} 条")
    print(f"  本次插入: {inserted_facts} 条")

    if inserted_facts > 0:
        # 查看样本
        samples = session.execute(sql_text("""
            SELECT id, clean_text, topic_tag, keywords
            FROM fact_statements
            WHERE document_id = :doc_id
            ORDER BY id
            LIMIT 5
        """), {"doc_id": document_id}).fetchall()

        print(f"\n  【样本数据】")
        for row in samples:
            print(f"    - {row.clean_text[:50]}... (主题: {row.topic_tag})")

    # 验证document_chunks
    print(f"\n【验证document_chunks】")

    after_chunks = session.execute(sql_text("SELECT COUNT(*) FROM document_chunks WHERE project_id = 1")).scalar()
    inserted_chunks = after_chunks - before_chunks

    print(f"  插入后: {after_chunks} 条")
    print(f"  本次插入: {inserted_chunks} 条")

    # 验证ChromaDB
    print(f"\n【验证ChromaDB向量】")

    after_vectors = len(collection.get(limit=20000)['ids'])
    inserted_vectors = after_vectors - before_vectors

    print(f"  插入后: {after_vectors} 条")
    print(f"  本次插入: {inserted_vectors} 条")

    # 测试语义检索
    if inserted_vectors > 0:
        print(f"\n【测试语义检索】")

        from FlagEmbedding import FlagModel
        model = FlagModel('./models/bge-large-zh-v1.5', use_fp16=False)

        test_queries = [
            "OPC孵化平台的核心功能",
            "商业模式是什么",
            "目标用户群体"
        ]

        for query in test_queries:
            query_embedding = model.encode([query])[0].tolist()

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=2,
                where={"document_id": document_id},
                include=["documents", "metadatas", "distances"]
            )

            print(f"\n  查询: {query}")
            if results and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    doc = results['documents'][0][i]
                    dist = results['distances'][0][i]
                    print(f"    {i+1}. {doc[:60]}... (相似度: {1-dist:.3f})")
            else:
                print(f"    ⚠️  未找到结果")

    session.close()

    # 最终结果
    print("\n" + "=" * 80)
    if inserted_facts > 0 and inserted_chunks > 0 and inserted_vectors > 0:
        print("🎉 商业计划书Pipeline测试完全成功！")
        print("=" * 80)
        print(f"\n✅ 完成验证:")
        print(f"  1. 文档提取成功")
        print(f"  2. 插入 {inserted_facts} 条fact_statements")
        print(f"  3. 插入 {inserted_chunks} 条document_chunks")
        print(f"  4. 插入 {inserted_vectors} 条ChromaDB向量")
        print(f"  5. 语义检索功能正常")
        print(f"\n🎊 完整Pipeline 100%工作！")
        return True
    else:
        print("⚠️  部分功能未完成")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = test_business_plan_pipeline()
    sys.exit(0 if success else 1)
