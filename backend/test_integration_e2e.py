#!/usr/bin/env python3
"""
端到端集成测试

测试完整的数据流：
Document Upload → Ingestion → Chunking → Vectorization → Knowledge Graph → Skills → Synthesis → Report
"""

import sys
sys.path.insert(0, 'src')

import logging
from app.database import SessionLocal, init_db
from app.models.project import Project, ProjectDocument
from app.models.pipeline_state import DocumentChunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_complete_pipeline():
    """测试完整的6-Agent v2 + Skills管道"""

    print("=" * 80)
    print("端到端集成测试：完整数据流")
    print("=" * 80)

    # 1. 准备测试数据
    db = SessionLocal()

    try:
        # 创建测试项目
        project = Project(
            name="Test Rural Research Project",
            description="测试乡村调研项目",
            status="active"
        )
        db.add(project)
        db.flush()

        project_id = project.id
        logger.info(f"✅ 创建测试项目 ID={project_id}")

        # 创建测试文档
        test_content = """
        【村庄调研记录】

        石桥村位于浙江省金华市，是一个有着800年历史的古村落。
        村中保存完好的明清建筑群，展现了浙江传统民居的特色。

        村民主要依靠茶叶种植和乡村旅游为生。近年来，在村委会带领下，
        全村发展生态茶园200亩，年产优质龙井茶5000斤。

        村里的祠堂是村民重要的精神寄托。每逢重大节日，村民都会在祠堂
        举行祭祀活动，延续了数百年的传统。这体现了乡土社会中礼治秩序的特点。

        在治理方面，村委会、党支部和老年协会共同管理村务，形成了三位一体
        的治理结构。重大决策都需要村民代表大会通过。

        经济上，村里正在探索"文化遗产+旅游+茶产业"的发展模式。
        去年接待游客3万人次，旅游收入达到500万元。
        """

        doc = ProjectDocument(
            project_id=project_id,
            title="石桥村调研记录",
            content=test_content,
            doc_type="interview",
            file_path="/test/shiqiao_village.txt"
        )
        db.add(doc)
        db.flush()

        doc_id = doc.id
        logger.info(f"✅ 创建测试文档 ID={doc_id}，长度={len(test_content)}字符")

        db.commit()

        # 2. 测试完整管道
        print("\n" + "=" * 80)
        print("开始执行完整管道")
        print("=" * 80)

        from app.services.workflows.v2_adapter import get_v2_adapter

        adapter = get_v2_adapter()

        # Step 1: Ingestion
        print("\n[Step 1] Ingestion Agent")
        print("-" * 40)
        ingestion_result = adapter.execute_v2_agent(
            agent_type='ingestion',
            input_data={'project_id': project_id},
            db_session=db
        )
        print(f"✅ Ingestion完成：{ingestion_result.output_data.get('document_count')}个文档")

        # Step 2: Chunking
        print("\n[Step 2] Chunking Agent")
        print("-" * 40)
        chunking_result = adapter.execute_v2_agent(
            agent_type='chunking',
            input_data={
                'project_id': project_id,
                'documents': ingestion_result.output_data.get('documents', [])
            },
            db_session=db
        )
        print(f"✅ Chunking完成：{chunking_result.output_data.get('chunk_count')}个chunks")

        # Step 3: Vectorization
        print("\n[Step 3] Vectorization Agent")
        print("-" * 40)
        vectorization_result = adapter.execute_v2_agent(
            agent_type='vectorization',
            input_data={
                'project_id': project_id,
                'stored_chunk_ids': chunking_result.output_data.get('stored_chunk_ids', [])
            },
            db_session=db
        )
        print(f"✅ Vectorization完成：{vectorization_result.output_data.get('vectorized_count')}个向量")

        # Step 4: Knowledge Graph + Skills
        print("\n[Step 4] Knowledge Agent + Skills Analysis")
        print("-" * 40)
        knowledge_result = adapter.execute_v2_agent(
            agent_type='knowledge',
            input_data={'project_id': project_id},
            db_session=db
        )
        print(f"✅ Knowledge Graph完成：{knowledge_result.output_data.get('entity_count')}个实体")

        skills_results = knowledge_result.output_data.get('skills_results')
        if skills_results:
            print(f"✅ Skills分析完成：{len(skills_results.get('skills_executed', []))}个Skills")
            for skill_id in skills_results.get('skills_executed', []):
                skill_data = skills_results.get('skills_results', {}).get(skill_id, {})
                print(f"   - {skill_id}: {skill_data.get('dimension_count', 0)}个维度")

        # Step 5: Synthesis
        print("\n[Step 5] Synthesis Agent")
        print("-" * 40)
        synthesis_result = adapter.execute_v2_agent(
            agent_type='synthesis',
            input_data={
                'project_id': project_id,
                'query': '生成石桥村综合分析报告'
            },
            db_session=db
        )
        print(f"✅ Synthesis完成：{synthesis_result.output_data.get('key_insights_count')}个洞察")

        # Step 6: Report
        print("\n[Step 6] Report Agent")
        print("-" * 40)
        report_result = adapter.execute_v2_agent(
            agent_type='report',
            input_data={
                'project_id': project_id,
                'synthesis_result_id': synthesis_result.output_data.get('synthesis_result_id'),
                'report_level': 'detailed'
            },
            db_session=db
        )
        print(f"✅ Report完成：类型={report_result.output_data.get('report_type')}")

        print("\n" + "=" * 80)
        print("✅ 完整管道测试成功！")
        print("=" * 80)

        # 清理测试数据
        print("\n清理测试数据...")
        db.query(DocumentChunk).filter(DocumentChunk.project_id == project_id).delete()
        db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).delete()
        db.query(Project).filter(Project.id == project_id).delete()
        db.commit()
        print("✅ 测试数据已清理")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    test_complete_pipeline()
