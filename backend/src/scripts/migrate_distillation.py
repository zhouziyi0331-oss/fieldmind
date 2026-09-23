"""
蒸馏功能数据库迁移脚本
添加 distilled_units 和 distilled_unit_relations 表
"""
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_distillation_tables(db_path: str):
    """创建蒸馏功能相关的数据表"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. 创建蒸馏产物表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distilled_units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                unit_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_chunks TEXT,
                credibility REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_distilled_units_project_id
            ON distilled_units(project_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_distilled_units_type
            ON distilled_units(unit_type)
        """)

        # 2. 创建蒸馏产物关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS distilled_unit_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                distilled_unit_id INTEGER NOT NULL,
                related_type TEXT NOT NULL,
                related_id INTEGER NOT NULL,
                relation_type TEXT,
                strength REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (distilled_unit_id) REFERENCES distilled_units(id) ON DELETE CASCADE
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_distilled_relations_unit_id
            ON distilled_unit_relations(distilled_unit_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_distilled_relations_related
            ON distilled_unit_relations(related_type, related_id)
        """)

        conn.commit()
        logger.info("✅ 蒸馏功能数据表创建成功")

        return True

    except Exception as e:
        logger.error(f"❌ 创建蒸馏功能数据表失败: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    # 测试迁移
    db_path = Path(__file__).parents[2] / "data" / "fieldmind.db"
    migrate_distillation_tables(str(db_path))
