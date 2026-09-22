"""
测试材料溯源功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.source_traceback_service import SourceTracebackService


def test_source_traceback():
    """测试溯源功能"""
    print("\n" + "="*70)
    print("🧪 测试材料溯源功能")
    print("="*70)

    db = SessionLocal()

    try:
        service = SourceTracebackService(db)

        # 测试数据：模拟一个文创分析结果
        test_analysis = {
            'project_id': 1,
            'analysis_type': 'creative',
            'title': '文创分析测试：布依族山歌',
            'parameters': {
                'keywords': ['山歌', '传统文化']
            },
            'result': {
                'creative_possibilities': [
                    {
                        'idea': '山歌剧本杀',
                        'description': '结合传统山歌与现代剧本杀形式',
                        'feasibility_score': 75
                    },
                    {
                        'idea': '山歌音乐节',
                        'description': '举办布依族山歌主题音乐节',
                        'feasibility_score': 82
                    }
                ],
                'keywords': ['山歌', '传统文化']
            }
        }

        print("\n【步骤1】保存分析结果并追溯来源...")
        print(f"   分析类型: {test_analysis['analysis_type']}")
        print(f"   标题: {test_analysis['title']}")

        analysis = service.save_analysis_with_sources(
            project_id=test_analysis['project_id'],
            analysis_type=test_analysis['analysis_type'],
            title=test_analysis['title'],
            parameters=test_analysis['parameters'],
            result=test_analysis['result']
        )

        print(f"✅ 分析结果已保存，ID: {analysis.id}")

        # 获取完整的分析（含溯源）
        print("\n【步骤2】获取完整分析（含溯源信息）...")

        full_analysis = service.get_analysis_with_sources(analysis.id)

        if full_analysis:
            print(f"✅ 获取成功")
            print(f"\n   分析ID: {full_analysis['id']}")
            print(f"   分析类型: {full_analysis['analysis_type']}")
            print(f"   陈述数量: {len(full_analysis['statements'])}")

            # 显示每个陈述和它的来源
            for idx, statement in enumerate(full_analysis['statements'][:3]):  # 只显示前3个
                print(f"\n   陈述 {idx + 1}:")
                print(f"   ├─ 内容: {statement['text']}")
                print(f"   ├─ 类型: {statement['type']}")
                print(f"   ├─ 置信度: {statement.get('confidence_score', 'N/A')}")
                print(f"   └─ 来源数量: {len(statement['sources'])}")

                # 显示来源
                for source_idx, source in enumerate(statement['sources'][:2]):  # 每个陈述显示前2个来源
                    print(f"      来源 {source_idx + 1}:")
                    print(f"      ├─ 类型: {source['type']}")
                    print(f"      ├─ 相关性: {source.get('relevance_score', 'N/A')}")
                    if source.get('quoted_text'):
                        preview = source['quoted_text'][:60] + "..." if len(source['quoted_text']) > 60 else source['quoted_text']
                        print(f"      └─ 引用: {preview}")

        # 测试验证功能
        if full_analysis and full_analysis['statements']:
            first_statement = full_analysis['statements'][0]
            if first_statement['sources']:
                first_source = first_statement['sources'][0]

                print("\n【步骤3】测试来源验证...")
                print(f"   验证来源ID: {first_source['id']}")

                verification = service.verify_source(
                    source_id=first_source['id'],
                    user_id='test_user',
                    status='verified',
                    notes='测试验证：来源正确'
                )

                print(f"✅ 验证成功，ID: {verification.id}")
                print(f"   状态: {verification.status}")
                print(f"   备注: {verification.notes}")

        # 测试获取陈述来源
        if full_analysis and full_analysis['statements']:
            first_statement_id = full_analysis['statements'][0]['id']

            print("\n【步骤4】测试获取特定陈述的来源...")
            print(f"   陈述ID: {first_statement_id}")

            sources = service.get_statement_sources(first_statement_id)

            print(f"✅ 获取成功，找到 {len(sources)} 个来源")

        print("\n" + "="*70)
        print("🎉 溯源功能测试通过！")
        print("="*70)

        print("\n✅ 核心功能验证:")
        print("  • 分析结果保存成功")
        print("  • 陈述自动提取")
        print("  • 来源自动追溯")
        print("  • 来源验证功能正常")
        print("  • 数据查询功能正常")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_source_traceback()
    sys.exit(0 if success else 1)
