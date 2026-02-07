"""add new column

Revision ID: 8a85fd3729d2
Revises: a1e37a4d340a
Create Date: 2026-02-02 14:11:29.024927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a85fd3729d2'
down_revision: Union[str, Sequence[str], None] = 'a1e37a4d340a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
