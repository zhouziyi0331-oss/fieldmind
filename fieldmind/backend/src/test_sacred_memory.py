"""
神圣记忆Skill测试套件
测试基于景军《神圣记忆》理论框架的社会记忆分析功能
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from app.services.skills.sacred_memory import SacredMemorySkill


class TestSacredMemorySkill:
    """神圣记忆Skill测试类"""

    @pytest.fixture
    def skill(self):
        """创建SacredMemorySkill实例"""
        return SacredMemorySkill()

    def test_skill_initialization(self, skill):
        """测试Skill初始化"""
        assert skill.skill_id == "sacred_memory"
        assert skill.skill_name == "神圣记忆理论分析（社会记忆6维度）"
        assert len(skill.dimensions) == 6

    def test_dimensions_count(self, skill):
        """测试维度数量"""
        assert len(skill.dimensions) == 6, f"应有6个维度，实际有{len(skill.dimensions)}个"

    def test_dimension_ids(self, skill):
        """测试维度ID正确性"""
        expected_dims = {
            'historical_memory',
            'trauma_memory',
            'ritual_memory',
            'genealogy_memory',
            'symbol_memory',
            'identity_memory'
        }
        actual_dims = set(skill.dimensions.keys())
        assert actual_dims == expected_dims, f"维度ID不匹配: {actual_dims} vs {expected_dims}"

    def test_dimension_structure(self, skill):
        """测试每个维度的结构完整性"""
        for dim_id, dimension in skill.dimensions.items():
            assert dimension.dimension_id == dim_id
            assert dimension.dimension_name is not None
            assert dimension.description is not None
            assert len(dimension.keywords) > 0
            assert len(dimension.example_sentences) > 0

    def test_historical_memory_dimension(self, skill):
        """测试历史记忆维度"""
        dim = skill.dimensions['historical_memory']
        assert dim.dimension_name == '历史记忆'
        assert '建村' in dim.keywords
        assert '祖先' in dim.keywords

    def test_trauma_memory_dimension(self, skill):
        """测试创伤/磨难记忆维度"""
        dim = skill.dimensions['trauma_memory']
        assert dim.dimension_name == '创伤/磨难记忆'
        assert '灾难' in dim.keywords
        assert '磨难' in dim.keywords

    def test_ritual_memory_dimension(self, skill):
        """测试仪式记忆维度"""
        dim = skill.dimensions['ritual_memory']
        assert dim.dimension_name == '仪式记忆'
        assert '仪式' in dim.keywords
        assert '祭祀' in dim.keywords

    def test_genealogy_memory_dimension(self, skill):
        """测试谱系记忆维度"""
        dim = skill.dimensions['genealogy_memory']
        assert dim.dimension_name == '谱系记忆'
        assert '家谱' in dim.keywords
        assert '族谱' in dim.keywords

    def test_symbol_memory_dimension(self, skill):
        """测试文化象征记忆维度"""
        dim = skill.dimensions['symbol_memory']
        assert dim.dimension_name == '文化象征记忆'
        assert '庙宇' in dim.keywords
        assert '祠堂' in dim.keywords

    def test_identity_memory_dimension(self, skill):
        """测试身份认同记忆维度"""
        dim = skill.dimensions['identity_memory']
        assert dim.dimension_name == '身份认同记忆'
        assert '认同' in dim.keywords
        assert '我们' in dim.keywords

    def test_analyze_comprehensive_text(self, skill):
        """测试综合文本分析"""
        # 构建包含所有6个维度特征的综合文本
        test_text = """
        【历史记忆】
        我们村的历史可以追溯到明朝，据老人讲，开基祖是从山西洪洞县大槐树下迁来的。
        村里的族谱详细记载了建村的传说，祠堂里还保存着先祖留下的匾额。
        当年我们村出过进士，这是全村人引以为豪的历史。

        【创伤/磨难记忆】
        三年困难时期村里饿死了很多人，老人们不愿意多谈那段苦难的日子。
        文革时期祠堂被毁，很多珍贵的文物丢失了，这是村里最大的损失。
        有些痛苦的记忆，老人们至今不愿提起，保持沉默。

        【仪式记忆】
        每年清明节，全村人都会聚集在祠堂祭祖，这个传统从未中断。
        正月十五的庙会特别热闹，舞龙舞狮的传统已经传承了几百年。
        婚礼必须按照传统仪式进行，长辈们对这些礼仪非常讲究。
        村里的祭祀仪式有严格的程序，体现了对祖先的敬畏。

        【谱系记忆】
        我们家的族谱记录了二十代祖先的名字和事迹，是家族最重要的传家宝。
        村里最近在组织修订族谱，把外出的子孙都记录进去。
        每个人的名字都按辈分字辈排列，这样可以一眼看出辈分高低。
        通过族谱，我们还找到了很多远房亲戚，认祖归宗的活动很频繁。

        【文化象征记忆】
        村口那棵三百年的大榕树是我们村的标志，老人说树有神灵保护。
        祠堂是全村人的精神寄托，里面供奉着历代祖先的牌位。
        村里的古庙承载着几代人的记忆，是村民信仰的中心。
        那座牌坊见证了家族的荣耀，是我们村最重要的文物。

        【身份认同记忆】
        我们村的人特别团结，外人很难真正融入进来。
        村民对本村的文化传统非常自豪，这是我们的根。
        我们的习俗和邻村不一样，这是我们的特色。
        通过文化活动，大家的归属感和认同感越来越强。
        """

        result = skill.analyze(test_text)

        # 验证分析结果
        assert result.success is True
        assert result.total_matches > 0
        assert result.avg_confidence > 0

        # 验证每个维度都被检测到
        detected_dimensions = {dim_id for dim_id, matches in result.dimensions.items() if len(matches) > 0}
        print(f"\n检测到的维度: {detected_dimensions}")
        print(f"总匹配数: {result.total_matches}")
        print(f"平均置信度: {result.avg_confidence:.3f}")

        # 打印每个维度的匹配情况
        for dim_id, matches in result.dimensions.items():
            if len(matches) > 0:
                avg_sim = sum(m.similarity for m in matches) / len(matches)
                print(f"  {skill.dimensions[dim_id].dimension_name}: {len(matches)} 个匹配, 平均相似度 {avg_sim:.3f}")

        # 期望至少检测到4个维度（宽松要求）
        assert len(detected_dimensions) >= 4, f"应至少检测到4个维度，实际检测到{len(detected_dimensions)}个"

    def test_analyze_empty_text(self, skill):
        """测试空文本分析"""
        result = skill.analyze("")
        assert result.success is True
        assert result.total_matches == 0

    def test_analyze_irrelevant_text(self, skill):
        """测试无关文本分析"""
        irrelevant_text = "今天天气很好，阳光明媚。我喜欢吃苹果和香蕉。"
        result = skill.analyze(irrelevant_text)
        assert result.success is True
        # 无关文本应该很少或没有匹配
        assert result.total_matches < 5


def test_backward_compatible_function():
    """测试向后兼容的函数接口"""
    from app.services.skills.sacred_memory import analyze

    test_text = "我们村的族谱记录了祖先的历史，每年清明都要祭祖。"
    result = analyze(test_text)

    assert result is not None
    assert 'skill_name' in result
    assert 'total_matches' in result
    assert 'avg_confidence' in result
    assert 'dimensions' in result


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '-s'])
