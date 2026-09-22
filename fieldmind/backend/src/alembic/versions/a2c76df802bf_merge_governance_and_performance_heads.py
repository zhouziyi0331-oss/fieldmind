"""merge governance and performance heads

Revision ID: a2c76df802bf
Revises: 003_seed_governance_data, 93e53fe4e26e
Create Date: 2026-08-21 10:33:08.961378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2c76df802bf'
down_revision: Union[str, None] = ('003_seed_governance_data', '93e53fe4e26e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
