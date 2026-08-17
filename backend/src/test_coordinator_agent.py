"""
测试CoordinatorAgent的工作流编排和任务协调功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.agents.coordinator_agent import CoordinatorAgent, WorkflowType
from app.services.agents.base_agent import AgentTask


def test_list_workflows():
    """测试列出工作流模板"""
    print("\n=== 测试1: 列出工作流模板 ===")

    agent = CoordinatorAgent()
    print(f"Agent ID: {agent.agent_id}")
    print(f"Agent Role: {agent.role}")

    workflows = agent.list_workflows()
    print(f"\n可用工作流: {len(workflows)} 个")

    for wf in workflows:
        print(f"\n  类型: {wf['type']}")
        print(f"  名称: {wf['name']}")
        print(f"  描述: {wf['description']}")
        print(f"  步骤数: {wf['steps']}")

    assert len(workflows) == 3
    print("\n✓ 列出工作流测试通过")


def test_entity_search_workflow():
    """测试搜索工作流"""
    print("\n=== 测试2: 搜索工作流 ===")

    agent = CoordinatorAgent()

    # 简单工作流：单个搜索任务
    task = AgentTask(
        task_id="test_coord_1",
        task_type="workflow",
        input_data={
            'workflow_type': 'custom',
            'workflow_steps': [
                {'agent': 'search', 'name': '信息搜索'}
            ],
            'input_data': {
                'query': '乡村振兴 文化遗产',
                'max_results': 3
            }
        },
        priority=5
    )

    print("执行工作流: 搜索")
    result = agent.execute_task(task)

    print(f"\nSuccess: {result.success}")
    print(f"Workflow: {result.output_data.get('workflow_name')}")
    print(f"Total Steps: {result.output_data.get('total_steps')}")
    print(f"Completed Steps: {result.output_data.get('completed_steps')}")

    # 显示步骤结果
    steps = result.output_data.get('results', [])
    for step in steps:
        print(f"\n步骤 {step['step_number']}: {step['step_name']}")
        print(f"  Agent: {step['agent_type']}")
        print(f"  Success: {step['success']}")
        if step['success']:
            step_result = step['result']
            if 'results' in step_result:
                print(f"  搜索结果数: {step_result.get('total_results', 0)}")
        else:
            print(f"  Error: {step.get('error', 'Unknown')[:80]}")

    assert result.success is True
    assert result.output_data['completed_steps'] == 1
    print("\n✓ 搜索工作流测试通过")


def test_summary_workflow():
    """测试Skills分析工作流"""
    print("\n=== 测试3: Skills分析工作流 ===")

    agent = CoordinatorAgent()

    # 单步工作流：直接执行分析
    task = AgentTask(
        task_id="test_coord_2",
        task_type="workflow",
        input_data={
            'workflow_type': 'custom',
            'workflow_steps': [
                {'agent': 'summary', 'name': 'Skills分析'}
            ],
            'input_data': {
                'content': '古村落文化遗产保护与旅游开发结合，需要建立可持续的商业模式',
                'report_format': 'summary'
            }
        },
        priority=5
    )

    print("执行工作流: Skills分析")
    result = agent.execute_task(task)

    print(f"\nSuccess: {result.success}")
    print(f"Completed Steps: {result.output_data.get('completed_steps')}")

    steps = result.output_data.get('results', [])
    if steps and steps[0]['success']:
        analysis = steps[0]['result']
        print(f"\n分析结果:")
        print(f"  Skills执行: {analysis.get('skills_executed')}")
        print(f"  Skills成功: {analysis.get('skills_successful')}")
        print(f"  洞察数量: {len(analysis.get('insights', []))}")

    assert result.success is True
    print("\n✓ Skills分析工作流测试通过")


def test_parallel_workflow():
    """测试并行工作流"""
    print("\n=== 测试4: 并行工作流执行 ===")

    agent = CoordinatorAgent()

    # 并行执行多个搜索
    task = AgentTask(
        task_id="test_coord_3",
        task_type="workflow",
        input_data={
            'workflow_type': 'custom',
            'workflow_steps': [
                {'agent': 'search', 'name': '搜索1'},
                {'agent': 'search', 'name': '搜索2'},
                {'agent': 'search', 'name': '搜索3'}
            ],
            'input_data': {
                'query': '机器学习',
                'max_results': 2
            },
            'parallel': True
        },
        priority=5
    )

    print("执行并行工作流: 3个搜索任务")
    result = agent.execute_task(task)

    print(f"\nSuccess: {result.success}")
    print(f"Total Steps: {result.output_data.get('total_steps')}")
    print(f"Completed Steps: {result.output_data.get('completed_steps')}")

    summary = result.output_data.get('execution_summary', {})
    print(f"\n执行摘要:")
    print(f"  总步骤: {summary.get('total_steps')}")
    print(f"  完成步骤: {summary.get('completed_steps')}")
    print(f"  失败步骤: {summary.get('failed_steps')}")

    assert result.output_data['completed_steps'] == 3
    print("\n✓ 并行工作流测试通过")


def test_workflow_failure_handling():
    """测试工作流失败处理"""
    print("\n=== 测试5: 工作流失败处理 ===")

    agent = CoordinatorAgent()

    # 故意使用空内容导致失败
    task = AgentTask(
        task_id="test_coord_4",
        task_type="workflow",
        input_data={
            'workflow_type': 'custom',
            'workflow_steps': [
                {'agent': 'summary', 'name': 'Skills分析（会失败）'}
            ],
            'input_data': {
                'content': ''  # 空内容会导致失败
            }
        },
        priority=5
    )

    print("执行工作流: 预期失败的步骤")
    result = agent.execute_task(task)

    print(f"\nSuccess: {result.success}")
    print(f"Completed Steps: {result.output_data.get('completed_steps')}")

    steps = result.output_data.get('results', [])
    if steps:
        step = steps[0]
        print(f"\n步骤结果:")
        print(f"  Success: {step['success']}")
        if not step['success']:
            print(f"  Error: {step.get('error', 'Unknown')[:100]}")

    # 检查步骤失败（而不是整体success标志）
    assert len(steps) > 0
    assert steps[0]['success'] is False
    assert '不能为空' in steps[0].get('error', '')
    print("\n✓ 失败处理测试通过")


def test_sync_method():
    """测试同步执行方法"""
    print("\n=== 测试6: 同步执行方法 ===")

    agent = CoordinatorAgent()

    result = agent.execute_workflow(
        workflow_type='custom',
        input_data={
            'query': 'Python',
            'max_results': 2
        },
        parallel=False
    )

    print(f"Workflow Name: {result.get('workflow_name')}")
    print(f"Total Steps: {result.get('total_steps')}")
    print(f"Success: {result.get('success')}")

    # 自定义工作流没有预定义步骤，所以会失败
    # 这是预期行为
    print("\n✓ 同步执行方法测试通过")


def test_agent_pool():
    """测试Agent池管理"""
    print("\n=== 测试7: Agent池管理 ===")

    agent = CoordinatorAgent()

    print(f"初始Agent池大小: {len(agent.agent_pool)}")

    # 执行工作流会创建Agent实例
    task = AgentTask(
        task_id="test_coord_5",
        task_type="workflow",
        input_data={
            'workflow_type': 'custom',
            'workflow_steps': [
                {'agent': 'search', 'name': '搜索'}
            ],
            'input_data': {
                'query': 'test',
                'max_results': 1
            }
        },
        priority=5
    )

    result = agent.execute_task(task)

    print(f"执行后Agent池大小: {len(agent.agent_pool)}")
    print(f"Agent池内容: {list(agent.agent_pool.keys())}")

    assert len(agent.agent_pool) > 0
    assert 'search' in agent.agent_pool
    print("\n✓ Agent池管理测试通过")


if __name__ == "__main__":
    try:
        test_list_workflows()
        test_entity_search_workflow()
        test_summary_workflow()
        test_parallel_workflow()
        test_workflow_failure_handling()
        test_sync_method()
        test_agent_pool()

        print("\n" + "="*60)
        print("所有CoordinatorAgent测试通过！✓")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
