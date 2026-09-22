"""
测试4个Workflow的真实执行功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def test_research_report_crew():
    """测试研究报告工作流"""
    print("\n" + "="*60)
    print("测试1: ResearchReportCrew - 研究报告工作流")
    print("="*60)

    from app.services.workflows.research_report_crew import ResearchReportCrew

    crew = ResearchReportCrew()
    print(f"Workflow: {crew.name()}")
    print(f"Description: {crew.description()}")
    print(f"Steps: {len(crew.steps)}")

    # 执行研究报告生成
    print("\n执行研究: 乡村振兴 文化遗产")
    result = crew.execute_research(
        query="乡村振兴 文化遗产",
        max_results=5,
        extract_content=False  # 不提取内容，加快测试
    )

    print(f"\nStatus: {result['status']}")
    print(f"Query: {result['query']}")

    if 'search_summary' in result:
        summary = result['search_summary']
        print(f"\n搜索结果:")
        print(f"  总数: {summary['total_results']}")
        print(f"  来源:")
        for idx, source in enumerate(summary['sources'][:3], 1):
            print(f"    {idx}. {source['title'][:50]}...")

    if 'execution_summary' in result:
        exec_sum = result['execution_summary']
        print(f"\n执行摘要:")
        print(f"  完成步骤: {exec_sum['successful_steps']}/{exec_sum['total_steps']}")
        print(f"  总耗时: {exec_sum['total_time']:.2f}秒")

    if 'key_insights' in result:
        insights = result['key_insights']
        print(f"\n关键洞察: {len(insights)} 条")
        for idx, insight in enumerate(insights[:2], 1):
            print(f"  {idx}. {insight.get('skill', '')}: {insight.get('dimension', '')}")

    assert result['status'] in ['success', 'partial']
    print("\n✓ ResearchReportCrew测试通过")


def test_rag_query_crew():
    """测试RAG查询工作流"""
    print("\n" + "="*60)
    print("测试2: RAGQueryCrew - RAG查询工作流")
    print("="*60)

    from app.services.workflows.rag_query_crew import RAGQueryCrew

    crew = RAGQueryCrew()
    print(f"Workflow: {crew.name()}")
    print(f"Description: {crew.description()}")
    print(f"Steps: {len(crew.steps)}")

    # 执行RAG查询
    print("\n执行查询: 如何保护乡村文化遗产？")
    result = crew.query(
        question="如何保护乡村文化遗产？",
        max_results=3
    )

    print(f"\nStatus: {result['status']}")
    print(f"Query: {result['query']}")

    if 'query_analysis' in result:
        analysis = result['query_analysis']
        print(f"\n查询分析:")
        print(f"  实体数: {analysis['entity_count']}")
        print(f"  搜索查询: {analysis['search_query']}")
        if analysis.get('entities'):
            print(f"  关键实体:")
            for entity in analysis['entities'][:3]:
                if isinstance(entity, dict):
                    print(f"    - {entity.get('entity', '')}")

    if 'retrieval' in result:
        retrieval = result['retrieval']
        print(f"\n检索结果: {retrieval['total_results']} 个")

    if 'answer' in result and 'insights' in result['answer']:
        insights = result['answer']['insights']
        print(f"\n答案洞察: {len(insights)} 条")
        for idx, insight in enumerate(insights[:2], 1):
            print(f"  {idx}. {insight.get('skill', '')}")

    assert result['status'] in ['success', 'partial']
    print("\n✓ RAGQueryCrew测试通过")


def test_autonomous_crew():
    """测试自主工作流"""
    print("\n" + "="*60)
    print("测试3: AutonomousCrew - 自主工作流")
    print("="*60)

    from app.services.workflows.autonomous_crew import AutonomousCrew

    crew = AutonomousCrew()
    print(f"Workflow: {crew.name()}")
    print(f"Description: {crew.description()}")
    print(f"Steps: {len(crew.steps)}")

    # 执行自主任务（AI自动理解并调度）
    print("\n执行自主任务: 搜索机器学习的最新研究")
    result = crew.execute_autonomous(
        task_description="搜索机器学习的最新研究",
        max_results=3
    )

    print(f"\nStatus: {result['status']}")
    print(f"Task: {result['task_description']}")

    if 'task_analysis' in result:
        analysis = result['task_analysis']
        print(f"\n任务分析:")
        print(f"  推断工作流: {analysis['inferred_workflow']}")
        print(f"  提取实体数: {len(analysis.get('entities', []))}")

    if 'coordination' in result:
        coord = result['coordination']
        print(f"\n协调执行:")
        print(f"  工作流: {coord.get('workflow_executed', 'N/A')}")
        print(f"  完成步骤: {coord.get('completed_steps', 0)}")

    if 'execution_summary' in result:
        exec_sum = result['execution_summary']
        print(f"\n执行摘要:")
        print(f"  完成步骤: {exec_sum['successful_steps']}/{exec_sum['total_steps']}")
        print(f"  总耗时: {exec_sum['total_time']:.2f}秒")

    assert result['status'] in ['success', 'partial']
    print("\n✓ AutonomousCrew测试通过")


def test_workflow_base_features():
    """测试Workflow基类功能"""
    print("\n" + "="*60)
    print("测试4: WorkflowBase基类功能")
    print("="*60)

    from app.services.workflows.research_report_crew import ResearchReportCrew
    from app.services.workflows.base_workflow import WorkflowInput, WorkflowStatus

    crew = ResearchReportCrew()

    # 测试workflow_id生成
    print(f"Workflow ID: {crew.workflow_id}")
    assert crew.workflow_id.startswith('workflow_')

    # 测试状态管理
    print(f"Initial Status: {crew.status}")
    assert crew.status == WorkflowStatus.PENDING

    # 测试步骤定义
    print(f"Total Steps: {len(crew.steps)}")
    for idx, step in enumerate(crew.steps, 1):
        print(f"  Step {idx}: {step.step_name} (agent={step.agent_type})")

    assert len(crew.steps) > 0

    # 测试Agent池
    print(f"\nInitial Agent Pool Size: {len(crew.agent_pool)}")
    assert len(crew.agent_pool) == 0

    print("\n✓ WorkflowBase功能测试通过")


if __name__ == "__main__":
    try:
        test_workflow_base_features()
        test_research_report_crew()
        test_rag_query_crew()
        test_autonomous_crew()

        print("\n" + "="*60)
        print("所有Workflow测试通过！✓")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
