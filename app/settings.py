import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    app_name: str = "OYSTERBUILD"
    async_database_url: str = os.getenv(
        "ASYNC_DATABASE_URL", "postgresql+asyncpg://testuser:testpass@db:5432/testdb"
    )
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://testuser:testpass@db:5432/testdb"
    )
    jwt_token_expire_minutes: int = 120
    jwt_secret: str = os.getenv("JWT_SECRET_KEY", " ")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", " ")
    cloudinary_cloud_name: str = os.getenv("CLOUDINARY_CLOUD_NAME", " ")
    cloudinary_api_key: str = os.getenv("CLOUDINARY_API_KEY", "")
    cloudinary_api_secret: str = os.getenv("CLOUDINARY_API_SECRET", " ")
    email_host_user: str = os.getenv("EMAIL_HOST_USER", "")
    email_host_password: str = os.getenv("EMAIL_HOST_PASSWORD", " ")
    paystack_secret_key: str = os.getenv("PAYSTACK_SECRET_KEY", " ")
    paystack_public_key: str = os.getenv("PAYSTACK_PUBLIC_KEY", " ")
    celery_broker_url: str = os.getenv("REDIS_URL", " ")
    celery_result_backend: str = os.getenv("REDIS_URL", " ")

def get_settings() -> Settings:
    return Settings()
