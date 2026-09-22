#!/usr/bin/env python3
"""
CapaMesh 端到端测试脚本

测试流程：
1. 检查数据源连接（Neo4j, SQLite）
2. 测试执行引擎的查询功能
3. 测试推理引擎
4. 输出完整的执行报告
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from capamesh.execution_engine import ExecutionEngine


async def test_datasource_connections():
    """测试数据源连接"""
    print("\n" + "="*60)
    print("步骤 1: 测试数据源连接")
    print("="*60)

    engine = ExecutionEngine(
        views_dir="capamesh/views",
        bindings_dir="capamesh/bindings"
    )

    # 测试 Neo4j
    if engine.neo4j_driver:
        print("✅ Neo4j 连接成功")
        try:
            with engine.neo4j_driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                print(f"   Neo4j 测试查询: {record['test']}")
        except Exception as e:
            print(f"❌ Neo4j 查询失败: {e}")
    else:
        print("❌ Neo4j 未连接")

    # 测试 SQLite
    if engine.sqlite_conn:
        print("✅ SQLite 连接成功")
        try:
            cursor = engine.sqlite_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            count = cursor.fetchone()[0]
            print(f"   SQLite chunks 数量: {count}")
        except Exception as e:
            print(f"❌ SQLite 查询失败: {e}")
    else:
        print("❌ SQLite 未连接")

    return engine


async def test_neo4j_query(engine: ExecutionEngine):
    """测试 Neo4j 查询执行"""
    print("\n" + "="*60)
    print("步骤 2: 测试 Neo4j 查询执行")
    print("="*60)

    # 测试查询：获取所有 Person 节点
    query = """
    MATCH (p:Person)
    RETURN p
    LIMIT 5
    """

    print(f"执行查询: {query.strip()}")
    result = await engine._execute_neo4j_query(query, {})

    print(f"\n查询结果:")
    print(f"  节点数量: {len(result.get('nodes', []))}")
    print(f"  记录数量: {len(result.get('records', []))}")

    if result.get('nodes'):
        print(f"\n前 3 个节点:")
        for i, node in enumerate(result['nodes'][:3], 1):
            print(f"  {i}. {node.get('_labels', [])} - {node.get('name', 'N/A')}")

    return result


async def test_view_execution(engine: ExecutionEngine):
    """测试视图执行"""
    print("\n" + "="*60)
    print("步骤 3: 测试视图执行")
    print("="*60)

    # 列出所有可用视图
    print(f"\n可用视图: {len(engine.views)}")
    for view_id in engine.views.keys():
        print(f"  - {view_id}")

    # 测试执行一个视图（如果存在）
    if engine.views:
        view_id = list(engine.views.keys())[0]
        print(f"\n测试执行视图: {view_id}")

        # 构造测试参数
        parameters = {
            "asset_id": "test_asset_001",
            "person_name": "王大爷"
        }

        result = await engine.execute(view_id, parameters)

        print(f"\n执行结果:")
        print(f"  状态: {result.get('status')}")
        print(f"  耗时: {result.get('metadata', {}).get('query_time_ms')} ms")
        print(f"  数据源数量: {result.get('metadata', {}).get('sources_used')}")

        if result.get('status') == 'success':
            print(f"\n输出数据:")
            data = result.get('data', {})
            for key, value in list(data.items())[:5]:
                print(f"  {key}: {value}")

        return result
    else:
        print("⚠️  没有可用的视图")
        return None


async def test_inference_engine(engine: ExecutionEngine):
    """测试推理引擎"""
    print("\n" + "="*60)
    print("步骤 4: 测试推理引擎")
    print("="*60)

    # 构造测试视图和数据
    test_view = {
        "view_id": "test_inference",
        "inference_logic": {
            "count_items": {
                "type": "aggregation",
                "operation": "count",
                "source_field": "items",
                "depends_on": ["items"],
                "target_field": "item_count"
            },
            "average_score": {
                "type": "aggregation",
                "operation": "average",
                "source_field": "scores",
                "avg_field": "value",
                "depends_on": ["scores"],
                "target_field": "avg_score"
            },
            "risk_level": {
                "type": "classification",
                "depends_on": ["avg_score"],
                "rules": [
                    {"condition": "avg_score >= 8", "result": "高危"},
                    {"condition": "avg_score >= 5", "result": "中危"},
                    {"condition": "avg_score >= 0", "result": "低危"}
                ],
                "target_field": "risk_level"
            }
        }
    }

    test_data = {
        "items": [
            {"name": "item1", "value": 10},
            {"name": "item2", "value": 20},
            {"name": "item3", "value": 30}
        ],
        "scores": [
            {"value": 7.5},
            {"value": 8.2},
            {"value": 6.8}
        ]
    }

    print("测试数据:")
    print(f"  items 数量: {len(test_data['items'])}")
    print(f"  scores 数量: {len(test_data['scores'])}")

    result = await engine._execute_inference(test_view, test_data.copy())

    print(f"\n推理结果:")
    print(f"  item_count: {result.get('item_count')}")
    print(f"  avg_score: {result.get('avg_score')}")
    print(f"  risk_level: {result.get('risk_level')}")

    return result


async def test_sqlite_query(engine: ExecutionEngine):
    """测试 SQLite 查询"""
    print("\n" + "="*60)
    print("步骤 5: 测试 SQLite 查询")
    print("="*60)

    query = """
    SELECT id, text, chunk_index
    FROM document_chunks
    LIMIT 3
    """

    print(f"执行查询: {query.strip()}")
    result = await engine._execute_sqlite_query(query, {})

    print(f"\n查询结果:")
    print(f"  行数: {result.get('count')}")
    print(f"  列: {', '.join(result.get('columns', []))}")

    if result.get('rows'):
        print(f"\n前 3 行:")
        for i, row in enumerate(result['rows'][:3], 1):
            print(f"  {i}. ID={row.get('id')}, Index={row.get('chunk_index')}")
            text = row.get('text', '')[:50]
            print(f"     Text: {text}...")

    return result


async def generate_summary_report(engine: ExecutionEngine):
    """生成汇总报告"""
    print("\n" + "="*60)
    print("汇总报告")
    print("="*60)

    # 统计 Neo4j 数据
    neo4j_stats = {}
    if engine.neo4j_driver:
        try:
            with engine.neo4j_driver.session() as session:
                # 节点统计
                result = session.run("MATCH (n) RETURN count(n) as count")
                neo4j_stats['nodes'] = result.single()['count']

                # 关系统计
                result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                neo4j_stats['relationships'] = result.single()['count']

                # 标签统计
                result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
                neo4j_stats['labels'] = result.single()['labels']
        except Exception as e:
            print(f"⚠️  Neo4j 统计失败: {e}")

    # 统计 SQLite 数据
    sqlite_stats = {}
    if engine.sqlite_conn:
        try:
            cursor = engine.sqlite_conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM document_chunks")
            sqlite_stats['chunks'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM chunk_entities")
            sqlite_stats['entities'] = cursor.fetchone()[0]

            try:
                cursor.execute("SELECT COUNT(*) FROM entity_relations")
                sqlite_stats['relations'] = cursor.fetchone()[0]
            except:
                sqlite_stats['relations'] = 0
        except Exception as e:
            print(f"⚠️  SQLite 统计失败: {e}")

    print("\nNeo4j 数据统计:")
    print(f"  节点: {neo4j_stats.get('nodes', 0)}")
    print(f"  关系: {neo4j_stats.get('relationships', 0)}")
    print(f"  标签: {', '.join(neo4j_stats.get('labels', []))[:100]}...")

    print("\nSQLite 数据统计:")
    print(f"  Chunks: {sqlite_stats.get('chunks', 0)}")
    print(f"  Entities: {sqlite_stats.get('entities', 0)}")
    print(f"  Relations: {sqlite_stats.get('relations', 0)}")

    print("\nCapaMesh 组件:")
    print(f"  视图数量: {len(engine.views)}")
    print(f"  绑定数量: {len(engine.bindings)}")
    print(f"  推理引擎: ✅ 已加载")

    return {
        'neo4j': neo4j_stats,
        'sqlite': sqlite_stats,
        'capamesh': {
            'views': len(engine.views),
            'bindings': len(engine.bindings)
        }
    }


async def main():
    """主测试流程"""
    print("="*60)
    print("CapaMesh 端到端测试")
    print("="*60)

    try:
        # 1. 测试数据源连接
        engine = await test_datasource_connections()

        # 2. 测试 Neo4j 查询
        await test_neo4j_query(engine)

        # 3. 测试 SQLite 查询
        await test_sqlite_query(engine)

        # 4. 测试推理引擎
        await test_inference_engine(engine)

        # 5. 测试视图执行
        await test_view_execution(engine)

        # 6. 生成汇总报告
        summary = await generate_summary_report(engine)

        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)

        # 关闭连接
        engine.close()

        return summary

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
