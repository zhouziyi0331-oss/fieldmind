"""
完整流程测试：音频 -> 转录 -> 知识图谱 -> 可视化数据
测试整个 FieldMind 处理流程
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import asyncio
import json
from pathlib import Path

from app.services.agents.transcript_agent import TranscriptAgent
from app.services.agents.knowledge_agent import KnowledgeAgent
from app.services.agents.base_agent import AgentTask


def test_complete_pipeline():
    """测试完整流程"""

    # === 选择测试音频 ===
    test_audio = Path("../uploads/project_1/real_voice_test.mp3")
    if not test_audio.exists():
        print(f"❌ 测试音频不存在: {test_audio}")
        return False

    print("=" * 60)
    print("🎯 完整流程测试")
    print("=" * 60)
    print(f"📁 测试音频: {test_audio}")
    print(f"📊 文件大小: {test_audio.stat().st_size / 1024:.2f} KB")
    print()

    # === 步骤1: 音频转录 ===
    print("🎤 步骤1: 音频转录")
    print("-" * 60)

    transcript_agent = TranscriptAgent()

    # 使用 AgentTask 封装输入
    task = AgentTask(
        task_id='test_complete_001',
        task_type='transcription',
        input_data={
            'file_path': str(test_audio),
            'enable_metrics': True,
            'auto_trigger_knowledge': True
        }
    )

    try:
        transcript_result = transcript_agent.execute_task(task)

        if not transcript_result.success:
            print(f"❌ 转录失败: {transcript_result.errors}")
            return False

        # 从 output_data 的 transcript 字段获取数据
        transcript_data = transcript_result.output_data.get('transcript', {})
        cleaned_text = transcript_data.get('full_text', '')
        segments = transcript_data.get('segments', [])

        print(f"✅ 转录成功")
        print(f"   文本长度: {len(cleaned_text)} 字符")
        print(f"   段落数: {len(segments)}")

        # 检查是否自动生成了知识图谱
        if 'knowledge_graph' in transcript_result.output_data:
            kg_result_data = transcript_result.output_data['knowledge_graph']
            if isinstance(kg_result_data, dict):
                print(f"   知识图谱: 实体 {len(kg_result_data.get('entities', []))}, 关系 {len(kg_result_data.get('relations', []))}")
            else:
                print(f"   ⚠️  知识图谱格式异常: {type(kg_result_data)}")
        else:
            print("   ⚠️  未自动生成知识图谱")

        print()

    except Exception as e:
        print(f"❌ 转录异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # === 步骤2: 手动测试知识图谱（如果自动触发失败）===
    if 'knowledge_graph' not in transcript_result.output_data:
        print("🔗 步骤2: 手动构建知识图谱")
        print("-" * 60)

        knowledge_agent = KnowledgeAgent()
        kg_task = AgentTask(
            task_id='test_complete_kg_001',
            task_type='knowledge_graph',
            input_data={
                'text': cleaned_text,
                'segments': segments,
                'doc_id': 'test_doc_complete',
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
            print(f"   实体数: {len(kg_data.get('entities', []))}")
            print(f"   关系数: {len(kg_data.get('relations', []))}")
            print()

        except Exception as e:
            print(f"❌ 知识图谱构建异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        kg_data = transcript_result.output_data.get('knowledge_graph', {})

    # === 步骤3: 分析知识图谱质量 ===
    print("📊 步骤3: 知识图谱质量分析")
    print("-" * 60)

    entities = kg_data.get('entities', [])
    relations = kg_data.get('relations', [])

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
            confidences.append(conf)

        print("\n关系分布:")
        for rtype, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {rtype}: {count}")

        print(f"\n置信度统计:")
        print(f"  - 平均: {sum(confidences) / len(confidences):.3f}")
        print(f"  - 最高: {max(confidences):.3f}")
        print(f"  - 最低: {min(confidences):.3f}")
        print(f"  - 唯一值数: {len(set(confidences))}")
    else:
        print("\n⚠️  未提取到关系")

    print()

    # === 步骤4: 生成前端可视化数据 ===
    print("🎨 步骤4: 生成前端可视化数据")
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
    output_path = Path('test_output_complete_pipeline.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(frontend_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 可视化数据已生成: {output_path}")
    print(f"   节点数: {len(frontend_data['nodes'])}")
    print(f"   边数: {len(frontend_data['links'])}")
    print(f"   社区数: {len(frontend_data.get('communities', []))}")
    print()

    # === 总结 ===
    print("=" * 60)
    print("🎉 完整流程测试通过！")
    print("=" * 60)
    print("\n后续步骤:")
    print("1. 将 test_output_complete_pipeline.json 加载到前端")
    print("2. 在浏览器中查看 KnowledgeGraphViewer 组件")
    print("3. 测试交互功能（缩放、拖拽、过滤）")
    print()

    return True


if __name__ == "__main__":
    # 不需要 asyncio.run，因为所有方法都是同步的
    success = test_complete_pipeline()
    sys.exit(0 if success else 1)
