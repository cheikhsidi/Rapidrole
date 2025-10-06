"""
Community API endpoints.

This module provides endpoints for:
- Activity feed
- Leaderboards
- User badges and achievements
- Community engagement
"""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import ActivityFeed, Application, User, UserBadge
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext

logger = get_logger(__name__)
router = APIRouter()


@router.get("/feed")
async def get_activity_feed(
    limit: int = Query(50, le=100, description="Number of activities to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    activity_type: str | None = Query(None, description="Filter by activity type"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get public activity feed showing recent community activity.

    Returns anonymized activities like:
    - Recent applications
    - Badges earned
    - Milestones reached

    Args:
        limit: Maximum number of activities (default: 50, max: 100)
        offset: Pagination offset
        activity_type: Optional filter by type
        db: Database session

    Returns:
        List of recent public activities
    """
    start_time = time.time()

    logger.info(
        "Activity feed requested",
        extra={"limit": limit, "offset": offset, "activity_type": activity_type},
    )

    async with AsyncTraceContext("api.get_activity_feed"):
        query = select(ActivityFeed).where(ActivityFeed.is_public == 1)

        if activity_type:
            query = query.where(ActivityFeed.activity_type == activity_type)

        query = query.order_by(desc(ActivityFeed.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        activities = result.scalars().all()

        response = {
            "total": len(activities),
            "activities": [
                {
                    "id": str(activity.id),
                    "type": activity.activity_type,
                    "data": activity.activity_data,
                    "created_at": activity.created_at,
                }
                for activity in activities
            ],
        }

        logger.info(
            "Activity feed retrieved",
            extra={
                "activities_count": response["total"],
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return response


@router.get("/leaderboard")
async def get_leaderboard(
    metric: str = Query("points", description="Metric to rank by: points, streak, applications"),
    limit: int = Query(10, le=50, description="Number of users to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get community leaderboard rankings.

    Args:
        metric: Ranking metric (points, streak, applications)
        limit: Number of top users to return
        db: Database session

    Returns:
        Leaderboard with top users
    """
    start_time = time.time()

    logger.info("Leaderboard requested", extra={"metric": metric, "limit": limit})

    async with AsyncTraceContext("api.get_leaderboard", {"metric": metric}):
        # Only show users who opted in
        query = select(User).where(User.show_in_leaderboard == 1)

        # Order by requested metric
        if metric == "points":
            query = query.order_by(desc(User.total_points))
        elif metric == "streak":
            query = query.order_by(desc(User.current_streak))
        elif metric == "applications":
            # Count applications per user
            query = (
                select(User, func.count(Application.id).label("app_count"))
                .join(Application, User.id == Application.user_id)
                .where(User.show_in_leaderboard == 1)
                .group_by(User.id)
                .order_by(desc("app_count"))
            )

        query = query.limit(limit)
        result = await db.execute(query)

        if metric == "applications":
            rows = result.all()
            leaderboard = [
                {
                    "rank": idx + 1,
                    "user_id": str(user.id) if user.profile_public else "anonymous",
                    "name": user.full_name if user.profile_public else "Anonymous User",
                    "value": app_count,
                    "metric": metric,
                }
                for idx, (user, app_count) in enumerate(rows)
            ]
        else:
            users = result.scalars().all()
            leaderboard = [
                {
                    "rank": idx + 1,
                    "user_id": str(user.id) if user.profile_public else "anonymous",
                    "name": user.full_name if user.profile_public else "Anonymous User",
                    "value": getattr(
                        user, "total_points" if metric == "points" else "current_streak"
                    ),
                    "metric": metric,
                }
                for idx, user in enumerate(users)
            ]

        logger.info(
            "Leaderboard retrieved",
            extra={
                "metric": metric,
                "users_count": len(leaderboard),
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return {"leaderboard": leaderboard, "metric": metric}


@router.get("/badges/{user_id}")
async def get_user_badges(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all badges earned by a user.

    Args:
        user_id: UUID of the user
        db: Database session

    Returns:
        List of user's badges
    """
    logger.info("User badges requested", extra={"user_id": str(user_id)})

    async with AsyncTraceContext("api.get_user_badges", {"user_id": str(user_id)}):
        result = await db.execute(
            select(UserBadge)
            .where(UserBadge.user_id == user_id)
            .order_by(desc(UserBadge.earned_at))
        )
        badges = result.scalars().all()

        response = {
            "user_id": str(user_id),
            "total_badges": len(badges),
            "badges": [
                {
                    "id": str(badge.id),
                    "type": badge.badge_type,
                    "name": badge.badge_name,
                    "description": badge.badge_description,
                    "earned_at": badge.earned_at,
                }
                for badge in badges
            ],
        }

        logger.info(
            "User badges retrieved",
            extra={"user_id": str(user_id), "badges_count": response["total_badges"]},
        )

        return response


@router.get("/stats")
async def get_community_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall community statistics.

    Returns:
        Community-wide statistics
    """
    logger.info("Community stats requested")

    async with AsyncTraceContext("api.get_community_stats"):
        # Count total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar()

        # Count total applications
        total_apps_result = await db.execute(select(func.count(Application.id)))
        total_applications = total_apps_result.scalar()

        # Count pro users
        pro_users_result = await db.execute(
            select(func.count(User.id)).where(User.account_tier == "pro")
        )
        pro_users = pro_users_result.scalar()

        stats = {
            "total_users": total_users,
            "total_applications": total_applications,
            "pro_users": pro_users,
            "free_users": total_users - pro_users,
        }

        logger.info("Community stats retrieved", extra=stats)

        return stats
