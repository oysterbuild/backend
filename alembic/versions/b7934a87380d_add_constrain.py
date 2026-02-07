"""add constrain

Revision ID: b7934a87380d
Revises: 662a3853e2a6
Create Date: 2026-02-02 14:04:48.604775

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7934a87380d"
down_revision: Union[str, Sequence[str], None] = "662a3853e2a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "check_transaction_status",  # Name of the constraint
        "transaction",  # Name of the table
        "status IN ('SUCCESS', 'FAILED', 'PENDING')",  # The actual SQL rule
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
