from models.base_model import BaseModel
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import UniqueConstraint, CheckConstraint
from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Boolean,
    Float,
    ForeignKey,
    DateTime,
    DECIMAL,
    UUID,
    CheckConstraint,
    Date,
)


class Invoice(BaseModel):
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plan.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    invoice_id = Column(
        String(50), unique=True, nullable=False, index=True, primary_key=True
    )

    currency = Column(String(3), nullable=False, default="NGN")
    amount = Column(Numeric(12, 2), nullable=False)

    billing_period_months = Column(Integer, nullable=False, default=1)

    status = Column(
        String(15),
        nullable=False,
        default="PENDING",
    )

    issued_at = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(Date, nullable=False)

    paid_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'PAID', 'OVERDUE', 'CANCELLED')",
            name="check_invoice_status",
        ),
        CheckConstraint(
            "currency IN ('NGN', 'USD')",
            name="check_invoice_currency",
        ),
    )


class Transaction(BaseModel):

    invoice_id = Column(
        String(100),
        ForeignKey("invoice.invoice_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("buildingproject.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Internal reference (your system)
    reference = Column(
        String(100),
        unique=True,
        nullable=True,
        index=True,
    )
    authorization_url = Column(
        String(200),
        nullable=True,
    )
    # Payment gateway
    provider = Column(
        String(20),
        nullable=False,
    )
    # PAYSTACK | FLUTTERWAVE | STRIPE | PAYPAL | BANK_TRANSFER | CRYPTO

    # Reference from provider
    provider_reference = Column(
        String(400),
        nullable=True,
        index=True,
    )

    payment_method = Column(String(20), nullable=False, default="bank")
    # card | bank | ussd | transfer | wallet | crypto

    currency = Column(String(3), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    status = Column(
        String(15),
        nullable=False,
        default="PENDING",
    )

    paid_at = Column(DateTime(timezone=True), nullable=True)

    provider_payload = Column(
        JSONB,
        nullable=True,
        default=dict,
    )

    __table_args__ = (
        # Ensure no duplicate transactions per provider
        UniqueConstraint(
            "provider",
            "provider_reference",
            name="uq_provider_provider_reference",
        ),
        CheckConstraint(
            "provider IN ('PAYSTACK','FLUTTERWAVE','STRIPE','PAYPAL','BANK_TRANSFER','CRYPTO')",
            name="check_transaction_provider",
        ),
        CheckConstraint(
            "status IN ('SUCCESS', 'FAILED', 'REFUNDED','PENDING')",
            name="check_transaction_status",
        ),
        CheckConstraint(
            "currency IN ('NGN', 'USD')",
            name="check_transaction_currency",
        ),
    )
