"""
Add business dimension fields for real data governance

Revision ID: 007_add_business_dimensions
Revises: 006_add_quantification_fields
Create Date: 2026-08-21 12:30:00.000000

这是真正的数据治理：添加业务维度字段
- 衣食住行
- 民俗
- 物质文化遗产
- 非物质文化遗产
- 政策
- 历史
"""
from alembic import op
import sqlalchemy as sa

revision = '007_add_business_dimensions'
down_revision = '006_add_quantification_fields'
branch_labels = None
depends_on = None


def upgrade():
    """添加业务维度字段到 document_chunks 表"""

    print("\n" + "="*60)
    print("添加业务维度字段 - 真正的数据治理")
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

    # 定义需要添加的业务维度字段
    fields_to_add = [
        ('dimension_category', 'TEXT', '一级维度：衣食住行/民俗/非遗/物质遗产/政策/历史'),
        ('dimension_sub_category', 'TEXT', '二级细分：具体类别'),
        ('time_period', 'TEXT', '时间区间'),
        ('location', 'TEXT', '地点（村寨名）'),
        ('culture_code', 'TEXT', '文化形态编码'),
        ('keywords_matched', 'TEXT', '匹配到的关键词（JSON）'),
        ('confidence_score', 'FLOAT', '分类置信度（0-1）')
    ]

    added_count = 0
    skipped_count = 0

    for field_name, field_type, description in fields_to_add:
        if field_name in existing_columns:
            print(f"⏭  跳过已存在的字段: {field_name}")
            skipped_count += 1
            continue

        try:
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
    print("\n这7个字段让数据治理具备：")
    print("  ✓ 维度分类（衣食住行、民俗、非遗等）")
    print("  ✓ 时空定位（时间区间、地点）")
    print("  ✓ 文化标识（文化形态编码）")
    print("  ✓ 可追溯（关键词匹配记录）")
    print("\n现在可以按业务维度查询和统计了！")
    print()


def downgrade():
    """删除业务维度字段"""
    print("\n回滚：删除业务维度字段")
    print("⚠️  SQLite 不支持 DROP COLUMN")
    print("如需删除字段，请手动重建表")
