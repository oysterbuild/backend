from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.building_project import BuildingProject
from models.chat import ChatMessage
from models.project_members import ProjectMember
from models.users import User
from utils.loggers import setup_logger
from utils.pagination import normalize_pagination
from utils.redis_client import redis_client

logger = setup_logger("ChatService")

CHAT_CHANNEL_PREFIX = "chat:"


def _channel(project_id: str) -> str:
    return f"{CHAT_CHANNEL_PREFIX}{project_id}"


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Access helpers
    # ------------------------------------------------------------------

    async def _assert_project_participant(self, project_id: str, user_id: str) -> None:
        """Raise 403 if the user is neither the project owner nor an active member."""
        project = await self.db.scalar(
            select(BuildingProject).where(BuildingProject.id == project_id)
        )
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        is_owner = str(project.owner_id) == user_id

        if not is_owner:
            member = await self.db.scalar(
                select(ProjectMember).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                    ProjectMember.is_active.is_(True),
                )
            )
            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not a participant of this project.",
                )

    # ------------------------------------------------------------------
    # HTTP: send message
    # ------------------------------------------------------------------

    async def send_message(
        self,
        project_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text",
    ) -> dict:
        await self._assert_project_participant(project_id, sender_id)

        try:
            msg = ChatMessage(
                project_id=project_id,
                sender_id=sender_id,
                content=content,
                message_type=message_type,
            )
            self.db.add(msg)
            await self.db.commit()
            await self.db.refresh(msg)

            # fetch sender info
            sender = await self.db.get(User, sender_id)

            payload = self._serialize_message(msg, sender)

            # publish to Redis so WebSocket subscribers receive it
            await redis_client.publish(_channel(project_id), json.dumps(payload))

            return {"data": payload, "message": "Message sent successfully"}
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"send_message failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while sending the message.",
            ) from e

    # ------------------------------------------------------------------
    # HTTP: get message history
    # ------------------------------------------------------------------

    async def get_project_messages(
        self,
        project_id: str,
        user_id: str,
        page: int = 1,
        limit: int = 20,
        before: Optional[datetime] = None,
    ) -> dict:
        await self._assert_project_participant(project_id, user_id)

        page, limit, offset = normalize_pagination(page, limit)

        stmt = (
            select(ChatMessage, User)
            .join(User, ChatMessage.sender_id == User.id)
            .where(ChatMessage.project_id == project_id)
        )
        if before:
            stmt = stmt.where(ChatMessage.created_at < before)

        stmt = stmt.order_by(ChatMessage.created_at.desc()).offset(offset).limit(limit)
        rows = (await self.db.execute(stmt)).all()

        messages = [self._serialize_message(msg, sender) for msg, sender in rows]

        total = await self.db.scalar(
            select(func.count())
            .select_from(ChatMessage)
            .where(ChatMessage.project_id == project_id)
        )

        return {
            "meta_data": {"page": page, "limit": limit, "total": total},
            "data": messages,
            "message": "Messages fetched successfully",
        }

    # ------------------------------------------------------------------
    # HTTP: mark messages as read
    # ------------------------------------------------------------------

    async def mark_as_read(self, project_id: str, user_id: str) -> dict:
        """Mark all messages in the project as read for the requesting user (messages NOT sent by them)."""
        await self._assert_project_participant(project_id, user_id)

        await self.db.execute(
            update(ChatMessage)
            .where(
                ChatMessage.project_id == project_id,
                ChatMessage.sender_id != user_id,
                ChatMessage.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self.db.commit()
        return {"data": None, "message": "Messages marked as read"}

    # ------------------------------------------------------------------
    # HTTP: unread count
    # ------------------------------------------------------------------

    async def get_unread_count(self, project_id: str, user_id: str) -> dict:
        await self._assert_project_participant(project_id, user_id)

        count = await self.db.scalar(
            select(func.count())
            .select_from(ChatMessage)
            .where(
                ChatMessage.project_id == project_id,
                ChatMessage.sender_id != user_id,
                ChatMessage.is_read.is_(False),
            )
        )
        return {
            "data": {"project_id": project_id, "unread_count": count or 0},
            "message": "Unread count fetched successfully",
        }

    # ------------------------------------------------------------------
    # WebSocket: publish-only helper (called from router)
    # ------------------------------------------------------------------

    async def handle_ws_message(
        self,
        project_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text",
    ) -> dict:
        """Persist a message and publish it on the Redis channel. Returns the serialised payload."""
        msg = ChatMessage(
            project_id=project_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)

        sender = await self.db.get(User, sender_id)
        payload = self._serialize_message(msg, sender)

        await redis_client.publish(_channel(project_id), json.dumps(payload))
        return payload

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_message(msg: ChatMessage, sender: Optional[User]) -> dict:
        return {
            "id": str(msg.id),
            "project_id": str(msg.project_id),
            "sender_id": str(msg.sender_id),
            "content": msg.content,
            "message_type": msg.message_type,
            "is_read": msg.is_read,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
            "updated_at": msg.updated_at.isoformat() if msg.updated_at else None,
            "sender_first_name": sender.first_name if sender else None,
            "sender_last_name": sender.last_name if sender else None,
            "sender_image_url": sender.image_url if sender else None,
        }
