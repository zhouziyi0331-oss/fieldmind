"""merge_migration_heads

Revision ID: 6e100f21029c
Revises: 007_pipeline_tracking, fd1ee1e9d5d3
Create Date: 2026-08-18 12:49:31.530405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e100f21029c'
down_revision: Union[str, None] = ('007_pipeline_tracking', 'fd1ee1e9d5d3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
