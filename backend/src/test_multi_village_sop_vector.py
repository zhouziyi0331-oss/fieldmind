"""
测试多村比较分析Skill的向量语义功能
Test Multi-Village SOP Skill vector semantic analysis
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.skills.multi_village_sop import MultiVillageSOPSkill
import time
import numpy as np


def test_real_comparative_text():
    """测试1: 真实多村比较文本"""
    print("\n" + "="*80)
    print("测试1: 真实多村比较调查文本")
    print("="*80)

    text = """
    这次调研了三个村：张家村、李家村和王家村。从基本情况看，张家村最大，
    有600多户2500人，李家村中等规模400户1800人，王家村最小200户不到1000人。
    三个村都在山区，但张家村靠近县城，开车半小时就到，交通很方便。
    李家村在山里，离县城一个多小时。王家村最偏远，要两个小时山路。

    经济水平差异很明显。张家村人均收入达到4万元，主要靠乡村旅游和特色种植。
    李家村人均2万多，主要还是传统农业加外出务工。王家村最困难，人均只有1.2万，
    基本就靠种地和低保。基础设施方面，张家村水电路网都很完善，村里道路全部硬化，
    还有污水处理系统。李家村基础设施一般，主路硬化了但很多巷道还是土路。
    王家村条件最差，连自来水都不稳定。

    发展路径上，三个村走的路完全不同。张家村依托区位优势和古村落资源，
    大力发展乡村旅游，村集体办了民宿和农家乐，带动村民增收。李家村主打
    特色农产品，成立了合作社种植中药材，但规模还不大，效益一般。王家村
    基本还是传统种植，没什么产业，年轻人都外出打工了。

    在治理模式上也有差异。张家村的村支书很有能力，十几年一直连任，
    村里发展的大小事都是他在推动，村民很信任他。李家村情况比较复杂，
    村里有几个大姓，宗族势力强，村委会协调起来比较难。王家村干部年龄偏大，
    思想比较保守，缺乏发展意识。

    分析下来，造成三个村差异的关键因素有这么几点：一是地理位置，
    张家村靠近县城是最大优势。二是带头人，张家村支书有想法有能力，
    这点太重要了。三是资源禀赋，张家村有古建筑群，是发展旅游的基础。
    四是政策支持，张家村被列为省级美丽乡村示范点，获得大量项目资金。

    从比较中可以总结出一些规律：第一，区位条件固然重要，但不是决定性的，
    关键还是要有好的带头人和发展思路。第二，产业发展是核心，不能只靠
    外出务工和政府补贴。第三，要因地制宜，张家村的旅游模式不能简单
    复制到王家村。第四，基础设施是前提，路不通什么都搞不起来。
    """

    skill = MultiVillageSOPSkill()
    result = skill.analyze(text)

    print(f"\n✓ 分析成功: {result.success}")
    print(f"✓ 总匹配数: {result.total_matches}")
    print(f"✓ 平均置信度: {result.avg_confidence:.3f}")
    print(f"✓ 执行时间: {result.execution_time:.3f}秒")

    print(f"\n各维度匹配详情:")
    for dim_id, matches in result.dimensions.items():
        print(f"\n【{matches[0].dimension_name}】 - {len(matches)}个匹配")
        for i, match in enumerate(matches[:3], 1):
            print(f"  {i}. {match.sentence[:60]}...")
            print(f"     相似度: {match.similarity:.3f}")

    print(f"\n提取的关键词: {', '.join(result.keywords[:10])}")

    assert result.success, "应该成功识别多村比较内容"
    assert result.total_matches >= 15, f"应该至少有15个匹配，实际: {result.total_matches}"
    assert result.avg_confidence > 0.65, f"平均置信度应该>0.65，实际: {result.avg_confidence}"
    assert len(result.dimensions) >= 3, f"应该覆盖至少3个维度，实际: {len(result.dimensions)}"

    print("\n✅ 测试1通过")
    return result


def test_baseline_comparison():
    """测试2: 基础对比维度"""
    print("\n" + "="*80)
    print("测试2: 基础对比能力测试")
    print("="*80)

    text = """
    A村有800户3000多人，B村只有300户1200人，规模差了一倍多。
    两个村的地理位置很不一样，A村在平原地区，B村在山区。
    经济水平对比：A村人均收入5万元，B村2万元，差距明显。
    基础设施方面，A村的路、水、电都很完善，B村还比较落后。
    """

    skill = MultiVillageSOPSkill()
    result = skill.analyze(text)

    print(f"\n基础对比维度匹配:")
    if 'baseline_comparison' in result.dimensions:
        matches = result.dimensions['baseline_comparison']
        print(f"  找到 {len(matches)} 个匹配")
        for match in matches:
            print(f"  - {match.sentence} (相似度: {match.similarity:.3f})")

        avg_sim = np.mean([m.similarity for m in matches])
        print(f"\n  平均相似度: {avg_sim:.3f}")
        assert avg_sim > 0.65, f"基础对比维度平均相似度应该>0.65，实际: {avg_sim}"

    print("\n✅ 测试2通过")


def test_difference_analysis():
    """测试3: 差异分析维度"""
    print("\n" + "="*80)
    print("测试3: 差异分析能力测试")
    print("="*80)

    text = """
    A村和B村的发展路径完全不同，A村搞旅游，B村搞工业。
    治理模式上差异明显，A村是村委会主导，B村宗族势力更强。
    文化特征也不一样，A村保留传统习俗多，B村更现代化开放。
    社会结构对比：A村宗族观念强，B村外来人口多，更包容。
    """

    skill = MultiVillageSOPSkill()
    result = skill.analyze(text)

    print(f"\n差异分析维度匹配:")
    if 'difference_analysis' in result.dimensions:
        matches = result.dimensions['difference_analysis']
        print(f"  找到 {len(matches)} 个匹配")
        for match in matches:
            print(f"  - {match.sentence} (相似度: {match.similarity:.3f})")

        assert len(matches) >= 3, f"应该识别至少3个差异点，实际: {len(matches)}"

    print("\n✅ 测试3通过")


def test_factor_identification():
    """测试4: 因素识别维度"""
    print("\n" + "="*80)
    print("测试4: 影响因素识别测试")
    print("="*80)

    text = """
    A村发展好主要是因为有个能干的书记，这是关键。
    地理位置是重要因素，靠近高速路口带来很大便利。
    B村落后很大程度上源于交通不便，山路难行。
    政策支持力度不同，A村得到示范村项目，资金充足。
    A村有独特的温泉资源，这是其他村无法复制的优势。
    """

    skill = MultiVillageSOPSkill()
    result = skill.analyze(text)

    print(f"\n因素识别维度匹配:")
    if 'factor_identification' in result.dimensions:
        matches = result.dimensions['factor_identification']
        print(f"  找到 {len(matches)} 个匹配")
        for match in matches:
            print(f"  - {match.sentence} (相似度: {match.similarity:.3f})")

        avg_sim = np.mean([m.similarity for m in matches])
        print(f"\n  平均相似度: {avg_sim:.3f}")
        assert avg_sim > 0.70, f"因素识别维度平均相似度应该>0.70，实际: {avg_sim}"

    print("\n✅ 测试4通过")


def test_pattern_extraction():
    """测试5: 模式提炼维度"""
    print("\n" + "="*80)
    print("测试5: 模式提炼能力测试")
    print("="*80)

    text = """
    调研发现，成功的村庄都有一个共性：都有强有力的党支部领导。
    A村的"合作社+农户"模式值得其他村学习借鉴，可复制性强。
    从比较中总结出规律：资源重要，但人的因素更关键。
    这几个村的经验表明，生态保护和经济发展可以双赢。
    典型教训是：不尊重村民意愿的项目都失败了，这点要记住。
    """

    skill = MultiVillageSOPSkill()
    result = skill.analyze(text)

    print(f"\n模式提炼维度匹配:")
    if 'pattern_extraction' in result.dimensions:
        matches = result.dimensions['pattern_extraction']
        print(f"  找到 {len(matches)} 个匹配")
        for match in matches:
            print(f"  - {match.sentence} (相似度: {match.similarity:.3f})")

        avg_sim = np.mean([m.similarity for m in matches])
        print(f"\n  平均相似度: {avg_sim:.3f}")
        assert avg_sim > 0.70, f"模式提炼维度平均相似度应该>0.70，实际: {avg_sim}"

    print("\n✅ 测试5通过")


def test_performance():
    """测试6: 性能测试"""
    print("\n" + "="*80)
    print("测试6: 性能测试 - 模型缓存效果")
    print("="*80)

    text = "A村和B村规模不同，发展路径也不一样。关键因素是地理位置和带头人。"

    skill = MultiVillageSOPSkill()

    # 第一次调用
    start1 = time.time()
    result1 = skill.analyze(text)
    time1 = time.time() - start1

    # 第二次调用（使用缓存）
    start2 = time.time()
    result2 = skill.analyze(text)
    time2 = time.time() - start2

    print(f"\n第一次执行: {time1:.3f}秒")
    print(f"第二次执行: {time2:.3f}秒")
    print(f"加速比: {time1/time2:.2f}x")

    assert time2 < time1, "第二次执行应该更快（使用缓存）"
    print("\n✅ 测试6通过")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("多村比较分析Skill - 向量语义测试套件")
    print("="*80)

    try:
        # 运行所有测试
        result = test_real_comparative_text()
        test_baseline_comparison()
        test_difference_analysis()
        test_factor_identification()
        test_pattern_extraction()
        test_performance()

        print("\n" + "="*80)
        print("✅ 所有测试通过！")
        print("="*80)
        print(f"\n核心指标:")
        print(f"  - 总匹配数: {result.total_matches}")
        print(f"  - 平均置信度: {result.avg_confidence:.3f}")
        print(f"  - 执行时间: {result.execution_time:.3f}秒")
        print(f"  - 维度覆盖: {len(result.dimensions)}/4")

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
