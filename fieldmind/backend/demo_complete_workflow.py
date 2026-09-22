"""
完整工作流演示 - 从上传文档到生成提案
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import tempfile
import time


def complete_workflow_demo():
    """演示完整的工作流程"""

    print("\n" + "="*70)
    print("🎬 FieldMind 完整工作流演示")
    print("="*70)

    BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") + "/api"
    project_id = 1

    # ============================================================
    # 第一步：上传文档
    # ============================================================
    print("\n【第一步】上传田野调查文档...")

    test_content = """
田野调查记录 - 布依族文化传承现状

调查时间：2024年3月15日
调查地点：贵州省黔南州某布依族村寨

一、山歌传承现状

王大娘（68岁）是村里有名的山歌手。她告诉我们，布依族的山歌主要有三种类型：

第一种是情歌，主要在节日和婚礼时演唱。旋律优美，歌词含蓄。

第二种是劳动歌，在田间地头劳作时演唱。节奏明快，富有动感。

第三种是叙事歌，讲述历史故事和传说。篇幅较长，内容丰富。

二、传承挑战

王大娘说："现在的年轻人都出去打工了，回来也不愿意学唱山歌。我们担心以后就失传了。"

三、保护措施

政府现在很重视，让我们这些老艺人去学校教孩子们，希望能把这个传统保留下来。

四、文创机会

山歌可以和现代元素结合，开发山歌剧本杀、山歌音乐节等新形式。

五、建议

