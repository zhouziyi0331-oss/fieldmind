#!/usr/bin/env python3
"""
完整系统健康检查 - 发现并报告所有技术漏洞
System Health Check - Find and report all technical gaps
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

import sqlite3
from app.config import settings
import ast
import inspect


def check_governance_models():
    """检查治理模型完整性"""
    print("\n1. 治理模型完整性检查")
    print("=" * 60)

    from app.models.governance import (
        MetricDictionary, LineageEdge, MetricCalculationHistory,
        QualityRule, QualityCheckResult, ChangeEvent, GovernanceMetadata
    )

    models = [
        MetricDictionary, LineageEdge, MetricCalculationHistory,
        QualityRule, QualityCheckResult, ChangeEvent, GovernanceMetadata
    ]

    issues = []

    for model in models:
        model_name = model.__name__

        # Check if model has __tablename__
        if not hasattr(model, '__tablename__'):
            issues.append(f"{model_name} 缺少 __tablename__")

        # Check if model has primary key
        if not hasattr(model, '__mapper__'):
            issues.append(f"{model_name} 缺少 mapper 配置")
        else:
            pk_columns = [c.name for c in model.__mapper__.primary_key]
            if not pk_columns:
                issues.append(f"{model_name} 缺少主键")
            else:
                print(f"  ✓ {model_name}: 主键={pk_columns}")

    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False, issues

    print(f"\n  结果: ✓ 所有模型完整")
    return True, []


def check_service_implementations():
    """检查服务实现完整性"""
    print("\n2. 服务实现完整性检查")
    print("=" * 60)

    services = [
        ('app.services.lineage_tracker', 'LineageTracker'),
        ('app.services.metadata_collector', 'MetadataCollector'),
        ('app.services.metric_calculator', 'calculate_chunk_metrics'),
    ]

    issues = []

    for module_path, name in services:
        try:
            module = __import__(module_path, fromlist=[name])
            obj = getattr(module, name)

            if callable(obj):
                # It's a function
                source = inspect.getsource(obj)
                if 'pass' in source and len(source.split('\n')) < 5:
                    issues.append(f"{name} 是空实现")
                elif 'TODO' in source or 'FIXME' in source:
                    issues.append(f"{name} 包含 TODO/FIXME")
                else:
                    print(f"  ✓ {name}: 实现完整")
            else:
                # It's a class
                methods = [m for m in dir(obj) if not m.startswith('_')]
                if not methods:
                    issues.append(f"{name} 没有公开方法")
                else:
                    print(f"  ✓ {name}: {len(methods)} 个公开方法")

        except Exception as e:
            issues.append(f"{name} 导入失败: {e}")

    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False, issues

    print(f"\n  结果: ✓ 所有服务实现完整")
    return True, []


def check_plugin_coverage():
    """检查插件覆盖率"""
    print("\n3. 插件覆盖率检查")
    print("=" * 60)

    from app.agents.ingestion_agent import get_ingestion_agent

    agent = get_ingestion_agent()

    # 常见文件类型
    common_formats = {
        'pdf', 'doc', 'docx', 'txt', 'md', 'html', 'json', 'xml',
        'jpg', 'png', 'gif', 'mp3', 'wav', 'mp4', 'avi',
        'xlsx', 'csv', 'pptx', 'zip', 'eml'
    }

    supported = set(agent.plugins.keys())
    missing = common_formats - supported

    print(f"  支持的格式: {len(supported)}")
    print(f"  常见格式覆盖: {len(common_formats - missing)}/{len(common_formats)}")

    if missing:
        print(f"  ⚠ 未覆盖的常见格式: {missing}")
        return False, list(missing)

    print(f"\n  结果: ✓ 覆盖所有常见格式")
    return True, []


def check_database_integrity():
    """检查数据库完整性"""
    print("\n4. 数据库完整性检查")
    print("=" * 60)

    db_path = settings.DATABASE_URL.replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    issues = []

    # Check foreign key integrity
    cursor.execute("PRAGMA foreign_key_check")
    fk_errors = cursor.fetchall()
    if fk_errors:
        issues.append(f"外键约束错误: {len(fk_errors)} 条")
        for err in fk_errors[:3]:
            print(f"  ✗ {err}")
    else:
        print(f"  ✓ 外键完整性正常")

    # Check for tables without indexes
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE '%_fts%'
    """)
    tables = [row[0] for row in cursor.fetchall()]

    tables_without_indexes = []
    for table in tables:
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        if not indexes:
            tables_without_indexes.append(table)

    if tables_without_indexes:
        print(f"  ⚠ {len(tables_without_indexes)} 个表缺少索引")
        for table in tables_without_indexes[:5]:
            print(f"    - {table}")
    else:
        print(f"  ✓ 所有主要表都有索引")

    # Check metric dictionary initialization
    cursor.execute("SELECT COUNT(*) FROM metric_dictionary")
    metric_count = cursor.fetchone()[0]
    if metric_count < 20:
        issues.append(f"指标字典不完整: {metric_count}/20+")
    else:
        print(f"  ✓ 指标字典已初始化: {metric_count} 条")

    # Check quality rules
    cursor.execute("SELECT COUNT(*) FROM quality_rules")
    rule_count = cursor.fetchone()[0]
    if rule_count == 0:
        issues.append("质量规则未初始化")
    else:
        print(f"  ✓ 质量规则已初始化: {rule_count} 条")

    conn.close()

    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False, issues

    print(f"\n  结果: ✓ 数据库完整性良好")
    return True, []


