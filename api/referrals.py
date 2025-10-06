"""
Referral System API endpoints.

This module provides endpoints for:
- Creating referral invites
- Tracking referral status
- Claiming referral rewards
"""

import time
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Referral, User
from utils.error_handling import not_found_exception
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext

logger = get_logger(__name__)
router = APIRouter()


class CreateReferralRequest(BaseModel):
    referred_email: EmailStr


@router.post("/invite")
async def create_referral(
    referrer_id: UUID,
    request: CreateReferralRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a referral invite.

    Args:
        referrer_id: UUID of the user making the referral
        request: Referral request with email
        db: Database session

    Returns:
        Referral details
    """
    start_time = time.time()

    logger.info(
        "Referral invite requested",
        extra={
            "referrer_id": str(referrer_id),
            "referred_email": request.referred_email,
        },
    )

    async with AsyncTraceContext("api.create_referral"):
        # Verify referrer exists
        referrer_result = await db.execute(select(User).where(User.id == referrer_id))
        referrer = referrer_result.scalar_one_or_none()

        if not referrer:
            raise not_found_exception("User", str(referrer_id))

        # Check if email already referred
        existing_result = await db.execute(
            select(Referral).where(
                Referral.referrer_id == referrer_id,
                Referral.referred_email == request.referred_email,
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            logger.warning(
                "Email already referred",
                extra={"referrer_id": str(referrer_id), "email": request.referred_email},
            )
            return {
                "message": "Email already referred",
                "referral_id": str(existing.id),
                "status": existing.status,
            }

        # Create referral
        referral = Referral(
            referrer_id=referrer_id,
            referred_email=request.referred_email,
            status="pending",
        )

        db.add(referral)
        await db.commit()
        await db.refresh(referral)

        logger.info(
            "Referral created",
            extra={
                "referral_id": str(referral.id),
                "referrer_id": str(referrer_id),
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return {
            "referral_id": str(referral.id),
            "referrer_id": str(referrer_id),
            "referred_email": referral.referred_email,
            "status": referral.status,
            "referral_link": f"https://rapidrole.com/signup?ref={referrer.referral_code}",
        }


@router.get("/{user_id}")
async def get_user_referrals(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all referrals made by a user.

    Args:
        user_id: UUID of the user
        db: Database session

    Returns:
        List of user's referrals
    """
    logger.info("User referrals requested", extra={"user_id": str(user_id)})

    async with AsyncTraceContext("api.get_user_referrals"):
        result = await db.execute(select(Referral).where(Referral.referrer_id == user_id))
        referrals = result.scalars().all()

        response = {
            "user_id": str(user_id),
            "total_referrals": len(referrals),
            "referrals": [
                {
                    "id": str(ref.id),
                    "referred_email": ref.referred_email,
                    "status": ref.status,
                    "reward_claimed": bool(ref.reward_claimed),
                    "created_at": ref.created_at,
                    "accepted_at": ref.accepted_at,
                }
                for ref in referrals
            ],
        }

        logger.info(
            "User referrals retrieved",
            extra={"user_id": str(user_id), "total": response["total_referrals"]},
        )

        return response


@router.post("/{referral_id}/claim")
async def claim_referral_reward(
    referral_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Claim reward for a successful referral.

    Args:
        referral_id: UUID of the referral
        db: Database session

    Returns:
        Reward claim confirmation
    """
    logger.info("Referral reward claim requested", extra={"referral_id": str(referral_id)})

    async with AsyncTraceContext("api.claim_referral_reward"):
        result = await db.execute(select(Referral).where(Referral.id == referral_id))
        referral = result.scalar_one_or_none()

        if not referral:
            raise not_found_exception("Referral", str(referral_id))

        if referral.reward_claimed:
            return {
                "message": "Reward already claimed",
                "referral_id": str(referral_id),
            }

        if referral.status != "accepted":
            return {
                "message": "Referral not yet accepted",
                "referral_id": str(referral_id),
                "status": referral.status,
            }

        # Mark reward as claimed
        referral.reward_claimed = 1

        # Award points to referrer
        referrer_result = await db.execute(select(User).where(User.id == referral.referrer_id))
        referrer = referrer_result.scalar_one_or_none()

        if referrer:
            referrer.total_points += 100  # Reward points

        await db.commit()

        logger.info(
            "Referral reward claimed",
            extra={
                "referral_id": str(referral_id),
                "referrer_id": str(referral.referrer_id),
            },
        )

        return {
            "message": "Reward claimed successfully",
            "referral_id": str(referral_id),
            "points_awarded": 100,
        }
