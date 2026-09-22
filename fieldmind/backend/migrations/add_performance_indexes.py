#!/usr/bin/env python3
"""
数据库性能索引迁移脚本 v2
基于实际表结构添加索引
"""

import sys
from pathlib import Path

# 添加项目路径
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

from sqlalchemy import create_engine, text, inspect
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_index_if_not_exists(engine, table_name: str, index_name: str, columns: str):
    """创建索引（如果不存在）"""
    inspector = inspect(engine)

    # 检查表是否存在
    if table_name not in inspector.get_table_names():
        logger.warning(f"⚠️  表 {table_name} 不存在，跳过")
        return None

    existing_indexes = [idx['name'] for idx in inspector.get_indexes(table_name)]

    if index_name in existing_indexes:
        logger.info(f"⏭️  索引 {index_name} 已存在，跳过")
        return False

    try:
        with engine.connect() as conn:
            sql = f"CREATE INDEX {index_name} ON {table_name} ({columns})"
            conn.execute(text(sql))
            conn.commit()
        logger.info(f"✅ 创建索引: {index_name} ON {table_name}({columns})")
        return True
    except Exception as e:
        logger.error(f"❌ 创建索引失败 {index_name}: {e}")
        return False


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("开始数据库性能索引迁移（基于实际表结构）")
    logger.info("=" * 80)

    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL)

    # 索引定义列表（基于实际表结构）
    indexes = [
        # Projects 表索引
        {
            "table": "projects",
            "name": "idx_projects_created",
            "columns": "created_at DESC",
            "purpose": "按创建时间排序项目"
        },

        # Documents 表索引
        {
            "table": "documents",
            "name": "idx_documents_project_status",
            "columns": "project_id, status",
            "purpose": "查询项目下特定状态的文档"
        },
        {
            "table": "documents",
            "name": "idx_documents_created",
            "columns": "created_at DESC",
            "purpose": "按创建时间排序文档"
        },

        # Project Documents 表索引
        {
            "table": "project_documents",
            "name": "idx_project_docs_project",
            "columns": "project_id, created_at DESC",
            "purpose": "查询项目的所有文档（按时间排序）"
        },
        {
            "table": "project_documents",
            "name": "idx_project_docs_status",
            "columns": "processing_status",
            "purpose": "按处理状态过滤文档"
        },

        # Document Chunks 表索引
        {
            "table": "document_chunks",
            "name": "idx_doc_chunks_document",
            "columns": "document_id, chunk_index",
            "purpose": "按文档和顺序查询分块"
        },
        {
            "table": "document_chunks",
            "name": "idx_doc_chunks_project",
            "columns": "project_id",
            "purpose": "按项目查询所有分块"
        },

        # Structured Insights 表索引（结论）
        {
            "table": "structured_insights",
            "name": "idx_insights_document",
            "columns": "document_id, chunk_index",
            "purpose": "查询文档的结构化洞察"
        },
        {
            "table": "structured_insights",
            "name": "idx_insights_project",
            "columns": "project_id, created_at DESC",
            "purpose": "查询项目的所有洞察（按时间排序）"
        },
        {
            "table": "structured_insights",
            "name": "idx_insights_dimension",
            "columns": "dimension, sub_dimension",
            "purpose": "按维度筛选洞察"
        },

        # Project Members 表索引
        {
            "table": "project_members",
            "name": "idx_members_project_user",
            "columns": "project_id, user_id",
            "purpose": "快速查询用户在项目中的角色"
        },
        {
            "table": "project_members",
            "name": "idx_members_user",
            "columns": "user_id",
            "purpose": "查询用户参与的所有项目"
        },
        {
            "table": "project_members",
            "name": "idx_members_active",
            "columns": "is_active",
            "purpose": "过滤活跃成员"
        },

        # Project Invites 表索引
        {
            "table": "project_invites",
            "name": "idx_invites_project",
            "columns": "project_id, status",
            "purpose": "查询项目的邀请状态"
        },
        {
            "table": "project_invites",
            "name": "idx_invites_code",
            "columns": "invite_code",
            "purpose": "通过邀请码快速查找邀请"
        },
        {
            "table": "project_invites",
            "name": "idx_invites_expires",
            "columns": "expires_at",
            "purpose": "清理过期邀请"
        },

        # Project Activity Logs 表索引
        {
            "table": "project_activity_logs",
            "name": "idx_activity_project_time",
            "columns": "project_id, created_at DESC",
            "purpose": "按时间倒序查询项目活动"
        },
        {
            "table": "project_activity_logs",
            "name": "idx_activity_user",
            "columns": "user_id",
            "purpose": "查询用户的所有活动"
        },
        {
            "table": "project_activity_logs",
            "name": "idx_activity_action",
            "columns": "action",
            "purpose": "按操作类型筛选活动"
        },

        # Users 表索引
        {
            "table": "users",
            "name": "idx_users_email",
            "columns": "email",
            "purpose": "通过邮箱快速查找用户（登录）"
        },
        {
            "table": "users",
            "name": "idx_users_username",
            "columns": "username",
            "purpose": "通过用户名查找用户"
        },

        # Entities 表索引（知识图谱）
        {
            "table": "entities",
            "name": "idx_entities_type",
            "columns": "type",
            "purpose": "按实体类型筛选"
        },
        {
            "table": "entities",
            "name": "idx_entities_text",
            "columns": "text",
            "purpose": "快速查找实体文本"
        },

        # Entity Relations 表索引
        {
            "table": "entity_relations",
            "name": "idx_relations_source",
            "columns": "source_entity_id",
            "purpose": "查询实体的所有关系"
        },
        {
            "table": "entity_relations",
            "name": "idx_relations_target",
            "columns": "target_entity_id",
            "purpose": "查询指向实体的关系"
        },
        {
            "table": "entity_relations",
            "name": "idx_relations_type",
            "columns": "relation_type",
            "purpose": "按关系类型筛选"
        },

        # Document Entities 表索引
        {
            "table": "document_entities",
            "name": "idx_doc_entities_doc",
            "columns": "document_id",
            "purpose": "查询文档的所有实体"
        },
        {
            "table": "document_entities",
            "name": "idx_doc_entities_entity",
            "columns": "entity_id",
            "purpose": "查询实体出现的文档"
        },

        # Processing Tasks 表索引
        {
            "table": "processing_tasks",
            "name": "idx_tasks_document",
            "columns": "document_id, status",
            "purpose": "查询文档的处理任务"
        },
        {
            "table": "processing_tasks",
            "name": "idx_tasks_status",
            "columns": "status, created_at DESC",
            "purpose": "按状态和时间查询任务"
        },

        # Audit Logs 表索引
        {
            "table": "audit_logs",
            "name": "idx_audit_timestamp",
            "columns": "timestamp DESC",
            "purpose": "按时间倒序查询审计日志"
        },
        {
            "table": "audit_logs",
            "name": "idx_audit_actor",
            "columns": "actor_id, actor_type",
            "purpose": "查询特定用户的操作"
        },
        {
            "table": "audit_logs",
            "name": "idx_audit_action",
            "columns": "action",
            "purpose": "按操作类型筛选"
        },
    ]

    # 执行索引创建
    created_count = 0
    skipped_count = 0
    failed_count = 0
    table_not_found = 0

    for idx_def in indexes:
        logger.info(f"\n📌 {idx_def['purpose']}")
        result = create_index_if_not_exists(
            engine,
            idx_def['table'],
            idx_def['name'],
            idx_def['columns']
        )

        if result is True:
            created_count += 1
        elif result is False:
            skipped_count += 1
        elif result is None:
            table_not_found += 1
        else:
            failed_count += 1

    # 输出摘要
    logger.info("\n" + "=" * 80)
    logger.info("索引迁移完成")
    logger.info("=" * 80)
    logger.info(f"✅ 新建索引: {created_count}")
    logger.info(f"⏭️  跳过索引: {skipped_count}")
    logger.info(f"⚠️  表不存在: {table_not_found}")
    logger.info(f"❌ 失败索引: {failed_count}")
    logger.info(f"📊 总计: {len(indexes)}")

    if failed_count > 0:
        logger.warning("⚠️  部分索引创建失败，请检查日志")
        return 1
    else:
        logger.info("🎉 所有可用表的索引创建成功！")
        return 0


if __name__ == "__main__":
    exit(main())
