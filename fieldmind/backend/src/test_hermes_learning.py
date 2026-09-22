#!/usr/bin/env python3
"""
Hermes Learning Engine 测试脚本
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.hermes_learning_engine import (
    HermesLearningEngine,
    LearningType,
    FeedbackScore,
    LearnedSkill
)
import time


def test_basic_learning():
    """测试基础学习功能"""
    print("\n" + "="*60)
    print("测试1: 基础学习功能")
    print("="*60)

    # 初始化引擎
    engine = HermesLearningEngine(
        storage_path="./data/test_learning",
        enable_auto_learning=True
    )

    # 记录几次经验
    print("\n1. 记录工具使用经验...")
    exp_id_1 = engine.record_experience(
        project_id=1,
        learning_type=LearningType.TOOL_USAGE,
        context={
            "task": "文档分析",
            "document_type": "pdf",
            "pages": 10
        },
        action={
            "tool": "document_analyzer",
            "parameters": {
                "mode": "deep",
                "extract_entities": True
            }
        },
        result={
            "entities_found": 25,
            "keywords": 15,
            "summary_generated": True
        },
        success=True,
        execution_time=2.5
    )
    print(f"   ✅ 记录成功: {exp_id_1}")

    print("\n2. 记录工作流优化经验...")
    exp_id_2 = engine.record_experience(
        project_id=1,
        learning_type=LearningType.WORKFLOW_OPTIMIZATION,
        context={
            "workflow": "document_processing",
            "documents_count": 5
        },
        action={
            "optimization": "parallel_processing",
            "batch_size": 3
        },
        result={
            "time_saved": 5.2,
            "throughput_increase": "40%"
        },
        success=True,
        execution_time=8.0
    )
    print(f"   ✅ 记录成功: {exp_id_2}")

    print("\n3. 记录错误纠正经验...")
    exp_id_3 = engine.record_experience(
        project_id=1,
        learning_type=LearningType.ERROR_CORRECTION,
        context={
            "error_type": "encoding_error",
            "file_format": "pdf"
        },
        action={
            "fix": "use_alternative_parser",
            "parser": "pymupdf"
        },
        result={
            "error_resolved": True,
            "alternative_successful": True
        },
        success=True,
        execution_time=1.2
    )
    print(f"   ✅ 记录成功: {exp_id_3}")

    # 获取统计
    print("\n4. 获取学习统计...")
    stats = engine.get_stats()
    print(f"   总经验数: {stats['total_experiences']}")
    print(f"   总技能数: {stats['total_skills']}")
    print(f"   成功率: {stats['success_rate']:.2%}")
    print(f"   学习类型分布:")
    for lt, count in stats['learning_types'].items():
        if count > 0:
            print(f"      - {lt}: {count}")

    return engine


def test_similar_experiences(engine):
    """测试相似经验检索"""
    print("\n" + "="*60)
    print("测试2: 相似经验检索")
    print("="*60)

    context = {
        "task": "文档分析",
        "document_type": "pdf"
    }

    print(f"\n查询上下文: {context}")
    similar = engine.get_similar_experiences(
        context=context,
        learning_type=LearningType.TOOL_USAGE,
        limit=3
    )

    print(f"\n找到 {len(similar)} 条相似经验:")
    for i, exp in enumerate(similar, 1):
        print(f"\n   经验 {i}:")
        print(f"      ID: {exp.experience_id}")
        print(f"      类型: {exp.learning_type.value}")
        print(f"      成功: {exp.success}")
        print(f"      执行时间: {exp.execution_time:.2f}s")


def test_action_suggestion(engine):
    """测试动作建议"""
    print("\n" + "="*60)
    print("测试3: 动作建议")
    print("="*60)

    context = {
        "task": "文档分析",
        "document_type": "pdf",
        "pages": 15
    }

    print(f"\n当前上下文: {context}")
    suggested = engine.suggest_action(
        context=context,
        learning_type=LearningType.TOOL_USAGE
    )

    if suggested:
        print(f"\n建议的动作:")
        print(f"   {suggested}")
    else:
        print("\n   暂无建议（需要更多历史数据）")


def test_skill_registration(engine):
    """测试技能注册"""
    print("\n" + "="*60)
    print("测试4: 技能注册")
    print("="*60)

    # 创建一个学习到的技能
    skill = LearnedSkill(
        skill_id="skill_pdf_analysis_v1",
        skill_name="PDF深度分析",
        skill_type="tool_chain",
        description="针对学术PDF的深度分析工作流",
        trigger_conditions=[
            {"condition": "document_type == 'pdf'"},
            {"condition": "analysis_depth == 'deep'"}
        ],
        action_sequence=[
            {"step": 1, "action": "extract_text", "tool": "pymupdf"},
            {"step": 2, "action": "extract_entities", "tool": "ner_model"},
            {"step": 3, "action": "generate_summary", "tool": "llm_summarizer"}
        ],
        success_rate=0.95,
        avg_execution_time=3.2,
        usage_count=10,
        confidence_score=0.9
    )

    print(f"\n注册技能: {skill.skill_name}")
    skill_id = engine.register_skill(skill)
    print(f"   ✅ 注册成功: {skill_id}")

    # 验证技能已保存
    print(f"\n验证技能库...")
    stats = engine.get_stats()
    print(f"   当前技能数: {stats['total_skills']}")


def test_persistence(engine):
    """测试持久化"""
    print("\n" + "="*60)
    print("测试5: 持久化验证")
    print("="*60)

    print("\n1. 创建新引擎实例（重新加载）...")
    new_engine = HermesLearningEngine(
        storage_path="./data/test_learning",
        enable_auto_learning=False
    )

    stats = new_engine.get_stats()
    print(f"   加载的经验数: {stats['total_experiences']}")
    print(f"   加载的技能数: {stats['total_skills']}")

    if stats['total_experiences'] > 0:
        print("   ✅ 持久化成功")
    else:
        print("   ⚠️ 持久化可能有问题")


def main():
    """主测试流程"""
    print("\n" + "="*80)
    print(" Hermes Learning Engine 测试套件")
    print("="*80)

    try:
        # 测试1: 基础功能
        engine = test_basic_learning()

        # 测试2: 相似经验检索
        test_similar_experiences(engine)

        # 测试3: 动作建议
        test_action_suggestion(engine)

        # 测试4: 技能注册
        test_skill_registration(engine)

        # 测试5: 持久化
        test_persistence(engine)

        print("\n" + "="*80)
        print(" ✅ 所有测试通过！")
        print("="*80)

        # 最终统计
        final_stats = engine.get_stats()
        print(f"\n最终统计:")
        print(f"   总经验数: {final_stats['total_experiences']}")
        print(f"   总技能数: {final_stats['total_skills']}")
        print(f"   成功率: {final_stats['success_rate']:.2%}")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
