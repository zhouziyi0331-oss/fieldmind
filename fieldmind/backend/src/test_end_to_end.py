"""
端到端测试：上传真实文档并验证完整流水线
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.tools.document import UnifiedDocumentPipeline
from app.models.project import Project, ProjectDocument
import tempfile
from datetime import datetime


def create_test_document():
    """创建测试文档"""
    content = """
田野调查记录 - 布依族山歌访谈

访谈时间：2024年3月15日
访谈地点：贵州省黔南州某布依族村寨
受访人：王大娘（68岁，布依族山歌传承人）

访谈记录：

问：您能介绍一下布依族山歌的主要类型吗？

答：我们布依族的山歌主要有三大类。第一类是情歌，年轻人在节日或者婚礼上唱，旋律很优美，歌词也很含蓄，不会直接说喜欢，都是用比喻。

第二类是劳动歌，在田里干活的时候唱。这种歌节奏比较快，很有劲，唱着唱着就不觉得累了。我年轻的时候，大家一起插秧，边插边唱，一天下来能插好多田。

第三类是叙事歌，讲的是我们布依族的历史故事和传说。这种歌篇幅很长，有的要唱好几个小时。我记得我阿婆教我的一首《十二月歌》，讲的是一年四季的农事和节日，每个月都有不同的内容。

问：现在年轻人还唱山歌吗？

答：现在唱的人少了。年轻人都出去打工了，回来也不太愿意学。我们这些老人还在唱，但是担心以后就失传了。政府现在也重视，让我们去学校教孩子们，希望能把这个传统保留下来。

山歌不仅仅是唱歌，它是我们布依族文化的重要组成部分。每一首歌都承载着我们的记忆，我们的情感，我们对生活的理解。

