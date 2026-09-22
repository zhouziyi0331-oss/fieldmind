"""
测试 IngestionMetadataEnhancer - 采集元数据增强器

验证：
1. 12个元数据字段全部生成
2. 来源系统检测
3. 数据分类（public/internal/confidential/restricted）
4. 质量评估
5. 治理标签生成
6. 保留期限计算
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ingestion_metadata_enhancer import (
    IngestionMetadataEnhancer,
    create_metadata_enhancer,
    DataClassification,
    ProcessingStatus
)


def test_initialization():
    """测试初始化"""
    print("\n" + "="*60)
    print("测试1: IngestionMetadataEnhancer 初始化")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()
    assert enhancer is not None
    assert enhancer.metadata_version == "2.0"
    print("✅ 元数据增强器初始化成功")

    # 测试工厂方法
    enhancer2 = create_metadata_enhancer()
    assert enhancer2 is not None
    print("✅ 工厂方法创建成功")

    print("\n✅ 初始化测试通过")


def test_basic_enhancement():
    """测试基础元数据增强"""
    print("\n" + "="*60)
    print("测试2: 基础元数据增强（12个字段）")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    file_path = "/home/user/documents/report.pdf"
    file_type = "pdf"
    content = "这是一份测试报告。包含了一些业务数据。"
    existing_metadata = {
        'file_name': 'report.pdf',
        'file_size': 1024 * 100,  # 100KB
        'created_at': '2024-01-01T00:00:00'
    }

    enhanced = enhancer.enhance_metadata(
        file_path=file_path,
        file_type=file_type,
        raw_content=content,
        existing_metadata=existing_metadata
    )

    # 验证12个字段
    required_fields = [
        'source_system',
        'business_owner',
        'data_classification',
        'retention_period',
        'last_accessed_at',
        'access_count',
        'quality_score',
        'processing_status',
        'error_message',
        'retry_count',
        'metadata_version',
        'governance_tags'
    ]

    print("检查12个治理字段:")
    for field in required_fields:
        assert field in enhanced, f"缺少字段: {field}"
        print(f"  ✓ {field}: {enhanced[field]}")

    print("\n✅ 12个字段全部生成")


def test_source_system_detection():
    """测试来源系统检测"""
    print("\n" + "="*60)
    print("测试3: 来源系统检测")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    test_cases = [
        {
            'path': '/sharepoint/documents/file.pdf',
            'expected': 'sharepoint'
        },
        {
            'path': '/google_drive/my_files/doc.txt',
            'expected': 'google_drive'
        },
        {
            'path': '/downloads/web_file.pdf',
            'expected': 'web'
        },
        {
            'path': '/local/file.txt',
            'expected': 'local_upload'
        }
    ]

    for case in test_cases:
        result = enhancer._detect_source_system(case['path'], {})
        print(f"  路径: {case['path']}")
        print(f"    检测结果: {result}")
        print(f"    预期: {case['expected']}")
        assert result == case['expected'], f"检测错误: {result} != {case['expected']}"
        print(f"    ✓ 正确")

    print("\n✅ 来源系统检测测试通过")


def test_business_owner_identification():
    """测试业务负责人识别"""
    print("\n" + "="*60)
    print("测试4: 业务负责人识别")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    # 从路径提取
    path1 = "/users/john/documents/report.pdf"
    owner1 = enhancer._identify_business_owner(path1, {})
    print(f"路径: {path1}")
    print(f"  识别出: {owner1}")
    assert owner1 == "john"
    print("  ✓ 从路径提取成功")

    # 从元数据提取
    path2 = "/documents/report.pdf"
    metadata2 = {'author': 'Alice'}
    owner2 = enhancer._identify_business_owner(path2, metadata2)
    print(f"\n路径: {path2}")
    print(f"元数据: {metadata2}")
    print(f"  识别出: {owner2}")
    assert owner2 == "Alice"
    print("  ✓ 从元数据提取成功")

    print("\n✅ 业务负责人识别测试通过")


def test_data_classification():
    """测试数据分类"""
    print("\n" + "="*60)
    print("测试5: 数据分类")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    test_cases = [
        {
            'content': '这是一份公开的报告',
            'filename': 'public_report.pdf',
            'expected': DataClassification.PUBLIC.value
        },
        {
            'content': '内部业务报告，包含销售数据',
            'filename': 'sales_report.pdf',
            'expected': DataClassification.INTERNAL.value
        },
        {
            'content': '员工薪资表，包含工资和身份证号码',
            'filename': 'salary.xlsx',
            'expected': DataClassification.CONFIDENTIAL.value
        },
        {
            'content': '绝密文件，严格保密',
            'filename': 'top_secret.pdf',
            'expected': DataClassification.RESTRICTED.value
        }
    ]

    for case in test_cases:
        result = enhancer._classify_data_sensitivity(
            case['content'],
            case['filename'],
            'pdf'
        )
        print(f"\n文件名: {case['filename']}")
        print(f"内容: {case['content'][:30]}...")
        print(f"  分类结果: {result}")
        print(f"  预期: {case['expected']}")
        assert result == case['expected'], f"分类错误"
        print(f"  ✓ 正确")

    print("\n✅ 数据分类测试通过")


def test_retention_period():
    """测试保留期限计算"""
    print("\n" + "="*60)
    print("测试6: 保留期限计算")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    test_cases = [
        {
            'classification': DataClassification.RESTRICTED.value,
            'expected_days': 2555,  # 7年
            'expected_years': 7
        },
        {
            'classification': DataClassification.CONFIDENTIAL.value,
            'expected_days': 1825,  # 5年
            'expected_years': 5
        },
        {
            'classification': DataClassification.INTERNAL.value,
            'expected_days': 1095,  # 3年
            'expected_years': 3
        },
        {
            'classification': DataClassification.PUBLIC.value,
            'expected_days': 730,   # 2年
            'expected_years': 2
        }
    ]

    for case in test_cases:
        days = enhancer._calculate_retention_period('pdf', case['classification'])
        years = days / 365
        print(f"\n分类: {case['classification']}")
        print(f"  保留期限: {days}天 ({years:.1f}年)")
        print(f"  预期: {case['expected_days']}天 ({case['expected_years']}年)")
        assert days == case['expected_days']
        print(f"  ✓ 正确")

    print("\n✅ 保留期限计算测试通过")


def test_quality_assessment():
    """测试质量评估"""
    print("\n" + "="*60)
    print("测试7: 质量评估")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    # 高质量内容
    high_quality_content = """
    # 标题

    这是一份完整的报告。包含多个段落。

    第一段内容，详细描述了业务情况。

    第二段内容，分析了市场趋势。
    """

    high_quality_metadata = {
        'file_name': 'report.pdf',
        'file_size': 1024 * 500,
        'created_at': '2024-01-01'
    }

    score_high = enhancer._assess_initial_quality(
        high_quality_content,
        'pdf',
        high_quality_metadata
    )

    print(f"高质量内容:")
    print(f"  内容长度: {len(high_quality_content)}")
    print(f"  质量得分: {score_high}")
    assert score_high >= 70, f"高质量内容得分应该>=70"
    print(f"  ✓ 得分合理")

    # 低质量内容
    low_quality_content = "短"

    low_quality_metadata = {
        'file_name': 'temp.txt'
    }

    score_low = enhancer._assess_initial_quality(
        low_quality_content,
        'txt',
        low_quality_metadata
    )

    print(f"\n低质量内容:")
    print(f"  内容长度: {len(low_quality_content)}")
    print(f"  质量得分: {score_low}")
    assert score_low < 70, f"低质量内容得分应该<70"
    print(f"  ✓ 得分合理")

    print(f"\n质量差异: {score_high - score_low:.2f}分")
    print("\n✅ 质量评估测试通过")


def test_governance_tags():
    """测试治理标签生成"""
    print("\n" + "="*60)
    print("测试8: 治理标签生成")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    content = "这是一份测试文档。" * 100  # 创建长文档
    metadata = {
        'file_name': 'test.pdf',
        'file_size': 1024 * 1024 * 5,  # 5MB
        'file_type': 'pdf',
        'source_system': 'sharepoint',
        'data_classification': 'confidential',
        'quality_score': 85,
        'translated': True,
        'original_language': 'en',
        'source_count': 10
    }

    tags = enhancer._generate_governance_tags(
        '/path/to/test.pdf',
        'pdf',
        content,
        metadata
    )

    print(f"生成的标签: {tags}")
    print(f"标签数量: {len(tags)}")

    # 验证必要的标签类型
    tag_prefixes = ['type:', 'classification:', 'source:', 'size:', 'lang:', 'quality:']
    for prefix in tag_prefixes:
        has_tag = any(tag.startswith(prefix) for tag in tags)
        assert has_tag, f"缺少 {prefix} 标签"
        print(f"  ✓ 包含 {prefix} 标签")

    # 验证具体标签
    assert 'type:pdf' in tags
    assert 'classification:confidential' in tags
    assert 'source:sharepoint' in tags
    assert 'quality:high' in tags
    assert 'lang:translated' in tags

    print("\n✅ 治理标签生成测试通过")


def test_full_enhancement_workflow():
    """测试完整的增强流程"""
    print("\n" + "="*60)
    print("测试9: 完整增强流程")
    print("="*60)

    enhancer = IngestionMetadataEnhancer()

    # 模拟真实场景
    file_path = "/users/alice/sharepoint/confidential/salary_2024.xlsx"
    file_type = "excel"
    content = "员工姓名,工资,身份证号\n张三,10000,110101199001011234\n李四,12000,110101199002021234"

    existing_metadata = {
        'file_name': 'salary_2024.xlsx',
        'file_size': 1024 * 50,
        'created_at': '2024-01-01T00:00:00',
        'sheet_count': 1,
        'rows': 3
    }

    enhanced = enhancer.enhance_metadata(
        file_path=file_path,
        file_type=file_type,
        raw_content=content,
        existing_metadata=existing_metadata
    )

    print("\n增强后的元数据:")
    print(f"  来源系统: {enhanced['source_system']}")
    print(f"  业务负责人: {enhanced['business_owner']}")
    print(f"  数据分类: {enhanced['data_classification']}")
    print(f"  保留期限: {enhanced['retention_period']}天")
    print(f"  质量得分: {enhanced['quality_score']}")
    print(f"  处理状态: {enhanced['processing_status']}")
    print(f"  元数据版本: {enhanced['metadata_version']}")
    print(f"  治理标签: {enhanced['governance_tags']}")

    # 验证关键结果
    assert enhanced['source_system'] == 'sharepoint'
    print("\n  ✓ 来源系统检测正确")

    assert enhanced['business_owner'] == 'alice'
    print("  ✓ 业务负责人识别正确")

    assert enhanced['data_classification'] == 'confidential'
    print("  ✓ 数据分类正确（包含敏感信息）")

    assert enhanced['retention_period'] == 1825
    print("  ✓ 保留期限正确（机密数据5年）")

    assert enhanced['metadata_version'] == '2.0'
    print("  ✓ 元数据版本正确")

    assert len(enhanced['governance_tags']) > 0
    print("  ✓ 治理标签已生成")

    print("\n✅ 完整增强流程测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("IngestionMetadataEnhancer 功能测试")
    print("="*60)

    try:
        test_initialization()
        test_basic_enhancement()
        test_source_system_detection()
        test_business_owner_identification()
        test_data_classification()
        test_retention_period()
        test_quality_assessment()
        test_governance_tags()
        test_full_enhancement_workflow()

        print("\n" + "="*60)
        print("✅✅✅ 所有测试通过！")
        print("="*60)
        print("\n说明:")
        print("  - IngestionMetadataEnhancer 核心逻辑正确")
        print("  - 12个元数据字段全部实现")
        print("  - 来源系统检测准确")
        print("  - 数据分类智能")
        print("  - 质量评估合理")
        print("  - 治理标签丰富")
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
