"""
Ontology Model Unit Tests - 本体模型单元测试

验证本体模型的完整性和正确性
"""

import json
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestOntologyCompleteness:
    """测试本体模型的完整性"""

    @staticmethod
    def load_json(file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def test_schema_exists(self):
        """测试schema.json文件存在"""
        schema_path = project_root / 'ontology' / 'schema.json'
        assert schema_path.exists(), "schema.json文件不存在"
        print("✅ schema.json文件存在")

    def test_entity_count(self):
        """测试实体类型数量"""
        schema = self.load_json(project_root / 'ontology' / 'schema.json')
        entities = schema.get('entities', [])

        assert len(entities) >= 8, f"实体类型数量不足，当前: {len(entities)}, 要求: >=8"
        print(f"✅ 实体类型数量: {len(entities)}")

        # 验证必需的实体类型
        entity_types = [e['entity_type'] for e in entities]
        required_types = ['Person', 'Location', 'CulturalAsset', 'Event', 'Policy', 'Document', 'Chunk', 'Organization']

        for req_type in required_types:
            assert req_type in entity_types, f"缺少必需的实体类型: {req_type}"

        print(f"✅ 所有必需实体类型都存在: {', '.join(required_types)}")

    def test_entity_structure(self):
        """测试实体结构的完整性"""
        schema = self.load_json(project_root / 'ontology' / 'schema.json')

        for entity in schema['entities']:
            # 每个实体必须有entity_type
            assert 'entity_type' in entity, f"实体缺少entity_type"

            # 每个实体必须有id_field
            assert 'id_field' in entity, f"实体{entity['entity_type']}缺少id_field"

            # 每个实体必须有attributes
            assert 'attributes' in entity, f"实体{entity['entity_type']}缺少attributes"

            # id_field必须在attributes中
            id_field = entity['id_field']
            assert id_field in entity['attributes'], f"实体{entity['entity_type']}的id_field不在attributes中"

            # id_field必须是unique的
            id_attr = entity['attributes'][id_field]
            assert id_attr.get('unique') == True, f"实体{entity['entity_type']}的id_field不是unique的"

            print(f"✅ 实体{entity['entity_type']}结构完整")

    def test_relation_count(self):
        """测试关系类型数量"""
        schema = self.load_json(project_root / 'ontology' / 'schema.json')
        relations = schema.get('relations', [])

        assert len(relations) >= 12, f"关系类型数量不足，当前: {len(relations)}, 要求: >=12"
        print(f"✅ 关系类型数量: {len(relations)}")

    def test_relation_structure(self):
        """测试关系结构的完整性"""
        schema = self.load_json(project_root / 'ontology' / 'schema.json')

        for relation in schema['relations']:
            # 每个关系必须有relation_type
            assert 'relation_type' in relation, "关系缺少relation_type"

            # 每个关系必须有source和target
            assert 'source' in relation, f"关系{relation['relation_type']}缺少source"
            assert 'target' in relation, f"关系{relation['relation_type']}缺少target"

            # 每个关系必须有cardinality
            assert 'cardinality' in relation, f"关系{relation['relation_type']}缺少cardinality"

            # cardinality必须是合法值
            valid_cardinalities = ['one_to_one', 'one_to_many', 'many_to_one', 'many_to_many']
            assert relation['cardinality'] in valid_cardinalities, \
                f"关系{relation['relation_type']}的cardinality不合法"

            print(f"✅ 关系{relation['relation_type']}结构完整")

    def test_state_machines_exist(self):
        """测试状态机文件存在"""
        sm_path = project_root / 'ontology' / 'state_machines.json'
        assert sm_path.exists(), "state_machines.json文件不存在"
        print("✅ state_machines.json文件存在")

    def test_state_machine_count(self):
        """测试状态机数量"""
        sm = self.load_json(project_root / 'ontology' / 'state_machines.json')
        state_machines = sm.get('state_machines', [])

        assert len(state_machines) >= 2, f"状态机数量不足，当前: {len(state_machines)}, 要求: >=2"
        print(f"✅ 状态机数量: {len(state_machines)}")

    def test_state_machine_structure(self):
        """测试状态机结构"""
        sm = self.load_json(project_root / 'ontology' / 'state_machines.json')

        for machine in sm['state_machines']:
            # 必须有entity_type
            assert 'entity_type' in machine, "状态机缺少entity_type"

            # 必须有states
            assert 'states' in machine, f"状态机{machine['entity_type']}缺少states"
            assert len(machine['states']) > 0, f"状态机{machine['entity_type']}没有状态"

            # 必须有一个初始状态
            initial_states = [s for s in machine['states'] if s.get('is_initial') == True]
            assert len(initial_states) == 1, \
                f"状态机{machine['entity_type']}必须有且仅有一个初始状态，当前: {len(initial_states)}"

            # 必须有transitions
            assert 'transitions' in machine, f"状态机{machine['entity_type']}缺少transitions"

            print(f"✅ 状态机{machine['entity_type']}结构完整")

    def test_state_transition_validity(self):
        """测试状态转换的有效性"""
        sm = self.load_json(project_root / 'ontology' / 'state_machines.json')

        for machine in sm['state_machines']:
            state_names = [s['name'] for s in machine['states']]

            for transition in machine['transitions']:
                # from状态必须存在
                assert transition['from'] in state_names, \
                    f"状态机{machine['entity_type']}的转换from状态不存在: {transition['from']}"

                # to状态必须存在
                assert transition['to'] in state_names, \
                    f"状态机{machine['entity_type']}的转换to状态不存在: {transition['to']}"

            print(f"✅ 状态机{machine['entity_type']}的转换有效")

    def test_inference_rules_exist(self):
        """测试推理规则文件存在"""
        rules_path = project_root / 'ontology' / 'inference_rules.json'
        assert rules_path.exists(), "inference_rules.json文件不存在"
        print("✅ inference_rules.json文件存在")

    def test_inference_rule_count(self):
        """测试推理规则数量"""
        rules = self.load_json(project_root / 'ontology' / 'inference_rules.json')
        rule_list = rules.get('inference_rules', [])

        assert len(rule_list) >= 5, f"推理规则数量不足，当前: {len(rule_list)}, 要求: >=5"
        print(f"✅ 推理规则数量: {len(rule_list)}")

    def test_inference_rule_structure(self):
        """测试推理规则结构"""
        rules = self.load_json(project_root / 'ontology' / 'inference_rules.json')

        for rule in rules['inference_rules']:
            # 必须有rule_id
            assert 'rule_id' in rule, "推理规则缺少rule_id"

            # 必须有name
            assert 'name' in rule, f"推理规则{rule['rule_id']}缺少name"

            # 必须有conditions
            assert 'conditions' in rule, f"推理规则{rule['rule_id']}缺少conditions"

            # 必须有inference
            assert 'inference' in rule, f"推理规则{rule['rule_id']}缺少inference"

            # inference必须有action
            assert 'action' in rule['inference'], f"推理规则{rule['rule_id']}的inference缺少action"

            print(f"✅ 推理规则{rule['rule_id']}结构完整")

    def test_rule_priority(self):
        """测试推理规则优先级"""
        rules = self.load_json(project_root / 'ontology' / 'inference_rules.json')

        for rule in rules['inference_rules']:
            assert 'priority' in rule, f"推理规则{rule['rule_id']}缺少priority"

            valid_priorities = ['high', 'medium', 'low']
            assert rule['priority'] in valid_priorities, \
                f"推理规则{rule['rule_id']}的priority不合法: {rule['priority']}"

        print("✅ 所有推理规则都有合法的优先级")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始测试本体模型")
    print("="*60 + "\n")

    tester = TestOntologyCompleteness()

    tests = [
        ("schema文件存在", tester.test_schema_exists),
        ("实体类型数量", tester.test_entity_count),
        ("实体结构完整性", tester.test_entity_structure),
        ("关系类型数量", tester.test_relation_count),
        ("关系结构完整性", tester.test_relation_structure),
        ("状态机文件存在", tester.test_state_machines_exist),
        ("状态机数量", tester.test_state_machine_count),
        ("状态机结构", tester.test_state_machine_structure),
        ("状态转换有效性", tester.test_state_transition_validity),
        ("推理规则文件存在", tester.test_inference_rules_exist),
        ("推理规则数量", tester.test_inference_rule_count),
        ("推理规则结构", tester.test_inference_rule_structure),
        ("推理规则优先级", tester.test_rule_priority),
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
