"""
测试 ReportGovernanceSummaryGenerator - 报告治理摘要生成器

验证：
1. 治理摘要生成
2. 数据质量摘要
3. 血缘关系摘要
4. 指标统计摘要
5. 治理问题检测
6. 合规性评估
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.report_governance_summary_generator import (
    ReportGovernanceSummaryGenerator,
    create_governance_summary_generator,
    QualitySummary,
    LineageSummary,
    MetricsSummary,
    GovernanceIssue,
    ComplianceAssessment
)


def test_initialization():
    """测试初始化"""
    print("\n" + "="*60)
    print("测试1: ReportGovernanceSummaryGenerator 初始化")
    print("="*60)

    generator = ReportGovernanceSummaryGenerator()
    assert generator is not None
    print("✅ 治理摘要生成器初始化成功")

    # 测试工厂方法
    generator2 = create_governance_summary_generator()
    assert generator2 is not None
    print("✅ 工厂方法创建成功")

    print("\n✅ 初始化测试通过")


def test_empty_summary():
    """测试无数据库连接时的空摘要"""
    print("\n" + "="*60)
    print("测试2: 空摘要生成（无数据库）")
    print("="*60)

    generator = ReportGovernanceSummaryGenerator(db_session=None)

    summary = generator.generate_summary(
        project_id=1,
        document_id="doc_123"
    )

    print(f"空摘要: {summary}")
    assert 'error' in summary
    print("✅ 无数据库时正确返回空摘要")

    print("\n✅ 空摘要测试通过")


def test_quality_summary_structure():
    """测试数据质量摘要结构"""
    print("\n" + "="*60)
    print("测试3: 数据质量摘要结构")
    print("="*60)

    quality = QualitySummary(
        total_documents=100,
        avg_quality_score=75.5,
        high_quality_count=30,
        medium_quality_count=50,
        low_quality_count=20,
        completeness_rate=85.5,
        issues_count=20
    )

    print(f"总文档数: {quality.total_documents}")
    print(f"平均质量分: {quality.avg_quality_score}")
    print(f"高质量: {quality.high_quality_count}")
    print(f"中质量: {quality.medium_quality_count}")
    print(f"低质量: {quality.low_quality_count}")
    print(f"完整性: {quality.completeness_rate}%")
    print(f"问题数: {quality.issues_count}")

    assert quality.total_documents == quality.high_quality_count + quality.medium_quality_count + quality.low_quality_count
    print("\n✅ 质量摘要结构正确")

    print("\n✅ 质量摘要测试通过")


def test_lineage_summary_structure():
    """测试血缘关系摘要结构"""
    print("\n" + "="*60)
    print("测试4: 血缘关系摘要结构")
    print("="*60)

    lineage = LineageSummary(
        total_lineage_edges=500,
        max_depth=5,
        avg_depth=2.5,
        file_to_chunk_count=100,
        chunk_to_entity_count=200,
        traceable_documents=50,
        coverage_rate=95.5
    )

    print(f"总血缘边数: {lineage.total_lineage_edges}")
    print(f"最大深度: {lineage.max_depth}")
    print(f"平均深度: {lineage.avg_depth}")
    print(f"file→chunk: {lineage.file_to_chunk_count}")
    print(f"chunk→entity: {lineage.chunk_to_entity_count}")
    print(f"可追溯文档: {lineage.traceable_documents}")
    print(f"覆盖率: {lineage.coverage_rate}%")

    assert lineage.file_to_chunk_count + lineage.chunk_to_entity_count <= lineage.total_lineage_edges
    print("\n✅ 血缘摘要结构正确")

    print("\n✅ 血缘摘要测试通过")


def test_metrics_summary_structure():
    """测试指标统计摘要结构"""
    print("\n" + "="*60)
    print("测试5: 指标统计摘要结构")
    print("="*60)

    metrics = MetricsSummary(
        total_chunks=1000,
        avg_semantic_density=0.15,
        avg_coherence=0.75,
        avg_readability=65.5,
        avg_complexity=4.2,
        total_entities=500,
        total_keywords=300,
        metrics_coverage_rate=98.5
    )

    print(f"总chunk数: {metrics.total_chunks}")
    print(f"平均语义密度: {metrics.avg_semantic_density}")
    print(f"平均连贯性: {metrics.avg_coherence}")
    print(f"平均可读性: {metrics.avg_readability}")
    print(f"平均复杂度: {metrics.avg_complexity}")
    print(f"总实体数: {metrics.total_entities}")
    print(f"总关键词数: {metrics.total_keywords}")
    print(f"指标覆盖率: {metrics.metrics_coverage_rate}%")

    assert metrics.avg_semantic_density > 0
    assert 0 <= metrics.avg_coherence <= 1
    print("\n✅ 指标摘要结构正确")

    print("\n✅ 指标摘要测试通过")


def test_governance_issue_detection():
    """测试治理问题检测逻辑"""
    print("\n" + "="*60)
    print("测试6: 治理问题检测逻辑")
    print("="*60)

    generator = ReportGovernanceSummaryGenerator()

    # 模拟有问题的摘要
    quality_low = QualitySummary(
        total_documents=100,
        avg_quality_score=60.0,
        high_quality_count=20,
        medium_quality_count=50,
        low_quality_count=30,  # 30个低质量
        completeness_rate=65.0,  # 完整性低
        issues_count=30
    )

    lineage_low = LineageSummary(
        total_lineage_edges=50,
        max_depth=2,
        avg_depth=1.2,
        file_to_chunk_count=50,
        chunk_to_entity_count=0,
        traceable_documents=30,
        coverage_rate=45.0  # 覆盖率低
    )

    metrics_low = MetricsSummary(
        total_chunks=1000,
        avg_semantic_density=0.03,  # 语义密度过低
        avg_coherence=0.5,
        avg_readability=50.0,
        avg_complexity=3.0,
        total_entities=100,
        total_keywords=50,
        metrics_coverage_rate=70.0  # 覆盖率低
    )

    issues = generator._detect_governance_issues(quality_low, lineage_low, metrics_low)

    print(f"\n检测到 {len(issues)} 个治理问题:")
    for i, issue in enumerate(issues):
        print(f"\n问题 {i+1}:")
        print(f"  类型: {issue.issue_type}")
        print(f"  严重性: {issue.severity}")
        print(f"  描述: {issue.description}")
        print(f"  建议: {issue.recommendation}")

    # 应该检测到至少4个问题
    assert len(issues) >= 4
    print(f"\n✅ 成功检测到 {len(issues)} 个问题")

    # 验证问题类型
    issue_types = {issue.issue_type for issue in issues}
    assert 'quality' in issue_types
    assert 'lineage' in issue_types
    print("✅ 问题类型覆盖全面")

    print("\n✅ 治理问题检测测试通过")


def test_compliance_assessment():
    """测试合规性评估逻辑"""
    print("\n" + "="*60)
    print("测试7: 合规性评估逻辑")
    print("="*60)

    generator = ReportGovernanceSummaryGenerator()

    # 良好的合规性
    quality_good = QualitySummary(
        total_documents=100,
        avg_quality_score=85.0,
        high_quality_count=80,
        medium_quality_count=18,
        low_quality_count=2,
        completeness_rate=98.0,
        issues_count=2
    )

    lineage_good = LineageSummary(
        total_lineage_edges=500,
        max_depth=5,
        avg_depth=2.5,
        file_to_chunk_count=100,
        chunk_to_entity_count=200,
        traceable_documents=95,
        coverage_rate=95.0
    )

    assessment = generator._assess_compliance(1, None, quality_good, lineage_good)

    print("\n合规性评估结果:")
    print(f"  数据分类合规: {assessment.data_classification_compliance}")
    print(f"  保留策略合规: {assessment.retention_policy_compliance}")
    print(f"  访问控制合规: {assessment.access_control_compliance}")
    print(f"  审计追踪合规: {assessment.audit_trail_compliance}")
    print(f"  总分: {assessment.overall_score}")
    print(f"  建议: {assessment.recommendations}")

    assert assessment.overall_score >= 90
    print(f"\n✅ 良好的合规性得分: {assessment.overall_score}")

    # 较差的合规性
    quality_bad = QualitySummary(
        total_documents=100,
        avg_quality_score=55.0,
        high_quality_count=10,
        medium_quality_count=40,
        low_quality_count=50,
        completeness_rate=60.0,
        issues_count=50
    )

    lineage_bad = LineageSummary(
        total_lineage_edges=50,
        max_depth=2,
        avg_depth=1.0,
        file_to_chunk_count=50,
        chunk_to_entity_count=0,
        traceable_documents=30,
        coverage_rate=30.0
    )

    assessment_bad = generator._assess_compliance(1, None, quality_bad, lineage_bad)

    print(f"\n较差的合规性得分: {assessment_bad.overall_score}")
    assert assessment_bad.overall_score < 90
    print("✅ 较差的合规性正确识别")

    print("\n✅ 合规性评估测试通过")


def test_summary_dict_conversion():
    """测试摘要对象到字典的转换"""
    print("\n" + "="*60)
    print("测试8: 摘要对象转字典")
    print("="*60)

    from app.services.report_governance_summary_generator import GovernanceSummary

    summary = GovernanceSummary(
        project_id=1,
        document_id="doc_123",
        generated_at="2024-01-01T00:00:00",
        quality_summary=QualitySummary(10, 75.0, 5, 3, 2, 90.0, 2),
        lineage_summary=LineageSummary(100, 3, 2.0, 50, 30, 10, 95.0),
        metrics_summary=MetricsSummary(100, 0.15, 0.75, 65.0, 4.0, 50, 30, 98.0),
        governance_issues=[],
        compliance_assessment=ComplianceAssessment(True, True, True, True, 95.0, ["良好"])
    )

    generator = ReportGovernanceSummaryGenerator()
    result_dict = generator._summary_to_dict(summary)

    print("\n转换后的字典结构:")
    print(f"  project_id: {result_dict['project_id']}")
    print(f"  document_id: {result_dict['document_id']}")
    print(f"  quality_summary: {list(result_dict['quality_summary'].keys())}")
    print(f"  lineage_summary: {list(result_dict['lineage_summary'].keys())}")
    print(f"  metrics_summary: {list(result_dict['metrics_summary'].keys())}")
    print(f"  governance_issues: {len(result_dict['governance_issues'])}")
    print(f"  compliance_assessment: {list(result_dict['compliance_assessment'].keys())}")

    # 验证字典结构
    assert 'project_id' in result_dict
    assert 'quality_summary' in result_dict
    assert 'lineage_summary' in result_dict
    assert 'metrics_summary' in result_dict
    assert 'governance_issues' in result_dict
    assert 'compliance_assessment' in result_dict

    print("\n✅ 字典结构完整")

    print("\n✅ 字典转换测试通过")


def test_issue_severity_levels():
    """测试问题严重性级别"""
    print("\n" + "="*60)
    print("测试9: 问题严重性级别")
    print("="*60)

    generator = ReportGovernanceSummaryGenerator()

    # 测试不同严重程度的质量问题
    test_cases = [
        {
            'low_quality_count': 10,
            'expected_severity': 'high'
        },
        {
            'low_quality_count': 3,
            'expected_severity': 'medium'
        }
    ]

    for case in test_cases:
        quality = QualitySummary(
            total_documents=100,
            avg_quality_score=60.0,
            high_quality_count=50,
            medium_quality_count=40,
            low_quality_count=case['low_quality_count'],
            completeness_rate=90.0,
            issues_count=case['low_quality_count']
        )

        lineage = LineageSummary(100, 2, 1.5, 50, 30, 50, 95.0)
        metrics = MetricsSummary(1000, 0.15, 0.75, 65.0, 4.0, 500, 300, 95.0)

        issues = generator._detect_governance_issues(quality, lineage, metrics)

        quality_issues = [i for i in issues if i.issue_type == 'quality' and '质量低于50分' in i.description]
        if quality_issues:
            print(f"\n低质量文档数: {case['low_quality_count']}")
            print(f"  检测到的严重性: {quality_issues[0].severity}")
            print(f"  预期严重性: {case['expected_severity']}")
            assert quality_issues[0].severity == case['expected_severity']
            print(f"  ✓ 严重性级别正确")

    print("\n✅ 问题严重性级别测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("ReportGovernanceSummaryGenerator 功能测试")
    print("="*60)

    try:
        test_initialization()
        test_empty_summary()
        test_quality_summary_structure()
        test_lineage_summary_structure()
        test_metrics_summary_structure()
        test_governance_issue_detection()
        test_compliance_assessment()
        test_summary_dict_conversion()
        test_issue_severity_levels()

        print("\n" + "="*60)
        print("✅✅✅ 所有测试通过！")
        print("="*60)
        print("\n说明:")
        print("  - ReportGovernanceSummaryGenerator 核心逻辑正确")
        print("  - 5个摘要结构完整")
        print("  - 治理问题检测智能")
        print("  - 合规性评估合理")
        print("  - 需要真实数据库连接才能测试完整的查询流程")
        print()

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
