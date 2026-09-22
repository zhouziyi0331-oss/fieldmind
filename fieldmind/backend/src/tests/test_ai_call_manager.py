#!/usr/bin/env python3
"""
测试 AI 调用管理器
"""
import sys
from pathlib import Path
import asyncio
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.ai_call_manager import AICallManager, ModelTier

print("=" * 80)
print("测试 AI 调用管理器")
print("=" * 80)


async def test_ai_call_manager():
    """测试 AI 调用管理器"""

    # 检查 API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n❌ 未设置 ANTHROPIC_API_KEY，跳过 AI 调用测试")
        print("提示: export ANTHROPIC_API_KEY=your_key")
        return

    # 初始化管理器
    print("\n1. 初始化 AI 调用管理器...")
    manager = AICallManager(
        api_key=api_key,
        max_concurrent=3,
        rate_limit_per_min=10
    )

    # 2. 测试单次调用
    print("\n2. 测试单次 API 调用...")
    try:
        result = await manager.call_with_retry(
            messages=[
                {"role": "user", "content": "请用一句话介绍田野调查"}
            ],
            model=ModelTier.HAIKU,
            max_tokens=100
        )

        print(f"  ✅ 调用成功:")
        print(f"    响应: {result['text'][:100]}...")
        print(f"    Token: {result['usage']['total_tokens']}")
        print(f"    成本: ${result['cost']:.4f}")
        print(f"    耗时: {result['duration']:.2f}s")

    except Exception as e:
        print(f"  ❌ 调用失败: {e}")

    # 3. 测试批量调用
    print("\n3. 测试批量并发调用...")
    batch_requests = [
        {
            "messages": [{"role": "user", "content": f"什么是田野调查方法{i+1}？"}],
            "model": ModelTier.HAIKU,
            "max_tokens": 50
        }
        for i in range(3)
    ]

    try:
        results = await manager.batch_call(batch_requests)

        success = sum(1 for r in results if not isinstance(r, Exception))
        print(f"  ✅ 批量调用完成: {success}/{len(results)} 成功")

    except Exception as e:
        print(f"  ❌ 批量调用失败: {e}")

    # 4. 测试智能调用
    print("\n4. 测试智能模型选择...")
    try:
        simple_result = await manager.smart_call(
            messages=[{"role": "user", "content": "你好"}],
            task_complexity="simple",
            max_tokens=20
        )
        print(f"  ✅ 简单任务使用: Haiku")

    except Exception as e:
        print(f"  ❌ 智能调用失败: {e}")

    # 5. 查看统计
    print("\n5. 调用统计:")
    metrics = manager.get_metrics()
    print(f"  总调用: {metrics['total_calls']}")
    print(f"  成功率: {metrics['success_rate']:.1%}")
    print(f"  总Token: {metrics['total_tokens']}")
    print(f"  总成本: ${metrics['total_cost']:.4f}")
    print(f"  平均耗时: {metrics['avg_duration']:.2f}s")


if __name__ == "__main__":
    print("\n开始测试...\n")
    asyncio.run(test_ai_call_manager())

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)
