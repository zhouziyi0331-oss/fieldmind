"""
Phase 4: 手动验证脚本

由于pytest未安装，使用此脚本进行手动验证
运行方式: cd /Users/alwan/FieldMind/backend/src && python -m tests.test_phase4_manual_verification
"""

import sys
import warnings
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def test_tool_imports():
    """测试1: 验证工具函数可以正确导入"""
    print("\n" + "="*60)
    print("测试1: 工具函数导入测试")
    print("="*60)

    results = []

    # 测试transcript工具
    try:
        from app.tools.transcript import transcribe_audio, clean_transcript, extract_metrics
        print("✅ app.tools.transcript 导入成功")
        print(f"   - transcribe_audio: {transcribe_audio.__name__}")
        print(f"   - clean_transcript: {clean_transcript.__name__}")
        print(f"   - extract_metrics: {extract_metrics.__name__}")
        results.append(('transcript', True))
    except Exception as e:
        print(f"❌ app.tools.transcript 导入失败: {e}")
        results.append(('transcript', False))

    # 测试entity工具
    try:
        from app.tools.entity import extract_entities
        print("✅ app.tools.entity 导入成功")
        print(f"   - extract_entities: {extract_entities.__name__}")
        results.append(('entity', True))
    except Exception as e:
        print(f"❌ app.tools.entity 导入失败: {e}")
        results.append(('entity', False))

    # 测试relation工具
    try:
        from app.tools.relation import extract_relations
        print("✅ app.tools.relation 导入成功")
        print(f"   - extract_relations: {extract_relations.__name__}")
        results.append(('relation', True))
    except Exception as e:
        print(f"❌ app.tools.relation 导入失败: {e}")
        results.append(('relation', False))

    # 测试summary工具
    try:
        from app.tools.summary import analyze_with_skills
        print("✅ app.tools.summary 导入成功")
        print(f"   - analyze_with_skills: {analyze_with_skills.__name__}")
        results.append(('summary', True))
    except Exception as e:
        print(f"❌ app.tools.summary 导入失败: {e}")
        results.append(('summary', False))

    return results


def test_deprecation_warnings():
    """测试2: 验证废弃警告"""
    print("\n" + "="*60)
    print("测试2: 废弃警告测试")
    print("="*60)

    results = []

    # 测试KnowledgeAgent废弃警告
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            from app.services.agents.knowledge_agent import KnowledgeAgent as OldKnowledgeAgent
            agent = OldKnowledgeAgent()

            deprecation_warnings = [warning for warning in w
                                   if issubclass(warning.category, DeprecationWarning)]

            if deprecation_warnings:
                print(f"✅ KnowledgeAgent 废弃警告正常触发")
                print(f"   警告信息: {deprecation_warnings[0].message}")
                results.append(('knowledge_agent_warning', True))
            else:
                print("⚠️  KnowledgeAgent 未触发废弃警告")
                results.append(('knowledge_agent_warning', False))

    except Exception as e:
        print(f"❌ KnowledgeAgent 测试失败: {e}")
        results.append(('knowledge_agent_warning', False))

    # 测试Coordinator废弃警告
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            from app.services.agents.coordinator_agent import EnhancedCoordinatorAgent
            agent = EnhancedCoordinatorAgent()

            deprecation_warnings = [warning for warning in w
                                   if issubclass(warning.category, DeprecationWarning)]

            if deprecation_warnings:
                print(f"✅ Coordinator 废弃警告正常触发")
                print(f"   警告信息: {deprecation_warnings[0].message}")
                results.append(('coordinator_warning', True))
            else:
                print("⚠️  Coordinator 未触发废弃警告")
                results.append(('coordinator_warning', False))

    except Exception as e:
        print(f"❌ Coordinator 测试失败: {e}")
        results.append(('coordinator_warning', False))

    return results


