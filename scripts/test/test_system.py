#!/usr/bin/env python3
"""
系统测试脚本

测试各个组件的基本功能
"""

import os
import sys
import requests
import time
from pathlib import Path

# API 基础 URL
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health_check():
    """测试健康检查端点"""
    print_section("测试 1: 健康检查")

    try:
        response = requests.get(f"{API_BASE_URL}/health")

        if response.status_code == 200:
            data = response.json()
            print("✓ 健康检查通过")
            print(f"  状态: {data.get('status')}")
            print(f"  数据库: {data.get('database')}")
            print(f"  向量数据库: {data.get('vector_db')}")
            return True
        else:
            print(f"✗ 健康检查失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 健康检查失败: {e}")
        return False


def test_document_upload():
    """测试文档上传"""
    print_section("测试 2: 文档上传")

    try:
        # 创建测试文本文件
        test_file_path = Path("test_document.txt")
        test_content = """
        十八洞村位于湖南省湘西土家族苗族自治州花垣县。
        这里是苗族聚居地，保留着丰富的苗族文化传统。
        苗族山歌是当地重要的文化遗产，世代相传。
        村民们通过山歌表达情感，记录历史，传承文化。
        """

        test_file_path.write_text(test_content, encoding='utf-8')

        # 上传文件
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {
                'title': '十八洞村文化调查测试',
                'auto_process': 'true'
            }

            response = requests.post(
                f"{API_BASE_URL}/api/v1/documents/upload",
                files=files,
                data=data
            )

        # 清理测试文件
        test_file_path.unlink()

        if response.status_code == 200:
            doc = response.json()
            print("✓ 文档上传成功")
            print(f"  文档 ID: {doc.get('id')}")
            print(f"  标题: {doc.get('title')}")
            print(f"  状态: {doc.get('status')}")
            return doc.get('id')
        else:
            print(f"✗ 文档上传失败: HTTP {response.status_code}")
            print(f"  错误: {response.text}")
            return None

    except Exception as e:
        print(f"✗ 文档上传失败: {e}")
        return None


def test_document_list(document_id=None):
    """测试文档列表"""
    print_section("测试 3: 文档列表")

    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/documents/")

        if response.status_code == 200:
            data = response.json()
            print("✓ 获取文档列表成功")
            print(f"  总文档数: {data.get('total')}")

            if data.get('documents'):
                print(f"  最新文档:")
                for doc in data['documents'][:3]:
                    print(f"    - [{doc['id']}] {doc['title']} ({doc['status']})")

            return True
        else:
            print(f"✗ 获取文档列表失败: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"✗ 获取文档列表失败: {e}")
        return False


def test_chat(document_id=None):
    """测试对话系统"""
    print_section("测试 4: 智能对话")

    try:
        payload = {
            'query': '十八洞村在哪里？有什么特色文化？',
            'top_k': 3
        }

        if document_id:
            payload['document_ids'] = [document_id]

        response = requests.post(
            f"{API_BASE_URL}/api/v1/chat/chat",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ 对话查询成功")
            print(f"  会话 ID: {data.get('session_id')}")
            print(f"  答案: {data.get('answer')[:200]}...")
            print(f"  引用来源: {len(data.get('sources', []))} 个")
            return data.get('session_id')
        else:
            print(f"✗ 对话查询失败: HTTP {response.status_code}")
            print(f"  错误: {response.text}")
            return None

    except Exception as e:
        print(f"✗ 对话查询失败: {e}")
        return None


def test_context_generation(document_id=None):
    """测试知识脉络生成"""
    print_section("测试 5: 知识脉络生成")

    if not document_id:
        print("⚠ 跳过测试（需要文档 ID）")
        return None

    try:
        payload = {
            'context_type': 'cultural',
            'document_ids': [document_id]
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/contexts/generate",
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ 知识脉络生成成功")
            print(f"  脉络 ID: {data.get('id')}")
            print(f"  类型: {data.get('context_type')}")
            print(f"  标题: {data.get('title')}")
            return data.get('id')
        else:
            print(f"✗ 知识脉络生成失败: HTTP {response.status_code}")
            print(f"  错误: {response.text}")
            return None

    except Exception as e:
        print(f"✗ 知识脉络生成失败: {e}")
        return None


def test_report_generation(document_id=None, context_id=None):
    """测试报告生成"""
    print_section("测试 6: 分析报告生成")

    if not document_id:
        print("⚠ 跳过测试（需要文档 ID）")
        return None

    try:
        payload = {
            'document_ids': [document_id],
            'tiers': [1],  # 只测试第一层报告
            'export_format': 'html'
        }

        if context_id:
            payload['context_ids'] = [context_id]

        print("  正在生成报告（这可能需要一些时间）...")

        response = requests.post(
            f"{API_BASE_URL}/api/v1/reports/generate",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ 报告生成成功")

            report = data.get('report', {})
            metadata = report.get('metadata', {})

            print(f"  报告 ID: {metadata.get('report_id')}")
            print(f"  生成时间: {metadata.get('generated_at')}")

            if data.get('export_path'):
                print(f"  导出路径: {data.get('export_path')}")

            return metadata.get('report_id')
        else:
            print(f"✗ 报告生成失败: HTTP {response.status_code}")
            print(f"  错误: {response.text}")
            return None

    except Exception as e:
        print(f"✗ 报告生成失败: {e}")
        return None


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("  知识脉络分析系统 - 功能测试")
    print("=" * 60)
    print(f"\nAPI 地址: {API_BASE_URL}")
    print("请确保系统已启动并运行在上述地址")

    input("\n按 Enter 键开始测试...")

    # 测试结果
    results = {
        'health_check': False,
        'document_upload': False,
        'document_list': False,
        'chat': False,
        'context_generation': False,
        'report_generation': False
    }

    # 1. 健康检查
    results['health_check'] = test_health_check()
    if not results['health_check']:
        print("\n✗ 健康检查失败，请确保系统正常运行")
        sys.exit(1)

    time.sleep(1)

    # 2. 文档上传
    document_id = test_document_upload()
    results['document_upload'] = document_id is not None

    time.sleep(2)

    # 3. 文档列表
    results['document_list'] = test_document_list(document_id)

    time.sleep(1)

    # 4. 对话系统
    session_id = test_chat(document_id)
    results['chat'] = session_id is not None

    time.sleep(1)

    # 5. 知识脉络
    context_id = test_context_generation(document_id)
    results['context_generation'] = context_id is not None

    time.sleep(1)

    # 6. 报告生成
    report_id = test_report_generation(document_id, context_id)
    results['report_generation'] = report_id is not None

    # 测试总结
    print_section("测试总结")

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests / total_tests * 100:.1f}%")

    print("\n详细结果:")
    for test_name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {test_name}: {status}")

    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查系统配置和日志。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
