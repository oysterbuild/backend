import asyncio
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession

from models.project_members import ProjectMember
from utils.loggers import setup_logger
from models.users import User
from fastapi import HTTPException, status
from models.core import Role
from sqlalchemy import select, func, exists, update, and_
from constant.roles import PROJECT_OWNER
from constant.permissions import (
    CAN_MANAGE_PROJECT,
    CAN_VIEW_PROJECT,
    CAN_MANAGE_REPORT,
    CAN_VIEW_REPORT,
    CAN_EXPORT_REPORT,
    CAN_SUBMIT_UPDATE,
    CAN_MANAGE_UPDATE,
    CAN_MANAGE_FILES,
    CAN_MANAGE_PROJECT_PAYMENT,
    CAN_VIEW_PROJECT_PAYMENT,
)
from models.users import User
from services.email_service import get_email_service

logger = setup_logger("Inspector_Service")


class InspectorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_assigned_project_inspector(
        self, project_id: str, user_id: str, page: int = 1, limit: int = 10
    ):
        # check the permission of the person assigning
        try:
            # check the intiator permission
            page = max(page, 1)
            limit = min(limit, 100)
            offset = (page - 1) * limit

            query = (
                select(ProjectMember, User)
                .join(User, ProjectMember.user_id == User.id)
                .where(ProjectMember.project_id == project_id)
            )

            result = await self.db.execute(
                query.order_by(ProjectMember.joined_at.desc())
                .offset(offset)
                .limit(limit)
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
        except HTTPException as http_exc:
            raise http_exc

        except Exception as e:
            raise e

    async def assign_inspector(self, payload: dict, user_id: str):
        try:
            # check permission again:
            notify_me = payload.pop("notify_me")
            project_member_instance = ProjectMember(**payload)
            self.db.add(project_member_instance)
            await self.db.commit()
            await self.db.refresh(project_member_instance)

            # trigger_send email to the user:
            if notify_me:
                pass

            return {
                "data": project_member_instance,
                "message": "Project Inspector Saved Successfully",
            }
        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc

        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PROJECT_UPDATE] Critical Error: {str(e)}", exc_info=True)
            raise Exception(f"An error occurred while updating the project: {str(e)}")

    async def fetch_inspectors(self, user_id: str, page: int, limit: int):
        try:
            page = max(page, 1)
            limit = min(limit, 100)
            offset = (page - 1) * limit
            # check permissions
            stmt_inspectors = (
                select(User).where(User.role == "INSPECTOR").offset(offset).limit(limit)
            )
            result = (await self.db.execute(stmt_inspectors)).scalars().all()
            return {
                "data": result,
                "message": "Inspectors Fetched Successfully",
            }
        except HTTPException as http_exc:
            raise http_exc

        except Exception as e:
            raise e

    async def remove_inspector(self, inspector_id: str, user_id: str):
        try:
            # check permission again:
            result = await self.db.execute(
                select(ProjectMember).where(ProjectMember.id == inspector_id)
            )

            project_member_instance = result.scalar_one_or_none()

            if not project_member_instance:
                raise HTTPException(status=404, detail="Inspector not found")
            await self.db.delete(project_member_instance)
            await self.db.commit()

            return {
                "data": None,
                "message": "Project Inspector Removed Successfully",
            }
        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc

        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PROJECT_UPDATE] Critical Error: {str(e)}", exc_info=True)
            raise Exception(f"An error occurred while updating the project: {str(e)}")
