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


router = APIRouter(prefix="/admin")
logger = setup_logger("admin")


# project service
def get_project_service(
    db: AsyncSession = Depends(get_database),
) -> ProjectSetupService:
    return ProjectSetupService(db=db)


@router.get("/all-projects")
async def get_all_project(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    project_status: Optional[
        Literal[
            "Active",
            "Pending",
            "Draft",
            "Completed",
            "Cancelled",
            "Awaiting_Payment",
            "Paid",
            "Expired",
        ]
    ] = Query(None, description="Filter by project status"),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("id"))
    logger.info(
        f"admin get_all_project user_id={user_id} page={page} limit={limit} project_status={project_status}"
    )
    try:
        return await project_service.get_all_project(
            user_id=user_id,
            page=page,
            limit=limit,
            project_status=project_status,
        )
    except HTTPException as e:
        logger.error(f"admin get_all_project HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"admin get_all_project failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.get("/project/{project_id}/analytics")
async def get_project_analytics(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    project_service: ProjectSetupService = Depends(get_project_service),
):

    user_id = str(current_user.get("id"))
    return await project_service.get_project_analytics(
        user_id=user_id, project_id=project_id
    )


@router.get("/project/analytics")
async def get_all_project_analytics(
    current_user: dict = Depends(get_current_user),
    project_service: ProjectSetupService = Depends(get_project_service),
):
    user_id = str(current_user.get("id"))
    logger.info(f"admin get_all_project_analytics user_id={user_id}")
    try:
        return await project_service.get_all_project_analytics(
            user_id=user_id,
        )
    except HTTPException as e:
        logger.error(f"admin get_all_project_analytics HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"admin get_all_project_analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.put("/project/{project_id}/update-status")
async def update_project_status(
    project_id: str,
    project_status: Literal[
        "Completed", "Cancelled", "Pending", "Active", "Draft"
    ] = Query(..., description="Project_status"),
    current_user: dict = Depends(get_current_user),
    project_service: ProjectSetupService = Depends(get_project_service),
):
    user_id = str(current_user.get("id"))
    logger.info(
        f"admin update_project_status user_id={user_id} project_id={project_id} new_status={project_status}"
    )
    try:
        return await project_service.update_project_status(
            user_id=user_id, project_id=project_id, project_status=project_status
        )
    except HTTPException as e:
        logger.error(f"admin update_project_status HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"admin update_project_status failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )
