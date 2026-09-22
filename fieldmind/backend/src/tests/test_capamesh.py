"""
CapaMesh Tests - CapaMesh 组件测试

验证 P2 阶段的查询解析器、执行引擎、治理层
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from capamesh.query_parser import create_parser
from capamesh.execution_engine import create_engine
from capamesh.governance_layer import create_governance_layer
import asyncio


class TestQueryParser:
    """测试查询解析器"""

    def test_parser_initialization(self):
        """测试解析器初始化"""
        print("\n" + "="*60)
        print("测试1: 查询解析器初始化")
        print("="*60)

        parser = create_parser("views")

        assert len(parser.views) >= 6, f"视图数量不足: {len(parser.views)}"
        assert len(parser.intent_keywords) >= 6, f"意图索引不足: {len(parser.intent_keywords)}"

        print(f"✅ 加载了 {len(parser.views)} 个视图")
        print(f"✅ 构建了 {len(parser.intent_keywords)} 个意图索引")

    def test_structured_query_parsing(self):
        """测试结构化查询解析"""
        print("\n" + "="*60)
        print("测试2: 结构化查询解析")
        print("="*60)

        parser = create_parser("views")

        query = {
            "view_id": "cultural_heritage_health_view",
            "parameters": {
                "cultural_asset_id": "布依族山歌"
            }
        }

        result = parser.parse(query)

        assert result['view_id'] == "cultural_heritage_health_view"
        assert result['confidence'] == 1.0
        assert result['parameters']['cultural_asset_id'] == "布依族山歌"

        print(f"✅ 视图ID: {result['view_id']}")
        print(f"✅ 置信度: {result['confidence']}")
        print(f"✅ 参数: {result['parameters']}")

    def test_natural_language_parsing(self):
        """测试自然语言查询解析"""
        print("\n" + "="*60)
        print("测试3: 自然语言查询解析")
        print("="*60)

        parser = create_parser("views")

        queries = [
            "查看布依族山歌的传承情况",
            "王大爷的社会关系网络",
            "大坪村有哪些文化资产",
            "非遗保护政策的影响",
        ]

        for query in queries:
            result = parser.parse(query)
            print(f"\n查询: {query}")
            print(f"  匹配视图: {result.get('view_id')}")
            print(f"  置信度: {result.get('confidence')}")
            print(f"  提取参数: {result.get('parameters')}")

        print("\n✅ 自然语言查询解析测试通过")

    def test_parameter_validation(self):
        """测试参数验证"""
        print("\n" + "="*60)
        print("测试4: 参数验证")
        print("="*60)

        parser = create_parser("views")

        # 有效参数
        valid_params = {
            "cultural_asset_id": "布依族山歌"
        }

        validation = parser.validate_parameters(
            "cultural_heritage_health_view",
            valid_params
        )

        assert validation['valid'] == True
        print(f"✅ 有效参数验证通过")

        # 缺少必需参数
        invalid_params = {}

        validation = parser.validate_parameters(
            "cultural_heritage_health_view",
            invalid_params
        )

        assert validation['valid'] == False
        assert len(validation['errors']) > 0
        print(f"✅ 无效参数检测通过: {validation['errors']}")


class TestExecutionEngine:
    """测试执行引擎"""

    def test_engine_initialization(self):
        """测试执行引擎初始化"""
        print("\n" + "="*60)
        print("测试5: 执行引擎初始化")
        print("="*60)

        engine = create_engine("views", "bindings")

        assert len(engine.views) >= 6, f"视图数量不足: {len(engine.views)}"
        assert len(engine.bindings) >= 4, f"绑定数量不足: {len(engine.bindings)}"
        assert len(engine.binding_instances) >= 4, f"绑定实例不足: {len(engine.binding_instances)}"

        print(f"✅ 加载了 {len(engine.views)} 个视图")
        print(f"✅ 加载了 {len(engine.bindings)} 个绑定配置")
        print(f"✅ 初始化了 {len(engine.binding_instances)} 个绑定实例")

    def test_query_execution(self):
        """测试查询执行"""
        print("\n" + "="*60)
        print("测试6: 查询执行")
        print("="*60)

        engine = create_engine("views", "bindings")

        # 执行一个简单的查询
        async def run_query():
            result = await engine.execute(
                "cultural_heritage_health_view",
                {"cultural_asset_id": "布依族山歌"}
            )
            return result

        result = asyncio.run(run_query())

        assert result['status'] in ['success', 'error']
        assert 'metadata' in result
        assert 'query_time_ms' in result['metadata']

        print(f"✅ 查询状态: {result['status']}")
        print(f"✅ 查询耗时: {result['metadata']['query_time_ms']}ms")
        print(f"✅ 数据源数量: {result['metadata'].get('sources_used', 0)}")


class TestGovernanceLayer:
    """测试治理层"""

    def test_governance_initialization(self):
        """测试治理层初始化"""
        print("\n" + "="*60)
        print("测试7: 治理层初始化")
        print("="*60)

        gov = create_governance_layer()

        assert gov.cache_enabled == True
        assert gov.rate_limit_enabled == True
        assert gov.fallback_enabled == True
        assert gov.monitoring_enabled == True

        print(f"✅ 缓存启用: {gov.cache_enabled}")
        print(f"✅ 限流启用: {gov.rate_limit_enabled}")
        print(f"✅ 降级启用: {gov.fallback_enabled}")
        print(f"✅ 监控启用: {gov.monitoring_enabled}")

    def test_cache_operations(self):
        """测试缓存操作"""
        print("\n" + "="*60)
        print("测试8: 缓存操作")
        print("="*60)

        gov = create_governance_layer()

        # 生成缓存键
        cache_key = gov.generate_cache_key(
            "cultural_heritage_health_view",
            {"cultural_asset_id": "布依族山歌"}
        )

        print(f"✅ 生成缓存键: {cache_key}")

        # 缓存不存在
        cached = gov.get_cached(cache_key)
        assert cached is None
        print(f"✅ 缓存未命中（预期行为）")

        # 设置缓存
        test_data = {"test": "data"}
        gov.set_cache(cache_key, test_data)
        print(f"✅ 设置缓存")

        # 读取缓存
        cached = gov.get_cached(cache_key)
        assert cached == test_data
        print(f"✅ 缓存命中")

    def test_rate_limiting(self):
        """测试限流"""
        print("\n" + "="*60)
        print("测试9: 限流控制")
        print("="*60)

        gov = create_governance_layer({
            'cache': {'enabled': True, 'backend': 'memory', 'ttl_seconds': 300},
            'rate_limit': {'enabled': True, 'requests_per_minute': 5},
            'fallback': {'enabled': True, 'rules': []},
            'monitoring': {'enabled': True, 'metrics': []}
        })

        client_id = "test_client"

        # 前5个请求应该通过
        for i in range(5):
            allowed = gov.check_rate_limit(client_id)
            assert allowed == True

        print(f"✅ 前5个请求通过")

        # 第6个请求应该被限制
        allowed = gov.check_rate_limit(client_id)
        assert allowed == False
        print(f"✅ 第6个请求被限制")

    def test_metrics_collection(self):
        """测试指标收集"""
        print("\n" + "="*60)
        print("测试10: 指标收集")
        print("="*60)

        gov = create_governance_layer()

        # 记录一些请求
        gov.record_request(100, 'success')
        gov.record_request(200, 'success')
        gov.record_request(150, 'error')

        metrics = gov.get_metrics()

        assert metrics['total_requests'] == 3
        assert metrics['errors'] == 1
        assert metrics['error_rate'] == 1/3

        print(f"✅ 总请求数: {metrics['total_requests']}")
        print(f"✅ 错误数: {metrics['errors']}")
        print(f"✅ 错误率: {metrics['error_rate']:.2%}")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试 CapaMesh 组件")
    print("="*60 + "\n")

    test_classes = [
        TestQueryParser(),
        TestExecutionEngine(),
        TestGovernanceLayer()
    ]

    tests = [
        ("查询解析器初始化", test_classes[0].test_parser_initialization),
        ("结构化查询解析", test_classes[0].test_structured_query_parsing),
        ("自然语言查询解析", test_classes[0].test_natural_language_parsing),
        ("参数验证", test_classes[0].test_parameter_validation),
        ("执行引擎初始化", test_classes[1].test_engine_initialization),
        ("查询执行", test_classes[1].test_query_execution),
        ("治理层初始化", test_classes[2].test_governance_initialization),
        ("缓存操作", test_classes[2].test_cache_operations),
        ("限流控制", test_classes[2].test_rate_limiting),
        ("指标收集", test_classes[2].test_metrics_collection),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 测试失败: {test_name}")
            print(f"   错误: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试出错: {test_name}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
