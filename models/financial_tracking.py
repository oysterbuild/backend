from models.base_model import BaseModel
from sqlalchemy import (
    String,
    Column,
    Boolean,
    UniqueConstraint,
    DateTime,
    Text,
    CheckConstraint,
    UUID,
    Float,
    ForeignKey,
    DECIMAL,
)
from sqlalchemy.types import Enum  # <-- rename Enum
from datetime import datetime
from schemas.enums import PaymentStatus


# -----------------------------
# FINANCIAL TRACKING
# -----------------------------
class ProjectPayment(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    milestone_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projectmilestone.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    amount = Column(DECIMAL(20, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="NGN")  # NGN or USD
    status = Column(
        Enum(PaymentStatus, name="payment_status_emum"), default=PaymentStatus.PENDING
    )
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("currency IN ('NGN', 'USD')", name="check_currency"),
    )
