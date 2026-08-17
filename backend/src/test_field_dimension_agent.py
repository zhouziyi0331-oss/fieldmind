"""
测试 FieldDimensionAgent
验证田野维度解构功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.agents.field_dimension_agent import FieldDimensionAgent


def test_field_dimension_agent():
    """测试田野维度解构Agent"""

    # 准备测试数据
    test_text = """
李家村位于山区，全村共有200户人家。村支书张建国介绍说，近年来村里的主要收入来源是外出打工和种植经济作物。
村委会每月召开一次村民代表大会，讨论村里的重要事务。去年关于土地承包的纠纷，通过村干部调解得到了解决。
村里有80%的青壮年外出务工，留守的老人主要种植玉米和水稻。山林资源比较丰富，但环境保护意识还需要加强。
村里成立了农业合作社，负责统一采购种子和化肥。村长李建华说，今年打算引进新的灌溉设备，提高农作物产量。
"""

    # 模拟EntityRelationAgent的输出
    entity_relations = {
        'entities': [
            {'name': '李家村', 'type': 'location'},
            {'name': '张建国', 'type': 'person'},
            {'name': '村委会', 'type': 'organization'},
            {'name': '农业合作社', 'type': 'organization'},
            {'name': '李建华', 'type': 'person'}
        ],
        'relations': [
            {'source': '张建国', 'target': '李家村', 'relation': 'works_at'}
        ],
        'entity_types': {
            'person': ['张建国', '李建华'],
            'location': ['李家村'],
            'organization': ['村委会', '农业合作社']
        }
    }

    # 启用的Skills
    enabled_skills = ['community_governance', 'livelihood_ecology']

    # 准备输入
    input_data = {
        'text_content': test_text,
        'enabled_skills': enabled_skills,
        'entity_relations': entity_relations
    }

    # 创建Agent并执行
    agent = FieldDimensionAgent()
    print("🧪 测试 FieldDimensionAgent")
    print("=" * 60)

    result = agent.execute(input_data)

    # 验证结果
    print(f"\n✅ Agent执行状态: {'成功' if result.success else '失败'}")
    print(f"⏱️  执行耗时: {result.execution_time:.3f}秒")
    print(f"📊 置信度: {result.confidence:.2f}")

    if result.success:
        data = result.data
        print(f"\n📈 分析结果:")
        print(f"   - 总维度数: {data['total_dimensions']}")
        print(f"   - 总匹配数: {data['total_matches']}")
        print(f"   - 相关实体: {data['entity_count']}")

        # 显示各个维度的分析结果
        print(f"\n🔍 维度分析详情:")
        for dim_id, dim_data in data['dimensions'].items():
            print(f"\n   [{dim_data['skill_name']}] {dim_data['dimension_name']}")
            print(f"   - 匹配数: {dim_data['matched_count']}")
            print(f"   - 相关实体: {dim_data['related_entities']}")
            if dim_data['contexts']:
                print(f"   - 上下文示例: {dim_data['contexts'][0][:50]}...")

        # 显示摘要
        print(f"\n📝 分析摘要:")
        summary = data['summary']
        print(f"   - 使用Skill数: {summary['total_skills']}")

        print(f"\n   🏆 Top维度:")
        for top_dim in summary['top_dimensions'][:3]:
            print(f"      - {top_dim['name']} ({top_dim['skill']}): {top_dim['matches']}次匹配")

        print(f"\n   📊 Skill统计:")
        for skill_id, stats in summary['skill_stats'].items():
            print(f"      - {stats['skill_name']}: {stats['dimension_count']}个维度, {stats['total_matches']}次匹配")

    else:
        print(f"\n❌ 错误信息: {result.errors}")

    print("\n" + "=" * 60)

    # 断言验证
    assert result.success, "Agent执行应该成功"
    assert result.data['total_dimensions'] > 0, "应该有维度分析结果"
    assert result.data['total_matches'] > 0, "应该有匹配的关键词"
    assert result.execution_time < 1.0, "执行时间应该小于1秒"

    print("✅ 所有测试通过！")
    return True


if __name__ == '__main__':
    try:
        test_field_dimension_agent()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
