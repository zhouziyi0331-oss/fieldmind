"""
RAG增强系统集成测试

真实连接FieldMind数据库，测试完整功能
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.models.project import Project, ProjectDocument
from app.services.rag.enhanced_agent import create_enhanced_rag_agent
from datetime import datetime


async def test_integration():
    """集成测试主流程"""
    print("=" * 80)
    print("RAG增强系统集成测试 - 连接真实数据库")
    print("=" * 80)

    # 1. 初始化数据库
    print("\n[1/6] 初始化数据库连接...")
    try:
        init_db()
        db = SessionLocal()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return

    # 2. 查找测试项目
    print("\n[2/6] 查找测试项目...")
    try:
        project = db.query(Project).first()
        if not project:
            print("⚠️  数据库中没有项目，创建测试项目...")
            project = Project(
                name="RAG测试项目",
                description="用于测试RAG增强系统",
                created_at=datetime.now()
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"✅ 创建测试项目: {project.name} (ID: {project.id})")
        else:
            print(f"✅ 使用现有项目: {project.name} (ID: {project.id})")
    except Exception as e:
        print(f"❌ 查找项目失败: {e}")
        db.close()
        return

    # 3. 查找项目文档
    print(f"\n[3/6] 查找项目 {project.id} 的文档...")
    try:
        documents = db.query(ProjectDocument).filter(
            ProjectDocument.project_id == project.id
        ).limit(5).all()

        if not documents:
            print("⚠️  项目没有文档，创建测试文档...")
            test_doc = ProjectDocument(
                project_id=project.id,
                file_name="测试文档.txt",
                file_type="txt",
                content="FieldMind是一个智能知识管理系统。系统支持文档上传、智能检索、AI问答等功能。用户可以创建项目，上传文档，然后通过自然语言查询获取答案。",
                extracted_text="FieldMind是一个智能知识管理系统。系统支持文档上传、智能检索、AI问答等功能。",
                file_size=100,
                created_at=datetime.now()
            )
            db.add(test_doc)
            db.commit()
            db.refresh(test_doc)
            documents = [test_doc]
            print(f"✅ 创建测试文档: {test_doc.file_name} (ID: {test_doc.id})")
        else:
            print(f"✅ 找到 {len(documents)} 个文档")
            for doc in documents:
                print(f"   - {doc.file_name} (ID: {doc.id})")

    except Exception as e:
        print(f"❌ 查找文档失败: {e}")
        db.close()
        return

    # 4. 创建Agent并索引文档
    print(f"\n[4/6] 创建RAG Agent并索引文档...")
    try:
        agent = await create_enhanced_rag_agent(enable_all_features=True)
        print("✅ Agent创建成功")

        indexed = 0
        for doc in documents:
            content = doc.content or doc.extracted_text or ""
            if len(content) < 10:
                continue

            await agent.index_document(
                doc_id=f"proj_{project.id}_doc_{doc.id}",
                content=content,
                metadata={
                    "project_id": project.id,
                    "document_id": doc.id,
                    "file_name": doc.file_name
                }
            )
            indexed += 1

        print(f"✅ 成功索引 {indexed} 个文档")

    except Exception as e:
        print(f"❌ 索引文档失败: {e}")
        import traceback
        traceback.print_exc()
        db.close()
        return

    # 5. 执行测试查询
    print(f"\n[5/6] 执行测试查询...")
    test_queries = [
        "FieldMind有哪些功能？",
        "如何使用这个系统？",
        "系统支持什么格式的文档？"
    ]

    for i, query in enumerate(test_queries, 1):
        try:
            print(f"\n查询 {i}: {query}")
            result = await agent.process_query(query, top_k=3)

            print(f"  意图: {result['intent']['intent_type']}")
            print(f"  答案: {result['answer'][:100]}...")
            print(f"  检索到 {len(result['retrieval_results'])} 个结果")

            if result.get('citations'):
                print(f"  引用 {len(result['citations'])} 处")
                for j, cite in enumerate(result['citations'][:2], 1):
                    print(f"    [{j}] 置信度: {cite['confidence_score']:.2%}")

        except Exception as e:
            print(f"  ❌ 查询失败: {e}")

    # 6. 获取统计信息
    print(f"\n[6/6] 系统统计信息...")
    try:
        stats = agent.get_statistics()
        print(f"  索引文档数: {stats['total_documents']}")
        print(f"  对话轮次: {stats['conversation_turns']}")
        print(f"  可用工具: {stats['available_tools']}")
        print(f"  混合检索: {'✅ 启用' if stats['hybrid_retrieval_enabled'] else '❌ 禁用'}")
        print(f"  多样性优化: {'✅ 启用' if stats['diversity_enabled'] else '❌ 禁用'}")
        print(f"  引用追踪: {'✅ 启用' if stats['citation_tracking_enabled'] else '❌ 禁用'}")

    except Exception as e:
        print(f"❌ 获取统计失败: {e}")

    # 清理
    db.close()

    print("\n" + "=" * 80)
    print("✅ 集成测试完成")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_integration())
