"""merge_heads

Revision ID: 38056f8a46c5
Revises: 009_knowledge_graph_integration, b65525f1a4d6
Create Date: 2026-09-24 11:05:41.401529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38056f8a46c5'
down_revision: Union[str, None] = ('009_knowledge_graph_integration', 'b65525f1a4d6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
