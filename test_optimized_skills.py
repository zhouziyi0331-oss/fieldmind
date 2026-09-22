#!/usr/bin/env python3
"""
测试优化后的 Skills 内容生成质量
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend" / "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.skills.field_investigation_skill import FieldInvestigationSkill

# 数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def test_optimized_skills():
    """测试优化后的 Skills"""
    print("=" * 80)
    print("测试优化后的 Skills 内容生成")
    print("=" * 80)

    session = SessionLocal()

    try:
        # 项目ID（音寨布依族村）
        project_id = 2  # 使用数字ID而不是字符串

        # 1. 提取 ReportMaterial
        print("\n[步骤 1] 提取 ReportMaterial...")
        builder = DataDrivenReportBuilder(session)
        material_obj = builder.extract_report_material(project_id)

        print(f"✓ 主关键词数量: {len(material_obj.main_keywords)}")
        print(f"✓ 引用池大小: {len(material_obj.citation_pool)}")
        print(f"✓ 时间线事件: {len(material_obj.timeline)}")
        print(f"✓ 核心实体: {sum(len(entities) for entities in material_obj.core_entities.values())}")

        # 转换为字典格式供 Skills 使用
        material = {
            'main_keywords': material_obj.main_keywords,
            'keyword_communities': material_obj.keyword_communities,
            'keyword_relations': material_obj.keyword_relations,
            'core_entities': [
                {'entity_type': etype, 'entity': e.get('entity', '')}
                for etype, entities in material_obj.core_entities.items()
                for e in entities
            ],
            'entity_relations': material_obj.entity_relations,
            'timeline': material_obj.timeline,
            'citation_pool': material_obj.citation_pool,
            'project_statistics': {
                'total_chunks': material_obj.total_chunks,
                'total_words': material_obj.total_words,
                'total_documents': material_obj.total_documents
            }
        }

        # 2. 测试 Skills 生成内容
        print("\n[步骤 2] 使用优化后的 Skills 生成内容...")
        skill = FieldInvestigationSkill()

        chapters = [
            "文化遗产资源盘点",
            "内容挖掘与价值提炼",
            "综合田野发现"
        ]

        results = {}

        for chapter_title in chapters:
            print(f"\n生成章节: {chapter_title}")
            content = skill.generate_field_report_content(material, chapter_title)

            word_count = len(content)
            line_count = content.count('\n')

            results[chapter_title] = {
                'content': content,
                'word_count': word_count,
                'line_count': line_count
            }

            print(f"  字数: {word_count}")
            print(f"  行数: {line_count}")

            # 显示前500字预览
            print(f"\n  内容预览:")
            print("  " + "-" * 70)
            preview = content[:500].replace('\n', '\n  ')
            print(f"  {preview}")
            if len(content) > 500:
                print(f"  ... (还有 {len(content) - 500} 字)")
            print("  " + "-" * 70)

        # 3. 统计对比
        print("\n" + "=" * 80)
        print("优化效果对比")
        print("=" * 80)

        total_words = sum(r['word_count'] for r in results.values())
        avg_words = total_words / len(results)

        print(f"\n总字数: {total_words}")
        print(f"平均字数/章: {avg_words:.0f}")
        print(f"\n各章节详情:")
        for title, stats in results.items():
            print(f"  {title}: {stats['word_count']} 字")

        print("\n对比基准:")
        print("  优化前: 169-458 字/章")
        print("  目标: 1000+ 字/章")
        print(f"  实际: {avg_words:.0f} 字/章")

        if avg_words >= 1000:
            print("\n✓ 达到目标！内容质量显著提升")
        elif avg_words >= 600:
            print("\n△ 有改善，但未达到最优目标")
        else:
            print("\n✗ 仍需进一步优化")

        # 4. 保存完整报告到文件
        output_file = project_root / "test_output_optimized.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 音寨布依族村田野调查报告（优化版）\n\n")
            f.write(f"生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            for title, stats in results.items():
                f.write(f"## {title}\n\n")
                f.write(stats['content'])
                f.write(f"\n\n*（字数: {stats['word_count']}）*\n\n")
                f.write("---\n\n")

        print(f"\n完整报告已保存到: {output_file}")

    finally:
        session.close()

if __name__ == "__main__":
    test_optimized_skills()
