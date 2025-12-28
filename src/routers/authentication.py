"""
Authentication Router
Routes for user registration, login, OTP verification, and authentication.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks
from psycopg_pool import AsyncConnectionPool

from src.services.authentication.registration import RegistrationService
from src.services.authentication.otp import OtpService
from src.schemas.authentication import RegistrationRequest, OtpVerificationRequest


router = APIRouter()


# Dependency to get db pool from app state
def get_db_pool(request: Request) -> AsyncConnectionPool:
    """Get database pool from app state."""
    return request.app.state.db_pool


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegistrationRequest,
    background_tasks: BackgroundTasks,
    db_pool: AsyncConnectionPool = Depends(get_db_pool)
):
    """
    Register a new user with email.
    
    - Creates user record
    - Queues OTP email for background sending
    
    Returns:
        201: User created, OTP queued
        400: Email already exists
        500: Server error
    """
    service = RegistrationService(db_pool)
    result = await service.registerUser(data, background_tasks)
    return result


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
async def verify_otp(
    data: OtpVerificationRequest,
    db_pool: AsyncConnectionPool = Depends(get_db_pool)
):
    """
    Verify OTP sent to user's email.
    
    Returns:
        200: OTP verified successfully
        400: Invalid OTP
        401: OTP expired or max attempts exceeded
        404: No OTP found for user
    """
    otp_service = OtpService(db_pool)
    is_valid = await otp_service.verify_otp(data)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    return {"message": "OTP verified successfully", "verified": True}
