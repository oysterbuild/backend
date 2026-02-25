import logging
from celery import Celery
from celery.schedules import crontab
from settings import get_settings
import asyncio

logger = logging.getLogger("celery_worker")

settings = get_settings()

celery = Celery(
    "celery_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery.conf.update(
    task_acks_late=True,  # Prevent task loss on worker crash
    worker_prefetch_multiplier=1,  # Immediate task pickup
    worker_concurrency=4,  # Adjust based on CPU cores
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    broker_transport_options={"visibility_timeout": 3600},
    broker_connection_retry_on_startup=True,
    timezone="UTC",
)
# Beat schedule (cron jobs)
celery.conf.beat_schedule = {
    # Runs exactly at 01:00 (1 AM) every day
    "expire-plans-every-hour": {
        "task": "schedule_plan_expiration",
        "schedule": crontab(hour=1, minute=0), 
    },

    # Runs exactly at 01:30 (1 AM) every day
    "send-expiration-notifications": {
        "task": "schedule_plan_expire_notification_email",
        "schedule": crontab(hour=1, minute=30),  
    },
}


# # ---------------------------
# # Celery Tasks
# # ---------------------------
@celery.task(name="schedule_plan_expiration")
def schedule_plan_expiration():

    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from services.plan_usage_service import ProjectPlanUsageService
    # Import engine here or from your DB module
    from utils.db_setup import AsyncSessionLocal, engine

    async def run():
        try:
            async with AsyncSessionLocal() as db:
                service = ProjectPlanUsageService(db=db)
                await service.schedule_plan_expiration()
        finally:
            # THIS IS THE FIX: Clear the pool before the loop exits
            await engine.dispose()

    logger.info("Running plan expiration task")
    asyncio.run(run())
    return "Plan expiration task completed"


@celery.task(name="schedule_plan_expire_notification_email")
def schedule_plan_expiration_email():

    import os
    import sys

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from services.plan_usage_service import ProjectPlanUsageService
    from utils.db_setup import AsyncSessionLocal, engine

    async def run():
        try:
            async with AsyncSessionLocal() as db:
                service = ProjectPlanUsageService(db=db)
                await service.send_plan_expiration_reminders()
        finally:
            # THIS IS THE FIX: Clear the pool before the loop exits
            await engine.dispose()

    logger.info("Running plan expiration email task")
    asyncio.run(run())
    return "Plan expiration email task completed"
