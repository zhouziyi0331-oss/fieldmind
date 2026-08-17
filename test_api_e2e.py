#!/usr/bin/env python3
"""
API端到端测试

测试覆盖：
1. 健康检查API
2. 文档上传API
3. 文档处理状态查询API
4. 语义检索API
5. 知识图谱查询API
6. 统计数据API
"""

import requests
import time
import os

BASE_URL = "http://localhost:8000"
TEST_FILE = "/Users/alwan/Downloads/启程 - AI时代高校生OPC孵化平台 创投商业计划书 (3).docx"

def test_api_e2e():
    print("=" * 80)
    print("🌐 API 端到端测试")
    print("=" * 80)

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "tests": []
    }

    # Test 1: 健康检查API
    print("\n【Test 1】健康检查 API - GET /health")
    results["total"] += 1
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] == "healthy"
            assert "services" in data
            print("  ✅ PASSED")
            print(f"     状态: {data['status']}")
            print(f"     服务: API={data['services']['api']}, DB={data['services']['database']}")
            results["passed"] += 1
            results["tests"].append({"name": "健康检查", "status": "PASSED"})
        else:
            print(f"  ❌ FAILED: HTTP {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"name": "健康检查", "status": "FAILED"})
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["failed"] += 1
        results["tests"].append({"name": "健康检查", "status": "FAILED"})

    # Test 2: 文档上传API
    print("\n【Test 2】文档上传 API - POST /api/v1/documents/upload")
    results["total"] += 1
    document_id = None
    try:
        with open(TEST_FILE, 'rb') as f:
            filename = os.path.basename(TEST_FILE)
            files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            data = {'project_id': 1}

            resp = requests.post(
                f"{BASE_URL}/api/v1/documents/upload",
                files=files,
                data=data,
                timeout=300
            )

            if resp.status_code == 200:
                result = resp.json()
                document_id = result.get('document_id')
                assert document_id is not None
                print("  ✅ PASSED")
                print(f"     document_id: {document_id}")
                print(f"     chunks: {result.get('processing_result', {}).get('chunks_stored', 0)}")
                results["passed"] += 1
                results["tests"].append({"name": "文档上传", "status": "PASSED"})
            else:
                print(f"  ❌ FAILED: HTTP {resp.status_code}")
                print(f"     响应: {resp.text[:200]}")
                results["failed"] += 1
                results["tests"].append({"name": "文档上传", "status": "FAILED"})
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["failed"] += 1
        results["tests"].append({"name": "文档上传", "status": "FAILED"})

    if not document_id:
        print("\n⚠️ 文档上传失败，跳过后续依赖测试")
        return results

    # Test 3: 语义检索API
    print("\n【Test 3】语义检索 API - POST /api/document-processing/projects/{project_id}/semantic-search")
    results["total"] += 1
    try:
        query_params = {
            "query": "OPC孵化平台的核心功能",
            "top_k": 5
        }

        resp = requests.post(
            f"{BASE_URL}/api/document-processing/projects/1/semantic-search",
            params=query_params,
            timeout=30
        )

        if resp.status_code == 200:
            result = resp.json()
            assert "results" in result
            assert result["total_results"] >= 0
            print("  ✅ PASSED")
            print(f"     查询: {query_params['query']}")
            print(f"     结果数: {result['total_results']}")
            if result["results"]:
                print(f"     最高相似度: {result['results'][0].get('score', 0):.3f}")
            results["passed"] += 1
            results["tests"].append({"name": "语义检索", "status": "PASSED"})
        else:
            print(f"  ❌ FAILED: HTTP {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"name": "语义检索", "status": "FAILED"})
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["failed"] += 1
        results["tests"].append({"name": "语义检索", "status": "FAILED"})

    # Test 4: 知识图谱查询API
    print("\n【Test 4】知识图谱查询 API - GET /api/knowledge-graph/entities")
    results["total"] += 1
    try:
        resp = requests.get(
            f"{BASE_URL}/api/knowledge-graph/entities",
            params={"project_id": 1, "limit": 10},
            timeout=10
        )

        if resp.status_code == 200:
            result = resp.json()
            print("  ✅ PASSED")
            print(f"     实体数: {len(result) if isinstance(result, list) else result.get('total', 0)}")
            results["passed"] += 1
            results["tests"].append({"name": "知识图谱查询", "status": "PASSED"})
        else:
            print(f"  ❌ FAILED: HTTP {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"name": "知识图谱查询", "status": "FAILED"})
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["failed"] += 1
        results["tests"].append({"name": "知识图谱查询", "status": "FAILED"})

    # Test 5: 文档统计API
    print("\n【Test 5】文档统计 API - GET /api/document-processing/projects/{project_id}/chunks/statistics")
    results["total"] += 1
    try:
        resp = requests.get(
            f"{BASE_URL}/api/document-processing/projects/1/chunks/statistics",
            timeout=10
        )

        if resp.status_code == 200:
            result = resp.json()
            print("  ✅ PASSED")
            print(f"     统计数据: {result}")
            results["passed"] += 1
            results["tests"].append({"name": "文档统计", "status": "PASSED"})
        else:
            print(f"  ❌ FAILED: HTTP {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"name": "文档统计", "status": "FAILED"})
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["failed"] += 1
        results["tests"].append({"name": "文档统计", "status": "FAILED"})

    # Test 6: 关键词搜索API
    print("\n【Test 6】关键词搜索 API - POST /api/keyword-search/projects/{project_id}/search")
    results["total"] += 1
    try:
        search_data = {
            "keyword": "AI孵化",
            "limit": 5
        }

        resp = requests.post(
            f"{BASE_URL}/api/keyword-search/projects/1/search",
            json=search_data,
            timeout=10
        )

        if resp.status_code == 200:
            result = resp.json()
            print("  ✅ PASSED")
            print(f"     查询: {search_data['keyword']}")
            print(f"     结果: {result.get('total', 0)} 条")
            results["passed"] += 1
            results["tests"].append({"name": "关键词搜索", "status": "PASSED"})
        else:
            print(f"  ❌ FAILED: HTTP {resp.status_code}")
            results["failed"] += 1
            results["tests"].append({"name": "关键词搜索", "status": "FAILED"})
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        results["failed"] += 1
        results["tests"].append({"name": "关键词搜索", "status": "FAILED"})

    # 测试总结
    print("\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print(f"总测试数: {results['total']}")
    print(f"通过: {results['passed']} ✅")
    print(f"失败: {results['failed']} ❌")
    print(f"通过率: {results['passed']/results['total']*100:.1f}%")

    print("\n详细结果:")
    for test in results["tests"]:
        status_icon = "✅" if test["status"] == "PASSED" else "❌"
        print(f"  {status_icon} {test['name']}: {test['status']}")

    print("=" * 80)

    return results["failed"] == 0

if __name__ == "__main__":
    success = test_api_e2e()
    exit(0 if success else 1)
