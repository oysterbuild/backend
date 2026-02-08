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

router = APIRouter(prefix="/payment")

settings = get_settings()


# make singleton
def get_payment_service(db: AsyncSession = Depends(get_database)) -> PaymentService:
    return PaymentService(db=db)


@router.post("/invoice")
async def roles(
    invoice_id: str = File(..., description="invoice id"),
    provider: Literal["PAYSTACK", "FLUTTERWAVE"] = File(
        ..., examples=["PAYSTACK", "FLUTTERWAVE"]
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

    event: str = payload.get("event")
    data: dict = payload.get("data", {})

    await payment_service.payment_webhook(payload, "PAYSTACK")

    # if event == "charge.success":

    # Safely get the reference
    # reference: str = data.get("reference") or data.get("refund_reference")

    # Your logic here...
    return {"status": "success"}
