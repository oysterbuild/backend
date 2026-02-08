import string
from time import time
from sqlalchemy.ext.asyncio import AsyncSession
from models.building_project import BuildingProject
from models.payments import Invoice, Transaction
from datetime import datetime, timezone, date
from models.plans import Plan
from fastapi import HTTPException, status
import hashlib
from utils.loggers import setup_logger
from settings import get_settings
from settings import Settings
from typing import Any, Dict, Optional
import httpx
from models.plans import PaymentHistory
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func, exists, update
from helpers.payments import handle_success_payment, handle_failed_payment
from services.email_service import get_email_service
from helpers.constant import get_next_cycle_date
import uuid


logger = setup_logger("Payment_Service")
settings = get_settings()


class PaystackServiceBaseAPIClient:
    """This handle all request to PAYMENT_PROVIDER API"""

    """
    Initialize the PAYMENT client.
    - api_key: Your PAYMENT API key
    - secret_key: Your PAYMENT API secret
    - environment: "sandbox" or "production"
    - settings: Optional config object with a custom base_url
    """

    def __init__(
        self,
        db: AsyncSession,
        settings: Optional[Settings] = None,
        provider: str = "PAYSTACK",
    ):
        self.api_key = ""
        self.environment = ""
        self.public_key = ""
        self.provider = provider
        self.db = db

        """
        NB
        // HoneyCoin API Endpoints
        -----------------------
         Production Environment:
           - Standard API (non-crypto): https://api-v2.honeycoin.app/api/b2b
           - Crypto-related API:         https://crypto.honeycoin.app/api
        
        // Sandbox Environment (for testing):
          - Standard API (non-crypto): https://api-v2.honeycoin.app/api/sandbox/b2b
          - Crypto-related API:         https://crypto.honeycoin.app/api/sandbox
        
        Use the appropriate endpoint based on the environment (production or sandbox)
        and the type of request (crypto vs normal).
        This helps separate testing from live transactions and keeps crypto calls isolated.
        """
        self.baseurl = "https://api.paystack.co"
        self.paystack_secret_key = settings.paystack_secret_key

        logger.info(
            f"Connected to {self.baseurl} for HoneyCoin {self.environment} environment"
        )

    async def generated_request_headers(self):
        """Generate request headers with cached bearer token."""

        header = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        header["Authorization"] = f"Bearer {self.paystack_secret_key}"

        logger.info("Bearer Token added to Authorization header successfully")
        return header

    async def make_request(
        self,
        method: str,
        endpoint: str = "",
        json: dict = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_seconds: float = 30.0,
        api_type: Optional[str] = "Standard",
    ):
        """Make HTTP request with comprehensive error handling."""

        logger.info("Triggered Make request method")

        timeout = httpx.Timeout(timeout_seconds, connect=10.0)
        provider = self.provider

        # RESOLVE BASE_URL
        resolve_base_url = self.baseurl
        logger.info(f"Current API resolved as {resolve_base_url}")

        try:
            url = f"{resolve_base_url}{endpoint}"
            logger.info(f"Resolved Total URL: {url}")
            headers = await self.generated_request_headers()

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method, url=url, headers=headers, json=json, params=params
                )

            # Use the centralized response handler
            return await self._handle_response(response, json, url)

        except httpx.TimeoutException:
            logger.error(f"[{provider}] Request timeout to {url}")
            raise HTTPException(
                status_code=408,
                detail={
                    "status": False,
                    "statusCode": 408,
                    "message": "Request timeout - API may be unavailable",
                    "provider": provider,
                },
            )

        except httpx.ConnectError:
            logger.error(f"[{provider}] Connection error to {url}")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": False,
                    "statusCode": 503,
                    "message": "Connection failed - check your network connectivity",
                    "provider": provider,
                },
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"[{provider}] HTTP status error: {e}")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": False,
                    "statusCode": 503,
                    "message": f"HTTP error: {str(e)}",
                    "provider": provider,
                },
            )

        except httpx.RequestError as e:
            logger.error(f"[{provider}] General request error: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": False,
                    "statusCode": 500,
                    "message": f"Request failed: {str(e)}",
                    "provider": self.provider,
                },
            )

        except HTTPException:
            raise

        except Exception as e:
            logger.error(f"[{provider}] Unexpected error: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": False,
                    "statusCode": 500,
                    "message": str(e),
                    "provider": provider,
                },
            )

    # Centralized response handler (as you requested)
    async def _handle_response(
        self, response: httpx.Response, payload: dict = None, url: str = ""
    ) -> Dict[str, Any]:
        """Centralized response handling with status code specific logic."""

        # Success case
        if response.status_code in [200, 201]:
            logger.info(f"Request successful: {response.status_code}")
            return response.json()

        # Parse error message
        try:
            error_data = response.json()
            error_message = error_data.get("message", response.text)
        except ValueError:
            error_message = response.text

        # Handle specific status codes
        status_handlers = {
            400: self._handle_bad_request,
            401: self._handle_unauthorized,
            402: self._handle_insufficient_funds,
            403: self._handle_forbidden,
            404: self._handle_not_found,
            429: self._handle_rate_limit,
        }

        handler = status_handlers.get(response.status_code)  # Get the function
        if handler:
            handler(
                error_message, payload, url, response
            )  # pass variable to the function

        # Handle 5xx errors
        if response.status_code >= 500:
            self._handle_server_error(response, payload, url)

        # Fallback for unhandled status codes
        self._handle_generic_error(response, error_message)

    def _handle_bad_request(
        self, message: str, payload: dict, url: str, response: httpx.Response
    ):
        """Handle 400 Bad Request errors."""
        logger.warning(f"[{self.provider}] Bad request (400): {message}")
        if payload:
            logger.info(f"Request payload: {payload}")

        raise HTTPException(
            status_code=400,
            detail={
                "status": False,
                "statusCode": 400,
                "message": message,
                "provider": self.provider,
            },
        )

    def _handle_unauthorized(
        self, message: str, payload: dict, url: str, response: httpx.Response
    ):
        """Handle 401 Unauthorized errors."""
        logger.error(f"[{self.provider}] Unauthorized (401): Invalid API credentials")
        raise HTTPException(
            status_code=401,
            detail={
                "status": False,
                "statusCode": 401,
                "message": f"Invalid API Credential. {response.text}",
                "provider": self.provider,
            },
        )

    def _handle_insufficient_funds(
        self, message: str, payload: dict, url: str, response: httpx.Response
    ):
        """Handle 402 Insufficient Funds errors."""
        logger.error(f"[{self.provider}] Insufficient funds (402)")
        raise HTTPException(
            status_code=402,
            detail={
                "status": False,
                "statusCode": 402,
                "message": f"Insufficient fund. {response.text}",
                "provider": self.provider,
            },
        )

    def _handle_forbidden(
        self, message: str, payload: dict, url: str, response: httpx.Response
    ):
        """Handle 403 Forbidden errors."""
        logger.error(f"[{self.provider}] Forbidden (403): Access denied")
        raise HTTPException(
            status_code=403,
            detail={
                "status": False,
                "statusCode": 403,
                "message": "Access denied - check API permissions",
                "provider": self.provider,
            },
        )

    def _handle_not_found(
        self, message: str, payload: dict, url: str, response: httpx.Response
    ):
        """Handle 404 Not Found errors."""
        logger.error(f"[{self.provider}] Not found (404): {url}")
        raise HTTPException(
            status_code=404,
            detail={
                "status": False,
                "statusCode": 404,
                "message": message,
                "provider": self.provider,
            },
        )

    def _handle_rate_limit(
        self, message: str, payload: dict, url: str, response: httpx.Response
    ):
        """Handle 429 Rate Limit errors."""
        logger.error(f"[{self.provider}] Rate limited (429): Too many requests")
        raise HTTPException(
            status_code=429,
            detail={
                "status": False,
                "statusCode": 429,
                "message": "Rate limit exceeded - Too many requests",
                "provider": self.provider,
            },
        )

    def _handle_server_error(self, response: httpx.Response, payload: dict, url: str):
        """Handle 5xx Server errors."""
        logger.error(f"Request payload: {payload}")
        logger.error(
            f"[{self.provider}] Server error ({response.status_code}): {response.text}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "status": False,
                "statusCode": response.status_code,
                "message": f"Server error: {response.text}",
                "provider": self.provider,
            },
        )

    def _handle_generic_error(self, response: httpx.Response, message: str):
        """Handle unclassified status codes."""
        logger.error(
            f"[{self.provider}] Unexpected status {response.status_code}: {message}"
        )

        raise HTTPException(
            status_code=response.status_code,
            detail={
                "status": False,
                "statusCode": response.status_code,
                "message": message,
                "provider": self.provider,
            },
        )

    async def initiate_payment(self, data: dict):
        try:
            data = {"amount": (data.get("amount") * 100), "email": data.get("email")}
            endpoint = "/transaction/initialize"
            resp = await self.make_request("POST", endpoint, data)
            return resp
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"@initialize_transaction ->{e} ",
            )
            # return None

    async def format_paystack_resp(self, data: dict):
        pass

    async def paystack_success_webhook(self, data: dict):
        payload = {}
        tranx = await self.db.scalar(
            select(Transaction).where(
                Transaction.provider_reference == data.get("reference")
            )
        )

        if not tranx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction not found"
            )

        await handle_success_payment(
            db=self.db, payload=payload, transaction=tranx, provider_payload=data
        )

        return

    async def paystack_failed_webhook(self, data: dict):
        payload = {}
        tranx = await self.db.scalar(
            select(Transaction).where(
                Transaction.provider_reference == data.get("reference")
            )
        )
        if not tranx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction not found"
            )
        await handle_failed_payment(
            db=self.db, payload=payload, transaction=tranx, provider_payload=data
        )


class PaymentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.paystack_base_client = PaystackServiceBaseAPIClient(
            settings=get_settings(), provider="PAYSTACK", db=db
        )

    async def make_payment(self, provider: str, invoice_id: str, user_email: str):
        try:
            invoice = await self.db.scalar(
                select(Invoice).where(Invoice.invoice_id == invoice_id)
            )
            if not invoice:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not Found"
                )

            if invoice.status == "PAID":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="This invoice has been paid for",
                )

            resp = {}
            if provider == "PAYSTACK":
                paystack_payload = {
                    "email": user_email,
                    "amount": float(invoice.amount),
                }
                resp = await self.paystack_base_client.initiate_payment(
                    paystack_payload
                )
                resp = resp.get("data")
            else:
                pass

            txn_ref = f"TXN-{int(time())}-{uuid.uuid4().hex[:8].upper()}"
            transaction_data = {
                "invoice_id": invoice_id,
                "authorization_url": resp.get("authorization_url"),
                "reference": txn_ref,
                "provider_reference": resp.get("reference"),
                "amount": float(invoice.amount),
                "currency": "NGN",
                "project_id": str(invoice.project_id),
                "provider": provider,
                "provider_payload": resp,  # This is now a separate object, no circle!
                "status": "PENDING",  # Good practice to ensure status is set
                "payment_method": "card",
            }
            response = await self.log_transaction(transaction_data)
            return {
                "data": response,
                "message": "Payment Created Please Continue to make payment",
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Payment Error-> {e}"
            )

    async def generate_invoice_number(self, project_id: str) -> str:
        """
        Generate invoice number based on project_id + timestamp hash.
        Format: INV-<first8chars_of_hash>
        """
        now = datetime.now(tz=timezone.utc).isoformat()
        base_string = f"{project_id}-{now}"
        hash_val = hashlib.sha256(base_string.encode()).hexdigest()[:8].upper()

        return f"INV-{hash_val}"

    # async def generate_payment_invoice(
    #     self, project_id: str, plan_id: str, project: BuildingProject
    # ):
    #     # invoice number
    #     plan = await self.db.get(Plan, plan_id)
    #     if not plan:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="plan not found"
    #         )
    #     invoice = None

    #     if plan.plan_status != "Free":
    #         invoice_number = await self.generate_invoice_number(project_id)
    #         invoice = Invoice(
    #             project_id=project_id,
    #             plan_id=plan_id,
    #             invoice_id=invoice_number,
    #             currency=plan.currency,
    #             amount=plan.amount,
    #             issued_at=datetime.now(tz=timezone.utc),
    #             due_date=datetime.now(tz=timezone.utc).date(),
    #         )
    #         self.db.add(invoice)
    #         await self.db.flush()
    #         await self.db.refresh(invoice)

    #     else:
    #         project.subscription_end_date = (
    #             get_next_cycle_date(
    #                 datetime.now(tz=timezone.utc).date(),
    #                 plan.frequency,
    #                 1,
    #             ),
    #         )

    #         project.payment_status = "Active"
    #         project.plan_id = plan_id

    #     # Before creating new payment_history check if has any pending is
    #     # if he has then update it instead of creating new one

    #     history_stmt = (
    #         select(PaymentHistory)
    #         .where(
    #             PaymentHistory.project_id == project_id,
    #             PaymentHistory.status == "Pending",
    #         )
    #         .with_for_update()
    #     )

    #     pending_history = (await self.db.execute(history_stmt)).scalar_one_or_none()

    #     if not pending_history:
    #         payment_history = PaymentHistory(
    #             project_id=project_id,
    #             plan_id=plan_id,
    #             invoice_id=invoice.invoice_id if invoice else None,
    #             currency=plan.currency,
    #             amount=plan.amount,
    #             months=1,  # default to montly,
    #             status="Pending",
    #             start_date=datetime.now(tz=timezone.utc).date(),
    #             next_billing_date=get_next_cycle_date(
    #                 datetime.now(tz=timezone.utc).date(),  # <- pass actual date
    #                 plan.frequency,
    #                 1,
    #             ),
    #         )

    #         self.db.add(payment_history)
    #     else:
    #         pending_history.invoice_id = invoice.invoice_id if invoice else None
    #         pending_history.plan_id = plan_id
    #         pending_history.start_date = datetime.now(tz=timezone.utc).date()
    #         pending_history.next_billing_date = (
    #             get_next_cycle_date(
    #                 datetime.now(tz=timezone.utc).date(),
    #                 plan.frequency,
    #                 1,
    #             ),
    #         )

    #     # PAYMENT HISTORY
    #     await self.db.commit()
    #     await self.db.refresh(payment_history)
    #     return payment_history

    async def generate_payment_invoice(
        self, project_id: str, plan_id: str, project: BuildingProject
    ):
        plan = await self.db.get(Plan, plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found",
            )

        now = datetime.now(tz=timezone.utc)
        today = now.date()

        invoice = None

        # -------------------------
        # Paid plan
        # -------------------------
        if plan.plan_status != "Free":
            invoice_number = await self.generate_invoice_number(project_id)

            invoice = Invoice(
                project_id=project_id,
                plan_id=plan_id,
                invoice_id=invoice_number,
                currency=plan.currency,
                amount=plan.amount,
                issued_at=now,
                due_date=today,
            )
            self.db.add(invoice)
            await self.db.flush()
            await self.db.refresh(invoice)

        # -------------------------
        # Free plan
        # -------------------------
        else:
            project.subscription_end_date = get_next_cycle_date(
                today,
                plan.frequency,
                1,
            )
            project.payment_status = "Active"
            project.plan_id = plan_id

        # -------------------------
        # Payment history handling
        # -------------------------
        history_stmt = (
            select(PaymentHistory)
            .where(
                PaymentHistory.project_id == project_id,
                PaymentHistory.status == "Pending",
            )
            .with_for_update()
        )

        pending_history = (await self.db.execute(history_stmt)).scalar_one_or_none()

        next_billing_date = get_next_cycle_date(
            today,
            plan.frequency,
            1,
        )

        if not pending_history:
            payment_history = PaymentHistory(
                project_id=project_id,
                plan_id=plan_id,
                invoice_id=invoice.invoice_id if invoice else None,
                currency=plan.currency,
                amount=plan.amount,
                months=1,
                status="Active" if plan.plan_status == "Free" else "Pending",
                start_date=today,
                next_billing_date=next_billing_date,
            )
            self.db.add(payment_history)

        else:
            pending_history.invoice_id = invoice.invoice_id if invoice else None
            pending_history.plan_id = plan_id
            pending_history.start_date = today
            pending_history.next_billing_date = next_billing_date

            # If free plan, mark as success
            if plan.plan_status == "Free":
                pending_history.status = "Active"

            payment_history = pending_history

        # -------------------------
        # Commit
        # -------------------------
        await self.db.commit()
        await self.db.refresh(payment_history)

        return payment_history

    async def log_transaction(self, data: dict):
        try:
            transaction = Transaction(
                invoice_id=data["invoice_id"],
                project_id=data["project_id"],
                reference=data["reference"],
                provider=data["provider"],
                provider_reference=data["provider_reference"],
                payment_method="card",
                currency=data["currency"],
                amount=data["amount"],
                provider_payload=data["provider_payload"],
                status=data["status"],
                authorization_url=data["authorization_url"],
            )

            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            return transaction
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Payment Error-> {e}"
            )

    async def payment_webhook(self, payload: dict, provider: str):
        try:
            logger.info(
                "[PAYMENT_WEBHOOK] Incoming webhook | Provider=%s | Payload keys=%s",
                provider,
                list(payload.keys()),
            )

            if provider == "PAYSTACK":
                event: str = payload.get("event")
                data: dict = payload.get("data", {})

                logger.info(
                    "[PAYSTACK_WEBHOOK] Event received | Event=%s | Reference=%s",
                    event,
                    data.get("reference"),
                )

                if event == "charge.success":
                    logger.info(
                        "[PAYSTACK_WEBHOOK] Processing SUCCESS | Reference=%s | Amount=%s",
                        data.get("reference"),
                        data.get("amount"),
                    )

                    await self.paystack_base_client.paystack_success_webhook(data)

                elif event == "charge.failed":
                    logger.warning(
                        "[PAYSTACK_WEBHOOK] Processing FAILED | Reference=%s | Reason=%s",
                        data.get("reference"),
                        data.get("gateway_response"),
                    )

                    await self.paystack_base_client.paystack_failed_webhook(data)
                else:
                    logger.warning(
                        "[PAYSTACK_WEBHOOK] Unhandled event type | Event=%s",
                        event,
                    )

            else:
                logger.warning(
                    "[PAYMENT_WEBHOOK] Unsupported provider | Provider=%s",
                    provider,
                )

        except Exception as e:
            logger.exception(
                "[PAYMENT_WEBHOOK] Critical error | Provider=%s | Error=%s",
                provider,
                str(e),
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment Error -> {e}",
            )

    def get_next_cycle_date(
        self, last_cycle_date: datetime, frequency: string, num=1
    ) -> datetime:
        due_date = None

        if frequency == "Monthly":
            due_date = last_cycle_date + relativedelta(months=num)
        elif frequency == "Yearly":
            due_date = last_cycle_date + relativedelta(years=num)
        elif frequency == "Daily":
            due_date = last_cycle_date + relativedelta(days=+1)
        elif frequency == "Weekly":
            due_date = last_cycle_date + relativedelta(weeks=+1)
        elif frequency == "Quarterly":
            due_date = last_cycle_date + relativedelta(months=+3)

        return due_date
