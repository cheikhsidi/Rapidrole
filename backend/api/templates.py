"""
Agent Template Marketplace API endpoints.

This module provides endpoints for:
- Creating and sharing agent templates
- Browsing and searching templates
- Remixing templates
- Template usage tracking
"""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import AgentTemplate, User
from utils.error_handling import not_found_exception
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext

logger = get_logger(__name__)
router = APIRouter()


class CreateTemplateRequest(BaseModel):
    name: str
    description: str
    category: str
    template_data: dict
    is_public: bool = True


class UpdateTemplateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    template_data: dict | None = None
    is_public: bool | None = None


@router.post("/")
async def create_template(
    request: CreateTemplateRequest,
    creator_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Create and publish a new agent template.

    Args:
        request: Template creation data
        creator_id: UUID of the template creator
        db: Database session

    Returns:
        Created template details
    """
    start_time = time.time()

    logger.info(
        "Template creation requested",
        extra={
            "creator_id": str(creator_id),
            "name": request.name,
            "category": request.category,
        },
    )

    async with AsyncTraceContext("api.create_template"):
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == creator_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise not_found_exception("User", str(creator_id))

        # Create template
        template = AgentTemplate(
            creator_id=creator_id,
            name=request.name,
            description=request.description,
            category=request.category,
            template_data=request.template_data,
            is_public=1 if request.is_public else 0,
        )

        db.add(template)
        await db.commit()
        await db.refresh(template)

        response = {
            "id": str(template.id),
            "creator_id": str(template.creator_id),
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "is_public": bool(template.is_public),
            "created_at": template.created_at,
        }

        logger.info(
            "Template created successfully",
            extra={
                "template_id": str(template.id),
                "creator_id": str(creator_id),
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return response


@router.get("/")
async def browse_templates(
    category: str | None = Query(None, description="Filter by category"),
    featured: bool = Query(False, description="Show only featured templates"),
    sort_by: str = Query("popular", description="Sort by: popular, recent, top_rated"),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Browse and search agent templates.

    Args:
        category: Optional category filter
        featured: Show only featured templates
        sort_by: Sorting method (popular, recent, top_rated)
        limit: Maximum results
        offset: Pagination offset
        db: Database session

    Returns:
        List of templates matching criteria
    """
    start_time = time.time()

    logger.info(
        "Template browse requested",
        extra={
            "category": category,
            "featured": featured,
            "sort_by": sort_by,
        },
    )

    async with AsyncTraceContext("api.browse_templates"):
        query = select(AgentTemplate).where(AgentTemplate.is_public == 1)

        if category:
            query = query.where(AgentTemplate.category == category)

        if featured:
            query = query.where(AgentTemplate.is_featured == 1)

        # Apply sorting
        if sort_by == "popular":
            query = query.order_by(desc(AgentTemplate.usage_count))
        elif sort_by == "recent":
            query = query.order_by(desc(AgentTemplate.created_at))
        elif sort_by == "top_rated":
            query = query.order_by(desc(AgentTemplate.upvotes - AgentTemplate.downvotes))

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        templates = result.scalars().all()

        response = {
            "total": len(templates),
            "templates": [
                {
                    "id": str(template.id),
                    "creator_id": str(template.creator_id),
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "usage_count": template.usage_count,
                    "upvotes": template.upvotes,
                    "downvotes": template.downvotes,
                    "is_featured": bool(template.is_featured),
                    "created_at": template.created_at,
                }
                for template in templates
            ],
        }

        logger.info(
            "Templates retrieved",
            extra={
                "templates_count": response["total"],
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return response


@router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific template.

    Args:
        template_id: UUID of the template
        db: Database session

    Returns:
        Complete template details including template_data
    """
    logger.info("Template details requested", extra={"template_id": str(template_id)})

    async with AsyncTraceContext("api.get_template"):
        result = await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id))
        template = result.scalar_one_or_none()

        if not template:
            raise not_found_exception("Template", str(template_id))

        # Increment usage count
        template.usage_count += 1
        await db.commit()

        response = {
            "id": str(template.id),
            "creator_id": str(template.creator_id),
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "template_data": template.template_data,
            "usage_count": template.usage_count,
            "upvotes": template.upvotes,
            "downvotes": template.downvotes,
            "is_featured": bool(template.is_featured),
            "created_at": template.created_at,
            "updated_at": template.updated_at,
        }

        logger.info(
            "Template retrieved",
            extra={"template_id": str(template_id), "usage_count": template.usage_count},
        )

        return response


@router.post("/{template_id}/vote")
async def vote_template(
    template_id: UUID,
    vote_type: str = Query(..., regex="^(up|down)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Vote on a template (upvote or downvote).

    Args:
        template_id: UUID of the template
        vote_type: "up" or "down"
        db: Database session

    Returns:
        Updated vote counts
    """
    logger.info(
        "Template vote requested", extra={"template_id": str(template_id), "vote_type": vote_type}
    )

    async with AsyncTraceContext("api.vote_template"):
        result = await db.execute(select(AgentTemplate).where(AgentTemplate.id == template_id))
        template = result.scalar_one_or_none()

        if not template:
            raise not_found_exception("Template", str(template_id))

        if vote_type == "up":
            template.upvotes += 1
        else:
            template.downvotes += 1

        await db.commit()

        response = {
            "template_id": str(template_id),
            "upvotes": template.upvotes,
            "downvotes": template.downvotes,
            "score": template.upvotes - template.downvotes,
        }

        logger.info(
            "Template voted",
            extra={
                "template_id": str(template_id),
                "vote_type": vote_type,
                "new_score": response["score"],
            },
        )

        return response


@router.post("/{template_id}/remix")
async def remix_template(
    template_id: UUID,
    creator_id: UUID,
    request: CreateTemplateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new template based on an existing one (remix).

    Args:
        template_id: UUID of the original template
        creator_id: UUID of the new creator
        request: New template data
        db: Database session

    Returns:
        Created remixed template
    """
    logger.info(
        "Template remix requested",
        extra={"original_template_id": str(template_id), "creator_id": str(creator_id)},
    )

    async with AsyncTraceContext("api.remix_template"):
        # Get original template
        original_result = await db.execute(
            select(AgentTemplate).where(AgentTemplate.id == template_id)
        )
        original = original_result.scalar_one_or_none()

        if not original:
            raise not_found_exception("Template", str(template_id))

        # Create new template
        new_template = AgentTemplate(
            creator_id=creator_id,
            name=request.name,
            description=request.description,
            category=request.category,
            template_data=request.template_data,
            is_public=1 if request.is_public else 0,
        )

        db.add(new_template)

        # Increment original usage count
        original.usage_count += 1

        await db.commit()
        await db.refresh(new_template)

        logger.info(
            "Template remixed successfully",
            extra={
                "original_template_id": str(template_id),
                "new_template_id": str(new_template.id),
            },
        )

        return {
            "id": str(new_template.id),
            "original_template_id": str(template_id),
            "name": new_template.name,
            "created_at": new_template.created_at,
        }