def check_orchestrator_completeness():
    """检查编排器完整性"""
    print("\n5. 编排器完整性检查")
    print("=" * 60)

    from app.orchestration.data_governance_orchestrator import DataGovernanceOrchestrator

    orchestrator = DataGovernanceOrchestrator()

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

    issues = []

    for stage_name in stages:
        if not hasattr(orchestrator, stage_name):
            issues.append(f"缺少阶段: {stage_name}")
            continue

        method = getattr(orchestrator, stage_name)
        source = inspect.getsource(method)

        # Check for incomplete implementations
        if 'TODO' in source or 'FIXME' in source:
            issues.append(f"{stage_name} 包含 TODO/FIXME")
        elif 'pass' in source and len(source.split('\n')) < 10:
            issues.append(f"{stage_name} 是空实现")
        else:
            lines = len(source.split('\n'))
            print(f"  ✓ {stage_name}: {lines} 行实现")

    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False, issues

    print(f"\n  结果: ✓ 所有8个阶段实现完整")
    return True, []


def check_error_handling():
    """检查错误处理"""
    print("\n6. 错误处理检查")
    print("=" * 60)

    from app.orchestration.data_governance_orchestrator import DataGovernanceOrchestrator

    source = inspect.getsource(DataGovernanceOrchestrator.process_file)

    has_try_except = 'try:' in source and 'except' in source
    has_logging = 'logger.error' in source or 'logger.exception' in source
    has_rollback = 'rollback' in source
    has_finally = 'finally:' in source

    print(f"  {'✓' if has_try_except else '✗'} Try-Except 块")
    print(f"  {'✓' if has_logging else '✗'} 错误日志")
    print(f"  {'✓' if has_rollback else '✗'} 事务回滚")
    print(f"  {'✓' if has_finally else '✗'} Finally 清理")

    all_checks = [has_try_except, has_logging, has_rollback, has_finally]

    if not all(all_checks):
        issues = []
        if not has_try_except:
            issues.append("缺少异常处理")
        if not has_logging:
            issues.append("缺少错误日志")
        if not has_rollback:
            issues.append("缺少事务回滚")
        if not has_finally:
            issues.append("缺少资源清理")

        print(f"\n  结果: ✗ 错误处理不完整")
        return False, issues

    print(f"\n  结果: ✓ 错误处理完整")
    return True, []


def check_security_issues():
    """检查安全问题"""
    print("\n7. 安全问题检查")
    print("=" * 60)

    issues = []

    # Check for SQL injection vulnerabilities
    from app.services import lineage_tracker
    source = inspect.getsource(lineage_tracker)

    if 'execute("' in source and '%s' in source:
        issues.append("可能存在 SQL 注入风险（使用字符串格式化）")
    else:
        print(f"  ✓ SQL 注入防护正常")

    # Check for hardcoded credentials
    from app.config import settings
    if settings.SECRET_KEY == "your-secret-key-change-in-production":
        issues.append("使用默认密钥（生产环境不安全）")
        print(f"  ⚠ 检测到默认密钥")
    else:
        print(f"  ✓ 密钥配置正常")

    # Check for sensitive data logging protection
    from app.core import logging
    log_source = inspect.getsource(logging)

    # Check if sanitization is implemented
    if 'SensitiveDataFilter' in log_source and 'filter=sensitive_filter' in log_source:
        print(f"  ✓ 敏感信息脱敏已实现")
    elif 'sanitize' in log_source.lower():
        print(f"  ✓ 敏感信息处理正常")
    else:
        issues.append("可能记录敏感信息")
        print(f"  ⚠ 可能记录敏感信息")

    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        print(f"\n  结果: ⚠ 发现 {len(issues)} 个安全风险")
        return False, issues

    print(f"\n  结果: ✓ 未发现严重安全问题")
    return True, []


