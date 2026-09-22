"""
Add structurization quantification fields to document_chunks

Revision ID: 006_add_quantification_fields
Revises: 005_seed_governance
Create Date: 2026-08-21 11:30:00.000000

这是 FieldMind 最核心的迁移：添加7个量化字段
把非结构化文本变成结构化数据

7个字段：
1. word_count - 字数
2. sentence_count - 句数
3. exclamation_count - 感叹号数量
4. emotion_polarity - 情感极性（-1到1）
5. subjectivity - 主观性（0到1）
6. emotion_word_density - 情绪词密度
7. avg_word_length - 平均词长
"""
from alembic import op
import sqlalchemy as sa

revision = '006_add_quantification_fields'
down_revision = '005_seed_governance'
branch_labels = None
depends_on = None


def upgrade():
    """添加7个量化字段到 document_chunks 表"""

    print("\n" + "="*60)
    print("开始添加文本结构化量化字段")
    print("这是从'非结构化→结构化'的关键一步")
    print("="*60)

    conn = op.get_bind()

    # 检查表是否存在
    result = conn.execute(sa.text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='document_chunks'"
    ))

    if not result.fetchone():
        print("⚠️  document_chunks 表不存在，跳过")
        return

    # 检查哪些字段已经存在
    result = conn.execute(sa.text("PRAGMA table_info(document_chunks)"))
    existing_columns = {row[1] for row in result.fetchall()}

    # 定义需要添加的7个字段
    fields_to_add = [
        ('word_count', 'INTEGER', '字数'),
        ('sentence_count', 'INTEGER', '句数'),
        ('exclamation_count', 'INTEGER', '感叹号数量'),
        ('emotion_polarity', 'FLOAT', '情感极性（-1到1）'),
        ('subjectivity', 'FLOAT', '主观性（0到1）'),
        ('emotion_word_density', 'FLOAT', '情绪词密度'),
        ('avg_word_length', 'FLOAT', '平均词长')
    ]

    added_count = 0
    skipped_count = 0

    for field_name, field_type, description in fields_to_add:
        if field_name in existing_columns:
            print(f"⏭  跳过已存在的字段: {field_name}")
            skipped_count += 1
            continue

        try:
            # SQLite 使用 ALTER TABLE ADD COLUMN
            conn.execute(sa.text(f"""
                ALTER TABLE document_chunks
                ADD COLUMN {field_name} {field_type}
            """))
            print(f"✅ 添加字段: {field_name} ({field_type}) - {description}")
            added_count += 1
        except Exception as e:
            print(f"❌ 添加字段 {field_name} 失败: {e}")

    print("\n" + "="*60)
    print(f"✅ 完成！添加了 {added_count} 个字段，跳过 {skipped_count} 个已存在字段")
    print("="*60)
    print("\n这7个字段让每个文本块都有了：")
    print("  ✓ 基础统计（字数、句数、感叹号）")
    print("  ✓ 情感指标（情感极性、主观性）")
    print("  ✓ 复杂度指标（情绪词密度、平均词长）")
    print("\n现在 document_chunks 表的每条记录都是结构化数据了！")
    print()


def downgrade():
    """删除7个量化字段"""
    print("\n回滚：删除量化字段")

    # SQLite 不支持 DROP COLUMN，需要重建表
    # 这里只打印提示，实际生产环境需要谨慎操作
    print("⚠️  SQLite 不支持 DROP COLUMN")
    print("如需删除字段，请手动重建表")
