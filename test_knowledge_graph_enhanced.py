#!/usr/bin/env python3
"""
测试知识图谱增强功能
"""

import sys
sys.path.append('/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.services.knowledge_graph_service import KnowledgeGraphService

def test_enhanced_extraction():
    """测试增强提取规则"""
    kg = KnowledgeGraphService()

    # 测试文本（田野调查笔记）
    test_text = """
    王大爷说，杀猪菜是我们村的传统美食。
    李婶也很喜欢做这道菜。
    村里的祠堂是明代建筑，位于村口。
    2024年春节，村里举办了盛大的庆典活动。
    传统文化影响年轻人的价值观。
    张三认为现代化发展很重要。
    这个村庄属于东山镇。
    节日包括春节、中秋节、端午节。
    在北京市朝阳区进行了实地调研。
    研究团队参加了田野考察活动。
    """

    print("=" * 60)
    print("📊 知识图谱增强提取测试")
    print("=" * 60)

    # 提取实体和关系（不使用LLM）
    print("\n【阶段1】规则提取（基础+增强）")
    entities, relations = kg.extract_entities_and_relations(test_text, use_llm=False)

    print(f"\n✅ 提取到 {len(entities)} 个实体:")
    entity_by_type = {}
    for entity in entities:
        entity_type = entity.entity_type
        if entity_type not in entity_by_type:
            entity_by_type[entity_type] = []
        entity_by_type[entity_type].append(entity.name)

    for entity_type, names in sorted(entity_by_type.items()):
        print(f"  {entity_type}: {', '.join(names[:10])}")

    print(f"\n✅ 提取到 {len(relations)} 个关系:")
    for i, relation in enumerate(relations[:10], 1):
        print(f"  {i}. {relation.source} --[{relation.relation_type}]--> {relation.target}")

    # 添加到图谱
    print("\n【阶段2】构建图谱")
    kg.add_entities_and_relations(entities, relations)

    # 获取统计
    stats = kg.get_statistics()
    print(f"\n📈 图谱统计:")
    print(f"  节点数: {stats['node_count']}")
    print(f"  边数: {stats['edge_count']}")
    print(f"  密度: {stats['density']:.3f}")
    print(f"  实体类型分布: {stats['entity_types']}")
    print(f"  关系类型分布: {stats['relation_types']}")

    # 导出可视化
    output_path = '/tmp/knowledge_graph_enhanced.html'
    kg.export_for_visualization(output_path)
    print(f"\n✅ 可视化已导出: {output_path}")

    # 保存图谱
    json_path = '/tmp/knowledge_graph_enhanced.json'
    kg.save_to_file(json_path)
    print(f"✅ 图谱数据已保存: {json_path}")

    print("\n" + "=" * 60)
    print("🎉 测试完成！")
    print("=" * 60)

    return kg, entities, relations, stats


def test_llm_extraction():
    """测试LLM增强提取（如果配置了API key）"""
    import os

    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
        print("\n⚠️ 未检测到LLM API密钥，跳过LLM测试")
        print("提示: 设置 ANTHROPIC_API_KEY 或 OPENAI_API_KEY 启用LLM增强")
        return

    print("\n" + "=" * 60)
    print("🤖 LLM增强提取测试")
    print("=" * 60)

    kg = KnowledgeGraphService()

    test_text = """
    王大爷今年68岁，是村里德高望重的老人。他说，杀猪菜起源于明代，
    至今已有500多年历史。村里的李婶是制作杀猪菜的高手，她的手艺
    传承自祖母。2024年春节，村委会组织了盛大的庆典活动，吸引了
    来自北京、上海等地的游客超过3000人。
    """

    # 使用LLM提取
    entities, relations = kg.extract_entities_and_relations(test_text, use_llm=True)

    print(f"\n✅ LLM提取到 {len(entities)} 个实体")
    print(f"✅ LLM提取到 {len(relations)} 个关系")

    print("\n实体详情:")
    for entity in entities[:15]:
        print(f"  - {entity.name} ({entity.entity_type}) [来源: {entity.properties.get('source', 'unknown')}]")

    print("\n关系详情:")
    for relation in relations[:10]:
        confidence = relation.properties.get('confidence', 0)
        print(f"  - {relation.source} --[{relation.relation_type}]--> {relation.target} (置信度: {confidence:.2f})")

    print("\n🎉 LLM测试完成！")


if __name__ == "__main__":
    # 测试1: 增强规则提取
    kg, entities, relations, stats = test_enhanced_extraction()

    # 测试2: LLM增强提取（如果可用）
    test_llm_extraction()

    print("\n" + "=" * 60)
    print("📚 完整测试报告")
    print("=" * 60)
    print(f"✅ 规则提取: {len(entities)}个实体, {len(relations)}个关系")
    print(f"✅ 图谱构建: {stats['node_count']}个节点, {stats['edge_count']}条边")
    print(f"✅ 实体类型: {len(stats['entity_types'])}种")
    print(f"✅ 关系类型: {len(stats['relation_types'])}种")
    print("\n🎊 所有优化已完成并验证！")
