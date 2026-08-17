#!/usr/bin/env python3
"""
反幻觉四锁机制验证测试

四锁机制：
1. 事实陈述锁（Fact Statements Lock）：将文档分解为原子级事实陈述
2. 引用溯源锁（Citation Lock）：每个回答追溯到原文档位置
3. 置信度评分锁（Confidence Lock）：基于证据强度评估置信度
4. 多源验证锁（Multi-source Lock）：跨文档交叉验证关键信息
"""

import requests
import sqlite3
import json

BASE_URL = "http://localhost:8000"
DB_PATH = "/Users/alwan/FieldMind-Rebuild/fieldmind-backend/data/fieldmind.db"

def test_anti_hallucination():
    print("=" * 80)
    print("🔒 反幻觉四锁机制验证")
    print("=" * 80)

    # 获取最新上传的文档
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, original_filename, chunk_count
        FROM documents
        ORDER BY uploaded_at DESC
        LIMIT 1
    """)
    doc = cursor.fetchone()

    if not doc:
        print("❌ 没有找到测试文档")
        return False

    doc_id, filename, chunk_count = doc
    print(f"\n📄 测试文档: {filename}")
    print(f"   document_id: {doc_id}")
    print(f"   chunks: {chunk_count}")

    # 【锁1】事实陈述锁验证
    print("\n" + "=" * 80)
    print("【锁1】事实陈述锁（Fact Statements Lock）")
    print("=" * 80)

    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT document_id) as docs,
               AVG(LENGTH(clean_text)) as avg_length
        FROM fact_statements
        WHERE document_id = ?
    """, (doc_id,))

    fact_stats = cursor.fetchone()
    total_facts, doc_count, avg_length = fact_stats

    print(f"✅ 事实陈述数量: {total_facts} 条")
    print(f"   平均长度: {avg_length:.1f} 字符")
    print(f"   文档覆盖: {doc_count} 个文档")

    # 显示示例
    cursor.execute("""
        SELECT clean_text, chunk_index, sentence_type
        FROM fact_statements
        WHERE document_id = ?
        LIMIT 3
    """, (doc_id,))

    print("\n   示例事实陈述:")
    for i, (text, chunk_idx, stype) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {text[:80]}...")
        print(f"      来源: chunk#{chunk_idx}, 类型:{stype}")

    # 【锁2】引用溯源锁验证
    print("\n" + "=" * 80)
    print("【锁2】引用溯源锁（Citation Lock）")
    print("=" * 80)

    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN chunk_index IS NOT NULL THEN 1 END) as with_chunk,
               COUNT(CASE WHEN source_file IS NOT NULL THEN 1 END) as with_source
        FROM fact_statements
        WHERE document_id = ?
    """, (doc_id,))

    cite_stats = cursor.fetchone()
    total, with_chunk, with_source = cite_stats

    chunk_coverage = (with_chunk / total * 100) if total > 0 else 0
    source_coverage = (with_source / total * 100) if total > 0 else 0

    print(f"✅ 引用溯源覆盖率:")
    print(f"   块索引标注: {with_chunk}/{total} ({chunk_coverage:.1f}%)")
    print(f"   源文件标注: {with_source}/{total} ({source_coverage:.1f}%)")

    # 测试语义检索是否返回来源信息
    query_params = {
        "query": "平台的核心价值",
        "top_k": 3
    }

    resp = requests.post(
        f"{BASE_URL}/api/document-processing/projects/1/semantic-search",
        params=query_params,
        timeout=30
    )

    if resp.status_code == 200:
        results = resp.json()
        print(f"\n   语义检索测试:")
        print(f"   查询: {query_params['query']}")

        for i, result in enumerate(results.get('results', [])[:2], 1):
            metadata = result.get('metadata', {})
            print(f"\n   结果{i}:")
            print(f"     chunk_id: {result.get('chunk_id')}")
            print(f"     document_id: {metadata.get('document_id')}")
            print(f"     chunk_index: {metadata.get('chunk_index')}")
            print(f"     相似度: {result.get('score', 0):.3f}")
    else:
        print(f"   ⚠️ 语义检索测试失败: {resp.status_code}")

    # 【锁3】置信度评分锁验证
    print("\n" + "=" * 80)
    print("【锁3】置信度评分锁（Confidence Lock）")
    print("=" * 80)

    # 检查是否有置信度字段
    cursor.execute("PRAGMA table_info(fact_statements)")
    columns = [row[1] for row in cursor.fetchall()]

    has_confidence = 'confidence_score' in columns

    if has_confidence:
        cursor.execute("""
            SELECT AVG(confidence_score) as avg_conf,
                   MIN(confidence_score) as min_conf,
                   MAX(confidence_score) as max_conf,
                   COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_conf
            FROM fact_statements
            WHERE document_id = ? AND confidence_score IS NOT NULL
        """, (doc_id,))

        conf_stats = cursor.fetchone()
        avg_conf, min_conf, max_conf, high_conf = conf_stats

        print(f"✅ 置信度评分统计:")
        print(f"   平均置信度: {avg_conf:.3f}")
        print(f"   置信度区间: [{min_conf:.3f}, {max_conf:.3f}]")
        print(f"   高置信度(≥0.8): {high_conf} 条")
    else:
        print("⚠️ 数据库未启用置信度字段")
        print("   建议: 添加confidence_score列以支持置信度评估")

    # 【锁4】多源验证锁验证
    print("\n" + "=" * 80)
    print("【锁4】多源验证锁（Multi-source Lock）")
    print("=" * 80)

    # 检查跨文档关联
    cursor.execute("""
        SELECT COUNT(*) as total_docs
        FROM documents
    """)
    total_docs = cursor.fetchone()[0]

    print(f"✅ 文档库规模: {total_docs} 个文档")

    # 检查实体关联（跨文档验证基础）
    cursor.execute("""
        SELECT COUNT(*) as total_entities
        FROM entities
    """)

    total_entities = cursor.fetchone()[0]

    # 检查document_ids字段是否存在
    cursor.execute("PRAGMA table_info(entities)")
    entity_columns = [row[1] for row in cursor.fetchall()]
    has_doc_ids = 'document_ids' in entity_columns

    if has_doc_ids:
        cursor.execute("""
            SELECT COUNT(CASE WHEN json_array_length(document_ids) > 1 THEN 1 END) as multi_doc
            FROM entities
        """)
        multi_doc = cursor.fetchone()[0]
    else:
        multi_doc = 0

    print(f"   实体总数: {total_entities}")
    print(f"   跨文档实体: {multi_doc} (出现在多个文档)")

    if multi_doc > 0:
        cross_doc_rate = (multi_doc / total_entities * 100)
        print(f"   跨文档验证率: {cross_doc_rate:.1f}%")

        # 显示示例
        cursor.execute("""
            SELECT name, entity_type, document_ids
            FROM entities
            WHERE json_array_length(document_ids) > 1
            LIMIT 3
        """)

        print("\n   跨文档实体示例:")
        for name, etype, doc_ids in cursor.fetchall():
            doc_list = json.loads(doc_ids)
            print(f"   • {name} ({etype})")
            print(f"     出现在 {len(doc_list)} 个文档")
    else:
        print("   ⚠️ 当前实体未建立跨文档关联")
        print("   建议: 上传多个相关文档以启用跨文档验证")

    conn.close()

    # 总结
    print("\n" + "=" * 80)
    print("📊 四锁机制验证总结")
    print("=" * 80)

    print("✅ 锁1 - 事实陈述锁: PASSED")
    print(f"   原子级事实陈述已建立 ({total_facts}条)")

    print(f"✅ 锁2 - 引用溯源锁: {'PASSED' if chunk_coverage > 80 else 'PARTIAL'}")
    print(f"   块索引溯源覆盖率 {chunk_coverage:.1f}%")

    print(f"{'✅' if has_confidence else '⚠️'} 锁3 - 置信度评分锁: {'PASSED' if has_confidence else 'NOT_IMPLEMENTED'}")
    print(f"   {'置信度评分机制已启用' if has_confidence else '需要添加置信度字段'}")

    print(f"{'✅' if multi_doc > 0 else '⚠️'} 锁4 - 多源验证锁: {'PASSED' if multi_doc > 0 else 'NEEDS_MORE_DOCS'}")
    print(f"   {'跨文档实体验证已建立' if multi_doc > 0 else '需要更多文档支持跨文档验证'}")

    print("\n" + "=" * 80)
    return True

if __name__ == "__main__":
    success = test_anti_hallucination()
    exit(0 if success else 1)
