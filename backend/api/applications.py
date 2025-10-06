"""
Application management API endpoints.

This module provides endpoints for:
- Creating job applications
- Retrieving application details
- Updating application status
- Listing user applications
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
import time

from db.database import get_db
from db.models import Application, JobPosting, UserProfile
from agents.workflow import application_workflow
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext
from utils.error_handling import not_found_exception

logger = get_logger(__name__)
router = APIRouter()


class CreateApplicationRequest(BaseModel):
    user_id: UUID
    job_id: UUID


class UpdateApplicationStatusRequest(BaseModel):
    status: str


@router.post("/")
async def create_application(
    request: CreateApplicationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new job application.
    
    Args:
        request: Application creation request with user_id and job_id
        db: Database session
        
    Returns:
        Created application details including:
        - Application ID
        - User ID
        - Job ID
        - Status (draft)
        - Creation timestamp
        
    Raises:
        HTTPException: 404 if job or user profile not found
    """
    start_time = time.time()
    
    logger.info(
        "Application creation requested",
        extra={
            "user_id": str(request.user_id),
            "job_id": str(request.job_id),
        }
    )
    
    async with AsyncTraceContext(
        "api.create_application",
        {"user_id": str(request.user_id), "job_id": str(request.job_id)}
    ):
        # Verify job exists
        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == request.job_id)
        )
        job = job_result.scalar_one_or_none()
        if not job:
            logger.warning(
                "Job not found for application creation",
                extra={"job_id": str(request.job_id)}
            )
            raise not_found_exception("Job", str(request.job_id))
        
        # Verify user profile exists
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == request.user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            logger.warning(
                "User profile not found for application creation",
                extra={"user_id": str(request.user_id)}
            )
            raise not_found_exception("User profile", str(request.user_id))
        
        logger.debug(
            "Creating application",
            extra={
                "user_id": str(request.user_id),
                "job_id": str(request.job_id),
                "job_title": job.title,
            }
        )
        
        # Create application
        application = Application(
            user_id=request.user_id,
            job_id=request.job_id,
            status="draft",
        )
        db.add(application)
        await db.commit()
        await db.refresh(application)
        
        response = {
            "id": str(application.id),
            "user_id": str(application.user_id),
            "job_id": str(application.job_id),
            "status": application.status,
            "created_at": application.created_at,
        }
        
        logger.info(
            "Application created successfully",
            extra={
                "application_id": str(application.id),
                "user_id": str(request.user_id),
                "job_id": str(request.job_id),
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            }
        )
        
        return response


@router.get("/{application_id}")
async def get_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific application.
    
    Args:
        application_id: UUID of the application
        db: Database session
        
    Returns:
        Complete application details including:
        - Application metadata (IDs, status, timestamps)
        - Compatibility scores
        - Generated documents (resume, cover letter)
        - AI recommendations
        
    Raises:
        HTTPException: 404 if application not found
    """
    logger.info(
        "Application details requested",
        extra={"application_id": str(application_id)}
    )
    
    async with AsyncTraceContext("api.get_application", {"application_id": str(application_id)}):
        result = await db.execute(
            select(Application).where(Application.id == application_id)
        )
        app = result.scalar_one_or_none()
        
        if not app:
            logger.warning(
                "Application not found",
                extra={"application_id": str(application_id)}
            )
            raise not_found_exception("Application", str(application_id))
        
        logger.debug(
            "Application details retrieved",
            extra={
                "application_id": str(application_id),
                "status": app.status,
                "user_id": str(app.user_id),
            }
        )
        
        return {
            "id": str(app.id),
            "user_id": str(app.user_id),
            "job_id": str(app.job_id),
            "status": app.status,
            "compatibility_score": app.compatibility_score,
            "skill_match_score": app.skill_match_score,
            "experience_match_score": app.experience_match_score,
            "tailored_resume": app.tailored_resume,
            "cover_letter": app.cover_letter,
            "ai_recommendations": app.ai_recommendations,
            "submitted_at": app.submitted_at,
            "created_at": app.created_at,
        }


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: UUID,
    request: UpdateApplicationStatusRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update the status of an application.
    
    Args:
        application_id: UUID of the application
        request: Status update request
        db: Database session
        
    Returns:
        Updated application ID and status
        
    Raises:
        HTTPException: 404 if application not found
        
    Note:
        When status is set to "submitted", the submitted_at timestamp
        is automatically set to the current time.
    """
    logger.info(
        "Application status update requested",
        extra={
            "application_id": str(application_id),
            "new_status": request.status,
        }
    )
    
    async with AsyncTraceContext(
        "api.update_application_status",
        {"application_id": str(application_id), "status": request.status}
    ):
        result = await db.execute(
            select(Application).where(Application.id == application_id)
        )
        app = result.scalar_one_or_none()
        
        if not app:
            logger.warning(
                "Application not found for status update",
                extra={"application_id": str(application_id)}
            )
            raise not_found_exception("Application", str(application_id))
        
        old_status = app.status
        app.status = request.status
        
        if request.status == "submitted":
            app.submitted_at = datetime.utcnow()
            logger.debug(
                "Application marked as submitted",
                extra={"application_id": str(application_id)}
            )
        
        await db.commit()
        
        logger.info(
            "Application status updated",
            extra={
                "application_id": str(application_id),
                "old_status": old_status,
                "new_status": app.status,
            }
        )
        
        return {"id": str(app.id), "status": app.status}


@router.get("/user/{user_id}")
async def get_user_applications(
    user_id: UUID,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all applications for a specific user.
    
    Args:
        user_id: UUID of the user
        status: Optional status filter (draft, submitted, interview, rejected, accepted)
        db: Database session
        
    Returns:
        List of applications with summary information:
        - Application ID
        - Job ID
        - Status
        - Compatibility score
        - Creation timestamp
        
    Note:
        Applications are returned in reverse chronological order (newest first).
    """
    logger.info(
        "User applications requested",
        extra={
            "user_id": str(user_id),
            "status_filter": status,
        }
    )
    
    async with AsyncTraceContext(
        "api.get_user_applications",
        {"user_id": str(user_id), "status": status}
    ):
        query = select(Application).where(Application.user_id == user_id)
        
        if status:
            query = query.where(Application.status == status)
            logger.debug(
                "Filtering applications by status",
                extra={"status": status}
            )
        
        result = await db.execute(query.order_by(Application.created_at.desc()))
        applications = result.scalars().all()
        
        response = {
            "total": len(applications),
            "applications": [
                {
                    "id": str(app.id),
                    "job_id": str(app.job_id),
                    "status": app.status,
                    "compatibility_score": app.compatibility_score,
                    "created_at": app.created_at,
                }
                for app in applications
            ],
        }
        
        logger.info(
            "User applications retrieved",
            extra={
                "user_id": str(user_id),
                "total_applications": response["total"],
                "status_filter": status,
            }
        )
        
        return response
