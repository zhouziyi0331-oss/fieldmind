"""
测试学习引擎 - Phase 3 验证
Test Learning Engine - Phase 3 Validation

此脚本验证自主学习引擎的核心功能:
- 从分析结果中提取模式
- 识别重复出现的模式
- 自动生成Skill定义
- 验证Skill质量
- 演化思维模型
- 生成学习报告

This script validates the core functionality of the self-learning engine:
- Extract patterns from analysis results
- Identify recurring patterns
- Auto-generate Skill definitions
- Validate Skill quality
- Evolve thinking models
- Generate learning reports
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.learning_engine import (
    LearningEngine,
    Pattern,
    SkillDefinition,
    ThinkingModel,
    LearningResult
)


# ============================================================================
# 测试数据准备 - Test Data Preparation
# ============================================================================

def create_sample_analysis_results() -> List[Dict[str, Any]]:
    """
    创建样本分析结果
    Create sample analysis results from previous knowledge analysis
    """

    # 分析结果 1: AI医疗文档分析
    analysis_1 = {
        "analysis_id": "analysis_001",
        "timestamp": "2026-08-01T10:00:00",
        "documents_analyzed": 15,
        "semantic_analysis": {
            "clusters": [
                {
                    "cluster_id": 0,
                    "size": 8,
                    "keywords": ["医疗AI", "诊断", "影像分析", "深度学习"],
                    "coherence": 0.85
                },
                {
                    "cluster_id": 1,
                    "size": 5,
                    "keywords": ["患者数据", "隐私保护", "HIPAA", "合规"],
                    "coherence": 0.78
                },
                {
                    "cluster_id": 2,
                    "size": 2,
                    "keywords": ["临床试验", "FDA批准", "监管"],
                    "coherence": 0.72
                }
            ],
            "topics": [
                {
                    "topic_id": 0,
                    "keywords": ["AI医疗诊断", "影像识别", "准确率", "临床应用"],
                    "representative_docs": [0, 3, 7]
                },
                {
                    "topic_id": 1,
                    "keywords": ["数据隐私", "GDPR", "安全加密", "患者权益"],
                    "representative_docs": [4, 8, 11]
                }
            ],
            "cross_relations": [
                {
                    "doc_pair": [0, 3],
                    "similarity": 0.92,
                    "relation_type": "high_similarity",
                    "summary": "两篇文档都讨论医疗AI诊断准确率提升"
                },
                {
                    "doc_pair": [4, 8],
                    "similarity": 0.85,
                    "relation_type": "complementary",
                    "summary": "文档4讨论隐私法规，文档8讨论技术实现"
                }
            ]
        },
        "llm_analysis": {
            "key_insights": [
                "AI医疗诊断系统在影像分析领域表现优异，准确率达95%以上",
                "数据隐私和合规是医疗AI应用的主要障碍",
                "跨机构数据共享需要标准化协议"
            ],
            "summary": "医疗AI技术成熟但需解决隐私和监管问题",
            "recommendations": [
                "建立统一的医疗数据隐私标准",
                "加速FDA审批流程",
                "推动医疗机构间数据共享协议"
            ]
        },
        "metadata": {
            "analysis_focus": "医疗AI应用",
            "document_types": ["研究论文", "技术报告", "监管文件"],
            "analysis_duration": 45.2
        }
    }

    # 分析结果 2: 区块链金融分析
    analysis_2 = {
        "analysis_id": "analysis_002",
        "timestamp": "2026-08-01T14:30:00",
        "documents_analyzed": 12,
        "semantic_analysis": {
            "clusters": [
                {
                    "cluster_id": 0,
                    "size": 6,
                    "keywords": ["DeFi", "智能合约", "去中心化", "流动性"],
                    "coherence": 0.88
                },
                {
                    "cluster_id": 1,
                    "size": 4,
                    "keywords": ["加密货币", "交易所", "监管", "合规"],
                    "coherence": 0.81
                },
                {
                    "cluster_id": 2,
                    "size": 2,
                    "keywords": ["NFT", "数字资产", "所有权"],
                    "coherence": 0.75
                }
            ],
            "topics": [
                {
                    "topic_id": 0,
                    "keywords": ["DeFi协议", "收益农场", "风险管理", "安全审计"],
                    "representative_docs": [0, 2, 5]
                },
                {
                    "topic_id": 1,
                    "keywords": ["监管框架", "KYC", "AML", "证券法"],
                    "representative_docs": [3, 7, 9]
                }
            ],
            "cross_relations": [
                {
                    "doc_pair": [0, 2],
                    "similarity": 0.90,
                    "relation_type": "high_similarity",
                    "summary": "都讨论DeFi协议的安全性问题"
                },
                {
                    "doc_pair": [3, 7],
                    "similarity": 0.87,
                    "relation_type": "complementary",
                    "summary": "监管要求与技术实现的对比"
                }
            ]
        },
        "llm_analysis": {
            "key_insights": [
                "DeFi生态系统快速增长但存在安全风险",
                "监管不确定性是区块链金融面临的主要挑战",
                "智能合约审计需求激增"
            ],
            "summary": "区块链金融创新快速但监管滞后",
            "recommendations": [
                "建立DeFi协议安全标准",
                "推动监管沙盒实验",
                "加强智能合约审计能力"
            ]
        },
        "metadata": {
            "analysis_focus": "区块链金融",
            "document_types": ["白皮书", "技术文档", "监管报告"],
            "analysis_duration": 38.7
        }
    }

    # 分析结果 3: 计算机视觉分析
    analysis_3 = {
        "analysis_id": "analysis_003",
        "timestamp": "2026-08-01T16:00:00",
        "documents_analyzed": 18,
        "semantic_analysis": {
            "clusters": [
                {
                    "cluster_id": 0,
                    "size": 9,
                    "keywords": ["目标检测", "YOLO", "实时处理", "边缘计算"],
                    "coherence": 0.91
                },
                {
                    "cluster_id": 1,
                    "size": 6,
                    "keywords": ["图像分割", "语义理解", "场景识别"],
                    "coherence": 0.84
                },
                {
                    "cluster_id": 2,
                    "size": 3,
                    "keywords": ["3D重建", "SLAM", "深度估计"],
                    "coherence": 0.79
                }
            ],
            "topics": [
                {
                    "topic_id": 0,
                    "keywords": ["实时目标检测", "模型压缩", "移动端部署", "推理优化"],
                    "representative_docs": [0, 4, 8, 12]
                },
                {
                    "topic_id": 1,
                    "keywords": ["语义分割", "实例分割", "Transformer", "注意力机制"],
                    "representative_docs": [2, 6, 10, 14]
                }
            ],
            "cross_relations": [
                {
                    "doc_pair": [0, 4],
                    "similarity": 0.94,
                    "relation_type": "high_similarity",
                    "summary": "都讨论YOLO模型的实时性能优化"
                },
                {
                    "doc_pair": [2, 6],
                    "similarity": 0.88,
                    "relation_type": "complementary",
                    "summary": "传统CNN与Transformer在分割任务上的对比"
                }
            ]
        },
        "llm_analysis": {
            "key_insights": [
                "实时目标检测技术在边缘设备上取得突破",
                "Transformer架构在视觉任务中逐步替代CNN",
                "模型压缩和量化技术成为部署关键"
            ],
            "summary": "计算机视觉向轻量化和实时化发展",
            "recommendations": [
                "优先采用YOLO最新版本进行实时检测",
                "探索Vision Transformer在分割任务的应用",
                "建立模型压缩和量化标准流程"
            ]
        },
        "metadata": {
            "analysis_focus": "计算机视觉",
            "document_types": ["学术论文", "技术博客", "开源项目"],
            "analysis_duration": 52.1
        }
    }

    return [analysis_1, analysis_2, analysis_3]


def create_sample_feedback() -> Dict[str, Any]:
    """
    创建样本用户反馈
    Create sample user feedback
    """
    return {
        "useful_insights": [
            "AI医疗诊断系统在影像分析领域表现优异",
            "DeFi生态系统快速增长但存在安全风险",
            "Transformer架构在视觉任务中逐步替代CNN"
        ],
        "preferred_analysis_depth": "deep",
        "preferred_topics": ["技术实现", "监管合规", "实际应用"],
        "ignored_topics": ["历史背景", "理论基础"],
        "rating": 4.5,
        "comments": "分析深入且有实际价值，希望能更关注技术实现细节"
    }


# ============================================================================
# 测试函数 - Test Functions
# ============================================================================

async def test_pattern_extraction(engine: LearningEngine, analysis_results: List[Dict[str, Any]]):
    """
    测试模式提取功能
    Test pattern extraction from analysis results
    """
    print("\n" + "="*80)
    print("测试 1: 模式提取 | Test 1: Pattern Extraction")
    print("="*80)

    try:
        # 使用第一个分析结果测试模式提取
        patterns = await engine._extract_patterns(analysis_results[0])

        print(f"\n✓ 成功提取 {len(patterns)} 个模式")
        print(f"✓ Successfully extracted {len(patterns)} patterns\n")

        for i, pattern in enumerate(patterns, 1):
            print(f"模式 {i} | Pattern {i}:")
            print(f"  名称 | Name: {pattern.name}")
            print(f"  描述 | Description: {pattern.description}")
            print(f"  成功率 | Success Rate: {pattern.success_rate:.2f}")
            print(f"  频率 | Frequency: {pattern.frequency}")
            print(f"  分析步骤 | Steps: {len(pattern.analysis_steps)} 步")
            if pattern.example_cases:
                print(f"  示例数量 | Examples: {len(pattern.example_cases)}")
            print()

        return patterns

    except Exception as e:
        print(f"\n✗ 模式提取失败 | Pattern extraction failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


async def test_skill_generation(engine: LearningEngine, patterns: List[Pattern]):
    """
    测试Skill生成功能
    Test Skill generation from patterns
    """
    print("\n" + "="*80)
    print("测试 2: Skill生成 | Test 2: Skill Generation")
    print("="*80)

    if not patterns:
        print("\n✗ 没有可用的模式进行Skill生成")
        print("✗ No patterns available for Skill generation")
        return []

    skills = []

    try:
        for i, pattern in enumerate(patterns[:3], 1):  # 测试前3个模式
            print(f"\n从模式 {i} 生成Skill | Generating Skill from Pattern {i}...")

            skill = await engine._generate_skill_from_pattern(pattern)

            if skill:
                skills.append(skill)
                print(f"\n✓ 成功生成Skill: {skill.name}")
                print(f"✓ Successfully generated Skill: {skill.name}")
                print(f"  描述 | Description: {skill.description}")
                print(f"  置信度 | Confidence: {skill.confidence_score:.2f}")
                print(f"  触发条件 | Triggers: {len(skill.trigger_conditions)} 个")
                print(f"  输入字段 | Input fields: {len(skill.input_schema.get('properties', {}))} 个")
                print(f"  输出字段 | Output fields: {len(skill.output_schema.get('properties', {}))} 个")
                print(f"  实现代码 | Implementation: {len(skill.implementation_logic)} 字符")
            else:
                print(f"\n✗ 无法从模式 {i} 生成Skill")
                print(f"✗ Failed to generate Skill from Pattern {i}")

        print(f"\n总结 | Summary: 成功生成 {len(skills)}/{len(patterns[:3])} 个Skill")
        print(f"Summary: Successfully generated {len(skills)}/{len(patterns[:3])} Skills")

        return skills

    except Exception as e:
        print(f"\n✗ Skill生成失败 | Skill generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return skills


async def test_thinking_model_evolution(engine: LearningEngine, analysis_results: List[Dict[str, Any]], feedback: Dict[str, Any]):
    """
    测试思维模型演化功能
    Test thinking model evolution
    """
    print("\n" + "="*80)
    print("测试 3: 思维模型演化 | Test 3: Thinking Model Evolution")
    print("="*80)

    try:
        # 先添加足够的分析历史（至少5次）以满足最小历史记录要求
        for i in range(2):  # 重复添加以达到5次
            for analysis in analysis_results:
                engine.analysis_history.append(analysis)

        print(f"\n已添加 {len(engine.analysis_history)} 次分析历史")
        print(f"Added {len(engine.analysis_history)} analysis history entries")

        thinking_models = await engine._evolve_thinking_models()

        print(f"\n✓ 成功演化 {len(thinking_models)} 个思维模型")
        print(f"✓ Successfully evolved {len(thinking_models)} thinking models\n")

        for i, model in enumerate(thinking_models, 1):
            print(f"思维模型 {i} | Thinking Model {i}:")
            print(f"  名称 | Name: {model.name}")
            print(f"  描述 | Description: {model.description}")
            print(f"  认知模式 | Patterns: {', '.join(model.cognitive_patterns)}")
            print(f"  推理步骤 | Steps: {len(model.reasoning_steps)} 步")
            print(f"  有效性 | Effectiveness: {model.effectiveness_score:.2f}")
            if model.applicable_scenarios:
                print(f"  适用场景 | Scenarios: {', '.join(model.applicable_scenarios[:3])}")
            print()

        return len(thinking_models) > 0

    except Exception as e:
        print(f"\n✗ 思维模型演化失败 | Thinking model evolution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_learning_pipeline(engine: LearningEngine, analysis_results: List[Dict[str, Any]], feedback: Dict[str, Any]):
    """
    测试完整的学习管道
    Test complete learning pipeline
    """
    print("\n" + "="*80)
    print("测试 4: 完整学习管道 | Test 4: Complete Learning Pipeline")
    print("="*80)

    try:
        # 逐个分析结果进行学习，并重复处理以创建重复模式
        all_results = []

        for i, analysis in enumerate(analysis_results, 1):
            print(f"\n处理分析结果 {i}/{len(analysis_results)}")
            print(f"Processing analysis result {i}/{len(analysis_results)}")

            learning_result = await engine.learn_from_analysis(analysis, feedback)
            all_results.append(learning_result)

            print(f"\n学习结果 {i} | Learning Result {i}:")
            print(f"  提取模式 | Patterns extracted: {len(learning_result.patterns_extracted)}")
            print(f"  生成Skill | Skills generated: {len(learning_result.skills_generated)}")
            print(f"  思维模型 | Thinking models: {len(learning_result.thinking_models)}")
            print(f"  学习时间 | Learning time: {learning_result.learning_metadata.get('learning_time', 0):.2f}秒")

            if learning_result.learning_metadata:
                print(f"  总成本 | Total cost: ${learning_result.learning_metadata.get('total_cost', 0):.4f}")

        # 再处理一次第一个分析以创建重复模式
        print(f"\n重复处理第一个分析以验证重复模式识别")
        print(f"Re-processing first analysis to verify recurring pattern detection")

        final_result = await engine.learn_from_analysis(analysis_results[0], feedback)

        print(f"\n最终学习结果 | Final Learning Result:")
        print(f"  提取模式 | Patterns extracted: {len(final_result.patterns_extracted)}")
        print(f"  生成Skill | Skills generated: {len(final_result.skills_generated)}")
        print(f"  思维模型 | Thinking models: {len(final_result.thinking_models)}")

        # 检查引擎的整体学习状态
        print(f"\n引擎整体状态 | Engine Overall State:")
        print(f"  历史记录 | History entries: {len(engine.analysis_history)}")
        print(f"  模式库 | Pattern database: {len(engine.patterns_db)}")
        print(f"  已注册Skill | Registered skills: {len(engine.registered_skills)}")
        print(f"  思维模型 | Thinking models: {len(engine.thinking_models_db)}")

        return True

    except Exception as e:
        print(f"\n✗ 完整学习管道失败 | Complete learning pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_skill_export(engine: LearningEngine):
    """
    测试Skill导出功能
    Test Skill export functionality
    """
    print("\n" + "="*80)
    print("测试 5: Skill导出 | Test 5: Skill Export")
    print("="*80)

    try:
        output_dir = "/Users/alwan/generated_skills"
        await engine.export_skills(output_dir)

        print(f"\n✓ 成功导出 {len(engine.skills_db)} 个Skill到: {output_dir}")
        print(f"✓ Successfully exported {len(engine.skills_db)} Skills to: {output_dir}")

        # 检查导出的文件
        import os
        if os.path.exists(output_dir) and len(engine.skills_db) > 0:
            files = os.listdir(output_dir)
            print(f"\n导出文件列表 | Exported files:")
            for file in files:
                if file.endswith('.json'):
                    print(f"  - {file}")

        return True

    except Exception as e:
        print(f"\n✗ Skill导出失败 | Skill export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_learning_report_export(engine: LearningEngine, analysis_results: List[Dict[str, Any]]):
    """
    测试学习报告导出功能
    Test learning report export functionality
    """
    print("\n" + "="*80)
    print("测试 6: 学习报告导出 | Test 6: Learning Report Export")
    print("="*80)

    try:
        # 先进行一次学习以生成数据
        learning_result = await engine.learn_from_analysis(analysis_results[0], create_sample_feedback())

        output_path = "/Users/alwan/learning_report.md"
        await engine.export_learning_report(output_path)

        print(f"\n✓ 成功导出学习报告到: {output_path}")
        print(f"✓ Successfully exported learning report to: {output_path}")

        # 读取并显示部分内容
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')[:30]  # 显示前30行
            print(f"\n报告预览 | Report Preview (前30行 | first 30 lines):")
            print("-" * 80)
            print('\n'.join(lines))
            print("-" * 80)

        return True

    except Exception as e:
        print(f"\n✗ 学习报告导出失败 | Learning report export failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# 主测试函数 - Main Test Function
# ============================================================================

async def run_all_tests():
    """
    运行所有测试
    Run all tests
    """
    print("\n" + "="*80)
    print("Phase 3 学习引擎测试套件 | Phase 3 Learning Engine Test Suite")
    print("="*80)
    print(f"开始时间 | Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 准备测试数据
    print("\n准备测试数据 | Preparing test data...")
    analysis_results = create_sample_analysis_results()
    feedback = create_sample_feedback()
    print(f"✓ 准备了 {len(analysis_results)} 个分析结果和用户反馈")
    print(f"✓ Prepared {len(analysis_results)} analysis results and user feedback")

    # 初始化学习引擎
    print("\n初始化学习引擎 | Initializing learning engine...")
    engine = LearningEngine()
    print("✓ 学习引擎初始化完成")
    print("✓ Learning engine initialized")

    # 运行测试
    test_results = {}

    # Test 1: 模式提取
    patterns = await test_pattern_extraction(engine, analysis_results)
    test_results['pattern_extraction'] = len(patterns) > 0

    # Test 2: Skill生成
    skills = await test_skill_generation(engine, patterns)
    test_results['skill_generation'] = len(skills) > 0

    # Test 3: 思维模型演化
    thinking_model_success = await test_thinking_model_evolution(engine, analysis_results, feedback)
    test_results['thinking_model_evolution'] = thinking_model_success

    # Test 4: 完整学习管道
    pipeline_success = await test_complete_learning_pipeline(engine, analysis_results, feedback)
    test_results['complete_pipeline'] = pipeline_success

    # Test 5: Skill导出
    export_success = await test_skill_export(engine)
    test_results['skill_export'] = export_success

    # Test 6: 学习报告导出
    report_success = await test_learning_report_export(engine, analysis_results)
    test_results['learning_report_export'] = report_success

    # 打印测试总结
    print("\n" + "="*80)
    print("测试总结 | Test Summary")
    print("="*80)

    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)

    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n总计 | Total: {passed_tests}/{total_tests} 测试通过")
    print(f"成功率 | Success rate: {(passed_tests/total_tests*100):.1f}%")
    print(f"\n结束时间 | End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    return test_results


# ============================================================================
# 主程序入口 - Main Entry Point
# ============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Phase 3 学习引擎测试 - Learning Engine Test                  ║
║                                                                              ║
║  此测试验证自主学习引擎的所有核心功能:                                               ║
║  This test validates all core functionalities of the self-learning engine:  ║
║                                                                              ║
║  ✓ 模式提取 Pattern Extraction                                               ║
║  ✓ Skill生成 Skill Generation                                                ║
║  ✓ 思维模型演化 Thinking Model Evolution                                      ║
║  ✓ 完整学习管道 Complete Learning Pipeline                                    ║
║  ✓ Skill导出 Skill Export                                                     ║
║  ✓ 学习报告 Learning Report                                                   ║
║                                                                              ║
║  注意: 需要配置有效的LLM API密钥                                                 ║
║  Note: Valid LLM API key required                                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    # 运行测试
    asyncio.run(run_all_tests())
