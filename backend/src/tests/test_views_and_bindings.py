"""
Views and Bindings Tests - 视图和绑定测试

验证 P1 阶段的语义视图和数据绑定
"""

import json
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestViewsAndBindings:
    """测试视图和绑定的完整性"""

    @staticmethod
    def load_json(file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_views_directory_exists(self):
        """测试views目录存在"""
        views_dir = project_root / 'views'
        assert views_dir.exists(), "views目录不存在"
        print("✅ views目录存在")

    def test_view_count(self):
        """测试视图数量"""
        views_dir = project_root / 'views'
        view_files = list(views_dir.glob('*.json'))

        assert len(view_files) >= 6, f"视图数量不足，当前: {len(view_files)}, 要求: >=6"
        print(f"✅ 视图数量: {len(view_files)}")

        # 验证必需的视图
        required_views = [
            'cultural_heritage_health_view.json',
            'person_network_view.json',
            'location_assets_view.json',
            'policy_impact_view.json',
            'timeline_view.json',
            'dimension_analysis_view.json'
        ]

        for required_view in required_views:
            view_path = views_dir / required_view
            assert view_path.exists(), f"缺少必需的视图: {required_view}"

        print(f"✅ 所有必需视图都存在: {', '.join(required_views)}")

    def test_view_structure(self):
        """测试视图结构的完整性"""
        views_dir = project_root / 'views'
        view_files = list(views_dir.glob('*.json'))

        for view_file in view_files:
            view = self.load_json(view_file)

            # 必需字段
            required_fields = ['view_id', 'name', 'version', 'description', 'intent', 'input', 'output', 'data_bindings']

            for field in required_fields:
                assert field in view, f"视图{view_file.name}缺少字段: {field}"

            # input必须有required
            assert 'required' in view['input'], f"视图{view_file.name}的input缺少required"

            # output必须是字典
            assert isinstance(view['output'], dict), f"视图{view_file.name}的output不是字典"

            # data_bindings必须是数组且非空
            assert isinstance(view['data_bindings'], list), f"视图{view_file.name}的data_bindings不是数组"
            assert len(view['data_bindings']) > 0, f"视图{view_file.name}的data_bindings为空"

            print(f"✅ 视图{view_file.name}结构完整")

    def test_bindings_directory_exists(self):
        """测试bindings目录存在"""
        bindings_dir = project_root / 'bindings'
        assert bindings_dir.exists(), "bindings目录不存在"
        print("✅ bindings目录存在")

    def test_binding_count(self):
        """测试绑定配置数量"""
        bindings_dir = project_root / 'bindings'
        binding_files = list(bindings_dir.glob('*.json'))

        assert len(binding_files) >= 4, f"绑定配置数量不足，当前: {len(binding_files)}, 要求: >=4"
        print(f"✅ 绑定配置数量: {len(binding_files)}")

        # 验证必需的绑定
        required_bindings = [
            'neo4j_graph_binding.json',
            'sqlite_sql_binding.json',
            'chromadb_vector_binding.json',
            'sqlite_fulltext_binding.json'
        ]

        for required_binding in required_bindings:
            binding_path = bindings_dir / required_binding
            assert binding_path.exists(), f"缺少必需的绑定配置: {required_binding}"

        print(f"✅ 所有必需绑定配置都存在: {', '.join(required_bindings)}")

    def test_binding_structure(self):
        """测试绑定配置结构"""
        bindings_dir = project_root / 'bindings'
        binding_files = list(bindings_dir.glob('*.json'))

        for binding_file in binding_files:
            binding = self.load_json(binding_file)

            # 必需字段
            required_fields = ['binding_id', 'binding_name', 'version', 'channel_type', 'connection']

            for field in required_fields:
                assert field in binding, f"绑定{binding_file.name}缺少字段: {field}"

            # channel_type必须是合法值
            valid_channel_types = ['graph', 'sql', 'vector', 'fulltext']
            assert binding['channel_type'] in valid_channel_types, \
                f"绑定{binding_file.name}的channel_type不合法: {binding['channel_type']}"

            # connection必须是字典
            assert isinstance(binding['connection'], dict), \
                f"绑定{binding_file.name}的connection不是字典"

            print(f"✅ 绑定{binding_file.name}结构完整")

    def test_view_binding_consistency(self):
        """测试视图和绑定的一致性"""
        views_dir = project_root / 'views'
        bindings_dir = project_root / 'bindings'

        view_files = list(views_dir.glob('*.json'))
        bindings = {self.load_json(b)['binding_id']: b.name for b in bindings_dir.glob('*.json')}

        # 收集所有视图中使用的 channel_type
        used_channel_types = set()

        for view_file in view_files:
            view = self.load_json(view_file)

            for binding_def in view['data_bindings']:
                channel_type = binding_def.get('channel_type')
                if channel_type:
                    used_channel_types.add(channel_type)

        print(f"\n视图使用的channel_type: {used_channel_types}")

        # 验证每种 channel_type 都有对应的绑定配置
        binding_channel_types = {self.load_json(bindings_dir / b)['channel_type'] for b in bindings.values()}

        for channel_type in used_channel_types:
            assert channel_type in binding_channel_types, \
                f"缺少 {channel_type} 类型的绑定配置"

        print("✅ 所有视图使用的channel_type都有对应的绑定配置")

    def test_view_input_output_types(self):
        """测试视图的输入输出类型定义"""
        views_dir = project_root / 'views'
        view_files = list(views_dir.glob('*.json'))

        for view_file in view_files:
            view = self.load_json(view_file)

            # 检查input中的required参数
            for param in view['input']['required']:
                assert 'name' in param, f"视图{view_file.name}的required参数缺少name"
                assert 'type' in param, f"视图{view_file.name}的required参数缺少type"

            # 检查output中的字段定义
            for field_name, field_def in view['output'].items():
                assert 'type' in field_def, f"视图{view_file.name}的output字段{field_name}缺少type"
                assert 'source' in field_def, f"视图{view_file.name}的output字段{field_name}缺少source"

            print(f"✅ 视图{view_file.name}的输入输出类型定义完整")

    def test_view_data_binding_references(self):
        """测试视图中的data_binding引用"""
        views_dir = project_root / 'views'
        view_files = list(views_dir.glob('*.json'))

        for view_file in view_files:
            view = self.load_json(view_file)

            for binding_def in view['data_bindings']:
                # 每个绑定必须有 binding_id
                assert 'binding_id' in binding_def, \
                    f"视图{view_file.name}的data_binding缺少binding_id"

                # 每个绑定必须有 channel_type
                assert 'channel_type' in binding_def, \
                    f"视图{view_file.name}的data_binding缺少channel_type"

                # 每个绑定必须有 output_mapping
                assert 'output_mapping' in binding_def, \
                    f"视图{view_file.name}的data_binding缺少output_mapping"

            print(f"✅ 视图{view_file.name}的data_binding引用完整")

    def test_view_test_cases(self):
        """测试视图是否包含测试用例"""
        views_dir = project_root / 'views'
        view_files = list(views_dir.glob('*.json'))

        for view_file in view_files:
            view = self.load_json(view_file)

            # 应该有 test_cases
            assert 'test_cases' in view, f"视图{view_file.name}缺少test_cases"
            assert len(view['test_cases']) > 0, f"视图{view_file.name}的test_cases为空"

            for test_case in view['test_cases']:
                assert 'name' in test_case, f"视图{view_file.name}的test_case缺少name"
                assert 'input' in test_case, f"视图{view_file.name}的test_case缺少input"
                assert 'expected_output' in test_case, f"视图{view_file.name}的test_case缺少expected_output"

            print(f"✅ 视图{view_file.name}包含测试用例")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试视图和绑定")
    print("="*60 + "\n")

    tester = TestViewsAndBindings()

    tests = [
        ("views目录存在", tester.test_views_directory_exists),
        ("视图数量", tester.test_view_count),
        ("视图结构完整性", tester.test_view_structure),
        ("bindings目录存在", tester.test_bindings_directory_exists),
        ("绑定配置数量", tester.test_binding_count),
        ("绑定配置结构", tester.test_binding_structure),
        ("视图和绑定一致性", tester.test_view_binding_consistency),
        ("视图输入输出类型", tester.test_view_input_output_types),
        ("视图data_binding引用", tester.test_view_data_binding_references),
        ("视图测试用例", tester.test_view_test_cases),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n测试: {test_name}")
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 错误: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
