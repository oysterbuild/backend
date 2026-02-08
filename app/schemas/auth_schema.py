from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, Any, Literal
from uuid import UUID
from datetime import datetime

from sqlalchemy import DateTime

# =========================
# AUTH REQUEST SCHEMAS
# =========================


class SuccessResponse(BaseModel):
    success: bool = True
    status_code: int = 200
    message: str
    data: Optional[Any] = None


class SignupRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=225)
    last_name: str = Field(..., min_length=1, max_length=225)
    email: EmailStr
    phone_number: str = Field(..., min_length=7, max_length=15)
    password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Ayomide",
                "last_name": "Fagbemi",
                "email": "ayo@example.com",
                "phone_number": "+2348100000000",
                "password": "StrongPassword123",
            }
        }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr
    otp_token: str


class ForgetPasswordRequest(BaseModel):
    password: str
    confirm_password: str
    email: EmailStr
    otp_token: str

    @model_validator(mode="before")
    def check_passwords_match(cls, values: dict[str, Any]) -> dict[str, Any]:
        password = values.get("password")
        confirm = values.get("confirm_password")
        if password != confirm:
            raise ValueError("Password and confirm_password must match")
        return values


class ResetPasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_new_password: str

    @model_validator(mode="before")
    def check_passwords_match(cls, values: dict[str, Any]) -> dict[str, Any]:
        new_password = values.get("new_password")
        confirm_new_password = values.get("confirm_new_password")
        if new_password != confirm_new_password:
            raise ValueError("new_password and confirm_password must match")
        return values


class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = Field(None, max_length=225)
    last_name: Optional[str] = Field(None, max_length=225)

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Ayomide",
                "last_name": "Fagbemi",
            }
        }


# =========================
# AUTH RESPONSE SCHEMAS
# =========================


class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    is_email_verified: bool
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    user: UserResponse


class EmailVerificationResponse(BaseModel):
    message: str
    is_verified: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class ErrorResponse(BaseModel):
    message: str
    errors: Optional[dict] = None


class SendOTPRequest(BaseModel):
    email: EmailStr
    email_type: Literal["sign_up", "forgot_password", "reset_password"]
