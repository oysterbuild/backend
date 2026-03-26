"""add constraint

Revision ID: 99782f1f6b5f
Revises: ca01d8350a2d
Create Date: 2026-03-25 18:24:07.835665

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "99782f1f6b5f"
down_revision: Union[str, Sequence[str], None] = "ca01d8350a2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE payment_status_enum AS ENUM('Pending', 'Paid', 'Approved', 'Expired', 'Overdue', 'Awaiting_Payment')"
    )
    op.execute("ALTER TABLE buildingproject DROP CONSTRAINT IF EXISTS check_status")
    op.execute(
        "ALTER TABLE buildingproject DROP CONSTRAINT IF EXISTS check_payment_status"
    )
    op.execute("ALTER TABLE paymenthistory DROP CONSTRAINT IF EXISTS check_status")
    op.create_check_constraint(
        "check_status",
        "buildingproject",
        "status IN ('Active', 'Pending', 'Draft', 'Completed', 'Cancelled')",
    )

    op.create_check_constraint(
        "check_payment_status",
        "buildingproject",
        "payment_status IN ('Active', 'Pending', 'Expired', 'Awaiting_Payment', 'Paid')",
    )
    op.create_check_constraint(
        "check_status",
        "paymenthistory",
        "status IN ('Active', 'Pending', 'Expired', 'Overdue', 'Paid')",
    )


def downgrade() -> None:
    # Drop check constraints
    op.drop_constraint("check_status", "paymenthistory", type_="check")
    op.execute("DROP TYPE payment_status_enum")
    op.drop_constraint("check_status", "buildingproject", type_="check")
    op.drop_constraint("check_payment_status", "buildingproject", type_="check")
