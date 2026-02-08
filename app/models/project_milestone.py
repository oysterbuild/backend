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
    Integer,
    DECIMAL,
)
from sqlalchemy.types import Enum  # <-- rename Enum
from datetime import datetime
from schemas.enums import MilestoneStatus


# -----------------------------
# MILESTONES
# -----------------------------
class ProjectMilestone(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(225), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    expected_deliverables = Column(Text)
    payment_percentage = Column(Float, nullable=True, default=0)
    payment_amount = Column(DECIMAL(20, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="NGN")  # NGN or USD
    sequential_order = Column(Integer, default=0)
    status = Column(
        Enum(MilestoneStatus, name="milestone_status_enum"),
        default=MilestoneStatus.PENDING,
    )

    __table_args__ = (
        CheckConstraint("currency IN ('NGN', 'USD')", name="check_currency"),
    )
