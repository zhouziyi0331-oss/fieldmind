"""
测试完整数据流追溯链

验证：Document → Chunk (数据库) → Entity (数据库) → Knowledge → Synthesis → Report
"""

import sys
import os

# 添加项目根目录到路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_flow():
    """测试完整数据流"""

    # 延迟导入避免循环依赖
    from app.models.project import Project, ProjectDocument
    from app.agents.coordinator import AgentCoordinator, PipelineStage

    # 创建数据库会话（直接使用数据库路径）
    db_path = "/Users/alwan/FieldMind-Rebuild/fieldmind-backend/fieldmind.db"
    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 1. 创建测试项目（需要owner_id，使用1作为测试用户）
        project = Project(
            name="数据流测试项目",
            description="测试Document→Chunk→Entity的完整追溯链",
            owner_id=1  # 假设存在ID为1的用户
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info(f"✅ 创建项目: {project.name} (ID: {project.id})")

        # 2. 创建测试文档
        doc = ProjectDocument(
            project_id=project.id,
            filename="test_field_report.txt",
            original_filename="测试田野调查文档.txt",
            file_path="/tmp/test_field_report.txt",
            file_type="text",
            text_content="""
            贵州省黔东南苗族侗族自治州的苗族银饰锻制技艺是国家级非物质文化遗产。
            该技艺传承人张师傅在雷山县经营银饰作坊已有30年历史。
            银饰制作工序包括：熔银、拉丝、编织、焊接、錾刻等12道工序。
            联合国教科文组织于2006年将其列入人类非物质文化遗产代表作名录。
            当地政府提供了资金支持和培训项目，帮助年轻人学习传统技艺。
            """
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"✅ 创建文档: {doc.filename} (ID: {doc.id})")

        # 3. 运行6Agent Pipeline（前3个阶段）
        coordinator = AgentCoordinator()

        logger.info("\n" + "="*60)
        logger.info("开始运行Pipeline：Document → Chunk → Analysis")
        logger.info("="*60)

        result = coordinator.process_project(
            project_id=project.id,
            db_session=db,
            custom_stages=[
                PipelineStage.DOCUMENT_LOAD,
                PipelineStage.CHUNK,
                PipelineStage.ANALYSIS
            ]
        )

        if result.success:
            logger.info(f"\n✅ Pipeline执行成功！")
            logger.info(f"执行阶段数: {len(result.completed_stages)}")
            logger.info(f"完成阶段: {[s.value for s in result.completed_stages]}")
        else:
            logger.error(f"\n❌ Pipeline执行失败: {result.error_message}")
            return

        # 4. 验证数据流追溯链
        logger.info("\n" + "="*60)
        logger.info("验证数据流追溯链")
        logger.info("="*60)

        # 检查document_chunks表
        chunks_count = db.execute(text("""
            SELECT COUNT(*) FROM document_chunks
            WHERE document_id = :doc_id
        """), {"doc_id": doc.id}).scalar()
        logger.info(f"\n✅ document_chunks表: {chunks_count} 条记录")

        # 检查entities表
        entities_count = db.execute(text("""
            SELECT COUNT(*) FROM entities
            WHERE document_ids LIKE :pattern
        """), {"pattern": f"%{doc.id}%"}).scalar()
        logger.info(f"✅ entities表: {entities_count} 条记录")

        # 检查chunk_entities关联表
        chunk_entities_count = db.execute(text("""
            SELECT COUNT(*) FROM chunk_entities
        """)).scalar()
        logger.info(f"✅ chunk_entities关联表: {chunk_entities_count} 条记录")

        # 5. 完整追溯链查询
        logger.info("\n" + "="*60)
        logger.info("完整追溯链查询示例")
        logger.info("="*60)

        traceability_query = text("""
            SELECT
                dc.chunk_id,
                dc.text AS chunk_text,
                e.name AS entity_name,
                e.entity_type,
                ce.confidence,
                ce.mention_context
            FROM document_chunks dc
            JOIN chunk_entities ce ON dc.chunk_id = ce.chunk_id
            JOIN entities e ON ce.entity_id = e.id
            WHERE dc.document_id = :doc_id
            LIMIT 5
        """)

        results = db.execute(traceability_query, {"doc_id": doc.id}).fetchall()

        if results:
            logger.info(f"\n找到 {len(results)} 个追溯记录（显示前5个）：")
            for row in results:
                logger.info(f"\n  Chunk ID: {row.chunk_id}")
                logger.info(f"  Chunk文本: {row.chunk_text[:50]}...")
                logger.info(f"  Entity: {row.entity_name} ({row.entity_type})")
                logger.info(f"  置信度: {row.confidence}")
        else:
            logger.warning("\n⚠️ 未找到追溯记录，可能Entity提取未执行")

        logger.info("\n" + "="*60)
        logger.info("✅ 数据流追溯链测试完成！")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_data_flow()
