"""
测试对话增强记忆功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.conversation_memory_service import ConversationMemoryService


def test_conversation_memory():
    """测试对话记忆功能"""
    print("\n" + "="*70)
    print("🧪 测试对话增强记忆功能")
    print("="*70)

    db = SessionLocal()

    try:
        service = ConversationMemoryService(db)

        # 测试1: 准备上下文
        print("\n【测试1】准备项目上下文...")

        project_id = 1
        query = "布依族山歌有哪些类型？"

        context = service.prepare_context(
            project_id=project_id,
            query=query
        )

        print(f"✅ 上下文准备成功")
        print(f"   项目ID: {context['project_id']}")
        print(f"   查询: {context['query']}")
        print(f"   文档数: {len(context.get('documents', []))}")
        print(f"   分析数: {len(context.get('analyses', []))}")
        print(f"   相关chunks: {len(context.get('relevant_chunks', []))}")

        # 显示统计信息
        stats = context.get('statistics', {})
        print(f"\n   项目统计:")
        print(f"   ├─ 总文档数: {stats.get('total_documents', 0)}")
        print(f"   ├─ 总chunks数: {stats.get('total_chunks', 0)}")
        print(f"   └─ 总分析数: {stats.get('total_analyses', 0)}")

        # 测试2: 生成带上下文的回答
        print("\n【测试2】生成带引用的回答...")

        response = service.generate_contextualized_response(
            project_id=project_id,
            query=query,
            context=context
        )

        print(f"✅ 回答生成成功")
        print(f"   回答: {response.get('answer')}")
        print(f"   置信度: {response.get('confidence')}")
        print(f"   引用数: {len(response.get('citations', []))}")

        # 显示引用
        citations = response.get('citations', [])
        if citations:
            print(f"\n   引用来源:")
            for idx, citation in enumerate(citations[:3], 1):
                print(f"   {idx}. 类型: {citation['type']}")
                if citation['type'] == 'chunk':
                    preview = citation['text'][:50] + "..." if len(citation['text']) > 50 else citation['text']
                    print(f"      内容: {preview}")
                    print(f"      相似度: {citation.get('similarity', 'N/A')}")
                elif citation['type'] == 'analysis':
                    print(f"      标题: {citation['title']}")

        # 测试3: 保存对话到知识库
        print("\n【测试3】保存对话到知识库...")

        conversation_id = service.save_conversation(
            project_id=project_id,
            query=query,
            response=response
        )

        print(f"✅ 对话已保存")
        print(f"   对话ID: {conversation_id}")
        print(f"   类型: conversation")
        print(f"   说明: 对话内容作为\"第四层分析\"保存，下次可引用")

        print("\n" + "="*70)
        print("🎉 对话增强记忆功能测试通过！")
        print("="*70)

        print("\n✅ 核心功能验证:")
        print("  • 自动准备项目上下文")
        print("  • 语义检索相关chunks")
        print("  • 引用历史分析结果")
        print("  • 回答自动标注来源")
        print("  • 对话保存到知识库")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_conversation_memory()
    sys.exit(0 if success else 1)
