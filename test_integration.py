"""
测试编年史和关键词集成
验证文档处理流水线是否正确集成时间线事件和关键词提取
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from app.core.database import get_db_session
from app.models.timeline import TimelineEvent
from app.models.keyword import Keyword, DocumentKeyword
from app.models.project import ProjectDocument
from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline

def test_integration():
    """测试集成状态"""
    db = get_db_session()

    print("=" * 80)
    print("📊 FieldMind 编年史和关键词功能集成测试")
    print("=" * 80)

    # 1. 检查现有数据
    print("\n1️⃣ 检查现有数据状态：")
    print("-" * 80)

    timeline_count = db.query(TimelineEvent).count()
    print(f"   timeline_events 记录数: {timeline_count}")

    try:
        keyword_count = db.query(DocumentKeyword).count()
        print(f"   document_keywords 记录数: {keyword_count}")
    except Exception as e:
        print(f"   ⚠️  document_keywords 表可能不存在: {e}")
        keyword_count = 0

    doc_count = db.query(ProjectDocument).count()
    print(f"   project_documents 记录数: {doc_count}")

    # 2. 选择一个文档进行测试
    print("\n2️⃣ 选择测试文档：")
    print("-" * 80)

    sample_doc = db.query(ProjectDocument).filter(
        ProjectDocument.word_count > 100
    ).first()

    if not sample_doc:
        print("   ❌ 没有找到合适的测试文档")
        db.close()
        return

    print(f"   文档ID: {sample_doc.id}")
    print(f"   文件名: {sample_doc.filename}")
    print(f"   字数: {sample_doc.word_count}")
    print(f"   项目ID: {sample_doc.project_id}")

    # 3. 检查该文档的时间线事件
    print("\n3️⃣ 检查文档的时间线事件：")
    print("-" * 80)

    # 使用 JSON 查询（兼容旧数据）或直接查询 document_id
    try:
        doc_events = db.query(TimelineEvent).filter(
            TimelineEvent.document_id == sample_doc.id
        ).all()
    except:
        # 如果 document_id 不存在，尝试从 document_ids JSON 查询
        doc_events = []

    print(f"   该文档的时间线事件数: {len(doc_events)}")

    if doc_events:
        print(f"   示例事件:")
        for i, event in enumerate(doc_events[:3], 1):
            print(f"      {i}. {event.title} ({event.date.strftime('%Y-%m-%d')})")

    # 4. 检查该文档的关键词
    print("\n4️⃣ 检查文档的关键词：")
    print("-" * 80)

    try:
        doc_keywords = db.query(DocumentKeyword).filter(
            DocumentKeyword.document_id == sample_doc.id
        ).all()

        print(f"   该文档的关键词数: {len(doc_keywords)}")

        if doc_keywords:
            print(f"   Top 10 关键词:")
            sorted_kw = sorted(doc_keywords, key=lambda x: x.score, reverse=True)
            for i, kw in enumerate(sorted_kw[:10], 1):
                print(f"      {i}. {kw.keyword} (score: {kw.score:.2f}, source: {kw.source})")
    except Exception as e:
        print(f"   ⚠️  关键词查询失败: {e}")

    # 5. 测试手动运行流水线
    print("\n5️⃣ 测试手动运行处理流水线：")
    print("-" * 80)

    # 读取文档内容
    if sample_doc.extracted_text:
        text_content = sample_doc.extracted_text
    else:
        print("   ⚠️  文档没有提取的文本，跳过流水线测试")
        db.close()
        return

    print(f"   文本长度: {len(text_content)} 字符")

    # 运行流水线（只测试时间线和关键词部分）
    print(f"   开始测试时间线提取...")

    try:
        from app.services.timeline_event_builder import get_timeline_event_builder

        timeline_builder = get_timeline_event_builder(db)

        # 删除旧的事件
        db.query(TimelineEvent).filter(
            TimelineEvent.document_id == sample_doc.id
        ).delete()
        db.commit()

        # 重新提取
        timeline_events = timeline_builder.build_events_from_document(
            document_id=sample_doc.id,
            project_id=sample_doc.project_id,
            text_content=text_content,
            metadata={'filename': sample_doc.filename}
        )

        print(f"   ✅ 提取了 {len(timeline_events)} 个时间线事件")

        if timeline_events:
            print(f"   示例事件:")
            for i, event in enumerate(timeline_events[:3], 1):
                print(f"      {i}. {event.title} ({event.date.strftime('%Y-%m-%d')})")

    except Exception as e:
        print(f"   ❌ 时间线提取失败: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n   开始测试关键词提取...")

    try:
        from app.services.keyword_service import KeywordService
        import asyncio

        keyword_service = KeywordService(db)

        # 删除旧的关键词
        try:
            db.query(DocumentKeyword).filter(
                DocumentKeyword.document_id == sample_doc.id
            ).delete()
            db.commit()
        except:
            pass

        # 重新提取
        keywords = asyncio.run(keyword_service.extract_keywords_mixed(
            text=text_content,
            document_id=sample_doc.id,
            project_id=sample_doc.project_id,
            top_n=30,
            use_llm=False
        ))

        print(f"   ✅ 提取了 {len(keywords)} 个关键词")

        if keywords:
            print(f"   Top 10 关键词:")
            sorted_kw = sorted(keywords, key=lambda x: x.get('score', 0), reverse=True)
            for i, kw in enumerate(sorted_kw[:10], 1):
                print(f"      {i}. {kw.get('keyword', 'N/A')} (score: {kw.get('score', 0):.2f})")

    except Exception as e:
        print(f"   ❌ 关键词提取失败: {e}")
        import traceback
        traceback.print_exc()

    # 6. 总结
    print("\n" + "=" * 80)
    print("📋 集成测试总结")
    print("=" * 80)

    # 重新统计
    final_timeline_count = db.query(TimelineEvent).count()
    try:
        final_keyword_count = db.query(DocumentKeyword).count()
    except:
        final_keyword_count = 0

    print(f"   时间线事件总数: {final_timeline_count} (初始: {timeline_count})")
    print(f"   关键词记录总数: {final_keyword_count} (初始: {keyword_count})")

    if final_timeline_count > timeline_count:
        print(f"   ✅ 时间线事件提取功能工作正常 (+{final_timeline_count - timeline_count})")
    else:
        print(f"   ⚠️  时间线事件没有增加，可能文档中没有时间表达式")

    if final_keyword_count > keyword_count:
        print(f"   ✅ 关键词提取功能工作正常 (+{final_keyword_count - keyword_count})")
    else:
        print(f"   ⚠️  关键词没有增加，请检查 document_keywords 表是否存在")

    print("\n" + "=" * 80)
    print("🎯 下一步建议：")
    print("=" * 80)

    if final_keyword_count == keyword_count:
        print("   1. 创建 document_keywords 数据表（运行迁移脚本）")

    print("   2. 上传新文档测试完整流水线")
    print("   3. 测试编年史API: GET /api/chronicle/projects/{project_id}/years")
    print("   4. 测试关键词API（需要创建 keywords.py API）")
    print("   5. 为已有文档批量提取时间线和关键词")

    db.close()

if __name__ == "__main__":
    test_integration()
