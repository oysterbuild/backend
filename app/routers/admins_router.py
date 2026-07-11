from typing import Literal, Optional
import json
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from dependencies.auth import get_current_user
from services.projects import ProjectSetupService
from services.auth_service import AuthService
from utils.db_setup import get_database
from utils.loggers import setup_logger
from utils.file_upload import upload_file_optimized
from datetime import datetime, timezone
from schemas.projects_schema import (
    ProjectSetupWithAssigneeDto,
    SuccessResponse,
    ProjectAssignUpdateDto,
)
from typing import List, Optional, Literal


router = APIRouter(prefix="/admin")
logger = setup_logger("admin")


def get_project_service(
    db: AsyncSession = Depends(get_database),
) -> ProjectSetupService:
    return ProjectSetupService(db=db)


def get_user_service(db: AsyncSession = Depends(get_database)) -> AuthService:
    return AuthService(database=db)


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
    logger.info(
        f"admin get_project_analytics user_id={user_id} project_id={project_id}"
    )
    try:
        return await project_service.get_project_analytics(
            user_id=user_id, project_id=project_id
        )
    except HTTPException as e:
        logger.error(f"admin get_project_analytics HTTP error: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"admin get_project_analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
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


# admin view all customers
@router.get("/fetch-users")
async def get_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    user_service: AuthService = Depends(get_user_service),
):
    try:
        user_id = str(current_user.get("id") or current_user.get("user_id"))
        return await user_service.get_all_users(user_id, page, limit)

    except HTTPException as e:
        logger.error("Admin failed to fetch users | detail=%s", e.detail)
        raise e

    except Exception as e:
        logger.exception("Admin failed to fetch users | user_id=%s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )


@router.post("/create-project")
async def admin_create_project(
    project_data: str = Form(
        ...,
        description="JSON payload for project data",
        json_schema_extra={
            "name": "Project A",
            "description": "Detailed project",
            "project_type": "Residential",
            "location_text": "Lagos",
            "location_map": "https://maps.google.com/...",
            "start_date": "2026-01-25T10:00:00",
            "end_date": "2026-02-25T10:00:00",
            "budget": 500000,
            "budget_currency": "NGN",
            "status": "Active",
            "plan_id": "c56a4180-65aa-42ec-a945-5fd21dec0538",
            "preferred_inspection_days": ["Monday", "Wednesday"],
            "preferred_inspection_window": "Morning",
            "assignee_user_id": "174b1898-da04-4e06-afbb-9f63380b7e36",
        },
        # ),
    ),
    images: List[UploadFile] = File([]),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a project with a JSON payload and multiple images.

    **Required JSON Payload Structure for `project_data` field:**
    ```json
    args={
        "name": "Project A",
        "description": "Detailed project",
        "project_type": "Residential",
        "location_text": "Lagos",
        "location_map": "https://maps.google.com/...",
        "start_date": "2026-02-10",
        "end_date": "2026-02-25",
        "budget": 3000000,
        "budget_currency": "USD",
        "status": "Active",
        "plan_id": "174b1898-da04-4e06-af3b-9f63380b7e36",
        "preferred_inspection_days": [
            "Monday",
            "Wednesday"
        ],
        "floor_number":1,
        "preferred_inspection_window": "Morning",
        "assignee_user_id:"174b1898-da04-4e06-afbb-9f63380b7e36"
    }
    ```
    """
    logger.info(f"User {current_user.get('id')} started creating a project")
    try:
        # Parse JSON
        try:
            data = json.loads(project_data)
            logger.info("Project payload parsed successfully")

            if "start_date" in data:
                data["start_date"] = datetime.fromisoformat(data["start_date"]).date()
            if "end_date" in data:
                data["end_date"] = datetime.fromisoformat(data["end_date"]).date()

            project = ProjectSetupWithAssigneeDto(**data)
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Payload -> {e}",
            )

        # Upload all images concurrently
        uploaded_image_urls = await asyncio.gather(
            *(
                upload_file_optimized(
                    img,
                    "project_image",
                    str(current_user.get("id")),
                    current_user,
                    "PROJECT",
                )
                for img in images
            )
        )

        # Combine project data with uploaded image URLs
        project_dict = project.dict()
        project_dict["images"] = uploaded_image_urls

        created_project = await project_service.admin_create_project(
            project_dict, current_user
        )
        logger.info(
            f"Project '{project.name}' created successfully by user {current_user.get('id')}"
        )

        return SuccessResponse(
            message="Project Created Successfully", data=created_project
        )
    except HTTPException as e:
        logger.error("Admin failed to fetch users | detail=%s", e.detail)
        raise e

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.put("/project/{project_id}/update")
async def update_project(
    project_id: str,
    project_data: str = Form(
        ...,
        description="JSON payload for project data",
    ),
    images: List[UploadFile] = File([]),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a project with a JSON payload and multiple images.

    **Required JSON Payload Structure for `project_data` field:**
    ```json
    {
        "name": "Project A",
        "description": "Detailed project",
        "project_type": "Residential",
        "location_text": "Lagos",
        "location_map": "https://maps.google.com/...",
        "start_date": "2026-01-25T10:00:00",
        "end_date": "2026-02-25T10:00:00",
        "budget": 500000,
        "budget_currency": "NGN",
        "status": "Active",
        "plan_id": "c56a4180-65aa-42ec-a945-5fd21dec0538",
        "preferred_inspection_days": ["Monday", "Wednesday"],
        "preferred_inspection_window": "Morning",
        "existing_image_ids": ["uuid1", "uuid2"],
        "floor_number":1
        "assignee_user_id:"174b1898-da04-4e06-afbb-9f63380b7e36"
    }
    ```
    """
    try:
        user_id = str(current_user.get("id"))

        try:
            data = json.loads(project_data)
            logger.info("Project payload parsed successfully")

            if "start_date" in data:
                data["start_date"] = datetime.fromisoformat(data["start_date"]).date()
            if "end_date" in data:
                data["end_date"] = datetime.fromisoformat(data["end_date"]).date()

            dto = ProjectAssignUpdateDto(**data).model_dump()
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Payload -> {e}",
            )

        response = await project_service.admin_update_project(
            user_id,
            project_id,
            project_dto=dto,
            images=images,
            current_user=current_user,
        )
        return response
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )
