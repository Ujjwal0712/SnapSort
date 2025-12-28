"""
Middleware
Custom middleware for the FastAPI application.
"""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.config.logger import logger


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to log response time for each request."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        response = await call_next(request)
        
        process_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
        
        # Add response time to headers
        response.headers["X-Response-Time"] = f"{process_time:.2f}ms"
        
        # Log the request with response time
        logger.info(
            "%s %s - %d - %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            process_time
        )
        
        return response
