#!/usr/bin/env python3
"""
使用音寨布依族村真实数据测试 Skills 集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.services.report_generation.data_driven_report_builder import DataDrivenReportBuilder
from app.services.report_generation.report_content_engine import ReportContentEngine

# 数据库连接
DATABASE_URL = "sqlite:///backend/src/data/fieldmind.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_yinzhai_project():
    """创建音寨项目并导入数据"""
    print("\n" + "="*80)
    print("步骤 1: 创建音寨布依族村项目")
    print("="*80)

    session = SessionLocal()
    try:
        # 检查项目是否已存在
        result = session.execute(
            text("SELECT id FROM projects WHERE name = '音寨布依族村'")
        ).fetchone()

        if result:
            project_id = result[0]
            print(f"✓ 项目已存在，ID: {project_id}")
            return project_id

        # 创建新项目
        session.execute(text("""
            INSERT INTO projects (name, description, owner_id, is_archived, status, created_at, updated_at)
            VALUES ('音寨布依族村',
                    '贵州音寨布依族村文化全景深度报告 - 整村运营前期田野调查',
                    'test_user',
                    0,
                    'active',
                    datetime('now'),
                    datetime('now'))
        """))
        session.commit()

        # 获取项目ID
        result = session.execute(
            text("SELECT id FROM projects WHERE name = '音寨布依族村'")
        ).fetchone()
        project_id = result[0]

        print(f"✓ 项目创建成功，ID: {project_id}")
        return project_id

    finally:
        session.close()

def import_yinzhai_document(project_id):
    """导入音寨报告文档到项目"""
    print("\n" + "="*80)
    print("步骤 2: 导入音寨报告文档")
    print("="*80)

    session = SessionLocal()
    try:
        # 检查文档是否已存在
        result = session.execute(
            text(f"SELECT id FROM documents WHERE project_id = {project_id}")
        ).fetchone()

        if result:
            print(f"✓ 文档已存在")
            return

        # 读取文本文件
        with open('/Users/alwan/FieldMind/test_data_yinzhai.txt', 'r', encoding='utf-8') as f:
            content = f.read()

        # 插入文档记录（使用 'DOCUMENT' 类型大写）
        doc_id = f"doc_yinzhai_{project_id}"
        session.execute(text(f"""
            INSERT INTO documents
            (id, project_id, name, type, mime_type, storage_path, status, created_at, updated_at)
            VALUES
            ('{doc_id}', {project_id}, '音寨布依族村文化全景深度报告.txt',
             'DOCUMENT', 'text/plain', '/Users/alwan/FieldMind/test_data_yinzhai.txt',
             'COMPLETED', datetime('now'), datetime('now'))
        """))

        print(f"✓ 文档导入成功")
        print(f"  - 文档ID: {doc_id}")
        print(f"  - 内容长度: {len(content):,} 字符")

        session.commit()

    finally:
        session.close()

def test_material_extraction(project_id):
    """测试素材提取"""
    print("\n" + "="*80)
    print("步骤 3: 提取报告素材")
    print("="*80)

    session = SessionLocal()
    try:
        builder = DataDrivenReportBuilder(db=session)
        material = builder.extract_report_material(project_id)

        print(f"\n✓ 素材提取完成:")
        print(f"  - 主关键词数量: {len(material.main_keywords)}")
        print(f"  - 关键词社群: {len(material.keyword_communities)}")
        print(f"  - 核心实体: {len(material.core_entities)}")
        print(f"  - 时间线事件: {len(material.timeline)}")
        print(f"  - 引用池大小: {len(material.citation_pool)}")

        if material.main_keywords:
            print(f"\n  前10个主关键词:")
            keywords_list = list(material.main_keywords)[:10] if isinstance(material.main_keywords, dict) else material.main_keywords[:10]
            for kw in keywords_list:
                print(f"    - {kw}")

        if material.core_entities:
            print(f"\n  前10个核心实体:")
            entities_list = list(material.core_entities)[:10] if isinstance(material.core_entities, dict) else material.core_entities[:10]
            for entity in entities_list:
                print(f"    - {entity}")

        return material
    finally:
        session.close()

def test_outline_generation(material, report_level):
    """测试大纲生成"""
    level_names = {1: "田野调查报告", 2: "学术分析报告", 3: "商业分析报告"}

    print("\n" + "="*80)
    print(f"步骤 4: 生成 Level {report_level} {level_names[report_level]}大纲")
    print("="*80)

    session = SessionLocal()
    try:
        builder = DataDrivenReportBuilder(db=session)
        outline = builder.generate_dynamic_outline(material, report_level=report_level)

        print(f"\n✓ 大纲生成完成，共 {len(outline)} 章:")
        for i, section in enumerate(outline, 1):
            title = section.get('title', '未命名章节')
            print(f"  {i}. {title}")

        return outline
    finally:
        session.close()

def test_content_generation(material, outline, report_level):
    """测试内容生成"""
    level_names = {1: "田野调查", 2: "学术分析", 3: "商业分析"}

    print("\n" + "="*80)
    print(f"步骤 5: 生成 Level {report_level} {level_names[report_level]} 章节内容")
    print("="*80)

    engine = ReportContentEngine()

    # 测试前3章
    test_chapters = min(3, len(outline))
    results = []

    for i in range(test_chapters):
        section = outline[i]
        chapter_title = section.get('title', f'第{i+1}章')

        print(f"\n正在生成: {chapter_title}")

        try:
            filled_section = engine.fill_section(
                section_outline=section,
                material=material,
                report_level=report_level
            )

            content = filled_section.get('content', '')
            citations = filled_section.get('citations', [])
            word_count = len(content)

            results.append({
                'title': chapter_title,
                'success': True,
                'word_count': word_count,
                'citation_count': len(citations),
                'content_preview': content[:300] + '...' if len(content) > 300 else content
            })

            print(f"  ✓ 成功 - {word_count} 字, {len(citations)} 个引用")

        except Exception as e:
            results.append({
                'title': chapter_title,
                'success': False,
                'error': str(e)
            })
            print(f"  ✗ 失败 - {str(e)}")

    return results

def print_test_summary(level, results):
    """打印测试总结"""
    level_names = {1: "田野调查报告", 2: "学术分析报告", 3: "商业分析报告"}

    print("\n" + "="*80)
    print(f"Level {level} {level_names[level]} 测试结果")
    print("="*80)

    success_count = sum(1 for r in results if r['success'])
    total_words = sum(r.get('word_count', 0) for r in results if r['success'])
    avg_words = total_words / success_count if success_count > 0 else 0

    print(f"\n成功生成: {success_count}/{len(results)} 章")
    print(f"总字数: {total_words:,} 字")
    print(f"平均字数/章: {avg_words:.0f} 字")

    print("\n详细结果:")
    for i, result in enumerate(results, 1):
        if result['success']:
            print(f"\n{i}. {result['title']}: ✓ 成功")
            print(f"   字数: {result['word_count']:,}")
            print(f"   引用: {result['citation_count']}")
            print(f"   内容预览:")
            print(f"   {result['content_preview'][:200]}")
        else:
            print(f"\n{i}. {result['title']}: ✗ 失败")
            print(f"   错误: {result['error']}")

def main():
    """主测试流程"""
    print("\n" + "#"*80)
    print("# 音寨布依族村 - Skills 真实数据测试")
    print("#"*80)

    # 1. 创建项目
    project_id = create_yinzhai_project()

    # 2. 导入文档
    import_yinzhai_document(project_id)

    # 3. 提取素材
    material = test_material_extraction(project_id)

    # 4-5. 测试 Level 1 田野调查报告
    print("\n\n" + "#"*80)
    print("# 测试 Level 1: 田野调查报告（大地遗产 Skill）")
    print("#"*80)

    outline_l1 = test_outline_generation(material, report_level=1)
    results_l1 = test_content_generation(material, outline_l1, report_level=1)
    print_test_summary(1, results_l1)

    # 6-7. 测试 Level 3 商业分析报告
    print("\n\n" + "#"*80)
    print("# 测试 Level 3: 商业分析报告（乡遗商途 Skill）")
    print("#"*80)

    outline_l3 = test_outline_generation(material, report_level=3)
    results_l3 = test_content_generation(material, outline_l3, report_level=3)
    print_test_summary(3, results_l3)

    # 总结
    print("\n\n" + "#"*80)
    print("# 测试完成总结")
    print("#"*80)

    l1_success_rate = sum(1 for r in results_l1 if r['success']) / len(results_l1) * 100
    l3_success_rate = sum(1 for r in results_l3 if r['success']) / len(results_l3) * 100

    print(f"\nLevel 1 田野调查: {l1_success_rate:.0f}% 成功率")
    print(f"Level 3 商业分析: {l3_success_rate:.0f}% 成功率")

    if l1_success_rate >= 80 and l3_success_rate >= 80:
        print("\n✅ 测试通过 - Skills 集成成功且内容生成正常")
    else:
        print("\n⚠️  测试部分通过 - 需要优化内容生成质量")

if __name__ == "__main__":
    main()
