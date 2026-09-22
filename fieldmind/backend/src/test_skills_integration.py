"""
测试Skills集成到文档处理流程
"""

import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock
import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app.services.background_tasks import execute_all_skills
from app.models.project import Project


def test_execute_all_skills_basic():
    """测试基本的Skills批量执行"""
    # 准备测试文本（包含多个维度的内容）
    test_content = """
    我们村是明朝时从山西迁来的，据老人讲开基祖是跟随朱元璋打天下的功臣。
    村里每年正月十五都要举行盛大的庙会，祭拜祖先，这个传统已经延续了几百年。
    族谱记载了我们家族十五代的传承，从开基祖到现在的子孙后代。

    村里人之间的关系很密切，大家都是熟人，办事情讲人情不讲法律。
    土地对我们来说非常重要，祖祖辈辈都靠这片土地生活。

    这里有丰富的文化遗产，包括古建筑、传统手工艺、民间故事等。
    我们正在考虑将这些文化资源开发成旅游产品，吸引游客。
    需要进行市场调研，评估商业可行性。
    """

    # Mock数据库session
    mock_db = Mock(spec=Session)

    # Mock项目（默认启用所有Skills）
    mock_project = Mock(spec=Project)
    mock_project.id = 1
    mock_project.settings = None  # 使用默认配置

    mock_db.query.return_value.filter.return_value.first.return_value = mock_project

    # 执行Skills分析
    result = execute_all_skills(
        content=test_content,
        document_id=1,
        project_id=1,
        db=mock_db
    )

    # 验证结果结构
    assert 'results' in result
    assert 'summary' in result

    summary = result['summary']
    assert 'total' in summary
    assert 'success' in summary
    assert 'error' in summary

    # 验证执行了6个Skills
    assert summary['total'] == 6

    # 验证所有6个Skills的结果都存在
    results = result['results']
    expected_skills = [
        'heritage_dadi',
        'business_feasibility',
        'multi_village_sop',
        'literature_market_research',
        'xiangtu_china',
        'sacred_memory'
    ]

    for skill_id in expected_skills:
        assert skill_id in results, f"Skill {skill_id} 结果缺失"
        skill_result = results[skill_id]

        # 如果成功，应该有dimensions字段
        if skill_result.get('success'):
            assert 'dimensions' in skill_result
            assert 'metadata' in skill_result
            assert 'elapsed_time' in skill_result
            print(f"✅ {skill_id}: {len(skill_result['dimensions'])} 维度检测到")
        else:
            # 失败的话应该有error字段
            assert 'error' in skill_result
            print(f"❌ {skill_id}: {skill_result['error']}")

    print(f"\n📊 总结: {summary['success']}/{summary['total']} 个Skills成功")


def test_execute_all_skills_with_enabled_subset():
    """测试只启用部分Skills"""
    test_content = """
    我们村是明朝时从山西迁来的，祖祖辈辈靠土地生活。
    村里人之间的关系很密切，这是典型的差序格局。
    """

    # Mock数据库session
    mock_db = Mock(spec=Session)

    # Mock项目（只启用2个Skills）
    mock_project = Mock(spec=Project)
    mock_project.id = 1
    mock_project.settings = {
        'enabled_skills': ['xiangtu_china', 'sacred_memory']
    }

    mock_db.query.return_value.filter.return_value.first.return_value = mock_project

    # 执行Skills分析
    result = execute_all_skills(
        content=test_content,
        document_id=1,
        project_id=1,
        db=mock_db
    )

    # 验证只执行了2个Skills
    assert result['summary']['total'] == 2
    assert 'xiangtu_china' in result['results']
    assert 'sacred_memory' in result['results']
    assert 'heritage_dadi' not in result['results']

    print(f"✅ 部分启用测试通过: 只执行了配置的2个Skills")


def test_execute_all_skills_empty_content():
    """测试空内容"""
    # Mock数据库session
    mock_db = Mock(spec=Session)

    mock_project = Mock(spec=Project)
    mock_project.id = 1
    mock_project.settings = {
        'enabled_skills': ['xiangtu_china']
    }

    mock_db.query.return_value.filter.return_value.first.return_value = mock_project

    # 执行Skills分析（空内容）
    result = execute_all_skills(
        content="",
        document_id=1,
        project_id=1,
        db=mock_db
    )

    # 验证结果
    assert result['summary']['total'] == 1

    # xiangtu_china应该成功执行，但可能不会检测到匹配
    xiangtu_result = result['results']['xiangtu_china']
    assert xiangtu_result['success'] == True
    # 空内容时total_matches应该为0
    assert xiangtu_result['total_matches'] == 0

    print(f"✅ 空内容测试通过")


if __name__ == '__main__':
    print("=" * 60)
    print("Skills集成测试")
    print("=" * 60)

    print("\n测试1: 基本批量执行（所有6个Skills）")
    print("-" * 60)
    test_execute_all_skills_basic()

    print("\n测试2: 部分启用Skills")
    print("-" * 60)
    test_execute_all_skills_with_enabled_subset()

    print("\n测试3: 空内容处理")
    print("-" * 60)
    test_execute_all_skills_empty_content()

    print("\n" + "=" * 60)
    print("✅ 所有集成测试通过！")
    print("=" * 60)
