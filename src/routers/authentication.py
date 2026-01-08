"""
Authentication Router
Routes for user registration, login, OTP verification, and authentication.
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks, Header
from psycopg_pool import AsyncConnectionPool

from src.services.authentication.registration import RegistrationService
from src.services.authentication.otp import OtpService
from src.services.authentication.login import LoginService
from src.schemas.authentication import (
    RegistrationRequest, 
    OtpVerificationRequest, 
    CompleteRegistrationRequest,
    ImageKitAuthResponse,
    LoginRequest,
    RefreshTokenRequest,
)
from src.utils.token import create_registration_token, verify_registration_token
from src.utils.imagekit import generate_auth_params
from src.utils.response import success_response, error_response
from src.middlewares.auth import get_current_user, CurrentUser


router = APIRouter()


# Dependency to get db pool from app state
def get_db_pool(request: Request) -> AsyncConnectionPool:
    """Get database pool from app state."""
    return request.app.state.db_pool


@router.post("/register")
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
    result = await service.register_user(data, background_tasks)

    if not result:
        return error_response(500, "Server error")
    
    registration_token = create_registration_token(str(result["user_id"]))
    
    return success_response(201, result["message"], {"token": registration_token})


@router.post("/verify-otp")
async def verify_otp(
    data: OtpVerificationRequest,
    authorization: str = Header(..., description="Registration token from OTP verification"),
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
    # Extract token from Authorization header (supports "Bearer <token>" format)
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # Verify the registration token
    payload = verify_registration_token(token)
    user_id = payload.get("sub")

    otp_service = OtpService(db_pool)
    is_valid = await otp_service.verify_otp(data, user_id)
    
    if not is_valid:
        return error_response(400, "Invalid or expired OTP")
    
    return success_response(200, "OTP verified successfully")


@router.get("/upload-signature")
async def get_upload_signature(
    authorization: str = Header(..., description="Registration token from OTP verification")
):
    """
    Get ImageKit authentication parameters for client-side selfie upload.
    
    Requires a valid registration token in Authorization header.
    
    Returns:
        200: ImageKit authentication parameters (token, expire, signature)
        401: Invalid or expired registration token
    """
    # Extract token from Authorization header
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # Verify the registration token
    payload = verify_registration_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        return error_response(401, "Invalid registration token")
    
    # Generate ImageKit auth params
    auth_data = generate_auth_params()
    
    return success_response(200, "Upload signature generated", auth_data)


@router.post("/complete-registration")
async def complete_registration(
    data: CompleteRegistrationRequest,
    authorization: str = Header(..., description="Registration token from OTP verification"),
    db_pool: AsyncConnectionPool = Depends(get_db_pool)
):
    """
    Complete registration with username, password, and selfie.
    
    Requires a valid registration token in Authorization header.
    
    Returns:
        200: Registration completed successfully
        400: Username already taken
        401: Invalid or expired registration token
        404: User not found
        500: Server error
    """
    # Extract token from Authorization header (supports "Bearer <token>" format)
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # Verify the registration token
    payload = verify_registration_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        return error_response(401, "Invalid registration token")
    
    # Complete registration
    service = RegistrationService(db_pool)
    result = await service.complete_registration(
        user_id=user_id,
        username=data.username,
        password=data.password,
        selfie_url=data.selfie_url,
        file_id=data.file_id
    )
    
    return success_response(200, result["message"])


@router.post("/login")
async def login(
    data: LoginRequest,
    db_pool: AsyncConnectionPool = Depends(get_db_pool)
):
    """
    Authenticate user with email/username and password.
    
    Returns:
        200: Login successful with tokens
        401: Invalid credentials or inactive account
        500: Server error
    """
    service = LoginService(db_pool)
    result = await service.login(data)
    
    return success_response(200, "Login successful", result)


@router.post("/refresh")
async def refresh_token(
    data: RefreshTokenRequest,
    db_pool: AsyncConnectionPool = Depends(get_db_pool)
):
    """
    Refresh access token using a valid refresh token.
    
    No access token required - only validates the refresh token.
    
    Returns:
        200: New access token
        401: Invalid or expired refresh token
    """
    service = LoginService(db_pool)
    result = await service.refresh_tokens(data.refresh_token)
    
    return success_response(200, "Token refreshed successfully", result)


@router.post("/logout")
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
    db_pool: AsyncConnectionPool = Depends(get_db_pool)
):
    """
    Logout user by invalidating the current session.
    
    Requires valid access token in Authorization header.
    
    Returns:
        200: Logged out successfully
    """
    service = LoginService(db_pool)
    await service.logout(current_user.session_id)
    
    return success_response(200, "Logged out successfully")
