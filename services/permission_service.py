from ast import Tuple
from models.core import Role, Permission, RolePermission
from models.project_members import ProjectMember
from constant import permissions as app_permissions
from sqlalchemy.ext.asyncio import AsyncSession
from utils.db_setup import get_database
from fastapi import Depends, HTTPException, status
from sqlalchemy import select, delete, exc
from constant.roles_permissions import default_role_permissions
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.loggers import setup_logger
from typing import Optional
from uuid import UUID
from models.users import User

logger = setup_logger("Load_Permission")


class PermissionService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ---------------------------------------------------------
    async def add_roles(self) -> None:
        """Seed default roles"""
        logger.info("🔹 Seeding roles")

        for item in default_role_permissions:
            stmt = select(Role).where(Role.name == item["role"])
            role = await self.db.scalar(stmt)

            if role:
                continue

            self.db.add(
                Role(
                    name=item["role"],
                    description=item["description"],
                )
            )
            logger.info(f"✅ Role created: {item['role']}")

        await self.db.commit()

    # ---------------------------------------------------------
    async def add_permissions(self) -> None:
        """Seed application permissions"""
        logger.info("🔹 Seeding permissions")

        app_permissions_ = app_permissions.__dict__
        for perm in filter(lambda k: k[0] != "_", app_permissions_.keys()):
            print(perm)
            stmt = select(Permission).where(Permission.name == perm)
            permission = await self.db.scalar(stmt)

            if permission:
                continue

            self.db.add(
                Permission(
                    name=perm,
                    description="",
                )
            )
            logger.info(f"✅ Permission created: {perm}")

        await self.db.commit()

    # ---------------------------------------------------------
    async def add_role_permissions(self) -> None:
        """
        Seed role-permission mappings.
        Safe to run multiple times.
        """
        logger.info("🔹 Seeding role-permission mappings")

        for item in default_role_permissions:
            role_stmt = select(Role).where(Role.name == item["role"])
            role = await self.db.scalar(role_stmt)

            if not role:
                logger.warning(f"⚠️ Role not found: {item['role']}")
                continue

            for perm_enum in item["permissions"]:
                perm_stmt = select(Permission).where(Permission.name == perm_enum)
                permission = await self.db.scalar(perm_stmt)

                if not permission:
                    logger.warning(f"⚠️ Permission not found: {perm_enum}")
                    continue

                rp_stmt = select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
                exists = await self.db.scalar(rp_stmt)

                if exists:
                    continue

                self.db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )

                logger.info(f"🔗 Linked {role.name} → {permission.name}")

        await self.db.commit()
        logger.info("✅ Role-permission seeding completed")

    async def clear_all(self):
        # Delete all RolePermission mappings first (to avoid FK issues)
        await self.db.execute(delete(RolePermission))

        # Delete all permissions
        await self.db.execute(delete(Permission))

        # Delete all roles
        await self.db.execute(delete(Role))

        # Commit the transaction
        await self.db.commit()

    # ---------------------------------------------------------
    async def run_all(self) -> None:
        """Convenience runner"""
        await self.add_roles()
        await self.add_permissions()
        await self.add_role_permissions()

    async def is_system_admin(self, user_id: UUID):
        try:
            user = await self.db.get(User, user_id)
            if user_id and user.role == "SUPER_ADMIN":
                return True
            return False
        except Exception as e:
            raise e

    # super admin:
    async def has_project_permission(
        self,
        user_id: str,
        project_id: str,
        permission_name: str,
    ):
        try:
            # 1. System user → allow
            if await self.is_system_admin(user_id):
                return True

            # 2. Find project membership
            stmt = (
                select(Permission.id)
                .join(RolePermission, Permission.id == RolePermission.permission_id)
                .join(Role, Role.id == RolePermission.role_id)
                .join(ProjectMember, ProjectMember.role_id == Role.id)
                .where(
                    ProjectMember.user_id == user_id,
                    ProjectMember.project_id == project_id,
                    ProjectMember.is_active.is_(True),
                    Permission.name == permission_name,
                )
            )

            result = await self.db.execute(stmt)
            return result.first() is not None
        except Exception as e:
            raise e

    async def get_roles(self):
        try:
            perm_stmt = select(Role).where(Role.name != "PROJECT_OWNER")

            result = (await self.db.execute(perm_stmt)).scalars().all()
            return {"data": result, "message": "Role Fetched Successfully"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error {e}",
            )


# -----------------------------
# Runner function
# -----------------------------
async def seed_roles_permissions():
    """
    Seed roles, permissions, and role-permissions safely on app startup
    """
    # Use the DB session async generator
    async for db in get_database():
        loader = PermissionService(db_session=db)
        try:
            logger.info("🔹 Starting role & permission seeding")
            await loader.run_all()
            # await loader.clear_all()
            logger.info("Role & permission seeding completed successfully")
        except Exception as e:
            logger.error(f"Error seeding roles/permissions: {e}")
            await db.rollback()  # rollback on error
        finally:
            await db.close()  # ensure session is closed
            logger.info("DB session closed")
