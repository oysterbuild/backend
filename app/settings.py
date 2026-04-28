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
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    sendgrid_from_email: str = os.getenv("SENDGRID_FROM_EMAIL", "")
    paystack_secret_key: str = os.getenv("PAYSTACK_SECRET_KEY", " ")
    paystack_public_key: str = os.getenv("PAYSTACK_PUBLIC_KEY", " ")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    celery_broker_url: str = os.getenv("REDIS_URL", " ")
    celery_result_backend: str = os.getenv("REDIS_URL", " ")
    cors_origins: str = os.getenv("ALLOWED_ORIGIN", "http://localhost:8000")
    debug: str = os.getenv("DEBUG", "True")
    allowed_hosts: str = os.getenv("ALLOWED_HOST", "localhost")
    environment: str = os.getenv("ENVIRONMENT", "development")
    # Async SQLAlchemy pool (per process). Increase if you run many workers × concurrent requests.
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))


def get_settings() -> Settings:
    return Settings()
