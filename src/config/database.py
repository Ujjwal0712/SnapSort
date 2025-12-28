"""
Database Configuration
PostgreSQL connection pool using psycopg[pool]
"""

from psycopg_pool import ConnectionPool, AsyncConnectionPool
from contextlib import contextmanager, asynccontextmanager
from typing import Generator, AsyncGenerator
import psycopg
from psycopg.rows import dict_row

from src.config.settings import settings


def _get_connection_string() -> str:
    """Convert DATABASE_URL to psycopg-compatible format.
    
    Strips SQLAlchemy driver prefixes like +psycopg or +asyncpg.
    """
    db_url = settings.DATABASE_URL
    # Remove SQLAlchemy driver prefixes
    if db_url.startswith("postgresql+psycopg://"):
        return db_url.replace("postgresql+psycopg://", "postgresql://")
    elif db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("postgresql+asyncpg://", "postgresql://")
    return db_url


# Synchronous connection pool
pool: ConnectionPool | None = None


def init_pool() -> ConnectionPool:
    """Initialize the synchronous connection pool"""
    global pool
    if pool is None:
        pool = ConnectionPool(
            conninfo=_get_connection_string(),
            min_size=settings.POOL_MIN_SIZE,
            max_size=settings.POOL_MAX_SIZE,
            open=True,
            kwargs={"row_factory": dict_row}
        )
    return pool


def close_pool() -> None:
    """Close the synchronous connection pool"""
    global pool
    if pool is not None:
        pool.close()
        pool = None


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """Get a connection from the pool (context manager)"""
    if pool is None:
        raise RuntimeError("Connection pool not initialized. Call init_pool() first.")
    with pool.connection() as conn:
        yield conn


@contextmanager
def get_db_cursor() -> Generator[psycopg.Cursor, None, None]:
    """Get a cursor from a pooled connection (context manager)"""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            yield cur


# Async connection pool
async_pool: AsyncConnectionPool | None = None


async def init_async_pool() -> AsyncConnectionPool:
    """Initialize the async connection pool"""
    global async_pool
    if async_pool is None:
        async_pool = AsyncConnectionPool(
            conninfo=_get_connection_string(),
            min_size=settings.POOL_MIN_SIZE,
            max_size=settings.POOL_MAX_SIZE,
            open=False,
            kwargs={"row_factory": dict_row}
        )
        await async_pool.open()
    return async_pool


async def close_async_pool() -> None:
    """Close the async connection pool"""
    global async_pool
    if async_pool is not None:
        await async_pool.close()
        async_pool = None


@asynccontextmanager
async def get_async_db_connection() -> AsyncGenerator[psycopg.AsyncConnection, None]:
    """Get an async connection from the pool (context manager)"""
    if async_pool is None:
        raise RuntimeError("Async connection pool not initialized. Call init_async_pool() first.")
    async with async_pool.connection() as conn:
        yield conn


@asynccontextmanager
async def get_async_db_cursor() -> AsyncGenerator[psycopg.AsyncCursor, None]:
    """Get an async cursor from a pooled connection (context manager)"""
    async with get_async_db_connection() as conn:
        async with conn.cursor() as cur:
            yield cur
