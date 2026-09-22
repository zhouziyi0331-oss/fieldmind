"""
测试SearchAgent的真实搜索功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.agents.search_agent import SearchAgent
from app.services.agents.base_agent import AgentTask, AgentStatus
from datetime import datetime


def test_basic_search():
    """测试基础搜索功能"""
    print("\n=== 测试1: 基础搜索功能 ===")

    agent = SearchAgent()
    print(f"Agent ID: {agent.agent_id}")
    print(f"Agent Role: {agent.role}")
    print(f"Search Available: {agent.search_available}")

    # 创建搜索任务
    task = AgentTask(
        task_id="test_search_1",
        task_type="search",
        input_data={
            'query': "乡村振兴 文化遗产",
            'max_results': 5,
            'region': 'cn-zh',  # 中国地区
            'extract_content': False
        },
        priority=5
    )

    print(f"\n执行搜索任务: {task.input_data['query']}")
    result = agent.execute_task(task)

    print(f"Success: {result.success}")
    print(f"Total Results: {result.output_data.get('total_results', 0)}")
    print(f"Execution Time: {result.execution_time:.2f}s")

    # 显示搜索结果
    results = result.output_data.get('results', [])
    for idx, res in enumerate(results, 1):
        print(f"\n结果 {idx}:")
        print(f"  标题: {res.get('title', '')[:50]}...")
        print(f"  URL: {res.get('url', '')}")
        print(f"  摘要: {res.get('snippet', '')[:100]}...")

    assert result.success is True
    assert len(results) > 0
    print("\n✓ 基础搜索测试通过")


def test_search_with_content_extraction():
    """测试搜索+内容提取功能"""
    print("\n=== 测试2: 搜索+内容提取 ===")

    agent = SearchAgent()

    task = AgentTask(
        task_id="test_search_2",
        task_type="search",
        input_data={
            'query': "Python programming tutorial",
            'max_results': 2,  # 只取2条，避免太慢
            'extract_content': True
        },
        priority=5
    )

    print(f"执行搜索任务（含内容提取）: {task.input_data['query']}")
    result = agent.execute_task(task)

    print(f"Success: {result.success}")

    results = result.output_data.get('results', [])
    for idx, res in enumerate(results, 1):
        print(f"\n结果 {idx}:")
        print(f"  标题: {res.get('title', '')}")
        print(f"  URL: {res.get('url', '')}")
        content = res.get('content', '')
        if content:
            print(f"  内容长度: {len(content)} 字符")
            print(f"  内容预览: {content[:200]}...")
        else:
            print(f"  内容提取失败: {res.get('content_error', 'Unknown error')}")

    assert result.success is True
    print("\n✓ 内容提取测试通过")


def test_sync_search_method():
    """测试同步搜索方法"""
    print("\n=== 测试3: 同步搜索方法 ===")

    agent = SearchAgent()

    print("使用search_sync方法搜索...")
    result = agent.search_sync(
        query="机器学习",
        max_results=3,
        extract_content=False
    )

    print(f"Query: {result.get('query')}")
    print(f"Total Results: {result.get('total_results', 0)}")

    results = result.get('results', [])
    for idx, res in enumerate(results, 1):
        print(f"\n结果 {idx}: {res.get('title', '')[:60]}")

    assert len(results) > 0
    print("\n✓ 同步搜索方法测试通过")


def test_empty_query():
    """测试空查询处理"""
    print("\n=== 测试4: 空查询处理 ===")

    agent = SearchAgent()

    task = AgentTask(
        task_id="test_search_empty",
        task_type="search",
        input_data={'query': ""},
        priority=5
    )

    result = agent.execute_task(task)

    print(f"Success: {result.success}")
    print(f"Errors: {result.errors}")

    assert result.success is False
    assert len(result.errors) > 0
    assert any('不能为空' in err for err in result.errors)
    print("\n✓ 空查询处理测试通过")


def test_task_history():
    """测试任务历史记录"""
    print("\n=== 测试5: 任务历史记录 ===")

    agent = SearchAgent()

    # 执行多个任务
    queries = ["AI", "机器学习", "深度学习"]
    for query in queries:
        agent.search_sync(query, max_results=2)

    print(f"任务历史数量: {len(agent.task_history)}")

    for idx, task_result in enumerate(agent.task_history, 1):
        print(f"\n任务 {idx}:")
        print(f"  Task ID: {task_result.task_id}")
        print(f"  Success: {task_result.success}")
        print(f"  Query: {task_result.output_data.get('query', 'N/A')}")
        print(f"  Results: {task_result.output_data.get('total_results', 0)}")

    assert len(agent.task_history) == 3
    print("\n✓ 任务历史记录测试通过")


if __name__ == "__main__":
    try:
        test_basic_search()
        test_search_with_content_extraction()
        test_sync_search_method()
        test_empty_query()
        test_task_history()

        print("\n" + "="*60)
        print("所有SearchAgent测试通过！✓")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
