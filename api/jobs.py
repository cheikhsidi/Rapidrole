"""
Job-related API endpoints.

This module provides endpoints for:
- Parsing and storing job postings
- Analyzing job requirements with AI
- Semantic job search
- Job details retrieval
"""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.job_analyzer import job_analyzer
from db.database import get_db
from db.models import JobPosting, UserProfile
from embeddings.matcher import semantic_matcher
from utils.error_handling import not_found_exception
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext

logger = get_logger(__name__)
router = APIRouter()


@router.post("/parse")
async def parse_job_posting(
    url: str,
    platform: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Parse and store a job posting from URL.

    Args:
        url: Job posting URL
        platform: Platform name (linkedin, indeed, etc.)
        db: Database session

    Returns:
        Parsed job information

    Note:
        In production, this would implement actual web scraping logic
        for each supported platform.
    """
    logger.info("Job parsing requested", extra={"url": url, "platform": platform})

    async with AsyncTraceContext("api.parse_job_posting", {"platform": platform}):
        # TODO: Implement actual scraping logic
        logger.warning("Job parsing not yet implemented, returning placeholder")

        return {
            "message": "Job parsing endpoint",
            "url": url,
            "platform": platform,
        }


@router.post("/analyze/{job_id}")
async def analyze_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a job posting using AI to extract structured information.

    Args:
        job_id: UUID of the job posting to analyze
        db: Database session

    Returns:
        Job analysis results including:
        - Required and preferred skills
        - Experience level
        - Key responsibilities
        - Confidence score

    Raises:
        HTTPException: 404 if job not found
    """
    start_time = time.time()

    logger.info("Job analysis requested", extra={"job_id": str(job_id)})

    async with AsyncTraceContext("api.analyze_job", {"job_id": str(job_id)}):
        # Fetch job from database
        result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            logger.warning("Job not found for analysis", extra={"job_id": str(job_id)})
            raise not_found_exception("Job", str(job_id))

        logger.debug(
            "Job retrieved for analysis",
            extra={
                "job_id": str(job_id),
                "title": job.title,
                "company": job.company,
            },
        )

        # Analyze with AI agent
        state = {
            "job_posting": {
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "requirements": job.requirements,
            },
            "errors": [],
        }

        analyzed_state = await job_analyzer.analyze(state)

        response = {
            "job_id": str(job_id),
            "analysis": {
                "required_skills": analyzed_state.get("required_skills", []),
                "preferred_skills": analyzed_state.get("preferred_skills", []),
                "experience_level": analyzed_state.get("experience_level"),
                "key_responsibilities": analyzed_state.get("key_responsibilities", []),
            },
            "confidence_score": analyzed_state.get("confidence_score", 0),
        }

        logger.info(
            "Job analysis completed",
            extra={
                "job_id": str(job_id),
                "required_skills_count": len(response["analysis"]["required_skills"]),
                "confidence_score": response["confidence_score"],
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return response


@router.get("/search")
async def search_jobs(
    user_id: UUID,
    limit: int = Query(20, le=100, description="Maximum number of results"),
    min_score: float = Query(0.6, ge=0.0, le=1.0, description="Minimum compatibility score"),
    db: AsyncSession = Depends(get_db),
):
    """
    Semantic search for jobs compatible with user profile.

    Uses multi-dimensional vector similarity to find jobs that match:
    - User skills
    - Work experience
    - Career goals

    Args:
        user_id: UUID of the user
        limit: Maximum number of results (default: 20, max: 100)
        min_score: Minimum compatibility score (0.0-1.0, default: 0.6)
        db: Database session

    Returns:
        List of compatible jobs with compatibility scores and breakdowns

    Raises:
        HTTPException: 404 if user profile not found
    """
    start_time = time.time()

    logger.info(
        "Job search requested",
        extra={
            "user_id": str(user_id),
            "limit": limit,
            "min_score": min_score,
        },
    )

    async with AsyncTraceContext("api.search_jobs", {"user_id": str(user_id)}):
        # Get user profile
        result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        if not profile:
            logger.warning("User profile not found for job search", extra={"user_id": str(user_id)})
            raise not_found_exception("User profile", str(user_id))

        logger.debug("User profile retrieved for job search", extra={"user_id": str(user_id)})

        # Find compatible jobs using semantic matching
        compatible_jobs = await semantic_matcher.find_compatible_jobs(
            db=db,
            user_profile=profile,
            limit=limit,
            min_score=min_score,
        )

        response = {
            "total": len(compatible_jobs),
            "jobs": [
                {
                    "id": str(job["job"].id),
                    "title": job["job"].title,
                    "company": job["job"].company,
                    "location": job["job"].location,
                    "compatibility_score": job["compatibility_score"],
                    "breakdown": job["breakdown"],
                }
                for job in compatible_jobs
            ],
        }

        logger.info(
            "Job search completed",
            extra={
                "user_id": str(user_id),
                "results_count": response["total"],
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return response


@router.get("/{job_id}")
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific job posting.

    Args:
        job_id: UUID of the job posting
        db: Database session

    Returns:
        Complete job posting details including:
        - Title, company, location
        - Description and requirements
        - Salary range (if available)
        - Original URL
        - Posted date

    Raises:
        HTTPException: 404 if job not found
    """
    logger.info("Job details requested", extra={"job_id": str(job_id)})

    async with AsyncTraceContext("api.get_job", {"job_id": str(job_id)}):
        result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            logger.warning("Job not found", extra={"job_id": str(job_id)})
            raise not_found_exception("Job", str(job_id))

        logger.debug(
            "Job details retrieved",
            extra={
                "job_id": str(job_id),
                "title": job.title,
                "company": job.company,
            },
        )

        return {
            "id": str(job.id),
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "requirements": job.requirements,
            "salary_range": {
                "min": job.salary_min,
                "max": job.salary_max,
            }
            if job.salary_min
            else None,
            "url": job.url,
            "posted_at": job.posted_at,
        }
