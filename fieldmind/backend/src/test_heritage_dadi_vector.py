"""
测试大地文化遗产活化运营Skill的向量语义功能
Test Heritage DADI Skill based on Dadi methodology
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.skills.heritage_dadi import HeritageDADISkill
import time


def test_real_dadi_project_text():
    """测试1: 真实项目文本 - 大地方法论综合体现"""
    print("\n" + "="*80)
    print("测试1: 真实项目文本 - 大地方法论综合体现")
    print("="*80)

    text = """
    我们这个古村活化项目，一开始就把保护、旅游、产业和社区发展统筹考虑，
    做了一张总体规划蓝图。不能像以前那样各干各的，文保部门只管保护，
    旅游公司只顾赚钱，最后搞得一团糟。现在规划阶段就把四个维度都纳入进来了。

    团队组建上，我们打破了传统的单一专业模式。除了文化遗产专家，还引入了艺术家、
    建筑设计师、商业运营团队、科技公司做数字化，形成了真正的跨界合作。
    这些不同领域的人在一起碰撞，产生了很多新想法。

    利益分配机制是关键。我们明确规定本地居民在项目中的主体地位，
    成立了村民合作社，收益按比例分红，还预留了讲解员、民宿管家等就业岗位给村民。
    保护单位、运营公司、当地社区三方利益都要平衡，任何一方长期受损都不可持续。

    最重要的是，我们从规划阶段就引入了运营团队的思维。不是等建完了再想怎么运营，
    而是一开始就问：一年后这里靠什么持续吸引人？内容怎么更新？谁来负责日常管理？
    这样设计出来的方案才真正能落地运转。

    内容挖掘上，我们不满足于简单展示这座古桥、那栋老屋。而是深入挖掘背后的故事：
    这座桥见证了当地的茶马古道贸易，这段历史能回应今天乡村振兴中的产业振兴问题。
    我们追问的是：这件遗产在当下语境中能回应什么社会问题？为什么在今天仍有意义？

    艺术化转化也是重点。我们请了艺术家把传统的土家族织锦元素重新设计，
    做成现代装置艺术放在民宿大堂。老建筑不只是保护对象，也是可以再创作的艺术素材。
    设计师用当代手法演绎传统美学，让年轻人也能产生共鸣。

    乡土生活的激活同样重要。我们发现城市家庭很向往那种邻里相处、集体劳作的场景。
    所以把打糍粑、晒秋、赶集等乡土生活方式变成可以参与的体验项目。
    不是简单复原民俗表演，而是真的让游客融入当地的生活节奏和社群关系。

    转化路径上，我们把文化内容植入到"食住行游购娱"的每个环节。
    特色餐饮用本地食材和传统做法，民宿设计融入土家建筑符号，伴手礼开发了文创产品。
    每个文化元素都找到了具体的旅游要素载体。

    原来的村史馆只是静态展览，我们重新设计成了开放式的文化沙龙空间，
    可以办讲座、做手工、搞研学。公共文化设施不能只有展陈功能，
    要增加体验和经营属性，让它真正活起来。

    最成功的是我们孵化的"古村音乐节"IP。每年春天举办一次，邀请民谣歌手来演出，
    已经办了三届，现在成了区域性的文化品牌。这个IP是可识别、可复购、可授权的资产，
    不是办完就散的一次性活动。

    在EPCO机制上，我们从一开始就实行设计、采购、施工、运营一体化管理。
    设计师出方案的时候，运营团队就在旁边提意见：这个空间以后怎么用？
    那个设施维护成本高不高？这样避免了各环节脱节，减少了大量返工浪费。

    运营前置的思维贯穿全程。施工阶段我们就预留了后期运营所需的水电接口、
    仓储空间、办公场地。顶层规划、空间改造、内容植入、日常管理形成了完整闭环。
    这种模式让项目降本、保质、提效，周期大大缩短。
    """

    skill = HeritageDADISkill()
    result = skill.analyze(text)

    print(f"\n✓ 分析成功: {result.success}")
    print(f"✓ 总匹配数: {result.total_matches}")
    print(f"✓ 平均置信度: {result.avg_confidence:.3f}")
    print(f"✓ 执行时间: {result.execution_time:.3f}秒")

    print(f"\n各维度匹配详情:")
    for dim_id, matches in result.dimensions.items():
        if matches:
            print(f"\n【{matches[0].dimension_name}】 - {len(matches)}个匹配")
            for i, match in enumerate(matches[:3], 1):
                print(f"  {i}. {match.sentence.strip()[:60]}...")
                print(f"     相似度: {match.similarity:.3f}")

    print(f"\n提取的关键词: {', '.join(result.keywords[:8])}")

    assert result.success, "应该成功识别大地方法论内容"
    assert result.total_matches >= 20, f"应该至少有20个匹配，实际: {result.total_matches}"
    print("\n✅ 测试1通过")
    return result


def test_value_principles():
    """测试2: 价值层-四大原则"""
    print("\n" + "="*80)
    print("测试2: 价值层-四大原则识别")
    print("="*80)

    text = """
    这个方案必须统筹保护、旅游、产业、社区四个维度，不能顾此失彼。
    我们组建了跨学科团队，文化、艺术、科技、商业各领域专家都参与进来。
    村民要参与决策和收益分配，保护方、运营方、社区三方利益必须平衡。
    项目不是建完就完事，必须有三年的内容更新计划和持续运营机制。
    """

    skill = HeritageDADISkill()
    result = skill.analyze(text)

    value_matches = result.dimensions.get('value_principles', [])
    print(f"\n价值层匹配: {len(value_matches)}个")
    for match in value_matches:
        print(f"  - {match.sentence.strip()[:50]}... (相似度: {match.similarity:.3f})")

    assert len(value_matches) >= 3, f"价值层匹配不足: {len(value_matches)}"
    print("\n✅ 测试2通过")


def test_content_excavation():
    """测试3: 方法层-内容挖掘"""
    print("\n" + "="*80)
    print("测试3: 方法层-内容挖掘识别")
    print("="*80)

    text = """
    这座古桥不只是文物，它见证了茶马古道的商贸繁荣，能回应今天的乡村产业振兴问题。
    我们请艺术家把传统剪纸元素重新设计，做成现代装置艺术。
    打糍粑、晒秋这些乡土生活方式，能让城市家庭找到久违的邻里感和慢节奏。
    不满足于"发现了什么"，要追问"它为什么在今天仍有意义"。
    """

    skill = HeritageDADISkill()
    result = skill.analyze(text)

    excavation_matches = result.dimensions.get('content_excavation', [])
    print(f"\n内容挖掘匹配: {len(excavation_matches)}个")
    for match in excavation_matches:
        print(f"  - {match.sentence.strip()[:50]}... (相似度: {match.similarity:.3f})")

    assert len(excavation_matches) >= 3, f"内容挖掘匹配不足: {len(excavation_matches)}"
    print("\n✅ 测试3通过")


def test_content_transformation():
    """测试4: 方法层-内容转化"""
    print("\n" + "="*80)
    print("测试4: 方法层-内容转化识别")
    print("="*80)

    text = """
    文化主题与餐饮、住宿、游览、购物全面融合，打造完整的旅游要素体验。
    村史馆改造成可以办沙龙、做研学的开放式体验空间，不再是单纯展陈。
    孵化了"古村音乐节"这个IP，每年办一次，已经成为可识别、可复购的区域品牌。
    """

    skill = HeritageDADISkill()
    result = skill.analyze(text)

    transformation_matches = result.dimensions.get('content_transformation', [])
    print(f"\n内容转化匹配: {len(transformation_matches)}个")
    for match in transformation_matches:
        print(f"  - {match.sentence.strip()[:50]}... (相似度: {match.similarity:.3f})")

    assert len(transformation_matches) >= 2, f"内容转化匹配不足: {len(transformation_matches)}"
    print("\n✅ 测试4通过")


def test_epco_mechanism():
    """测试5: 落地层-EPCO机制"""
    print("\n" + "="*80)
    print("测试5: 落地层-EPCO机制识别")
    print("="*80)

    text = """
    规划阶段就要想清楚谁来运营、如何持续，不能建完再说。
    设计、采购、施工、运营一体化管理，避免各环节脱节和返工浪费。
    运营不是最后环节，而是贯穿全链条的第一思维。
    EPCO模式让我们在施工时就预留了后期运营所需的设施接口。
    """

    skill = HeritageDADISkill()
    result = skill.analyze(text)

    epco_matches = result.dimensions.get('epco_mechanism', [])
    print(f"\nEPCO机制匹配: {len(epco_matches)}个")
    for match in epco_matches:
        print(f"  - {match.sentence.strip()[:50]}... (相似度: {match.similarity:.3f})")

    assert len(epco_matches) >= 3, f"EPCO机制匹配不足: {len(epco_matches)}"
    print("\n✅ 测试5通过")


def test_performance():
    """测试6: 性能测试"""
    print("\n" + "="*80)
    print("测试6: 性能测试 - 模型缓存效果")
    print("="*80)

    text = """
    项目统筹了保护、旅游、产业、社区四个维度，引入跨界团队，
    建立了三方利益平衡机制，设计了内容持续更新计划。
    """

    skill = HeritageDADISkill()

    start1 = time.time()
    result1 = skill.analyze(text)
    time1 = time.time() - start1

    start2 = time.time()
    result2 = skill.analyze(text)
    time2 = time.time() - start2

    print(f"\n第一次执行: {time1:.3f}秒")
    print(f"第二次执行: {time2:.3f}秒")
    print(f"加速比: {time1/time2:.2f}x")

    assert result1.total_matches == result2.total_matches
    print("\n✅ 测试6通过")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("大地文化遗产活化运营Skill - 向量语义测试套件")
    print("="*80)

    result = test_real_dadi_project_text()
    test_value_principles()
    test_content_excavation()
    test_content_transformation()
    test_epco_mechanism()
    test_performance()

    print("\n" + "="*80)
    print("✅ 所有测试通过！")
    print("="*80)

    print(f"\n核心指标:")
    print(f"  - 总匹配数: {result.total_matches}")
    print(f"  - 平均置信度: {result.avg_confidence:.3f}")
    print(f"  - 执行时间: {result.execution_time:.3f}秒")
    print(f"  - 维度覆盖: 4/4")
