"""
工作舱统一服务测试脚本

测试所有工作舱 API 端点
"""

import asyncio
import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')

from app.database import get_db
from app.core.workbench_services import get_workbench_services


async def test_workbench_services():
    """测试工作舱服务"""

    print("=" * 60)
    print("🧪 工作舱统一服务测试")
    print("=" * 60)

    # 获取数据库会话
    db = next(get_db())

    try:
        # 1. 测试服务初始化
        print("\n1️⃣ 测试服务初始化...")
        services = get_workbench_services(db)
        print("✅ 工作舱服务初始化成功")

        # 2. 测试健康检查
        print("\n2️⃣ 测试健康检查...")
        health = services.health_check()
        print(f"   整体状态: {health['status']}")
        print(f"   可用服务: {health['available_services']}/{health['total_services']}")

        for name, status in health['services'].items():
            emoji = "✅" if status['status'] == 'available' else "⚠️" if status['status'] == 'degraded' else "❌"
            print(f"   {emoji} {name}: {status['status']} (v{status['version']})")

        # 3. 测试各服务信息
        print("\n3️⃣ 测试服务信息查询...")
        all_services = services.get_all_services_status()

        for name, info in all_services.items():
            print(f"\n   📦 {info.name}")
            print(f"      状态: {info.status.value}")
            print(f"      版本: {info.version}")
            print(f"      描述: {info.description}")
            print(f"      能力: {', '.join(info.capabilities[:3])}...")

        # 4. 测试 NLP 服务
        print("\n4️⃣ 测试 NLP 服务...")
        tokens = services.nlp.tokenize("这是一个测试文本", "zh")
        print(f"   分词结果: {tokens}")

        # 5. 测试 RAG 服务
        print("\n5️⃣ 测试 RAG 服务...")
        rag_result = services.rag.query(
            question="测试问题",
            project_id=1,
            top_k=5
        )
        print(f"   RAG 查询状态: {rag_result.get('answer', '服务可用')[:50]}...")

        # 6. 测试文档服务
        print("\n6️⃣ 测试文档服务...")
        formats = services.document.get_supported_formats()
        print(f"   支持格式: {len(formats)} 种")
        print(f"   格式列表: {', '.join(formats[:10])}...")

        # 7. 测试知识图谱服务
        print("\n7️⃣ 测试知识图谱服务...")
        kg_info = services.knowledge_graph.get_info()
        print(f"   知识图谱服务: {kg_info.status.value}")

        # 8. 测试未实现的服务
        print("\n8️⃣ 测试未实现的服务...")

        print("   爬虫服务:")
        try:
            services.crawler.crawl_website("https://example.com")
        except NotImplementedError as e:
            print(f"   ⚠️  预期行为: {e}")

        print("\n   记忆服务:")
        try:
            services.memory.store_memory(1, "测试", {})
        except NotImplementedError as e:
            print(f"   ⚠️  预期行为: {e}")

        print("\n   可视化服务:")
        try:
            services.visualization.generate_mind_map({})
        except NotImplementedError as e:
            print(f"   ⚠️  预期行为: {e}")

        print("\n" + "=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)

        # 总结
        print("\n📊 测试总结:")
        print(f"   ✅ 可用服务: {health['available_services']} 个")
        print(f"   ⚠️  降级服务: {sum(1 for s in health['services'].values() if s['status'] == 'degraded')} 个")
        print(f"   ❌ 不可用服务: {sum(1 for s in health['services'].values() if s['status'] == 'unavailable')} 个")

        print("\n🎯 下一步:")
        print("   1. 启动后端: cd backend && python -m uvicorn app.main:app --reload")
        print("   2. 测试 API: curl http://localhost:8000/api/v1/workbench/health")
        print("   3. 查看文档: http://localhost:8000/docs")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_workbench_services())
