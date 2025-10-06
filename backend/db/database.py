"""
Database connection management and session handling.

This module provides:
- PostgreSQL connection pooling with SQLAlchemy
- Redis connection management
- Async session management
- Connection health checks
- Proper resource cleanup
"""

import time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, text
from redis.asyncio import Redis, ConnectionPool
from typing import AsyncGenerator

from config.settings import settings
from utils.logging import get_logger, log_database_query

logger = get_logger(__name__)

# SQLAlchemy
logger.info("Creating database engine", extra={"database_url": settings.database_url.split("@")[-1]})
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.app_env == "development",
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# Redis
redis_pool: ConnectionPool | None = None
redis_client: Redis | None = None


async def init_db():
    """
    Initialize database connections.
    
    This function:
    - Sets up Redis connection pool
    - Verifies database connectivity
    - Creates tables if needed (dev only)
    """
    global redis_pool, redis_client
    
    logger.info("Initializing database connections")
    
    try:
        # Initialize Redis
        logger.info("Connecting to Redis", extra={"redis_url": settings.redis_url.split("@")[-1]})
        redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            decode_responses=True,
        )
        redis_client = Redis(connection_pool=redis_pool)
        
        # Test Redis connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
        
        # Test database connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")
        
        # Create tables in development (use Alembic in production)
        if settings.app_env == "development":
            logger.info("Creating database tables (development mode)")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
        
    except Exception as e:
        logger.error("Failed to initialize database connections", exc_info=True)
        raise


async def close_db():
    """
    Close database connections gracefully.
    
    This ensures all connections are properly closed during shutdown.
    """
    global redis_client, redis_pool
    
    logger.info("Closing database connections")
    
    try:
        if redis_client:
            await redis_client.aclose()
            logger.info("Redis connection closed")
        
        if redis_pool:
            await redis_pool.aclose()
            logger.info("Redis pool closed")
        
        await engine.dispose()
        logger.info("Database engine disposed")
        
    except Exception as e:
        logger.error("Error closing database connections", exc_info=True)
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database sessions.
    
    Provides:
    - Automatic transaction management
    - Proper error handling and rollback
    - Connection cleanup
    
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    start_time = time.time()
    session = AsyncSessionLocal()
    
    try:
        logger.debug("Database session created")
        yield session
        await session.commit()
        
        duration = time.time() - start_time
        log_database_query(
            operation="session",
            table="N/A",
            duration=duration,
        )
        
    except Exception as e:
        logger.error("Database session error, rolling back", exc_info=True)
        await session.rollback()
        
        duration = time.time() - start_time
        log_database_query(
            operation="session",
            table="N/A",
            duration=duration,
            error=str(e),
        )
        raise
        
    finally:
        await session.close()
        logger.debug("Database session closed")


async def get_redis() -> Redis:
    """
    Dependency for Redis client.
    
    Returns:
        Redis client instance
        
    Raises:
        RuntimeError: If Redis is not initialized
    """
    if redis_client is None:
        logger.error("Redis client requested but not initialized")
        raise RuntimeError("Redis not initialized")
    return redis_client


async def health_check_db() -> bool:
    """
    Check database health.
    
    Returns:
        True if database is healthy, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error("Database health check failed", exc_info=True)
        return False


async def health_check_redis() -> bool:
    """
    Check Redis health.
    
    Returns:
        True if Redis is healthy, False otherwise
    """
    try:
        if redis_client:
            await redis_client.ping()
            return True
        return False
    except Exception as e:
        logger.error("Redis health check failed", exc_info=True)
        return False
