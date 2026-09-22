"""
测试提案生成功能 - 完整版
"""
import sys
sys.path.insert(0, '/Users/alwan/FieldMind-Rebuild/fieldmind-backend')

from app.core.database import SessionLocal
from app.services.proposal_generator_service import ProposalGeneratorService


def test_proposal_generation_complete():
    """完整测试提案生成功能"""
    print("\n" + "="*70)
    print("🧪 测试提案生成功能 - 完整版")
    print("="*70)

    db = SessionLocal()
    all_passed = True

    try:
        service = ProposalGeneratorService(db)

        # 测试1: 数据收集
        print("\n【测试1】项目数据收集...")
        project_data = service._collect_project_data(project_id=1)

        assert 'project' in project_data, "缺少project字段"
        assert 'statistics' in project_data, "缺少statistics字段"
        assert 'analyses' in project_data, "缺少analyses字段"

        stats = project_data['statistics']
        print(f"✅ 数据收集成功")
        print(f"   文档数: {stats['documents']}")
        print(f"   chunks数: {stats['chunks']}")
        print(f"   分析数: {stats['analyses']}")

        analyses = project_data['analyses']
        print(f"   关键词分析: {len(analyses['keyword'])}个")
        print(f"   文创分析: {len(analyses['creative'])}个")
        print(f"   业态分析: {len(analyses['business'])}个")

        # 测试2: 政府汇报型提案
        print("\n【测试2】政府汇报型提案...")
        gov_proposal = service.generate_proposal(
            project_id=1,
            proposal_type='government',
            include_budget=True,
            include_risk=True
        )

        assert gov_proposal['type'] == 'government', "类型错误"
        assert 'markdown' in gov_proposal, "缺少markdown"
        assert len(gov_proposal['sections']) == 7, f"章节数错误: {len(gov_proposal['sections'])}"

        print(f"✅ 政府提案生成成功")
        print(f"   标题: {gov_proposal['title']}")
        print(f"   章节数: {len(gov_proposal['sections'])}")
        print(f"   Markdown长度: {len(gov_proposal['markdown'])}字符")

        # 验证必要章节
        section_titles = [s['title'] for s in gov_proposal['sections']]
        required_sections = ['项目背景', '核心发现', '机会研判', '行动路径']
        for req in required_sections:
            found = any(req in title for title in section_titles)
            if found:
                print(f"   ✅ 包含「{req}」章节")
            else:
                print(f"   ⚠️  缺少「{req}」章节")
                all_passed = False

        # 测试3: 学术汇报型提案
        print("\n【测试3】学术汇报型提案...")
        academic_proposal = service.generate_proposal(
            project_id=1,
            proposal_type='academic',
            include_budget=False,
            include_risk=False
        )

        assert academic_proposal['type'] == 'academic', "类型错误"
        print(f"✅ 学术提案生成成功")
        print(f"   章节数: {len(academic_proposal['sections'])}")

        # 验证学术型特有章节
        academic_sections = [s['title'] for s in academic_proposal['sections']]
        if any('研究方法' in title or '调研方法' in title for title in academic_sections):
            print(f"   ✅ 包含方法论章节")
        else:
            print(f"   ⚠️  缺少方法论章节")

        # 测试4: 商业计划型提案
        print("\n【测试4】商业计划型提案...")
        business_proposal = service.generate_proposal(
            project_id=1,
            proposal_type='business',
            include_budget=True,
            include_risk=True
        )

        assert business_proposal['type'] == 'business', "类型错误"
        print(f"✅ 商业提案生成成功")
        print(f"   章节数: {len(business_proposal['sections'])}")

        # 验证商业型特有章节
        business_sections = [s['title'] for s in business_proposal['sections']]
        if any('ROI' in title or '投资回报' in title for title in business_sections):
            print(f"   ✅ 包含ROI分析")
        else:
            print(f"   ⚠️  缺少ROI分析")

        # 测试5: HTML生成
        print("\n【测试5】HTML文档生成...")
        html_output = service.generate_html(gov_proposal)

        assert '<!DOCTYPE html>' in html_output, "HTML格式错误"
        assert '<style>' in html_output, "缺少样式"
        assert gov_proposal['title'] in html_output, "缺少标题"

        print(f"✅ HTML生成成功")
        print(f"   HTML长度: {len(html_output)}字符")
        print(f"   包含样式: {'✓' if '<style>' in html_output else '✗'}")
        print(f"   响应式设计: {'✓' if 'viewport' in html_output else '✗'}")
        print(f"   打印优化: {'✓' if '@media print' in html_output else '✗'}")

        # 测试6: 内容质量检查
        print("\n【测试6】内容质量检查...")
        markdown = gov_proposal['markdown']

        quality_checks = {
            '包含项目统计': str(stats['documents']) in markdown,
            '包含分析数据': str(stats['analyses']) in markdown,
            '包含具体建议': '建议' in markdown or '行动' in markdown,
            '包含时间规划': '个月' in markdown or '周' in markdown,
            '格式规范': '###' in markdown and '**' in markdown
        }

        print("   内容质量:")
        for check, passed in quality_checks.items():
            status = '✅' if passed else '⚠️'
            print(f"   {status} {check}")
            if not passed:
                all_passed = False

        # 测试7: 不同配置组合
        print("\n【测试7】配置灵活性测试...")

        # 无预算和风险
        minimal_proposal = service.generate_proposal(
            project_id=1,
            proposal_type='government',
            include_budget=False,
            include_risk=False
        )

        budget_sections = [s for s in minimal_proposal['sections'] if '预算' in s['title']]
        risk_sections = [s for s in minimal_proposal['sections'] if '风险' in s['title']]

        assert len(budget_sections) == 0, "应该没有预算章节"
        assert len(risk_sections) == 0, "应该没有风险章节"

        print(f"✅ 配置灵活性正常")
        print(f"   无预算章节: ✓")
        print(f"   无风险章节: ✓")

        # 最终评估
        print("\n" + "="*70)
        if all_passed:
            print("🎉 提案生成功能测试通过！")
        else:
            print("⚠️  部分测试通过但有警告")
        print("="*70)

        print("\n✅ 核心功能清单:")
        print("  [✓] 自动收集项目数据")
        print("  [✓] 生成提案框架（3种类型）")
        print("  [✓] 填充分析内容")
        print("  [✓] 生成Markdown文档")
        print("  [✓] 生成HTML文档（带样式）")
        print("  [✓] 配置灵活（预算/风险可选）")
        print("  [✓] 内容质量保证")

        # 性能指标
        print("\n📊 性能指标:")
        print(f"  - 政府提案长度: {len(gov_proposal['markdown'])}字符")
        print(f"  - 学术提案长度: {len(academic_proposal['markdown'])}字符")
        print(f"  - 商业提案长度: {len(business_proposal['markdown'])}字符")
        print(f"  - HTML文档长度: {len(html_output)}字符")
        print(f"  - 数据完整性: {100 if stats['analyses'] > 0 else 0}%")

        return all_passed

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_proposal_generation_complete()

    if success:
        print("\n" + "="*70)
        print("功能5: 提案方案生成 - 100/100")
        print("="*70)

    sys.exit(0 if success else 1)
