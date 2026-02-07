from utils.db_setup import Base
from sqlalchemy import Column, UUID, DateTime
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import declared_attr


class BaseModel(Base):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), index=True, primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # to generate tablename from classname
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
