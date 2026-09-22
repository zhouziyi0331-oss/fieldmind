"""
工作流引擎测试套件

测试Phase 4实现的所有核心功能：
- DAG构建和拓扑排序
- 依赖管理
- 失败重试
- 状态持久化
- 并行执行
- 条件执行

日期: 2026-08-01
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    StepType,
    StepStatus,
    WorkflowStatus,
    RetryPolicy,
    DAG,
    StateStore
)


# ============================================================================
# 模拟执行器
# ============================================================================

async def mock_document_processor(input_data: dict, parameters: dict):
    """模拟文档处理"""
    await asyncio.sleep(0.5)
    return {
        "processed_documents": input_data.get("documents", []),
        "count": len(input_data.get("documents", [])),
        "status": "processed"
    }


async def mock_semantic_analyzer(input_data: dict, parameters: dict):
    """模拟语义分析"""
    await asyncio.sleep(0.8)
    return {
        "clusters": ["主题1", "主题2", "主题3"],
        "topics": ["AI", "医疗", "科技"],
        "similarity_score": 0.85
    }


async def mock_llm_analyzer(input_data: dict, parameters: dict):
    """模拟LLM分析"""
    await asyncio.sleep(1.0)
    tier = parameters.get("tier", 1)
    return {
        "tier": tier,
        "analysis": f"这是Tier{tier}分析结果，基于{input_data.get('clusters', [])}个主题",
        "word_count": 8000 + tier * 2000
    }


async def mock_learning_engine(input_data: dict, parameters: dict):
    """模拟学习引擎"""
    await asyncio.sleep(0.6)
    return {
        "patterns_extracted": 3,
        "skills_generated": 2,
        "thinking_models": 1
    }


async def mock_report_generator(input_data: dict, parameters: dict):
    """模拟报告生成"""
    await asyncio.sleep(0.5)
    return {
        "report_url": "/reports/test_report.pdf",
        "format": parameters.get("format", "pdf"),
        "pages": 25
    }


async def mock_failing_step(input_data: dict, parameters: dict):
    """模拟失败的步骤（用于测试重试）"""
    # 第一次和第二次失败，第三次成功
    attempt = parameters.get("_attempt", 1)
    if attempt < 3:
        raise RuntimeError(f"模拟失败 (尝试 {attempt})")
    return {"status": "success", "attempt": attempt}


# ============================================================================
# 测试函数
# ============================================================================

async def test_dag_construction():
    """测试1: DAG构建和拓扑排序"""
    print("\n" + "="*70)
    print("测试1: DAG构建和拓扑排序")
    print("="*70)

    steps = [
        WorkflowStep(
            step_id="step_a",
            name="步骤A",
            type=StepType.DOCUMENT_PROCESSING,
            dependencies=[]
        ),
        WorkflowStep(
            step_id="step_b",
            name="步骤B",
            type=StepType.SEMANTIC_ANALYSIS,
            dependencies=["step_a"]
        ),
        WorkflowStep(
            step_id="step_c",
            name="步骤C",
            type=StepType.LLM_ANALYSIS,
            dependencies=["step_a"]
        ),
        WorkflowStep(
            step_id="step_d",
            name="步骤D",
            type=StepType.REPORT_GENERATION,
            dependencies=["step_b", "step_c"]
        )
    ]

    dag = DAG()
    for step in steps:
        dag.add_node(step)

    for step in steps:
        for dep in step.dependencies:
            dag.add_edge(dep, step.step_id)

    # 拓扑排序
    sorted_steps = dag.topological_sort()

    print(f"\n✓ DAG构建成功")
    print(f"  节点数: {len(dag.nodes)}")
    print(f"  拓扑排序: {' → '.join([s.step_id for s in sorted_steps])}")

    # 验证顺序
    step_indices = {s.step_id: i for i, s in enumerate(sorted_steps)}
    for step in steps:
        for dep in step.dependencies:
            assert step_indices[dep] < step_indices[step.step_id], \
                f"依赖顺序错误: {dep} 应该在 {step.step_id} 之前"

    print(f"✓ 依赖顺序验证通过")

    # 测试环检测
    print(f"\n测试环检测...")
    dag_with_cycle = DAG()
    cycle_steps = [
        WorkflowStep("s1", "步骤1", StepType.CUSTOM, dependencies=["s2"]),
        WorkflowStep("s2", "步骤2", StepType.CUSTOM, dependencies=["s1"])
    ]
    for s in cycle_steps:
        dag_with_cycle.add_node(s)
        for dep in s.dependencies:
            dag_with_cycle.add_edge(dep, s.step_id)

    assert dag_with_cycle.has_cycle(), "应该检测到环"
    print(f"✓ 环检测正常工作")

    return True


async def test_simple_workflow():
    """测试2: 简单工作流执行"""
    print("\n" + "="*70)
    print("测试2: 简单工作流执行")
    print("="*70)

    # 创建工作流定义
    workflow_def = WorkflowDefinition(
        workflow_id="wf_simple_test",
        name="简单测试工作流",
        description="测试基本的工作流执行",
        steps=[
            WorkflowStep(
                step_id="process_docs",
                name="文档处理",
                type=StepType.DOCUMENT_PROCESSING,
                dependencies=[],
                input_mapping={"workflow_input": "documents"}
            ),
            WorkflowStep(
                step_id="analyze",
                name="语义分析",
                type=StepType.SEMANTIC_ANALYSIS,
                dependencies=["process_docs"],
                input_mapping={"docs": "process_docs.processed_documents"}
            )
        ]
    )

    # 创建引擎并注册执行器
    engine = WorkflowEngine()
    engine.register_executor(StepType.DOCUMENT_PROCESSING, mock_document_processor)
    engine.register_executor(StepType.SEMANTIC_ANALYSIS, mock_semantic_analyzer)

    # 执行工作流
    input_data = {
        "documents": ["doc1.txt", "doc2.txt", "doc3.txt"]
    }

    result = await engine.execute_workflow(workflow_def, input_data)

    print(f"\n✓ 工作流执行完成")
    print(f"  实例ID: {result.instance_id}")
    print(f"  状态: {result.status}")
    print(f"  耗时: {result.duration:.2f}秒")
    print(f"  完成步骤数: {len(result.step_results)}")

    # 验证结果
    assert result.status == WorkflowStatus.COMPLETED, "工作流应该成功完成"
    assert len(result.step_results) == 2, "应该有2个步骤结果"
    assert all(r.status == StepStatus.COMPLETED for r in result.step_results.values()), \
        "所有步骤都应该成功"

    # 检查输出
    process_result = result.step_results["process_docs"]
    assert process_result.output["count"] == 3, "应该处理3个文档"

    analyze_result = result.step_results["analyze"]
    assert len(analyze_result.output["clusters"]) == 3, "应该有3个聚类"

    print(f"✓ 结果验证通过")

    return True


async def test_parallel_execution():
    """测试3: 并行执行"""
    print("\n" + "="*70)
    print("测试3: 并行执行")
    print("="*70)

    workflow_def = WorkflowDefinition(
        workflow_id="wf_parallel_test",
        name="并行执行测试",
        description="测试并行步骤执行",
        steps=[
            WorkflowStep(
                step_id="process",
                name="文档处理",
                type=StepType.DOCUMENT_PROCESSING,
                dependencies=[]
            ),
            # 这三个步骤可以并行
            WorkflowStep(
                step_id="analyze_semantic",
                name="语义分析",
                type=StepType.SEMANTIC_ANALYSIS,
                dependencies=["process"]
            ),
            WorkflowStep(
                step_id="analyze_tier1",
                name="Tier1分析",
                type=StepType.LLM_ANALYSIS,
                dependencies=["process"],
                parameters={"tier": 1}
            ),
            WorkflowStep(
                step_id="analyze_tier2",
                name="Tier2分析",
                type=StepType.LLM_ANALYSIS,
                dependencies=["process"],
                parameters={"tier": 2}
            ),
            # 这个步骤依赖前面三个
            WorkflowStep(
                step_id="generate_report",
                name="生成报告",
                type=StepType.REPORT_GENERATION,
                dependencies=["analyze_semantic", "analyze_tier1", "analyze_tier2"]
            )
        ]
    )

    engine = WorkflowEngine(max_concurrent_steps=3)
    engine.register_executor(StepType.DOCUMENT_PROCESSING, mock_document_processor)
    engine.register_executor(StepType.SEMANTIC_ANALYSIS, mock_semantic_analyzer)
    engine.register_executor(StepType.LLM_ANALYSIS, mock_llm_analyzer)
    engine.register_executor(StepType.REPORT_GENERATION, mock_report_generator)

    import time
    start_time = time.time()

    result = await engine.execute_workflow(
        workflow_def,
        {"documents": ["doc1.txt"]}
    )

    elapsed_time = time.time() - start_time

    print(f"\n✓ 并行工作流执行完成")
    print(f"  总耗时: {elapsed_time:.2f}秒")
    print(f"  完成步骤数: {len(result.step_results)}")

    # 验证并行执行效果
    # 如果串行执行: 0.5 + (0.8 + 1.0 + 1.0) + 0.5 = 3.8秒
    # 如果并行执行: 0.5 + max(0.8, 1.0, 1.0) + 0.5 = 2.0秒左右
    assert elapsed_time < 3.5, f"并行执行应该更快 (实际: {elapsed_time:.2f}秒)"

    print(f"✓ 并行执行效果验证通过 (比串行快)")

    return True


async def test_retry_mechanism():
    """测试4: 失败重试机制"""
    print("\n" + "="*70)
    print("测试4: 失败重试机制")
    print("="*70)

    # 创建一个会失败的执行器（前2次失败，第3次成功）
    attempt_counter = {"count": 0}

    async def failing_executor(input_data: dict, parameters: dict):
        attempt_counter["count"] += 1
        if attempt_counter["count"] < 3:
            raise RuntimeError(f"模拟失败 (尝试 {attempt_counter['count']})")
        return {"status": "success", "attempt": attempt_counter["count"]}

    workflow_def = WorkflowDefinition(
        workflow_id="wf_retry_test",
        name="重试测试工作流",
        description="测试失败重试机制",
        steps=[
            WorkflowStep(
                step_id="flaky_step",
                name="不稳定的步骤",
                type=StepType.CUSTOM,
                retry_policy=RetryPolicy(
                    max_attempts=3,
                    initial_delay=0.1,
                    exponential_base=2.0
                )
            )
        ]
    )

    engine = WorkflowEngine()
    engine.register_executor(StepType.CUSTOM, failing_executor)

    result = await engine.execute_workflow(workflow_def, {})

    print(f"\n✓ 重试工作流执行完成")
    print(f"  状态: {result.status}")
    print(f"  总尝试次数: {attempt_counter['count']}")

    # 验证
    assert result.status == WorkflowStatus.COMPLETED, "工作流应该最终成功"
    assert attempt_counter["count"] == 3, "应该尝试3次"

    step_result = result.step_results["flaky_step"]
    assert step_result.status == StepStatus.COMPLETED, "步骤应该最终成功"
    assert step_result.attempt == 3, "应该记录尝试次数"

    print(f"✓ 重试机制验证通过")

    return True


async def test_state_persistence():
    """测试5: 状态持久化"""
    print("\n" + "="*70)
    print("测试5: 状态持久化")
    print("="*70)

    state_store = StateStore()
    engine = WorkflowEngine(state_store=state_store)
    engine.register_executor(StepType.DOCUMENT_PROCESSING, mock_document_processor)
    engine.register_executor(StepType.SEMANTIC_ANALYSIS, mock_semantic_analyzer)

    workflow_def = WorkflowDefinition(
        workflow_id="wf_state_test",
        name="状态持久化测试",
        description="测试状态存储和恢复",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="步骤1",
                type=StepType.DOCUMENT_PROCESSING
            ),
            WorkflowStep(
                step_id="step2",
                name="步骤2",
                type=StepType.SEMANTIC_ANALYSIS,
                dependencies=["step1"]
            )
        ]
    )

    result = await engine.execute_workflow(workflow_def, {"documents": ["test.txt"]})
    instance_id = result.instance_id

    print(f"\n✓ 工作流执行完成")
    print(f"  实例ID: {instance_id}")

    # 从状态存储中恢复
    stored_workflow = await state_store.get_workflow(instance_id)
    assert stored_workflow is not None, "应该能从状态存储中获取工作流"
    assert stored_workflow.status == WorkflowStatus.COMPLETED, "状态应该是已完成"
    assert len(stored_workflow.step_results) == 2, "应该有2个步骤结果"

    print(f"✓ 从状态存储中成功恢复工作流")
    print(f"  状态: {stored_workflow.status}")
    print(f"  步骤数: {len(stored_workflow.step_results)}")

    # 验证步骤结果
    step1_result = await state_store.get_step_result(instance_id, "step1")
    assert step1_result is not None, "应该能获取步骤1的结果"
    assert step1_result.status == StepStatus.COMPLETED, "步骤1应该是完成状态"

    print(f"✓ 步骤结果持久化验证通过")

    return True


async def test_complex_workflow():
    """测试6: 复杂工作流（完整分析流程）"""
    print("\n" + "="*70)
    print("测试6: 复杂工作流（完整分析流程）")
    print("="*70)

    workflow_def = WorkflowDefinition(
        workflow_id="wf_full_analysis",
        name="完整分析工作流",
        description="模拟完整的文档分析流程",
        steps=[
            # 阶段1: 文档处理
            WorkflowStep(
                step_id="process_documents",
                name="文档处理",
                type=StepType.DOCUMENT_PROCESSING,
                input_mapping={"workflow_input": "documents"}
            ),

            # 阶段2: 并行分析
            WorkflowStep(
                step_id="semantic_analysis",
                name="语义分析",
                type=StepType.SEMANTIC_ANALYSIS,
                dependencies=["process_documents"],
                input_mapping={"docs": "process_documents.processed_documents"}
            ),
            WorkflowStep(
                step_id="entity_extraction",
                name="实体提取",
                type=StepType.ENTITY_EXTRACTION,
                dependencies=["process_documents"]
            ),

            # 阶段3: LLM分析（依赖阶段2）
            WorkflowStep(
                step_id="tier1_analysis",
                name="Tier1分析",
                type=StepType.LLM_ANALYSIS,
                dependencies=["semantic_analysis", "entity_extraction"],
                parameters={"tier": 1}
            ),
            WorkflowStep(
                step_id="tier2_analysis",
                name="Tier2分析",
                type=StepType.LLM_ANALYSIS,
                dependencies=["tier1_analysis"],
                parameters={"tier": 2}
            ),
            WorkflowStep(
                step_id="tier3_analysis",
                name="Tier3分析",
                type=StepType.LLM_ANALYSIS,
                dependencies=["tier2_analysis"],
                parameters={"tier": 3}
            ),

            # 阶段4: 学习和报告（依赖阶段3）
            WorkflowStep(
                step_id="learning",
                name="学习引擎",
                type=StepType.LEARNING,
                dependencies=["tier1_analysis", "tier2_analysis", "tier3_analysis"]
            ),
            WorkflowStep(
                step_id="generate_report",
                name="生成报告",
                type=StepType.REPORT_GENERATION,
                dependencies=["tier3_analysis"],
                parameters={"format": "pdf"}
            )
        ]
    )

    # 创建引擎并注册所有执行器
    engine = WorkflowEngine(max_concurrent_steps=3)
    engine.register_executor(StepType.DOCUMENT_PROCESSING, mock_document_processor)
    engine.register_executor(StepType.SEMANTIC_ANALYSIS, mock_semantic_analyzer)
    engine.register_executor(StepType.ENTITY_EXTRACTION, mock_semantic_analyzer)  # 复用
    engine.register_executor(StepType.LLM_ANALYSIS, mock_llm_analyzer)
    engine.register_executor(StepType.LEARNING, mock_learning_engine)
    engine.register_executor(StepType.REPORT_GENERATION, mock_report_generator)

    # 执行工作流
    input_data = {
        "documents": ["医疗AI论文.pdf", "区块链金融.pdf", "计算机视觉.pdf"]
    }

    import time
    start_time = time.time()

    result = await engine.execute_workflow(workflow_def, input_data)

    elapsed_time = time.time() - start_time

    print(f"\n✓ 复杂工作流执行完成")
    print(f"  状态: {result.status}")
    print(f"  总耗时: {elapsed_time:.2f}秒")
    print(f"  完成步骤数: {len(result.step_results)}/{len(workflow_def.steps)}")

    # 显示执行摘要
    print(f"\n执行摘要:")
    for step_id, step_result in result.step_results.items():
        print(f"  • {step_id}: {step_result.status} (耗时: {step_result.duration:.2f}秒)")

    # 验证
    assert result.status == WorkflowStatus.COMPLETED, "工作流应该成功完成"
    assert len(result.step_results) == 8, "应该有8个步骤结果"

    # 验证最终输出
    assert "generate_report" in result.output, "应该有报告生成输出"
    assert "learning" in result.output, "应该有学习引擎输出"

    print(f"✓ 复杂工作流验证通过")

    return True


async def test_workflow_serialization():
    """测试7: 工作流序列化/反序列化"""
    print("\n" + "="*70)
    print("测试7: 工作流序列化/反序列化")
    print("="*70)

    # 创建工作流定义
    workflow_def = WorkflowDefinition(
        workflow_id="wf_serialization_test",
        name="序列化测试工作流",
        description="测试工作流的导入导出",
        steps=[
            WorkflowStep(
                step_id="step1",
                name="步骤1",
                type=StepType.DOCUMENT_PROCESSING,
                parameters={"param1": "value1"}
            ),
            WorkflowStep(
                step_id="step2",
                name="步骤2",
                type=StepType.SEMANTIC_ANALYSIS,
                dependencies=["step1"],
                retry_policy=RetryPolicy(max_attempts=3)
            )
        ],
        tags=["test", "serialization"],
        metadata={"author": "test_user"}
    )

    # 导出为JSON
    engine = WorkflowEngine()
    json_str = engine.export_workflow_definition(workflow_def)

    print(f"\n✓ 工作流定义导出成功")
    print(f"  JSON长度: {len(json_str)} 字符")

    # 从JSON导入
    imported_def = WorkflowEngine.import_workflow_definition(json_str)

    print(f"✓ 工作流定义导入成功")

    # 验证
    assert imported_def.workflow_id == workflow_def.workflow_id, "workflow_id应该一致"
    assert imported_def.name == workflow_def.name, "name应该一致"
    assert len(imported_def.steps) == len(workflow_def.steps), "步骤数应该一致"
    assert imported_def.steps[1].retry_policy.max_attempts == 3, "重试策略应该保留"
    assert imported_def.tags == workflow_def.tags, "标签应该一致"

    print(f"✓ 序列化/反序列化验证通过")

    return True


# ============================================================================
# 主测试函数
# ============================================================================

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("工作流引擎测试套件")
    print("Phase 4: 工作流引擎实现")
    print("="*70)

    tests = [
        ("DAG构建和拓扑排序", test_dag_construction),
        ("简单工作流执行", test_simple_workflow),
        ("并行执行", test_parallel_execution),
        ("失败重试机制", test_retry_mechanism),
        ("状态持久化", test_state_persistence),
        ("复杂工作流", test_complex_workflow),
        ("工作流序列化", test_workflow_serialization)
    ]

    results = {}
    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            success = await test_func()
            results[test_name] = "✓ 通过" if success else "✗ 失败"
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            results[test_name] = f"✗ 异常: {str(e)}"
            failed += 1
            print(f"\n✗ 测试失败: {test_name}")
            print(f"  错误: {e}")
            import traceback
            traceback.print_exc()

    # 打印测试摘要
    print("\n" + "="*70)
    print("测试摘要")
    print("="*70)

    for test_name, result in results.items():
        print(f"{result} - {test_name}")

    print(f"\n总计: {len(tests)}个测试")
    print(f"通过: {passed}个 ({passed/len(tests)*100:.1f}%)")
    print(f"失败: {failed}个 ({failed/len(tests)*100:.1f}%)")

    if passed == len(tests):
        print(f"\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")

    return passed == len(tests)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
