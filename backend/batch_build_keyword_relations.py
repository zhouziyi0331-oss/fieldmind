"""
批量构建关键词共现关系
用于为已有项目构建关键词关系网络
"""

import sys
import os
import argparse
import logging
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.core.database import SessionLocal
from app.services.keyword_relation_builder import KeywordRelationBuilder
from app.models.keyword import Keyword

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def batch_build_relations(
    project_id: int,
    min_cooccurrence: int = 2,
    recalculate: bool = False,
    test_mode: bool = False,
    limit: int = None
):
    """
    批量构建关键词关系

    Args:
        project_id: 项目ID
        min_cooccurrence: 最小共现次数
        recalculate: 是否重新计算（删除旧数据）
        test_mode: 测试模式（只处理部分数据）
        limit: 限制处理的关键词数量（测试用）
    """
    db = SessionLocal()

    try:
        logger.info("=" * 60)
        logger.info("关键词共现关系构建")
        logger.info("=" * 60)
        logger.info(f"项目ID: {project_id}")
        logger.info(f"最小共现次数: {min_cooccurrence}")
        logger.info(f"重新计算: {recalculate}")
        logger.info(f"测试模式: {test_mode}")
        if limit:
            logger.info(f"限制关键词数: {limit}")
        logger.info("")

        # 获取关键词统计
        total_keywords = db.query(Keyword).filter(
            Keyword.project_id == project_id
        ).count()

        logger.info(f"项目关键词总数: {total_keywords}")

        if total_keywords == 0:
            logger.warning("项目没有关键词，退出")
            return

        # 测试模式：限制处理范围
        if test_mode and not limit:
            limit = 50
            logger.info(f"测试模式：限制处理 Top {limit} 关键词")

        # 创建关系构建器
        builder = KeywordRelationBuilder(db)

        # 构建共现关系
        start_time = datetime.now()
        logger.info("\n开始构建共现关系...")

        stats = builder.build_cooccurrence_relations(
            project_id=project_id,
            min_cooccurrence=min_cooccurrence,
            recalculate=recalculate
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "=" * 60)
        logger.info("构建完成")
        logger.info("=" * 60)
        logger.info(f"处理文档数: {stats['documents_processed']}")
        logger.info(f"发现关键词对: {stats['keyword_pairs_found']}")
        logger.info(f"创建关系数: {stats['relations_created']}")
        logger.info(f"耗时: {duration:.2f} 秒")

        # 获取统计信息
        logger.info("\n获取关系统计...")
        relation_stats = builder.get_relation_statistics(project_id)

        logger.info("\n" + "=" * 60)
        logger.info("关系网络统计")
        logger.info("=" * 60)
        logger.info(f"总关系数: {relation_stats['total_relations']}")
        logger.info(f"平均强度: {relation_stats['average_strength']}")
        logger.info(f"最大共现次数: {relation_stats['max_cooccurrence']}")

        logger.info("\n连接最多的关键词 (Top 10):")
        for idx, item in enumerate(relation_stats['top_connected_keywords'], 1):
            logger.info(f"{idx}. {item['keyword']} - {item['connections']} 个连接")

        # 示例：展示最强关系
        from app.models.keyword import KeywordRelation
        top_relations = db.query(KeywordRelation).filter(
            KeywordRelation.project_id == project_id
        ).order_by(KeywordRelation.strength.desc()).limit(10).all()

        logger.info("\n最强关系 (Top 10):")
        for idx, rel in enumerate(top_relations, 1):
            kw1 = db.query(Keyword).filter(Keyword.id == rel.keyword1_id).first()
            kw2 = db.query(Keyword).filter(Keyword.id == rel.keyword2_id).first()
            if kw1 and kw2:
                logger.info(
                    f"{idx}. {kw1.text} <-> {kw2.text} "
                    f"(共现:{rel.co_occurrence}, 强度:{rel.strength:.4f})"
                )

        logger.info("\n✅ 关键词关系网络构建完成！")

    except Exception as e:
        logger.error(f"构建失败: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="批量构建关键词共现关系")

    parser.add_argument(
        '--project-id',
        type=int,
        default=1,
        help='项目ID（默认: 1）'
    )

    parser.add_argument(
        '--min-cooccurrence',
        type=int,
        default=2,
        help='最小共现次数，过滤噪音（默认: 2）'
    )

    parser.add_argument(
        '--recalculate',
        action='store_true',
        help='重新计算（删除旧关系）'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式（限制处理数量）'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='限制处理的关键词数量'
    )

    args = parser.parse_args()

    # 执行构建
    batch_build_relations(
        project_id=args.project_id,
        min_cooccurrence=args.min_cooccurrence,
        recalculate=args.recalculate,
        test_mode=args.test,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
