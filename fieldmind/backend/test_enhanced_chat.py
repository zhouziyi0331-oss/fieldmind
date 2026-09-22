#!/usr/bin/env python3
"""
FieldMind 增强对话功能测试脚本
测试长记忆系统和增强AI对话的完整功能
"""

import requests
import json
import time
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"
PROJECT_ID = 1

def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def print_result(test_name: str, success: bool, data: Any = None):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{status} | {test_name}")
    if data and not success:
        print(f"   详情: {data}")

def test_health_check():
    """测试 1: 健康检查"""
    print_section("测试 1: 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        success = response.status_code == 200
        print_result("健康检查", success, response.json() if success else response.text)
        return success
    except Exception as e:
        print_result("健康检查", False, str(e))
        return False

def test_basic_chat():
    """测试 2: 基础对话（无长记忆）"""
    print_section("测试 2: 基础对话")
    try:
        payload = {
            "session_id": "test-basic-001",
            "message": "你好，简单介绍一下你自己",
            "project_id": PROJECT_ID,
            "use_long_memory": False,
            "use_deep_thinking": False
        }

        print("发送请求...")
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/enhanced",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print_result("基础对话", True)
            print(f"   回复: {data.get('answer', '')[:100]}...")
            print(f"   令牌: {data.get('metadata', {}).get('tokens_used', {})}")
            return True
        else:
            print_result("基础对话", False, response.text)
            return False
    except Exception as e:
        print_result("基础对话", False, str(e))
        return False

def test_long_memory():
    """测试 3: 长记忆功能"""
    print_section("测试 3: 长记忆功能")

    # 第一步：存储信息
    print("步骤 1/2: 存储记忆...")
    try:
        payload = {
            "session_id": "test-memory-001",
            "message": "请记住这个重要信息：FieldMind 项目的代号是 Phoenix-2024，启动日期是 2024年7月31日",
            "project_id": PROJECT_ID,
            "use_long_memory": True,
            "use_deep_thinking": False
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/chat/enhanced",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            print_result("存储记忆", True)
        else:
            print_result("存储记忆", False, response.text)
            return False
    except Exception as e:
        print_result("存储记忆", False, str(e))
        return False

    # 等待向量化完成
    print("等待向量化完成（2秒）...")
    time.sleep(2)

    # 第二步：在新会话中回忆
    print("\n步骤 2/2: 回忆记忆...")
    try:
        payload = {
            "session_id": "test-memory-002",  # 不同的会话
            "message": "FieldMind 项目的代号是什么？启动日期是哪天？",
            "project_id": PROJECT_ID,
            "use_long_memory": True,
            "use_deep_thinking": False
        }

        response = requests.post(
            f"{BASE_URL}/api/v1/chat/enhanced",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')

            # 检查是否包含关键信息
            has_code = "Phoenix-2024" in answer or "Phoenix" in answer
            has_date = "2024年7月31日" in answer or "7月31日" in answer

            success = has_code or has_date
            print_result("回忆记忆", success)
            print(f"   回复: {answer[:200]}...")

            if data.get('sources'):
                print(f"   来源: {len(data['sources'])} 个记忆片段")

            return success
        else:
            print_result("回忆记忆", False, response.text)
            return False
    except Exception as e:
        print_result("回忆记忆", False, str(e))
        return False

def test_memory_search():
    """测试 4: 记忆搜索"""
    print_section("测试 4: 记忆搜索")
    try:
        payload = {
            "query": "FieldMind 项目",
            "project_id": PROJECT_ID,
            "top_k": 5
        }

        print("搜索记忆...")
        response = requests.post(
            f"{BASE_URL}/api/v1/memory/search",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print_result("记忆搜索", True)
            print(f"   找到 {len(results)} 条记忆")

            for i, result in enumerate(results[:3], 1):
                print(f"   [{i}] 相关度: {result.get('relevance_score', 0):.2f}")
                print(f"       内容: {result.get('content', '')[:80]}...")

            return True
        else:
            print_result("记忆搜索", False, response.text)
            return False
    except Exception as e:
        print_result("记忆搜索", False, str(e))
        return False

def test_deep_thinking():
    """测试 5: 深度思考模式"""
    print_section("测试 5: 深度思考模式")
    try:
        payload = {
            "session_id": "test-thinking-001",
            "message": "设计一个高可用的分布式缓存系统，需要考虑哪些关键因素？",
            "project_id": PROJECT_ID,
            "use_long_memory": False,
            "use_deep_thinking": True
        }

        print("发送深度思考请求（可能需要较长时间）...")
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/enhanced",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            has_thinking = bool(data.get('thinking_process'))

            print_result("深度思考", has_thinking)
            print(f"   回复长度: {len(data.get('answer', ''))} 字符")

            if has_thinking:
                thinking = data['thinking_process']
                print(f"   思考过程长度: {len(thinking)} 字符")
                print(f"   思考片段: {thinking[:150]}...")

            print(f"   令牌使用: {data.get('metadata', {}).get('tokens_used', {})}")
            return has_thinking
        else:
            print_result("深度思考", False, response.text)
            return False
    except Exception as e:
        print_result("深度思考", False, str(e))
        return False

def test_skill_mode():
    """测试 6: 技能模式"""
    print_section("测试 6: 技能模式")
    try:
        payload = {
            "session_id": "test-skill-001",
            "message": "审查这段代码：for i in range(len(items)): print(items[i])",
            "project_id": PROJECT_ID,
            "use_long_memory": False,
            "skill_config": {
                "skill_name": "code_review",
                "workflow_prompt": """你是一位资深代码审查专家。审查代码时关注：
1. 代码可读性和简洁性
2. Python 最佳实践
3. 性能优化机会
4. 潜在的 bug 或边界情况
请提供具体的改进建议。"""
            }
        }

        print("发送技能模式请求...")
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/enhanced",
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')

            # 检查是否包含代码审查相关内容
            has_review = any(keyword in answer.lower() for keyword in
                           ['建议', '优化', '改进', 'enumerate', 'pythonic'])

            print_result("技能模式", has_review)
            print(f"   回复: {answer[:200]}...")
            return has_review
        else:
            print_result("技能模式", False, response.text)
            return False
    except Exception as e:
        print_result("技能模式", False, str(e))
        return False

def test_memory_statistics():
    """测试 7: 记忆统计"""
    print_section("测试 7: 记忆统计")
    try:
        print("获取记忆统计...")
        response = requests.get(
            f"{BASE_URL}/api/v1/memory/statistics",
            params={"project_id": PROJECT_ID},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_result("记忆统计", True)
            print(f"   短期记忆: {data.get('short_term_count', 0)}")
            print(f"   中期记忆: {data.get('mid_term_count', 0)}")
            print(f"   长期记忆: {data.get('long_term_count', 0)}")
            print(f"   向量总数: {data.get('total_vectors', 0)}")
            print(f"   平均相关度: {data.get('avg_relevance_score', 0):.2f}")
            return True
        else:
            print_result("记忆统计", False, response.text)
            return False
    except Exception as e:
        print_result("记忆统计", False, str(e))
        return False

def main():
    """主测试流程"""
    print("\n" + "🚀 FieldMind 增强对话功能测试")
    print("=" * 60)
    print(f"后端地址: {BASE_URL}")
    print(f"项目 ID: {PROJECT_ID}")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # 执行所有测试
    results['健康检查'] = test_health_check()

    if not results['健康检查']:
        print("\n❌ 服务未运行，请先启动后端服务：")
        print("   cd /Users/alwan/FieldMind-Rebuild/fieldmind-backend")
        print("   ./start.sh")
        return

    results['基础对话'] = test_basic_chat()
    results['长记忆功能'] = test_long_memory()
    results['记忆搜索'] = test_memory_search()
    results['深度思考模式'] = test_deep_thinking()
    results['技能模式'] = test_skill_mode()
    results['记忆统计'] = test_memory_statistics()

    # 汇总结果
    print_section("测试汇总")
    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常。")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查日志。")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
