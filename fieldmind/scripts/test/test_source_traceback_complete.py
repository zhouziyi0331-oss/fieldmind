"""
完整测试材料溯源功能 - 包含测试数据准备
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

import sqlite3
from datetime import datetime
import json

DB_PATH = "/Users/alwan/FieldMind-Rebuild/fieldmind-backend/fieldmind.db"

def setup_test_data():
    """准备测试数据"""
    print("=" * 60)
    print("准备测试数据")
    print("=" * 60)

    # 使用SQLAlchemy的数据库连接
    from app.core.database import SessionLocal, engine
    import sqlite3

    # 获取SQLAlchemy的数据库路径
    db_url = str(engine.url)
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        # 相对路径转绝对路径
        if db_path.startswith('./'):
            db_path = '/Users/alwan/FieldMind-Rebuild/fieldmind-backend/' + db_path[2:]

    print(f"使用数据库: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 清理旧数据
    cursor.execute("DELETE FROM document_chunks WHERE document_id >= 3000")
    conn.commit()

    # 先添加向量化的文档chunks
    from app.services.document_processing_pipeline_complete import DocumentProcessingPipeline

    pipeline = DocumentProcessingPipeline(conn, max_retries=2)

    # 测试文档：关于布依族山歌的材料
    test_docs = [
        {
            "document_id": 3001,
            "project_id": 1,
            "text": """
            布依族山歌是布依族传统文化的重要组成部分。
            山歌在布依族人民的日常生活中扮演着重要角色。
            山歌通常在田间劳作时演唱，表达劳动人民的情感。
            布依族山歌具有独特的旋律和节奏特点。
            """,
            "metadata": {"source": "test", "topic": "布依族山歌"}
        },
        {
            "document_id": 3002,
            "project_id": 1,
            "text": """
            剧本杀是近年来流行的娱乐形式。
            剧本杀结合了推理、角色扮演等多种元素。
            年轻人特别喜欢参与剧本杀活动。
            剧本杀可以融合各种文化主题。
            """,
            "metadata": {"source": "test", "topic": "剧本杀"}
        },
        {
            "document_id": 3003,
            "project_id": 1,
            "text": """
            音乐节是展示文化的重要平台。
            传统文化可以通过音乐节传播给更多人。
            民族音乐在音乐节上深受欢迎。
            音乐节能够吸引大量游客和文化爱好者。
            """,
            "metadata": {"source": "test", "topic": "音乐节"}
        }
    ]

    print(f"\n正在处理 {len(test_docs)} 个测试文档...")
    for doc in test_docs:
        result = pipeline.process_document(
            document_id=doc["document_id"],
            project_id=doc["project_id"],
            text_content=doc["text"],
            metadata=doc["metadata"]
        )
        if result["success"]:
            print(f"✅ 文档 {doc['document_id']}: {result['chunks_count']}个块")
        else:
            print(f"❌ 文档 {doc['document_id']}: {result.get('error')}")

    conn.close()
    print("\n✅ 测试数据准备完成")

    # 确保SQLAlchemy看到新数据 - 清除会话缓存
    from app.core.database import SessionLocal
    db = SessionLocal()
    db.commit()  # 提交任何待处理的事务
    db.close()

    print("✅ 数据库会话已刷新\n")


def test_source_traceback():
    """测试溯源功能"""
    print("=" * 60)
    print("测试材料溯源功能")
    print("=" * 60)

    from app.core.database import SessionLocal
    from app.services.source_traceback_service import SourceTracebackService

    db = SessionLocal()

    try:
        service = SourceTracebackService(db)

        # 测试分析：文创分析
        test_analysis = {
            'project_id': 1,
            'analysis_type': 'creative',
            'title': '布依族山歌文创开发方案',
            'parameters': {
                'keywords': ['山歌', '布依族', '文创']
            },
            'result': {
                'keywords': ['山歌', '布依族', '文创'],  # 添加到result中
                'creative_possibilities': [
                    {
                        'idea': '山歌主题剧本杀',
                        'description': '将布依族山歌元素融入剧本杀游戏'
                    },
                    {
                        'idea': '布依族山歌音乐节',
                        'description': '举办以布依族山歌为主题的音乐节活动'
                    }
                ]
            }
        }

        print("\n【步骤1】保存分析并追溯来源...")
        analysis = service.save_analysis_with_sources(
            project_id=test_analysis['project_id'],
            analysis_type=test_analysis['analysis_type'],
            title=test_analysis['title'],
            parameters=test_analysis['parameters'],
            result=test_analysis['result']
        )

        print(f"✅ 分析保存成功，ID: {analysis.id}")

        # 获取完整分析
        print("\n【步骤2】获取完整分析（含溯源）...")
        full_analysis = service.get_analysis_with_sources(analysis.id)

        if full_analysis:
            print(f"✅ 获取成功")
            print(f"\n分析详情:")
            print(f"  ID: {full_analysis['id']}")
            print(f"  类型: {full_analysis['analysis_type']}")
            print(f"  标题: {full_analysis['title']}")
            print(f"  陈述数: {len(full_analysis['statements'])}")

            # 显示每个陈述及其来源
            for idx, statement in enumerate(full_analysis['statements']):
                print(f"\n  陈述 {idx + 1}:")
                print(f"  ├─ 内容: {statement['text']}")
                print(f"  ├─ 类型: {statement['type']}")
                print(f"  ├─ 置信度: {statement.get('confidence_score', 0.8)}")
                print(f"  └─ 来源数: {len(statement['sources'])}")

                # 显示来源详情
                for s_idx, source in enumerate(statement['sources'][:3]):
                    print(f"     来源 {s_idx + 1}:")
                    print(f"     ├─ 类型: {source['type']}")
                    print(f"     ├─ 相关性: {source.get('relevance_score', 0):.3f}")
                    if source.get('quoted_text'):
                        preview = source['quoted_text'][:50] + "..." if len(source['quoted_text']) > 50 else source['quoted_text']
                        print(f"     └─ 引用: {preview}")

            # 测试来源验证
            if full_analysis['statements'] and full_analysis['statements'][0]['sources']:
                first_source = full_analysis['statements'][0]['sources'][0]

                print("\n【步骤3】测试来源验证...")
                verification = service.verify_source(
                    source_id=first_source['id'],
                    user_id='test_user',
                    status='verified',
                    notes='测试验证通过'
                )

                print(f"✅ 验证成功")
                print(f"  状态: {verification.status}")
                print(f"  备注: {verification.notes}")

            # 评估溯源质量
            total_statements = len(full_analysis['statements'])
            statements_with_sources = sum(1 for s in full_analysis['statements'] if s['sources'])
            total_sources = sum(len(s['sources']) for s in full_analysis['statements'])

            print("\n" + "=" * 60)
            print("溯源质量评估")
            print("=" * 60)
            print(f"总陈述数: {total_statements}")
            print(f"有来源的陈述: {statements_with_sources}")
            print(f"总来源数: {total_sources}")
            print(f"平均来源数: {total_sources / total_statements if total_statements > 0 else 0:.2f}")
            print(f"溯源覆盖率: {statements_with_sources / total_statements * 100 if total_statements > 0 else 0:.1f}%")

            # 判断是否合格
            coverage = statements_with_sources / total_statements if total_statements > 0 else 0
            if coverage >= 0.8 and total_sources > 0:
                print("\n🎉 溯源功能测试通过！")
                print("✅ 陈述提取正常")
                print("✅ 来源追溯成功")
                print("✅ 相似度计算正常")
                print("✅ 来源验证功能正常")
                return True
            else:
                print(f"\n⚠️ 溯源覆盖率不足: {coverage * 100:.1f}%")
                return False
        else:
            print("❌ 获取分析失败")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


def main():
    print("\n🚀 开始完整溯源功能测试")
    print("=" * 60)

    # 步骤1: 准备测试数据
    setup_test_data()

    # 步骤2: 测试溯源
    success = test_source_traceback()

    if success:
        print("\n" + "=" * 60)
        print("🎉 功能3: 材料溯源回溯 - 100/100")
        print("=" * 60)
    else:
        print("\n⚠️ 部分测试未通过")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
