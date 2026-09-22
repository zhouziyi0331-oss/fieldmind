#!/usr/bin/env python3
"""
CapaMesh 完整视图测试

使用真实数据测试所有视图的完整功能
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from capamesh.execution_engine import ExecutionEngine
import sqlite3


async def get_sample_data():
    """从数据库获取样本数据用于测试"""
    db_path = "data/fieldmind.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    samples = {}

    # 获取一个文化资产
    cursor.execute("SELECT name FROM entities WHERE entity_type = 'CulturalAsset' LIMIT 1")
    result = cursor.fetchone()
    if result:
        samples['cultural_asset'] = result[0]

    # 获取一个人物
    cursor.execute("SELECT name FROM entities WHERE entity_type = 'Person' LIMIT 1")
    result = cursor.fetchone()
    if result:
        samples['person'] = result[0]

    # 获取一个地点
    cursor.execute("SELECT name FROM entities WHERE entity_type = 'Location' LIMIT 1")
    result = cursor.fetchone()
    if result:
        samples['location'] = result[0]

    conn.close()
    return samples


async def test_cultural_asset_view(engine: ExecutionEngine, asset_name: str):
    """测试文化资产详情视图"""
    print("\n" + "="*60)
    print(f"测试视图: cultural_asset_detail")
    print(f"参数: asset_name = '{asset_name}'")
    print("="*60)

    result = await engine.execute(
        view_id="cultural_asset_detail",
        parameters={"asset_name": asset_name}
    )

    print(f"\n状态: {result['status']}")
    print(f"耗时: {result['metadata']['query_time_ms']} ms")

    if result['status'] == 'success':
        data = result['data']
        print(f"\n输出数据:")
        print(f"  资产名称: {data.get('asset_name')}")
        print(f"  相关地点: {len(data.get('locations', {}).get('records', []))} 个")
        print(f"  传承人: {len(data.get('inheritors', {}).get('records', []))} 个")
        print(f"  提及次数: {data.get('mention_count', 0)}")

        print(f"\n证据来源:")
        for evidence in result.get('evidence', []):
            print(f"  - {evidence['binding_id']}: {evidence['status']} ({evidence['duration_ms']}ms)")

    return result


async def test_person_network_view(engine: ExecutionEngine, person_name: str):
    """测试人物关系网络视图"""
    print("\n" + "="*60)
    print(f"测试视图: person_network")
    print(f"参数: person_name = '{person_name}'")
    print("="*60)

    result = await engine.execute(
        view_id="person_network",
        parameters={"person_name": person_name, "depth": 2}
    )

    print(f"\n状态: {result['status']}")
    print(f"耗时: {result['metadata']['query_time_ms']} ms")

    if result['status'] == 'success':
        data = result['data']
        print(f"\n输出数据:")
        print(f"  人物姓名: {data.get('person_name')}")

        related = data.get('direct_connections', {})
        if isinstance(related, dict) and 'records' in related:
            print(f"  直接关联: {len(related['records'])} 个实体")

        print(f"  关联数量: {data.get('connection_count', 0)}")
        print(f"  网络密度: {data.get('network_density', 0):.2f}")

        activities = data.get('activities', {})
        if isinstance(activities, dict) and 'rows' in activities:
            print(f"  相关活动: {len(activities['rows'])} 条")

        print(f"\n证据来源:")
        for evidence in result.get('evidence', []):
            print(f"  - {evidence['binding_id']}: {evidence['status']} ({evidence['duration_ms']}ms)")

    return result


async def test_location_summary_view(engine: ExecutionEngine, location_name: str):
    """测试地点文化资源汇总视图"""
    print("\n" + "="*60)
    print(f"测试视图: location_cultural_summary")
    print(f"参数: location_name = '{location_name}'")
    print("="*60)

    result = await engine.execute(
        view_id="location_cultural_summary",
        parameters={"location_name": location_name}
    )

    print(f"\n状态: {result['status']}")
    print(f"耗时: {result['metadata']['query_time_ms']} ms")

    if result['status'] == 'success':
        data = result['data']
        print(f"\n输出数据:")
        print(f"  地点名称: {data.get('location_name')}")

        assets = data.get('cultural_assets', {})
        if isinstance(assets, dict) and 'records' in assets:
            print(f"  文化资产: {len(assets['records'])} 个")

        people = data.get('local_people', {})
        if isinstance(people, dict) and 'records' in people:
            print(f"  当地人物: {len(people['records'])} 个")

        events = data.get('events', {})
        if isinstance(events, dict) and 'records' in events:
            print(f"  相关事件: {len(events['records'])} 个")

        print(f"  资产数量: {data.get('asset_count', 0)}")
        print(f"  人物数量: {data.get('people_count', 0)}")
        print(f"  文化丰富度: {data.get('cultural_richness_score', 0):.2f}")
        print(f"  丰富度等级: {data.get('richness_level', 'N/A')}")

        print(f"\n证据来源:")
        for evidence in result.get('evidence', []):
            print(f"  - {evidence['binding_id']}: {evidence['status']} ({evidence['duration_ms']}ms)")

    return result


async def main():
    """主测试流程"""
    print("="*60)
    print("CapaMesh 完整视图测试")
    print("="*60)

    # 初始化引擎
    engine = ExecutionEngine(
        views_dir="capamesh/views",
        bindings_dir="capamesh/bindings"
    )

    print(f"\n✅ 加载了 {len(engine.views)} 个视图")
    print(f"✅ 加载了 {len(engine.bindings)} 个绑定")

    # 获取样本数据
    print("\n获取测试数据...")
    samples = await get_sample_data()

    print(f"  文化资产: {samples.get('cultural_asset', 'N/A')}")
    print(f"  人物: {samples.get('person', 'N/A')}")
    print(f"  地点: {samples.get('location', 'N/A')}")

    results = {}

    # 测试文化资产视图
    if samples.get('cultural_asset'):
        try:
            results['cultural_asset'] = await test_cultural_asset_view(
                engine,
                samples['cultural_asset']
            )
        except Exception as e:
            print(f"\n❌ 文化资产视图测试失败: {e}")

    # 测试人物网络视图
    if samples.get('person'):
        try:
            results['person_network'] = await test_person_network_view(
                engine,
                samples['person']
            )
        except Exception as e:
            print(f"\n❌ 人物网络视图测试失败: {e}")

    # 测试地点汇总视图
    if samples.get('location'):
        try:
            results['location_summary'] = await test_location_summary_view(
                engine,
                samples['location']
            )
        except Exception as e:
            print(f"\n❌ 地点汇总视图测试失败: {e}")

    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)

    success_count = sum(1 for r in results.values() if r.get('status') == 'success')
    total_count = len(results)

    print(f"\n成功: {success_count}/{total_count}")

    for view_name, result in results.items():
        status = "✅" if result.get('status') == 'success' else "❌"
        time_ms = result.get('metadata', {}).get('query_time_ms', 0)
        print(f"  {status} {view_name}: {time_ms}ms")

    # 关闭连接
    engine.close()

    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
