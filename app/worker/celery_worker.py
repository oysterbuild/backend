import logging
from celery import Celery
from celery.schedules import crontab
from settings import get_settings

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
    "expire-plans-every-hour": {
        "task": "schedule_plan_expiration",
        "schedule": crontab(minute=0, hour="*"),  # every hour
    },
    "send-expiration-notifications": {
        "task": "schedule_plan_expire_notification",
        "schedule": crontab(minute="*/15"),  # every 15 minutes
    },
}


# ---------------------------
# Celery Tasks
# ---------------------------


@celery.task(name="schedule_plan_expiration")
def schedule_plan_expiration():
    """
    Task to expire user plans.
    Runs every hour.
    """
    logger.info("Running plan expiration task")
    # TODO: implement expiration logic
    return "Plan expiration task completed"


@celery.task(name="schedule_plan_expire_notification")
def schedule_plan_expire_notification():
    """
    Task to send plan expiration notifications.
    Runs every 15 minutes.
    """
    logger.info("Running plan expiration notification task")
    # TODO: implement notification logic
    return "Plan expiration notification task completed"
