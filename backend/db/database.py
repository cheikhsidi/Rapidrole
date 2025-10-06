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
from collections.abc import AsyncGenerator

from redis.asyncio import ConnectionPool, Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config.settings import settings
from utils.logging import get_logger, log_database_query

logger = get_logger(__name__)

# SQLAlchemy
logger.info(
    "Creating database engine", extra={"database_url": settings.database_url.split("@")[-1]}
)

# Build engine kwargs - SQLite doesn't support pooling parameters
engine_kwargs = {"echo": settings.app_env == "development"}

if "sqlite" not in settings.database_url.lower():
    # PostgreSQL/MySQL support connection pooling
    engine_kwargs.update(
        {
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
    )

engine = create_async_engine(settings.database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


class DatabaseManager:
    """
    Manages database and Redis connections.

    This class provides a cleaner interface for connection management
    and makes testing easier by avoiding global state.
    """

    def __init__(self):
        self.redis_pool: ConnectionPool | None = None
        self.redis_client: Redis | None = None
        self._initialized = False

    async def initialize(self):
        """
        Initialize database connections.

        This function:
        - Sets up Redis connection pool
        - Verifies database connectivity
        - Creates tables if needed (dev only)
        """
        if self._initialized:
            logger.warning("Database manager already initialized")
            return

        logger.info("Initializing database connections")

        try:
            # Initialize Redis
            logger.info(
                "Connecting to Redis", extra={"redis_url": settings.redis_url.split("@")[-1]}
            )
            self.redis_pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=True,
            )
            self.redis_client = Redis(connection_pool=self.redis_pool)

            # Test Redis connection
            await self.redis_client.ping()
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

            self._initialized = True

        except Exception:
            logger.error("Failed to initialize database connections", exc_info=True)
            raise

    async def close(self):
        """
        Close database connections gracefully.

        This ensures all connections are properly closed during shutdown.
        """
        if not self._initialized:
            return

        logger.info("Closing database connections")

        try:
            if self.redis_client:
                await self.redis_client.aclose()
                logger.info("Redis connection closed")

            if self.redis_pool:
                await self.redis_pool.aclose()
                logger.info("Redis pool closed")

            await engine.dispose()
            logger.info("Database engine disposed")

            self._initialized = False

        except Exception:
            logger.error("Error closing database connections", exc_info=True)
            raise

    def get_redis(self) -> Redis:
        """Get Redis client instance."""
        if not self._initialized or self.redis_client is None:
            raise RuntimeError("Database manager not initialized")
        return self.redis_client


# Global instance for application use
db_manager = DatabaseManager()


async def init_db():
    """Initialize database connections (compatibility wrapper)."""
    await db_manager.initialize()


async def close_db():
    """Close database connections (compatibility wrapper)."""
    await db_manager.close()


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
    return db_manager.get_redis()


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
    except Exception:
        logger.error("Database health check failed", exc_info=True)
        return False


async def health_check_redis() -> bool:
    """
    Check Redis health.

    Returns:
        True if Redis is healthy, False otherwise
    """
    try:
        if db_manager._initialized and db_manager.redis_client:
            await db_manager.redis_client.ping()
            return True
        return False
    except Exception:
        logger.error("Redis health check failed", exc_info=True)
        return False
