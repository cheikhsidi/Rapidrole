"""
AI intelligence and insights API endpoints.

This module provides endpoints for:
- Job-candidate compatibility analysis
- Personalized job recommendations
- Application insights and suggestions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import time

from db.database import get_db
from db.models import Application, JobPosting, UserProfile
from embeddings.matcher import semantic_matcher
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext
from utils.error_handling import not_found_exception

logger = get_logger(__name__)
router = APIRouter()


@router.get("/compatibility/{user_id}/{job_id}")
async def get_compatibility(
    user_id: UUID,
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate detailed compatibility between a user and a job.
    
    Uses multi-dimensional semantic matching to analyze:
    - Skills alignment
    - Experience match
    - Career goals alignment
    
    Args:
        user_id: UUID of the user
        job_id: UUID of the job
        db: Database session
        
    Returns:
        Compatibility analysis with:
        - Overall compatibility score (0.0-1.0)
        - Skills match score
        - Experience match score
        - Goals alignment score
        
    Raises:
        HTTPException: 404 if user profile or job not found
    """
    start_time = time.time()
    
    logger.info(
        "Compatibility analysis requested",
        extra={
            "user_id": str(user_id),
            "job_id": str(job_id),
        }
    )
    
    async with AsyncTraceContext(
        "api.get_compatibility",
        {"user_id": str(user_id), "job_id": str(job_id)}
    ):
        # Get user profile
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            logger.warning(
                "User profile not found for compatibility analysis",
                extra={"user_id": str(user_id)}
            )
            raise not_found_exception("User profile", str(user_id))
        
        # Get job
        job_result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        job = job_result.scalar_one_or_none()
        if not job:
            logger.warning(
                "Job not found for compatibility analysis",
                extra={"job_id": str(job_id)}
            )
            raise not_found_exception("Job", str(job_id))
        
        logger.debug(
            "Calculating compatibility",
            extra={
                "user_id": str(user_id),
                "job_id": str(job_id),
                "job_title": job.title,
            }
        )
        
        # Calculate compatibility using semantic matching
        compatibility = await semantic_matcher.calculate_compatibility(job, profile)
        
        response = {
            "user_id": str(user_id),
            "job_id": str(job_id),
            "compatibility": compatibility,
        }
        
        logger.info(
            "Compatibility analysis completed",
            extra={
                "user_id": str(user_id),
                "job_id": str(job_id),
                "overall_score": compatibility["overall_score"],
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            }
        )
        
        return response


@router.get("/recommendations/{user_id}")
async def get_recommendations(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered job recommendations for a user.
    
    Returns top 10 jobs with compatibility score >= 0.7, ranked by
    overall compatibility.
    
    Args:
        user_id: UUID of the user
        db: Database session
        
    Returns:
        List of recommended jobs with:
        - Job details (ID, title, company)
        - Compatibility score
        - Explanation of why the job is recommended
        
    Raises:
        HTTPException: 404 if user profile not found
    """
    start_time = time.time()
    
    logger.info(
        "Job recommendations requested",
        extra={"user_id": str(user_id)}
    )
    
    async with AsyncTraceContext("api.get_recommendations", {"user_id": str(user_id)}):
        # Get user profile
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            logger.warning(
                "User profile not found for recommendations",
                extra={"user_id": str(user_id)}
            )
            raise not_found_exception("User profile", str(user_id))
        
        logger.debug(
            "Finding compatible jobs for recommendations",
            extra={"user_id": str(user_id)}
        )
        
        # Find compatible jobs with high threshold
        compatible_jobs = await semantic_matcher.find_compatible_jobs(
            db=db,
            user_profile=profile,
            limit=10,
            min_score=0.7,
        )
        
        response = {
            "user_id": str(user_id),
            "recommendations": [
                {
                    "job_id": str(job["job"].id),
                    "title": job["job"].title,
                    "company": job["job"].company,
                    "score": job["compatibility_score"],
                    "reason": f"Strong match on skills ({job['breakdown']['skills_match']:.2f}) and experience ({job['breakdown']['experience_match']:.2f})",
                }
                for job in compatible_jobs
            ],
        }
        
        logger.info(
            "Job recommendations generated",
            extra={
                "user_id": str(user_id),
                "recommendations_count": len(response["recommendations"]),
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            }
        )
        
        return response


@router.get("/insights/{application_id}")
async def get_application_insights(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-generated insights for a specific application.
    
    Args:
        application_id: UUID of the application
        db: Database session
        
    Returns:
        Application insights including:
        - Overall compatibility score
        - Skills match score
        - Experience match score
        - AI-generated recommendations
        
    Raises:
        HTTPException: 404 if application not found
    """
    logger.info(
        "Application insights requested",
        extra={"application_id": str(application_id)}
    )
    
    async with AsyncTraceContext("api.get_application_insights", {"application_id": str(application_id)}):
        result = await db.execute(
            select(Application).where(Application.id == application_id)
        )
        app = result.scalar_one_or_none()
        
        if not app:
            logger.warning(
                "Application not found for insights",
                extra={"application_id": str(application_id)}
            )
            raise not_found_exception("Application", str(application_id))
        
        response = {
            "application_id": str(application_id),
            "insights": {
                "compatibility_score": app.compatibility_score,
                "skill_match": app.skill_match_score,
                "experience_match": app.experience_match_score,
                "recommendations": app.ai_recommendations or [],
            },
        }
        
        logger.info(
            "Application insights retrieved",
            extra={
                "application_id": str(application_id),
                "compatibility_score": app.compatibility_score,
            }
        )
        
        return response