def test_v2_agent_tool_integration():
    """测试3: 验证v2 Agent可以找到新工具"""
    print("\n" + "="*60)
    print("测试3: v2 Agent工具集成测试")
    print("="*60)

    results = []

    # 测试IngestionAgent
    try:
        from app.agents.v2.ingestion_agent import IngestionAgent
        agent = IngestionAgent()

        # 检查_extract_audio方法是否存在
        if hasattr(agent, '_extract_audio'):
            print("✅ IngestionAgent._extract_audio 方法存在")

            # 检查方法中是否引用了新工具
            import inspect
            source = inspect.getsource(agent._extract_audio)
            if 'transcribe_audio' in source:
                print("   ✓ 方法中包含 transcribe_audio 调用")
                results.append(('ingestion_tool_integration', True))
            else:
                print("   ⚠️ 方法中未找到 transcribe_audio 调用")
                results.append(('ingestion_tool_integration', False))
        else:
            print("❌ IngestionAgent._extract_audio 方法不存在")
            results.append(('ingestion_tool_integration', False))

    except Exception as e:
        print(f"❌ IngestionAgent 测试失败: {e}")
        results.append(('ingestion_tool_integration', False))

    # 测试KnowledgeAgent
    try:
        from app.agents.v2.knowledge_agent import KnowledgeAgent
        agent = KnowledgeAgent()

        if hasattr(agent, '_build_comprehensive'):
            print("✅ KnowledgeAgent._build_comprehensive 方法存在")

            import inspect
            source = inspect.getsource(agent._build_comprehensive)
            has_entity = 'extract_entities' in source
            has_relation = 'extract_relations' in source

            if has_entity:
                print("   ✓ 方法中包含 extract_entities 调用")
            if has_relation:
                print("   ✓ 方法中包含 extract_relations 调用")

            results.append(('knowledge_tool_integration', has_entity and has_relation))
        else:
            print("❌ KnowledgeAgent._build_comprehensive 方法不存在")
            results.append(('knowledge_tool_integration', False))

    except Exception as e:
        print(f"❌ KnowledgeAgent 测试失败: {e}")
        results.append(('knowledge_tool_integration', False))

    # 测试ReportAgent
    try:
        from app.agents.v2.report_agent import ReportAgent
        agent = ReportAgent()

        if hasattr(agent, '_prepare_skill_results'):
            print("✅ ReportAgent._prepare_skill_results 方法存在")

            import inspect
            source = inspect.getsource(agent._prepare_skill_results)
            if 'analyze_with_skills' in source:
                print("   ✓ 方法中包含 analyze_with_skills 调用")
                results.append(('report_tool_integration', True))
            else:
                print("   ⚠️ 方法中未找到 analyze_with_skills 调用")
                results.append(('report_tool_integration', False))
        else:
            print("❌ ReportAgent._prepare_skill_results 方法不存在")
            results.append(('report_tool_integration', False))

    except Exception as e:
        print(f"❌ ReportAgent 测试失败: {e}")
        results.append(('report_tool_integration', False))

    return results


def test_tool_function_signatures():
    """测试4: 验证工具函数签名正确"""
    print("\n" + "="*60)
    print("测试4: 工具函数签名验证")
    print("="*60)

    results = []

    try:
        from app.tools.transcript import transcribe_audio
        import inspect
        sig = inspect.signature(transcribe_audio)
        params = list(sig.parameters.keys())

        expected = ['file_path', 'file_type', 'language', 'enable_metrics', 'enable_cleaning']
        if all(p in params for p in expected):
            print(f"✅ transcribe_audio 签名正确: {params}")
            results.append(('transcribe_audio_sig', True))
        else:
            print(f"⚠️ transcribe_audio 签名不完整: {params}")
            results.append(('transcribe_audio_sig', False))
    except Exception as e:
        print(f"❌ transcribe_audio 签名检查失败: {e}")
        results.append(('transcribe_audio_sig', False))

    try:
        from app.tools.entity import extract_entities
        import inspect
        sig = inspect.signature(extract_entities)
        params = list(sig.parameters.keys())

        if 'text' in params:
            print(f"✅ extract_entities 签名正确: {params}")
            results.append(('extract_entities_sig', True))
        else:
            print(f"⚠️ extract_entities 缺少text参数: {params}")
            results.append(('extract_entities_sig', False))
    except Exception as e:
        print(f"❌ extract_entities 签名检查失败: {e}")
        results.append(('extract_entities_sig', False))

    try:
        from app.tools.relation import extract_relations
        import inspect
        sig = inspect.signature(extract_relations)
        params = list(sig.parameters.keys())

        if 'text' in params:
            print(f"✅ extract_relations 签名正确: {params}")
            results.append(('extract_relations_sig', True))
        else:
            print(f"⚠️ extract_relations 缺少text参数: {params}")
            results.append(('extract_relations_sig', False))
    except Exception as e:
        print(f"❌ extract_relations 签名检查失败: {e}")
        results.append(('extract_relations_sig', False))

    try:
        from app.tools.summary import analyze_with_skills
        import inspect
        sig = inspect.signature(analyze_with_skills)
        params = list(sig.parameters.keys())

        if 'content' in params:
            print(f"✅ analyze_with_skills 签名正确: {params}")
            results.append(('analyze_with_skills_sig', True))
        else:
            print(f"⚠️ analyze_with_skills 缺少content参数: {params}")
            results.append(('analyze_with_skills_sig', False))
    except Exception as e:
        print(f"❌ analyze_with_skills 签名检查失败: {e}")
        results.append(('analyze_with_skills_sig', False))

    return results


def print_summary(all_results):
    """打印测试总结"""
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    total = 0
    passed = 0

    for test_results in all_results:
        for name, success in test_results:
            total += 1
            if success:
                passed += 1

    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"成功率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n✅ Phase 4 验证全部通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试未通过")
        return 1


def main():
    """主测试流程"""
    print("="*60)
    print("Phase 4: 工具函数集成 - 手动验证")
    print("="*60)

    all_results = []

    # 运行所有测试
    all_results.append(test_tool_imports())
    all_results.append(test_deprecation_warnings())
    all_results.append(test_v2_agent_tool_integration())
    all_results.append(test_tool_function_signatures())

    # 打印总结
    exit_code = print_summary(all_results)

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
