"""
Authentication Router
Routes for user registration, login, and authentication.
"""

from fastapi import APIRouter, Depends, Request
from psycopg_pool import AsyncConnectionPool

from src.services.authentication.registration import RegistrationService


router = APIRouter()


# Dependency to get db pool from app state
def get_db_pool(request: Request) -> AsyncConnectionPool:
    """Get database pool from app state."""
    return request.app.state.db_pool


@router.post("/register")
async def register(
    request: Request,
    db_pool: AsyncConnectionPool = Depends(get_db_pool)
):
    """Register a new user."""
    # Pass pool to service
    service = RegistrationService(db_pool)
    # result = await service.register_user(data)
    return {"message": "Registration endpoint"}
