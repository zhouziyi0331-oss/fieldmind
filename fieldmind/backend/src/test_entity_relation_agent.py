"""
测试 EntityRelationAgent

验证实体关系分析专员的功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.entity_relation_agent import EntityRelationAgent


def test_entity_relation_agent():
    """测试实体关系分析Agent"""

    print("=" * 60)
    print("测试 EntityRelationAgent - 实体关系分析专员")
    print("=" * 60)

    # 创建Agent实例
    agent = EntityRelationAgent()

    # 准备测试文本（典型的田野调查访谈片段）
    test_text = """
    李家村位于华北平原，距离县城约15公里。村支书张建国是本村人，今年58岁，
    在村里工作已经20多年。他说："咱们村现在主要靠外出打工赚钱，种地收入很少。"

    张建国的儿子张小明在北京打工，每年春节才回来一次。村里像张小明这样的年轻人有很多，
    大约占全村人口的40%。村委会主任李建华和张建国是多年的同事，两人一起管理村务。

    村里有个养殖合作社，由王大爷创办，主要养殖肉鸡。合作社位于村东头，
    现在有20多户村民参与。李建华支持合作社的发展，还帮助申请了政府补贴。

    每年正月十五，李家村都会举办元宵节庆祝活动，这是村里最重要的传统节日。
    张建国和李建华会组织村民大会，商议村里的大事。
    """

    # 执行分析
    print("\n📄 测试文本:")
    print(test_text[:200] + "...\n")

    input_data = {
        'document_id': 1,
        'text_content': test_text,
        'entities': []  # 模拟没有预提取实体的情况
    }

    print("🤖 开始执行 Agent...\n")
    result = agent.execute(input_data)

    # 输出结果
    print("\n" + "=" * 60)
    print("执行结果")
    print("=" * 60)

    print(f"\n✅ 执行状态: {'成功' if result.success else '失败'}")
    print(f"⏱️  执行耗时: {result.execution_time:.3f} 秒")
    print(f"🎯 置信度: {result.confidence:.2f}")

    if result.errors:
        print(f"\n❌ 错误: {result.errors}")

    if result.warnings:
        print(f"\n⚠️  警告:")
        for warning in result.warnings:
            print(f"   - {warning}")

    # 显示提取的实体
    entities = result.data.get('entities', [])
    print(f"\n👥 提取的实体 (共 {len(entities)} 个):")
    for i, entity in enumerate(entities[:10], 1):  # 只显示前10个
        print(f"   {i}. {entity['name']}")
        print(f"      类型: {entity['type']}")
        print(f"      提及次数: {entity['mentions']}")
        if entity['contexts']:
            print(f"      上下文: {entity['contexts'][0][:50]}...")

    # 显示关系
    relations = result.data.get('relations', [])
    print(f"\n🔗 提取的关系 (共 {len(relations)} 个):")
    for i, relation in enumerate(relations[:10], 1):  # 只显示前10个
        print(f"   {i}. {relation['source']} --[{relation['relation']}]--> {relation['target']}")
        print(f"      类型: {relation['relation_type']}")
        print(f"      上下文: {relation['context']}")

    # 显示实体类型统计
    entity_types = result.data.get('entity_types', {})
    print(f"\n📊 实体类型统计:")
    for entity_type, count in entity_types.items():
        print(f"   {entity_type}: {count}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

    # 返回结果供进一步验证
    return result


def test_with_pre_entities():
    """测试带预提取实体的情况"""

    print("\n\n" + "=" * 60)
    print("测试 EntityRelationAgent - 带预提取实体")
    print("=" * 60)

    agent = EntityRelationAgent()

    test_text = "张书记在李家村工作多年，他领导村委会处理各项事务。"

    # 模拟动态发现引擎提取的实体
    pre_entities = [
        {'entity': '张书记', 'count': 2, 'type': 'person'},
        {'entity': '李家村', 'count': 3, 'type': 'location'},
        {'entity': '村委会', 'count': 1, 'type': 'organization'}
    ]

    input_data = {
        'document_id': 2,
        'text_content': test_text,
        'entities': pre_entities
    }

    print(f"\n📄 测试文本: {test_text}")
    print(f"\n📦 预提取实体: {len(pre_entities)} 个")

    result = agent.execute(input_data)

    print(f"\n✅ 执行状态: {'成功' if result.success else '失败'}")
    print(f"⏱️  执行耗时: {result.execution_time:.3f} 秒")

    entities = result.data.get('entities', [])
    relations = result.data.get('relations', [])

    print(f"\n👥 最终实体: {len(entities)} 个")
    for entity in entities:
        print(f"   - {entity['name']} ({entity['type']})")

    print(f"\n🔗 识别的关系: {len(relations)} 个")
    for relation in relations:
        print(f"   - {relation['source']} --[{relation['relation']}]--> {relation['target']}")

    print("\n" + "=" * 60)

    return result


if __name__ == '__main__':
    # 运行测试
    result1 = test_entity_relation_agent()
    result2 = test_with_pre_entities()

    # 验证测试是否通过
    if result1.success and result2.success:
        print("\n🎉 所有测试通过！EntityRelationAgent 运行正常。")
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)
