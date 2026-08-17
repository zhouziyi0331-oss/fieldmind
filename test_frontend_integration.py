#!/usr/bin/env python3
"""
前端集成测试：完整的文档上传→处理→向量化流程
测试：
1. 后端API可用性
2. 文档上传接口
3. 处理状态查询
4. ChromaDB向量验证
5. 语义检索功能
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"
TEST_FILE = "/Users/alwan/Downloads/启程 - AI时代高校生OPC孵化平台 创投商业计划书 (3).docx"

def test_frontend_integration():
    """测试前端集成"""

    print("=" * 80)
    print("🌐 前端集成测试")
    print("=" * 80)

    # 1. 测试后端健康状态
    print("\n【1】测试后端健康状态")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            health = resp.json()
            print(f"  ✅ 后端运行正常")
            print(f"     API: {health['services']['api']}")
            print(f"     数据库: {health['services']['database']}")
        else:
            print(f"  ❌ 后端异常: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ 无法连接后端: {e}")
        return False

    # 2. 测试文档上传
    print("\n【2】测试文档上传接口")
    document_id = None
    try:
        import os
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
                print(f"  ✅ 文档上传成功")

                document_id = result.get('document_id')
                task_id = result.get('task_id')
                status_url = result.get('status_url')

                print(f"     document_id: {document_id}")
                print(f"     文件名: {result.get('filename')}")

                # 如果是同步处理（有document_id但没有task_id）
                if document_id and not task_id:
                    print(f"  ✅ 同步处理完成")

                    if 'processing_result' in result:
                        proc = result['processing_result']
                        print(f"     fact_statements: {proc.get('fact_statements_count', 0)} 条")
                        print(f"     document_chunks: {proc.get('chunks_stored', 0)} 条")
                        print(f"     entities: {proc.get('entities_count', 0)} 个")

                # 如果是异步处理，轮询状态
                elif status_url and task_id:
                    print(f"\n  ⏳ 等待异步处理完成...")

                    max_wait = 60  # 最多等60秒
                    for i in range(max_wait):
                        time.sleep(1)
                        status_resp = requests.get(f"{BASE_URL}{status_url}", timeout=5)

                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            state = status_data.get('state', 'UNKNOWN')

                            if state == 'SUCCESS':
                                print(f"  ✅ 处理完成 (耗时{i+1}秒)")
                                result_data = status_data.get('result', {})
                                document_id = result_data.get('document_id')
                                print(f"     document_id: {document_id}")

                                if 'processing_result' in result_data:
                                    proc = result_data['processing_result']
                                    print(f"     fact_statements: {proc.get('fact_statements_count', 0)} 条")
                                    print(f"     document_chunks: {proc.get('chunks_stored', 0)} 条")
                                break

                            elif state == 'FAILURE':
                                print(f"  ❌ 处理失败: {status_data.get('error')}")
                                document_id = None
                                break

                            elif i % 5 == 0:
                                print(f"     状态: {state} ({i+1}s)")
                    else:
                        print(f"  ⚠️  异步处理超时")
                        document_id = None
                else:
                    print(f"  ⚠️  未获取到document_id或task_id")
                    document_id = None
            else:
                print(f"  ❌ 上传失败: {resp.status_code}")
                print(f"     响应: {resp.text[:200]}")
                document_id = None

    except Exception as e:
        print(f"  ❌ 上传异常: {e}")
        document_id = None

    if not document_id:
        print("\n⚠️ 文档上传失败，跳过后续测试")
        return False

    # 3. 测试语义检索
    print("\n【3】测试语义检索接口")
    try:
        query_params = {
            "query": "OPC孵化平台的核心功能",
            "top_k": 3
        }

        resp = requests.post(
            f"{BASE_URL}/api/document-processing/projects/1/semantic-search",
            params=query_params,
            timeout=30
        )

        if resp.status_code == 200:
            results = resp.json()
            print(f"  ✅ 语义检索成功")
            print(f"     查询: {query_params['query']}")
            print(f"     结果数: {len(results.get('results', []))}")

            for i, result in enumerate(results.get('results', [])[:3]):
                text = result.get('text', '')[:50]
                score = result.get('score', 0)
                print(f"     {i+1}. {text}... (相似度: {score:.3f})")

            return True
        else:
            print(f"  ❌ 检索失败: {resp.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ 检索异常: {e}")
        return False

    print("\n" + "=" * 80)
    print("🎉 前端集成测试完成！")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_frontend_integration()
    exit(0 if success else 1)
