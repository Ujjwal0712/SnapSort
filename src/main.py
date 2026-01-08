"""
SnapSort API
Main FastAPI application with database connection pool lifecycle management.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.config.settings import settings
from src.config.database import init_async_pool, close_async_pool
from src.config.logger import logger
from src.routers import authentication
from src.middlewares.response_time import ResponseTimeMiddleware
from src.middlewares.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events."""
    # Startup
    logger.info("Starting SnapSort API...")
    pool = await init_async_pool()
    logger.info("Database connection pool initialized")
    
    # Store pool in app state so routes/services can access it
    app.state.db_pool = pool
    
    yield
    
    # Shutdown
    logger.info("Shutting down SnapSort API...")
    await close_async_pool()
    logger.info("Database connection pool closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
            ## SnapSort - AI-Powered Photo Segregation System

            SnapSort is a photo-sharing application that uses **AI-based face recognition** 
            to automatically segregate and show users only the photos where they appear.

            ### Key Features:
            - 🎯 **Smart Photo Segregation**: AI detects faces and matches them to users
            - 👥 **Groups & Organizations**: Create groups for events, manage members
            - 📸 **Bulk Upload**: Upload many photos at once, processed in background
            - 🔐 **Secure Access**: Only see photos where you appear
            - 📥 **Easy Download**: Download your photos individually or in bulk

            ### Face Recognition Providers:
            - DeepFace (local, free)
            - InsightFace (local, better accuracy)
            - AWS Rekognition (cloud)
            - Google Vision (cloud)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(ResponseTimeMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(authentication.router, prefix="/auth", tags=["Authentication"])


# Exception handlers for standardized error responses
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.utils.exceptions import ServiceException


@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    """Convert ServiceException to standardized error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error": exc.error if exc.error else exc.message
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTPException to standardized error response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "error": exc.detail
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert validation errors to standardized error response."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body' prefix
        errors.append({
            "field": field,
            "message": error["msg"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation error",
            "error": errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with standardized error response."""
    logger.error("Unexpected error: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc) if settings.DEBUG else None
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"success": True, "message": "healthy", "data": {"app": settings.APP_NAME}}
