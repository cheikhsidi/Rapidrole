"""
Challenges and Gamification API endpoints.

This module provides endpoints for:
- Viewing active challenges
- Tracking challenge progress
- Completing challenges
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Challenge, User, UserChallengeProgress
from utils.error_handling import not_found_exception
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext

logger = get_logger(__name__)
router = APIRouter()


@router.get("/current")
async def get_current_challenges(
    challenge_type: str | None = Query(None, description="Filter by type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get currently active challenges.

    Args:
        challenge_type: Optional filter by challenge type
        db: Database session

    Returns:
        List of active challenges
    """
    logger.info("Current challenges requested", extra={"challenge_type": challenge_type})

    async with AsyncTraceContext("api.get_current_challenges"):
        now = datetime.utcnow()

        query = select(Challenge).where(
            and_(Challenge.is_active == 1, Challenge.start_date <= now, Challenge.end_date >= now)
        )

        if challenge_type:
            query = query.where(Challenge.challenge_type == challenge_type)

        result = await db.execute(query)
        challenges = result.scalars().all()

        response = {
            "total": len(challenges),
            "challenges": [
                {
                    "id": str(challenge.id),
                    "title": challenge.title,
                    "description": challenge.description,
                    "type": challenge.challenge_type,
                    "difficulty": challenge.difficulty,
                    "reward_points": challenge.reward_points,
                    "start_date": challenge.start_date,
                    "end_date": challenge.end_date,
                    "requirements": challenge.requirements,
                }
                for challenge in challenges
            ],
        }

        logger.info("Current challenges retrieved", extra={"challenges_count": response["total"]})

        return response


@router.get("/{user_id}/progress")
async def get_user_challenge_progress(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a user's progress on all challenges.

    Args:
        user_id: UUID of the user
        db: Database session

    Returns:
        User's challenge progress
    """
    logger.info("User challenge progress requested", extra={"user_id": str(user_id)})

    async with AsyncTraceContext("api.get_user_challenge_progress"):
        result = await db.execute(
            select(UserChallengeProgress).where(UserChallengeProgress.user_id == user_id)
        )
        progress_records = result.scalars().all()

        response = {
            "user_id": str(user_id),
            "total_challenges": len(progress_records),
            "completed": sum(1 for p in progress_records if p.completed),
            "in_progress": sum(1 for p in progress_records if not p.completed),
            "challenges": [
                {
                    "challenge_id": str(p.challenge_id),
                    "progress_data": p.progress_data,
                    "completed": bool(p.completed),
                    "completed_at": p.completed_at,
                    "started_at": p.started_at,
                }
                for p in progress_records
            ],
        }

        logger.info(
            "User challenge progress retrieved",
            extra={
                "user_id": str(user_id),
                "completed": response["completed"],
                "in_progress": response["in_progress"],
            },
        )

        return response


@router.post("/{challenge_id}/complete")
async def complete_challenge(
    challenge_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a challenge as completed for a user.

    Args:
        challenge_id: UUID of the challenge
        user_id: UUID of the user
        db: Database session

    Returns:
        Completion confirmation with rewards
    """
    logger.info(
        "Challenge completion requested",
        extra={"challenge_id": str(challenge_id), "user_id": str(user_id)},
    )

    async with AsyncTraceContext("api.complete_challenge"):
        # Get challenge
        challenge_result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
        challenge = challenge_result.scalar_one_or_none()

        if not challenge:
            raise not_found_exception("Challenge", str(challenge_id))

        # Get or create progress record
        progress_result = await db.execute(
            select(UserChallengeProgress).where(
                and_(
                    UserChallengeProgress.user_id == user_id,
                    UserChallengeProgress.challenge_id == challenge_id,
                )
            )
        )
        progress = progress_result.scalar_one_or_none()

        if not progress:
            progress = UserChallengeProgress(
                user_id=user_id,
                challenge_id=challenge_id,
                progress_data={},
            )
            db.add(progress)

        if progress.completed:
            return {
                "message": "Challenge already completed",
                "challenge_id": str(challenge_id),
                "completed_at": progress.completed_at,
            }

        # Mark as completed
        progress.completed = 1
        progress.completed_at = datetime.utcnow()

        # Award points to user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if user:
            user.total_points += challenge.reward_points

        await db.commit()

        logger.info(
            "Challenge completed",
            extra={
                "challenge_id": str(challenge_id),
                "user_id": str(user_id),
                "points_awarded": challenge.reward_points,
            },
        )

        return {
            "message": "Challenge completed",
            "challenge_id": str(challenge_id),
            "points_awarded": challenge.reward_points,
            "completed_at": progress.completed_at,
        }
