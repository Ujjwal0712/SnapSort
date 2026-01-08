"""
Standardized API Response Utilities
Provides consistent response format across all endpoints.
"""

from typing import Any, Optional
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class APIResponse(BaseModel):
    """Standardized API response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[Any] = None


def success_response(
    status_code: int,
    message: str,
    data: Any = None
) -> JSONResponse:
    """
    Send a standardized success response.
    
    Args:
        status_code: HTTP status code (e.g., 200, 201)
        message: Success message
        data: Optional response data
        
    Returns:
        JSONResponse with standardized format
    """
    response = {
        "success": True,
        "message": message,
    }
    if data is not None:
        response["data"] = data
    
    return JSONResponse(status_code=status_code, content=response)


def error_response(
    status_code: int,
    message: str,
    error: Any = None
) -> JSONResponse:
    """
    Send a standardized error response.
    
    Args:
        status_code: HTTP status code (e.g., 400, 500)
        message: Error message
        error: Optional error details
        
    Returns:
        JSONResponse with standardized format
    """
    response = {
        "success": False,
        "message": message,
    }
    
    if error is not None:
        if isinstance(error, Exception):
            response["error"] = str(error)
        else:
            response["error"] = error
    
    return JSONResponse(status_code=status_code, content=response)


def message_response(
    status_code: int,
    message: str
) -> JSONResponse:
    """
    Send a standardized message-only response (usually for simple success).
    
    Args:
        status_code: HTTP status code
        message: Response message
        
    Returns:
        JSONResponse with standardized format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
        }
    )
