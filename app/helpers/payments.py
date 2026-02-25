import asyncio
from models.payments import Invoice, Transaction
from models.plans import PaymentHistory, Plan,PlanPackageUsageCount
from models.building_project import BuildingProject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists, update,delete
from datetime import datetime, timezone
from fastapi import HTTPException, BackgroundTasks
from services.email_service import get_email_service
from models.users import User
from helpers.constant import get_next_cycle_date


async def handle_success_payment(
    db: AsyncSession, payload: dict, transaction: Transaction, provider_payload: dict
):

    invoice = await db.scalar(
        select(Invoice).where(Invoice.invoice_id == transaction.invoice_id)
    )
    if not invoice:
        raise HTTPException(
            status_code=400,
            detail="Invoice not found",
        )

    # update invoice
    invoice.status = "PAID"
    invoice.paid_at = datetime.now(tz=timezone.utc)

    # update transaction;
    transaction.status = "SUCCESS"
    transaction.paid_at = datetime.now(tz=timezone.utc)
    transaction.provider_payload = provider_payload

    # get the plan in the project
    plan = await db.get(Plan, invoice.plan_id)

    # Get and update history and make it paid:
    tranx_history = await db.scalar(
        select(PaymentHistory).where(
            PaymentHistory.invoice_id == transaction.invoice_id
        )
    )

    tranx_history.status = "Active"
    tranx_history.start_date = datetime.now(tz=timezone.utc).date()
    tranx_history.next_billing_date = get_next_cycle_date(
        datetime.now(tz=timezone.utc).date(),  # <- pass actual date
        plan.frequency,
        1,
    )

    project_id=invoice.project_id

    # update the project status and the plan
    project = await db.get(BuildingProject, project_id)

    if not project:
        raise HTTPException(
            status_code=400,
            detail="Invoice not found",
        )

    project.plan_id = invoice.plan_id
    project.payment_status = "Active"
    project.subscription_end_date = get_next_cycle_date(
        datetime.now(tz=timezone.utc).date(),  # <- pass actual date
        plan.frequency,
        1,
    )

    #clear all usage:
    delete_stmt = delete(PlanPackageUsageCount).where(
        PlanPackageUsageCount.project_id == project_id
    )

    await db.execute(delete_stmt)
    # save all
    await db.commit()

    # Get the user
    user = await db.get(User, project.owner_id)

    template_data = {
        "user_name": user.first_name,
        "plan_name": plan.name,
        "amount": f"{transaction.amount:,.2f}",
        "currency": transaction.currency,
        "reference": transaction.reference or transaction.provider_reference,
        "next_billing_date": tranx_history.next_billing_date.strftime("%d %b %Y"),
    }
    recipient = [user.email]

    email_subject = "Subscription Successful"

    # run under
    await asyncio.create_task(
        get_email_service().send_emails(
            subject=email_subject,
            recipient=recipient,
            template_name="subsciption_update.html",
            context=template_data,
        )
    )

    # Get the reference from transactions


async def handle_failed_payment(
    db: AsyncSession, payload: dict, transaction: Transaction, provider_payload: dict
):

    invoice = await db.scalar(
        select(Invoice).where(Invoice.invoice_id == transaction.invoice_id)
    )
    if not invoice:
        raise HTTPException(
            status_code=400,
            detail="Invoice not found",
        )

    invoice.status = "FAILED"
    invoice.paid_at = datetime.now(tz=timezone.utc)

    # update transaction;
    transaction.status = "FAILED"
    transaction.paid_at = datetime.now(tz=timezone.utc)
    transaction.provider_payload = provider_payload

    await db.commit()
