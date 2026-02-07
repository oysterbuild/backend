"""remove_old_check_constraint

Revision ID: d78f08a56522
Revises: 03a5db1142c4
Create Date: 2026-02-02 14:03:23.275868

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d78f08a56522"
down_revision: Union[str, Sequence[str], None] = "03a5db1142c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("check_transaction_status", "transaction", type_="check")


def downgrade() -> None:
    """Downgrade schema."""
    pass
