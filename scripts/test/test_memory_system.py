#!/usr/bin/env python3
"""
Mem0长期记忆系统测试脚本

测试内容：
1. 用户偏好记忆
2. 项目上下文记忆
3. 实体记忆
4. 记忆检索
5. 对话洞察提取
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.memory_service import MemoryService


async def test_memory_service():
    """测试Mem0记忆服务"""
    print("=" * 60)
    print("Mem0 长期记忆系统测试")
    print("=" * 60)

    # 初始化服务
    print("\n[1] 初始化Mem0服务...")
    memory_service = MemoryService()

    if not memory_service.is_enabled():
        print("❌ Mem0未启用（需要配置ANTHROPIC_API_KEY）")
        print("请在 .env 文件中设置 ANTHROPIC_API_KEY")
        return False

    print("✅ Mem0服务初始化成功")

    # 测试用户ID
    test_user_id = "test_user_001"

    # 测试1: 添加用户偏好
    print("\n[2] 测试用户偏好记忆...")
    preferences = [
        "用户喜欢详细的学术分析报告",
        "用户对民族文化的商业价值特别感兴趣",
        "用户偏好中文回复"
    ]

    for pref in preferences:
        result = await memory_service.add_user_preference(
            user_id=test_user_id,
            preference=pref
        )
        if result["status"] == "success":
            print(f"  ✅ 添加偏好: {pref[:30]}...")
        else:
            print(f"  ❌ 添加失败: {result['message']}")

    # 测试2: 添加项目上下文
    print("\n[3] 测试项目上下文记忆...")
    contexts = [
        "该项目研究十八洞村的山歌文化和传承现状",
        "项目关注点：旅游开发与文化保护的平衡",
        "研究时间跨度：2013年精准扶贫开始至今"
    ]

    for ctx in contexts:
        result = await memory_service.add_project_context(
            project_id=1,
            user_id=test_user_id,
            context=ctx
        )
        if result["status"] == "success":
            print(f"  ✅ 添加上下文: {ctx[:30]}...")
        else:
            print(f"  ❌ 添加失败: {result['message']}")

    # 测试3: 添加实体记忆
    print("\n[4] 测试实体记忆...")
    entities = [
        ("龙德成", "person", "十八洞村村长，精准扶贫见证者，熟悉村史和山歌传统"),
        ("十八洞村", "place", "湖南湘西苗族聚居地，精准扶贫首倡地，保留丰富山歌文化"),
        ("苗族山歌节", "event", "每年农历六月六举办，村民展示传统山歌的重要场合")
    ]

    for entity_name, entity_type, description in entities:
        result = await memory_service.add_entity_memory(
            user_id=test_user_id,
            entity_name=entity_name,
            entity_type=entity_type,
            description=description,
            project_id=1
        )
        if result["status"] == "success":
            print(f"  ✅ 添加实体: {entity_name} ({entity_type})")
        else:
            print(f"  ❌ 添加失败: {result['message']}")

    # 测试4: 检索相关记忆
    print("\n[5] 测试记忆检索...")
    queries = [
        "十八洞村的山歌文化",
        "用户对商业价值的偏好",
        "龙德成是谁"
    ]

    for query in queries:
        print(f"\n  查询: '{query}'")
        memories = await memory_service.get_relevant_memories(
            user_id=test_user_id,
            query=query,
            limit=3
        )

        if memories:
            print(f"  ✅ 找到 {len(memories)} 条相关记忆:")
            for i, mem in enumerate(memories, 1):
                content = mem.get("memory", "")
                print(f"    {i}. {content[:60]}...")
        else:
            print("  ⚠️  未找到相关记忆")

    # 测试5: 对话洞察提取
    print("\n[6] 测试对话洞察提取...")
    conversation_history = [
        {"role": "user", "content": "我想了解十八洞村的山歌有什么特点？"},
        {"role": "assistant", "content": "十八洞村的山歌具有浓郁的苗族特色，通常在节日和劳作时演唱。"},
        {"role": "user", "content": "这些山歌有商业价值吗？"},
        {"role": "assistant", "content": "有很大的商业潜力，可以开发文化旅游产品和演出活动。"}
    ]

    insights = await memory_service.extract_insights_from_conversation(
        user_id=test_user_id,
        conversation_history=conversation_history,
        session_id="test_session_001"
    )

    if insights:
        print(f"  ✅ 提取了 {len(insights)} 条洞察:")
        for i, insight in enumerate(insights, 1):
            print(f"    {i}. {insight[:60]}...")
    else:
        print("  ⚠️  未提取到明显洞察")

    # 测试6: 获取用户档案
    print("\n[7] 测试用户记忆档案...")
    profile = await memory_service.get_user_profile(user_id=test_user_id)

    print(f"  用户偏好: {len(profile['preferences'])} 条")
    print(f"  项目上下文: {len(profile['projects'])} 条")
    print(f"  实体记忆: {len(profile['entities'])} 条")
    print(f"  对话洞察: {len(profile['insights'])} 条")

    # 测试7: 获取所有记忆
    print("\n[8] 测试获取所有记忆...")
    all_memories = await memory_service.get_all_memories(
        user_id=test_user_id,
        limit=50
    )
    print(f"  ✅ 共有 {len(all_memories)} 条记忆")

    # 清理测试数据（可选）
    print("\n[9] 清理测试数据...")
    cleanup = input("  是否清理测试数据？(y/n): ").strip().lower()
    if cleanup == 'y':
        result = await memory_service.delete_all_memories(user_id=test_user_id)
        if result["status"] == "success":
            print("  ✅ 测试数据已清理")
        else:
            print(f"  ❌ 清理失败: {result['message']}")
    else:
        print("  ⚠️  跳过清理，测试数据保留")

    print("\n" + "=" * 60)
    print("✅ Mem0记忆系统测试完成")
    print("=" * 60)

    return True


async def test_memory_integration():
    """测试记忆系统与对话系统的集成"""
    print("\n" + "=" * 60)
    print("Mem0 与对话系统集成测试")
    print("=" * 60)

    from app.services.dialogue_system import DialogueSystem

    # 检查集成状态
    print("\n[1] 检查集成状态...")
    dialogue_system = DialogueSystem()
    print("  ✅ 对话系统初始化成功")

    memory_service = MemoryService()
    if memory_service.is_enabled():
        print("  ✅ 记忆服务已集成并启用")
    else:
        print("  ⚠️  记忆服务未启用")

    print("\n集成特性：")
    print("  • 对话时自动检索用户记忆")
    print("  • 根据用户偏好调整回答风格")
    print("  • 自动提取并保存对话洞察")
    print("  • 项目上下文自动注入提示词")

    print("\n" + "=" * 60)
    print("✅ 集成测试完成")
    print("=" * 60)


def main():
    """主函数"""
    print("\n🧠 Mem0 长期记忆系统测试工具\n")

    # 检查API密钥
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "sk-ant-your-api-key-here":
        print("❌ 错误: 未配置有效的 ANTHROPIC_API_KEY")
        print("\n请按以下步骤配置：")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 中设置 ANTHROPIC_API_KEY=sk-ant-your-actual-key")
        print("3. 重新运行此脚本")
        return

    print(f"✅ API密钥已配置: {api_key[:20]}...")

    # 运行测试
    try:
        # 测试记忆服务
        asyncio.run(test_memory_service())

        # 测试集成
        asyncio.run(test_memory_integration())

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
