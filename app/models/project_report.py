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
    Date,
    ARRAY,
)
from sqlalchemy.types import Enum  # <-- rename Enum
from datetime import datetime
from schemas.enums import ReportType


# -----------------------------
# REPORTS
# -----------------------------
class ProjectReport(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(225), nullable=False)
    report_type = Column(Enum(ReportType, name="report_type_enum"), nullable=False)
    report_date = Column(Date())
    description = Column(Text)
    progress_percent = Column(Float)
    recommendation = Column(ARRAY(String), default=list)
    approval_required = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    submitted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
