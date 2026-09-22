#!/usr/bin/env python3
"""
Data Governance System Verification Script
Checks all components and reports system health
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

import sqlite3
from app.config import settings


def check_module_imports():
    """Check if all governance modules can be imported"""
    print("\n1. 模块导入检查 (Module Import Check)")
    print("=" * 60)

    modules = [
        ("app.models.governance", "Governance Models"),
        ("app.agents.ingestion_agent", "Ingestion Agent"),
        ("app.orchestration.data_governance_orchestrator", "Data Governance Orchestrator"),
        ("app.services.lineage_tracker", "Lineage Tracker"),
        ("app.services.metadata_collector", "Metadata Collector"),
        ("app.services.structured_processor", "Structured Processor"),
    ]

    passed = 0
    failed = []

    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {display_name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {display_name}: {e}")
            failed.append(display_name)

    print(f"\n  结果: {passed}/{len(modules)} 通过")
    return len(failed) == 0, failed


def check_plugin_registration():
    """Check if all 18 ingestion plugins are registered"""
    print("\n2. 插件注册检查 (Plugin Registration Check)")
    print("=" * 60)

    try:
        from app.agents.ingestion_agent import get_ingestion_agent

        agent = get_ingestion_agent()
        plugins = agent.list_plugins()  # Returns unique plugin class names

        # Expected 18 plugin class names
        expected_plugins = [
            'PDFPlugin', 'DOCXPlugin', 'PPTPlugin', 'ExcelPlugin', 'TextPlugin',
            'MarkdownPlugin', 'HTMLPlugin', 'RTFPlugin', 'ImagePlugin',
            'AudioPlugin', 'VideoPlugin', 'CSVPlugin', 'JSONPlugin',
            'XMLPlugin', 'EPUBPlugin', 'ZIPPlugin', 'EmailPlugin', 'CodePlugin'
        ]

        print(f"  注册的插件: {len(plugins)}")
        print(f"  支持的格式: {len(agent.plugins)} 种")

        missing = [p for p in expected_plugins if p not in plugins]
        extra = [p for p in plugins if p not in expected_plugins]

        for plugin_name in sorted(plugins):
            # Count formats supported by this plugin
            formats = sum(1 for fmt, p in agent.plugins.items() if p.plugin_name == plugin_name)
            print(f"    • {plugin_name}: {formats} formats")

        if missing:
            print(f"\n  ⚠ 缺失插件: {missing}")
        if extra:
            print(f"  ℹ 额外插件: {extra}")

        success = len(plugins) >= 18 and len(missing) == 0
        print(f"\n  结果: {'✓ 通过' if success else '✗ 失败'}")
        return success, missing

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False, [str(e)]


def check_database_tables():
    """Check if all governance tables exist"""
    print("\n3. 数据库表检查 (Database Tables Check)")
    print("=" * 60)

    try:
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        existing_tables = {row[0] for row in cursor.fetchall()}

        required_tables = {
            'metric_dictionary',
            'lineage_edges',
            'metric_calculation_history',
            'quality_rules',
            'quality_check_results',
            'change_events',
            'governance_metadata'
        }

        missing = required_tables - existing_tables

        print(f"  数据库总表数: {len(existing_tables)}")
        print(f"  治理表数: {len(required_tables)}")

        for table in sorted(required_tables):
            status = "✓" if table in existing_tables else "✗"
            print(f"    {status} {table}")

        if missing:
            print(f"\n  ⚠ 缺失表: {missing}")

        conn.close()

        success = len(missing) == 0
        print(f"\n  结果: {'✓ 通过' if success else '✗ 失败'}")
        return success, list(missing)

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False, [str(e)]


def check_metric_dictionary():
    """Check metric dictionary initialization"""
    print("\n4. 指标字典检查 (Metric Dictionary Check)")
    print("=" * 60)

    try:
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check table structure
        cursor.execute("PRAGMA table_info(metric_dictionary)")
        columns = {row[1] for row in cursor.fetchall()}

        required_columns = {
            'metric_id', 'metric_name', 'metric_category', 'definition',
            'calculation_rule', 'unit', 'value_range', 'applicable_doc_types', 'priority'
        }

        missing_cols = required_columns - columns

        if missing_cols:
            print(f"  ✗ 缺失字段: {missing_cols}")
            conn.close()
            return False, list(missing_cols)

        print(f"  ✓ 表结构完整 ({len(columns)} 字段)")

        # Check metric count by category
        cursor.execute("""
            SELECT metric_category, COUNT(*) as cnt
            FROM metric_dictionary
            GROUP BY metric_category
            ORDER BY cnt DESC
        """)

        categories = cursor.fetchall()
        total_metrics = sum(cat[1] for cat in categories)

        print(f"\n  总指标数: {total_metrics}")
        for category, count in categories:
            print(f"    • {category}: {count}")

        # Check if core 6 categories exist
        expected_categories = {'structural', 'emotion', 'style', 'content', 'quality', 'temporal'}
        actual_categories = {cat[0] for cat in categories}
        missing_categories = expected_categories - actual_categories

        if missing_categories:
            print(f"\n  ⚠ 缺失类别: {missing_categories}")

        conn.close()

        success = total_metrics >= 20 and len(missing_categories) == 0
        print(f"\n  结果: {'✓ 通过' if success else '✗ 失败'}")
        return success, list(missing_categories) if missing_categories else []

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False, [str(e)]


def check_structured_processor_integration():
    """Check StructuredProcessor integration"""
    print("\n5. StructuredProcessor集成检查 (Integration Check)")
    print("=" * 60)

    try:
        from app.services.structured_processor import StructuredProcessor
        import inspect

        # Get full source code of the class
        source = inspect.getsource(StructuredProcessor)

        integrations = {
            'IngestionAgent': 'ingestion_agent' in source.lower() or 'get_ingestion_agent' in source,
            'LineageTracker': 'lineage_tracker' in source.lower() or 'from app.services.lineage_tracker' in source,
            'MetadataCollector': 'metadata_collector' in source.lower() or 'from app.services.metadata_collector' in source,
        }

        for component, integrated in integrations.items():
            status = "✓" if integrated else "✗"
            print(f"  {status} {component}")

        all_integrated = all(integrations.values())
        print(f"\n  结果: {'✓ 通过' if all_integrated else '✗ 失败'}")
        return all_integrated, [k for k, v in integrations.items() if not v]

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False, [str(e)]


def check_orchestrator():
    """Check DataGovernanceOrchestrator implementation"""
    print("\n6. 编排器检查 (Orchestrator Check)")
    print("=" * 60)

    try:
        from app.orchestration.data_governance_orchestrator import DataGovernanceOrchestrator
        import inspect

        orchestrator = DataGovernanceOrchestrator()

        # Check all 8 stages exist
        stages = [
            '_stage_ingestion',
            '_stage_metadata',
            '_stage_chunking',
            '_stage_metrics',
            '_stage_vectorization',
            '_stage_knowledge',
            '_stage_lineage',
            '_stage_quality'
        ]

        missing_stages = []
        for stage in stages:
            if hasattr(orchestrator, stage):
                print(f"  ✓ {stage}")
            else:
                print(f"  ✗ {stage}")
                missing_stages.append(stage)

        success = len(missing_stages) == 0
        print(f"\n  结果: {'✓ 通过' if success else '✗ 失败'}")
        return success, missing_stages

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False, [str(e)]


def check_extended_fields():
    """Check extended fields in documents and document_chunks"""
    print("\n7. 扩展字段检查 (Extended Fields Check)")
    print("=" * 60)

    try:
        db_path = settings.DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check documents extended fields
        cursor.execute("PRAGMA table_info(documents)")
        doc_columns = {row[1] for row in cursor.fetchall()}

        doc_extended_fields = {
            'file_hash', 'total_words', 'total_sentences', 'total_paragraphs',
            'language', 'speaker_count', 'collection_device', 'collection_location'
        }

        doc_missing = doc_extended_fields - doc_columns

        print(f"  documents表扩展字段:")
        for field in sorted(doc_extended_fields):
            status = "✓" if field in doc_columns else "✗"
            print(f"    {status} {field}")

        # Check document_chunks extended fields
        cursor.execute("PRAGMA table_info(document_chunks)")
        chunk_columns = {row[1] for row in cursor.fetchall()}

        chunk_extended_fields = {
            'quality_score', 'emotion_polarity', 'keyword_density',
            'entity_count', 'relation_count'
        }

        chunk_missing = chunk_extended_fields - chunk_columns

        print(f"\n  document_chunks表扩展字段:")
        for field in sorted(chunk_extended_fields):
            status = "✓" if field in chunk_columns else "✗"
            print(f"    {status} {field}")

        conn.close()

        total_missing = len(doc_missing) + len(chunk_missing)
        success = total_missing == 0

        print(f"\n  结果: {'✓ 通过' if success else f'✗ 失败 (缺失 {total_missing} 字段)'}")
        return success, list(doc_missing) + list(chunk_missing)

    except Exception as e:
        print(f"  ✗ 错误: {e}")
        return False, [str(e)]


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("Data Governance System Verification")
    print("=" * 60)

    checks = [
        ("模块导入", check_module_imports),
        ("插件注册", check_plugin_registration),
        ("数据库表", check_database_tables),
        ("指标字典", check_metric_dictionary),
        ("StructuredProcessor集成", check_structured_processor_integration),
        ("编排器", check_orchestrator),
        ("扩展字段", check_extended_fields),
    ]

    results = []

    for name, check_func in checks:
        try:
            success, details = check_func()
            results.append((name, success, details))
        except Exception as e:
            print(f"\n✗ {name} 检查失败: {e}")
            results.append((name, False, [str(e)]))

    # Summary
    print("\n" + "=" * 60)
    print("验证结果汇总 (Verification Summary)")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, details in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")
        if not success and details:
            print(f"      问题: {', '.join(str(d) for d in details[:3])}")

    print(f"\n总计: {passed}/{total} 项通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 系统验证完全通过！数据治理系统已就绪。")
        return 0
    else:
        print(f"\n⚠ 还有 {total - passed} 项需要修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
