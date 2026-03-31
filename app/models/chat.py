from sqlalchemy import Column, UUID, Text, Boolean, ForeignKey, String
from .base_model import BaseModel


class ChatMessage(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    # "text" | "image" | "file" — extend as needed
    message_type = Column(String(20), nullable=False, server_default="text")
    is_read = Column(Boolean, default=False, nullable=False)
