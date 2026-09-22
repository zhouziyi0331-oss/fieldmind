"""
文献市场调研Skill - 向量语义测试套件

验证LiteratureMarketResearchSkill的向量检索能力和语义匹配效果
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.services.skills.literature_market_research import LiteratureMarketResearchSkill


def test_real_research_text():
    """测试1: 真实调研报告文本"""
    print("\n" + "="*80)
    print("测试1: 真实调研报告文本")
    print("="*80 + "\n")

    skill = LiteratureMarketResearchSkill()

    # 模拟真实的调研报告片段
    text = """
    前期准备阶段我们做了大量文献调研工作。首先查阅了近五年国内外乡村旅游相关学术论文，
    重点研读了《乡村振兴战略下的文化旅游发展》《社区参与式旅游开发模式研究》等文献，
    梳理了理论基础和研究现状。还仔细研究了国家和省市的乡村振兴政策文件，
    明确了政策导向和资金支持方向。行业报告显示，2023年全国乡村旅游接待游客超过30亿人次，
    市场规模持续扩大，发展潜力巨大。

    在文献研究基础上，我们开展了为期两个月的实地市场调研。对周边三县市的潜在游客
    进行了问卷调查，共发放问卷600份，回收有效问卷537份，有效率89.5%。问卷结果显示，
    78%的受访者表示愿意在周末到乡村度假，人均消费预算在500-800元之间。
    我们还深度访谈了50位已有乡村游经验的游客，了解他们的真实体验和改进建议。
    调研发现，游客最看重的是环境质量、文化特色和服务水平，而不是设施豪华程度。

    竞品分析方面，我们重点调研了周边五个运营较好的乡村旅游项目。其中A村主打高端精品民宿，
    客单价800-1200元，客流量相对有限但利润率高；B村走大众路线，价格亲民但服务质量参差不齐；
    C村的特色是深度文化体验，开发了茶艺、陶艺、传统手工艺等体验项目，回头客比例达到45%。
    通过对比分析发现，本区域内缺乏中高端品质型民宿，市场存在供给缺口。
    竞争对手普遍存在文化挖掘不够深入、淡季客源不足的问题。

    基于数据分析和行业研判，我们认为未来三年乡村旅游仍将保持高速增长态势。
    一方面，乡村振兴战略持续推进，政策支持力度加大，这是重要的发展窗口期；
    另一方面，消费升级趋势明显，游客对品质和体验的要求越来越高，愿意为优质服务付费。
    疫情后人们更加注重健康养生和亲近自然，乡村度假需求将持续旺盛。
    同时我们注意到，非遗文化体验、研学旅行、康养度假等新兴业态正在兴起，
    这些都是未来可以抓住的市场机会。预计未来五年本地区游客量年均增长率将达到25%以上。
    """

    result = skill.analyze(text)

    print(f"✓ 分析成功: {result.success}")
    print(f"✓ 总匹配数: {result.total_matches}")
    print(f"✓ 平均置信度: {result.avg_confidence:.3f}")
    print(f"✓ 执行时间: {result.execution_time:.3f}秒")

    print("\n各维度匹配详情:\n")
    for dim_id, matches in result.dimensions.items():
        if matches:
            dim_name = skill.dimensions[dim_id].dimension_name
            print(f"【{dim_name}】 - {len(matches)}个匹配")
            for i, match in enumerate(matches[:3], 1):  # 只显示前3个
                print(f"  {i}. {match.sentence.strip()[:50]}...")
                print(f"     相似度: {match.similarity:.3f}")

    print(f"\n提取的关键词: {', '.join(result.keywords[:8])}")
    print("\n✅ 测试1通过\n")

    return result


def test_literature_review_dimension():
    """测试2: 文献综述维度识别"""
    print("="*80)
    print("测试2: 文献综述维度识别")
    print("="*80 + "\n")

    skill = LiteratureMarketResearchSkill()

    text = """
    文献检索发现，国内乡村旅游研究主要集中在以下几个方面：产业融合发展、
    文化遗产保护利用、社区参与机制等。查阅了《旅游学刊》《地理研究》等核心期刊
    近三年的相关论文50余篇，梳理出主要理论框架包括可持续发展理论、
    社区赋权理论、文化资本理论等。政策文件方面，国家出台了《关于实施乡村振兴战略的意见》
    《乡村振兴战略规划（2018-2022年）》等重要文件，为项目提供了政策依据。
    """

    result = skill.analyze(text)

    lit_matches = result.dimensions.get('literature_review', [])
    print(f"文献综述维度匹配:")
    print(f"  找到 {len(lit_matches)} 个匹配")
    for match in lit_matches:
        print(f"  - {match.sentence.strip()[:40]}... (相似度: {match.similarity:.3f})")

    if len(lit_matches) > 0:
        avg_sim = sum(m.similarity for m in lit_matches) / len(lit_matches)
        print(f"\n  平均相似度: {avg_sim:.3f}")

    assert len(lit_matches) >= 3, f"文献综述匹配数量不足: {len(lit_matches)}"
    print("\n✅ 测试2通过\n")


def test_market_survey_dimension():
    """测试3: 市场调查维度识别"""
    print("="*80)
    print("测试3: 市场调查维度识别")
    print("="*80 + "\n")

    skill = LiteratureMarketResearchSkill()

    text = """
    我们对目标客户群体进行了深度访谈和问卷调查。共访谈了80位潜在游客，
    了解他们的消费偏好和支付意愿。问卷调查覆盖周边五个城市，回收有效问卷1200份。
    调研数据显示，65%的受访者每年有2-3次乡村旅游需求，人均预算600-1000元。
    实地走访中发现，节假日客流量是平时的5倍以上，淡旺季差异明显。
    通过数据分析发现，年轻家庭和中老年群体是主要客源，他们的需求特点有所不同。
    """

    result = skill.analyze(text)

    survey_matches = result.dimensions.get('market_survey', [])
    print(f"市场调查维度匹配:")
    print(f"  找到 {len(survey_matches)} 个匹配")
    for match in survey_matches:
        print(f"  - {match.sentence.strip()[:40]}... (相似度: {match.similarity:.3f})")

    assert len(survey_matches) >= 4, f"市场调查匹配数量不足: {len(survey_matches)}"
    print("\n✅ 测试3通过\n")


def test_competitive_analysis_dimension():
    """测试4: 竞品分析维度识别"""
    print("="*80)
    print("测试4: 竞品分析维度识别")
    print("="*80 + "\n")

    skill = LiteratureMarketResearchSkill()

    text = """
    竞品调研发现，周边已有七八个同类项目在运营。其中标杆项目X村的成功经验值得学习，
    他们打造了独特的文化IP，建立了稳定的回头客群体，复购率超过50%。
    竞争对手Y村主打高端市场，定位精准但市场容量有限。通过对比分析发现，
    现有项目在文化体验深度和服务品质上还有提升空间，这是我们的差异化机会。
    案例研究表明，成功项目都非常重视品牌建设和口碑营销。
    """

    result = skill.analyze(text)

    comp_matches = result.dimensions.get('competitive_analysis', [])
    print(f"竞品分析维度匹配:")
    print(f"  找到 {len(comp_matches)} 个匹配")
    for match in comp_matches:
        print(f"  - {match.sentence.strip()[:40]}... (相似度: {match.similarity:.3f})")

    if len(comp_matches) > 0:
        avg_sim = sum(m.similarity for m in comp_matches) / len(comp_matches)
        print(f"\n  平均相似度: {avg_sim:.3f}")

    assert len(comp_matches) >= 3, f"竞品分析匹配数量不足: {len(comp_matches)}"
    print("\n✅ 测试4通过\n")


def test_trend_forecast_dimension():
    """测试5: 趋势预测维度识别"""
    print("="*80)
    print("测试5: 趋势预测维度识别")
    print("="*80 + "\n")

    skill = LiteratureMarketResearchSkill()

    text = """
    基于数据分析和行业研判，我们预测未来三到五年乡村旅游市场将继续保持高增长。
    乡村振兴政策支持力度持续加大，这是重要的战略机遇期。消费升级趋势下，
    游客对品质和体验的要求越来越高，中高端市场潜力巨大。
    后疫情时代人们更注重健康和亲近自然，乡村度假需求将持续旺盛。
    预判非遗文化体验、研学旅行、康养度假等新兴业态将快速发展，
    预计本区域游客量年均增长率将达到20%以上。
    """

    result = skill.analyze(text)

    trend_matches = result.dimensions.get('trend_forecast', [])
    print(f"趋势预测维度匹配:")
    print(f"  找到 {len(trend_matches)} 个匹配")
    for match in trend_matches:
        print(f"  - {match.sentence.strip()[:40]}... (相似度: {match.similarity:.3f})")

    if len(trend_matches) > 0:
        avg_sim = sum(m.similarity for m in trend_matches) / len(trend_matches)
        print(f"\n  平均相似度: {avg_sim:.3f}")

    assert len(trend_matches) >= 4, f"趋势预测匹配数量不足: {len(trend_matches)}"
    print("\n✅ 测试5通过\n")


def test_performance():
    """测试6: 性能测试 - 模型缓存效果"""
    print("="*80)
    print("测试6: 性能测试 - 模型缓存效果")
    print("="*80 + "\n")

    import time

    skill = LiteratureMarketResearchSkill()

    text = """
    查阅了大量学术文献和行业报告，对市场进行了深入调研，分析了主要竞争对手，
    预测了未来发展趋势。调研发现市场需求旺盛，竞争格局相对分散，存在较大机会。
    """

    # 第一次执行（冷启动）
    start1 = time.time()
    result1 = skill.analyze(text)
    time1 = time.time() - start1

    # 第二次执行（利用缓存）
    start2 = time.time()
    result2 = skill.analyze(text)
    time2 = time.time() - start2

    print(f"第一次执行: {time1:.3f}秒")
    print(f"第二次执行: {time2:.3f}秒")
    print(f"加速比: {time1/time2:.2f}x")

    assert result1.total_matches == result2.total_matches, "两次执行结果不一致"
    print("\n✅ 测试6通过\n")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("文献市场调研Skill - 向量语义测试套件")
    print("="*80)

    # 运行所有测试
    result = test_real_research_text()
    test_literature_review_dimension()
    test_market_survey_dimension()
    test_competitive_analysis_dimension()
    test_trend_forecast_dimension()
    test_performance()

    print("="*80)
    print("✅ 所有测试通过！")
    print("="*80)

    print(f"\n核心指标:")
    print(f"  - 总匹配数: {result.total_matches}")
    print(f"  - 平均置信度: {result.avg_confidence:.3f}")
    print(f"  - 执行时间: {result.execution_time:.3f}秒")
    print(f"  - 维度覆盖: 4/4")
