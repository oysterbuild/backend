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
)
from httpx import _status_codes
from schemas.auth_schema import (
    SignupRequest,
    UserResponse,
    EmailVerificationRequest,
    LoginRequest,
    SuccessResponse,
    ForgetPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
    SendOTPRequest,
)
from services.auth_service import AuthService
from utils.db_setup import get_database
from sqlalchemy.ext.asyncio import AsyncSession
from utils.db_setup import get_database
from dependencies.auth import get_current_user
from utils.file_upload import upload_file_optimized

router = APIRouter(prefix="/auth")


# make singleton
def get_auth_service(db: AsyncSession = Depends(get_database)) -> AuthService:
    return AuthService(database=db)


@router.post("/sign-up", response_model=SuccessResponse)
async def sign_up(
    request_body: SignupRequest, auth_service: AuthService = Depends(get_auth_service)
):
    result = await auth_service.sign_up(user_data=request_body.model_dump())
    return SuccessResponse(
        data=UserResponse.model_validate(result).model_dump(),
        status_code=200,
        message="user registration successful",
    )


@router.post("/sign-in", response_model=SuccessResponse)
async def sign_in(
    request_body: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    result = await auth_service.login(login_data=request_body.model_dump())
    return SuccessResponse(
        data=result,
        status_code=200,
        message="Login successful",
    )


@router.post("/email-verification", response_model=SuccessResponse)
async def email_verification(
    request_body: EmailVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.verify_email(verification_data=request_body.model_dump())
    return SuccessResponse(
        status_code=200,
        message="Email Verification successful",
    )


@router.post("/send-otp")
async def send_otp_pin(
    request_data: SendOTPRequest,  # Email is now in the body, safer for logs
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    # Use request_data.email and request_data.email_type
    return await auth_service.process_otp_request(
        email=request_data.email,
        email_type=request_data.email_type,
        background_task=background_tasks,
    )


@router.post("/forget-password", response_model=SuccessResponse)
async def forget_password(
    request_body: ForgetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    await auth_service.forget_password(request_body.model_dump())
    return SuccessResponse(
        status_code=200,
        message="Password Reset Successful",
    )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_passoword(
    request_body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("id"))
    response = await auth_service.reset_password(request_body.model_dump(), user_id)
    return SuccessResponse(
        status_code=200,
        data=response,
        message="Password Reset Successful",
    )


@router.get("/user/me", response_model=SuccessResponse)
async def get_user_me(current_user: dict = Depends(get_current_user)):
    return SuccessResponse(
        status_code=200,
        data=UserResponse(**current_user),
        message="User Fetched Successful",
    )


@router.put("/user/me", response_model=SuccessResponse)
async def user_me(
    first_name: str = Form(None, description="Your First Name John"),
    last_name: str = Form(None, description="Your Last Name Doe"),
    profile_image: UploadFile = File(None, description="Upload User Profile"),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user.get("id"))

    profile_pic_url = None
    if profile_image:
        profile_pic_url = await upload_file_optimized(
            profile_image, "profile_images", user_id, current_user, "PROFILE_IMAGES"
        )
    request_body = {
        "first_name": first_name,
        "last_name": last_name,
        "image_url": profile_pic_url["image_url"],
    }

    response = await auth_service.update_user_profile(request_body, user_id)
    return SuccessResponse(
        status_code=200,
        data=response,
        message="User Update Successful",
    )
