"""
Login Schemas
Pydantic models for login requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or username")
    password: str = Field(..., description="User password")
    device_info: Optional[str] = Field(None, description="Device information (e.g., 'iPhone 15, iOS 17.0')")
    ip_address: Optional[str] = Field(None, description="Client IP address")


class LoginResponse(BaseModel):
    message: str = Field(..., description="Response message")
    user_id: str = Field(..., description="User UUID")
    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived refresh token")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token to exchange")


class RefreshTokenResponse(BaseModel):
    access_token: str = Field(..., description="New access token")
