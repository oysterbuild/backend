from typing import Literal
from fastapi import (
    APIRouter,
    Depends,
    BackgroundTasks,
    Query,
    status,
    UploadFile,
    Form,
    File,
    HTTPException,
    Request,
)
from httpx import _status_codes
import hmac, hashlib
from services.payment_services import PaymentService
from utils.db_setup import get_database
from sqlalchemy.ext.asyncio import AsyncSession
from utils.db_setup import get_database
from dependencies.auth import get_current_user
from utils.file_upload import upload_file_optimized
from settings import get_settings
from services.plan_service import PlansService
from utils.loggers import setup_logger

router = APIRouter(prefix="/payment")

settings = get_settings()

logger = setup_logger("payment_route")


# make singleton
def get_payment_service(db: AsyncSession = Depends(get_database)) -> PaymentService:
    return PaymentService(db=db)


def get_plan_service(db: AsyncSession = Depends(get_database)) -> PaymentService:
    return PlansService(db=db)


@router.post("/invoice")
async def roles(
    invoice_id: str = File(..., description="invoice id"),
    provider: Literal["PAYSTACK", "FLUTTERWAVE", "STRIPE"] = File(
        ..., examples=["PAYSTACK", "FLUTTERWAVE", "STRIPE"]
    ),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: dict = Depends(get_current_user),
):
    # From the invoice
    user_email = current_user.get("email")
    result = await payment_service.make_payment(provider, invoice_id, user_email)
    return result


@router.post("/paystack/webhook-events")
async def paystack_webhook_event(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service),
):
    # 1. Get the raw bytes from the request (required for HMAC)
    body_bytes = await request.body()

    sig_header = request.headers.get("x-paystack-signature")
    secret = settings.paystack_secret_key

    # 2. Generate the hash using the bytes
    hash_ = hmac.new(
        secret.encode("utf-8"),
        body_bytes,  # Pass the awaited bytes here
        digestmod=hashlib.sha512,
    ).hexdigest()

    # Request not from paystack
    if hash_ != sig_header:
        raise HTTPException(
            detail="Unauthorized", status_code=status.HTTP_400_BAD_REQUEST
        )

    # 3. Parse the JSON data from the request
    payload = await request.json()

    # event: str = payload.get("event")
    # data: dict = payload.get("data", {})

    await payment_service.payment_webhook(payload, "PAYSTACK")

    # Your logic here...
    return {"status": "success"}


@router.post("/stripe/webhook-events")
async def stripe_webhook_event(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service),
):
    body_bytes = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            detail="Missing Stripe-Signature header",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    import stripe as stripe_lib

    stripe_lib.api_key = settings.stripe_secret_key

    try:
        event = stripe_lib.Webhook.construct_event(
            body_bytes, sig_header, settings.stripe_webhook_secret
        )
    except stripe_lib.errors.SignatureVerificationError:
        logger.warning("[STRIPE_WEBHOOK] Invalid signature rejected")
        raise HTTPException(
            detail="Invalid Stripe webhook signature",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    await payment_service.payment_webhook(dict(event), "STRIPE")
    return {"status": "success"}


@router.get("/plans")
async def get_plans(
    current_user: dict = Depends(get_current_user),
    plan_service: PlansService = Depends(get_plan_service),
):
    try:
        resp = await plan_service.get_plans()
        return {"message": "Plan Fetch Successfull", "data": resp, "status": True}
    except HTTPException as e:
        logger.error(f"HTTP Exception: {e.detail}")
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Something went wrong: {e}",
        )
