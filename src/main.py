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
    debug=settings.DEBUG,
    lifespan=lifespan
)


# Include routers
app.include_router(authentication.router, prefix="/auth", tags=["Authentication"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME}
