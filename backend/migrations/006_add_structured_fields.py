"""
数据库迁移：为 document_chunks 表添加结构化数据字段

版本：006
创建时间：2026-08-22
描述：添加语义增强字段和表格结构化字段，支持深度结构化数据处理
"""

import sqlite3
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def migrate_up(db_path: str):
    """升级数据库：添加新字段"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔄 开始数据库迁移：添加结构化数据字段")

    try:
        # 检查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='document_chunks'
        """)

        if not cursor.fetchone():
            print("⚠️  document_chunks 表不存在，跳过迁移")
            return

        # 获取现有列
        cursor.execute("PRAGMA table_info(document_chunks)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # 要添加的新列
        new_columns = [
            ("chapter_title", "TEXT", "所属章节标题"),
            ("section_title", "TEXT", "所属小节标题"),
            ("subsection_title", "TEXT", "所属子小节标题"),
            ("key_entities", "TEXT", "关键实体列表JSON"),
            ("domain_tags", "TEXT", "领域标签列表JSON"),
            ("primary_domain", "TEXT", "主领域标签"),
            ("temporal_context", "TEXT", "时间上下文"),
            ("spatial_context", "TEXT", "空间上下文"),
            ("chunk_role", "TEXT", "Chunk角色"),
            ("chunk_summary", "TEXT", "Chunk摘要"),
            ("enhanced_text", "TEXT", "增强文本"),
            ("enhancement_confidence", "INTEGER", "语义增强置信度"),
            ("is_table_chunk", "INTEGER DEFAULT 0", "是否为表格chunk"),
            ("table_sheet_name", "TEXT", "表格工作表名称"),
            ("table_row_range", "TEXT", "表格行范围"),
            ("structured_data", "TEXT", "结构化数据JSON"),
        ]

        added_count = 0

        for col_name, col_type, col_desc in new_columns:
            if col_name not in existing_columns:
                print(f"   ➕ 添加列: {col_name} ({col_desc})")
                cursor.execute(f"""
                    ALTER TABLE document_chunks
                    ADD COLUMN {col_name} {col_type}
                """)
                added_count += 1
            else:
                print(f"   ⏭️  跳过列: {col_name} (已存在)")

        conn.commit()

        print(f"\n✅ 迁移完成：添加了 {added_count} 个新字段")

        # 显示当前表结构
        cursor.execute("PRAGMA table_info(document_chunks)")
        columns = cursor.fetchall()
        print(f"\n📊 document_chunks 表现有 {len(columns)} 个字段")

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        raise

    finally:
        conn.close()


def migrate_down(db_path: str):
    """降级数据库：移除新字段（SQLite 不支持 DROP COLUMN，需要重建表）"""

    print("⚠️  SQLite 不支持直接删除列")
    print("   如需回滚，请手动重建表或恢复数据库备份")


if __name__ == "__main__":
    # 默认数据库路径
    default_db_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "data",
        "fieldmind.db"
    )

    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db_path

    print(f"📁 数据库路径: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        sys.exit(1)

    # 备份数据库
    import shutil
    from datetime import datetime

    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"💾 创建备份: {backup_path}")
    shutil.copy2(db_path, backup_path)

    # 执行迁移
    try:
        migrate_up(db_path)
        print(f"\n🎉 迁移成功！备份已保存至: {backup_path}")
    except Exception as e:
        print(f"\n💥 迁移失败，请使用备份恢复: {backup_path}")
        sys.exit(1)
