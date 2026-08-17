"""
添加Citations表
Create citations and document_citations tables
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_citations_table'
down_revision = None  # 实际使用时需要设置为上一个migration的revision
branch_labels = None
depends_on = None


def upgrade():
    # 创建citations表
    op.create_table(
        'citations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('authors', sa.JSON(), nullable=True),
        sa.Column('year', sa.String(length=20), nullable=True),
        sa.Column('publication', sa.String(length=300), nullable=True),
        sa.Column('publisher', sa.String(length=200), nullable=True),
        sa.Column('doi', sa.String(length=200), nullable=True),
        sa.Column('isbn', sa.String(length=50), nullable=True),
        sa.Column('url', sa.String(length=1000), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('citation_type', sa.String(length=50), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('cited_count', sa.Integer(), nullable=True, default=0),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('added_by', sa.Integer(), nullable=True),
        sa.Column('bibtex', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_citations_title', 'citations', ['title'])
    op.create_index('ix_citations_doi', 'citations', ['doi'], unique=True)
    op.create_index('ix_citations_project_id', 'citations', ['project_id'])
    op.create_index('ix_citations_citation_type', 'citations', ['citation_type'])

    # 创建document_citations关联表
    op.create_table(
        'document_citations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('citation_id', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('location_text', sa.String(length=500), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['citation_id'], ['citations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('ix_document_citations_document_id', 'document_citations', ['document_id'])
    op.create_index('ix_document_citations_citation_id', 'document_citations', ['citation_id'])


def downgrade():
    # 删除表和索引
    op.drop_index('ix_document_citations_citation_id', table_name='document_citations')
    op.drop_index('ix_document_citations_document_id', table_name='document_citations')
    op.drop_table('document_citations')

    op.drop_index('ix_citations_citation_type', table_name='citations')
    op.drop_index('ix_citations_project_id', table_name='citations')
    op.drop_index('ix_citations_doi', table_name='citations')
    op.drop_index('ix_citations_title', table_name='citations')
    op.drop_table('citations')
