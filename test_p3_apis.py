#!/usr/bin/env python3
"""
P3 API 集成测试脚本
测试所有 P3 API 端点是否正常工作
"""

import requests
import json
import sys
from typing import Dict, Any, List, Tuple

# FieldMind API 基础 URL
BASE_URL = "http://localhost:8013"

# 测试结果
test_results: List[Tuple[str, bool, str]] = []


def test_api(name: str, method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> bool:
    """
    测试 API 端点

    Args:
        name: 测试名称
        method: HTTP 方法 (GET, POST, etc.)
        endpoint: API 端点
        data: 请求数据
        headers: 请求头

    Returns:
        是否成功
    """
    url = f"{BASE_URL}{endpoint}"
    default_headers = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)

    try:
        if method == "GET":
            response = requests.get(url, headers=default_headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=default_headers, timeout=10)
        else:
            test_results.append((name, False, f"不支持的方法: {method}"))
            return False

        # 检查响应
        if response.status_code == 200:
            test_results.append((name, True, f"状态码: {response.status_code}"))
            return True
        elif response.status_code == 404:
            test_results.append((name, False, f"端点未找到 (404)"))
            return False
        elif response.status_code == 500:
            try:
                error_data = response.json()
                error_msg = error_data.get("message", "未知错误")
                test_results.append((name, False, f"服务器错误: {error_msg[:100]}"))
            except:
                test_results.append((name, False, f"服务器错误 (500)"))
            return False
        else:
            test_results.append((name, False, f"状态码: {response.status_code}"))
            return False

    except requests.exceptions.ConnectionError:
        test_results.append((name, False, "无法连接到服务器"))
        return False
    except requests.exceptions.Timeout:
        test_results.append((name, False, "请求超时"))
        return False
    except Exception as e:
        test_results.append((name, False, f"异常: {str(e)[:100]}"))
        return False


def print_results():
    """打印测试结果"""
    print("\n" + "=" * 80)
    print("P3 API 集成测试结果")
    print("=" * 80)

    success_count = sum(1 for _, success, _ in test_results if success)
    total_count = len(test_results)

    # 按类别分组显示
    categories = {
        "LLM 统计": [],
        "LLM 服务": [],
        "Agent 系统": [],
        "协作编辑": [],
        "知识图谱": [],
        "RAG 增强": [],
        "通知系统": [],
    }

    for name, success, message in test_results:
        if "LLM 统计" in name:
            category = "LLM 统计"
        elif "LLM 服务" in name:
            category = "LLM 服务"
        elif "Agent" in name:
            category = "Agent 系统"
        elif "协作" in name:
            category = "协作编辑"
        elif "知识图谱" in name:
            category = "知识图谱"
        elif "RAG" in name:
            category = "RAG 增强"
        elif "通知" in name:
            category = "通知系统"
        else:
            continue

        categories[category].append((name, success, message))

    # 打印每个类别
    for category, results in categories.items():
        if results:
            print(f"\n【{category}】")
            for name, success, message in results:
                status = "✅" if success else "❌"
                print(f"  {status} {name:40s} - {message}")

    # 总结
    print("\n" + "=" * 80)
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    print(f"总计: {success_count}/{total_count} 通过 ({success_rate:.1f}%)")
    print("=" * 80)

    return success_count == total_count


def main():
    """主测试函数"""
    print("=" * 80)
    print("开始测试 P3 API 集成...")
    print("=" * 80)

    # 1. 测试 LLM 统计 API
    print("\n🧪 测试 LLM 统计 API...")
    test_api("LLM 统计 - 获取成本", "GET", "/api/llm-stats/cost")
    test_api("LLM 统计 - 获取策略", "GET", "/api/llm-stats/strategy")

    # 2. 测试 LLM 服务 API
    print("🧪 测试 LLM 服务 API...")
    test_api(
        "LLM 服务 - 聊天完成",
        "POST",
        "/api/llm/chat",
        data={
            "messages": [{"role": "user", "content": "Hello"}],
            "routing_strategy": "cost_optimized"
        }
    )
    test_api("LLM 服务 - 提供商列表", "GET", "/api/llm/providers")
    test_api("LLM 服务 - 模型列表", "GET", "/api/llm/models")

    # 3. 测试 Agent 系统 API
    print("🧪 测试 Agent 系统 API...")
    test_api("Agent 系统 - 列表", "GET", "/api/agents/")
    test_api(
        "Agent 系统 - 创建",
        "POST",
        "/api/agents/create",
        data={
            "name": "测试助手",
            "type": "reasoning",
            "system_prompt": "你是一个测试助手"
        }
    )

    # 4. 测试协作编辑 API
    print("🧪 测试协作编辑 API...")
    test_api("协作编辑 - 文档列表", "GET", "/api/collaboration/documents")
    test_api(
        "协作编辑 - 创建文档",
        "POST",
        "/api/collaboration/documents",
        data={"initial_content": "测试内容"}
    )

    # 5. 测试知识图谱 API
    print("🧪 测试知识图谱 API...")
    test_api("知识图谱 - 实体列表", "GET", "/api/knowledge-graph/entities")
    test_api("知识图谱 - 关系列表", "GET", "/api/knowledge-graph/relationships")

    # 6. 测试 RAG 增强 API
    print("🧪 测试 RAG 增强 API...")
    test_api("RAG 增强 - 健康检查", "GET", "/api/rag/health")
    test_api(
        "RAG 增强 - 查询",
        "POST",
        "/api/rag/query",
        data={
            "query": "测试查询",
            "top_k": 5
        }
    )

    # 7. 测试通知系统 API
    print("🧪 测试通知系统 API...")
    test_api("通知系统 - 获取通知", "GET", "/api/notifications/")

    # 打印结果
    all_passed = print_results()

    # 返回退出码
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
