from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
from jwt import PyJWTError as JWTError
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, UTC, timezone
from models.users import User
from sqlalchemy.sql.functions import user
from utils.db_setup import get_database
from settings import get_settings
from utils.loggers import setup_logger
from schemas.auth_schema import UserResponse

# Set up logger
logger = setup_logger(__name__)

# Get settings
settings = get_settings()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_session: AsyncSession = Depends(get_database),
) -> Dict[str, Any]:
    """
    Get the current authenticated user from the JWT token.

    Args:
        token: JWT token from the Authorization header

    Returns:
        Dictionary with user details

    Raises:
        HTTPException: If the token is invalid or the user is not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        user_id: str = payload.get("sub", None)  # Get the user_id from the token
        exp = payload.get("exp")

        # Validate token data
        if not user_id:
            logger.warning("Token has no identifier (neither subject nor user_id)")
            raise credentials_exception

        # Normalize exp into a datetime
        exp_dt = None
        if exp is not None:
            if isinstance(exp, (int, float)):
                exp_dt = datetime.fromtimestamp(exp, tz=UTC)
            elif isinstance(exp, str):
                try:
                    exp_dt = datetime.fromisoformat(exp)
                    if exp_dt.tzinfo is None:
                        exp_dt = exp_dt.replace(tzinfo=UTC)
                except Exception:
                    exp_dt = None
            else:
                # Some JWT libs may return datetime objects directly
                try:
                    if hasattr(exp, "tzinfo"):
                        exp_dt = exp if exp.tzinfo else exp.replace(tzinfo=UTC)
                except Exception:
                    exp_dt = None

        if exp_dt is None or datetime.now(UTC) > exp_dt:
            logger.warning("Token has expired")
            logger.warning(
                f"Current time: {datetime.now(UTC)}, Expiration: {exp_dt if exp_dt else 'None'}"
            )
            raise credentials_exception

        user_data = await db_session.get(User, user_id)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Token, Authentication has Expired Please Login",
            )

        return UserResponse.model_validate(user_data).model_dump()

    except ExpiredSignatureError:
        logger.error("Authentication error: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Your session has expired. Please log in again.",
        )

    except TimeoutError:
        logger.error("Authentication error: Token verification timed out")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Timeout occurred during verification. Try again later.",
        )

    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        logger.error(f"Authentication error: {status.HTTP_401_UNAUTHORIZED}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: request timed out",
        )


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[Dict[str, Any]]:
    """
    Get the current user if authenticated, or None if not.
    This allows endpoints to support both authenticated and unauthenticated access.

    Args:
        token: Optional JWT token

    Returns:
        User data dictionary or None
    """
    if not token:
        return None

    try:
        return await get_current_user(token)
    except HTTPException:
        return None


def create_access_token(user_id: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user_id: The ID of the user
        expires_delta: Optional expiration time, defaults to settings value

    Returns:
        JWT token string
    """
    # Set expiration time
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_token_expire_minutes)

    # Create token data with expiration
    expires = datetime.now(UTC) + expires_delta

    # Create JWT payload
    to_encode = {
        "sub": user_id,
        "exp": expires,
        "iat": datetime.now(UTC),
        "type": "access",
    }

    # Encode and return token
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt
