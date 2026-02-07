"""add new column

Revision ID: a1e37a4d340a
Revises: b7934a87380d
Create Date: 2026-02-02 14:09:45.787416

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1e37a4d340a'
down_revision: Union[str, Sequence[str], None] = 'b7934a87380d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
