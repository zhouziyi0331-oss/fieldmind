"""
FieldMind MVP 功能 API 测试脚本
使用 HTTP 请求测试 API 端点，避免模型导入冲突
"""

import requests
import json
from datetime import datetime

# API 基础 URL
BASE_URL = "http://localhost:8000/api/v1"

# 测试结果统计
test_results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "errors": []
}

def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_test(name: str, status: str, message: str = ""):
    """打印测试结果"""
    symbols = {
        "pass": "✅ PASS",
        "fail": "❌ FAIL",
        "skip": "⏭️  SKIP"
    }
    print(f"{symbols.get(status, '❓')} | {name}")
    if message:
        print(f"     {message}")

    if status == "pass":
        test_results["passed"] += 1
    elif status == "fail":
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {message}")
    else:
        test_results["skipped"] += 1

def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_data_quality_api(project_id: int):
    """测试数据质量监控 API"""
    print_section("测试 1: 数据质量监控 API")

    try:
        # 测试 1.1: 获取项目质量概览
        response = requests.get(f"{BASE_URL}/data-quality/overview/{project_id}")
        if response.status_code == 200:
            data = response.json()
            score = data.get('quality_score', {}).get('overall_score', 0)
            print_test(
                "GET /data-quality/overview/{project_id}",
                "pass",
                f"质量评分: {score:.1f}"
            )
        else:
            print_test(
                "GET /data-quality/overview/{project_id}",
                "fail",
                f"状态码: {response.status_code}"
            )

        # 测试 1.2: 获取数据缺口
        response = requests.get(f"{BASE_URL}/data-quality/gaps/{project_id}")
        if response.status_code == 200:
            gaps = response.json()
            print_test(
                "GET /data-quality/gaps/{project_id}",
                "pass",
                f"发现 {len(gaps)} 个数据缺口"
            )
        else:
            print_test(
                "GET /data-quality/gaps/{project_id}",
                "fail",
                f"状态码: {response.status_code}"
            )

    except Exception as e:
        print_test("数据质量监控 API", "fail", f"异常: {str(e)}")

def test_traceability_api(project_id: int):
    """测试溯源回溯 API"""
    print_section("测试 2: 溯源回溯 API")

    try:
        # 测试 2.1: 溯源结论
        payload = {
            "conclusion_text": "村民们普遍认为需要改善公共设施",
            "project_id": project_id,
            "top_k": 5
        }
        response = requests.post(f"{BASE_URL}/traceability/trace", json=payload)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_sources', 0)
            print_test(
                "POST /traceability/trace",
                "pass",
                f"找到 {total} 个相关来源"
            )
        else:
            print_test(
                "POST /traceability/trace",
                "fail",
                f"状态码: {response.status_code}"
            )

    except Exception as e:
        print_test("溯源回溯 API", "fail", f"异常: {str(e)}")

