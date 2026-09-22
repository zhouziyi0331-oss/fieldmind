"""
测试 BusinessDimensionClassifier - 业务维度分类器

这是真正的数据治理验证：
- 能否正确识别6个业务维度
- 能否提取时间、地点
- 能否记录匹配的关键词
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.business_dimension_classifier import (
    BusinessDimensionClassifier,
    create_classifier,
    classify_text
)


def test_clothing_dimension():
    """测试"衣"维度识别"""
    print("\n" + "="*60)
    print("测试1: 衣食住行 - 衣")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "王奶奶还在做蜡染，用的是传统的蜂蜡和蓝靛。她说布依族的蜡染技艺是祖传的。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"\n分类结果:")
    print(f"  主维度: {result.primary_category}")
    print(f"  子维度: {result.sub_categories}")
    print(f"  匹配关键词: {result.matched_keywords}")
    print(f"  置信度: {result.confidence}")

    assert result.primary_category == '衣食住行' or result.primary_category == '非物质文化遗产'
    assert '衣' in result.sub_categories or result.primary_category == '非物质文化遗产'
    assert len(result.matched_keywords) > 0

    print("\n✅ 衣维度识别测试通过")


def test_food_dimension():
    """测试"食"维度识别"""
    print("\n" + "="*60)
    print("测试2: 衣食住行 - 食")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "布依族的糯食文化很有特色，过节家家户户都要打糍粑，还要酿米酒。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"  主维度: {result.primary_category}")
    print(f"  子维度: {result.sub_categories}")
    print(f"  匹配关键词: {result.matched_keywords}")

    assert result.primary_category == '衣食住行'
    assert '食' in result.sub_categories
    assert any(kw in ['糯', '糍粑', '酿酒', '米酒'] for kw in result.matched_keywords)

    print("\n✅ 食维度识别测试通过")


def test_housing_dimension():
    """测试"住"维度识别"""
    print("\n" + "="*60)
    print("测试3: 衣食住行 - 住")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "村里的老房子都是木结构吊脚楼，上面住人下面养牲口。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"  主维度: {result.primary_category}")
    print(f"  子维度: {result.sub_categories}")
    print(f"  匹配关键词: {result.matched_keywords}")

    assert result.primary_category == '衣食住行'
    assert '住' in result.sub_categories
    assert '吊脚楼' in result.matched_keywords

    print("\n✅ 住维度识别测试通过")


def test_folk_culture():
    """测试"民俗"维度识别"""
    print("\n" + "="*60)
    print("测试4: 民俗")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "六月六是布依族最大的节日，这一天全寨的人都会聚集在一起对歌跳舞。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"  主维度: {result.primary_category}")
    print(f"  匹配关键词: {result.matched_keywords}")
    print(f"  文化编码: {result.culture_code}")

    assert result.primary_category == '民俗'
    assert any(kw in ['六月六', '节日', '对歌'] for kw in result.matched_keywords)
    assert result.culture_code == 'F2'  # 六月六的编码

    print("\n✅ 民俗维度识别测试通过")


def test_intangible_heritage():
    """测试"非物质文化遗产"维度识别"""
    print("\n" + "="*60)
    print("测试5: 非物质文化遗产")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "布依族山歌已被列入省级非物质文化遗产名录，但现在会唱的年轻人越来越少了。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"  主维度: {result.primary_category}")
    print(f"  匹配关键词: {result.matched_keywords}")
    print(f"  文化编码: {result.culture_code}")

    assert result.primary_category == '非物质文化遗产'
    assert '非遗' in result.matched_keywords or '山歌' in result.matched_keywords
    assert result.culture_code == 'S1'  # 山歌的编码

    print("\n✅ 非遗维度识别测试通过")


def test_tangible_heritage():
    """测试"物质文化遗产"维度识别"""
    print("\n" + "="*60)
    print("测试6: 物质文化遗产")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "村口的古寨门已经有三百多年历史了，是县级文物保护单位。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"  主维度: {result.primary_category}")
    print(f"  匹配关键词: {result.matched_keywords}")

    assert result.primary_category == '物质文化遗产'
    assert any(kw in ['古', '寨门', '文物', '保护单位'] for kw in result.matched_keywords)

    print("\n✅ 物质文化遗产维度识别测试通过")


def test_policy():
    """测试"政策"维度识别"""
    print("\n" + "="*60)
    print("测试7: 政策")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "现在农村医保政策好了，看病能报销大部分。政府还给每户发了扶贫补贴。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"  主维度: {result.primary_category}")
    print(f"  匹配关键词: {result.matched_keywords}")

    assert result.primary_category == '政策'
    assert any(kw in ['政策', '医保', '政府', '扶贫', '补贴'] for kw in result.matched_keywords)

    print("\n✅ 政策维度识别测试通过")


def test_history():
    """测试"历史"维度识别"""
    print("\n" + "="*60)
    print("测试8: 历史")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "土改的时候，每家每户都分了田。老一辈人说，那时候日子虽然苦，但大家都很有干劲。"
    result = classifier.classify(text)

    print(f"\n原文: {text}")
    print(f"  主维度: {result.primary_category}")
    print(f"  匹配关键词: {result.matched_keywords}")
    print(f"  时间区间: {result.time_period}")

    assert result.primary_category == '历史'
    assert '土改' in result.matched_keywords
    assert result.time_period == '1950-1978'

    print("\n✅ 历史维度识别测试通过")


def test_time_period_extraction():
    """测试时间区间提取"""
    print("\n" + "="*60)
    print("测试9: 时间区间提取")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    test_cases = [
        ("解放前的旧社会，地主收租很重", "1949以前"),
        ("改革开放后，村里开始分田到户", "1979-2000"),
        ("2015年，村里通了公路", "2011-2020"),
        ("现在年轻人都外出打工了", "2021至今")
    ]

    for text, expected_period in test_cases:
        result = classifier.classify(text)
        print(f"\n文本: {text}")
        print(f"  识别时间: {result.time_period}")
        print(f"  预期时间: {expected_period}")
        assert result.time_period == expected_period, f"时间识别错误"
        print("  ✓ 正确")

    print("\n✅ 时间区间提取测试通过")


def test_location_extraction():
    """测试地点提取"""
    print("\n" + "="*60)
    print("测试10: 地点提取")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    test_cases = [
        ("大坪村的蜡染工艺远近闻名", "大坪村"),
        ("纳孔寨每年都举办六月六节", "纳孔寨"),
        ("贞丰县的糯食文化很有特色", "贞丰县")
    ]

    for text, expected_location in test_cases:
        result = classifier.classify(text)
        print(f"\n文本: {text}")
        print(f"  识别地点: {result.location}")
        print(f"  预期地点: {expected_location}")
        assert result.location == expected_location, f"地点识别错误"
        print("  ✓ 正确")

    print("\n✅ 地点提取测试通过")


def test_real_world_example():
    """测试真实世界示例"""
    print("\n" + "="*60)
    print("测试11: 真实世界综合示例")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = """
    王大爷今年78岁了，他说布依族的山歌是祖祖辈辈传下来的宝贝。
    以前每到农忙时节，大家在田里干活都要唱山歌，又热闹又能解乏。
    可是现在年轻人都不愿意学了，觉得土气。
    王大爷很担心，再过些年，这些老歌可能就失传了。
    他希望能有人来记录这些山歌，让后代也能听到祖辈的声音。
    """

    result = classifier.classify(text)

    print(f"\n真实文本:")
    print(text[:100] + "...")

    print(f"\n分类结果:")
    print(f"  主维度: {result.primary_category}")
    print(f"  子维度: {result.sub_categories}")
    print(f"  时间区间: {result.time_period}")
    print(f"  地点: {result.location}")
    print(f"  文化编码: {result.culture_code}")
    print(f"  匹配关键词: {result.matched_keywords}")
    print(f"  置信度: {result.confidence}")

    assert result.primary_category in ['非物质文化遗产', '历史']
    assert result.culture_code == 'S1'  # 山歌
    assert len(result.matched_keywords) > 0

    print("\n✅ 真实世界示例测试通过")


def test_to_dict():
    """测试转字典"""
    print("\n" + "="*60)
    print("测试12: 转换为字典格式")
    print("="*60)

    classifier = BusinessDimensionClassifier()

    text = "六月六节日期间，村民们穿着盛装聚集在一起对歌。"
    result = classifier.classify(text)
    result_dict = classifier.to_dict(result)

    print(f"\n字典格式:")
    for key, value in result_dict.items():
        print(f"  {key}: {value}")

    required_keys = [
        'dimension_category',
        'dimension_sub_category',
        'time_period',
        'location',
        'culture_code',
        'keywords_matched',
        'confidence_score'
    ]

    for key in required_keys:
        assert key in result_dict, f"缺少字段: {key}"

    print("\n✅ 转字典测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("BusinessDimensionClassifier 业务维度分类测试")
    print("这是真正的数据治理核心")
    print("="*60)

    try:
        test_clothing_dimension()
        test_food_dimension()
        test_housing_dimension()
        test_folk_culture()
        test_intangible_heritage()
        test_tangible_heritage()
        test_policy()
        test_history()
        test_time_period_extraction()
        test_location_extraction()
        test_real_world_example()
        test_to_dict()

        print("\n" + "="*60)
        print("✅✅✅ 所有测试通过！")
        print("="*60)
        print("\n核心成果:")
        print("  ✓ 6个业务维度全部可识别")
        print("  ✓ 时间区间自动提取")
        print("  ✓ 地点自动提取")
        print("  ✓ 文化编码自动识别")
        print("  ✓ 关键词匹配可追溯")
        print("\n这才是真正的数据治理！")
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
