"""added relations

Revision ID: dd35d009acff
Revises: 2c353fc290a4
Create Date: 2026-03-25 16:51:55.933256

"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dd35d009acff"
down_revision: Union[str, Sequence[str], None] = "2c353fc290a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Drop old constraint
    op.execute(
        """
        ALTER TABLE "user"
        DROP CONSTRAINT check_user_role_valid;
    """
    )

    # Add new constraint with INSPECTOR
    op.execute(
        """
        ALTER TABLE "user"
        ADD CONSTRAINT check_user_role_valid
        CHECK (role IN ('USER', 'SUPER_ADMIN', 'INSPECTOR'));
    """
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove updated constraint
    op.execute(
        """
        ALTER TABLE "user"
        DROP CONSTRAINT check_user_role_valid;
    """
    )

    # Restore old constraint (without INSPECTOR)
    op.execute(
        """
        ALTER TABLE "user"
        ADD CONSTRAINT check_user_role_valid
        CHECK (role IN ('USER', 'SUPER_ADMIN'));
    """
    )
