from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone, timedelta

from models.users import User, EmailVerificationCodes
from utils.security import get_password_hash, verify_password
from utils.helpers import email_nomalizers, generate_otp_pin
from utils.loggers import setup_logger
from dependencies.auth import create_access_token
from schemas.auth_schema import AuthResponse, UserResponse
from services.email_service import get_email_service
from constant.email_content import EMAIL_CONSTANT

logger = setup_logger("Auth_Service")


class AuthService:
    OTP_EXPIRY_MINUTES = 10

    def __init__(self, database: AsyncSession):
        self.db = database
        self.email_service = get_email_service()
        # self.background_task = BackgroundTasks()

    # ------------------------------------------------------------------
    # SIGN UP
    # ------------------------------------------------------------------
    async def sign_up(self, user_data: dict) -> User:
        email = email_nomalizers(user_data["email"])
        logger.info("Signup started | email=%s", email)

        try:
            async with self.db.begin():
                # Check email
                exists_email = await self.db.execute(
                    select(User).where(User.email == email)
                )
                if exists_email.scalar_one_or_none():
                    logger.warning("Signup failed | email exists | %s", email)
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email already registered",
                    )

                # Check phone
                # exists_phone = await self.db.execute(
                #     select(User).where(User.phone_number == user_data["phone_number"])
                # )
                # if exists_phone.scalar_one_or_none():
                #     logger.warning(
                #         "Signup failed | phone exists | %s",
                #         user_data["phone_number"],
                #     )
                #     raise HTTPException(
                #         status_code=status.HTTP_409_CONFLICT,
                #         detail="Phone number already registered",
                #     )

                user_data.update(
                    {
                        "email": email,
                        "password": get_password_hash(user_data["password"]),
                    }
                )

                user = User(**user_data, is_email_verified=True)
                self.db.add(user)
                await self.db.flush()
                await self.db.refresh(user)

            logger.info("Signup successful | user_id=%s", user.id)
            return user

        except HTTPException as http_exec:
            raise http_exec

        except SQLAlchemyError as db_err:
            logger.exception("Database error during signup | email=%s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )

        except Exception:
            logger.exception("Unexpected error during signup | email=%s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------
    async def login(self, login_data: dict):
        email = email_nomalizers(login_data["email"])
        logger.info("Login attempt | email=%s", email)

        try:
            result = await self.db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user or not verify_password(login_data["password"], user.password):
                logger.warning("Login failed | invalid credentials | %s", email)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Authentication details not found",
                )

            if not user.is_email_verified:
                logger.warning("Login blocked | email not verified | %s", email)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Please verify your email before login",
                )

            logger.info("Login successful | user_id=%s", user.id)
            return AuthResponse(
                access_token=create_access_token(str(user.id)),
                user=user,
            )

        except HTTPException:
            raise

        except Exception:
            logger.exception("Unexpected error during login | email=%s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # ------------------------------------------------------------------
    # FORGET PASSWORD
    # ------------------------------------------------------------------
    async def forget_password(self, data: dict):
        email = email_nomalizers(data["email"])
        otp = data["otp_token"]

        logger.info("Forget password request | email=%s", email)

        try:
            otp_result = await self.db.execute(
                select(EmailVerificationCodes).where(
                    EmailVerificationCodes.email == email,
                    EmailVerificationCodes.otp_code == otp,
                )
            )

            if not otp_result.scalar_one_or_none():
                logger.warning("Invalid OTP | forget password | %s", email)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email or OTP",
                )

            user_result = await self.db.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()

            if not user:
                logger.error("User not found | forget password | %s", email)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            user.password = get_password_hash(data["password"])
            await self.db.commit()

            logger.info("Password reset successful | email=%s", email)

        except HTTPException:
            raise

        except Exception:
            logger.exception("Unexpected error | forget password | %s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # ------------------------------------------------------------------
    # VERIFY EMAIL
    # ------------------------------------------------------------------
    async def verify_email(self, data: dict):
        email = email_nomalizers(data["email"])
        otp = data["otp_token"]

        logger.info("Email verification started | %s", email)

        try:
            result = await self.db.execute(
                select(EmailVerificationCodes).where(
                    EmailVerificationCodes.email == email,
                    EmailVerificationCodes.otp_code == otp,
                )
            )
            verification = result.scalar_one_or_none()

            if not verification or verification.is_expired():
                logger.warning("Invalid/expired OTP | %s", email)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired verification code",
                )

            logger.info("Email verified successfully | %s", email)
            return "Email verification successful"

        except HTTPException as exce:
            raise exce

        except Exception:
            logger.exception("Unexpected error | email verification | %s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # ------------------------------------------------------------------
    # SEND OTP
    # ------------------------------------------------------------------
    async def process_otp_request(
        self, email: str, background_task: BackgroundTasks, email_type: str = "sign_up"
    ):
        logger.info("Sending OTP | email=%s", email)

        try:
            otp = generate_otp_pin()
            expires_at = datetime.now(timezone.utc) + timedelta(
                minutes=self.OTP_EXPIRY_MINUTES
            )

            existing = await self.db.scalar(
                select(EmailVerificationCodes).where(
                    EmailVerificationCodes.email == email
                )
            )

            if existing:
                await self.db.delete(existing)

            self.db.add(
                EmailVerificationCodes(
                    email=email,
                    otp_code=otp,
                    expires_at=expires_at,
                )
            )
            await self.db.commit()

            # -----EMAIL SENDING-----------
            email_types = EMAIL_CONSTANT.get(email_type, {})
            subject = email_types.get("subject")
            template = email_types.get("templates")
            context = {"otp_code": otp}
            recepient_email = [email]

            background_task.add_task(
                self.email_service.send_emails,
                subject,
                recepient_email,
                template,
                context,
            )

            logger.info("OTP sent successfully | email=%s", email)

            return {"message": "Email Otp Sent Succesfully"}
        except Exception:
            logger.exception("OTP send failed | email=%s", email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to send OTP",
            )

    # ------------------------------------------------------------------
    # RESET PASSWORD (LOGGED IN)
    # ------------------------------------------------------------------
    async def reset_password(self, data: dict, user_id: str):
        logger.info("Reset password | user_id=%s", user_id)

        try:
            user = await self.db.get(User, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            if not verify_password(data["old_password"], user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid old password",
                )

            user.password = get_password_hash(data["new_password"])
            await self.db.commit()

            logger.info("Password reset successful | user_id=%s", user_id)
            return UserResponse.model_validate(user).model_dump()

        except HTTPException:
            raise

        except Exception:
            logger.exception("Unexpected error | reset password | %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    # ------------------------------------------------------------------
    # UPDATE PROFILE
    # ------------------------------------------------------------------
    async def update_user_profile(self, data: dict, user_id: str):
        logger.info("Profile update | user_id=%s", user_id)

        try:
            user = await self.db.get(User, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )

            fields_to_update = ("first_name", "last_name", "image_url")

            for field in fields_to_update:
                # Check if field exists AND is not None
                if field in data and data[field] is not None:
                    value = data[field]

                    # Fix for the "got dict, expected str" error for image_url
                    if field == "image_url" and isinstance(value, dict):
                        value = value.get("image_url")

                    setattr(user, field, value)

            await self.db.commit()

            logger.info("Profile updated | user_id=%s", user_id)
            return UserResponse.model_validate(user).model_dump()

        except HTTPException:
            raise

        except Exception:
            logger.exception("Unexpected error | profile update | %s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
