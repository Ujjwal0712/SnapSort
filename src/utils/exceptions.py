"""
Custom Service Exceptions
Standardized exceptions for service layer operations.
"""

from typing import Optional, Any


class ServiceException(Exception):
    """Base exception for service layer errors."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error = error
        super().__init__(message)


class BadRequestException(ServiceException):
    """400 Bad Request - Invalid input or business rule violation."""
    
    def __init__(self, message: str, error: Optional[Any] = None):
        super().__init__(message, status_code=400, error=error)


class UnauthorizedException(ServiceException):
    """401 Unauthorized - Authentication required or failed."""
    
    def __init__(self, message: str, error: Optional[Any] = None):
        super().__init__(message, status_code=401, error=error)


class ForbiddenException(ServiceException):
    """403 Forbidden - Access denied."""
    
    def __init__(self, message: str, error: Optional[Any] = None):
        super().__init__(message, status_code=403, error=error)


class NotFoundException(ServiceException):
    """404 Not Found - Resource not found."""
    
    def __init__(self, message: str, error: Optional[Any] = None):
        super().__init__(message, status_code=404, error=error)


class ConflictException(ServiceException):
    """409 Conflict - Resource already exists."""
    
    def __init__(self, message: str, error: Optional[Any] = None):
        super().__init__(message, status_code=409, error=error)


class InternalServerException(ServiceException):
    """500 Internal Server Error - Unexpected server error."""
    
    def __init__(self, message: str = "Internal server error", error: Optional[Any] = None):
        super().__init__(message, status_code=500, error=error)


class DatabaseTimeoutException(ServiceException):
    """503 Service Unavailable - Database timeout."""
    
    def __init__(self, message: str = "Database connection timeout", error: Optional[Any] = None):
        super().__init__(message, status_code=503, error=error)
