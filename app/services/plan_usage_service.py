from sqlalchemy.ext.asyncio import AsyncSession
from utils.loggers import setup_logger
from sqlalchemy import select, exists,update
from models.building_project import BuildingProject
from models.plans import PlanPackageUsageCount, Package
from fastapi import HTTPException, status
from models.plans import PaymentHistory,Plan
from datetime import datetime,timezone,timedelta
from models.users import User
from services.email_service import get_email_service

logger = setup_logger("Project_Plan_Usage_Service")


class ProjectPlanUsageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def has_storage_package(self, project_id: str) -> bool:
        try:
            logger.info(
                f"[StorageCheck] Checking storage access for project={project_id}"
            )

            # 1. Fetch project
            project = await self.db.get(BuildingProject, project_id)

            if not project:
                logger.warning(f"[StorageCheck] Project not found: {project_id}")
                return False

            if not project.plan_id:
                logger.warning(
                    f"[StorageCheck] No plan attached to project={project_id}"
                )
                return False

            if project.payment_status in ("Pending", "Expired"):
                logger.info(
                    f"[StorageCheck] Payment inactive for project={project_id}, "
                    f"status={project.payment_status}"
                )
                return False

            # 2. Fetch storage package for plan
            stmt_package = select(Package).where(
                Package.plan_id == project.plan_id,
                Package.tag == "storage",
            )
            package = await self.db.scalar(stmt_package)

            if not package:
                logger.info(
                    f"[StorageCheck] No storage package for plan={project.plan_id}"
                )
                return False

            if package.is_unlimited:
                logger.info(
                    f"[StorageCheck] Unlimited storage granted for project={project_id}"
                )
                return True

            # 3. Fetch usage
            stmt_usage = select(PlanPackageUsageCount.usage_count).where(
                PlanPackageUsageCount.project_id == project_id,
                PlanPackageUsageCount.package_id == package.id,
            )
            usage = (await self.db.scalar(stmt_usage)) or 0

            allowed = usage < (package.count or 0)

            logger.info(
                f"[StorageCheck] project={project_id} "
                f"usage={usage} limit={package.count} allowed={allowed}"
            )

            return allowed

        except Exception as e:
            logger.exception(
                f"[StorageCheck] Unexpected error for project={project_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to validate storage package",
            )

    async def has_report_package(self, project_id: str) -> bool:
        try:
            logger.info(
                f"[ReportCheck] Checking report access for project={project_id}"
            )

            project = await self.db.get(BuildingProject, project_id)

            if not project:
                logger.warning(f"[ReportCheck] Project not found: {project_id}")
                return False

            if not project.plan_id:
                logger.warning(
                    f"[ReportCheck] No plan attached to project={project_id}"
                )
                return False

            if project.payment_status in ("Pending", "Expired"):
                logger.info(
                    f"[ReportCheck] Payment inactive for project={project_id}, "
                    f"status={project.payment_status}"
                )
                return False

            stmt_package = select(Package).where(
                Package.plan_id == project.plan_id,
                Package.tag == "reports",
            )
            package = await self.db.scalar(stmt_package)

            if not package:
                logger.info(
                    f"[ReportCheck] No report package for plan={project.plan_id}"
                )
                return False

            if package.is_unlimited:
                logger.info(
                    f"[ReportCheck] Unlimited reports granted for project={project_id}"
                )
                return True

            stmt_usage = select(PlanPackageUsageCount.usage_count).where(
                PlanPackageUsageCount.project_id == project_id,
                PlanPackageUsageCount.package_tag == "reports",
            )
            usage = (await self.db.scalar(stmt_usage)) or 0

            allowed = usage < (package.count or 0)

            logger.info(
                f"[ReportCheck] project={project_id} "
                f"usage={usage} limit={package.count} allowed={allowed}"
            )

            return allowed

        except Exception as e:
            logger.exception(
                f"[ReportCheck] Unexpected error for project={project_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to validate report package",
            )

    async def has_member_invitation_package(self, project_id: str) -> bool:
        try:
            logger.info(
                f"[MemberInviteCheck] Checking member invite access for project={project_id}"
            )

            project = await self.db.get(BuildingProject, project_id)

            if not project:
                logger.warning(f"[MemberInviteCheck] Project not found: {project_id}")
                return False

            if not project.plan_id:
                logger.warning(
                    f"[MemberInviteCheck] No plan attached to project={project_id}"
                )
                return False

            if project.payment_status in ("Pending", "Expired"):
                logger.info(
                    f"[MemberInviteCheck] Payment inactive for project={project_id}, "
                    f"status={project.payment_status}"
                )
                return False

            stmt_package = select(Package).where(
                Package.plan_id == project.plan_id,
                Package.tag == "members",
            )
            package = await self.db.scalar(stmt_package)

            if not package:
                logger.info(
                    f"[MemberInviteCheck] No member package for plan={project.plan_id}"
                )
                return False

            if package.is_unlimited:
                logger.info(
                    f"[MemberInviteCheck] Unlimited members granted for project={project_id}"
                )
                return True

            stmt_usage = select(PlanPackageUsageCount.usage_count).where(
                PlanPackageUsageCount.project_id == project_id,
                PlanPackageUsageCount.package_id == package.id,
            )
            usage = (await self.db.scalar(stmt_usage)) or 0

            allowed = usage < (package.count or 0)

            logger.info(
                f"[MemberInviteCheck] project={project_id} "
                f"usage={usage} limit={package.count} allowed={allowed}"
            )

            return allowed

        except Exception as e:
            logger.exception(
                f"[MemberInviteCheck] Unexpected error for project={project_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to validate member invitation package",
            )

    async def increment_report_usage(self, project_id: str):
        stmt = (
            select(PlanPackageUsageCount)
            .where(
                PlanPackageUsageCount.project_id == project_id,
                PlanPackageUsageCount.package_tag == "reports",
            )
            .with_for_update()
        )

        result = await self.db.execute(stmt)
        usage = result.scalar_one_or_none()

        if not usage:
            self.db.add(
                PlanPackageUsageCount(
                    project_id=project_id, package_tag="reports", usage_count=1
                )
            )
            # create it new
        else:
            usage.usage_count += 1
            self.db.add(usage)


    async def schedule_plan_expiration(self):
        try:
            now = datetime.now(timezone.utc).date()
            logger.info(f"Running schedule_plan_expiration task for date: {now}")

            # 1. Update BuildingProjects directly
            # The database handles the locking and filtering in one step
            project_stmt = (
                update(BuildingProject)
                .where(
                    BuildingProject.payment_status == "Active",
                    BuildingProject.subscription_end_date <= now
                )
                .values(payment_status="Expired")
                # This returns the count of rows affected
                .execution_options(synchronize_session=False) 
            )
            
            project_result = await self.db.execute(project_stmt)
            logger.info(f"Expired {project_result.rowcount} BuildingProjects")

            # 2. Update PaymentHistory directly
            history_stmt = (
                update(PaymentHistory)
                .where(
                    PaymentHistory.status == "Active",
                    PaymentHistory.next_billing_date <= now
                )
                .values(status="Expired")
                .execution_options(synchronize_session=False)
            )
            
            history_result = await self.db.execute(history_stmt)
            logger.info(f"Expired {history_result.rowcount} PaymentHistory records")

            # Commit both updates
            await self.db.commit()
            logger.info("schedule_plan_expiration task completed successfully")

        except Exception as e:
            logger.exception(f"Unexpected error in schedule_plan_expiration: {e}")
            await self.db.rollback()
            raise e

    async def send_plan_expiration_reminders(self):
        try:
            today = datetime.now(timezone.utc).date()
            logger.info(f"Running plan expiration reminders for date: {today}")

            day_1 = today + timedelta(days=1)
            day_2 = today + timedelta(days=2)
            logger.debug(f"Checking subscriptions ending on: {day_1} and {day_2}")

            stmt = (
                select(
                    BuildingProject.name.label("project_name"),
                    BuildingProject.subscription_end_date.label("end_date"),
                    User.email,
                    User.first_name,
                    Plan.name.label("plan_name"),
                )
                .join(User, BuildingProject.owner_id == User.id)
                .join(Plan, BuildingProject.plan_id == Plan.id)
                .where(
                    BuildingProject.payment_status == "Active",
                    BuildingProject.subscription_end_date.in_([day_1, day_2])
                )
            )

            result = await self.db.execute(stmt)
            records = result.all()
            logger.info(f"Found {len(records)} subscriptions expiring soon")

            for project_name, end_date, email, first_name, plan_name in records:
                days_left = (end_date - today).days
                logger.debug(f"Preparing reminder for {email} ({project_name}), days left: {days_left}")

                if email:
                    context = {
                        "user_name": first_name,
                        "plan_name": plan_name,
                        "project_name": project_name,
                        "days_left": days_left,
                        "expiration_date": end_date
                    }

                    try:
                        await get_email_service().send_emails(
                            subject="Your Subscription Is About to Expire",
                            recipient=[email],
                            template_name="subscription_expires.html",
                            context=context
                        )
                        logger.info(f"Sent reminder email to {email} for project {project_name}")
                    except Exception as email_error:
                        logger.error(f"Failed to send email to {email}: {email_error}")

        except Exception as e:
            logger.exception(f"Error sending plan expiration reminders: {e}")
            raise e