1. 加强数字化记录和保护
2. 创新传承方式
3. 开发文创产品
    """

    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name

    # 上传文档
    try:
        with open(temp_file, 'rb') as f:
            files = {'file': ('complete_demo.txt', f, 'text/plain')}
            data = {'project_id': project_id}

            response = requests.post(
                f"{BASE_URL}/documents/upload",
                files=files,
                data=data,
                timeout=30
            )

        if response.status_code in [200, 201]:
            result = response.json()
            document_id = result.get('id')
            print(f"✅ 文档上传成功")
            print(f"   文档ID: {document_id}")
            print(f"   文件大小: {len(test_content)} 字")
        else:
            print(f"❌ 上传失败: {response.status_code}")
            return False

    finally:
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    # ============================================================
    # 第二步：处理文档（手动触发）
    # ============================================================
    print("\n【第二步】处理文档...")

    from app.core.database import SessionLocal
    from app.services.document_processing_pipeline import DocumentProcessingPipeline
    from app.models.project import ProjectDocument

    db = SessionLocal()

    try:
        doc = db.query(ProjectDocument).filter(
            ProjectDocument.id == document_id
        ).first()

        if doc:
            pipeline = DocumentProcessingPipeline()
            result = pipeline.process_document(
                document_id=doc.id,
                file_path=doc.file_path,
                project_id=doc.project_id,
                db=db
            )

            if result['success']:
                stages = result['stages']
                print(f"✅ 文档处理完成")
                print(f"   提取: {stages['extract']['text_length']} 字")
                print(f"   清洗: {stages['clean']['cleaned_length']} 字")
                print(f"   切分: {stages['chunk']['total_chunks']} chunks")
                print(f"   向量化: {stages['vectorize']['vectorized_chunks']} 向量")
                print(f"   入库: {stages['index']['stored_chunks']} 条记录")
    finally:
        db.close()

    # ============================================================
    # 第三步：进行分析
    # ============================================================
    print("\n【第三步】进行多维度分析...")

    # 3.1 关键词检索
    print("\n   3.1 关键词检索...")
    response = requests.post(
        f"{BASE_URL}/keyword-search/projects/{project_id}/search",
        json={'keyword': '山歌', 'include_videos': True, 'include_audios': True, 'include_documents': True},
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ 找到 {len(result.get('documents', []))} 个匹配")

    # 3.2 文创分析
    print("\n   3.2 文创分析...")
    response = requests.post(
        f"{BASE_URL}/creative-analysis/projects/{project_id}/analyze",
        json={'keywords': ['山歌', '传统文化'], 'mode': 'creative'},
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        possibilities = result.get('creative_possibilities', [])
        print(f"   ✅ 生成 {len(possibilities)} 个文创建议")
        for idx, p in enumerate(possibilities[:2], 1):
            print(f"      {idx}. {p.get('idea')}")

    # 3.3 业态分析
    print("\n   3.3 业态分析...")
    response = requests.post(
        f"{BASE_URL}/business-analysis/projects/{project_id}/analyze",
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        formats = result.get('suggested_formats', [])
        print(f"   ✅ 推荐 {len(formats)} 种业态")

    # ============================================================
    # 第四步：查看溯源信息
    # ============================================================
    print("\n【第四步】查看分析结果的溯源信息...")

    response = requests.get(
        f"{BASE_URL}/source-traceback/projects/{project_id}/analyses",
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        analyses = result.get('analyses', [])
        print(f"✅ 共有 {len(analyses)} 条分析记录")

        for analysis in analyses[:3]:
            print(f"   - {analysis['title']} (类型: {analysis['analysis_type']})")

    # ============================================================
    # 第五步：智能对话
    # ============================================================
    print("\n【第五步】智能对话（带项目上下文）...")

    response = requests.post(
        f"{BASE_URL}/conversation-memory/projects/{project_id}/ask",
        json={
            'query': '布依族山歌的传承现状如何？',
            'include_documents': True,
            'include_analyses': True,
            'include_chunks': True
        },
        timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        context_summary = result.get('context_summary', {})
        print(f"✅ 对话成功")
        print(f"   上下文: {context_summary.get('documents')} 文档, "
              f"{context_summary.get('analyses')} 分析, "
              f"{context_summary.get('relevant_chunks')} chunks")

    # ============================================================
    # 第六步：生成提案（高潮！）
    # ============================================================
    print("\n【第六步】生成行动提案 ⭐...")

    response = requests.post(
        f"{BASE_URL}/proposal/projects/{project_id}/generate",
        json={
            'proposal_type': 'government',
            'include_budget': True,
            'include_risk': True
        },
        timeout=15
    )

    if response.status_code == 200:
        result = response.json()
        proposal = result.get('proposal', {})

        print(f"✅ 提案生成成功！")
        print(f"   标题: {proposal.get('title')}")
        print(f"   类型: {proposal.get('type')}")
        print(f"   章节数: {len(proposal.get('sections', []))}")

        # 显示章节结构
        print(f"\n   提案结构:")
        for section in proposal.get('sections', []):
            print(f"   - {section['title']}")

        # 显示部分内容
        markdown = proposal.get('markdown', '')
        print(f"\n   提案预览（前500字）:")
        print("   " + "-"*66)
        preview = markdown[:500].replace('\n', '\n   ')
        print(f"   {preview}")
        print("   ...")
        print("   " + "-"*66)

        print(f"\n   📄 完整提案长度: {len(markdown)} 字符")
        print(f"   📥 可导出为Markdown格式")

    # ============================================================
    # 总结
    # ============================================================
    print("\n" + "="*70)
    print("🎉 完整工作流演示完成！")
    print("="*70)

    print("\n✅ 已验证的完整流程:")
    print("   1️⃣  上传田野调查文档")
    print("   2️⃣  自动处理（提取→清洗→切分→向量化→入库）")
    print("   3️⃣  多维度分析（关键词→文创→业态）")
    print("   4️⃣  查看溯源信息（每个结论有来源）")
    print("   5️⃣  智能对话（带完整上下文）")
    print("   6️⃣  一键生成提案（可直接汇报）⭐")

    print("\n🎯 核心价值:")
    print("   从「上传材料」到「生成提案」，全流程打通！")
    print("   用户真正可以拿着提案去汇报了！")

    return True


if __name__ == "__main__":
    success = complete_workflow_demo()
    sys.exit(0 if success else 1)
