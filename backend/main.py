from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from prometheus_client import make_asgi_app
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from config.settings import settings
from db.database import init_db, close_db
from api import jobs, applications, users, intelligence
from utils.logging import get_logger, setup_logging
from utils.middleware import (
    RequestTracingMiddleware,
    PerformanceMonitoringMiddleware,
    ErrorHandlingMiddleware,
)

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Initialize Sentry for error tracking
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        send_default_pii=False,  # Don't send PII to Sentry
    )
    logger.info("Sentry initialized", extra={"environment": settings.sentry_environment})


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("Application starting up", extra={"environment": settings.app_env})
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", exc_info=True)
        raise
    
    yield
    
    logger.info("Application shutting down")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error during shutdown", exc_info=True)


app = FastAPI(
    title="Job Copilot API",
    description="AI-Powered Universal Job Application Copilot",
    version="0.1.0",
    lifespan=lifespan,
)

# Add custom middleware (order matters!)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=settings.slow_request_threshold)
app.add_middleware(RequestTracingMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with proper logging"""
    logger.warning(
        "Request validation failed",
        extra={
            "path": request.url.path,
            "errors": exc.errors(),
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "error": str(exc),
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Import new routers
from api import community, templates, subscriptions, challenges, referrals

# Routers - Core Features
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["intelligence"])

# Routers - Community & Gamification
app.include_router(community.router, prefix="/api/v1/community", tags=["community"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(challenges.router, prefix="/api/v1/challenges", tags=["challenges"])
app.include_router(referrals.router, prefix="/api/v1/referrals", tags=["referrals"])

# Routers - Subscription & Monetization
app.include_router(subscriptions.router, prefix="/api/v1/subscriptions", tags=["subscriptions"])

# Metrics endpoint
if settings.enable_metrics:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "version": "0.1.0",
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes/load balancers"""
    from db.database import engine
    from redis.asyncio import Redis
    
    try:
        # Check database
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        
        # Check Redis
        from db.database import redis_client
        if redis_client:
            await redis_client.ping()
        
        logger.debug("Readiness check passed")
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e)},
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Job Copilot API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "environment": settings.app_env,
    }
