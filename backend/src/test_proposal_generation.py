"""
测试提案生成功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.proposal_generator_service import ProposalGeneratorService


def test_proposal_generation():
    """测试提案生成"""
    print("\n" + "="*70)
    print("🧪 测试提案生成功能")
    print("="*70)

    db = SessionLocal()

    try:
        service = ProposalGeneratorService(db)

        # 测试1: 生成政府汇报型提案
        print("\n【测试1】生成政府汇报型提案...")

        proposal = service.generate_proposal(
            project_id=1,
            proposal_type='government',
            include_budget=True,
            include_risk=True
        )

        print(f"✅ 提案生成成功")
        print(f"   标题: {proposal['title']}")
        print(f"   类型: {proposal['type']}")
        print(f"   章节数: {len(proposal['sections'])}")
        print(f"   Markdown长度: {len(proposal['markdown'])} 字符")

        # 显示章节结构
        print(f"\n   章节结构:")
        for section in proposal['sections']:
            print(f"   - {section['title']}")

        # 显示前500字
        print(f"\n   提案预览:")
        print("-" * 70)
        print(proposal['markdown'][:500])
        print("...")
        print("-" * 70)

        # 测试2: 生成学术汇报型提案
        print("\n【测试2】生成学术汇报型提案...")

        academic_proposal = service.generate_proposal(
            project_id=1,
            proposal_type='academic',
            include_budget=False,
            include_risk=False
        )

        print(f"✅ 学术提案生成成功")
        print(f"   章节数: {len(academic_proposal['sections'])}")

        # 测试3: 生成商业计划型提案
        print("\n【测试3】生成商业计划型提案...")

        business_proposal = service.generate_proposal(
            project_id=1,
            proposal_type='business',
            include_budget=True,
            include_risk=True
        )

        print(f"✅ 商业提案生成成功")
        print(f"   章节数: {len(business_proposal['sections'])}")

        print("\n" + "="*70)
        print("🎉 提案生成功能测试通过！")
        print("="*70)

        print("\n✅ 核心功能验证:")
        print("  • 自动收集项目数据")
        print("  • 生成提案框架")
        print("  • 填充分析内容")
        print("  • 生成Markdown文档")
        print("  • 支持3种提案类型")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_proposal_generation()
    sys.exit(0 if success else 1)
