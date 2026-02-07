from sqlalchemy import Column, Integer, String, Table, ForeignKey, UUID
from .base_model import BaseModel


# ---------------------------
# Roles table
# ---------------------------
class Role(BaseModel):
    name = Column(
        String(50), unique=True, nullable=False, index=True
    )  # super_admin, organization_admin, etc.
    description = Column(String(500), nullable=True, default="")


# ---------------------------
# Permissions table
# ---------------------------
class Permission(BaseModel):
    name = Column(String(100), unique=True, nullable=False)  # e.g., CAN_MANAGE_PROJECT
    description = Column(String(500), nullable=True, default="")


# ---------------------------
# Role-Permissions junction table (many-to-many)
# ---------------------------
class RolePermission(BaseModel):
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey("permission.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
