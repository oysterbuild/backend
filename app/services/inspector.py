from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status
from models.project_members import ProjectMember
from models.users import User
from utils.loggers import setup_logger
from utils.pagination import normalize_pagination

logger = setup_logger("Inspector_Service")


class InspectorService:
    """Project inspector assignment and listing (routes unchanged; only service API is renamed)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_assigned_inspectors(
        self, project_id: str, user_id: str, page: int = 1, limit: int = 10
    ):
        page, limit, offset = normalize_pagination(page, limit)

        query = (
            select(ProjectMember, User)
            .join(User, ProjectMember.user_id == User.id)
            .where(ProjectMember.project_id == project_id)
        )

        result = await self.db.execute(
            query.order_by(ProjectMember.joined_at.desc()).offset(offset).limit(limit)
        )

        rows = result.all()

        users_data = [
            {
                "inspection_id": str(project_member.id),
                "id": str(user.id),
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "image_url": user.image_url,
            }
            for project_member, user in rows
        ]

        count_stmt = (
            select(func.count())
            .select_from(ProjectMember)
            .where(ProjectMember.project_id == project_id)
        )

        total = await self.db.scalar(count_stmt)
        return {
            "meta_data": {"limit": limit, "page": page, "total": total},
            "data": users_data,
            "message": "Project Inspector Fetched Successfully",
        }

    async def assign_inspector_to_project(self, payload: dict, user_id: str):
        try:
            notify_me = payload.pop("notify_me")
            project_member_instance = ProjectMember(**payload)
            self.db.add(project_member_instance)
            await self.db.commit()
            await self.db.refresh(project_member_instance)

            if notify_me:
                pass

            return {
                "data": project_member_instance,
                "message": "Project Inspector Saved Successfully",
            }
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"assign_inspector_to_project failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while assigning the inspector.",
            ) from e

    async def list_inspectors(self, user_id: str, page: int, limit: int):
        page, limit, offset = normalize_pagination(page, limit)

        stmt_inspectors = (
            select(User).where(User.role == "INSPECTOR").offset(offset).limit(limit)
        )
        result = (await self.db.execute(stmt_inspectors)).scalars().all()
        return {
            "data": result,
            "message": "Inspectors Fetched Successfully",
        }

    async def remove_project_inspector(
        self, project_member_id: str, user_id: str
    ):
        """Remove a project member row. ``project_member_id`` is ``ProjectMember.id`` (path param is still named inspector_id on the router)."""
        try:
            result = await self.db.execute(
                select(ProjectMember).where(ProjectMember.id == project_member_id)
            )

            project_member_instance = result.scalar_one_or_none()

            if not project_member_instance:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Inspector not found",
                )
            await self.db.delete(project_member_instance)
            await self.db.commit()

            return {
                "data": None,
                "message": "Project Inspector Removed Successfully",
            }
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"remove_project_inspector failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while removing the inspector.",
            ) from e