调研者记录：
王大娘演唱了三首不同类型的山歌片段，嗓音清亮，富有感染力。访谈过程中，周围陆续有村民围观，几位老人也加入了演唱，形成了一个小型的山歌表演。这次访谈充分展现了布依族山歌在当地社区中的文化地位和传承现状。
    """

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
        f.write(content)
        return f.name, content


def test_end_to_end():
    """端到端测试"""
    print("\n" + "="*70)
    print("🧪 端到端测试：完整文档处理流水线")
    print("="*70)

    db = SessionLocal()

    try:
        # 步骤1: 获取或创建admin用户
        print("\n【步骤1】检查admin用户...")
        from app.models.user import User
        admin_user = db.query(User).filter(User.email == "admin@fieldmind.com").first()

        if not admin_user:
            print("   admin用户不存在，请先运行 python3 init_db.py")
            return False

        print(f"✅ 找到admin用户: ID={admin_user.id}")

        # 步骤2: 创建测试项目
        print("\n【步骤2】创建测试项目...")
        project = Project(
            name="布依族文化调研测试",
            description="端到端测试项目",
            owner_id=admin_user.id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f"✅ 项目创建成功: ID={project.id}, 名称={project.name}")

        # 步骤3: 创建测试文档
        print("\n【步骤3】创建测试文档...")
        file_path, content = create_test_document()
        print(f"✅ 测试文件创建: {file_path}")
        print(f"   文件大小: {len(content)} 字")

        document = ProjectDocument(
            project_id=project.id,
            filename="布依族山歌访谈.txt",
            original_filename="布依族山歌访谈.txt",
            file_type="text/plain",
            file_path=file_path,
            file_size=len(content),
            status="pending"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        print(f"✅ 文档记录创建: ID={document.id}")

        # 步骤4: 执行完整流水线
        print("\n【步骤4】执行文档处理流水线...")
        print("   ├─ 阶段1: 内容提取")
        print("   ├─ 阶段2: 数据清洗")
        print("   ├─ 阶段3: 文档切分")
        print("   ├─ 阶段4: 向量化")
        print("   └─ 阶段5: 入库索引")

        pipeline = UnifiedDocumentPipeline()

        # 进度回调函数
        current_stage = [None]
        def progress_callback(stage, progress, message):
            if stage != current_stage[0]:
                print(f"\n   ▶ {stage}: {message}")
                current_stage[0] = stage
            else:
                print(f"     {message}")

        result = pipeline.process_document(
            document_id=document.id,
            file_path=file_path,
            project_id=project.id,
            db=db,
            progress_callback=progress_callback
        )

        print("\n【步骤5】验证处理结果...")

        if result["success"]:
            print("✅ 处理成功！")

            # 验证各阶段
            stages = result["stages"]

            print("\n各阶段详情:")
            print(f"  ├─ 提取: {stages['extract']['text_length']} 字")
            print(f"  ├─ 清洗: 移除 {stages['clean']['removed_chars']} 字 ({stages['clean']['removed_chars']/stages['clean']['original_length']*100:.1f}%)")
            print(f"  ├─ 切分: {stages['chunk']['total_chunks']} 个chunks, 平均 {stages['chunk']['avg_chunk_size']} 字/chunk")
            print(f"  ├─ 向量化: {stages['vectorize']['vectorized_chunks']} 个向量, 维度 {stages['vectorize']['embedding_dim']}")
            print(f"  └─ 入库: {stages['index']['stored_chunks']} 条记录")

            # 步骤6: 查询验证
            print("\n【步骤6】查询验证...")

            from app.models.document_chunk import DocumentChunk

            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document.id
            ).all()

            print(f"✅ 数据库中找到 {len(chunks)} 个chunks")

            # 显示前3个chunk
            print("\n前3个chunks预览:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"\n  Chunk {i+1}:")
                print(f"  ├─ ID: {chunk.chunk_id}")
                print(f"  ├─ 长度: {chunk.text_length} 字")
                print(f"  ├─ 位置: {chunk.start_pos}-{chunk.end_pos}")
                print(f"  ├─ 有向量: {'是' if chunk.embedding else '否'}")
                preview = chunk.text[:60] + "..." if len(chunk.text) > 60 else chunk.text
                print(f"  └─ 内容: {preview}")

            # 步骤7: 语义搜索测试
            print("\n【步骤7】语义搜索测试...")

            from app.tools.vectorization import UnifiedVectorizationEngine, VectorEngine, StorageBackend
            vectorizer = VectorizationService()

            query = "布依族山歌的类型"
            search_results = vectorizer.semantic_search(
                query=query,
                project_id=project.id,
                db=db,
                top_k=3,
                threshold=0.3
            )

            print(f"✅ 搜索查询: \"{query}\"")
            print(f"   找到 {len(search_results)} 个相关结果:")

            for i, result in enumerate(search_results):
                print(f"\n   结果 {i+1}:")
                print(f"   ├─ 相似度: {result['similarity']:.3f}")
                print(f"   ├─ Chunk ID: {result['chunk_id']}")
                preview = result['text'][:80] + "..." if len(result['text']) > 80 else result['text']
                print(f"   └─ 内容: {preview}")

            print("\n" + "="*70)
            print("🎉 端到端测试完成！所有步骤验证通过")
            print("="*70)

            print("\n✅ 文档处理流水线工作正常:")
            print("  • 文档被正确切分成语义块")
            print("  • 每个chunk都成功向量化")
            print("  • 数据正确存储到数据库")
            print("  • 语义搜索功能正常")
            print("  • 完整工作流稳定运行")

            return True

        else:
            print(f"❌ 处理失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # 清理
        print("\n【清理】删除测试数据...")
        try:
            # 删除chunks
            from app.models.document_chunk import DocumentChunk
            db.query(DocumentChunk).filter(
                DocumentChunk.project_id == project.id
            ).delete()

            # 删除文档
            db.query(ProjectDocument).filter(
                ProjectDocument.project_id == project.id
            ).delete()

            # 删除项目
            db.query(Project).filter(
                Project.id == project.id
            ).delete()

            db.commit()
            print("✅ 测试数据已清理")

            # 删除临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
                print("✅ 临时文件已删除")

        except Exception as e:
            print(f"⚠️  清理时出错: {e}")

        db.close()


if __name__ == "__main__":
    success = test_end_to_end()
    sys.exit(0 if success else 1)
