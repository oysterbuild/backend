"""remove_old_check_constraint

Revision ID: 662a3853e2a6
Revises: d78f08a56522
Create Date: 2026-02-02 14:04:08.630122

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '662a3853e2a6'
down_revision: Union[str, Sequence[str], None] = 'd78f08a56522'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
