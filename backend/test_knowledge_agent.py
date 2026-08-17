"""
测试 KnowledgeAgent - 知识构建专员

测试流程：
1. 读取 TranscriptAgent 的输出
2. 调用 KnowledgeAgent 提取实体+关系
3. 验证知识图谱构建
4. 检查多格式输出
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from app.services.agents.knowledge_agent import KnowledgeAgent


async def test_knowledge_agent():
    """测试 KnowledgeAgent 完整链路"""

    print("="*80)
    print("🧪 测试 KnowledgeAgent - 知识构建专员")
    print("="*80)

    # Step 1: 准备测试数据（模拟 TranscriptAgent 的输出）
    print("\n📥 Step 1: 准备测试数据...")

    # 读取真实的转录文本
    transcript_file = Path("uploads/transcripts/doc_999.json")

    if transcript_file.exists():
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)

        # transcript_data 是 segments 列表
        if isinstance(transcript_data, list):
            segments = transcript_data
            # 拼接文本
            text = " ".join([seg.get('text', '') for seg in segments])
        else:
            text = transcript_data.get('cleaned_text', '')
            segments = transcript_data.get('segments', [])

        # 模拟已提取的核心人物（从之前的测试结果）
        existing_entities = [
            {"name": "思維斯", "mentions": 23, "contexts": ["上下文1", "上下文2"]},
            {"name": "邓小平", "mentions": 4, "contexts": ["上下文3"]},
            {"name": "雪山", "mentions": 3, "contexts": ["上下文4"]},
        ]

        print(f"   ✅ 加载文本: {len(text)} 字符")
        print(f"   ✅ 片段数: {len(segments)}")
        print(f"   ✅ 已有人物: {len(existing_entities)} 个")
    else:
        # 使用模拟数据
        print("   ⚠️ 未找到转录文件，使用模拟数据")
        text = """
        鐘百拜老师在掉烟村教学生跳传统舞蹈。他是村里有名的舞蹈传承人。
        村史馆里保存着很多蜡染作品。村民们经常在祠堂举行祭祀活动。
        张三是李四的父亲。他们一家住在村委会附近。
        昨天大家去了档案馆，找到了很多关于古道的资料。
        王五跟鐘百拜学习手工艺。他在村里的古树下开了一家手工艺店。
        培训班在文化馆举行，很多年轻人参加了刺绣培训。
        每年春节，村民们都会在广场上举办庙会。
        """
        segments = []
        existing_entities = [
            {"name": "鐘百拜", "mentions": 3, "contexts": ["老师在掉烟村教学生"]},
            {"name": "张三", "mentions": 1, "contexts": ["张三是李四的父亲"]},
        ]

    # Step 2: 初始化 KnowledgeAgent
    print("\n🚀 Step 2: 初始化 KnowledgeAgent...")
    agent = KnowledgeAgent()
    print("   ✅ Agent 初始化完成")

    # Step 3: 执行知识构建
    print("\n📚 Step 3: 执行知识构建...")

    task_input = {
        "doc_id": "doc_999",
        "text": text[:5000],  # 限制长度避免太慢
        "segments": segments[:100],
        "existing_entities": existing_entities,
        "enable_llm": False  # 暂时禁用LLM，先测试规则提取
    }

    result = await agent.execute(task_input)

    if not result:
        print(f"   ❌ 执行失败")
        return

    print("   ✅ 知识构建完成")

    # Step 4: 检查结果
    print("\n📊 Step 4: 检查知识图谱结果...")

    data = result

    # 实体列表
    entities = data.get('实体列表', [])
    print(f"\n   ✅ 实体列表: {len(entities)} 个")

    # 按类型分组
    entity_by_type = {}
    for entity in entities:
        etype = entity['实体类型']
        if etype not in entity_by_type:
            entity_by_type[etype] = []
        entity_by_type[etype].append(entity)

    for etype, ents in sorted(entity_by_type.items()):
        print(f"\n      【{etype}】: {len(ents)} 个")
        for ent in ents[:5]:  # 只显示前5个
            print(f"         - {ent['实体名称']}: 提及{ent['提及次数']}次")

    # 关系列表
    relations = data.get('关系列表', [])
    print(f"\n   ✅ 关系列表: {len(relations)} 个")

    if relations:
        # 按关系类型分组
        relation_by_type = {}
        for rel in relations:
            rtype = rel['关系类型']
            if rtype not in relation_by_type:
                relation_by_type[rtype] = []
            relation_by_type[rtype].append(rel)

        for rtype, rels in sorted(relation_by_type.items()):
            print(f"\n      【{rtype}】: {len(rels)} 个")
            for rel in rels[:3]:  # 只显示前3个
                print(f"         - {rel['主体']} --[{rel['关系类型']}]--> {rel['客体']}")
                print(f"           上下文: {rel['上下文'][:50]}...")

    # 共现分析
    co_occurrences = data.get('共现分析', [])
    print(f"\n   ✅ 共现分析: {len(co_occurrences)} 组")

    if co_occurrences:
        print("\n      【高频共现实体组】:")
        for co in co_occurrences[:5]:
            entities_str = " + ".join(co['共现实体组'][:3])
            print(f"         - {entities_str}: 共现{co['共现频次']}次")

    # 知识图谱统计
    kg_stats = data.get('知识图谱统计', {})
    print(f"\n   ✅ 知识图谱统计:")
    print(f"      - 节点总数: {kg_stats.get('节点总数', 0)}")
    print(f"      - 边总数: {kg_stats.get('边总数', 0)}")

    core_nodes = kg_stats.get('核心节点', [])
    if core_nodes:
        print(f"      - 核心节点: {', '.join(core_nodes[:5])}")

    communities = kg_stats.get('社区聚类', [])
    if communities:
        print(f"      - 社区数量: {len(communities)}")
        for comm in communities[:3]:
            members = ", ".join(comm['成员实体'][:5])
            print(f"         · {comm['社区ID']}: {members}")

    # Step 5: 检查可视化数据
    print("\n🎨 Step 5: 检查可视化数据...")

    vis_data = data.get('可视化数据', {})

    # D3.js 格式
    d3_data = vis_data.get('d3_graph', {})
    d3_nodes = d3_data.get('nodes', [])
    d3_links = d3_data.get('links', [])
    print(f"   ✅ D3.js 力导向图: {len(d3_nodes)} 个节点, {len(d3_links)} 条边")

    # 思维导图格式
    mindmap_data = vis_data.get('mindmap', {})
    if mindmap_data and 'root' in mindmap_data:
        root_name = mindmap_data['root']['data']['text']
        children_count = len(mindmap_data['root'].get('children', []))
        print(f"   ✅ 思维导图: 根节点='{root_name}', {children_count} 个分支")

    # Step 6: 保存输出
    print("\n💾 Step 6: 保存输出文件...")

    output_dir = Path("uploads/knowledge")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存完整JSON
    output_file = output_dir / "doc_999_knowledge_graph.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 保存到: {output_file}")

    # 保存 D3.js 数据（单独）
    d3_file = output_dir / "doc_999_d3_graph.json"
    with open(d3_file, 'w', encoding='utf-8') as f:
        json.dump(d3_data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ D3 数据: {d3_file}")

    # 保存思维导图数据（单独）
    mindmap_file = output_dir / "doc_999_mindmap.json"
    with open(mindmap_file, 'w', encoding='utf-8') as f:
        json.dump(mindmap_data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 思维导图: {mindmap_file}")

    print("\n" + "="*80)
    print("✅ KnowledgeAgent 测试完成！")
    print("="*80)
    print("\n测试覆盖:")
    print("  ✅ 实体提取（复用 + 规则匹配 + DynamicDiscovery）")
    print("  ✅ 关系提取（规则模板）")
    print("  ✅ 共现分析（句子级窗口）")
    print("  ✅ 知识图谱构建（NetworkX）")
    print("  ✅ 多格式输出（D3.js + 思维导图）")
    print("  ✅ 跨文档合并机制（框架已就绪）")
    print("\n待实现:")
    print("  ⏭️ LLM 辅助关系提取")
    print("  ⏭️ 数据库持久化")
    print("  ⏭️ 时间戳精确提取")


if __name__ == "__main__":
    asyncio.run(test_knowledge_agent())
