"""
简化的完整流程测试：使用已有转录文本 -> 知识图谱 -> 可视化数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import json
from pathlib import Path

from app.services.agents.knowledge_agent import KnowledgeAgent
from app.services.agents.base_agent import AgentTask


def test_kg_pipeline():
    """测试知识图谱到可视化的流程"""

    print("=" * 60)
    print("🎯 知识图谱 -> 可视化测试")
    print("=" * 60)

    # === 使用已有的转录数据 ===
    transcript_file = Path("uploads/transcripts/doc_999.json")
    if not transcript_file.exists():
        print(f"❌ 转录文件不存在: {transcript_file}")
        return False

    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)

    # transcript_data 就是 segments 列表
    segments = transcript_data if isinstance(transcript_data, list) else transcript_data.get('segments', [])
    full_text = ' '.join([seg.get('text', '') for seg in segments])

    print(f"📁 数据源: {transcript_file}")
    print(f"📊 文本长度: {len(full_text)} 字符")
    print(f"📊 段落数: {len(segments)}")
    print()

    # === 步骤1: 构建知识图谱 ===
    print("🔗 步骤1: 构建知识图谱")
    print("-" * 60)

    knowledge_agent = KnowledgeAgent()
    kg_task = AgentTask(
        task_id='test_kg_pipeline_001',
        task_type='knowledge_graph',
        input_data={
            'text': full_text,
            'segments': segments,
            'doc_id': 'doc_999',
            'existing_entities': []
        }
    )

    try:
        kg_result = knowledge_agent.execute_task(kg_task)

        if not kg_result.success:
            print(f"❌ 知识图谱构建失败: {kg_result.errors}")
            return False

        print(f"✅ 知识图谱构建成功")
        kg_data = kg_result.output_data.get('knowledge_graph', {})

        entities = kg_data.get('entities', [])
        relations = kg_data.get('relations', [])

        print(f"   实体数: {len(entities)}")
        print(f"   关系数: {len(relations)}")
        print()

    except Exception as e:
        print(f"❌ 知识图谱构建异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # === 步骤2: 分析知识图谱质量 ===
    print("📊 步骤2: 知识图谱质量分析")
    print("-" * 60)

    if not entities:
        print("❌ 未提取到任何实体")
        return False

    # 实体类型分布
    entity_types = {}
    for entity in entities:
        etype = entity.get('entity_type', '未知')
        entity_types[etype] = entity_types.get(etype, 0) + 1

    print("实体分布:")
    for etype, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {etype}: {count}")

    # 关系类型分布
    if relations:
        relation_types = {}
        confidences = []
        for relation in relations:
            rtype = relation.get('relation_type', '未知')
            relation_types[rtype] = relation_types.get(rtype, 0) + 1
            conf = relation.get('confidence', 0)
            if conf > 0:
                confidences.append(conf)

        print("\n关系分布:")
        for rtype, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {rtype}: {count}")

        if confidences:
            print(f"\n置信度统计:")
            print(f"  - 平均: {sum(confidences) / len(confidences):.3f}")
            print(f"  - 最高: {max(confidences):.3f}")
            print(f"  - 最低: {min(confidences):.3f}")
            print(f"  - 唯一值数: {len(set(confidences))}")
    else:
        print("\n⚠️  未提取到关系")

    print()

    # === 步骤3: 生成前端可视化数据 ===
    print("🎨 步骤3: 生成前端可视化数据")
    print("-" * 60)

    # 构造前端需要的数据格式
    frontend_data = {
        'nodes': [],
        'links': [],
        'communities': kg_data.get('communities', [])
    }

    # 实体 -> nodes
    for entity in entities:
        frontend_data['nodes'].append({
            'id': entity.get('canonical_name', entity.get('name')),
            'name': entity.get('name'),
            'type': entity.get('entity_type'),
            'mentionCount': entity.get('mention_count', 1),
            'contexts': entity.get('contexts', [])[:3]  # 前3个上下文
        })

    # 关系 -> links
    for relation in relations:
        frontend_data['links'].append({
            'source': relation.get('subject'),
            'target': relation.get('object'),
            'type': relation.get('relation_type'),
            'confidence': relation.get('confidence', 1.0),
            'context': relation.get('context', '')
        })

    # 保存为 JSON
    output_path = Path('test_output_kg_pipeline.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 可视化数据已生成: {output_path}")
    print(f"   节点数: {len(frontend_data['nodes'])}")
    print(f"   边数: {len(frontend_data['links'])}")
    print(f"   社区数: {len(frontend_data.get('communities', []))}")

    # 显示社区主题
    communities = frontend_data.get('communities', [])
    if communities:
        print(f"\n社区主题:")
        for comm in communities[:5]:  # 显示前5个
            topic = comm.get('topic_name', f"社区{comm.get('community_id', '?')}")
            members = comm.get('members', [])
            print(f"  - {topic}: {len(members)} 个成员")

    print()

    # === 总结 ===
    print("=" * 60)
    print("🎉 知识图谱流程测试通过！")
    print("=" * 60)
    print("\n后续步骤:")
    print("1. 将 test_output_kg_pipeline.json 加载到前端")
    print("2. 在浏览器中查看 KnowledgeGraphViewer 组件")
    print("3. 测试交互功能（缩放、拖拽、过滤）")
    print()

    return True


if __name__ == "__main__":
    success = test_kg_pipeline()
    sys.exit(0 if success else 1)
