import asyncio
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession
from models.building_project import BuildingProject
from models.project_members import ProjectMember
from utils.loggers import setup_logger
from services.upload_service import UploadMedia
from schemas.projects_schema import ProjectResponse
from services.plan_usage_service import ProjectPlanUsageService
from fastapi import HTTPException, status
from models.core import Role
from sqlalchemy import select, func, exists, update
from constant.roles import PROJECT_OWNER
from models.project_report import ProjectReport
from schemas.report_schema import ProjectReportRequest, ProjectReportResponse
from utils.file_upload import upload_file_optimized
from services.permission_service import PermissionService
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
from models.plans import PaymentHistory, Plan
from services.payment_services import PaymentService
from models.payments import Invoice
from models.media_upload import ProjectUpload, ReportUpload
from datetime import datetime,timezone,timedelta
from models.users import User
from services.email_service import get_email_service

logger = setup_logger("Project_Service")


class ProjectSetupService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.media_upload = UploadMedia(db=db)
        self.package_useage = ProjectPlanUsageService(db=db)
        self.organization_admin = PROJECT_OWNER
        self.permission = "Insufficient permission to complete the action"
        self.perms_role = PermissionService(db)
        self.payment_service = PaymentService(db)

    async def create_project(self, project_payload: dict, current_user: dict):
        """Initializes a new project, assigns ownership, handles media, and generates an invoice."""
        user_id = current_user.get("id")
        try:
            logger.info(f"[PROJECT_CREATE] Start: User {user_id} creating new project")

            # 1. Extract and Clean Data
            images = project_payload.pop("images", [])
            project_payload["owner_id"] = user_id

            # Enum to String Conversion
            for key in ["preferred_inspection_days", "preferred_inspection_window"]:
                if key in project_payload:
                    val = project_payload[key]
                    project_payload[key] = (
                        [d.value if hasattr(d, "value") else str(d) for d in val]
                        if isinstance(val, list)
                        else (val.value if hasattr(val, "value") else str(val))
                    )

            plan_id = str(project_payload.pop("plan_id"))

            # 2. Create Project Instance
            project = BuildingProject(**project_payload)
            self.db.add(project)
            await self.db.flush()
            await self.db.refresh(project)
            logger.info(f"[PROJECT_CREATE] Base record created: ID {project.id}")

            # 3. Assign Owner Role
            role_stmt = select(Role.id).where(Role.name == self.organization_admin)
            role_id = (await self.db.execute(role_stmt)).scalar_one_or_none()

            project_owner = ProjectMember(
                project_id=project.id,
                user_id=user_id,
                role_id=role_id,
            )
            self.db.add(project_owner)
            await self.db.flush()

            # 4. Handle Media
            if images:
                logger.info(
                    f"[PROJECT_CREATE] Uploading {len(images)} images for Project {project.id}"
                )
                await self.media_upload.upload_project_media(
                    project_id=project.id, images=images
                )

            # 5. Generate Payment Invoice
            invoice_resp = await self.payment_service.generate_payment_invoice(
                project.id, plan_id, project
            )

            await self.db.commit()
            await self.db.refresh(project)

            project_resp = ProjectResponse.model_validate(project).model_dump()
            project_resp["invoice_id"] = invoice_resp.invoice_id

            logger.info(
                f"[PROJECT_CREATE] Success: Project {project.id} is fully setup"
            )
            return project_resp

        except HTTPException as http_exec:
            raise http_exec

        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PROJECT_CREATE] Critical Failure: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create project: {str(e)}")

    async def get_all_user_project(
        self,
        user_id: str,
        page: int = 1,
        limit: int = 10,
        project_status: str | None = None,
    ):
        """Fetches a paginated list of projects associated with the user."""
        try:
            logger.info(
                f"[PROJECT_LIST] Fetching projects for User {user_id} (Page {page})"
            )

            page = max(page, 1)
            limit = min(limit, 100)
            offset = (page - 1) * limit

            # Filter by membership
            subquery = select(ProjectMember.project_id).where(
                ProjectMember.user_id == user_id
            )

            stmt = select(BuildingProject).where(BuildingProject.id.in_(subquery))

            if project_status:
                stmt = stmt.where(BuildingProject.status == project_status)

            # Execution
            result = await self.db.execute(
                stmt.order_by(BuildingProject.created_at.desc())
                .offset(offset)
                .limit(limit)
            )

            # Count total for meta_data
            count_stmt = (
                select(func.count())
                .select_from(BuildingProject)
                .where(BuildingProject.id.in_(subquery))
            )

            if project_status:
                count_stmt = count_stmt.where(BuildingProject.status == project_status)

            total = await self.db.scalar(count_stmt)  # total count scale

            projects = result.scalars().all()
            # -------------------------
            # Get images for projects
            # -------------------------
            project_ids = [p.id for p in projects]

            image_stmt = (
                select(ProjectUpload)
                .where(ProjectUpload.project_id.in_(project_ids))
                .order_by(ProjectUpload.uploaded_at.asc())
            )

            image_result = await self.db.execute(image_stmt)
            images = image_result.scalars().all()

            # group max 2 images per project
            project_image_map = {}
            for img in images:
                pid = img.project_id
                if pid not in project_image_map:
                    project_image_map[pid] = []

                if len(project_image_map[pid]) < 2:
                    project_image_map[pid].append(img.file_url)

            # attach images to projects
            data = []
            for project in projects:
                project_dict = project.__dict__.copy()
                project_dict["images"] = project_image_map.get(project.id, [])
                data.append(project_dict)

            return {
                "meta_data": {"limit": limit, "page": page, "total": total},
                "data": data,
                "message": "Projects fetched successfully",
            }

        except Exception as e:
            logger.error(f"[PROJECT_LIST] Error for User {user_id}: {str(e)}")
            raise Exception(f"Failed to fetch projects: {str(e)}")

    async def get_single_project(self, user_id: str, project_id: str):
        """Retrieves full details, media, and package status for a specific project."""
        try:
            logger.info(f"[PROJECT_GET] User {user_id} accessing Project {project_id}")

            # 1. Membership Check
            membership_stmt = select(
                exists().where(
                    ProjectMember.user_id == user_id,
                    ProjectMember.project_id == project_id,
                )
            )
            if not await self.db.scalar(membership_stmt):
                logger.warning(
                    f"[PROJECT_GET] Access Denied: User {user_id} on Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to view this project",
                )

            # 2. Fetch Project
            project = await self.db.get(BuildingProject, project_id)
            if not project:
                logger.warning(f"[PROJECT_GET] Not Found: Project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

            # 3. Enrich Data
            stmt_recent_report = (
                select(ProjectReport)
                .where(ProjectReport.project_id == project_id)
                .order_by(ProjectReport.report_date.desc())
                .limit(2)
            )

            #Get the report for the project
            project.recents_report = (
                (await self.db.execute(stmt_recent_report)).scalars().all()
            )

            #Get the plan Objects
            project.plan = await self.db.get(Plan,project.plan_id) if project.plan_id else {}

            #Determine is he can still post report for the project
            project.has_report_package = (await self.package_useage.has_report_package(
                project_id
            ))

            #only the owner has this actions
            project.has_report_action = (await self.perms_role.has_project_permission(user_id,project_id,CAN_MANAGE_REPORT))

            # Only project owner can see this
            project.has_payment_action = (True if str(project.owner_id) == user_id else False)

            # Media
            project.images = await self.media_upload.get_uploaded_project_media(
                project_id
            )

            return {"data": project, "message": "Project fetched successfully"}

        except HTTPException as http_e:
            raise http_e
        except Exception as e:
            logger.error(f"[PROJECT_GET] Critical Error for ID {project_id}: {str(e)}")
            raise Exception(f"Error retrieving project: {str(e)}")

    async def get_project_report(
        self, project_id: str, user_id: str, page: int = 1, limit: int = 10
    ):
        """Retrieves paginated reports for a project with permission validation."""
        try:
            logger.info(f"[REPORTS_GET] Fetching reports for Project {project_id}")

            # 1. Permission and Membership Check
            if not await self.perms_role.has_project_permission(
                user_id, project_id, CAN_VIEW_REPORT
            ):
                logger.warning(f"[REPORTS_GET] Permission Denied: User {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=self.permission_denied_msg,
                )

            membership_stmt = select(
                exists().where(
                    ProjectMember.user_id == user_id,
                    ProjectMember.project_id == project_id,
                )
            )
            if not await self.db.scalar(membership_stmt):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Project membership required",
                )

            # 2. Query
            page, limit = max(page, 1), min(limit, 100)
            offset = (page - 1) * limit

            stmt = (
                select(ProjectReport)
                .where(ProjectReport.project_id == project_id)
                .order_by(ProjectReport.report_date.desc())
                .limit(limit)
                .offset(offset)
            )

            reports = (await self.db.execute(stmt)).scalars().all()
            total = await self.db.scalar(
                select(func.count())
                .select_from(ProjectReport)
                .where(ProjectReport.project_id == project_id)
            )

            # ---------------------------------
            # Fetch one image per report
            # ---------------------------------
            report_ids = [r.id for r in reports]

            image_stmt = (
                select(ReportUpload)
                .where(
                    ReportUpload.report_id.in_(report_ids),
                    ReportUpload.file_type == "image",
                )
                .order_by(ReportUpload.uploaded_at.asc())
            )

            image_result = await self.db.execute(image_stmt)
            images = image_result.scalars().all()

            # map first image per report
            report_image_map = {}
            for img in images:
                if img.report_id not in report_image_map:
                    report_image_map[img.report_id] = img.file_url

            # attach image to reports
            data = []
            for report in reports:
                report_dict = report.__dict__.copy()
                report_dict["image"] = report_image_map.get(report.id)
                data.append(report_dict)

            return {
                "data": data,
                "meta_data": {"limit": limit, "page": page, "total": total},
                "message": "Project reports fetched successfully",
            }

        except HTTPException as http_e:
            raise http_e
        except Exception as e:
            logger.error(f"[REPORTS_GET] Error for Project {project_id}: {str(e)}")
            raise Exception(f"Failed to fetch reports: {str(e)}")

    async def get_single_report(self, project_id: str, user_id: str, report_id: str):
        """Fetches details of a specific report including media."""
        try:
            logger.info(f"[REPORT_SINGLE] User {user_id} fetching Report {report_id}")

            if not await self.perms_role.has_project_permission(
                user_id, project_id, CAN_VIEW_REPORT
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=self.permission_denied_msg,
                )

            report = await self.db.get(ProjectReport, report_id)
            if not report:
                logger.warning(f"[REPORT_SINGLE] Report {report_id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
                )

            media = await self.media_upload.get_uploaded_report(report_id)

            return {
                "data": {**report.__dict__, "report_media": media},
                "message": "Report fetched successfully",
            }
        except HTTPException as http_e:
            raise http_e
        except Exception as e:
            logger.error(f"[REPORT_SINGLE] Error for Report {report_id}: {str(e)}")
            raise Exception(f"Failed to fetch report details: {str(e)}")

    async def create_project_report(
        self, report_payload: dict, project_id: str, current_user: dict
    ):
        """Creates a new progress report for a project with optimized image uploads."""
        user_id = str(current_user.get("id"))
        try:
            logger.info(
                f"[REPORT_CREATE] Start: User {user_id} creating report for Project {project_id}"
            )

            # 1. Permission Check
            if not await self.perms_role.has_project_permission(
                user_id, project_id, CAN_MANAGE_REPORT
            ):
                logger.warning(
                    f"[REPORT_CREATE] Permission Denied: User {user_id} on Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # check the usage for report creation:
            if not await self.package_useage.has_report_package(project_id):
                logger.warning(
                    f"[REPORT_CREATE] Permission Denied: User {user_id} on Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You have exhausted your report plan usage",
                )

            # 2. Extract and Prepare Data
            images = report_payload.pop("images", [])
            logger.debug(f"[REPORT_CREATE] Payload: {report_payload}")

            report = ProjectReport(
                **report_payload,
                project_id=project_id,
                submitted_by=user_id,
            )

            self.db.add(report)
            await self.db.flush()
            await self.db.refresh(report)

            logger.info(f"[REPORT_CREATE] Report instance created: ID {report.id}")

            # 3. Handle Media Uploads
            if images:
                logger.info(
                    f"[REPORT_CREATE] Uploading {len(images)} images for Report {report.id}"
                )
                # new_images = await asyncio.gather(
                #     *(
                #         upload_file_optimized(
                #             img, "report_image", user_id, current_user, "REPORT"
                #         )
                #         for img in images
                #     )
                # )
                await self.media_upload.upload_report_media(
                    uploads=images, report_id=report.id
                )

            # FINAL ATOMIC USAGE UPDATE (only if everything worked)
            await self.package_useage.increment_report_usage(project_id)

            await self.db.commit()
            await self.db.refresh(report)

            report_data = report.__dict__

            logger.info(f"[REPORT_CREATE] Success: Report {report.id} finalized")
            return ProjectReportResponse.model_validate(report_data).model_dump()

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc

        except Exception as e:
            await self.db.rollback()
            logger.error(f"[REPORT_CREATE] Critical Error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create project report: {str(e)}")

    async def updates_project_report(
        self,
        project_id: str,
        report_id: str,
        user_id: str,
        report_dto: dict,
        images: list,
        current_user: dict = {},
    ):
        """Updates an existing project report and synchronizes media."""
        try:
            logger.info(
                f"[REPORT_UPDATE] Start: User {user_id} updating Report {report_id}"
            )

            # 1. Permission Check
            if not await self.perms_role.has_project_permission(
                user_id, project_id, CAN_MANAGE_REPORT
            ):
                logger.warning(f"[REPORT_UPDATE] Permission Denied: User {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # check the usage for report creation:
            if not await self.package_useage.has_report_package(project_id):
                logger.warning(
                    f"[REPORT_CREATE] Permission Denied: User {user_id} on Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You have exhausted your report plan usage",
                )

            # 2. Fetch Report
            report_stmt = await self.db.get(ProjectReport, report_id)
            if not report_stmt:
                logger.warning(f"[REPORT_UPDATE] Not Found: Report {report_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Report not found"
                )

            # 3. Process Data and Updates
            # existing_image_ids = report_dto.pop("existing_image_ids", [])
            report_dict = report_dto.copy()

            for key, value in report_dict.items():
                setattr(report_stmt, key, value)

            await self.db.flush()

            # 4. Handle Media Updates
            if images:
                logger.info(
                    f"[REPORT_UPDATE] Processing {len(images)} new images for Report {report_id}"
                )
                # new_images = await asyncio.gather(
                #     *(
                #         upload_file_optimized(
                #             img, "report_image", user_id, current_user, "REPORT"
                #         )
                #         for img in images
                #     )
                # )
                await self.media_upload.update_uploaded_report_media(report_id, images)
            # else:
            # If no new images, we still might need to remove deleted ones
            # await self.media_upload.update_uploaded_report_media(
            #     report_id, existing_image_ids, []
            # )

            await self.db.commit()
            await self.db.refresh(report_stmt)

            logger.info(f"[REPORT_UPDATE] Success: Report {report_id} updated")
            return {
                "data": report_stmt.__dict__,
                "message": "Report updated successfully",
            }

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[REPORT_UPDATE] Critical Error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to update report: {str(e)}")

    async def delete_project_report(
        self, project_id: str, user_id: str, report_id: str
    ):
        """Deletes a project report."""
        try:
            logger.info(
                f"[REPORT_DELETE] Start: User {user_id} deleting Report {report_id}"
            )

            if not await self.perms_role.has_project_permission(
                user_id, project_id, CAN_MANAGE_REPORT
            ):
                logger.warning(f"[REPORT_DELETE] Permission Denied: User {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # check the usage for report creation:
            if not await self.package_useage.has_report_package(project_id):
                logger.warning(
                    f"[REPORT_CREATE] Permission Denied: User {user_id} on Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You have exhausted your report plan usage",
                )

            stmt = await self.db.get(ProjectReport, report_id)
            if not stmt:
                logger.warning(f"[REPORT_DELETE] Not Found: Report {report_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found",
                )

            await self.db.delete(stmt)
            await self.db.commit()

            logger.info(f"[REPORT_DELETE] Success: Report {report_id} deleted")
            return {"message": "Report deleted successfully"}

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[REPORT_DELETE] Critical Error: {str(e)}", exc_info=True)
            raise Exception(f"Failed to delete report: {str(e)}")

    async def update_project(
        self,
        user_id: str,
        project_id: str,
        project_dto: dict,
        images: list,
        current_user: dict = {},
    ):
        """Updates project details, handles image uploads, and manages existing media."""
        try:
            logger.info(
                f"[PROJECT_UPDATE] Start: User {user_id} updating Project {project_id}"
            )

            # 1. Permission Check
            if not await self.perms_role.has_project_permission(
                user_id, project_id, CAN_MANAGE_PROJECT
            ):
                logger.warning(
                    f"[PROJECT_UPDATE] Permission Denied: User {user_id} cannot manage Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # 2. Fetch and Verify Ownership
            project_stmt = await self.db.get(BuildingProject, project_id)
            if not project_stmt:
                logger.warning(f"[PROJECT_UPDATE] Not Found: Project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
                )

            if str(project_stmt.owner_id) != user_id:
                logger.warning(
                    f"[PROJECT_UPDATE] Ownership Denied: User {user_id} is not the owner of Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # 3. Process Payload
            existing_image_ids = project_dto.pop("existing_image_ids", [])
            project_dict = project_dto.copy()

            # Clean Enums (Days and Windows)
            if "preferred_inspection_days" in project_dict:
                project_dict["preferred_inspection_days"] = [
                    day.value if hasattr(day, "value") else str(day)
                    for day in project_dict["preferred_inspection_days"]
                ]

            if "preferred_inspection_window" in project_dict:
                val = project_dict["preferred_inspection_window"]
                project_dict["preferred_inspection_window"] = (
                    val.value if hasattr(val, "value") else str(val)
                )

            # Apply updates to model
            for key, value in project_dict.items():
                setattr(project_stmt, key, value)

            await self.db.flush()

            # 4. Handle New Media Uploads
            new_images = []
            if images:
                logger.info(
                    f"[PROJECT_UPDATE] Uploading {len(images)} new images for Project {project_id}"
                )
                new_images = await asyncio.gather(
                    *(
                        upload_file_optimized(
                            img, "project_image", user_id, current_user, "PROJECT"
                        )
                        for img in images
                    )
                )

            # Sync media (Remove old, add new)
            await self.media_upload.update_uploaded_project_media(
                project_id, existing_image_ids, new_images
            )

            await self.db.commit()
            await self.db.refresh(project_stmt)

            logger.info(
                f"[PROJECT_UPDATE] Success: Project {project_id} updated successfully"
            )
            return project_stmt

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PROJECT_UPDATE] Critical Error: {str(e)}", exc_info=True)
            raise Exception(f"An error occurred while updating the project: {str(e)}")

    async def delete_project(self, user_id: str, project_id: str):
        """Deletes a project and its associated data."""
        try:
            logger.info(
                f"[PROJECT_DELETE] Start: User {user_id} attempting to delete Project {project_id}"
            )

            # 1. Permission Check
            if not await self.perms_role.has_project_permission(
                user_id, project_id, CAN_MANAGE_PROJECT
            ):
                logger.warning(
                    f"[PROJECT_DELETE] Permission Denied: User {user_id} cannot delete Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # 2. Fetch and Verify Ownership
            stmt = await self.db.get(BuildingProject, project_id)
            if not stmt:
                logger.warning(f"[PROJECT_DELETE] Not Found: Project {project_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

            if str(stmt.owner_id) != user_id:
                logger.warning(
                    f"[PROJECT_DELETE] Ownership Denied: User {user_id} is not the owner of Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # 3. Execution
            await self.db.delete(stmt)
            await self.db.commit()

            logger.info(
                f"[PROJECT_DELETE] Success: Project {project_id} deleted successfully"
            )
            return {"message": "Project deleted Successfully"}

        except HTTPException as http_exc:
            await self.db.rollback()
            raise http_exc
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[PROJECT_DELETE] Critical Error: {str(e)}", exc_info=True)
            raise Exception(f"An error occurred while deleting the project: {str(e)}")

    async def payments_history(
        self, project_id: str, user_id: str, page: int = 1, limit: int = 20
    ):
        """Fetches the full payment history for a specific project."""
        try:
            logger.info(
                f"[PAYMENTS] Fetching history for Project: {project_id} by User: {user_id}"
            )
            page = max(page, 1)
            limit = min(limit, 100)
            offset = (page - 1) * limit

            # Permission Check
            has_permission = await self.perms_role.has_project_permission(
                user_id, project_id, CAN_VIEW_PROJECT_PAYMENT
            )
            if not has_permission:
                logger.warning(
                    f"[PAYMENTS] Access Denied: User {user_id} lacks permission for Project {project_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            # Query building
            payments_stmt = (
                select(PaymentHistory, Plan)
                .join(Plan, PaymentHistory.plan_id == Plan.id)
                .where(PaymentHistory.project_id == project_id)
                .order_by(PaymentHistory.updated_at.desc())
                .offset(offset)
                .limit(limit)
            )
            # attach the invoice it with it

            result = await self.db.execute(payments_stmt)
            rows = result.all()

            payments = []
            for payment, plan in rows:
                payments.append(
                    {
                        **payment.__dict__,
                        "plan": {
                            "id": plan.id,
                            "name": plan.name,
                            "amount": plan.amount,
                            "currency": plan.currency,
                            "frequency": plan.frequency,
                        },
                    }
                )

            count_stmt = (
                select(func.count())
                .select_from(PaymentHistory)
                .where(PaymentHistory.project_id == project_id)
            )
            logger.info(
                f"[PAYMENTS] Successfully retrieved {len(payments)} records for Project: {project_id}"
            )
            total = await self.db.scalar(count_stmt)
            return {
                "meta_data": {"limit": limit, "page": page, "total": total},
                "data": payments,
                "message": "Payment History fetched successfully",
            }

        except HTTPException as http_exc:
            # Re-raise HTTP exceptions so FastAPI handles them correctly
            raise http_exc
        except Exception as e:
            logger.error(
                f"[PAYMENTS] Critical error fetching history for Project {project_id}: {str(e)}",
                exc_info=True,
            )
            raise Exception(
                f"Internal server error while fetching payment history: {str(e)}"
            )

    async def single_payments_history(
        self, project_id: str, user_id: str, payment_id: str
    ):
        """Fetches a specific payment record by ID."""
        try:
            logger.info(
                f"[PAYMENTS] Fetching Record: {payment_id} for Project: {project_id}"
            )

            # Permission Check
            has_permission = await self.perms_role.has_project_permission(
                user_id, project_id, CAN_VIEW_PROJECT_PAYMENT
            )
            if not has_permission:
                logger.warning(
                    f"[PAYMENTS] Access Denied: User {user_id} lacks permission to view record {payment_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=self.permission
                )

            stmt = (
                select(PaymentHistory, Plan)
                .join(Plan, PaymentHistory.plan_id == Plan.id)
                .where(PaymentHistory.id == payment_id)
            )

            result = await self.db.execute(stmt)

            result_payment, plan = result.first()

            if not result_payment:
                logger.warning(
                    f"[PAYMENTS] Not Found: Payment record {payment_id} does not exist"
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment record not found",
                )

            logger.info(
                f"[PAYMENTS] Successfully retrieved payment record: {payment_id}"
            )
            result_payment.plan = plan
            return result_payment

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(
                f"[PAYMENTS] Critical error fetching record {payment_id}: {str(e)}",
                exc_info=True,
            )
            raise Exception(
                f"Internal server error while fetching single payment record: {str(e)}"
            )

    async def update_subscription_plan(
        self, project_id: str, user_id: str, plan_id: str
    ):
        try:
            # check if the project is avialble
            project = await self.db.get(BuildingProject, project_id)

            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project Id Doesnt Exist",
                )

            if str(user_id) != str(project.owner_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=self.permission,
                )

            # Generate Invoice,Tag the project has pending
            invoice_id = await self.payment_service.generate_payment_invoice(
                project_id, plan_id, project
            )
            return invoice_id

        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            logger.error(
                f"[PAYMENTS] Critical error fetching record: {str(e)}",
                exc_info=True,
            )
            raise Exception(
                f"Internal server error while fetching single payment record: {str(e)}"
            )


