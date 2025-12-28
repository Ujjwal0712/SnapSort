"""
Registration Schemas
Pydantic models for registration requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class RegistrationRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")

class RegistrationResponse(BaseModel):
    user_id: UUID = Field(..., description="User UUID")
    
class OtpVerificationRequest(BaseModel):
    user_id: UUID = Field(..., description="User UUID")
    otp: str = Field(..., description="OTP to verify")