def test_collaboration_api(project_id: int):
    """测试协作与权限 API"""
    print_section("测试 3: 协作与权限 API")

    try:
        # 测试 3.1: 获取成员列表
        response = requests.get(f"{BASE_URL}/collaboration/projects/{project_id}/members")
        if response.status_code == 200:
            members = response.json()
            print_test(
                "GET /collaboration/projects/{project_id}/members",
                "pass",
                f"项目有 {len(members)} 位成员"
            )
        else:
            print_test(
                "GET /collaboration/projects/{project_id}/members",
                "fail",
                f"状态码: {response.status_code}"
            )

        # 测试 3.2: 生成邀请链接
        payload = {
            "role": "VIEWER",
            "expires_in_hours": 24
        }
        response = requests.post(f"{BASE_URL}/collaboration/projects/{project_id}/invite", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_test(
                "POST /collaboration/projects/{project_id}/invite",
                "pass",
                f"邀请码: {data.get('invite_code', 'N/A')[:10]}..."
            )
        else:
            print_test(
                "POST /collaboration/projects/{project_id}/invite",
                "fail",
                f"状态码: {response.status_code}"
            )

        # 测试 3.3: 获取活动日志
        response = requests.get(f"{BASE_URL}/collaboration/projects/{project_id}/activity?limit=10")
        if response.status_code == 200:
            logs = response.json()
            print_test(
                "GET /collaboration/projects/{project_id}/activity",
                "pass",
                f"共有 {len(logs)} 条活动记录"
            )
        else:
            print_test(
                "GET /collaboration/projects/{project_id}/activity",
                "fail",
                f"状态码: {response.status_code}"
            )

    except Exception as e:
        print_test("协作与权限 API", "fail", f"异常: {str(e)}")

def test_knowledge_graph_api(project_id: int):
    """测试知识图谱 API"""
    print_section("测试 4: 知识图谱 API")

    try:
        # 测试 4.1: 获取知识图谱
        response = requests.get(f"{BASE_URL}/knowledge-graph/{project_id}")
        if response.status_code == 200:
            data = response.json()
            nodes = data.get('nodes', [])
            edges = data.get('edges', [])
            print_test(
                "GET /knowledge-graph/{project_id}",
                "pass",
                f"节点: {len(nodes)}, 边: {len(edges)}"
            )
        else:
            print_test(
                "GET /knowledge-graph/{project_id}",
                "fail",
                f"状态码: {response.status_code}"
            )

    except Exception as e:
        print_test("知识图谱 API", "fail", f"异常: {str(e)}")

def test_basic_apis():
    """测试基础 API"""
    print_section("测试 5: 基础 API")

    try:
        # 测试 5.1: 获取项目列表
        response = requests.get(f"{BASE_URL}/projects")
        if response.status_code == 200:
            projects = response.json()
            print_test(
                "GET /projects",
                "pass",
                f"共有 {len(projects) if isinstance(projects, list) else 'N/A'} 个项目"
            )
            return projects[0]['id'] if projects and isinstance(projects, list) else None
        else:
            print_test(
                "GET /projects",
                "skip",
                "需要认证或项目不存在"
            )
            return None

    except Exception as e:
        print_test("基础 API", "fail", f"异常: {str(e)}")
        return None

def print_summary():
    """打印测试摘要"""
    print_section("测试摘要")

    total = test_results["passed"] + test_results["failed"] + test_results["skipped"]
    pass_rate = (test_results["passed"] / (total - test_results["skipped"]) * 100) if (total - test_results["skipped"]) > 0 else 0

    print(f"\n总测试数: {total}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    print(f"⏭️  跳过: {test_results['skipped']}")
    print(f"通过率: {pass_rate:.1f}%\n")

    if test_results["failed"] > 0:
        print("失败详情:")
        for error in test_results["errors"]:
            print(f"  • {error}")

    print("\n" + "="*80)

    if pass_rate >= 80:
        print("🎉 MVP 功能 API 测试通过！")
    elif pass_rate >= 60:
        print("⚠️  MVP 功能部分通过，存在一些问题。")
    else:
        print("❌ MVP 功能测试失败，需要调试。")

    print("="*80 + "\n")

def main():
    """主测试流程"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "FieldMind MVP API 测试" + " "*37 + "║")
    print("╚" + "="*78 + "╝")

    # 检查服务器状态
    print("\n检查服务器状态...")
    if not check_server():
        print("❌ 服务器未运行，请先启动后端服务")
        print("   启动命令: cd backend && uvicorn app.main:app --reload")
        return

    print("✅ 服务器正在运行\n")

    # 获取测试项目 ID
    project_id = test_basic_apis()

    if project_id:
        # 运行功能测试
        test_data_quality_api(project_id)
        test_traceability_api(project_id)
        test_collaboration_api(project_id)
        test_knowledge_graph_api(project_id)
    else:
        print("\n⚠️  未找到测试项目，跳过功能测试")
        print("   建议：先创建一个测试项目并上传文档")

    # 打印摘要
    print_summary()

if __name__ == "__main__":
    main()
