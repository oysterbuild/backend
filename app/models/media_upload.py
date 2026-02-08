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
)
from sqlalchemy.types import Enum  # <-- rename Enum
from datetime import datetime
from schemas.enums import PaymentStatus


class ProjectUpload(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(50))  # image, document, etc.
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ReportUpload(BaseModel):
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projectreport.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(50))
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
