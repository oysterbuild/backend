from models.base_model import BaseModel
from sqlalchemy import (
    String,
    Column,
    Boolean,
    UniqueConstraint,
    DateTime,
    Date,
    Text,
    CheckConstraint,
    UUID,
    Float,
    DECIMAL,
    ForeignKey,
    ARRAY,
    Integer,
)
from sqlalchemy.types import Enum  # <-- rename Enum
from datetime import datetime, date
from schemas.enums import ProjectType, InspectionWindowEnum, WeekdayEnum


# -----------------------------
# PROJECT MODEL
# -----------------------------
class BuildingProject(BaseModel):
    name = Column(String(225), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(Enum(ProjectType, name="project_type_emum"), nullable=False)
    location_text = Column(String(500))
    location_map = Column(String(500), nullable=True)  # URL or coordinates
    start_date = Column(Date())
    end_date = Column(Date())
    budget = Column(DECIMAL(20, 2), nullable=False, default=0.00)
    budget_currency = Column(String(3), nullable=False, default="NGN")  # NGN or USD
    status = Column(String(50), default="Draft")  # Active, Completed, On Hold
    payment_status = Column(String(50), default="Pending")
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )  # owner references User
    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("plan.id"), nullable=True, index=True
    )  # references Plan
    floor_number = Column(Integer(), default=1)
    preferred_inspection_days = Column(ARRAY(String), nullable=True)

    subscription_end_date = Column(Date(), nullable=True)  # references Plan

    preferred_inspection_window = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('Active', 'Pending','Draft','Completed')", name="check_status"
        ),
        CheckConstraint(
            "payment_status IN ('Active', 'Pending','Expired')",
            name="check_payment_status",
        ),
        CheckConstraint(
            "budget_currency IN ('NGN', 'USD')", name="check_budget_currency"
        ),
        CheckConstraint(
            "preferred_inspection_window IN ('Morning','Afternoon','Evening')",
            name="check_inspection_window",
        ),
        CheckConstraint(
            "preferred_inspection_days <@ ARRAY['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']::varchar[]",
            name="check_inspection_days",
        ),
    )
