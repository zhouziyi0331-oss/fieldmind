"""
Mem0 记忆服务测试脚本

测试 mem0 长期记忆功能
"""

import sys
sys.path.insert(0, '/Users/alwan/FieldMind/backend/src')


def test_mem0_service():
    """测试 Mem0 服务"""

    print("=" * 60)
    print("🧪 Mem0 长期记忆服务测试")
    print("=" * 60)

    from app.services.memory.mem0_service import get_mem0_service

    # 获取服务
    mem0 = get_mem0_service()

    # 检查可用性
    print("\n1️⃣ 检查服务可用性...")
    if mem0.is_available():
        print("   ✅ Mem0 服务可用")
    else:
        print("   ⚠️  Mem0 服务不可用")
        print("   💡 提示：运行 pip install mem0ai 安装 Mem0")
        return

    # 测试用户ID
    test_user_id = 999

    # 1. 测试存储记忆
    print("\n2️⃣ 测试存储记忆...")
    memory_id_1 = mem0.store_memory(
        user_id=test_user_id,
        content="我喜欢Python编程",
        metadata={"type": "preference", "category": "programming"}
    )
    print(f"   ✅ 记忆已存储: {memory_id_1}")

    memory_id_2 = mem0.store_memory(
        user_id=test_user_id,
        content="我最近在学习机器学习",
        metadata={"type": "conversation", "topic": "learning"}
    )
    print(f"   ✅ 记忆已存储: {memory_id_2}")

    memory_id_3 = mem0.store_memory(
        user_id=test_user_id,
        content="我对自然语言处理很感兴趣",
        metadata={"type": "preference", "category": "interest"}
    )
    print(f"   ✅ 记忆已存储: {memory_id_3}")

    # 2. 测试搜索记忆
    print("\n3️⃣ 测试搜索记忆...")
    results = mem0.search_memory(
        user_id=test_user_id,
        query="编程",
        limit=5
    )
    if results:
        print(f"   找到 {len(results)} 条相关记忆:")
        for result in results:
            print(f"      - {result.get('content')} (分数: {result.get('score', 0):.2f})")
    else:
        print("   ⚠️  未找到相关记忆")

    # 3. 测试获取用户记忆
    print("\n4️⃣ 测试获取所有记忆...")
    all_memories = mem0.get_user_memories(test_user_id, limit=10)
    print(f"   用户共有 {len(all_memories)} 条记忆")

    # 4. 测试用户偏好学习
    print("\n5️⃣ 测试用户偏好学习...")
    mem0.learn_user_preference(test_user_id, "language", "Python")
    mem0.learn_user_preference(test_user_id, "topic", "AI")
    mem0.learn_user_preference(test_user_id, "style", "简洁")

    preferences = mem0.get_user_preferences(test_user_id)
    print(f"   用户偏好:")
    for key, value in preferences.items():
        print(f"      {key}: {value}")

    # 5. 测试获取对话上下文
    print("\n6️⃣ 测试获取对话上下文...")
    context = mem0.get_conversation_context(test_user_id, limit=5)
    print(f"   对话上下文 ({len(context)} 条):")
    for ctx in context[:3]:
        print(f"      - {ctx.get('content', '')[:50]}...")

    # 6. 测试记忆统计
    print("\n7️⃣ 测试记忆统计...")
    stats = mem0.get_memory_stats(test_user_id)
    print(f"   统计信息:")
    print(f"      总记忆数: {stats.get('total_memories')}")
    print(f"      偏好数: {stats.get('preferences_count')}")
    print(f"      对话数: {stats.get('conversations_count')}")

    # 7. 清理测试数据
    print("\n8️⃣ 清理测试数据...")
    if input("   是否清除测试记忆? (y/n): ").lower() == 'y':
        mem0.clear_user_memories(test_user_id)
        print("   ✅ 测试记忆已清除")
    else:
        print("   ⚠️  保留测试记忆")

    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


def test_unified_memory_service():
    """测试统一记忆服务集成"""

    print("\n" + "=" * 60)
    print("🧪 测试统一记忆服务集成")
    print("=" * 60)

    from app.database import get_db
    from app.core.workbench_services import get_workbench_services

    db = next(get_db())

    try:
        services = get_workbench_services(db)

        print("\n1️⃣ 检查记忆服务状态...")
        info = services.memory.get_info()
        print(f"   服务名称: {info.name}")
        print(f"   服务状态: {info.status.value}")
        print(f"   服务版本: {info.version}")

        if info.status.value != "available":
            print("\n   ⚠️  记忆服务不可用，跳过集成测试")
            return

        test_user_id = 888

        print(f"\n2️⃣ 测试存储记忆...")
        memory_id = services.memory.store_memory(
            user_id=test_user_id,
            content="测试记忆内容",
            context={"source": "test"}
        )
        print(f"   ✅ 记忆已存储: {memory_id}")

        print(f"\n3️⃣ 测试搜索记忆...")
        results = services.memory.search_memory(
            user_id=test_user_id,
            query="测试",
            limit=5
        )
        print(f"   找到 {len(results)} 条记忆")

        print(f"\n4️⃣ 测试获取对话上下文...")
        context = services.memory.get_conversation_context(
            user_id=test_user_id,
            limit=5
        )
        print(f"   对话上下文: {len(context)} 条")

        print("\n✅ 统一记忆服务集成测试完成!")

    except NotImplementedError as e:
        print(f"\n   ⚠️  功能未实现: {e}")
    except Exception as e:
        print(f"\n   ❌ 测试失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    # 测试 Mem0 服务
    test_mem0_service()

    # 测试统一服务集成
    print("\n")
    test_unified_memory_service()

    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)
    print("\n💡 提示:")
    print("   - 如果 Mem0 不可用，请运行: pip install mem0ai")
    print("   - 首次使用会下载向量模型")
    print("   - 记忆数据存储在: ./data/memory_db/")
