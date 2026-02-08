import base64
import logging
import time
import httpx
from utils.loggers import setup_logger
from settings import get_settings
from typing import Dict, Any

settings = get_settings()

logger = setup_logger("cloudinary_service")
import hashlib


class CloudinaryService:
    def __init__(self):
        self.cloud_name = settings.cloudinary_cloud_name
        self.api_key = settings.cloudinary_api_key
        self.api_secret = settings.cloudinary_api_secret

        self.upload_url = (
            f"https://api.cloudinary.com/v1_1/{self.cloud_name}/auto/upload"
        )

        auth_bytes = f"{self.api_key}:{self.api_secret}".encode()
        self.auth_header = {
            "Authorization": f"Basic {base64.b64encode(auth_bytes).decode()}"
        }

    async def upload_file_async(
        self,
        file_bytes: bytes,
        public_id: str,
        folder: str,
        resource_type: str = "image",
    ) -> str:
        timestamp = int(time.time())

        params_to_sign = {
            "folder": folder,
            "public_id": public_id,
            "timestamp": timestamp,
            "overwrite": "true",
        }

        signature = await self.cloudinary_signature(params_to_sign, self.api_secret)

        files = {"file": ("file", file_bytes)}
        data = {
            **params_to_sign,
            "api_key": self.api_key,
            "signature": signature,
            "resource_type": resource_type,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.upload_url, files=files, data=data)

        if resp.status_code != 200:
            logger.error(f"Cloudinary upload failed [{resp.status_code}]: {resp.text}")
            raise Exception("Cloudinary upload failed")

        return resp.json()["secure_url"]

    async def cloudinary_signature(self, params: dict, api_secret: str) -> str:
        """
        Create Cloudinary signature
        """
        to_sign = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v)
        to_sign += api_secret
        return hashlib.sha1(to_sign.encode()).hexdigest()

    async def get_presigned_upload_params(self, folder: str) -> Dict[str, Any]:
        """
        Generates the signature and parameters for the frontend to upload directly.
        """
        timestamp = int(time.time())

        # These are the parameters you want to "lock" from the backend
        params_to_sign = {
            "folder": folder,
            "timestamp": timestamp,
        }

        signature = await self.cloudinary_signature(params_to_sign, self.api_secret)

        # Return everything the frontend needs to make the POST request
        return {
            "upload_url": self.upload_url,
            "api_key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "folder": folder,
            "cloud_name": self.cloud_name,
        }


def get_cloudinary() -> CloudinaryService:
    return CloudinaryService()