def check_performance_issues():
    """检查性能问题"""
    print("\n8. 性能问题检查")
    print("=" * 60)

    db_path = settings.DATABASE_URL.replace('sqlite:///', '')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    issues = []

    # Check for N+1 query problems in common operations
    from app.orchestration.data_governance_orchestrator import DataGovernanceOrchestrator
    source = inspect.getsource(DataGovernanceOrchestrator)

    # Check if batch operations are used instead of loops
    if 'record_lineage_batch' in source:
        print(f"  ✓ 使用批量操作，避免 N+1 查询")
    elif 'for chunk_id in chunk_ids' in source and 'record_lineage(' in source:
        print(f"  ⚠ 可能存在 N+1 查询问题")
        issues.append("编排器中可能存在 N+1 查询")
    else:
        print(f"  ✓ 未检测到明显的 N+1 查询")

    # Check for missing indexes on foreign keys
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        AND sql LIKE '%FOREIGN KEY%'
    """)
    tables_with_fks = [row[0] for row in cursor.fetchall()]

    missing_fk_indexes = []
    for table in tables_with_fks[:10]:  # Sample first 10
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        for fk in fks:
            col = fk[3]  # from column
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = cursor.fetchall()
            # Check if any index covers this column
            has_index = False
            for idx in indexes:
                cursor.execute(f"PRAGMA index_info({idx[1]})")
                cols = [r[2] for r in cursor.fetchall()]
                if col in cols:
                    has_index = True
                    break
            if not has_index:
                missing_fk_indexes.append(f"{table}.{col}")

    if missing_fk_indexes:
        print(f"  ⚠ {len(missing_fk_indexes)} 个外键缺少索引")
        for fk in missing_fk_indexes[:3]:
            print(f"    - {fk}")
    else:
        print(f"  ✓ 外键索引覆盖良好")

    # Check for large tables without pagination
    cursor.execute("""
        SELECT name, COUNT(*) as cnt
        FROM (
            SELECT 'documents' as name UNION ALL
            SELECT 'document_chunks' UNION ALL
            SELECT 'lineage_edges'
        ) tables
        GROUP BY name
    """)

    conn.close()

    if issues:
        print(f"\n  结果: ⚠ 发现 {len(issues)} 个性能问题")
        return False, issues

    print(f"\n  结果: ✓ 未发现严重性能问题")
    return True, []


def main():
    """运行所有健康检查"""
    print("=" * 60)
    print("FieldMind 系统健康检查")
    print("System Health Check - 技术漏洞全面扫描")
    print("=" * 60)

    checks = [
        ("治理模型", check_governance_models),
        ("服务实现", check_service_implementations),
        ("插件覆盖", check_plugin_coverage),
        ("数据库完整性", check_database_integrity),
        ("编排器完整性", check_orchestrator_completeness),
        ("错误处理", check_error_handling),
        ("安全问题", check_security_issues),
        ("性能问题", check_performance_issues),
    ]

    results = []
    all_issues = []

    for name, check_func in checks:
        try:
            success, issues = check_func()
            results.append((name, success))
            if issues:
                all_issues.extend([(name, issue) for issue in issues])
        except Exception as e:
            print(f"\n✗ {name} 检查失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
            all_issues.append((name, str(e)))

    # 汇总报告
    print("\n" + "=" * 60)
    print("健康检查汇总 (Health Check Summary)")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    print(f"\n总计: {passed}/{total} 项通过 ({passed/total*100:.1f}%)")

    if all_issues:
        print(f"\n发现的问题:")
        for category, issue in all_issues[:10]:  # Show first 10
            print(f"  • [{category}] {issue}")
        if len(all_issues) > 10:
            print(f"  ... 还有 {len(all_issues) - 10} 个问题")

    if passed == total:
        print("\n🎉 系统健康状态良好！未发现严重技术漏洞。")
        return 0
    elif passed >= total * 0.8:
        print(f"\n⚠ 系统基本健康，但有 {total - passed} 项需要改进")
        return 0
    else:
        print(f"\n❌ 系统存在 {total - passed} 个严重问题，需要立即修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
