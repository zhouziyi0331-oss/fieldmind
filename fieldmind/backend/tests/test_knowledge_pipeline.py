"""
知识构建流水线端到端测试
End-to-End Test for Knowledge Pipeline
"""

import pytest
import asyncio
from datetime import datetime


# 测试文本（史记风格样本）
TEST_TEXT = """
秦始皇二十六年，初并天下，置郡县。始皇自以为德高三皇，功过五帝，乃更号称皇帝。

丞相李斯，楚上蔡人也。年少时为郡小吏，见吏舍厕中鼠食不洁，近人犬，数惊恐之。
斯入仓，观仓中鼠，食积粟，居大庑之下，不见人犬之忧。於是李斯乃叹曰："人之贤不肖譬如鼠矣，在所自处耳！"

李斯少为上蔡郡小吏，而后学帝王之术。秦王政立李斯为丞相，辅佐秦王统一天下。

秦始皇三十四年，丞相李斯上书曰："今陛下创大业，建万世之功，固非愚儒所知。"始皇可其议。

李斯与赵高同为秦始皇重臣。始皇崩于沙丘，李斯与赵高谋立胡亥为二世皇帝。
后赵高陷害李斯，二世三年，李斯被腰斩于咸阳市。
"""


@pytest.mark.asyncio
async def test_complete_pipeline():
    """测试完整的九步流水线"""
    from app.services.knowledge_pipeline.orchestrator import KnowledgePipelineOrchestrator

    # 创建编排器
    orchestrator = KnowledgePipelineOrchestrator(
        document_id="test_doc_001",
        project_id="test_project_001",
        user_id="test_user_001",
        db_session=None,  # 测试中暂不持久化
        llm_service=None
    )

    # 执行流水线
    result = await orchestrator.execute(
        text=TEST_TEXT,
        enable_statistical_cleaning=True,
        enable_llm_cleaning=False,
        max_retries=1
    )

    # 验证执行成功
    assert result['status'] == 'completed'
    assert 'execution_id' in result
    assert 'results' in result
    assert len(result['errors']) == 0

    # 验证每一步都完成
    results = result['results']
    assert 'cleaning' in results
    assert 'structure' in results
    assert 'entity' in results
    assert 'event' in results
    assert 'relation' in results
    assert 'ontology' in results
    assert 'inference' in results
    assert 'knowledge' in results
    assert 'reader' in results

    print("\n✅ 测试通过：完整流水线执行成功")
    return result


if __name__ == "__main__":
    print("=" * 80)
    print("知识构建流水线端到端测试")
    print("=" * 80)

    # 运行完整流水线测试
    result = asyncio.run(test_complete_pipeline())

    print("\n" + "=" * 80)
    print("🎉 测试通过！")
    print("=" * 80)

    # 输出最终统计
    final_results = result['results']
    print("\n最终流水线统计：")
    print(f"  • 清洗修改: {final_results['cleaning']['statistics']['total_changes']} 处")
    print(f"  • 结构节点: {final_results['structure']['node_count']} 个")
    print(f"  • 实体数量: {final_results['entity']['statistics']['total_entities']} 个")
    print(f"  • 事件数量: {final_results['event']['statistics']['total_events']} 个")
    print(f"  • 关系数量: {final_results['relation']['statistics']['total_relations']} 个")
    print(f"  • 概念数量: {final_results['ontology']['statistics']['concept_count']} 个")
    print(f"  • 推理发现: {final_results['inference']['statistics']['total_findings']} 个")
    print(f"  • 知识单元: {final_results['knowledge']['statistics']['total_units']} 个")
    print(f"  • Wiki页面: {final_results['reader']['metadata']['wiki_pages']} 个")
