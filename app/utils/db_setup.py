from utils.loggers import setup_logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base
from settings import get_settings


# initialize settings
settings = get_settings()

logger = setup_logger("Database Setup")

# Initial Setup
ASYNC_DATABASE_URL = settings.async_database_url

# create database engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# create database session
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# declear a base model
Base = declarative_base()


# Database dependency function
async def get_database() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Starting Database Session..........")
            yield session
        finally:
            logger.info("Close Database Session..........")
            await session.close()
