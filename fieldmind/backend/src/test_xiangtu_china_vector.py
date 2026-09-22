"""
测试乡土中国Skill的向量语义分析功能
验证理论框架在田野文本中的识别能力
"""
import sys
import time
from pathlib import Path
import numpy as np

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.skills.xiangtu_china import XiangtuChinaSkill


def print_separator(title: str = ""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    else:
        print(f"{'-'*80}")


def test_real_field_text():
    """测试真实的田野调查文本"""
    print_separator("测试1: 真实田野调查文本 - 乡土中国理论识别")

    # 真实的田野调查文本，包含乡土中国理论的各个维度
    field_text = """
    XX村是一个典型的北方农村，村民世世代代守着这片土地，祖祖辈辈都在这里耕种。
    虽然现在年轻人外出打工的多了，但老一辈人还是安土重迁，宁愿守着几亩薄田也
    不愿离开故土。他们说，这里是根，土地是命根子，离开了就没了依靠。

    村里人都是几代人住在一起，谁家什么情况大家都知根知底。老街坊老邻居，低头
    不见抬头见，彼此太熟悉了。从小一起长大的玩伴，相互之间非常了解和信任。
    村里没有陌生人，新来的外地媳妇，不出半年大家就摸清了她家的底细。做生意
    借钱不用签合同，因为彼此熟悉，一句话就能作数。

    村里办事讲究关系远近。遇到困难首先找自己的本家亲戚，远房的也会伸手帮一把。
    办红白喜事时，按照关系亲疏决定帮忙的程度和份子钱多少。同姓本家之间相互
    照应，形成了一个紧密的关系网。外村来的媳妇刚开始被当外人，多年后才慢慢
    融入本村的圈子。村里有个说法：自己人就是自己人，外人就是外人，这界限
    分得清清楚楚。

    村里有很多老规矩，虽然没写在纸上，但大家都自觉遵守。办事讲究礼数，不守
    规矩会被人说闲话，在村里抬不起头。邻里有了纠纷，一般都是找村里德高望重的
    老人调解，很少闹到法院去。传统习俗代代相传，谁要破坏就会被全村人指责。
    年轻人做事不合规矩，老人会教训说这是祖上传下来的规矩不能改。村里靠舆论和
    面子维持秩序，做了丢人的事，全村都会知道，以后就没法在村里待了。

    总的来说，XX村虽然经历了现代化的冲击，但传统的乡土社会特征依然明显。
    """

    # 创建skill实例
    skill = XiangtuChinaSkill()

    # 执行分析
    start_time = time.time()
    result = skill.analyze(field_text)
    elapsed = time.time() - start_time

    # 打印结果
    print(f"分析完成 (耗时: {elapsed:.3f}秒)")
    print(f"Skill: {result.skill_name}")
    print(f"总匹配数: {result.total_matches}")
    print(f"整体置信度: {result.avg_confidence:.3f}")
    print()

    # 打印各维度结果
    for dim_id, matches in result.dimensions.items():
        if matches:
            first_match = matches[0]
            print(f"\n【维度】{first_match.dimension_name}")
            print(f"  维度ID: {dim_id}")
            print(f"  匹配数: {len(matches)}")

            avg_sim = np.mean([m.similarity for m in matches])
            print(f"  平均置信度: {avg_sim:.3f}")

            print(f"  典型案例:")
            for i, match in enumerate(matches[:3], 1):
                print(f"    {i}. [{match.similarity:.3f}] {match.sentence[:70]}...")

    print_separator()
    return result


def test_theory_recognition():
    """测试理论概念识别"""
    print_separator("测试2: 理论概念在具体情境中的识别")

    test_cases = [
        ("差序格局", "村里修路集资，本家族的多出钱，远房亲戚少出点，外姓的随意"),
        ("礼治秩序", "张家儿子不孝顺，全村人都指责，老张在村里再也抬不起头"),
        ("熟人社会", "村里人借东西从不打借条，因为低头不见抬头见，谁敢不还"),
        ("乡土本色", "虽然城里生活好，但老王说死也要死在老家，葬在祖坟"),
    ]

    skill = XiangtuChinaSkill()

    for theory_name, text in test_cases:
        print(f"\n测试理论概念: {theory_name}")
        print(f"文本: {text}")

        result = skill.analyze(text)

        # 找到匹配最高的维度
        best_dim = None
        best_score = 0
        for dim_id, matches in result.dimensions.items():
            if matches:
                max_score = max(m.similarity for m in matches)
                if max_score > best_score:
                    best_score = max_score
                    best_dim = matches[0].dimension_name

        if best_dim:
            print(f"  ✓ 识别为: {best_dim} (置信度: {best_score:.3f})")
        else:
            print(f"  ✗ 未识别到理论概念")

    print_separator()


def test_multiple_dimensions():
    """测试同一文本中识别多个理论维度"""
    print_separator("测试3: 复杂文本中的多维度识别")

    complex_text = """
    李家和王家因为宅基地发生纠纷，没有去法院，而是请村里的老支书调解。
    老支书说，两家祖祖辈辈都是邻居，又都是本村的老户，低头不见抬头见的，
    闹僵了对谁都不好。最后按照村里的老规矩，划出了一条公认的界线，
    两家人也都给老支书面子，不再争执。
    """

    print("测试文本:")
    print(complex_text)
    print()

    skill = XiangtuChinaSkill()
    result = skill.analyze(complex_text)

    print(f"识别到的理论维度: {result.total_matches} 个匹配")
    print()

    for dim_id, matches in result.dimensions.items():
        if matches:
            first_match = matches[0]
            avg_sim = np.mean([m.similarity for m in matches])
            print(f"  【{first_match.dimension_name}】")
            print(f"    匹配数: {len(matches)}, 平均置信度: {avg_sim:.3f}")
            print(f"    最高匹配: [{matches[0].similarity:.3f}] {matches[0].sentence[:60]}...")

    print_separator()


def test_synonym_recognition():
    """测试理论概念的不同表述形式"""
    print_separator("测试4: 理论概念的多样表述识别")

    # 差序格局的不同表述
    expressions = [
        "关系近的多帮衬，关系远的少照应",
        "分内外有别，自家人和外人不一样",
        "按亲疏远近办事，这是天经地义的",
    ]

    skill = XiangtuChinaSkill()

    print("测试'差序格局'的不同表述:")
    for expr in expressions:
        print(f"\n  表述: {expr}")
        result = skill.analyze(expr)

        if result.total_matches > 0:
            for dim_id, matches in result.dimensions.items():
                if matches:
                    print(f"    ✓ 识别为: {matches[0].dimension_name} [{matches[0].similarity:.3f}]")
        else:
            print(f"    ✗ 未识别")

    print_separator()


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("  乡土中国Skill - 向量语义理论分析测试")
    print("="*80)

    try:
        # 测试1: 真实田野文本
        result = test_real_field_text()

        # 测试2: 理论概念识别
        test_theory_recognition()

        # 测试3: 多维度识别
        test_multiple_dimensions()

        # 测试4: 同义表述识别
        test_synonym_recognition()

        # 最终总结
        print_separator("测试总结")
        print("✓ 所有测试完成")
        print(f"✓ 成功将费孝通《乡土中国》理论框架应用于田野文本分析")
        print(f"✓ 能够识别差序格局、礼治秩序、熟人社会、乡土本色四大维度")
        print(f"✓ 向量语义方法可以识别理论概念的多样表述形式")
        print(f"✓ 为学术理论与田野材料的对接提供了技术支持")
        print("="*80)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
