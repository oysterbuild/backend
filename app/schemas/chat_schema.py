from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SendMessageDTO(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    message_type: Literal["text", "image", "file"] = "text"


class ChatMessageResponse(BaseModel):
    id: UUID
    project_id: UUID
    sender_id: UUID
    content: str
    message_type: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    # Sender info — populated by the service
    sender_first_name: Optional[str] = None
    sender_last_name: Optional[str] = None
    sender_image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    meta_data: dict
    data: list[ChatMessageResponse]
    message: str


class UnreadCountResponse(BaseModel):
    project_id: UUID
    unread_count: int
