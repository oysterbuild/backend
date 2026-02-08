from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime,
    DECIMAL,
    UUID,
    CheckConstraint,
    Date,
)
from .base_model import BaseModel


class Plan(BaseModel):
    name = Column(String(225), nullable=False)
    description = Column(String, nullable=True)
    slug = Column(String(225), nullable=True)
    frequency = Column(
        String(20), nullable=False, default="Monthly"
    )  # Monthly/Yearly # same as above
    plan_status = Column(
        String(20), nullable=False, default="Free"
    )  # e.g., Free or Paid
    amount = Column(DECIMAL(20, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="NGN")  # NGN or USD
    deactivate = Column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint("plan_status IN ('Free', 'Paid')", name="check_plan_status"),
        CheckConstraint("frequency IN ('Monthly', 'Yearly')", name="check_frequency"),
        CheckConstraint("currency IN ('NGN', 'USD')", name="check_currency"),
    )


# ---------------------------
# Billing Packages
# ---------------------------
class Package(BaseModel):
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(500), nullable=False)  # e.g., "Number of Projects"
    count = Column(Float, nullable=True)  # e.g., 5 projects, storage in KB
    tag = Column(String(225), nullable=True)  # e.g., "projects", "reports", "storage"
    is_unlimited = Column(Boolean, default=False)  # True if unlimited


# ---------------------------
# Billing Packages
# ---------------------------
class PlanPackageUsageCount(BaseModel):
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("buildingproject.id"), nullable=False, index=True
    )
    package_tag = Column(String(50), nullable=False)
    usage_count = Column(Integer(), nullable=False, default=0)


class PaymentHistory(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invoice_id = Column(
        String(100),
        ForeignKey("invoice.invoice_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    currency = Column(String(3), nullable=False, default="NGN")  # NGN or USD
    amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    months = Column(Integer, nullable=False, default=0)
    status = Column(String(10), nullable=False, default="Pending")

    start_date = Column(Date, nullable=True)
    next_billing_date = Column(Date, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('Active', 'Pending','Expired')",
            name="check_status",
        ),
        CheckConstraint("currency IN ('NGN', 'USD')", name="check_currency"),
    )
