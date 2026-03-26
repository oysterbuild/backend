import asyncio
import json
from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    status,
    UploadFile,
    Form,
    File,
    HTTPException,
    Query,
)
from schemas.auth_schema import AllInspectorsSchema
from httpx import _status_codes
from schemas.inspectors_schema import InspectorCreationSetupDTO
from services.projects import ProjectSetupService
from utils.db_setup import get_database
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.auth import get_current_user
from utils.file_upload import upload_file_optimized
from typing import List, Optional, Literal
from datetime import datetime, timezone
from uuid import UUID
from utils.loggers import setup_logger
from services.inspector import InspectorService

router = APIRouter(prefix="/inspectors")
logger = setup_logger("project_inspectors")


def get_inspectors_service(db: AsyncSession = Depends(get_database)):
    return InspectorService(db=db)


# project service
def get_project_service(
    db: AsyncSession = Depends(get_database),
) -> ProjectSetupService:
    return ProjectSetupService(db=db)


@router.get("/projects")
async def get_inspector_project(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    project_status: Optional[
        Literal["Active", "Pending", "Draft", "Completed", "Cancelled"]
    ] = Query(None, description="Filter by project status"),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("id"))
    return await project_service.get_inspector_project(
        user_id=user_id,
        page=page,
        limit=limit,
        project_status=project_status,
    )


# This is admin Page this can be access by on Admin,i.e the route
@router.post("/{project_id}/assign/inspectors")
async def assign_inspectors(
    project_id: str,
    payload: InspectorCreationSetupDTO,
    inspector_service: InspectorService = Depends(get_inspectors_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("id"))
    dict_payload = payload.model_dump()
    dict_payload["project_id"] = project_id
    return await inspector_service.assign_inspector(dict_payload, user_id)


@router.get("/{project_id}/assigned/inspectors")
async def get_assigned_inspectors(
    project_id: str,
    inspector_service: InspectorService = Depends(get_inspectors_service),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    user_id = str(current_user.get("id"))
    return await inspector_service.get_assigned_project_inspector(
        project_id, user_id, page, limit
    )


@router.delete("/{inspector_id}/remove")
async def remove_assigned_inspector(
    inspector_id: str,
    inspector_service: InspectorService = Depends(get_inspectors_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("id"))
    return await inspector_service.remove_inspector(inspector_id, user_id)


# Get use that login as inspectors
@router.get("", response_model=AllInspectorsSchema)
async def get_inspectors(
    inspector_service: InspectorService = Depends(get_inspectors_service),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    user_id = str(current_user.get("id"))
    return await inspector_service.fetch_inspectors(user_id, page, limit)
