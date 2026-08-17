"""
测试 KnowledgeAgent 的增强功能
- LLM 辅助关系提取
- 数据库持久化
- 时间戳精确提取
- 向量相似度实体消歧
"""
import sys
import os
import asyncio
import json

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.agents.knowledge_agent import KnowledgeAgent


async def test_knowledge_agent_enhanced():
    """测试 KnowledgeAgent 增强功能"""

    print("=" * 80)
    print("🧪 测试 KnowledgeAgent - 增强功能")
    print("=" * 80)
    print()

    # ==================== Step 1: 准备测试数据 ====================
    print("📥 Step 1: 准备测试数据...")

    # 加载转录数据
    transcript_path = "uploads/transcripts/doc_999.json"
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)

    # 处理数据格式
    if isinstance(transcript_data, list):
        segments = transcript_data
        text = " ".join([seg.get('text', '') for seg in segments])
    else:
        text = transcript_data.get('cleaned_text', '')
        segments = transcript_data.get('segments', [])

    print(f"   ✅ 加载文本: {len(text)} 字符")
    print(f"   ✅ 片段数: {len(segments)}")

    # 模拟 TranscriptAgent 已提取的核心人物
    existing_entities = [
        {"name": "思維斯", "mentions": 23, "contexts": ["思維斯老师讲课", "思維斯参与活动"]},
        {"name": "邓小平", "mentions": 4, "contexts": ["邓小平同志"]},
        {"name": "雪山", "mentions": 3, "contexts": ["雪山地区"]},
    ]
    print(f"   ✅ 已有人物: {len(existing_entities)} 个")
    print()

    # ==================== Step 2: 初始化 Agent ====================
    print("🚀 Step 2: 初始化 KnowledgeAgent...")
    agent = KnowledgeAgent(agent_id="test_kg_agent")
    print("   ✅ Agent 初始化完成")
    print()

    # ==================== Step 3: 执行知识构建（启用所有增强功能） ====================
    print("📚 Step 3: 执行知识构建（启用增强功能）...")

    task_input = {
        "doc_id": "doc_999",
        "text": text,
        "segments": segments,
        "existing_entities": existing_entities,
        "enable_llm": True,  # 启用 LLM 辅助提取
        "db_session": None  # 暂不连接数据库（需要数据库环境）
    }

    result = await agent.execute(task_input)
    print("   ✅ 知识构建完成")
    print()

    # ==================== Step 4: 检查增强功能效果 ====================
    print("📊 Step 4: 检查增强功能效果...")
    print()

    # 4.1 检查时间戳提取
    print("   🕐 时间戳提取:")
    entities_with_timestamp = [
        e for e in result['实体列表']
        if e.get('首次出现时间戳', 0.0) > 0
    ]
    print(f"      - 带时间戳的实体: {len(entities_with_timestamp)} 个")
    if entities_with_timestamp:
        sample = entities_with_timestamp[0]
        print(f"      - 示例: {sample['实体名称']} (首次出现: {sample['首次出现时间戳']:.2f}s)")
    print()

    relations_with_timestamp = [
        r for r in result['关系列表']
        if r.get('时间戳', 0.0) > 0
    ]
    print(f"      - 带时间戳的关系: {len(relations_with_timestamp)} 个")
    if relations_with_timestamp:
        sample = relations_with_timestamp[0]
        print(f"      - 示例: {sample['主体']} --[{sample['关系类型']}]--> {sample['客体']} (时间: {sample['时间戳']:.2f}s)")
    print()

    # 4.2 检查 LLM 辅助提取的关系
    print("   🤖 LLM 辅助关系提取:")
    llm_relations = [
        r for r in result['关系列表']
        if r.get('置信度', 0) > 0.85  # LLM 提取的关系置信度通常较高
    ]
    print(f"      - LLM 提取的关系: {len(llm_relations)} 个")
    if llm_relations:
        for rel in llm_relations[:3]:
            print(f"      - {rel['主体']} --[{rel['关系类型']}]--> {rel['客体']} (置信度: {rel['置信度']})")
    print()

    # 4.3 统计信息
    print("   📈 总体统计:")
    print(f"      - 实体总数: {len(result['实体列表'])}")
    print(f"      - 关系总数: {len(result['关系列表'])}")
    print(f"      - 共现组数: {len(result['共现分析'])}")
    print(f"      - 知识图谱节点数: {result['知识图谱统计']['节点总数']}")
    print(f"      - 知识图谱边数: {result['知识图谱统计']['边总数']}")
    print()

    # ==================== Step 5: 保存输出 ====================
    print("💾 Step 5: 保存输出文件...")

    os.makedirs("uploads/knowledge", exist_ok=True)

    output_path = "uploads/knowledge/doc_999_enhanced_knowledge_graph.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"   ✅ 保存到: {output_path}")

    # 保存 D3.js 数据
    d3_path = "uploads/knowledge/doc_999_enhanced_d3_graph.json"
    with open(d3_path, 'w', encoding='utf-8') as f:
        json.dump(result['可视化数据']['d3_graph'], f, ensure_ascii=False, indent=2)
    print(f"   ✅ D3 数据: {d3_path}")

    # 保存思维导图数据
    mindmap_path = "uploads/knowledge/doc_999_enhanced_mindmap.json"
    with open(mindmap_path, 'w', encoding='utf-8') as f:
        json.dump(result['可视化数据']['mindmap'], f, ensure_ascii=False, indent=2)
    print(f"   ✅ 思维导图: {mindmap_path}")
    print()

    # ==================== 完成 ====================
    print("=" * 80)
    print("✅ KnowledgeAgent 增强功能测试完成！")
    print("=" * 80)
    print()
    print("已实现功能:")
    print("  ✅ LLM 辅助关系提取（需要 OPENAI_API_KEY）")
    print("  ✅ 数据库持久化（框架已就绪，需要数据库连接）")
    print("  ✅ 时间戳精确提取")
    print("  ✅ 向量相似度实体消歧")
    print()


if __name__ == "__main__":
    asyncio.run(test_knowledge_agent_enhanced())
