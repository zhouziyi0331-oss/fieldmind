"""
测试费孝通《乡土中国》Skill（完整8维度版）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app.services.skills.xiangtu_china import XiangtuChinaSkill


class TestXiangtuChinaSkill:
    """测试乡土中国理论分析Skill"""

    @pytest.fixture
    def skill(self):
        """创建skill实例"""
        return XiangtuChinaSkill()

    def test_skill_metadata(self, skill):
        """测试skill基本信息"""
        assert skill.skill_id == "xiangtu_china"
        assert "乡土中国" in skill.skill_name
        assert "费孝通" in skill.skill_description or "社会学" in skill.skill_description

    def test_dimensions_count(self, skill):
        """测试维度数量（应该是8个）"""
        assert len(skill.dimensions) == 8, f"应有8个维度，实际有{len(skill.dimensions)}个"

    def test_all_8_dimensions_present(self, skill):
        """测试8个核心维度是否都存在"""
        expected_dimensions = [
            'xiangtu_nature',           # 乡土本色
            'differential_mode',         # 差序格局
            'ritual_order',             # 礼治秩序
            'family_gender',            # 家族与男女有别
            'elder_rule',               # 长老统治
            'kinship_locality',         # 血缘与地缘
            'literacy_communication',   # 文字与乡（沟通钥匙）
            'cultural_consciousness'    # 文化自觉（转化钥匙）
        ]

        for dim_id in expected_dimensions:
            assert dim_id in skill.dimensions, f"缺少维度: {dim_id}"

    def test_xiangtu_nature_dimension(self, skill):
        """测试维度1：乡土本色（熟人社会）"""
        text = """
        我们村的人基本都认识，从小一起长大的。祖祖辈辈都生活在这里，
        离不开这片土地。大家都是熟人，抬头不见低头见，在村里办事不需要合同，
        大家都信得过。外来的人很少，本村人很少搬走。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'xiangtu_nature' in result.dimensions
        matches = result.dimensions['xiangtu_nature']
        assert len(matches) > 0, "应该检测到'乡土本色'特征"

        # 检查置信度
        avg_conf = sum(m.similarity for m in matches) / len(matches) if matches else 0
        assert avg_conf > 0.60, f"乡土本色维度置信度过低: {avg_conf:.3f}"

    def test_differential_mode_dimension(self, skill):
        """测试维度2：差序格局"""
        text = """
        村里办事要找对人，关键看你认识谁。这个项目能不能做，要看村里几个主要人物的态度。
        他家在村里说话有分量，是大姓。外来投资者很难融入村里的关系网。
        村民之间的合作主要靠亲戚关系，决策时会先问几个长者和大户的意见。
        红白喜事能看出谁在村里的人脉广。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'differential_mode' in result.dimensions
        matches = result.dimensions['differential_mode']
        assert len(matches) > 0, "应该检测到'差序格局'特征"

    def test_ritual_order_dimension(self, skill):
        """测试维度3：礼治秩序（含"无讼"）"""
        text = """
        村里有纠纷一般不会去法院，都是内部调解。村规民约规定了很多行为规范。
        遇到矛盾会请村里德高望重的老人来说理。打官司在村里被认为是很丢脸的事。
        很多事情靠口头约定和信任，不签合同。村民大会商议重要事项，少数服从多数。
        长辈的话在村里很有权威性。违反村规会受到舆论谴责，在村里抬不起头。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'ritual_order' in result.dimensions
        matches = result.dimensions['ritual_order']
        assert len(matches) > 0, "应该检测到'礼治秩序'特征"

    def test_family_gender_dimension(self, skill):
        """测试维度4：家族与男女有别"""
        text = """
        村里最大的几个姓氏各有祠堂。家族决策由族长和几个长辈共同商定。
        清明和春节都要集体祭祖。村里的土地和资源按家族分配。
        妇女主要负责家务和照顾老人孩子。公共事务中很少见到女性参与决策。
        大家族在村里很有影响力。家族内部的事情优先由家族内部解决。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'family_gender' in result.dimensions
        matches = result.dimensions['family_gender']
        assert len(matches) > 0, "应该检测到'家族与男女有别'特征"

    def test_elder_rule_dimension(self, skill):
        """测试维度5：长老统治"""
        text = """
        村里的重要决策都要征求几位老人的意见。老人说的话在村里很有分量。
        年轻人做事要听长辈的建议。村里有专门的老年人协会参与管理。
        传统技艺主要由老人传授。长者在纠纷调解中扮演重要角色。
        老人的口述历史是村庄记忆的重要载体。村民对老年人普遍尊重和照顾。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'elder_rule' in result.dimensions
        matches = result.dimensions['elder_rule']
        assert len(matches) > 0, "应该检测到'长老统治'特征"

    def test_kinship_locality_dimension(self, skill):
        """测试维度6：血缘与地缘"""
        text = """
        村里主要是三个大姓，各占一片区域。同姓的人家住得比较集中。
        在外打工的人最终都想回乡养老。村民对家乡有很强的认同感。
        外出的年轻人过年一定要回来。村后山上是各家族的祖坟。
        很多在外成功人士会回馈家乡。"金窝银窝不如自己的草窝"是村民常说的话。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'kinship_locality' in result.dimensions
        matches = result.dimensions['kinship_locality']
        assert len(matches) > 0, "应该检测到'血缘与地缘'特征"

    def test_literacy_communication_dimension(self, skill):
        """测试维度7：文字与乡（沟通钥匙）"""
        text = """
        村里的通知主要通过大喇叭广播。重要事情要开村民大会当面讲。
        老人不识字，书面材料看不懂。消息在村里传得很快，口口相传。
        现在用微信群通知，但还是要当面确认。公示栏贴了文件，但很少人去看。
        问卷调查要面对面访谈才有效。村民更相信当面说的话而不是书面承诺。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'literacy_communication' in result.dimensions
        matches = result.dimensions['literacy_communication']
        assert len(matches) > 0, "应该检测到'文字与乡'特征"

    def test_cultural_consciousness_dimension(self, skill):
        """测试维度8：文化自觉（转化钥匙）"""
        text = """
        村民开始意识到本地传统文化的价值。年轻人觉得传统习俗土气，不愿意参与。
        老人担心很多传统技艺后继无人。村里人对外来文化更感兴趣，对本土文化不自信。
        有村民主动学习和传承传统手工艺。文化遗产项目让村民重新认识自己的文化。
        村民对本地历史和文化知之甚少。通过文化活动，村民的文化自豪感增强了。
        """

        result = skill.analyze(text)

        assert result.success
        assert 'cultural_consciousness' in result.dimensions
        matches = result.dimensions['cultural_consciousness']
        assert len(matches) > 0, "应该检测到'文化自觉'特征"

    def test_comprehensive_village_scenario(self, skill):
        """测试综合场景：一个典型的乡村调查报告"""
        text = """
        【某村田野调查报告节选】

        这是一个典型的北方乡村，村民世世代代生活在这里，大家都是熟人，
        抬头不见低头见。村里主要有张、李、王三大姓，各有祠堂，每年清明都要集体祭祖。

        村里的决策主要由几位德高望重的老人商议。村民说："老人的话管用，
        年轻人要听长辈的。"遇到纠纷，大家首先想到的是找村里的老人调解，
        很少有人去法院打官司，因为"打官司丢人"。

        村里办事讲究关系远近。一位村民告诉我们："办事要找对人，看你认识谁。
        亲戚朋友的事情优先帮，外人就另当别论了。"红白喜事时，能看出谁在村里人脉广。

        村里的妇女主要负责家务和照顾老人孩子，公共事务的决策很少有女性参与。
        几个大家族在村里很有影响力，土地和资源的分配也主要按家族来。

        在外打工的年轻人虽然常年在外，但过年一定要回来。村民说："金窝银窝不如自己的草窝，
        根在这里。"村后山上是各家族的祖坟，落叶归根的观念根深蒂固。

        村里通知事情主要靠大喇叭广播和口口相传。虽然现在也用微信群，
        但重要的事情还是要开村民大会，当面说清楚。老人们不识字，看不懂书面材料，
        更相信当面承诺。

        关于本地文化，年轻人大多觉得传统习俗土气，不愿意参与。老人们担心很多
        传统技艺后继无人。不过最近的文化遗产项目让一些村民重新认识了自己文化的价值，
        开始有人主动学习传统手工艺了。
        """

        result = skill.analyze(text)

        # 基本检查
        assert result.success
        assert result.total_matches > 10, f"综合场景应该有较多匹配，实际: {result.total_matches}"
        assert result.avg_confidence > 0.65, f"综合场景置信度应该较高，实际: {result.avg_confidence:.3f}"

        # 检查至少能识别出6个维度
        detected_dimensions = [dim_id for dim_id, matches in result.dimensions.items() if len(matches) > 0]
        assert len(detected_dimensions) >= 6, f"综合场景应该识别出至少6个维度，实际: {len(detected_dimensions)}"

        print(f"\n综合场景测试结果:")
        print(f"- 总匹配数: {result.total_matches}")
        print(f"- 平均置信度: {result.avg_confidence:.3f}")
        print(f"- 检测到的维度: {detected_dimensions}")

        for dim_id in detected_dimensions:
            matches = result.dimensions[dim_id]
            avg_sim = sum(m.similarity for m in matches) / len(matches) if matches else 0
            print(f"  * {dim_id}: {len(matches)} 个匹配, 平均相似度 {avg_sim:.3f}")

    def test_empty_text(self, skill):
        """测试空文本处理"""
        result = skill.analyze("")
        assert result.success  # 应该不报错
        assert result.total_matches == 0

    def test_unrelated_text(self, skill):
        """测试无关文本"""
        text = """
        今天天气很好，阳光明媚。我去超市买了一些水果和蔬菜。
        晚上打算看一部电影，然后早点休息。明天还要上班。
        """

        result = skill.analyze(text)
        assert result.success
        # 无关文本应该匹配数很少或为0
        assert result.total_matches < 3, "无关文本不应有太多匹配"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
