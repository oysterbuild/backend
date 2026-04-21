from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_current_user
from schemas.auth_schema import AllInspectorsSchema
from schemas.inspectors_schema import InspectorCreationSetupDTO
from services.inspector import InspectorService
from services.projects import ProjectSetupService
from utils.db_setup import get_database

router = APIRouter(prefix="/inspectors")


def get_inspectors_service(db: AsyncSession = Depends(get_database)) -> InspectorService:
    return InspectorService(db=db)


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
    return await inspector_service.assign_inspector_to_project(dict_payload, user_id)


@router.get("/{project_id}/assigned/inspectors")
async def get_assigned_inspectors(
    project_id: str,
    inspector_service: InspectorService = Depends(get_inspectors_service),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    user_id = str(current_user.get("id"))
    return await inspector_service.list_assigned_inspectors(
        project_id, user_id, page, limit
    )


@router.delete("/{inspector_id}/remove")
async def remove_assigned_inspector(
    inspector_id: str,
    inspector_service: InspectorService = Depends(get_inspectors_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("id"))
    return await inspector_service.remove_project_inspector(inspector_id, user_id)


@router.get("", response_model=AllInspectorsSchema)
async def get_inspectors(
    inspector_service: InspectorService = Depends(get_inspectors_service),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    user_id = str(current_user.get("id"))
    return await inspector_service.list_inspectors(user_id, page, limit)
