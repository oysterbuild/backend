from typing import Literal
from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    Query,
    status,
    UploadFile,
    Form,
    File,
    HTTPException,
)
from httpx import _status_codes

from services.permission_service import PermissionService
from utils.db_setup import get_database
from sqlalchemy.ext.asyncio import AsyncSession
from utils.db_setup import get_database
from dependencies.auth import get_current_user
from utils.file_upload import upload_file_optimized

router = APIRouter(prefix="/core")


# make singleton
def get_perm_service(db: AsyncSession = Depends(get_database)) -> PermissionService:
    return PermissionService(db_session=db)


@router.get("/roles")
async def roles(
    permission_service: PermissionService = Depends(get_perm_service),
):
    result = await permission_service.get_roles()
    return result
