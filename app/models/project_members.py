from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime,
    DECIMAL,
    UUID,
    CheckConstraint,
    Text,
)
from datetime import datetime, timezone
from .base_model import BaseModel


# INSPECTORS
class ProjectMember(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # role_id = Column(
    #     UUID(as_uuid=True),
    #     ForeignKey("role.id", ondelete="CASCADE"),
    #     nullable=False,
    #     index=True,
    # )
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    visit_type = Column(String(225), nullable=True)
    note = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)  # member is active or not
    joined_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
