"""
Authentication endpoints for user registration, login, and token management.
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from utils.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    EMAIL_VERIFICATION_EXPIRE_HOURS,
    PASSWORD_RESET_EXPIRE_HOURS,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_secure_token,
    get_password_hash,
    verify_password,
)
from utils.email import send_password_reset_email, send_verification_email
from utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
security = HTTPBearer()


# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    account_tier: str

    class Config:
        from_attributes = True


# Dependency to get current user from token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# Optional dependency for endpoints that work with or without auth
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get the current user if authenticated, otherwise None."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, request: Request, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password strength
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    verification_token = generate_secure_token()
    verification_expires = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)

    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        verification_token=verification_token,
        verification_token_expires=verification_expires,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(
        "New user registered", extra={"user_id": str(new_user.id), "email": user_data.email}
    )

    # Send verification email
    base_url = str(request.base_url).rstrip("/")
    await send_verification_email(new_user.email, verification_token, base_url)

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access tokens."""
    # Get user
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("User logged in", extra={"user_id": str(user.id), "email": credentials.email})

    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Verify user exists
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Create new tokens
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (client should discard tokens)."""
    logger.info("User logged out", extra={"user_id": str(current_user.id)})
    return {"message": "Successfully logged out"}


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify user email address."""
    # Find user with this verification token
    result = await db.execute(
        select(User).where(
            User.verification_token == token,
            User.verification_token_expires > datetime.utcnow(),
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # Mark email as verified
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None

    await db.commit()

    logger.info("Email verified", extra={"user_id": str(user.id), "email": user.email})

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resend email verification link."""
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )

    # Generate new verification token
    verification_token = generate_secure_token()
    verification_expires = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)

    current_user.verification_token = verification_token
    current_user.verification_token_expires = verification_expires

    await db.commit()

    # Send verification email
    base_url = str(request.base_url).rstrip("/")
    await send_verification_email(current_user.email, verification_token, base_url)

    logger.info("Verification email resent", extra={"user_id": str(current_user.id)})

    return {"message": "Verification email sent"}


@router.post("/forgot-password")
async def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Request password reset email."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == request_data.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if not user:
        logger.warning(
            "Password reset requested for non-existent email",
            extra={"email": request_data.email},
        )
        return {"message": "If the email exists, a password reset link has been sent"}

    # Generate reset token
    reset_token = generate_secure_token()
    reset_expires = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)

    user.reset_token = reset_token
    user.reset_token_expires = reset_expires

    await db.commit()

    # Send password reset email
    base_url = str(request.base_url).rstrip("/")
    await send_password_reset_email(user.email, reset_token, base_url)

    logger.info("Password reset requested", extra={"user_id": str(user.id), "email": user.email})

    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    request_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reset password using reset token."""
    # Find user with this reset token
    result = await db.execute(
        select(User).where(
            User.reset_token == request_data.token,
            User.reset_token_expires > datetime.utcnow(),
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    # Validate new password
    if len(request_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Update password
    user.hashed_password = get_password_hash(request_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    await db.commit()

    logger.info("Password reset successful", extra={"user_id": str(user.id), "email": user.email})

    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    request_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for authenticated user."""
    # Verify current password
    if not verify_password(request_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    if len(request_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Check if new password is different from current
    if verify_password(request_data.new_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Update password
    current_user.hashed_password = get_password_hash(request_data.new_password)

    await db.commit()

    logger.info("Password changed", extra={"user_id": str(current_user.id)})

    return {"message": "Password changed successfully"}
