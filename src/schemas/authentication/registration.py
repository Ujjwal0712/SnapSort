"""
Registration Schemas
Pydantic models for registration requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class RegistrationRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    
class OtpVerificationRequest(BaseModel):
    otp: str = Field(..., description="OTP to verify")

class CompleteRegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=8, description="User password")
    selfie_url: str = Field(..., description="URL to user's selfie image")
    file_id: str = Field(..., description="ImageKit file ID for the selfie image")

class ImageKitAuthResponse(BaseModel):
    token: str = Field(..., description="Authentication token for upload")
    expire: int = Field(..., description="Unix timestamp when token expires")
    signature: str = Field(..., description="HMAC signature for authentication")
    folder: str = Field(..., description="Folder path to upload to")
