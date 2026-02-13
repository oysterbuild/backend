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
from httpx import _status_codes
from schemas.projects_schema import (
    ProjectSetupDto,
    SuccessResponse,
    ProjectSetupUpdateDto,
)
from schemas.report_schema import (
    ProjectReportRequest,
    ProjectReportResponse,
    UpdateProjectReportRequest,
)
from services.projects import ProjectSetupService
from utils.db_setup import get_database
from sqlalchemy.ext.asyncio import AsyncSession
from utils.db_setup import get_database
from dependencies.auth import get_current_user
from utils.file_upload import upload_file_optimized
from typing import List, Optional, Literal
from datetime import datetime, timezone
from uuid import UUID
from utils.loggers import setup_logger
from services.cloudinary_service import get_cloudinary, CloudinaryService

router = APIRouter(prefix="/projects")
logger = setup_logger("project_route")


# make singleton
def get_project_service(
    db: AsyncSession = Depends(get_database),
) -> ProjectSetupService:
    return ProjectSetupService(db=db)


# ----------------PROJECT CREATIONS ----------------


@router.post("", response_model=SuccessResponse)
async def create_project(
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
        },
        # ),
    ),
    images: List[UploadFile] = File([]),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    """
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
        "preferred_inspection_window": "Morning",
        "existing_image_ids": [
            "831277cc-36df-4140-ab19-18b8dac7a1df"
        ]
    }
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

            project = ProjectSetupDto(**data)
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

        created_project = await project_service.create_project(
            project_dict, current_user
        )
        logger.info(
            f"Project '{project.name}' created successfully by user {current_user.get('id')}"
        )

        return SuccessResponse(
            message="Project Created Successfully", data=created_project
        )

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.put("/{project_id}/update")
async def update_project(
    project_id: str,
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
            "existing_image_ids": ["image1_UUID", "image2_UUID"],
        },
        # ),
    ),
    images: List[UploadFile] = File([]),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))

        try:
            data = json.loads(project_data)
            logger.info("Project payload parsed successfully")

            if "start_date" in data:
                data["start_date"] = datetime.fromisoformat(data["start_date"]).date()
            if "end_date" in data:
                data["end_date"] = datetime.fromisoformat(data["end_date"]).date()

            dto = ProjectSetupUpdateDto(**data).model_dump()
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Payload -> {e}",
            )

        response = await project_service.update_project(
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


@router.delete("/{project_id}/delete")
async def delete_project(
    project_id: str,
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.delete_project(user_id, project_id)
        return response

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.get("")
async def projects(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    project_status: Optional[Literal["Active","Pending","Draft"]] = Query(None, description="Filter by project status"),
    project_service: "ProjectSetupService" = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.get_all_user_project(
            user_id=user_id, page=page, limit=limit, project_status=project_status
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


@router.get("/{project_id}/overview")
async def get_single_project(
    project_id: str,
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.get_single_project(user_id, project_id)
        return response

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


# ----------------END PROJECT CREATIONS ----------------


# ----------------START PROJECT REPORT ----------------
@router.get("/{project_id}/reports")
async def get_project_report(
    project_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.get_project_report(
            project_id, user_id, page, limit
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


@router.post("/{project_id}/reports")
async def create_report(
    project_id: str,
    report_data: ProjectReportRequest,
    # str = Form(
    #     ...,
    #     description="JSON payload for report data",
    #     json_schema_extra={
    #         "title": "Foundation Work Progress Report",
    #         "report_type": "Technical",
    #         "report_date": "2026-02-10",
    #         "description": "Foundation excavation and concrete pouring have been completed. Structural integrity tests passed and curing is ongoing.",
    #         "progress_percent": 35.5,
    #         "recommendation": "Lagos, Nigeria",
    #         "approval_required": True,
    #         "approved": False,
    #     },
    #     # ),
    # ),
    # images: List[UploadFile] = File([]),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    logger.info(f"User {current_user.get('id')} started creating a project")

    try:
        # Parse JSON
        # try:
        #     data = json.loads(report_data)
        #     logger.info("Project payload parsed successfully")

        #     if "report_date" in data:
        #         data["report_date"] = datetime.fromisoformat(data["report_date"]).date()

        #     if data["approval_required"]:
        #         data["approved"] = True

        #     project = ProjectReportRequest(**data)
        # except Exception as e:
        #     logger.error(f"JSON parsing failed: {e}")
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Invalid Payload -> {e}",
        #     )

        # # Combine project data with uploaded image URLs
        report_data = report_data.dict()
        # project_dict["images"] = images

        if report_data["approval_required"]:
            report_data["approved"] = True

        created_project = await project_service.create_project_report(
            report_data, project_id, current_user
        )
        logger.info(f"Project created successfully by user {current_user.get('id')}")

        return SuccessResponse(
            message="Report Created Successfully", data=created_project
        )

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.put("/{project_id}/reports/{report_id}")
async def update_report(
    project_id: str,
    report_id: str,
    report_data: UpdateProjectReportRequest,
    # str = Form(
    #     ...,
    #     description="JSON payload for report data",
    #     json_schema_extra={
    #         "title": "Weekly Site Progress Report",
    #         "report_type": "Milestone Completion",
    #         "report_date": "2026-01-27",
    #         "description": "Foundation work has been completed. Column casting is in progress.",
    #         "progress_percent": 85.5,
    #         "recommendation": [
    #             "Increase workforce to meet deadline",
    #             "Approve additional cement supply",
    #             "Schedule structural inspection",
    #         ],
    #         "approval_required": True,
    #         "approved": False,
    #         "existing_image_ids": [
    #             "bec167e4-d81d-4458-bb10-ab485b4986aa",
    #             "cd657a65-38be-48b0-96af-dcd640e24d0c",
    #         ],
    #     },
    #     # ),
    # ),
    # images: List[UploadFile] = File([]),
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    logger.info(f"User {current_user.get('id')} started creating a project")

    try:
        # Parse JSON
        user_id = str(current_user.get("id"))
        # try:

        #     data = json.loads(report_data)
        #     logger.info("Project payload parsed successfully")

        #     if "report_date" in data:
        #         data["report_date"] = datetime.fromisoformat(data["report_date"]).date()

        #     if data["approval_required"]:
        #         data["approved"] = True

        #     project = UpdateProjectReportRequest(**data)
        # except Exception as e:
        #     logger.error(f"JSON parsing failed: {e}")
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail=f"Invalid Payload -> {e}",
        #     )

        # Combine project data with uploaded image URLs
        report_dict = report_data.dict()
        # report_dict["images"] = images
        images = report_dict.pop("images")

        if report_dict["approval_required"]:
            report_dict["approved"] = True

        created_project = await project_service.updates_project_report(
            project_id, report_id, user_id, report_dict, images, current_user
        )
        logger.info(f"Project created successfully by user {current_user.get('id')}")

        return created_project

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.get("/{project_id}/reports/{report_id}")
async def get_single_report(
    project_id: str,
    report_id: str,
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.get_single_report(
            project_id, user_id, report_id
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


@router.delete("/{project_id}/reports/{report_id}")
async def delete_single_report(
    project_id: str,
    report_id: str,
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.delete_project_report(
            project_id, user_id, report_id
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


@router.get("/reports/upload/presigned-url")
async def generate_presigned_url(
    cloud_service: CloudinaryService = Depends(get_cloudinary),
):
    try:
        # DEFAULT TO REPORT
        folder_name = "REPORTS"
        presigned_data = await cloud_service.get_presigned_upload_params(
            folder=folder_name
        )
        return presigned_data

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


# ----------------PROJECT PAYMENT -----------------
@router.get("/{project_id}/payment/history")
async def get_subscriptions(
    project_id: str,
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.payments_history(project_id, user_id)
        # Get all subscription payments:
        return response
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.get("/{project_id}/payment/{payment_id}/history")
async def get_single_subscriptions(
    project_id: str,
    payment_id: str,
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))
        response = await project_service.single_payments_history(
            project_id, user_id, payment_id
        )
        # Get all subscription payments:
        return response
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )


@router.put("/{project_id}/plan/{plan_id}/upgrade")
async def update_subscriptions(
    project_id: str,
    plan_id: str,
    project_service: ProjectSetupService = Depends(get_project_service),
    current_user: dict = Depends(get_current_user),
):
    try:
        user_id = str(current_user.get("id"))

        response = await project_service.update_subscription_plan(
            project_id, user_id, plan_id
        )
        # Get all subscription payments:
        return response

    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )
