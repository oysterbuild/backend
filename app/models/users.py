from time import timezone
from models.base_model import BaseModel
from sqlalchemy import (
    String,
    Column,
    Boolean,
    UniqueConstraint,
    DateTime,
    Text,
    CheckConstraint,
)
from datetime import datetime, timedelta, timezone

# NB ROLE MANAGEMENT FOR REGISTER USER THE ROLE ARE admin,user,super_admin


class User(BaseModel):
    first_name = Column(String(225), nullable=False)
    last_name = Column(String(225), nullable=False)
    email = Column(String(500), nullable=False, unique=True, index=True)
    phone_number = Column(String(15), nullable=False, unique=True)
    password = Column(String(500), nullable=False)
    is_email_verified = Column(Boolean(), default=False)
    image_url = Column(Text, nullable=True)
    role = Column(
        String(20), nullable=False, server_default="USER"
    )  # Added user role, admin,super_admin,user

    __table_args__ = (
        CheckConstraint(
            "role IN ('SUPER_ADMIN', 'USER')",
            name="check_user_role_valid",
        ),
    )

    @property
    def full_name_details(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "image_url": self.image_url,
        }


class EmailVerificationCodes(BaseModel):
    email = Column(String(500), nullable=False, index=True)
    otp_code = Column(String(4), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("email", "otp_code", name="uq_email_otp"),)

    def is_expired(self) -> bool:
        return datetime.now(tz=timezone.utc) > self.expires_at
