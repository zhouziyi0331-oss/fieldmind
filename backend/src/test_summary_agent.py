"""
测试SummaryAgent的Skills分析和报告生成功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.agents.summary_agent import SummaryAgent
from app.services.agents.base_agent import AgentTask


def test_basic_summary():
    """测试基础分析功能"""
    print("\n=== 测试1: 基础Skills分析 ===")

    agent = SummaryAgent()
    print(f"Agent ID: {agent.agent_id}")
    print(f"Agent Role: {agent.role}")
    print(f"Available Skills: {len(agent.available_skills)}")

    # 测试内容
    content = """
    本项目位于浙江省某古村落，拥有丰富的文化遗产资源。
    村落保存完好的明清建筑群，具有重要的历史价值和文化意义。
    项目计划通过文化旅游开发，带动当地经济发展。
    需要建立多村联动机制，整合周边资源。
    商业模式需要充分考虑可持续性和盈利能力。
    """

    task = AgentTask(
        task_id="test_summary_1",
        task_type="summary",
        input_data={
            'content': content,
            'report_format': 'full',
            'include_statistics': True
        },
        priority=5
    )

    print(f"\n执行分析任务（内容长度: {len(content)} 字符）")
    result = agent.execute_task(task)

    print(f"Success: {result.success}")
    print(f"Skills Executed: {result.output_data.get('skills_executed')}")
    print(f"Skills Successful: {result.output_data.get('skills_successful')}")
    print(f"Execution Time: {result.execution_time:.2f}s")

    # 显示统计信息
    stats = result.output_data.get('statistics', {})
    print(f"\n统计信息:")
    print(f"  总匹配数: {stats.get('total_matches', 0)}")
    print(f"  总维度数: {stats.get('total_dimensions', 0)}")
    print(f"  平均置信度: {stats.get('avg_confidence', 0):.3f}")

    # 显示关键洞察
    insights = result.output_data.get('insights', [])
    print(f"\n关键洞察 (前3条):")
    for idx, insight in enumerate(insights[:3], 1):
        print(f"\n  {idx}. {insight['skill']} - {insight['dimension']}")
        print(f"     匹配数: {insight['match_count']}")
        print(f"     关键句: {insight['key_sentence'][:50]}...")
        print(f"     置信度: {insight['confidence']:.3f}")

    assert result.success is True
    assert result.output_data['skills_executed'] == 6
    assert result.output_data['skills_successful'] > 0
    print("\n✓ 基础分析测试通过")


def test_summary_format():
    """测试摘要格式报告"""
    print("\n=== 测试2: 摘要格式报告 ===")

    agent = SummaryAgent()

    content = """
    乡村振兴需要文化引领，保护传统建筑和非物质文化遗产。
    通过发展特色产业，提升村民收入。
    建立合作社机制，实现资源共享和风险共担。
    """

    task = AgentTask(
        task_id="test_summary_2",
        task_type="summary",
        input_data={
            'content': content,
            'report_format': 'summary'
        },
        priority=5
    )

    result = agent.execute_task(task)

    print(f"Success: {result.success}")
    print(f"Report Format: summary")

    # 检查摘要格式内容
    assert 'skills_summary' in result.output_data
    assert 'insights' in result.output_data
    assert 'skills_results' not in result.output_data  # 摘要格式不包含完整结果

    skills_summary = result.output_data['skills_summary']
    print(f"\nSkills摘要 ({len(skills_summary)} 个):")
    for skill_id, summary in list(skills_summary.items())[:3]:
        print(f"  - {summary['name']}: {summary['matches']} 匹配")

    print("\n✓ 摘要格式测试通过")


def test_insights_only():
    """测试只返回洞察"""
    print("\n=== 测试3: 洞察格式报告 ===")

    agent = SummaryAgent()

    content = """
    项目具有良好的市场前景和社会价值。
    需要进行详细的可行性研究和风险评估。
    """

    task = AgentTask(
        task_id="test_summary_3",
        task_type="summary",
        input_data={
            'content': content,
            'report_format': 'insights'
        },
        priority=5
    )

    result = agent.execute_task(task)

    print(f"Success: {result.success}")
    print(f"Report Format: insights")

    # 检查洞察格式内容
    assert 'insights' in result.output_data
    assert 'skills_results' not in result.output_data
    assert 'skills_summary' not in result.output_data

    insights = result.output_data['insights']
    print(f"\n提取到 {len(insights)} 条洞察")

    print("\n✓ 洞察格式测试通过")


def test_partial_skills():
    """测试部分Skills执行"""
    print("\n=== 测试4: 部分Skills执行 ===")

    agent = SummaryAgent()

    content = "测试内容：古村落文化保护与旅游开发结合"

    # 只执行2个Skills
    task = AgentTask(
        task_id="test_summary_4",
        task_type="summary",
        input_data={
            'content': content,
            'enabled_skills': ['heritage_dadi', 'business_feasibility'],
            'report_format': 'summary'
        },
        priority=5
    )

    result = agent.execute_task(task)

    print(f"Success: {result.success}")
    print(f"Skills Executed: {result.output_data.get('skills_executed')}")

    assert result.output_data['skills_executed'] == 2
    print("\n✓ 部分Skills执行测试通过")


def test_sync_method():
    """测试同步分析方法"""
    print("\n=== 测试5: 同步分析方法 ===")

    agent = SummaryAgent()

    result = agent.analyze_sync(
        content="乡村文化遗产保护项目",
        enabled_skills=['heritage_dadi'],
        report_format='insights'
    )

    print(f"Content Length: {result.get('content_length')}")
    print(f"Skills Executed: {result.get('skills_executed')}")
    print(f"Insights Count: {len(result.get('insights', []))}")

    assert result.get('skills_executed') == 1
    print("\n✓ 同步分析方法测试通过")


def test_empty_content():
    """测试空内容处理"""
    print("\n=== 测试6: 空内容处理 ===")

    agent = SummaryAgent()

    task = AgentTask(
        task_id="test_summary_empty",
        task_type="summary",
        input_data={'content': ""},
        priority=5
    )

    result = agent.execute_task(task)

    print(f"Success: {result.success}")
    print(f"Errors: {result.errors}")

    assert result.success is False
    assert len(result.errors) > 0
    print("\n✓ 空内容处理测试通过")


if __name__ == "__main__":
    try:
        test_basic_summary()
        test_summary_format()
        test_insights_only()
        test_partial_skills()
        test_sync_method()
        test_empty_content()

        print("\n" + "="*60)
        print("所有SummaryAgent测试通过！✓")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
