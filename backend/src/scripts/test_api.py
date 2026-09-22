#!/usr/bin/env python3
"""
API端点测试脚本

测试所有API接口：
1. 健康检查
2. 视图查询
3. 向量搜索
4. 全文搜索
5. 混合搜索
6. 实体和关系查询
7. 缓存管理
8. 系统信息
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def test_health_check():
    """测试健康检查"""
    print_section("测试 1: 健康检查")

    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"服务状态: {data['status']}")
        print(f"时间戳: {data['timestamp']}")
        print("服务列表:")
        for service, status in data['services'].items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {service}: {status}")
        return True
    else:
        print(f"❌ 健康检查失败")
        return False


def test_list_views():
    """测试列出视图"""
    print_section("测试 2: 列出所有视图")

    response = requests.get(f"{BASE_URL}/api/v1/views")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"视图数量: {data['count']}")
        print("\n可用视图:")
        for view in data['views']:
            print(f"  - {view['view_id']}: {view['name']}")
        return data['views']
    else:
        print(f"❌ 列出视图失败")
        return []


def test_execute_view(views):
    """测试执行视图"""
    print_section("测试 3: 执行视图查询")

    if not views:
        print("⚠️ 没有可用的视图")
        return False

    # 测试第一个视图
    test_view = views[0]
    print(f"测试视图: {test_view['view_id']}")

    # 根据视图准备参数
    parameters = {}
    if test_view['view_id'] == 'cultural_asset_detail':
        parameters = {"asset_name": "花鼓戏"}
    elif test_view['view_id'] == 'person_network':
        parameters = {"person_name": "王大爷"}
    elif test_view['view_id'] == 'location_cultural_summary':
        parameters = {"location_name": "苗寨"}

    print(f"参数: {parameters}")

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/v1/views/execute",
        json={
            "view_id": test_view['view_id'],
            "parameters": parameters
        }
    )
    elapsed_ms = (time.time() - start_time) * 1000

    print(f"状态码: {response.status_code}")
    print(f"响应时间: {elapsed_ms:.2f}ms")

    if response.status_code == 200:
        data = response.json()
        print(f"执行状态: {data['status']}")
        print(f"查询时间: {data['metadata']['query_time_ms']}ms")
        print(f"缓存命中: {data['metadata']['cache_hit']}")
        print(f"数据源数量: {data['metadata']['sources_used']}")
        return True
    else:
        print(f"❌ 视图执行失败: {response.text}")
        return False


def test_vector_search():
    """测试向量搜索"""
    print_section("测试 4: 向量语义搜索")

    query = "民族文化传承"
    print(f"查询: {query}")

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/v1/search/vector",
        json={
            "query": query,
            "n_results": 5
        }
    )
    elapsed_ms = (time.time() - start_time) * 1000

    print(f"状态码: {response.status_code}")
    print(f"响应时间: {elapsed_ms:.2f}ms")

    if response.status_code == 200:
        data = response.json()
        print(f"结果数量: {data['count']}")

        if data['count'] > 0:
            print("\n前3个结果:")
            for i in range(min(3, data['count'])):
                doc_id = data['results']['ids'][i]
                distance = data['results']['distances'][i]
                doc = data['results']['documents'][i][:60]
                print(f"  {i+1}. ID={doc_id}, 距离={distance:.4f}")
                print(f"     {doc}...")
        return True
    else:
        print(f"❌ 向量搜索失败: {response.text}")
        return False


def test_fulltext_search():
    """测试全文搜索"""
    print_section("测试 5: 全文关键词搜索")

    query = "fieldmind"
    print(f"查询: {query}")

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/v1/search/fulltext",
        json={
            "query": query,
            "limit": 5,
            "highlight": True
        }
    )
    elapsed_ms = (time.time() - start_time) * 1000

    print(f"状态码: {response.status_code}")
    print(f"响应时间: {elapsed_ms:.2f}ms")

    if response.status_code == 200:
        data = response.json()
        print(f"结果数量: {data['count']}")

        if data['count'] > 0:
            print("\n前3个结果:")
            for i, result in enumerate(data['results'][:3], 1):
                print(f"  {i}. ID={result['chunk_id']}, Rank={result['rank']:.4f}")
                print(f"     {result['text'][:60]}...")
        return True
    else:
        print(f"❌ 全文搜索失败: {response.text}")
        return False


def test_hybrid_search():
    """测试混合搜索"""
    print_section("测试 6: 混合搜索（向量+全文）")

    query = "文化传承"
    print(f"查询: {query}")

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/api/v1/search/hybrid",
        json={
            "query": query,
            "n_results": 10
        }
    )
    elapsed_ms = (time.time() - start_time) * 1000

    print(f"状态码: {response.status_code}")
    print(f"响应时间: {elapsed_ms:.2f}ms")

    if response.status_code == 200:
        data = response.json()
        print(f"向量搜索结果: {data['vector_results']['count']} 个")
        print(f"全文搜索结果: {data['fulltext_results']['count']} 个")
        print(f"共同结果: {len(data['common'])} 个")
        print(f"总唯一结果: {len(data['total_unique'])} 个")
        return True
    else:
        print(f"❌ 混合搜索失败: {response.text}")
        return False


def test_query_entities():
    """测试实体查询"""
    print_section("测试 7: 实体查询")

    response = requests.post(
        f"{BASE_URL}/api/v1/entities/query",
        json={
            "entity_type": "Person",
            "limit": 5
        }
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"实体数量: {data['count']}")

        if data['count'] > 0:
            print("\n前3个实体:")
            for i, entity in enumerate(data['entities'][:3], 1):
                print(f"  {i}. {entity['name']} ({entity['entity_type']})")
        return True
    else:
        print(f"❌ 实体查询失败: {response.text}")
        return False


def test_query_relations():
    """测试关系查询"""
    print_section("测试 8: 关系查询")

    response = requests.post(
        f"{BASE_URL}/api/v1/relations/query",
        json={
            "limit": 5
        }
    )

    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"关系数量: {data['count']}")

        if data['count'] > 0:
            print("\n前3个关系:")
            for i, rel in enumerate(data['relations'][:3], 1):
                print(f"  {i}. {rel['source_name']} --[{rel['relation_type']}]--> {rel['target_name']}")
        return True
    else:
        print(f"❌ 关系查询失败: {response.text}")
        return False


def test_cache_stats():
    """测试缓存统计"""
    print_section("测试 9: 缓存统计")

    response = requests.get(f"{BASE_URL}/api/v1/cache/stats")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if data['enabled']:
            stats = data['stats']
            print("缓存统计:")
            print(f"  命中: {stats['hits']}")
            print(f"  未命中: {stats['misses']}")
            print(f"  命中率: {stats['hit_rate']:.2%}")
            print(f"  设置: {stats['sets']}")
            print(f"  删除: {stats['deletes']}")
        else:
            print("⚠️ 缓存未启用")

        return True
    else:
        print(f"❌ 获取缓存统计失败: {response.text}")
        return False


def test_system_info():
    """测试系统信息"""
    print_section("测试 10: 系统信息")

    response = requests.get(f"{BASE_URL}/api/v1/system/info")
    print(f"状态码: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"API版本: {data['api_version']}")
        print(f"时间戳: {data['timestamp']}")

        if 'execution_engine' in data:
            ee = data['execution_engine']
            print(f"\n执行引擎:")
            print(f"  视图数: {ee['views_count']}")
            print(f"  绑定数: {ee['bindings_count']}")
            print(f"  Neo4j: {'✅' if ee['neo4j_connected'] else '❌'}")
            print(f"  SQLite: {'✅' if ee['sqlite_connected'] else '❌'}")

        if 'vector_store' in data:
            vs = data['vector_store']
            print(f"\n向量存储:")
            print(f"  文档数: {vs['document_count']}")
            print(f"  集合名: {vs['collection_name']}")

        if 'cache' in data:
            cache = data['cache']
            print(f"\n缓存:")
            print(f"  启用: {'✅' if cache['enabled'] else '❌'}")

        return True
    else:
        print(f"❌ 获取系统信息失败: {response.text}")
        return False


def main():
    """运行所有测试"""
    print("="*60)
    print("FieldMind CapaMesh API 测试")
    print("="*60)
    print(f"API地址: {BASE_URL}")
    print()

    # 检查API是否运行
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            print(f"❌ API未运行或无法访问")
            print(f"请先启动API: python api_server.py")
            return
    except Exception as e:
        print(f"❌ 无法连接到API: {e}")
        print(f"请先启动API: python api_server.py")
        return

    results = []

    # 运行所有测试
    results.append(("健康检查", test_health_check()))

    views = test_list_views()
    results.append(("列出视图", len(views) > 0))

    results.append(("执行视图", test_execute_view(views)))
    results.append(("向量搜索", test_vector_search()))
    results.append(("全文搜索", test_fulltext_search()))
    results.append(("混合搜索", test_hybrid_search()))
    results.append(("实体查询", test_query_entities()))
    results.append(("关系查询", test_query_relations()))
    results.append(("缓存统计", test_cache_stats()))
    results.append(("系统信息", test_system_info()))

    # 汇总结果
    print_section("测试结果汇总")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n通过: {passed}/{total}")
    print()

    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"  {icon} {name}")

    print("\n" + "="*60)
    if passed == total:
        print("✅ 所有测试通过")
    else:
        print(f"⚠️ {total - passed} 个测试失败")
    print("="*60)


if __name__ == "__main__":
    main()
