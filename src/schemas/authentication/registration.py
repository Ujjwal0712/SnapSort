"""
Registration Schemas
Pydantic models for registration requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class RegistrationRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    