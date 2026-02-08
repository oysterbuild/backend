# app/utils/file_upload.py
import time
from fastapi import UploadFile, HTTPException
from settings import get_settings
import logging
import asyncio

# import cloudinary.uploader
from services.cloudinary_service import get_cloudinary

# Initialize settings
settings = get_settings()

cloudinary_upload = get_cloudinary()
logger = logging.getLogger(__name__)


async def upload_file_optimized(
    file: UploadFile,
    label: str,
    user_id: str,
    current_user: dict,
    folder_name: str = "PROJECT",
) -> str:
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
    MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
    MAX_PDF_SIZE = 5 * 1024 * 1024  # 5MB

    # Extension validation
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"{label} must be JPG, JPEG, PNG or PDF",
        )

    # Safe public_id
    timestamp = int(time.time())
    safe_first = current_user.get("first_name", "user").replace(" ", "_")
    safe_last = current_user.get("last_name", "unknown").replace(" ", "_")

    public_id = f"{user_id}/{safe_first}_{safe_last}_{label}_{timestamp}"

    try:
        # 🔴 READ FILE ONCE (ONLY HERE)
        content = await file.read()

        # Size validation
        if ext == "pdf" and len(content) > MAX_PDF_SIZE:
            raise HTTPException(400, f"{label} exceeds 5MB limit")

        if ext != "pdf" and len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(400, f"{label} exceeds 2MB limit")

        resource_type = "raw" if ext == "pdf" else "image"

        logger.info(f"Uploading {label} for user {user_id}")

        result = await cloudinary_upload.upload_file_async(
            content, public_id, folder_name, resource_type=resource_type
        )

        logger.info(f"{label} uploaded successfully for user {user_id}")
        return {"image_url": result, "file_type": ext}

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Failed to upload {label} for user {user_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload {label}",
        )
