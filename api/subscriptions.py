"""
Subscription Management API endpoints.

This module provides endpoints for:
- Pro subscription management
- Subscription status checking
- Trial management
- Stripe webhook handling
"""

import time
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Subscription, User
from utils.error_handling import not_found_exception
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext

logger = get_logger(__name__)
router = APIRouter()


class SubscribeRequest(BaseModel):
    plan_type: str = "pro"
    payment_method_id: str | None = None


@router.post("/subscribe")
async def subscribe_to_pro(
    user_id: UUID,
    request: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Subscribe a user to Pro tier.

    Args:
        user_id: UUID of the user
        request: Subscription request data
        db: Database session

    Returns:
        Subscription details

    Note:
        In production, this would integrate with Stripe for payment processing.
    """
    start_time = time.time()

    logger.info(
        "Pro subscription requested",
        extra={"user_id": str(user_id), "plan_type": request.plan_type},
    )

    async with AsyncTraceContext("api.subscribe_to_pro", {"user_id": str(user_id)}):
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise not_found_exception("User", str(user_id))

        # Check if already subscribed
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        existing_sub = sub_result.scalar_one_or_none()

        if existing_sub and existing_sub.status == "active":
            logger.warning("User already has active subscription", extra={"user_id": str(user_id)})
            return {
                "message": "User already has active subscription",
                "subscription_id": str(existing_sub.id),
                "status": existing_sub.status,
            }

        # Create subscription
        # In production: integrate with Stripe here
        now = datetime.utcnow()
        subscription = Subscription(
            user_id=user_id,
            plan_type=request.plan_type,
            status="active",
            started_at=now,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            # stripe_customer_id would be set here
            # stripe_subscription_id would be set here
        )

        db.add(subscription)

        # Update user tier
        user.account_tier = "pro"
        user.pro_expires_at = subscription.current_period_end

        await db.commit()
        await db.refresh(subscription)

        logger.info(
            "Pro subscription created",
            extra={
                "user_id": str(user_id),
                "subscription_id": str(subscription.id),
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return {
            "subscription_id": str(subscription.id),
            "user_id": str(user_id),
            "plan_type": subscription.plan_type,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
        }


@router.get("/status/{user_id}")
async def get_subscription_status(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get subscription status for a user.

    Args:
        user_id: UUID of the user
        db: Database session

    Returns:
        Subscription status and details
    """
    logger.info("Subscription status requested", extra={"user_id": str(user_id)})

    async with AsyncTraceContext("api.get_subscription_status"):
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise not_found_exception("User", str(user_id))

        # Get subscription
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        subscription = sub_result.scalar_one_or_none()

        if not subscription:
            return {
                "user_id": str(user_id),
                "account_tier": user.account_tier,
                "has_subscription": False,
                "is_pro": user.account_tier == "pro",
            }

        # Check if subscription is still valid
        is_active = subscription.status == "active" and (
            subscription.current_period_end is None
            or subscription.current_period_end > datetime.utcnow()
        )

        response = {
            "user_id": str(user_id),
            "account_tier": user.account_tier,
            "has_subscription": True,
            "is_pro": is_active,
            "subscription": {
                "id": str(subscription.id),
                "plan_type": subscription.plan_type,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start,
                "current_period_end": subscription.current_period_end,
                "trial_end": subscription.trial_end,
            },
        }

        logger.info(
            "Subscription status retrieved", extra={"user_id": str(user_id), "is_pro": is_active}
        )

        return response


@router.post("/cancel/{user_id}")
async def cancel_subscription(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a user's subscription.

    Args:
        user_id: UUID of the user
        db: Database session

    Returns:
        Cancellation confirmation

    Note:
        Subscription remains active until end of current period.
    """
    logger.info("Subscription cancellation requested", extra={"user_id": str(user_id)})

    async with AsyncTraceContext("api.cancel_subscription"):
        # Get subscription
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        subscription = sub_result.scalar_one_or_none()

        if not subscription:
            raise not_found_exception("Subscription", str(user_id))

        # Cancel subscription
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()

        # In production: cancel Stripe subscription here

        await db.commit()

        logger.info(
            "Subscription cancelled",
            extra={
                "user_id": str(user_id),
                "subscription_id": str(subscription.id),
            },
        )

        return {
            "message": "Subscription cancelled",
            "subscription_id": str(subscription.id),
            "status": subscription.status,
            "access_until": subscription.current_period_end,
        }


@router.post("/trial/{user_id}")
async def start_trial(
    user_id: UUID,
    trial_days: int = 14,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a free trial for a user.

    Args:
        user_id: UUID of the user
        trial_days: Number of trial days (default: 14)
        db: Database session

    Returns:
        Trial details
    """
    logger.info("Trial start requested", extra={"user_id": str(user_id), "trial_days": trial_days})

    async with AsyncTraceContext("api.start_trial"):
        # Get user
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise not_found_exception("User", str(user_id))

        # Check if already has subscription
        sub_result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        existing_sub = sub_result.scalar_one_or_none()

        if existing_sub:
            raise HTTPException(status_code=400, detail="User already has a subscription or trial")

        # Create trial subscription
        now = datetime.utcnow()
        trial_end = now + timedelta(days=trial_days)

        subscription = Subscription(
            user_id=user_id,
            plan_type="pro",
            status="active",
            started_at=now,
            trial_start=now,
            trial_end=trial_end,
            current_period_start=now,
            current_period_end=trial_end,
        )

        db.add(subscription)

        # Update user tier
        user.account_tier = "pro"
        user.pro_expires_at = trial_end

        await db.commit()
        await db.refresh(subscription)

        logger.info(
            "Trial started",
            extra={
                "user_id": str(user_id),
                "trial_days": trial_days,
                "trial_end": trial_end,
            },
        )

        return {
            "subscription_id": str(subscription.id),
            "user_id": str(user_id),
            "trial_days": trial_days,
            "trial_end": trial_end,
            "status": "trial_active",
        }
