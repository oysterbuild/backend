from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from models.building_project import BuildingProject
from schemas.projects_schema import ProjectSetupDto
from utils.loggers import setup_logger
from models.media_upload import ProjectUpload, ReportUpload
from sqlalchemy import select, func, exists


logger = setup_logger("Upload_Media_Service")


class UploadMedia:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload_report_media(self, report_id: str, uploads: list):
        try:
            logger.info(
                f"Starting media upload for report_id={report_id}, images_count={len(uploads)}"
            )

            report_uploads = [
                ReportUpload(
                    report_id=report_id,
                    file_url=image.get("image_url"),
                    file_type=image.get("file_type"),
                )
                for image in uploads
            ]

            self.db.add_all(report_uploads)
            await self.db.flush()

            logger.info(
                f"Successfully uploaded {len(uploads)} images for report_id={report_id}"
            )
            return None

        except Exception as e:
            logger.error(
                f"Failed to upload project media for report_id={report_id}: {e}",
            )
            raise

    async def upload_project_media(self, project_id: str, images: []):
        try:
            logger.info(
                f"Starting media upload for project_id={project_id}, images_count={len(images)}"
            )

            project_uploads = [
                ProjectUpload(
                    project_id=project_id,
                    file_url=image.get("image_url"),
                    file_type=(
                        "Image"
                        if image.get("file_type") in ["jpg", "jpeg", "png"]
                        else "File"
                    ),
                )
                for image in images
            ]

            self.db.add_all(project_uploads)
            await self.db.flush()

            logger.info(
                f"Successfully uploaded {len(project_uploads)} images for project_id={project_id}"
            )
            return None

        except Exception as e:
            logger.error(
                f"Failed to upload project media for project_id={project_id}: {e}",
            )
            raise

    async def get_uploaded_report(self, report_id: str):
        try:
            stmt = (
                select(ReportUpload.id, ReportUpload.file_url, ReportUpload.file_type)
                .where(ReportUpload.report_id == report_id)
                .order_by(ReportUpload.created_at.desc())
            )
            result = await self.db.execute(stmt)
            return result.mappings().all()
        except Exception as e:
            raise e

    async def get_uploaded_project_media(self, project_id: str):
        try:
            stmt = (
                select(
                    ProjectUpload.id, ProjectUpload.file_url, ProjectUpload.file_type
                )
                .where(ProjectUpload.project_id == project_id)
                .order_by(ProjectUpload.created_at.desc())
            )
            result = await self.db.execute(stmt)
            return result.mappings().all()

        except Exception as e:
            raise e

    async def update_uploaded_project_media(
        self, project_id: str, existing_image_ids: list, new_images: []
    ):
        try:
            current_images = await self.get_uploaded_project_media(project_id)

            current_ids = {image.get("id") for image in current_images}

            keep_ids = set(existing_image_ids or [])

            delete_ids = current_ids - keep_ids

            if delete_ids:
                images_to_delete = [
                    img for img in current_images if img.id in delete_ids
                ]
                for img in images_to_delete:
                    await self.delete_uploaded_project_media(img.get("id"))

            await self.upload_project_media(project_id, new_images)
            # await self.db.commit()
        except Exception as e:
            raise e

    async def delete_uploaded_project_media(self, image_id: str = ""):
        try:
            stmt_image = await self.db.get(ProjectUpload, image_id)
            if stmt_image:
                await self.db.delete(stmt_image)
                # await self.db.commit()
        except Exception as e:
            raise e

    async def delete_uploaded_report_media(self, image_id: str = ""):
        try:
            stmt_image = await self.db.get(ReportUpload, image_id)
            if stmt_image:
                await self.db.delete(stmt_image)
                # await self.db.commit()
        except Exception as e:
            raise e

    # async def update_uploaded_report_media(
    #     self, report_id: str, existing_image_ids: list, new_images: []
    # ):
    #     try:
    #         current_images = await self.get_uploaded_report(report_id)

    #         current_ids = {image.get("id") for image in current_images}

    #         keep_ids = set(existing_image_ids or [])

    #         delete_ids = current_ids - keep_ids

    #         if delete_ids:
    #             images_to_delete = [
    #                 img for img in current_images if img.id in delete_ids
    #             ]
    #             for img in images_to_delete:
    #                 await self.delete_uploaded_report_media(img.get("id"))

    #         await self.upload_report_media(report_id, new_images)
    #     except Exception as e:
    #         raise e

    async def update_uploaded_report_media(
        self, report_id: str, new_images: List[Dict]
    ):
        """
        Update report media:
        - Keep existing images whose ID is passed
        - Delete images that are missing from the new_images
        - Save new URLs for images/videos provided by frontend
        """

        try:
            # 1. Get current images from DB
            current_images = await self.get_uploaded_report(
                report_id
            )  # list of ReportUpload ORM objects
            current_ids = {str(img.id) for img in current_images}

            # 2. Determine which IDs frontend wants to keep
            keep_ids = {str(img.get("id")) for img in new_images if img.get("id")}

            # 3. IDs to delete
            delete_ids = current_ids - keep_ids

            # 4. Delete removed images
            for img in current_images:
                if str(img.id) in delete_ids:
                    await self.delete_uploaded_report_media(str(img.id))

            # 5. Save new URLs from frontend
            # Only include items without an 'id' (new uploads)
            images_to_save = [
                img for img in new_images if not img.get("id") and img.get("image_url")
            ]

            await self.upload_report_media(report_id, images_to_save)

            # await self.db.commit()
        except Exception as e:
            raise e
