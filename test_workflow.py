#!/usr/bin/env python3
"""
FieldMind工作流测试脚本
测试各个自动触发链路是否正常工作
"""

import os
import sys
import time
import requests
from pathlib import Path

# API基础URL
BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def check_services():
    """检查所有必需服务是否运行"""
    print_section("1. 检查服务状态")

    services = {
        "FastAPI": f"{BASE_URL}/health",
        "Redis": "redis://localhost:6379",
        "Neo4j": "http://localhost:7474",
        "Ollama": "http://localhost:11434/api/tags",
    }

    for name, url in services.items():
        try:
            if url.startswith("redis://"):
                import redis
                r = redis.from_url(url)
                r.ping()
                print(f"✓ {name} 运行正常")
            elif name == "Neo4j":
                from neo4j import GraphDatabase
                driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
                driver.verify_connectivity()
                print(f"✓ {name} 运行正常")
            else:
                response = requests.get(url, timeout=5)
                if response.status_code < 400:
                    print(f"✓ {name} 运行正常")
                else:
                    print(f"✗ {name} 响应异常: {response.status_code}")
        except Exception as e:
            print(f"✗ {name} 无法连接: {e}")
            return False

    return True

def test_document_workflow():
    """测试文档处理工作流"""
    print_section("2. 测试文档处理工作流")

    # 创建测试文件
    test_file = Path("/tmp/test_document.txt")
    test_file.write_text("""
    这是一个测试文档。

    方言保护是一项重要的文化工作。在中国，各地方言丰富多样，
    包括粤语、闽南语、吴语等。保护方言需要多方面的努力。

    主要参与者：
    - 张伟（研究员）
    - 北京大学语言研究所
    - 中国方言保护协会
    """, encoding='utf-8')

    print(f"创建测试文件: {test_file}")

    # 上传文档
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            response = requests.post(
                f"{BASE_URL}/api/v1/documents/upload",
                files=files,
                timeout=30
            )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 文档上传成功")
            print(f"  任务ID: {result.get('task_id')}")
            print(f"  状态URL: {result.get('status_url')}")

            # 查询任务状态
            task_id = result.get('task_id')
            if task_id:
                print(f"\n等待任务完成...")
                for i in range(30):  # 最多等待30秒
                    time.sleep(1)
                    status_response = requests.get(
                        f"{BASE_URL}/api/v1/documents/status/{task_id}",
                        timeout=5
                    )
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        state = status_data.get('state', 'UNKNOWN')
                        print(f"  [{i+1}s] 状态: {state}")

                        if state == 'SUCCESS':
                            print(f"✓ 文档处理完成")
                            print(f"  结果: {status_data.get('result', {})}")
                            return True
                        elif state == 'FAILURE':
                            print(f"✗ 文档处理失败: {status_data.get('result')}")
                            return False

                print(f"⚠ 任务超时（30秒）")
                return False
        else:
            print(f"✗ 文档上传失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_audio_workflow():
    """测试音频处理工作流"""
    print_section("3. 测试音频处理工作流（模拟）")

    print("⚠ 音频处理需要真实音频文件，此处仅测试API端点")

    try:
        # 测试API端点是否存在
        response = requests.post(
            f"{BASE_URL}/api/v1/audio/upload",
            files={'file': ('test.txt', b'fake audio', 'audio/mpeg')},
            timeout=10
        )

        if response.status_code in [200, 422]:  # 422表示验证失败，但端点存在
            print(f"✓ 音频API端点存在")
            return True
        else:
            print(f"✗ 音频API异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_crawler_workflow():
    """测试爬虫工作流"""
    print_section("4. 测试爬虫工作流")

    # 使用一个简单的测试URL
    test_url = "https://example.com"

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/crawler/crawl",
            json={"url": test_url, "auto_process": True},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 爬虫任务提交成功")
            print(f"  任务ID: {result.get('task_id')}")

            # 等待任务完成
            task_id = result.get('task_id')
            if task_id:
                print(f"\n等待爬取完成...")
                for i in range(30):
                    time.sleep(1)
                    status_response = requests.get(
                        f"{BASE_URL}/api/v1/crawler/status/{task_id}",
                        timeout=5
                    )
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        state = status_data.get('state', 'UNKNOWN')
                        print(f"  [{i+1}s] 状态: {state}")

                        if state == 'SUCCESS':
                            print(f"✓ 爬取完成")
                            return True
                        elif state == 'FAILURE':
                            print(f"✗ 爬取失败: {status_data.get('result')}")
                            return False

                print(f"⚠ 任务超时（30秒）")
                return False
        else:
            print(f"✗ 爬虫任务提交失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_rag_workflow():
    """测试RAG查询工作流"""
    print_section("5. 测试RAG查询工作流")

    test_query = "方言保护的主要挑战有哪些？"

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rag/query",
            json={"query": test_query, "top_k": 5},
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ RAG查询成功")
            print(f"  答案: {result.get('answer', '')[:100]}...")
            print(f"  来源数: {len(result.get('sources', []))}")
            return True
        else:
            print(f"✗ RAG查询失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_report_workflow():
    """测试报告生成工作流"""
    print_section("6. 测试报告生成工作流（模拟）")

    print("⚠ 报告生成需要已有数据，此处仅测试API端点")

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/reports/generate",
            json={
                "title": "测试报告",
                "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
                "include_charts": True,
                "format": ["word"]
            },
            timeout=10
        )

        if response.status_code in [200, 422]:
            print(f"✓ 报告生成API端点存在")
            return True
        else:
            print(f"✗ 报告生成API异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_knowledge_graph():
    """测试知识图谱查询"""
    print_section("7. 测试知识图谱查询")

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )

        with driver.session() as session:
            # 查询节点数量
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            print(f"✓ 知识图谱连接成功")
            print(f"  节点数量: {count}")

            # 查询关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()["count"]
            print(f"  关系数量: {rel_count}")

            return True
    except Exception as e:
        print(f"✗ 知识图谱测试异常: {e}")
        return False

def check_celery_workers():
    """检查Celery Worker状态"""
    print_section("8. 检查Celery Worker状态")

    try:
        from app.celery_app import celery_app

        # 获取活跃worker
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()

        if active_workers:
            print(f"✓ Celery Worker运行正常")
            for worker_name, tasks in active_workers.items():
                print(f"  Worker: {worker_name}")
                print(f"    活跃任务数: {len(tasks)}")
            return True
        else:
            print(f"✗ 没有活跃的Celery Worker")
            print(f"  请运行: celery -A app.celery_app worker -Q documents,audio,crawler,rag,graph,reports,default --loglevel=info")
            return False
    except Exception as e:
        print(f"✗ Celery检查异常: {e}")
        return False

def main():
    """主测试流程"""
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " "*15 + "FieldMind 工作流测试" + " "*23 + "║")
    print("╚" + "═"*58 + "╝")

    # 测试结果统计
    results = {}

    # 1. 检查服务
    results['services'] = check_services()
    if not results['services']:
        print("\n⚠ 请先启动所有必需服务:")
        print("  ./start_services.sh")
        print("  celery -A app.celery_app worker -Q documents,audio,crawler,rag,graph,reports,default --loglevel=info")
        print("  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)

    # 2. 检查Celery Worker
    results['celery'] = check_celery_workers()

    # 3. 测试各个工作流
    results['document'] = test_document_workflow()
    results['audio'] = test_audio_workflow()
    results['crawler'] = test_crawler_workflow()
    results['rag'] = test_rag_workflow()
    results['report'] = test_report_workflow()
    results['graph'] = test_knowledge_graph()

    # 汇总结果
    print_section("测试汇总")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name.ljust(15)}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！工作流运行正常。")
        return 0
    else:
        print("\n⚠ 部分测试失败，请检查日志。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
