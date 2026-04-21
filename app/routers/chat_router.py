from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_current_user
from models.building_project import BuildingProject
from models.project_members import ProjectMember
from models.users import User
from schemas.chat_schema import ChatHistoryResponse, SendMessageDTO, UnreadCountResponse
from services.chat_service import ChatService, _channel
from settings import get_settings
from utils.db_setup import AsyncSessionLocal, get_database
from utils.loggers import setup_logger
from utils.redis_client import redis_client

router = APIRouter(prefix="/chat")
settings = get_settings()
logger = setup_logger("ChatRouter")


def get_chat_service(db: AsyncSession = Depends(get_database)) -> ChatService:
    return ChatService(db=db)


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------


@router.post("/{project_id}/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    project_id: str,
    payload: SendMessageDTO,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: dict = Depends(get_current_user),
):
    """Send a message to a project chat (HTTP fallback / REST clients)."""
    return await chat_service.send_message(
        project_id=project_id,
        sender_id=str(current_user["id"]),
        content=payload.content,
        message_type=payload.message_type,
    )


@router.get("/{project_id}/messages")
async def get_messages(
    project_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    before: Optional[datetime] = Query(
        None, description="Cursor: fetch messages created before this ISO timestamp"
    ),
    chat_service: ChatService = Depends(get_chat_service),
    current_user: dict = Depends(get_current_user),
):
    """Paginated message history for a project chat."""
    return await chat_service.get_project_messages(
        project_id=project_id,
        user_id=str(current_user["id"]),
        page=page,
        limit=limit,
        before=before,
    )


@router.patch("/{project_id}/messages/read")
async def mark_as_read(
    project_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: dict = Depends(get_current_user),
):
    """Mark all unread messages in the project as read for the current user."""
    return await chat_service.mark_as_read(
        project_id=project_id,
        user_id=str(current_user["id"]),
    )


@router.get("/{project_id}/messages/unread")
async def unread_count(
    project_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: dict = Depends(get_current_user),
):
    """Get the number of unread messages for the current user in this project."""
    return await chat_service.get_unread_count(
        project_id=project_id,
        user_id=str(current_user["id"]),
    )


# ---------------------------------------------------------------------------
# WebSocket helpers
# ---------------------------------------------------------------------------


async def _authenticate_ws(token: str, db: AsyncSession) -> dict:
    """Decode JWT and return the user dict, or raise WebSocketDisconnect on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise ValueError("no sub")

        user = await db.get(User, user_id)
        if not user:
            raise ValueError("user not found")

        return {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "image_url": user.image_url,
        }
    except (ExpiredSignatureError, PyJWTError, ValueError) as exc:
        raise WebSocketDisconnect(code=4001, reason="Unauthorized") from exc


async def _assert_ws_participant(
    project_id: str, user_id: str, db: AsyncSession
) -> None:
    """Close connection if user is not the project owner or an active member."""
    project = await db.scalar(
        select(BuildingProject).where(BuildingProject.id == project_id)
    )
    if not project:
        raise WebSocketDisconnect(code=4004, reason="Project not found")

    is_owner = str(project.owner_id) == user_id
    if not is_owner:
        member = await db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active.is_(True),
            )
        )
        if not member:
            raise WebSocketDisconnect(code=4003, reason="Forbidden")


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@router.websocket("/{project_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    project_id: str,
    token: str = Query(..., description="JWT access token"),
):
    """
    Real-time chat via WebSocket + Redis Pub/Sub.

    Connect: `ws://<host>/api/v1/chat/{project_id}/ws?token=<JWT>`

    Incoming frame (JSON):
        { "content": "Hello!", "message_type": "text" }

    Outgoing frame (JSON):
        { "id": "...", "project_id": "...", "sender_id": "...",
          "content": "...", "message_type": "text", "is_read": false,
          "created_at": "...", "sender_first_name": "...", ... }
    """
    await websocket.accept()

    # Short-lived DB session for handshake only. Holding a session for the entire
    # WebSocket lifetime exhausts the SQLAlchemy pool and breaks HTTP endpoints.
    async with AsyncSessionLocal() as db:
        try:
            current_user = await _authenticate_ws(token, db)
        except WebSocketDisconnect as exc:
            await websocket.close(code=exc.code, reason=exc.reason)
            return

        try:
            await _assert_ws_participant(project_id, current_user["id"], db)
        except WebSocketDisconnect as exc:
            await websocket.close(code=exc.code, reason=exc.reason)
            return

    channel = _channel(project_id)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    async def _receive_from_client() -> None:
        """Read frames from the WebSocket, persist and publish to Redis."""
        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_json({"error": "Invalid JSON", "detail": raw})
                    continue

                content = data.get("content", "").strip()
                if not content:
                    await websocket.send_json({"error": "Empty message"})
                    continue

                message_type = data.get("message_type", "text")
                if message_type not in ("text", "image", "file"):
                    message_type = "text"

                async with AsyncSessionLocal() as db:
                    chat_svc = ChatService(db=db)
                    await chat_svc.handle_ws_message(
                        project_id=project_id,
                        sender_id=current_user["id"],
                        content=content,
                        message_type=message_type,
                    )
        except WebSocketDisconnect:
            pass

    async def _broadcast_from_redis() -> None:
        """Forward Redis Pub/Sub messages to the WebSocket client."""
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await websocket.send_text(message["data"])
        except Exception:
            pass

    try:
        await asyncio.gather(
            _receive_from_client(),
            _broadcast_from_redis(),
            return_exceptions=False,
        )
    except Exception as exc:
        logger.warning(f"WS session ended for project {project_id}: {exc}")
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        try:
            await websocket.close()
        except Exception:
            pass
